"""Run existing browser/PDF checks on disposable synthetic-only release services.

Requires prebuilt orbitiq-api/web:<release>, orbitiq-browser:<browser-image>,
local Docker, and host pdftotext. No ports, private data or external test services.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from threading import Event

ENGINES = ("chromium", "firefox", "webkit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True)
    parser.add_argument("--browser-image", default="e1")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engineering-e2", action="store_true")
    args = parser.parse_args()
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)  # No overwrites or arbitrary inputs.
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    for key in (
        "DOCKER_HOST",
        "DOCKER_CONTEXT",
        "DOCKER_TLS",
        "DOCKER_TLS_VERIFY",
        "DOCKER_CERT_PATH",
    ):
        env.pop(key, None)
    docker = ["docker", "--host=unix:///var/run/docker.sock"]
    prefix = "orbitiq-e1-" + uuid.uuid4().hex[:12]
    volume, network = prefix + "-fixture", prefix + "-network"
    containers, commands, failures = [], [], []
    started = time.monotonic()

    def execute(argv, name, *, expected_failure=False, timeout=420):
        before = time.monotonic()
        with (output / (name + ".log")).open("w") as log:
            try:
                result = subprocess.run(
                    argv, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout
                )
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = 124
        commands.append(
            {
                "name": name,
                "exit_code": code,
                "seconds": round(time.monotonic() - before, 3),
                "expected_failure": expected_failure,
            }
        )
        (output / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        print(name, code, flush=True)
        if (code != 0) != expected_failure or code == 124:
            raise RuntimeError(f"{name} unexpected exit {code}; inspect {name}.log")
        return (output / (name + ".log")).read_text()

    def control(*argv):
        return subprocess.check_output(
            [*docker, *argv], env=env, text=True, timeout=30
        ).strip()

    def browser(web, engine, script, options, name, expected_failure=False):
        container = prefix + "-" + name
        containers.append(container)
        directory = output / name
        directory.mkdir()
        execute(
            [
                *docker,
                "run",
                "--rm",
                "--name",
                container,
                "--user",
                f"{os.getuid()}:{os.getgid()}",
                "--network",
                "container:" + web,
                "--shm-size=1g",
                "--tmpfs",
                "/tmp:rw,nosuid,nodev,size=1g",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges:true",
                "--mount",
                f"type=bind,src={root / 'scripts'},dst=/tests,readonly",
                "--mount",
                f"type=bind,src={directory},dst=/results",
                "-e",
                "ORBITIQ_BROWSER_DIAGNOSTICS=/results/diagnostics",
                "orbitiq-browser:" + args.browser_image,
                "python",
                "/tests/" + script,
                *options,
            ],
            name,
            expected_failure=expected_failure,
        )
        if expected_failure:
            diagnostics = directory / "diagnostics"
            assert (diagnostics / "failure.json").is_file()
            assert list(diagnostics.glob("trace-*.zip"))
            assert list(diagnostics.glob("failure-*.png"))
            if name == "external-denial-probe":
                assert json.loads((diagnostics / "console.json").read_text())[
                    "denied_external_requests"
                ]

    try:
        control("volume", "create", volume)
        control("network", "create", "--internal", network)
        seed_text = execute(
            [
                *docker,
                "run",
                "--rm",
                "--network=none",
                "--user=0",
                "--mount",
                f"type=volume,src={volume},dst=/fixtures",
                "--mount",
                f"type=bind,src={root / 'scripts/seed_browser_fixtures.py'},"
                "dst=/seed.py,readonly",
                "--mount",
                f"type=bind,src={root / 'backend/tests/fixtures/vallado-leo.json'},"
                "dst=/reference.json,readonly",
                "orbitiq-api:" + args.release,
                "python",
                "/seed.py",
            ],
            "seed",
        )
        fixture = json.loads(seed_text)
        (output / "fixture-description.json").write_text(
            json.dumps(fixture, indent=2) + "\n"
        )

        def fingerprint():
            return control(
                "run",
                "--rm",
                "--network=none",
                "--user=0",
                "--mount",
                f"type=volume,src={volume},dst=/fixtures,readonly",
                "orbitiq-api:" + args.release,
                "python",
                "-c",
                "import hashlib,json; from pathlib import Path; "
                "print(json.dumps({str(p.relative_to('/fixtures')):"
                "hashlib.sha256(p.read_bytes()).hexdigest() "
                "for p in Path('/fixtures').rglob('*') if p.is_file()},"
                "sort_keys=True))",
            )

        before = fingerprint()
        for mode in ("empty", "fixture"):
            api, web = prefix + "-api-" + mode, prefix + "-web-" + mode
            for name, image, options in [
                (
                    api,
                    "orbitiq-api:" + args.release,
                    [
                        "--network-alias=api",
                        "--mount",
                        f"type=volume,src={volume},dst=/fixtures,readonly",
                        "-e",
                        "ORBITIQ_ENVIRONMENT=production",
                        "-e",
                        "ORBITIQ_DATABASE_PATH=/fixtures/archive.sqlite3",
                        "-e",
                        "ORBITIQ_ALLOWED_HOSTS=127.0.0.1,localhost",
                        "-e",
                        "ORBITIQ_EOP_POLICY=measured_or_predicted",
                        *(
                            ["-e", "ORBITIQ_VALIDATION_ARCHIVE=/fixtures/validation"]
                            if mode == "fixture"
                            else []
                        ),
                    ],
                ),
                (web, "orbitiq-web:" + args.release, []),
            ]:
                containers.append(name)
                control(
                    "run",
                    "-d",
                    "--name",
                    name,
                    "--network",
                    network,
                    "--read-only",
                    "--tmpfs",
                    "/tmp:rw,noexec,nosuid,size=128m",
                    "--cap-drop=ALL",
                    "--security-opt=no-new-privileges:true",
                    *options,
                    image,
                )
            deadline = time.monotonic() + 90
            while True:
                probe = subprocess.run(
                    [
                        *docker,
                        "exec",
                        web,
                        "wget",
                        "-q",
                        "-T",
                        "2",
                        "-Y",
                        "off",
                        "-O",
                        "-",
                        "http://127.0.0.1:8080/api/ready",
                    ],
                    env=env,
                    capture_output=True,
                    timeout=10,
                )
                if probe.returncode == 0 and json.loads(probe.stdout) == {
                    "status": "ready"
                }:
                    break
                if time.monotonic() > deadline:
                    raise TimeoutError("Gateway/API readiness timed out")
                Event().wait(
                    0.25
                )  # Bounded readiness polling, never test synchronization.
            if mode == "empty":
                browser(
                    web,
                    "chromium",
                    "verify_browser_failure_states.py",
                    [
                        "--base-url",
                        "http://127.0.0.1:8080",
                        "--first",
                        str(fixture["first"]),
                    ],
                    "chromium-failure-states",
                )
                browser(
                    web,
                    "chromium",
                    "browser_failure_probe.py",
                    [],
                    "controlled-failure",
                    True,
                )
                browser(
                    web,
                    "chromium",
                    "browser_failure_probe.py",
                    ["--external"],
                    "external-denial-probe",
                    True,
                )
            for engine in ENGINES:
                common = ["--base-url", "http://127.0.0.1:8080", "--engine", engine]
                suites = [
                    (
                        "observation-" + mode,
                        "verify_observation_browser.py",
                        [
                            *common,
                            "--mode",
                            mode,
                            "--output",
                            "/results/evidence.json",
                            *(
                                ["--run-id", fixture["run_id"]]
                                if mode == "fixture"
                                else []
                            ),
                        ],
                    )
                ]
                if mode == "empty":
                    suites += [
                        (
                            "critical",
                            "verify_browser_critical.py",
                            [
                                *common,
                                "--catalog",
                                "6251",
                                "--first",
                                str(fixture["first"]),
                                "--second",
                                str(fixture["second"]),
                                "--output",
                                "/results/evidence.json",
                            ],
                        ),
                        (
                            "history",
                            "verify_history_browser.py",
                            [
                                *common,
                                "--catalog",
                                "6251",
                                "--fixture",
                                "--output-directory",
                                "/results/history",
                            ],
                        ),
                        (
                            "report",
                            "verify_report_browser.py",
                            [
                                *common,
                                "--first",
                                str(fixture["first"]),
                                "--second",
                                str(fixture["second"]),
                                "--output-directory",
                                "/results/reports",
                                *(["--maximum-track"] if engine == "chromium" else []),
                            ],
                        ),
                    ]
                if mode == "empty" and args.engineering_e2:
                    suites.append(
                        (
                            "engineering-e2",
                            "verify_engineering_e2.py",
                            ["--engine", engine],
                        )
                    )
                if mode == "empty":
                    suites.append(
                        (
                            "engineering-e6",
                            "verify_engineering_e6.py",
                            ["--engine", engine],
                        )
                    )
                for suite, script, options in suites:
                    name = engine + "-" + suite
                    try:
                        browser(web, engine, script, options, name)
                    except Exception as error:
                        failures.append({"stage": name, "error": str(error)})
            for name in (web, api):
                execute([*docker, "logs", name], name + "-server")
                control("rm", "-f", name)
        execute(
            [
                sys.executable,
                str(root / "scripts/verify_report_pdf.py"),
                "--directory",
                str(output / "chromium-report/reports"),
                "--output",
                str(output / "pdf-results.json"),
            ],
            "pdf",
        )
        pdfs = json.loads((output / "pdf-results.json").read_text())
        assert len(pdfs) == 7 and all(p["status"] == "PASS" for p in pdfs)
        assert (
            next(p for p in pdfs if "maximum-track" in p["file"])["track_rows_checked"]
            == 361
        )
        assert fingerprint() == before, (
            "Disposable fixture changed during read-only tests"
        )
        counts = {}
        for engine in ENGINES:
            paths = [
                output / f"{engine}-critical/evidence.json",
                output / f"{engine}-history/history/evidence.json",
                output / f"{engine}-report/reports/{engine}-results.json",
                output / f"{engine}-observation-empty/evidence.json",
                output / f"{engine}-observation-fixture/evidence.json",
            ]
            counts[engine] = sum(
                len(json.loads(path.read_text())["cases"]) for path in paths
            )
        assert counts == {"chromium": 27, "firefox": 25, "webkit": 25}, counts
        e6 = {}
        e7 = {}
        for engine in ENGINES:
            record = json.loads(
                (output / f"{engine}-engineering-e6/evidence.json").read_text()
            )
            assert record["status"] == "PASS" and len(record["round_trips"]) == 4
            e6[engine] = len(record["cases"])
            history = json.loads(
                (output / f"{engine}-history/history/evidence.json").read_text()
            )
            assert history["engineering_e7"]["status"] == "PASS"
            e7[engine] = len(history["engineering_e7"]["cases"])
        if failures:
            raise RuntimeError(str(failures))
        (output / "summary.json").write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "browser_flows": counts,
                    "total_flows": sum(counts.values()),
                    "pdf_checks": len(pdfs),
                    "engineering_e2": args.engineering_e2,
                    "engineering_e6": e6,
                    "engineering_e7": e7,
                    "additional_fault_injection_cases": len(
                        json.loads(
                            (
                                output / "chromium-failure-states/evidence.json"
                            ).read_text()
                        )["cases"]
                    ),
                    "fixture_unchanged": True,
                    "fixture_kind": fixture["fixture"],
                    "fixture_manifest_sha256": hashlib.sha256(
                        before.encode()
                    ).hexdigest(),
                    "seconds": round(time.monotonic() - started, 3),
                },
                indent=2,
            )
            + "\n"
        )
    except BaseException as error:
        (output / "failure.json").write_text(
            json.dumps(
                {"status": "FAIL", "error": str(error), "failed_stages": failures},
                indent=2,
            )
            + "\n"
        )
        raise
    finally:
        for container in reversed(containers):
            with (output / (container + "-cleanup.log")).open("w") as log:
                subprocess.run(
                    [*docker, "logs", container],
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=15,
                )
            subprocess.run(
                [*docker, "rm", "-f", container],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
        for kind, name in [("network", network), ("volume", volume)]:
            subprocess.run(
                [*docker, kind, "rm", name],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )


if __name__ == "__main__":
    main()
