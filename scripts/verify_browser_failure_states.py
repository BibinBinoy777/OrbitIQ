"""Explicit Chromium transport/WebGL fault injection; separate from 77 live flows."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, build_opener

from browser_diagnostics import browser_session
from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--first", required=True, type=int)
    args = parser.parse_args()
    base = args.base_url
    if base != "http://127.0.0.1:8080":
        raise ValueError("Only disposable E1 loopback service is supported")
    with build_opener(ProxyHandler({})).open(
        f"{base}/api/snapshots/{args.first}", timeout=10
    ) as response:
        source = json.loads(response.read())
    cases = []
    with browser_session(sync_playwright) as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        # Hold an actual transport request without manufacturing an API response.
        pending = []
        context.route("**/api/health", lambda route: pending.append(route))
        with page.expect_request("**/api/health"):
            page.goto(base, wait_until="domcontentloaded")
        expect(page.get_by_text("Connecting to backend…", exact=True)).to_be_visible()
        assert len(pending) == 1
        pending.pop().continue_()
        expect(page.get_by_text("Backend connected", exact=True)).to_be_visible()
        cases.append("in-flight backend request exposes loading state")
        context.close()

        context = browser.new_context()
        context.route("**/api/health", lambda route: route.abort())
        page = context.new_page()
        page.goto(base, wait_until="networkidle")
        expect(
            page.get_by_text(
                "Backend unavailable. Check that the API is running.", exact=True
            )
        ).to_be_visible()
        cases.append("failed backend request exposes actionable unavailable state")
        context.close()

        context = browser.new_context()
        page = context.new_page()
        page.goto(base, wait_until="networkidle")
        page.get_by_role("button", name="Discovery & history", exact=True).click()
        page.get_by_role("button", name="Historical analysis", exact=True).click()
        page.get_by_label("Historical satellite NORAD ID").fill("99999")
        page.get_by_role("button", name="Analyze archived history", exact=True).click()
        expect(
            page.get_by_text(
                "No archived records found for this NORAD identifier.", exact=True
            )
        ).to_be_visible()
        cases.append("real empty history response renders without invented records")
        context.close()

        query = {
            "v": "1",
            "mode": "snapshot",
            "frame": "TEME",
            "catalog": source["catalog_id"],
            "snapshot": source["id"],
            "epoch": source["orbital_epoch"],
            "retrieved": source["retrieved_at"],
            "sha": source["response_sha256"],
        }
        context = browser.new_context()
        page = context.new_page()
        page.goto(
            base + "/#/investigation?" + urlencode(query), wait_until="networkidle"
        )
        page.route("**/api/investigation-reports?*", lambda route: route.abort())
        page.get_by_role(
            "button", name="Generate investigation report", exact=True
        ).click()
        expect(page.get_by_role("alert")).to_be_visible()
        retry = page.get_by_role("button", name="Retry report generation", exact=True)
        expect(retry).to_be_enabled()
        page.unroute("**/api/investigation-reports?*")
        retry.click()
        expect(
            page.get_by_role("button", name="Download JSON evidence", exact=True)
        ).to_be_visible(timeout=30000)
        cases.append("failed export generation exposes retry and recovers on real API")
        context.close()
        browser.close()

        browser = p.chromium.launch(
            headless=True, args=["--disable-webgl", "--disable-webgl2"]
        )
        context = browser.new_context()
        page = context.new_page()
        query.update(
            mode="ground-track",
            frame="ITRS",
            at=source["orbital_epoch"],
            start=source["orbital_epoch"],
            duration_minutes=2,
            step_seconds=60,
            selected_index=0,
        )
        page.goto(
            base + "/#/investigation?" + urlencode(query), wait_until="networkidle"
        )
        expect(
            page.get_by_text(
                "3D graphics are unavailable. The 2D map, timeline and "
                "coordinate information remain usable.",
                exact=True,
            )
        ).to_be_visible(timeout=30000)
        assert not page.evaluate(
            "!!document.createElement('canvas').getContext('webgl2')"
        )
        cases.append(
            "disabled WebGL shows explicit 2D fallback; no rendering pass claimed"
        )
        context.close()
        browser.close()
    Path("/results/evidence.json").write_text(
        json.dumps(
            {
                "cases": cases,
                "fault_injection": "paused/aborted transport and disabled WebGL; "
                "no mock API responses",
                "scientific_observations": 0,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
