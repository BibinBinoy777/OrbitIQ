"""Verify the staged Git tree in isolation, with fresh locked installations.

Linux/macOS local development smoke check; no live provider or private data.
Requires Git, Python 3.12, uv 0.12.23, Node 24 and npm 11 on PATH. The output
must not exist. The exported index is identified by its exact Git tree ID.
"""

import argparse
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener


def fixture_step(step):
    """Run only inside the isolated installation against its disposable archive."""
    from contextlib import closing
    from datetime import UTC, datetime, timedelta

    import httpx
    from orbitiq.database import configured_path, connect_existing, validate
    from orbitiq.ingestion import celestrak, collection
    from orbitiq.storage import verify_archive

    path = configured_path()
    checkout = Path(__file__).resolve().parents[1]
    if (
        checkout.name != "checkout"
        or path != checkout.parent / "synthetic-only.sqlite3"
        or not (checkout.parent / ".orbitiq-e3-fixture").is_file()
    ):
        raise ValueError("Fixture steps require the isolated E3 smoke workspace")
    record = json.loads(
        (
            Path(__file__).parents[1] / "backend/tests/fixtures/vallado-leo.json"
        ).read_text()
    )[0]["omm"]
    raw = json.dumps([record]).encode()
    clock = datetime(2030, 1, 1, tzinfo=UTC)
    at = clock + timedelta(hours={"seed": 0, "failure": 2, "recover": 4}[step])
    calls = []

    def response(request):
        calls.append(request)
        if step == "failure":
            raise httpx.ConnectError("deterministic fixture connection failure")
        return httpx.Response(
            200,
            stream=httpx.ByteStream(raw),
            headers={"content-type": "application/json"},
        )

    try:
        result = collection.collect(
            path,
            6251,
            now=lambda: at,
            jitter=lambda: 0,
            transport=httpx.MockTransport(response),
            verify_replay=True,
        )
    except celestrak.IngestionError as error:
        if step != "failure" or error.category != "network":
            raise
    else:
        assert step != "failure", "Failure probe unexpectedly succeeded"
        assert result["outcome"] == ("inserted" if step == "seed" else "deduplicated")
    assert len(calls) == 1
    expected = {
        "seed": ["inserted"],
        "failure": ["acquisition_failed", "inserted"],
        "recover": ["deduplicated", "acquisition_failed", "inserted"],
    }[step]
    assert [row["outcome"] for row in collection.history(path)["attempts"]] == expected
    assert verify_archive(path) == 1
    with closing(connect_existing(path)) as db:
        validate(db)
    print(json.dumps({"step": step, "status": "PASS", "fixture": "NOT LIVE DATA"}))


def port():
    with socket.socket() as connection:
        connection.bind(("127.0.0.1", 0))
        return connection.getsockname()[1]


