"""Probe local release images, gateway security and optional test-CA TLS.

Only new empty fixture storage and ephemeral loopback ports are used. No normal
archive, live provider, public certificate, registry publication or deployment.
"""

import argparse
import hashlib
import json
import os
import socket
import ssl
import subprocess
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, help="Prebuilt local image tag")
    parser.add_argument(
        "--tls", action="store_true", help="Ephemeral loopback test CA only"
    )
    parser.add_argument("--output", type=Path, help="New JSON evidence file")
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("Evidence output must not exist")
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
            command,
            env=env,
            text=True,
            check=True,
            capture_output=True,
            timeout=120,
            **kwargs,
        ).stdout

    with tempfile.TemporaryDirectory(prefix="orbitiq-release-smoke-") as directory:
        path = Path(directory)
        path.chmod(0o755)
        env.update(
            ORBITIQ_RELEASE=args.release,
            ORBITIQ_DATA_DIRECTORY=directory,
            ORBITIQ_ALLOWED_HOSTS="127.0.0.1,localhost",
            ORBITIQ_HTTP_BIND="127.0.0.1:0",
            ORBITIQ_EOP_POLICY="measured_or_predicted",
        )
        ca = path / "test-ca.pem"
        if args.tls:
            tls = path / "tls"
            tls.mkdir(mode=0o755)
            tls.chmod(0o755)  # Explicitly support a restrictive host umask.
            run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-keyout",
                    str(path / "test-ca.key"),
                    "-out",
                    str(ca),
                    "-days",
                    "1",
                    "-subj",
                    "/CN=OrbitIQ local test CA",
                    "-addext",
                    "basicConstraints=critical,CA:TRUE",
                ]
            )
            run(
                [
                    "openssl",
                    "req",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-keyout",
                    str(tls / "key.pem"),
                    "-out",
                    str(path / "server.csr"),
                    "-subj",
                    "/CN=localhost",
                ]
            )
            extension = path / "server.ext"
            extension.write_text(
                "subjectAltName=DNS:localhost,IP:127.0.0.1\n"
                "extendedKeyUsage=serverAuth\nbasicConstraints=CA:FALSE\n"
            )
            run(
                [
                    "openssl",
                    "x509",
                    "-req",
                    "-in",
                    str(path / "server.csr"),
                    "-CA",
                    str(ca),
                    "-CAkey",
                    str(path / "test-ca.key"),
                    "-CAcreateserial",
                    "-out",
                    str(tls / "fullchain.pem"),
                    "-days",
                    "1",
                    "-extfile",
                    str(extension),
                ]
            )
            # Fake server key only: allow the non-root gateway inside this bind mount.
            # The private CA key stays outside that mount. All are deleted at exit.
            (tls / "key.pem").chmod(0o444)
            (tls / "fullchain.pem").chmod(0o444)
            env.update(ORBITIQ_TLS_DIRECTORY=str(tls), ORBITIQ_HTTPS_BIND="127.0.0.1:0")
            compose.extend(["-f", str(root / "deploy/compose.tls.yaml")])
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
        database = path / "orbitiq.sqlite3"
        before = hashlib.sha256(database.read_bytes()).hexdigest()
        checks = []
        opener = build_opener(ProxyHandler({}))  # Loopback requests only.

        def address(port):
            value = run([*compose, "port", "web", str(port)]).strip()
            if not value.startswith("127.0.0.1:") or "\n" in value:
                raise RuntimeError("Smoke endpoint must remain loopback-only")
            return value

        def request(base, route, expected=200, *, client=opener, **kwargs):
            try:
                response = client.open(Request(base + route, **kwargs), timeout=10)
            except HTTPError as error:
                response = error
            with response:
                body = response.read(1024 * 1024)
                assert response.status == expected, (route, response.status, expected)
                assert response.headers["X-Content-Type-Options"] == "nosniff"
                assert response.headers["X-Frame-Options"] == "DENY"
                assert response.headers["Referrer-Policy"] == "no-referrer"
                assert (
                    "frame-ancestors 'none'"
                    in response.headers["Content-Security-Policy"]
                )
                checks.append(
                    {"route": route.split("?", 1)[0], "http_status": response.status}
                )
                return body, response.headers

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
            base = "http://" + address(8080)
            for route in ["/", "/api/health", "/api/ready", "/api/snapshots"]:
                body, headers = request(base, route)
                assert "Strict-Transport-Security" not in headers
                if route == "/api/ready":
                    assert json.loads(body) == {"status": "ready"}
                if route == "/api/snapshots":
                    assert json.loads(body)["snapshots"] == []
            _, headers = request(
                base,
                "/api/health",
                headers={
                    "Origin": "https://untrusted.invalid",
                    "X-Request-ID": "forged-id",
                    "X-Forwarded-For": "203.0.113.1",
                    "Forwarded": "for=203.0.113.1;proto=https",
                    "X-Forwarded-Proto": "https",
                },
            )
            assert "Access-Control-Allow-Origin" not in headers
            assert headers["X-Request-ID"] != "forged-id"
            assert headers["Cache-Control"] == "no-store"
            request(base, "/api/health", 400, headers={"Host": "untrusted.invalid"})
            request(base, "/api/ingestion", 404)
            request(base, "/api/snapshots", 405, method="POST", data=b"{}")
            request(base, "/api/health", 413, method="GET", data=b"body")
            request(base, "/api/health?x=" + "x" * 5000, 414)
            unavailable = path / "unavailable.sqlite3"
            database.rename(
                unavailable
            )  # This new empty fixture only, never user data.
            try:
                request(base, "/api/health")
                body, _ = request(base, "/api/ready", 503)
                assert json.loads(body) == {"status": "unavailable"}
            finally:
                unavailable.rename(database)
            request(base, "/api/ready")
            previous = run([*compose, "ps", "-q", "api"]).strip()
            run(
                [
                    *compose,
                    "up",
                    "-d",
                    "--no-build",
                    "--pull",
                    "never",
                    "--force-recreate",
                    "--wait",
                    "--wait-timeout",
                    "90",
                    "api",
                ]
            )
            assert run([*compose, "ps", "-q", "api"]).strip() != previous
            request(base, "/api/health")
            request(base, "/api/ready")
            checks.append(
                {"case": "same-release-container-replacement", "status": "PASS"}
            )

            def limited(index):
                req = Request(
                    base + "/api/investigation-reports",
                    headers={
                        "X-Forwarded-For": f"203.0.113.{index + 1}",
                    },
                )
                try:
                    response = opener.open(req, timeout=10)
                except HTTPError as error:
                    response = error
                with response:
                    code = response.status
                    assert code in (422, 429, 503), code
                    if code in (429, 503):
                        assert response.headers["Retry-After"] == "1"
                        assert response.headers["Content-Security-Policy"]
                    if code == 503:
                        # The existing application admission bound may win the
                        # race before the gateway bucket rejects another call.
                        # Accept only that documented, safe capacity refusal.
                        payload = json.loads(response.read(8192))
                        assert payload["error"]["code"] == "capacity"
                        assert (
                            payload["detail"]
                            == "Calculation capacity busy; retry later"
                        )
                    return code

            with ThreadPoolExecutor(max_workers=12) as pool:
                statuses = list(pool.map(limited, range(24)))
            assert 429 in statuses, "Forwarded client IPs must not bypass edge limits"
            assert 422 in statuses, "At least one request must reach input validation"
            request(base, "/api/health")
            request(base, "/api/ready")
            checks.append(
                {
                    "case": "rate-limit-with-spoofed-forwarded-IP",
                    "statuses": sorted(set(statuses)),
                }
            )
            if args.tls:
                endpoint = address(8443)
                secure = "https://" + endpoint
                for version in (ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3):
                    context = ssl.create_default_context(cafile=str(ca))
                    context.minimum_version = context.maximum_version = version
                    trusted = build_opener(
                        ProxyHandler({}), HTTPSHandler(context=context)
                    )
                    body, headers = request(secure, "/api/ready", client=trusted)
                    assert json.loads(body) == {"status": "ready"}
                    assert headers["Strict-Transport-Security"] == "max-age=3600"
                    checks.append({"case": version.name, "status": "PASS"})
                try:
                    build_opener(ProxyHandler({})).open(
                        secure + "/api/ready", timeout=5
                    )
                except URLError as error:
                    assert isinstance(error.reason, ssl.SSLCertVerificationError)
                else:
                    raise AssertionError("Untrusted certificate was accepted")
                context = ssl.create_default_context(cafile=str(ca))
                with socket.create_connection(
                    ("127.0.0.1", int(endpoint.split(":")[1])), timeout=5
                ) as connection:
                    try:
                        context.wrap_socket(
                            connection, server_hostname="wrong-host.invalid"
                        )
                    except ssl.SSLCertVerificationError:
                        pass
                    else:
                        raise AssertionError("Wrong certificate hostname was accepted")
                checks.append(
                    {"case": "untrusted-CA-and-wrong-host-refused", "status": "PASS"}
                )
            assert hashlib.sha256(database.read_bytes()).hexdigest() == before
            result = {
                "status": "PASS",
                "fixture": "explicit empty isolated schema-3",
                "checks": checks,
                "archive_unchanged": True,
                "tls_verified": args.tls,
                "public_https_verified": False,
                "production_deployed": False,
            }
            if args.output:
                with args.output.open("x") as file:
                    json.dump(result, file, indent=2)
                    file.write("\n")
            print(json.dumps(result))
        finally:
            run([*compose, "down", "--timeout", "5"])


if __name__ == "__main__":
    main()
