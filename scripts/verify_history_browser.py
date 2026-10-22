"""Actual loopback historical-analysis UI checks; no API/canvas mocks or ingestion.

Use a separate read-only archive and explicit known catalog/IDs. Declare --fixture
for synthetic CI inputs; default operator mode expects genuine retained history.
Requires the existing provisioned Playwright browser image.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

from browser_diagnostics import browser_session
from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--catalog", type=int, required=True)
    parser.add_argument(
        "--engine", choices=["chromium", "firefox", "webkit"], required=True
    )
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    base, out = args.base_url.rstrip("/"), args.output_directory
    if urlsplit(base).scheme != "http" or urlsplit(base).hostname not in {
        "127.0.0.1",
        "localhost",
    }:
        raise ValueError("Explicit loopback test service required")
    out.mkdir(parents=True, exist_ok=False)
    opener = build_opener(ProxyHandler({}))
    with opener.open(
        f"{base}/api/historical-analysis?catalog_id={args.catalog}", timeout=30
    ) as response:
        expected = json.loads(response.read(4 * 1024 * 1024))
    assert expected["coverage"]["complete_anchored_history"]
    assert len(expected["points"]) == 2, (
        "This bounded rehearsal requires exactly two archived records"
    )
    ids = [p["metadata"]["id"] for p in expected["points"]]
    cases, errors, violations, requests = [], [], [], []
    with browser_session(sync_playwright) as p:
        options = {"headless": True}
        if args.engine == "chromium":
            options["args"] = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
        browser = getattr(p, args.engine).launch(**options)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000}, accept_downloads=True
        )
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request", lambda r: requests.append({"method": r.method, "url": r.url})
        )
        page.on(
            "console",
            lambda m: (
                violations.append(m.text)
                if "Content Security Policy" in m.text
                else None
            ),
        )
        page.goto(base, wait_until="networkidle")
        page.get_by_role("button", name="Discovery & history", exact=True).click()
        page.get_by_role("button", name="Historical analysis", exact=True).click()
        page.get_by_label("Historical satellite NORAD ID").fill(str(args.catalog))
        page.get_by_role("button", name="Analyze archived history", exact=True).click()
        expect(
            page.get_by_role(
                "heading", name=f"Historical coverage · NORAD {args.catalog}"
            )
        ).to_be_visible()
        expect(page.locator(".history-points > li")).to_have_count(2)
        expect(page.locator(".historical-analysis .notice")).to_contain_text(
            "only pairwise changes"
        )
        for source in expected["points"]:
            expect(
                page.locator(".history-points").get_by_text(
                    source["reference"]["response_sha256"], exact=True
                )
            ).to_be_visible()
        cases.append(
            "two archived source points, identities, clocks and pairwise limitation"
        )
        page.get_by_text(
            f"Inspect archived orbital elements #{ids[0]}", exact=True
        ).click()
        table = page.get_by_role("region", name=f"Snapshot {ids[0]} element values")
        expect(table).to_be_visible()
        for field in ["INCLINATION", "ECCENTRICITY", "MEAN_MOTION"]:
            row = table.get_by_role("row").filter(
                has=page.get_by_role("rowheader", name=field, exact=True)
            )
            expect(row).to_contain_text(str(expected["points"][0]["elements"][field]))
        cases.append("actual normalized element fields and authoritative units")
        change = next(
            f
            for f in expected["findings"]
            if f["rule_id"] == "history.element_change"
            and f["inputs"]["field"] == "MEAN_MOTION"
        )
        details = page.locator(".historical-analysis details").filter(
            has=page.get_by_text(change["title"] + " · informational", exact=True)
        )
        details.locator("summary").click()
        expect(details).to_contain_text(change["explanation"])
        for ref in change["sources"]:
            expect(details.locator("pre")).to_contain_text(ref["response_sha256"])
        cases.append(
            "deterministic explanation with exact payload and calculation references"
        )
        count_before = len(
            [r for r in requests if "/api/historical-analysis?" in r["url"]]
        )
        with page.expect_download() as download:
            page.get_by_role(
                "button", name="Export historical analysis JSON", exact=True
            ).click()
        target = out / "history.json"
        download.value.save_as(target)
        exported = json.loads(target.read_bytes())
        assert exported["coverage"]["validated_record_count"] == 2
        assert (
            exported["sources"] == expected["sources"]
            and exported["limitations"] == expected["limitations"]
        )
        assert (
            len([r for r in requests if "/api/historical-analysis?" in r["url"]])
            == count_before
        )
        with page.expect_download() as recipe:
            page.get_by_role(
                "button",
                name="Download existing replay capture definition pair-"
                + str(ids[0])
                + "-"
                + str(ids[1]),
                exact=True,
            ).click()
        recipe.value.save_as(out / "capture-definition.json")
        assert (
            json.loads((out / "capture-definition.json").read_bytes())
            == expected["comparisons"][0]["evidence"]["definition"]
        )
        cases.append(
            "captured JSON export and uncaptured replay recipe without recalculation"
        )
        page.get_by_label("Timeline page size").select_option("1")
        page.get_by_role("button", name="Analyze archived history", exact=True).click()
        expect(page.locator(".history-points > li")).to_have_count(1)
        expect(page.locator(".historical-analysis")).to_contain_text("Partial window")
        page.get_by_role("button", name="Next timeline page", exact=True).click()
        expect(page.locator(".history-points h5")).to_contain_text(f"#{ids[0]}")
        expect(
            page.get_by_role("button", name="Next timeline page", exact=True)
        ).to_be_disabled()
        page.get_by_role("button", name="Previous timeline page", exact=True).click()
        expect(page.locator(".history-points h5")).to_contain_text(f"#{ids[1]}")
        cases.append(
            "stable anchored pagination next/previous without "
            "duplicated or invented points"
        )
        page.get_by_label("Timeline page size").select_option("20")
        page.get_by_role("button", name="Analyze archived history", exact=True).click()
        expect(page.locator(".history-points > li")).to_have_count(2)
        for width, height in [(390, 844), (820, 1180), (1440, 1000)]:
            page.set_viewport_size({"width": width, "height": height})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth + 1"
            ), width
            page.get_by_role(
                "button", name="Export historical analysis JSON", exact=True
            ).focus()
            assert (
                page.evaluate("document.activeElement?.textContent")
                == "Export historical analysis JSON"
            )
            # WebKit screenshots inject inline CSS (see existing report harness).
            # Keep application CSP intact; layout/focus checks run in every engine.
            if args.engine != "webkit":
                page.screenshot(
                    path=str(out / f"history-{width}.png"),
                    full_page=True,
                    caret="initial",
                )

        cases.append(
            "responsive desktop/tablet/mobile layout, keyboard focus "
            "and labelled regions"
        )
        page.get_by_role(
            "button", name="Open selected historical comparison", exact=True
        ).click()
        page.get_by_role(
            "button", name="Compare selected snapshots", exact=True
        ).click()
        expect(
            page.get_by_role("rowheader", name="MEAN_MOTION · rev/day", exact=True)
        ).to_be_visible()
        cases.append("navigation to existing comparison service")
        page.get_by_role("button", name="Historical analysis", exact=True).click()
        # Returning remounts the form with its product default (25544). Use the
        # explicit test catalog again, including non-ISS public CI fixtures.
        page.get_by_label("Historical satellite NORAD ID").fill(str(args.catalog))
        page.get_by_role("button", name="Analyze archived history", exact=True).click()
        expect(page.locator(".history-points > li")).to_have_count(2)
        page.get_by_role(
            "button", name=f"Open existing snapshot detail #{ids[0]}", exact=True
        ).click()
        expect(
            page.get_by_role(
                "heading", name=f"Snapshot #{ids[0]}: fixed source detail", exact=True
            )
        ).to_be_visible()
        cases.append("navigation to existing snapshot detail")
        (out / "diagnostics.json").write_text(
            json.dumps(
                {"errors": errors, "violations": violations, "requests": requests},
                indent=2,
            )
        )
        assert not errors and not violations, {
            "errors": errors,
            "violations": violations,
        }
        assert all(r["method"] == "GET" for r in requests)
        evidence = {
            "engine": args.engine,
            "browser_version": browser.version,
            "screenshots_captured": args.engine != "webkit",
            "recorded_at": datetime.now(UTC).isoformat(),
            "cases": cases,
            "page_errors": errors,
            "csp_violations": violations,
            "requests": requests,
            "fixture_inputs": args.fixture,
            "fixture_sources" if args.fixture else "genuine_sources": expected[
                "sources"
            ],
            "no_ingestion_requests": True,
            "accessibility_scope": (
                "Semantic native controls, visible focus and responsive overflow; "
                "not a full screen-reader/WCAG audit"
            ),
        }
        (out / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
        context.close()
        browser.close()
    print(
        json.dumps({"engine": args.engine, "cases": len(cases), "errors": len(errors)})
    )


if __name__ == "__main__":
    main()
