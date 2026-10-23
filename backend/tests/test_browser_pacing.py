"""Selected browser journeys respect the real gateway; no retries/limit changes."""

import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "browser_diagnostics", Path(__file__).parents[2] / "scripts/browser_diagnostics.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def fixture_clock():
    now, sleeps = [100.0], []

    def wait(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    return module.CalculationPacer(clock=lambda: now[0], wait=wait), now, sleeps


def test_dense_calculations_share_a_budget_without_retries():
    pacer, now, waits = fixture_clock()
    pacer.schedule("http://127.0.0.1:8080/api/historical-analysis?limit=1")
    pacer.schedule("http://127.0.0.1:8080/api/investigation-reports?mode=snapshot")
    assert len(waits) == 1 and abs(waits[0] - 1.05) < 1e-9
    assert len(pacer.records) == 2
    now[0] += 2
    pacer.schedule("http://127.0.0.1:8080/api/comparisons")
    assert len(waits) == 1 and pacer.records[-1]["wait_seconds"] == 0


def test_metadata_assets_and_invalid_paths_do_not_spend_calculation_budget():
    pacer, _, waits = fixture_clock()
    for path in (
        "/api/health",
        "/api/snapshots/1",
        "/assets/index.js",
        "/api/historical-analysis-extra",
        "/api/snapshots/not-an-id/position",
    ):
        pacer.schedule("http://localhost:8080" + path)
    assert not pacer.records and not waits
    pacer.schedule("http://localhost:8080/api/historical-analysis")
    assert not waits


def test_all_calculation_route_families_and_optional_slash_are_scheduled():
    pacer, _, waits = fixture_clock()
    paths = (
        "/api/observation-validations/" + "ab" * 16,
        "/api/historical-analysis",
        "/api/comparisons",
        "/api/investigation-reports",
        "/api/snapshots/1/position",
        "/api/snapshots/1/earth-fixed",
        "/api/satellites/6251/ground-track",
    )
    for path in paths:
        for suffix in ("", "/?fixture=true"):
            pacer.schedule("http://127.0.0.1:8080" + path + suffix)
    assert len(pacer.records) == 14 and len(waits) == 13
