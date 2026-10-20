"""Operator-invoked readiness checks and bounded, opt-in webhook notifications."""

import argparse
import fcntl
import hashlib
import ipaddress
import json
import logging
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx

COMPONENTS = ("database", "orbital_data", "ingestion", "eop", "leap_seconds")
STATUSES = {"healthy", "degraded", "unavailable", "unknown"}
MAX_BYTES = 262144


def endpoint(value, allow_local_test=False):
    parsed = urlsplit(value)
    loopback = parsed.hostname == "localhost"
    try:
        loopback = loopback or ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        pass
    if (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Use a credential-free endpoint without query or fragment")
    if parsed.scheme != "https" and not (
        allow_local_test and parsed.scheme == "http" and loopback
    ):
        raise ValueError(
            "HTTPS is required; loopback HTTP needs explicit local-test mode"
        )
    return value.rstrip("/")


def request_json(client, url):
    with client.stream("GET", url) as response:
        response.raise_for_status()
        data = bytearray()
        for part in response.iter_bytes():
            data.extend(part)
            if len(data) > MAX_BYTES:
                raise ValueError("Monitoring response too large")
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError("Invalid monitoring response")
        return value


def timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Invalid receipt timestamp")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Receipt time requires a timezone")
    return parsed.astimezone(UTC)


def collect(client, base, *, now, backup_manifest=None, request_log=None):
    findings = []
    facts = {"latest_successful_acquisition_at": None}
    for path, component in [("/api/health", "api"), ("/api/ready", "storage_probe")]:
        try:
            value = request_json(client, base + path)
            expected = "ok" if component == "api" else "ready"
            if value.get("status") != expected:
                raise ValueError
        except (httpx.HTTPError, ValueError):
            findings.append({"component": component, "status": "unavailable"})
    try:
        value = request_json(client, base + "/api/readiness")
        for component in COMPONENTS:
            state = (
                value.get("components", {}).get(component, {}).get("status", "unknown")
            )
            if state not in STATUSES:
                state = "unknown"
            if state != "healthy":
                findings.append({"component": component, "status": state})
        raw = (
            value.get("components", {})
            .get("ingestion", {})
            .get("last_successful_acquisition_at")
        )
        if raw is not None:
            stamp = timestamp(raw)
            if stamp > now:
                raise ValueError
            facts["latest_successful_acquisition_at"] = stamp.isoformat()
    except (httpx.HTTPError, ValueError, AttributeError, TypeError):
        findings.append({"component": "scientific_assessment", "status": "unavailable"})
    try:
        if backup_manifest is None or backup_manifest.stat().st_size > MAX_BYTES:
            raise ValueError
        receipt = json.loads(backup_manifest.read_text())
        if receipt.get("status") != "passed":
            findings.append({"component": "backup_recovery", "status": "unavailable"})
        elif not (
            receipt.get("off_machine_recovery_verified") is True
            and receipt.get("remote_roundtrip_verified") is True
            and 0
            <= (now - timestamp(receipt.get("completed_at"))).total_seconds()
            <= 172800
            and re.fullmatch(r"[a-f0-9]{64}", str(receipt.get("backup_sha256", "")))
        ):
            findings.append({"component": "backup_recovery", "status": "unknown"})
    except (OSError, ValueError, AttributeError):
        findings.append({"component": "backup_recovery", "status": "unknown"})
    if request_log is not None:
        try:
            with request_log.open("rb") as file:
                size = file.seek(0, 2)
                file.seek(max(0, size - MAX_BYTES))
                lines = (
                    file.read(MAX_BYTES).decode("utf-8", errors="replace").splitlines()
                )
            failures, slow = 0, 0
            for line in lines:
                try:
                    row = json.loads(line)
                    if (
                        row.get("event") != "http_request"
                        or not 0
                        <= (now - timestamp(row.get("at_utc"))).total_seconds()
                        <= 300
                    ):
                        continue
                    failures += row.get("status") in {429, 500, 502, 503, 504}
                    slow += (
                        isinstance(row.get("duration_ms"), (int, float))
                        and row["duration_ms"] > 2000
                    )
                except (ValueError, AttributeError, TypeError):
                    continue
            facts.update(recent_failure_count=failures, recent_slow_count=slow)
            if failures >= 5:
                findings.append({"component": "request_failures", "status": "degraded"})
            if slow >= 5:
                findings.append({"component": "request_latency", "status": "degraded"})
        except OSError:
            findings.append({"component": "request_telemetry", "status": "unknown"})
    return sorted(findings, key=lambda x: x["component"]), facts


def atomic_state(path, value):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as file:
        temporary = Path(file.name)
        try:
            os.chmod(temporary, 0o600)
            json.dump(value, file)
            file.flush()
            os.fsync(file.fileno())
            os.replace(temporary, path)
            descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        finally:
            temporary.unlink(missing_ok=True)


