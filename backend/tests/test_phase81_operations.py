"""Isolated operational contracts; mock delivery is never production evidence."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from orbitiq.maintenance.backup_export import (
    ExportError,
    job_status,
    protected_file,
    repository_kind,
    restic,
)
from orbitiq.maintenance.monitor import collect, endpoint, notify

NOW = datetime(2026, 10, 19, 18, tzinfo=UTC)


def private(path, value):
    path.write_text(value)
    path.chmod(0o600)
    return path


@pytest.mark.parametrize(
    "value",
    [
        "http://remote.example",
        "s3:http://store.example/bucket",
        "s3:https://u:p@store.example/bucket",
        "s3:https://store.example/bucket?secret=x",
        "relative/path",
    ],
)
def test_repository_refuses_unsafe_or_ambiguous_targets(tmp_path, value):
    path = private(tmp_path / "repository", value)
    with pytest.raises(ExportError):
        repository_kind(path, False)


def test_local_repository_requires_explicit_test_label(tmp_path):
    path = private(tmp_path / "repository", str(tmp_path / "encrypted"))
    with pytest.raises(ExportError):
        repository_kind(path, False)
    assert repository_kind(path, True) == "local_test"


@pytest.mark.parametrize(
    "value",
    [
        "sftp:backup@storage.example:/srv/backups",
        "s3:https://storage.example/bucket/prefix",
    ],
)
def test_external_transport_configuration_is_not_a_verification_claim(tmp_path, value):
    path = private(tmp_path / "repository", value)
    assert repository_kind(path, False) == "external"


def test_operator_files_and_status_preserve_unknown_data(tmp_path):
    path = private(tmp_path / "secret", "not-printed")
    path.chmod(0o644)
    with pytest.raises(ExportError):
        protected_file(path)
    status = private(tmp_path / "status.json", '{"user_data":true}')
    before = status.read_bytes()
    with pytest.raises(ExportError):
        job_status(status, {"schema_version": 1, "status": "failed"})
    assert status.read_bytes() == before


def test_backup_failure_status_is_safe_and_atomic(tmp_path):
    path = tmp_path / "latest.json"
    result = {"schema_version": 1, "status": "failed", "completed_at": NOW.isoformat()}
    job_status(path, result)
    assert json.loads(path.read_text()) == {"kind": "orbitiq_backup_job", **result}
    assert path.stat().st_mode & 0o777 == 0o600


def test_storage_tool_failure_does_not_echo_credentials(monkeypatch):
    class Result:
        returncode = 1
        stdout = ""
        stderr = "secret-url private-password"

    monkeypatch.setattr(
        "orbitiq.maintenance.backup_export.subprocess.run", lambda *a, **k: Result()
    )
    with pytest.raises(ExportError) as error:
        restic(
            Path("/chosen/restic"), Path("/chosen/repo"), Path("/chosen/key"), "backup"
        )
    assert "secret" not in str(error.value) and "private-password" not in str(
        error.value
    )


@pytest.mark.parametrize(
    "value",
    [
        "http://remote.example",
        "https://u:p@example.org",
        "https://example.org?token=x",
        "https://example.org/#token",
        "file:///tmp/x",
    ],
)
def test_monitor_endpoint_refuses_credentials_and_unsafe_transport(value):
    with pytest.raises(ValueError):
        endpoint(value)


def test_local_http_requires_explicit_test_mode():
    with pytest.raises(ValueError):
        endpoint("http://127.0.0.1:1234")
    assert endpoint("http://127.0.0.1:1234", True) == "http://127.0.0.1:1234"


def responses(request):
    if request.url.path == "/api/health":
        return httpx.Response(200, json={"status": "ok"})
    if request.url.path == "/api/ready":
        return httpx.Response(200, json={"status": "ready"})
    return httpx.Response(
        200,
        json={
            "components": {
                name: {
                    "status": "healthy",
                    "last_successful_acquisition_at": NOW.isoformat(),
                }
                for name in [
                    "database",
                    "orbital_data",
                    "ingestion",
                    "eop",
                    "leap_seconds",
                ]
            }
        },
    )


def test_monitor_does_not_call_local_backup_off_machine_verified(tmp_path):
    backup = private(
        tmp_path / "receipt.json",
        json.dumps(
            {
                "status": "passed",
                "off_machine_recovery_verified": False,
                "remote_roundtrip_verified": False,
                "completed_at": NOW.isoformat(),
                "backup_sha256": "a" * 64,
            }
        ),
    )
    with httpx.Client(transport=httpx.MockTransport(responses)) as client:
        findings, facts = collect(
            client, "https://example.org", now=NOW, backup_manifest=backup
        )
    assert findings == [{"component": "backup_recovery", "status": "unknown"}]
    assert facts["latest_successful_acquisition_at"] == NOW.isoformat()


@pytest.mark.parametrize(
    "status,expected", [("failed", "unavailable"), ("passed", "unknown")]
)
def test_monitor_detects_failed_or_stale_recovery_receipts(tmp_path, status, expected):
    backup = private(
        tmp_path / "receipt.json",
        json.dumps(
            {
                "status": status,
                "off_machine_recovery_verified": True,
                "remote_roundtrip_verified": True,
                "completed_at": (NOW - timedelta(days=3)).isoformat(),
                "backup_sha256": "a" * 64,
            }
        ),
    )
    with httpx.Client(transport=httpx.MockTransport(responses)) as client:
        findings, _ = collect(
            client, "https://example.org", now=NOW, backup_manifest=backup
        )
    assert {"component": "backup_recovery", "status": expected} in findings


def test_monitor_handles_bad_readiness_and_detects_request_resource_pressure(tmp_path):
    log = private(
        tmp_path / "requests.log",
        "\n".join(
            json.dumps(
                {
                    "event": "http_request",
                    "at_utc": NOW.isoformat(),
                    "status": 503,
                    "duration_ms": 2500,
                    "query": "private-not-forwarded",
                }
            )
            for _ in range(5)
        ),
    )

    def fail(request):
        return httpx.Response(503, json={"private": "/data/secret"})

    with httpx.Client(transport=httpx.MockTransport(fail)) as client:
        findings, _ = collect(client, "https://example.org", now=NOW, request_log=log)
    assert {"component": "request_failures", "status": "degraded"} in findings
    assert {"component": "request_latency", "status": "degraded"} in findings
    assert "private" not in json.dumps(findings) and "/data/" not in json.dumps(
        findings
    )


def test_delivery_is_opt_in_and_mock_test_payload_is_unambiguous(tmp_path):
    sent = []

    def sink(request):
        sent.append(json.loads(request.content))
        return httpx.Response(204)

    state = tmp_path / "state.json"
    findings = [{"component": "api", "status": "unavailable"}]
    with httpx.Client(transport=httpx.MockTransport(sink)) as client:
        assert (
            notify(client, findings, state, now=NOW, webhook="https://sink.example")
            == "delivery_not_requested"
        )
        assert not sent
        assert (
            notify(
                client,
                findings,
                state,
                now=NOW,
                webhook="https://sink.example",
                deliver=True,
                test=True,
            )
            == "test_delivered"
        )
        assert (
            notify(
                client,
                [],
                state,
                now=NOW + timedelta(seconds=10),
                webhook="https://sink.example",
                deliver=True,
            )
            == "suppressed_cooldown"
        )
    assert len(sent) == 1 and sent[0]["test"] is True
    assert sent[0]["event"] == "orbitiq_monitor_test"


def test_failed_delivery_is_rate_limited_without_crashing_the_application(tmp_path):
    attempts = []

    def fail(request):
        attempts.append(1)
        raise httpx.ConnectError("private-host-and-token", request=request)

    state = tmp_path / "state.json"
    with httpx.Client(transport=httpx.MockTransport(fail)) as client:
        assert (
            notify(
                client,
                [],
                state,
                now=NOW,
                webhook="https://sink.example",
                deliver=True,
                test=True,
            )
            == "delivery_failed"
        )
        assert (
            notify(
                client,
                [],
                state,
                now=NOW + timedelta(seconds=30),
                webhook="https://sink.example",
                deliver=True,
                test=True,
            )
            == "suppressed_cooldown"
        )
    assert attempts == [1]
    assert "private" not in state.read_text()


def test_corrupt_or_future_state_is_not_reset(tmp_path):
    path = private(tmp_path / "state.json", '{"schema_version":999}')
    before = path.read_bytes()
    with httpx.Client(transport=httpx.MockTransport(responses)) as client:
        with pytest.raises(ValueError):
            notify(client, [], path, now=NOW)
    assert path.read_bytes() == before


def test_invalid_health_or_redirect_is_not_called_healthy():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                302, headers={"Location": "https://elsewhere.invalid"}
            )
        )
    ) as client:
        findings, _ = collect(client, "https://example.org", now=NOW)
    assert {"component": "api", "status": "unavailable"} in findings
