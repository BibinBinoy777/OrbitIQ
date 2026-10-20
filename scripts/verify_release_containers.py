"""Smoke-test prebuilt local images with an explicit empty, isolated archive.

No normal database, public service, registry push or upstream source is used.
Requires a local Docker daemon and Compose. All test containers are removed.
"""

import argparse
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from urllib.request import ProxyHandler, build_opener


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, help="Prebuilt local image tag")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    for name in (
        "DOCKER_HOST",
        "DOCKER_CONTEXT",
        "DOCKER_TLS",
        "DOCKER_TLS_VERIFY",
        "DOCKER_CERT_PATH",
    ):
        env.pop(name, None)
    docker = ["docker", "--host=unix:///var/run/docker.sock"]
    compose = [
        *docker,
        "compose",
        "-p",
        "orbitiq-smoke-" + uuid.uuid4().hex[:12],
        "-f",
        str(root / "deploy/compose.yaml"),
    ]

    def run(command, **kwargs):
        return subprocess.run(
            command, env=env, text=True, check=True, capture_output=True, **kwargs
        ).stdout

    with tempfile.TemporaryDirectory(prefix="orbitiq-release-smoke-") as directory:
        path = Path(directory)
        path.chmod(0o755)
        env.update(
            ORBITIQ_RELEASE=args.release,
            ORBITIQ_DATA_DIRECTORY=directory,
            ORBITIQ_ALLOWED_HOSTS="127.0.0.1",
            ORBITIQ_HTTP_BIND="127.0.0.1:0",
            ORBITIQ_EOP_POLICY="measured_or_predicted",
        )
        # Explicit fixture initialization, never application startup initialization.
        run(
            [
                *docker,
                "run",
                "--rm",
                "--network",
                "none",
                "--user",
                "0",
                "--mount",
                f"type=bind,src={directory},dst=/data",
                f"orbitiq-api:{args.release}",
                "python",
                "-c",
                "from pathlib import Path; from orbitiq.database import initialize; "
                "p=Path('/data/orbitiq.sqlite3'); initialize(p); p.chmod(0o444)",
            ]
        )
        before = (path / "orbitiq.sqlite3").read_bytes()
        try:
            run([*compose, "config", "--quiet"])
            run(
                [
                    *compose,
                    "up",
                    "-d",
                    "--no-build",
                    "--pull",
                    "never",
                    "--wait",
                    "--wait-timeout",
                    "90",
                ]
            )
            run([*compose, "exec", "-T", "web", "nginx", "-t"])
            address = run([*compose, "port", "web", "8080"]).strip()
            if not address.startswith("127.0.0.1:"):
                raise RuntimeError("Smoke service must remain loopback-only")
            opener = build_opener(ProxyHandler({}))  # Local loopback only.
            checks = []
            for route in ["/", "/api/health", "/api/ready", "/api/snapshots"]:
                with opener.open("http://" + address + route, timeout=10) as response:
                    body = response.read(1024 * 1024)
                    assert response.status == 200
                    assert response.headers["X-Content-Type-Options"] == "nosniff"
                    if route == "/api/ready":
                        assert json.loads(body) == {"status": "ready"}
                    if route == "/api/snapshots":
                        assert json.loads(body)["snapshots"] == []
                    checks.append({"route": route, "http_status": response.status})
            assert (path / "orbitiq.sqlite3").read_bytes() == before
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "fixture": "explicit empty isolated schema-3",
                        "checks": checks,
                        "archive_unchanged": True,
                    }
                )
            )
        finally:
            run([*compose, "down", "--timeout", "5"])


if __name__ == "__main__":
    main()
