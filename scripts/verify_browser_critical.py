"""Critical actual-API workflows; explicitly select test archive IDs and engine.

Requires Playwright 1.62 and its browser dependencies (deploy/Dockerfile.browser).
No source ingestion, orbital fixture insertion or API/canvas mocking occurs.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from urllib.request import ProxyHandler, build_opener

from browser_diagnostics import browser_session
from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--engine", choices=["chromium", "firefox", "webkit"], required=True
    )
    parser.add_argument("--catalog", type=int, required=True)
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--second", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("This test runner requires an explicitly local test service")
    opener = build_opener(ProxyHandler({}))

    def get(path):
        with opener.open(base + path, timeout=10) as response:
            return json.loads(response.read(262144))

    sources = [get(f"/api/snapshots/{sid}") for sid in [args.first, args.second]]
    assert all(s["catalog_id"] == args.catalog for s in sources)
    at = sources[1]["orbital_epoch"]
    errors, violations, requests, cases = [], [], [], []
    with browser_session(sync_playwright) as p:
        launch = {"headless": True}
        if args.engine == "chromium":
            launch["args"] = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
        browser = getattr(p, args.engine).launch(**launch)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})

        def watch(page):
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on(
                "request",
                lambda request: requests.append(
                    {"method": request.method, "url": request.url}
                ),
            )
            page.on(
                "console",
                lambda msg: (
                    violations.append(msg.text)
                    if "Content Security Policy" in msg.text
                    else None
                ),
            )

        def save(actions, title):
            actions.get_by_label("Investigation title", exact=True).fill(title)
            actions.get_by_label("Private local notes (optional)", exact=True).fill(
                "Local-only test note"
            )
            actions.get_by_label("Investigation title", exact=True).press("Enter")
            expect(
                actions.get_by_text(
                    f"Saved “{title}” in this browser. "
                    "Open Saved investigations to reopen it.",
                    exact=True,
                )
            ).to_be_visible()

        def share(actions):
            actions.get_by_role("button", name="Copy share link", exact=True).click()
            value = actions.get_by_label(
                "Shareable investigation link", exact=True
            ).input_value()
            assert "Local-only" not in value and len(value) <= 2048
            return value

        try:
            page = context.new_page()
            watch(page)
            page.goto(base, wait_until="networkidle")
            expect(page.get_by_text("Backend connected", exact=True)).to_be_visible()
            assert page.evaluate("window.isSecureContext")
            page.get_by_role("button", name="Discovery & history", exact=True).click()
            page.get_by_label("Name, NORAD ID or international identifier").fill(
                str(args.catalog)
            )
            page.get_by_role("button", name="Search stored records", exact=True).click()
            page.get_by_role(
                "button", name=f"Inspect snapshot #{args.first}", exact=True
            ).click()
            detail = page.get_by_role(
                "region",
                name=f"Snapshot #{args.first}: fixed source detail",
                exact=True,
            )
            expect(detail).to_be_visible()
            actions = detail.get_by_role(
                "region", name="Save or share snapshot investigation", exact=True
            )
            save(actions, "Browser source")
            source_link = share(actions)
            page.get_by_role("button", name="Saved investigations", exact=True).click()
            page.get_by_role("button", name="Open Browser source", exact=True).click()
            expect(
                page.get_by_text("Investigation inputs restored:", exact=False)
            ).to_be_visible()
            page.reload(wait_until="networkidle")
            expect(
                page.get_by_role(
                    "heading",
                    name="Shared investigation · read-only inputs",
                    exact=True,
                )
            ).to_be_visible()
            expect(page.get_by_label("Saved snapshot")).to_be_disabled()
            assert (
                len(
                    json.loads(
                        page.evaluate(
                            'localStorage.getItem("orbitiq.saved-investigations.v1")'
                        )
                    )["records"]
                )
                == 1
            )
            cases.append(
                {
                    "case": "discovery, keyboard save, exact reopen and sharing",
                    "status": "PASS",
                }
            )
            page.get_by_role(
                "button", name="Explore an editable copy", exact=True
            ).click()
            track = page.get_by_role(
                "region", name="Earth-relative ground track", exact=True
            )
            track.get_by_label("Duration (minutes)", exact=True).fill("2")
            track.get_by_label("Sample step (seconds)", exact=True).fill("60")
            track.get_by_role(
                "button", name="Generate ground track", exact=True
            ).click()
            expect(
                track.get_by_text(
                    "3 calculated samples · TEME → ITRS → WGS84", exact=True
                )
            ).to_be_visible()
            track.get_by_role("button", name="Next sample", exact=True).click()
            expect(
                track.get_by_label("Selected track sample", exact=True)
            ).to_have_value("1")
            action = track.get_by_role(
                "region", name="Save or share ground-track investigation", exact=True
            )
            save(action, "Browser track")
            track_link = share(action)
            cases.append(
                {
                    "case": "actual backend track and selected sample saved",
                    "status": "PASS",
                }
            )
            page.get_by_role("button", name="Discovery & history", exact=True).click()
            page.get_by_label("Name, NORAD ID or international identifier").fill(
                str(args.catalog)
            )
            page.get_by_role("button", name="Search stored records", exact=True).click()
            page.get_by_role(
                "button", name=f"Use #{args.first} as A", exact=True
            ).click()
            page.get_by_role(
                "button", name=f"Use #{args.second} as B", exact=True
            ).click()
            page.get_by_role("button", name="Compare snapshots", exact=True).click()
            page.get_by_label(
                "Common evaluation time (optional, explicit timezone)", exact=True
            ).fill(at)
            page.get_by_label("State frame").select_option("ITRS")
            page.get_by_role(
                "button", name="Compare selected snapshots", exact=True
            ).click()
            expect(
                page.get_by_role(
                    "heading", name="Common-time calculated states · ITRS", exact=True
                )
            ).to_be_visible()
            comparison_link = share(
                page.get_by_role(
                    "region", name="Save or share comparison investigation", exact=True
                )
            )
            cases.append(
                {
                    "case": "exact A/B historical common-time ITRS comparison",
                    "status": "PASS",
                    "source_ids": [args.first, args.second],
                    "at": at,
                }
            )
            page.get_by_role(
                "button", name="Scientific-data readiness", exact=True
            ).click()
            expect(
                page.get_by_role(
                    "heading", name="Scientific-data readiness", exact=True
                )
            ).to_be_visible()
            cases.append({"case": "actual readiness dashboard", "status": "PASS"})
            context.close()
            context = browser.new_context(
                viewport={"width": 390, "height": 844}, reduced_motion="reduce"
            )
            page = context.new_page()
            watch(page)
            page.goto(track_link, wait_until="networkidle")
            expect(
                page.get_by_label("Selected track sample", exact=True)
            ).to_have_value("1")
            expect(page.get_by_role("button", name="Play", exact=True)).to_be_disabled()
            expect(page.get_by_label("Duration (minutes)", exact=True)).to_be_disabled()
            assert (
                page.evaluate('localStorage.getItem("orbitiq.saved-investigations.v1")')
                is None
            )
            slider = page.get_by_label("Calculated sample", exact=True)
            slider.focus()
            page.keyboard.press("ArrowRight")
            expect(slider).to_have_value("2")
            canvas = page.locator("canvas")
            rendered = canvas.count() > 0 and canvas.is_visible()
            if rendered:
                assert canvas.evaluate('(c)=>!!c.getContext("webgl2")')
            else:
                expect(
                    page.get_by_text(
                        "3D graphics are unavailable. The 2D map, timeline and "
                        "coordinate information remain usable.",
                        exact=True,
                    )
                ).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            cases.append(
                {
                    "case": "mobile recipient, reduced motion, keyboard, graphics",
                    "status": "PASS",
                    "webgl2_rendered": rendered,
                    "physical_device": False,
                }
            )
            page.goto(comparison_link, wait_until="networkidle")
            expect(
                page.get_by_role(
                    "heading", name="Common-time calculated states · ITRS", exact=True
                )
            ).to_be_visible()
            expect(page.get_by_label("State frame")).to_be_disabled()
            cases.append(
                {
                    "case": "shared comparison restores read-only definition",
                    "status": "PASS",
                }
            )
            parts = urlsplit(source_link)
            params = parse_qs(parts.fragment.split("?", 1)[1])
            params["snapshot"] = ["999999"]
            invalid = urlunsplit(
                (
                    parts.scheme,
                    parts.netloc,
                    parts.path,
                    parts.query,
                    "/investigation?" + urlencode({k: v[0] for k, v in params.items()}),
                )
            )
            page.goto(invalid, wait_until="networkidle")
            expect(page.get_by_role("alert")).to_contain_text(
                "missing from this archive"
            )
            cases.append(
                {
                    "case": "missing source disclosed without replacement",
                    "status": "PASS",
                }
            )
            assert not errors and not violations
            assert all(
                r["method"] == "GET" and r["url"].startswith(base) for r in requests
            )
            result = {
                "status": "PASS",
                "engine": args.engine,
                "browser_version": browser.version,
                "checked_at_utc": datetime.now(UTC).isoformat(),
                "cases": cases,
                "requests": len(requests),
                "page_errors": errors,
                "csp_violations": violations,
                "source_hashes": [s["response_sha256"] for s in sources],
                "api_mocked": False,
                "canvas_mocked": False,
            }
            args.output.write_text(json.dumps(result, indent=2) + "\n")
            print(
                json.dumps(
                    {"status": "PASS", "engine": args.engine, "cases": len(cases)}
                )
            )
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
