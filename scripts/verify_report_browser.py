"""Actual local report downloads, shared inputs and print layout; no API mocking.

Run inside deploy/Dockerfile.browser with a separately restored read-only archive.
Chromium also writes PDFs for external text/pagination checks; other engines check
print CSS and downloads, not their native print dialogs or native PDF generation.
"""

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic
from urllib.parse import urlencode, urlsplit
from urllib.request import ProxyHandler, build_opener

from browser_diagnostics import browser_session
from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--engine", choices=["chromium", "firefox", "webkit"], required=True
    )
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--second", type=int, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--maximum-track", action="store_true")
    args = parser.parse_args()
    base, output = args.base_url.rstrip("/"), args.output_directory
    assert urlsplit(base).hostname in {"127.0.0.1", "localhost"}
    assert urlsplit(base).scheme == "http"
    output.mkdir(parents=True, exist_ok=True)
    opener = build_opener(ProxyHandler({}))

    def source(sid):
        with opener.open(f"{base}/api/snapshots/{sid}", timeout=10) as response:
            s = json.loads(response.read())
        return {
            "snapshot_id": s["id"],
            **{
                k: s[k]
                for k in (
                    "catalog_id",
                    "orbital_epoch",
                    "retrieved_at",
                    "response_sha256",
                )
            },
        }

    a, b = source(args.first), source(args.second)

    def link(d):
        q = {"v": "1", "mode": d["mode"], "frame": d["frame"]}
        for ref, prefix in [(a, "")] + (
            [(b, "b_")] if d["mode"] == "comparison" else []
        ):
            for key, field in [
                ("catalog", "catalog_id"),
                ("snapshot", "snapshot_id"),
                ("epoch", "orbital_epoch"),
                ("retrieved", "retrieved_at"),
                ("sha", "response_sha256"),
            ]:
                q[prefix + key] = ref[field]
        if "at" in d:
            q["at"] = d["at"]
        if d["mode"] == "comparison":
            q["category"] = "all"
        if "track" in d:
            q.update(d["track"])
        return base + "/#/investigation?" + urlencode(q)

    def shifted(value, seconds):
        return (
            (
                datetime.fromisoformat(value.replace("Z", "+00:00"))
                + timedelta(seconds=seconds)
            )
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

    definitions = [
        {"mode": "snapshot", "frame": "TEME"},
        {"mode": "position", "frame": "TEME", "at": a["orbital_epoch"]},
        {
            "mode": "ground-track",
            "frame": "ITRS",
            "at": shifted(a["orbital_epoch"], 60),
            "track": {
                "start": a["orbital_epoch"],
                "duration_minutes": 2,
                "step_seconds": 60,
                "selected_index": 1,
            },
        },
        {"mode": "comparison", "frame": "ITRS", "at": b["orbital_epoch"]},
    ]
    if args.maximum_track:
        definitions.append(
            {
                **definitions[2],
                "case_name": "maximum-track",
                "track": {
                    **definitions[2]["track"],
                    "duration_minutes": 360,
                },
            }
        )
    errors, violations, requests, cases = [], [], [], []
    stage = "startup"
    # These dense fixture journeys obey the gateway budget, without response retries.
    with browser_session(sync_playwright, pace_calculations=True) as p:
        options = {"headless": True}
        if args.engine == "chromium":
            options["args"] = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
        browser = getattr(p, args.engine).launch(**options)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000}, accept_downloads=True
        )
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on(
            "request", lambda r: requests.append({"url": r.url, "method": r.method})
        )
        page.on(
            "console",
            lambda m: (
                violations.append(
                    {"message": m.text, "stage": stage, "location": m.location}
                )
                if "Content Security Policy" in m.text
                else None
            ),
        )
        try:
            for d in definitions:
                mode = d["mode"]
                case_name = d.get("case_name", mode)
                page.goto(link(d), wait_until="networkidle")
                expect(
                    page.get_by_role(
                        "heading",
                        name="Shared investigation · read-only inputs",
                        exact=True,
                    )
                ).to_be_visible()
                shared = page.get_by_role(
                    "region", name="Shared investigation · read-only inputs", exact=True
                )
                if mode == "ground-track":
                    expect(
                        shared.get_by_label("Selected track sample", exact=True)
                    ).to_have_value("1", timeout=30000)
                    actions = shared.locator(
                        '[aria-label="Calculated ground-track result"] '
                        ".investigation-report-actions"
                    )
                else:
                    actions = shared.locator(".investigation-report-actions").first
                expect(
                    actions.get_by_role(
                        "button", name="Generate investigation report", exact=True
                    )
                ).to_be_visible()
                started = monotonic()
                actions.get_by_role(
                    "button", name="Generate investigation report", exact=True
                ).click()
                expect(
                    actions.get_by_role(
                        "button", name="Download JSON evidence", exact=True
                    )
                ).to_be_visible(timeout=30000)
                generation_seconds = monotonic() - started
                report_requests = sum(
                    "/api/investigation-reports?" in r["url"] for r in requests
                )
                stage = "JSON download"
                with page.expect_download() as download:
                    actions.get_by_role(
                        "button", name="Download JSON evidence", exact=True
                    ).click()
                json_path = output / f"{args.engine}-{case_name}.json"
                download.value.save_as(json_path)
                report = json.loads(json_path.read_text())
                assert report["status"] == "complete", report["calculation"]["errors"]
                assert report["investigation"]["definition"]["mode"] == mode
                assert (
                    report["sources"][0]["reference"]["snapshot_id"] == a["snapshot_id"]
                )
                assert (
                    report["sources"][0]["payload_hash"]["value"]
                    == a["response_sha256"]
                )
                assert report["investigation"]["description"] is None
                stage = "HTML download"
                with page.expect_download() as download:
                    actions.get_by_role(
                        "button", name="Download printable HTML", exact=True
                    ).click()
                html_path = output / f"{args.engine}-{case_name}.html"
                download.value.save_as(html_path)
                html = html_path.read_text()
                assert report["report_id"] in html and a["response_sha256"] in html
                assert "counter(page)" in html and "Scientific limitations" in html
                stage = "preview"
                actions.get_by_role(
                    "button", name="Open printable report", exact=True
                ).click()
                dialog = page.get_by_role("dialog")
                expect(dialog).to_be_visible()
                expect(
                    dialog.get_by_role(
                        "button", name="Print report / Save as PDF", exact=True
                    )
                ).to_be_focused()
                text = dialog.inner_text()
                assert report["report_id"] in text
                assert report["investigation"]["id"] in text
                assert all(
                    w in text for w in report["warnings"] + report["limitations"]
                )
                for s in report["sources"]:
                    assert s["payload_hash"]["value"] in text
                    assert s["reference"]["orbital_epoch"] in text
                if mode == "position":
                    assert (
                        json.dumps(
                            report["calculation"]["data"]["position_km"],
                            separators=(",", ":"),
                        )
                        in text
                    )
                if mode == "ground-track":
                    assert "Selected sample #1" in text
                    if args.maximum_track and case_name == "maximum-track":
                        assert report["calculation"]["data"]["sample_count"] == 361
                        assert (
                            dialog.get_by_role(
                                "table",
                                name="All returned ITRS track samples",
                                exact=True,
                            )
                            .locator("tbody tr")
                            .count()
                            == 361
                        )
                if mode in {"ground-track", "comparison"}:
                    assert (
                        "measured_or_predicted" in text
                        and "leap_seconds_sha256" in text
                    )
                stage = "print CSS"
                page.emulate_media(media="print")
                assert (
                    page.locator("#root").evaluate("e => getComputedStyle(e).display")
                    == "none"
                )
                assert (
                    dialog.locator("thead").first.evaluate(
                        "e => getComputedStyle(e).display"
                    )
                    == "table-header-group"
                )
                if args.engine == "chromium":
                    page.pdf(
                        path=str(output / f"chromium-{case_name}.pdf"),
                        prefer_css_page_size=True,
                        print_background=True,
                    )
                stage = "screenshot"
                page.emulate_media(media="screen")
                # WebKit's screenshot implementation injects inline CSS even
                # with caret=initial. Keep application CSP intact; other engines
                # capture screenshots and all engines check actual layout/focus.
                if args.engine != "webkit":
                    page.screenshot(
                        path=str(output / f"{args.engine}-{case_name}.png"),
                        caret="initial",
                    )
                stage = "keyboard and mobile"
                page.keyboard.press("Escape")
                expect(dialog).not_to_be_visible()
                expect(
                    actions.get_by_role(
                        "button", name="Open printable report", exact=True
                    )
                ).to_be_focused()
                assert "report-printing" not in page.locator("body").get_attribute(
                    "class"
                )
                assert report_requests == sum(
                    "/api/investigation-reports?" in r["url"] for r in requests
                )
                page.set_viewport_size({"width": 390, "height": 844})
                actions.get_by_role(
                    "button", name="Open printable report", exact=True
                ).click()
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth + 1"
                )
                assert dialog.evaluate("e => e.scrollWidth <= e.clientWidth + 1")
                page.keyboard.press("Escape")
                page.set_viewport_size({"width": 1440, "height": 1000})
                cases.append(
                    {
                        "mode": mode,
                        "case": case_name,
                        "status": "PASS",
                        "report_id": report["report_id"],
                        "json_bytes": json_path.stat().st_size,
                        "html_bytes": html_path.stat().st_size,
                        "generation_seconds": round(generation_seconds, 3),
                    }
                )
            if args.engine == "chromium":
                stage = "saved card"
                page.goto(base, wait_until="networkidle")
                page.get_by_role(
                    "button", name="Discovery & history", exact=True
                ).click()
                page.get_by_label("Name, NORAD ID or international identifier").fill(
                    str(a["catalog_id"])
                )
                page.get_by_role(
                    "button", name="Search stored records", exact=True
                ).click()
                page.get_by_role(
                    "button", name=f"Inspect snapshot #{args.first}", exact=True
                ).click()
                save = page.get_by_role(
                    "region", name="Save or share snapshot investigation", exact=True
                )
                save.get_by_label("Investigation title", exact=True).fill(
                    "Report audit local title"
                )
                save.get_by_label("Private local notes (optional)", exact=True).fill(
                    "PRIVATE_LOCAL_REPORT_TEST_ONLY"
                )
                save.get_by_role(
                    "button", name="Save in this browser", exact=True
                ).click()
                expect(
                    save.get_by_text(
                        "Saved “Report audit local title” in this browser. "
                        "Open Saved investigations to reopen it.",
                        exact=True,
                    )
                ).to_be_visible()
                page.get_by_role(
                    "button", name="Saved investigations", exact=True
                ).click()
                card = page.get_by_role(
                    "article", name="Report audit local title", exact=True
                )
                card.get_by_role(
                    "button", name="Generate investigation report", exact=True
                ).click()
                expect(
                    card.get_by_role(
                        "button", name="Download JSON evidence", exact=True
                    )
                ).to_be_visible(timeout=30000)
                captures = []
                for extension, button in [
                    ("json", "Download JSON evidence"),
                    ("html", "Download printable HTML"),
                ]:
                    with page.expect_download() as downloaded:
                        card.get_by_role("button", name=button, exact=True).click()
                    target = output / f"chromium-saved.{extension}"
                    downloaded.value.save_as(target)
                    content = target.read_text()
                    assert "PRIVATE_LOCAL_REPORT_TEST_ONLY" not in content
                    assert "Report audit local title" not in content
                    captures.append(content)
                captured = json.loads(captures[0])
                assert captured["report_id"] in captures[1]
                card.get_by_role(
                    "button", name="Open printable report", exact=True
                ).click()
                dialog = page.get_by_role("dialog")
                expect(dialog).to_be_visible()
                assert "PRIVATE_LOCAL_REPORT_TEST_ONLY" not in dialog.inner_text()
                page.emulate_media(media="print")
                assert (
                    page.locator("#root").evaluate("e => getComputedStyle(e).display")
                    == "none"
                )
                page.pdf(
                    path=str(output / "chromium-saved.pdf"), prefer_css_page_size=True
                )
                page.emulate_media(media="screen")
                page.keyboard.press("Escape")
                expect(
                    card.get_by_text("PRIVATE_LOCAL_REPORT_TEST_ONLY", exact=True)
                ).to_be_visible()
                cases.append(
                    {
                        "case": "saved-card",
                        "mode": "snapshot",
                        "status": "PASS",
                        "report_id": captured["report_id"],
                        "local_notes_excluded": True,
                    }
                )
            stage = "standalone HTML"
            offline = context.new_page()
            offline.on("pageerror", lambda e: errors.append(str(e)))
            offline_requests = []
            offline.on("request", lambda r: offline_requests.append(r.url))
            offline.goto((output / f"{args.engine}-position.html").as_uri())
            expect(
                offline.get_by_role("article", name="OrbitIQ investigation report")
            ).to_be_visible()
            assert offline.locator("section").count() == 7
            assert (
                offline.locator(".report-sheet").evaluate(
                    "e => getComputedStyle(e).backgroundColor"
                )
                == "rgb(255, 255, 255)"
            )
            assert (
                offline.locator("thead").first.evaluate(
                    "e => getComputedStyle(e).display"
                )
                == "table-header-group"
            )
            assert all(url.startswith("file:") for url in offline_requests)
            if args.engine == "chromium":
                (output / "chromium-position-offline.json").write_bytes(
                    (output / "chromium-position.json").read_bytes()
                )
                offline.pdf(
                    path=str(output / "chromium-position-offline.pdf"),
                    prefer_css_page_size=True,
                )
            offline.close()
            assert not errors and not violations, {
                "page_errors": errors,
                "csp_violations": violations,
            }
            assert all(
                r["method"] == "GET" and r["url"].startswith(base) for r in requests
            )
            result = {
                "status": "PASS",
                "engine": args.engine,
                "browser_version": browser.version,
                "checked_at_utc": datetime.now(UTC).isoformat(),
                "cases": cases,
                "page_errors": errors,
                "csp_violations": violations,
                "api_mocked": False,
                "same_capture_downloads_verified": True,
                "native_pdf_verified": args.engine == "chromium",
                "screenshots_captured": args.engine != "webkit",
                "standalone_html_offline_checked": True,
            }
            (output / f"{args.engine}-results.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            print(json.dumps(result))
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