def verify(output):
    root = Path(__file__).resolve().parents[1]
    output.mkdir(parents=False, exist_ok=False)
    checkout = output / "checkout"
    checkout.mkdir()
    (output / ".orbitiq-e3-fixture").touch(exist_ok=False)
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("ORBITIQ_")
        and key not in {"PYTHONPATH", "UV_PROJECT_ENVIRONMENT", "VIRTUAL_ENV"}
    }
    env.update(
        UV_CACHE_DIR=str(output / "uv-cache"),
        npm_config_cache=str(output / "npm-cache"),
    )
    stages = []
    processes = []
    logs = []
    opener = build_opener(ProxyHandler({}))  # Only loopback requests below.

    def run(name, command, *, cwd=checkout, success=True):
        with (output / f"{name}.log").open("w") as log:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=240,
                check=False,
            )
        assert (result.returncode == 0) == success, f"See {name}.log"
        stages.append({"stage": name, "exit_code": result.returncode})

    def request(base, route, expected=200):
        try:
            response = opener.open(base + route, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            body = response.read(2 * 1024 * 1024)
            assert response.status == expected, (route, response.status)
            return body

    def start(name, command, cwd):
        log = (output / f"{name}.log").open("w")
        logs.append(log)
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        processes.append(process)
        return process

    def stop(process):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            result = process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
            raise RuntimeError("Service required forced shutdown") from None
        assert result in (0, -signal.SIGTERM), f"Service exited {result}"

    def available(process, base, route):
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            assert process.poll() is None, "Service exited before becoming available"
            try:
                request(base, route)
                return
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(0.2)
        raise TimeoutError("Local service did not become available in 40 seconds")

    try:
        tree = subprocess.check_output(
            ["git", "write-tree"], cwd=root, text=True
        ).strip()
        run(
            "export-index",
            ["git", "checkout-index", "--all", f"--prefix={checkout}/"],
            cwd=root,
        )
        assert not (checkout / "data").exists()
        assert not (checkout / ".venv").exists()
        assert not (checkout / "frontend/node_modules").exists()
        run("uv-sync", ["uv", "sync", "--locked"])
        run("npm-ci", ["npm", "ci"], cwd=checkout / "frontend")
        run("frontend-build", ["npm", "run", "build"], cwd=checkout / "frontend")
        config = {}
        for line in (checkout / ".env.example").read_text().splitlines():
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key] = value
        api_port, web_port = port(), port()
        while web_port == api_port:
            web_port = port()
        api, web = f"http://127.0.0.1:{api_port}", f"http://127.0.0.1:{web_port}"
        database = output / "synthetic-only.sqlite3"
        config.update(ORBITIQ_DATABASE_PATH=str(database), ORBITIQ_BACKEND_URL=api)
        env.update(config, PYTHONPATH=str(checkout / "backend"))
        python = str(checkout / ".venv/bin/python")
        api_command = [
            python,
            "-m",
            "uvicorn",
            "orbitiq.main:app",
            "--app-dir",
            "backend",
            "--host",
            "127.0.0.1",
            "--port",
            str(api_port),
        ]
        backend = start("backend-first-start", api_command, checkout)
        available(backend, api, "/api/health")
        request(api, "/api/ready", 503)
        assert not database.exists(), "Startup must never initialize a database"
        stages.append({"stage": "missing-database-safe", "status": "PASS"})
        run("explicit-init", [python, "-m", "orbitiq.database", "init"])
        run(
            "duplicate-init-refused",
            [python, "-m", "orbitiq.database", "init"],
            success=False,
        )
        run(
            "migration-no-op",
            [
                python,
                "-m",
                "orbitiq.database",
                "migrate",
                "--backup",
                str(output / "not-needed.sqlite3"),
            ],
        )
        assert not (output / "not-needed.sqlite3").exists()
        request(api, "/api/ready")
        assert json.loads(request(api, "/api/snapshots"))["snapshots"] == []
        frontend = start(
            "frontend-dev",
            ["npm", "run", "dev", "--", "--port", str(web_port)],
            checkout / "frontend",
        )
        available(frontend, web, "/")
        request(web, "/api/health")
        smoke = [python, "scripts/verify_fresh_checkout.py", "--fixture-step"]
        run("fixture-seed", [*smoke, "seed"])
        snapshots = json.loads(request(web, "/api/snapshots"))["snapshots"]
        assert len(snapshots) == 1 and snapshots[0]["catalog_id"] == 6251
        sid = snapshots[0]["id"]
        request(web, f"/api/snapshots/{sid}")
        request(
            web, f"/api/snapshots/{sid}/position?at=2006-06-25T19%3A46%3A43.980096Z"
        )
        run("fixture-failure", [*smoke, "failure"])
        request(web, "/api/health")
        request(web, "/api/ready")
        assert len(json.loads(request(web, "/api/snapshots"))["snapshots"]) == 1
        stop(backend)
        backend = start("backend-restart", api_command, checkout)
        available(backend, api, "/api/health")
        request(web, "/api/ready")
        run("fixture-recover", [*smoke, "recover"])
        assert len(json.loads(request(web, "/api/snapshots"))["snapshots"]) == 1
        run(
            "recovery-rehearsal",
            [
                python,
                "-m",
                "orbitiq.maintenance.recovery",
                "--directory",
                str(output / "recovery"),
            ],
        )
        for process in reversed(processes):
            stop(process)
        receipt = {
            "status": "PASS",
            "source_tree": tree,
            "source": "isolated Git index checkout; fresh .venv/node_modules",
            "fixture": "Vallado 6251, NOT LIVE DATA; injected collector clock",
            "checks": stages,
            "frontend_proxy": "PASS",
            "restart": "PASS",
            "cleanup": "services stopped; fixture-only evidence retained under output",
            "production_deployed": False,
        }
        (output / "summary.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt))
    except BaseException:
        (output / "failure.json").write_text(
            json.dumps({"status": "FAIL", "completed_stages": stages}, indent=2) + "\n"
        )
        raise
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                stop(process)
        for log in logs:
            log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fixture-step", choices=["seed", "failure", "recover"])
    args = parser.parse_args()
    if args.fixture_step:
        fixture_step(args.fixture_step)
    elif args.output and args.output.is_absolute():
        verify(args.output)
    else:
        parser.error("--output must be an absolute, non-existing directory")


if __name__ == "__main__":
    main()