def notify(
    client,
    findings,
    state_file,
    *,
    now,
    webhook=None,
    token_file=None,
    deliver=False,
    test=False,
    interval=1800,
    monitor_id="orbitiq",
):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", monitor_id):
        raise ValueError("Invalid bounded monitor identifier")
    if (
        not state_file.is_absolute()
        or state_file.is_symlink()
        or not state_file.parent.is_dir()
    ):
        raise ValueError("Select an existing private state directory and absolute file")
    if (
        state_file.parent.stat().st_mode & 0o077
        or state_file.parent.stat().st_uid != os.getuid()
    ):
        raise ValueError("Monitoring state directory must be private")
    lock = state_file.with_suffix(state_file.suffix + ".lock")
    if lock.is_symlink():
        raise ValueError("Invalid monitoring lock")
    with lock.open("a+") as file:
        os.fchmod(file.fileno(), 0o600)
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = {
            "schema_version": 1,
            "last_attempt_at": None,
            "last_delivered_state": None,
        }
        if state_file.exists():
            if state_file.stat().st_size > 8192:
                raise ValueError("Corrupt monitoring state preserved")
            data = json.loads(state_file.read_text())
            if (
                not isinstance(data, dict)
                or set(data) != set(state)
                or data["schema_version"] != 1
            ):
                raise ValueError("Unsupported monitoring state preserved")
            if data["last_attempt_at"] is not None:
                timestamp(data["last_attempt_at"])
            if data["last_delivered_state"] is not None and not re.fullmatch(
                r"[a-f0-9]{64}", str(data["last_delivered_state"])
            ):
                raise ValueError("Corrupt monitoring state preserved")
            state = data
        digest = hashlib.sha256(
            json.dumps(findings, sort_keys=True).encode()
        ).hexdigest()
        if not deliver or not webhook:
            return "not_configured" if not webhook else "delivery_not_requested"
        elapsed = (
            (now - timestamp(state["last_attempt_at"])).total_seconds()
            if state["last_attempt_at"]
            else None
        )
        if elapsed is not None and elapsed < interval:
            return "suppressed_cooldown"
        if (
            not findings
            and state["last_delivered_state"] in (None, digest)
            and not test
        ):
            return "no_incident"
        headers = {}
        if token_file is not None:
            if (
                not token_file.is_absolute()
                or token_file.is_symlink()
                or token_file.stat().st_mode & 0o077
                or token_file.stat().st_size > 4096
            ):
                raise ValueError("Alert token file must be private and bounded")
            token = token_file.read_text().strip()
            if not token or "\n" in token or "\r" in token:
                raise ValueError("Invalid alert credential configuration")
            headers["Authorization"] = "Bearer " + token
        # Persist admission before sending, so failed/killed delivery cannot storm.
        state["last_attempt_at"] = now.isoformat()
        atomic_state(state_file, state)
        payload = {
            "schema_version": 1,
            "event": "orbitiq_monitor_test" if test else "orbitiq_readiness",
            "test": test,
            "monitor_id": monitor_id,
            "at_utc": now.isoformat(),
            "incident_id": digest,
            "active": bool(findings),
            "components": findings,
        }
        try:
            with client.stream(
                "POST", webhook, json=payload, headers=headers
            ) as response:
                if not 200 <= response.status_code < 300:
                    return "delivery_failed"
        except httpx.HTTPError:
            return "delivery_failed"
        state["last_delivered_state"] = digest
        atomic_state(state_file, state)
        return "test_delivered" if test else "delivered"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--backup-manifest", type=Path)
    parser.add_argument("--request-log", type=Path)
    parser.add_argument("--webhook-url-file", type=Path)
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--deliver", action="store_true")
    parser.add_argument("--test-alert", action="store_true")
    parser.add_argument("--allow-local-test", action="store_true")
    parser.add_argument("--interval-seconds", type=int, default=1800)
    args = parser.parse_args()
    os.umask(0o077)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    try:
        if not 300 <= args.interval_seconds <= 86400:
            raise ValueError("Alert interval must be 300..86400 seconds")
        base = endpoint(args.base_url, args.allow_local_test)
        webhook = None
        if args.webhook_url_file:
            p = args.webhook_url_file
            if (
                not p.is_absolute()
                or p.is_symlink()
                or p.stat().st_mode & 0o077
                or p.stat().st_size > 4096
            ):
                raise ValueError("Webhook configuration must be private and bounded")
            webhook = endpoint(p.read_text().strip(), args.allow_local_test)
        now = datetime.now(UTC)
        with httpx.Client(
            timeout=httpx.Timeout(5, connect=2), follow_redirects=False
        ) as client:
            findings, facts = collect(
                client,
                base,
                now=now,
                backup_manifest=args.backup_manifest,
                request_log=args.request_log,
            )
            delivery = notify(
                client,
                findings,
                args.state_file,
                now=now,
                webhook=webhook,
                token_file=args.token_file,
                deliver=args.deliver,
                test=args.test_alert or args.allow_local_test,
                interval=args.interval_seconds,
            )
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "at_utc": now.isoformat(),
                    "findings": findings,
                    "facts": facts,
                    "delivery": delivery,
                    "production_delivery_verified": False,
                }
            )
        )
        if delivery == "delivery_failed":
            raise SystemExit(2)
    except (OSError, ValueError, RuntimeError, httpx.HTTPError):
        parser.exit(
            1, "Monitoring check refused; inspect private configuration/state.\n"
        )


if __name__ == "__main__":
    main()
