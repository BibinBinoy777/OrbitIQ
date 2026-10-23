"""Record exact local images and test evidence; never approve or deploy production.

CI uses a clean committed checkout. --candidate-index is explicitly local-only,
and the resulting record is ineligible for release. No registry calls or keys.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKER = ["docker", "--host=unix:///var/run/docker.sock"]
SHA256 = re.compile(r"[a-f0-9]{64}")


def command(argv, *, root=ROOT):
    env = os.environ.copy()
    for name in (
        "DOCKER_HOST",
        "DOCKER_CONTEXT",
        "DOCKER_TLS",
        "DOCKER_TLS_VERIFY",
        "DOCKER_CERT_PATH",
    ):
        env.pop(name, None)
    return subprocess.check_output(argv, cwd=root, env=env, text=True, timeout=90)


def digest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Release inputs must be regular, non-symlink files")
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def inventory(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Artifact directory is unavailable or symbolic")
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Artifact symlinks are refused")
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = digest(path)
    if not result:
        raise ValueError("Empty release artifact")
    return result


def source(*, candidate=False, root=ROOT):
    staged = command(["git", "diff", "--cached", "--name-only"], root=root).strip()
    unstaged = command(["git", "diff", "--name-only"], root=root).strip()
    untracked = command(
        ["git", "ls-files", "--others", "--exclude-standard"], root=root
    ).strip()
    if unstaged or untracked or (staged and not candidate):
        raise ValueError(
            "Release requires a clean source; stage a local candidate explicitly"
        )
    revision = command(["git", "rev-parse", "HEAD"], root=root).strip()
    tree = command(
        ["git", "write-tree"] if candidate else ["git", "rev-parse", "HEAD^{tree}"],
        root=root,
    ).strip()
    names = command(["git", "ls-files", "-z"], root=root).split("\0")
    return {
        "revision": revision,
        "tree": tree,
        "kind": "reviewed-index" if candidate else "committed",
        "files_sha256": {name: digest(root / name) for name in names if name},
    }


def images(release, identity):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}", release):
        raise ValueError("Invalid local release tag")
    found = {}
    for role in ("api", "web"):
        reference = f"orbitiq-{role}:{release}"
        spec = json.loads(
            command(
                [
                    *DOCKER,
                    "image",
                    "inspect",
                    reference,
                    "--format",
                    '{"id":{{json .Id}},"labels":{{json .Config.Labels}},'
                    '"os":{{json .Os}},"architecture":{{json .Architecture}}}',
                ]
            )
        )
        labels = spec["labels"] or {}
        if (
            labels.get("org.opencontainers.image.revision") != identity["revision"]
            or labels.get("io.orbitiq.source-tree") != identity["tree"]
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", spec["id"])
        ):
            raise ValueError("Image labels/identity do not match the reviewed source")
        found[role] = {
            "reference": reference,
            "id": spec["id"],
            "os": spec["os"],
            "architecture": spec["architecture"],
        }
    return found


def web_files(image):
    container = command(
        [
            *DOCKER,
            "create",
            "--network=none",
            "--name",
            "orbitiq-e4-inspect-" + uuid.uuid4().hex,
            "--entrypoint",
            "/bin/true",
            image,
        ]
    ).strip()
    try:
        with tempfile.TemporaryDirectory(prefix="orbitiq-web-artifact-") as directory:
            command([*DOCKER, "cp", f"{container}:/usr/share/nginx/html/.", directory])
            return inventory(Path(directory))
    finally:
        command([*DOCKER, "rm", container])  # Only the stopped container created above.


def write_new(path, value):
    with path.open("x") as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write("\n")


def load(path):
    if path.is_symlink() or path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("Unsafe or oversized evidence file")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("Evidence must be an object")
    return value


def capture(release, frontend, output, *, candidate=False):
    identity = source(candidate=candidate)
    built = images(release, identity)
    files = inventory(frontend)
    if web_files(built["web"]["id"]) != files:
        raise ValueError("Tested web image differs from frontend build artifact")
    record = {
        "schema_version": 1,
        "kind": "orbitiq_release_capture",
        "created_at": datetime.now(UTC).isoformat(),
        "source": identity,
        "images": built,
        "frontend_files_sha256": files,
        "production_approved": False,
    }
    write_new(output, record)
    return record


def evidence(directory):
    proxy = load(directory / "proxy.json")
    browser = directory / "browser"
    summary = load(browser / "summary.json")
    if (
        proxy.get("status") != "PASS"
        or not proxy.get("tls_verified")
        or not proxy.get("archive_unchanged")
        or len(proxy.get("checks", [])) < 10
        or summary.get("status") != "PASS"
        or not summary.get("engineering_e2")
        or not summary.get("fixture_unchanged")
        or summary.get("pdf_checks") != 7
        or summary.get("additional_fault_injection_cases") != 5
        or "SYNTHETIC" not in summary.get("fixture_kind", "")
    ):
        raise ValueError("Required proxy/browser checks are missing or failed")
    flows = summary.get("browser_flows", {})
    if (
        set(flows) != {"chromium", "firefox", "webkit"}
        or any(type(count) is not int or count <= 0 for count in flows.values())
        or sum(flows.values()) != summary.get("total_flows")
    ):
        raise ValueError("Incomplete browser-engine evidence")
    files = [
        directory / "proxy.json",
        browser / "summary.json",
        browser / "commands.json",
        browser / "pdf-results.json",
    ]
    commands = json.loads((browser / "commands.json").read_text())
    probes = [c for c in commands if c["expected_failure"]]
    if len(probes) != 2 or any(
        c["exit_code"] != (1 if c["expected_failure"] else 0) for c in commands
    ):
        raise ValueError("Unexpected failed/cancelled test or missing failure probe")
    for engine in flows:
        path = browser / f"{engine}-engineering-e2/evidence.json"
        check = load(path)
        if (
            not check.get("checks")
            or check.get("issues")
            or any(c.get("pass") is not True for c in check["checks"])
            or len(check.get("accessibility", [])) != 6
            or any(s["violations"] for s in check["accessibility"])
        ):
            raise ValueError(
                "Accessibility/regression evidence is incomplete or failed"
            )
        files.append(path)
        history_path = browser / f"{engine}-history/history/evidence.json"
        history = load(history_path).get("engineering_e7", {})
        expected_cases = {
            "initial_retry",
            "next_retry",
            "previous_retry",
            "wrong_window_refused",
            "captured_export",
            "input_clears_retry",
            "keyboard_layout",
        }
        if (
            history.get("status") != "PASS"
            or history.get("page_errors")
            or history.get("no_network_writes") is not True
            or history.get("browser_storage_unchanged") is not True
            or len(history.get("cases", [])) != 7
            or {c.get("case") for c in history.get("cases", [])} != expected_cases
            or any(c.get("status") != "PASS" for c in history["cases"])
            or summary.get("engineering_e7", {}).get(engine) != 7
            or len(history.get("accessibility", [])) != 2
            or any(a["violations"] for a in history["accessibility"])
            or {
                layout.get("width")
                for layout in history.get("layouts", [])
                if layout.get("status") == "PASS"
            }
            != {320, 1440}
        ):
            raise ValueError(
                "Historical window recovery evidence is incomplete or failed"
            )
        download = history_path.parent / "selected-window.json"
        receipt = history.get("download", {})
        if receipt.get("file") != download.name or digest(download) != receipt.get(
            "sha256"
        ):
            raise ValueError("Historical captured export changed or is missing")
        captured = load(download)
        if captured.get("request") != history.get("captured_request"):
            raise ValueError("Historical captured window does not match receipt")
        files.extend([history_path, download])
        path = browser / f"{engine}-engineering-e6/evidence.json"
        recovery = load(path)
        if (
            recovery.get("status") != "PASS"
            or recovery.get("engine") != engine
            or recovery.get("original_browser_unchanged") is not True
            or recovery.get("no_network_writes") is not True
            or recovery.get("page_errors")
            or recovery.get("offline_import") is not True
            or len(recovery.get("cases", [])) != 13
            or any(c.get("status") != "PASS" for c in recovery["cases"])
            or summary.get("engineering_e6", {}).get(engine) != len(recovery["cases"])
            or {r.get("mode") for r in recovery.get("round_trips", [])}
            != {"snapshot", "position", "ground-track", "comparison"}
            or len(recovery.get("round_trips", [])) != 4
            or any(
                r.get("status") != "PASS"
                or r.get("independent_context") is not True
                or r.get("record_equal") is not True
                or r.get("original_unchanged") is not True
                for r in recovery["round_trips"]
            )
            or len(recovery.get("accessibility", [])) != 4
            or any(s["violations"] for s in recovery["accessibility"])
            or {
                r.get("width")
                for r in recovery.get("layouts", [])
                if r.get("status") == "PASS"
            }
            != {320, 390, 1440}
        ):
            raise ValueError("Portable recovery evidence is incomplete or failed")
        files.append(path)
        downloads = recovery.get("downloaded_bundles", [])
        if len(downloads) < 13 or len(set(downloads)) != len(downloads):
            raise ValueError("Native portable downloads are missing")
        for name in downloads:
            if not isinstance(name, str) or not re.fullmatch(
                r"\d{2}-orbitiq-investigation-(snapshot|position|ground-track|comparison)-[a-f0-9-]{36}\.json",
                name,
            ):
                raise ValueError("Invalid portable download evidence name")
            downloaded = path.parent / "bundles" / name
            if downloaded.is_symlink() or not 0 < downloaded.stat().st_size <= 16384:
                raise ValueError("Invalid portable download evidence size")
            bundle = load(downloaded)
            if (
                set(bundle) != {"kind", "schema_version", "exported_at", "record"}
                or bundle["kind"] != "orbitiq_saved_investigation_bundle"
                or bundle["schema_version"] != 1
                or not isinstance(bundle["record"], dict)
            ):
                raise ValueError("Invalid portable download evidence format")
            files.append(downloaded)
    pdf_results = json.loads((browser / "pdf-results.json").read_text())
    pdfs = sorted(browser.rglob("*.pdf"))
    if (
        len(pdf_results) != 7
        or len(pdfs) != 7
        or any(p["status"] != "PASS" for p in pdf_results)
    ):
        raise ValueError("Incomplete PDF evidence")
    by_name = {entry["file"]: entry for entry in pdf_results}
    if set(by_name) != {path.name for path in pdfs}:
        raise ValueError("PDF evidence names differ from tested artifacts")
    for path in pdfs:
        entry = by_name[path.name]
        report = path.with_suffix(".json")
        if (
            digest(path) != entry.get("sha256")
            or path.stat().st_size != entry["bytes"]
            or digest(report) != entry.get("report_sha256")
        ):
            raise ValueError("PDF or captured report changed after validation")
        files.append(report)
    files.extend(pdfs)
    return {p.relative_to(directory).as_posix(): digest(p) for p in files}


def seal(captured, frontend, directory, output):
    if captured.parent.resolve() != directory.resolve():
        raise ValueError("Capture must be inside the release evidence directory")
    before = load(captured)
    if (
        before.get("schema_version") != 1
        or before.get("kind") != "orbitiq_release_capture"
    ):
        raise ValueError("Unsupported capture")
    identity = source(candidate=before["source"]["kind"] == "reviewed-index")
    if identity != before["source"]:
        raise ValueError("Source changed after image capture")
    release = before["images"]["api"]["reference"].split(":", 1)[1]
    current = images(release, identity)
    if current != before["images"]:
        raise ValueError("Image tag was substituted after capture")
    if (
        inventory(frontend) != before["frontend_files_sha256"]
        or web_files(current["web"]["id"]) != before["frontend_files_sha256"]
    ):
        raise ValueError("Frontend artifact changed after capture")
    result = {
        **before,
        "kind": "orbitiq_verified_release_record",
        "verified_at": datetime.now(UTC).isoformat(),
        "capture_sha256": digest(captured),
        "capture_name": captured.name,
        "evidence_sha256": evidence(directory),
        "status": "PASS",
        "production_approved": False,
        "release_candidate": identity["kind"] == "committed",
        "required_remote_jobs": ["backend", "frontend", "release-images"],
        "approval": "Exact-SHA CI and separate human production approval required",
    }
    write_new(output, result)
    return result


def verify_files(record, directory, frontend=None):
    value = load(record)
    if (
        value.get("schema_version") != 1
        or value.get("kind") != "orbitiq_verified_release_record"
        or value.get("status") != "PASS"
        or value.get("production_approved") is not False
    ):
        raise ValueError("Unsupported or unsuccessful release record")
    name = value.get("capture_name", "")
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+\.json", name):
        raise ValueError("Invalid capture name")
    captured = directory / name
    before = load(captured)
    if digest(captured) != value.get("capture_sha256") or any(
        before.get(key) != value.get(key)
        for key in ("source", "images", "frontend_files_sha256")
    ):
        raise ValueError("Capture or recorded artifact identity was changed")
    if frontend is not None and inventory(frontend) != value["frontend_files_sha256"]:
        raise ValueError("Frontend artifact checksum mismatch")
    expected = value.get("evidence_sha256")
    if not expected or expected != evidence(directory):
        raise ValueError("Release evidence was changed or is incomplete")
    for checksum in expected.values():
        if not SHA256.fullmatch(checksum):
            raise ValueError("Invalid artifact checksum")
    return {
        "status": "PASS",
        "scope": "artifact integrity only; not deployment approval",
        "revision": value["source"]["revision"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    p = sub.add_parser("capture")
    p.add_argument("--release", required=True)
    p.add_argument("--frontend", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--candidate-index", action="store_true")
    p = sub.add_parser("seal")
    p.add_argument("--capture", type=Path, required=True)
    p.add_argument("--frontend", type=Path, required=True)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("verify-files")
    p.add_argument("--record", type=Path, required=True)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--frontend", type=Path)
    args = parser.parse_args()
    try:
        if args.operation == "capture":
            result = capture(
                args.release, args.frontend, args.output, candidate=args.candidate_index
            )
        elif args.operation == "seal":
            result = seal(args.capture, args.frontend, args.directory, args.output)
        else:
            result = verify_files(args.record, args.directory, args.frontend)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        parser.exit(
            1,
            "Release verification refused; inspect source, images and evidence.\n",
        )
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("status", "kind", "revision", "scope")
                if k in result
            }
        )
    )


if __name__ == "__main__":
    main()
