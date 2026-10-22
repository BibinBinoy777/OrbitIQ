"""Loopback observation UI checks; fixture mode uses synthetic records only."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--engine", choices=["chromium", "firefox", "webkit"], required=True
    )
    parser.add_argument("--mode", choices=["empty", "fixture"], required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        urlsplit(args.base_url).hostname not in {"127.0.0.1", "localhost"}
        or urlsplit(args.base_url).scheme != "http"
    ):
        raise ValueError("Explicit loopback service required")
    errors, violations, requests, cases = [], [], [], []
    with sync_playwright() as p:
        options = {"headless": True}
        if args.engine == "chromium":
            options["args"] = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
        browser = getattr(p, args.engine).launch(**options)
        page = browser.new_page(
            viewport={"width": 1440, "height": 1000}, accept_downloads=True
        )
        page.on("pageerror", lambda e: errors.append(str(e)))
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
        page.goto(args.base_url, wait_until="networkidle")
        page.get_by_role("button", name="Discovery & history", exact=True).click()
        page.get_by_role("button", name="Observation validation", exact=True).click()
        page.get_by_role(
            "button", name="Inspect available validation evidence", exact=True
        ).click()
        if args.mode == "empty":
            expect(
                page.get_by_text(
                    "No observation validation archive is configured.", exact=False
                )
            ).to_be_visible()
            expect(
                page.get_by_label("Captured prediction / observation run")
            ).to_have_count(0)
            cases.append(
                "genuine archive with zero observations exposes "
                "no fabricated selection/results"
            )
        else:
            if not args.run_id:
                raise ValueError("Explicit synthetic run required")
            page.get_by_label("Captured prediction / observation run").select_option(
                args.run_id
            )
            page.get_by_role(
                "button", name="Open captured validation", exact=True
            ).click()
            expect(
                page.get_by_role("heading", name="Captured validation · NORAD 6251")
            ).to_be_visible()
            expect(
                page.get_by_text("2 requested records;", exact=False)
            ).to_contain_text("0 independently verified observations")
            expect(
                page.get_by_role("rowheader", name="SYNTHETIC-ONLY-0", exact=True)
            ).to_be_visible()
            cases.append(
                "controlled synthetic discrepancies retain "
                "zero verified-independence count"
            )
            page.get_by_text(
                "Source, prediction, compatibility and uncertainty evidence", exact=True
            ).click()
            expect(
                page.locator(".historical-analysis details").first.locator("pre")
            ).to_contain_text("unverified_input_lineage")
            cases.append(
                "source/prediction metadata, compatibility checks, "
                "residual and uncertainty inspectable"
            )
            before = len(requests)
            with page.expect_download() as download:
                page.get_by_role(
                    "button",
                    name="Export captured observation validation JSON",
                    exact=True,
                ).click()
            filename = args.output.with_suffix(".export.json")
            download.value.save_as(filename)
            value = json.loads(filename.read_bytes())
            assert (
                value["report_id"] == args.run_id
                and value["summary"]["independently_verified_count"] == 0
            )
            assert value["samples"][0]["residual"]["magnitude_km"] == 5
            assert len(requests) == before
            cases.append("JSON export matches captured result without recalculation")
        for width, height in [(390, 844), (820, 1180), (1440, 1000)]:
            page.set_viewport_size({"width": width, "height": height})
            assert page.evaluate(
                "document.documentElement.scrollWidth<=window.innerWidth+1"
            )
        page.get_by_role(
            "button", name="Inspect available validation evidence", exact=True
        ).focus()
        assert (
            page.evaluate("document.activeElement.textContent")
            == "Inspect available validation evidence"
        )
        cases.append("responsive overflow and native keyboard focus")
        assert not errors and not violations, {
            "errors": errors,
            "violations": violations,
        }
        assert all(r["method"] == "GET" for r in requests)
        args.output.write_text(
            json.dumps(
                {
                    "engine": args.engine,
                    "version": browser.version,
                    "mode": args.mode,
                    "cases": cases,
                    "errors": errors,
                    "csp_violations": violations,
                    "requests": requests,
                    "scientific_observations_used": 0,
                },
                indent=2,
            )
            + "\n"
        )
        browser.close()
    print(json.dumps({"engine": args.engine, "mode": args.mode, "cases": len(cases)}))


if __name__ == "__main__":
    main()
