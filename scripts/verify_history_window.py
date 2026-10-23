"""E7 isolated history fault-injection checks, separate from the unmapped API flow.

Use only public/synthetic loopback fixtures. Transport and wrong-window injections
are explicit; successful recovery and captured export use the actual backend.
"""

import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect

CASES = {
    "initial_retry",
    "next_retry",
    "previous_retry",
    "wrong_window_refused",
    "captured_export",
    "input_clears_retry",
    "keyboard_layout",
}


def verify_window(
    browser, base, catalog, full, out, axe_script=Path("/opt/axe/axe.min.js")
):
    context = browser.new_context(
        viewport={"width": 1440, "height": 1000}, accept_downloads=True
    )
    page = context.new_page()
    requests, errors, checks, audits, layouts = [], [], [], [], []
    page.on("request", lambda r: requests.append({"method": r.method, "url": r.url}))
    page.on("pageerror", lambda e: errors.append(str(e)))
    pattern = "**/api/historical-analysis?*"

    def urls():
        return [r["url"] for r in requests if "/api/historical-analysis?" in r["url"]]

    def click(name):
        page.get_by_role("button", name=name, exact=True).click()

    def loaded():
        expect(
            page.get_by_role("heading", name=f"Historical coverage · NORAD {catalog}")
        ).to_be_visible()
        expect(page.locator(".history-points > li")).to_have_count(1)
        expect(page.locator(".historical-analysis")).to_contain_text("Partial window:")

    def absent():
        expect(page.get_by_role("alert")).to_be_visible()
        expect(
            page.get_by_role("heading", name=f"Historical coverage · NORAD {catalog}")
        ).to_have_count(0)
        expect(
            page.get_by_role(
                "button", name="Export historical analysis JSON", exact=True
            )
        ).to_have_count(0)
        expect(page.locator(".history-points > li")).to_have_count(0)

    def audit(name):
        page.evaluate(axe_script.read_text())
        result = page.evaluate("""async () => { const r=await axe.run(document,
          {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});
          return {violations:r.violations.map(v=>v.id),
                  incomplete:r.incomplete.map(v=>v.id)}; }""")
        assert not result["violations"], result
        audits.append({"view": name, **result})

    def transport_failure(name):
        page.route(pattern, lambda route: route.fulfill(status=503, body="Unavailable"))
        click(name)
        absent()
        failed = urls()[-1]
        page.unroute(pattern)
        with page.expect_response(
            lambda r: "/api/historical-analysis?" in r.url and r.status == 200
        ) as response:
            retry = page.get_by_role(
                "button", name="Retry historical analysis", exact=True
            )
            retry.focus()
            retry.press("Enter")
        loaded()
        assert urls()[-1] == failed, (urls()[-1], failed)
        return response.value.json()

    try:
        page.goto(base, wait_until="networkidle")
        original = page.evaluate("JSON.stringify(localStorage)")
        click("Discovery & history")
        click("Historical analysis")
        page.get_by_label("Historical satellite NORAD ID").fill(str(catalog))
        page.get_by_label("Timeline page size").select_option("1")
        first = transport_failure("Analyze archived history")
        assert first["request"]["limit"] == 1 and first["request"]["before_id"] is None
        checks.append({"case": "initial_retry", "status": "PASS"})
        older = transport_failure("Next timeline page")
        assert older["request"]["anchor_id"] == first["pagination"]["anchor_id"]
        assert older["request"]["before_id"] == first["pagination"]["next_before_id"]
        expect(
            page.get_by_role("button", name="Next timeline page", exact=True)
        ).to_be_disabled()
        checks.append({"case": "next_retry", "status": "PASS"})
        previous = transport_failure("Previous timeline page")
        assert previous["request"] == first["request"]
        assert parse_qs(urlsplit(urls()[-1]).query)["anchor_id"] == [
            str(first["pagination"]["anchor_id"])
        ]
        expect(
            page.get_by_role("button", name="Previous timeline page", exact=True)
        ).to_be_disabled()
        checks.append({"case": "previous_retry", "status": "PASS"})
        # Valid same-catalog report for an entirely different window must be refused.
        page.route(pattern, lambda route: route.fulfill(status=200, json=full))
        click("Analyze archived history")
        absent()
        expect(page.get_by_role("alert")).to_contain_text("bounded contract")
        audit("wrong-window error")
        failed = urls()[-1]
        checks.append({"case": "wrong_window_refused", "status": "PASS"})
        page.unroute(pattern)
        with page.expect_response(
            lambda r: "/api/historical-analysis?" in r.url and r.status == 200
        ) as response:
            click("Retry historical analysis")
        captured = response.value.json()
        loaded()
        assert urls()[-1] == failed
        assert captured["request"] == first["request"]
        count = len(urls())
        with page.expect_download() as download:
            export = page.get_by_role(
                "button", name="Export historical analysis JSON", exact=True
            )
            export.focus()
            export.press("Enter")
        target = out / "selected-window.json"
        download.value.save_as(target)
        assert json.loads(target.read_bytes()) == captured
        assert len(urls()) == count, (
            "Export must use the capture without another request"
        )
        checks.append({"case": "captured_export", "status": "PASS"})
        audit("recovered partial window")
        for width in (320, 1440):
            page.set_viewport_size({"width": width, "height": 1000})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= innerWidth + 1"
            )
            export.focus()
            assert export.evaluate("e=>e===document.activeElement")
            layouts.append({"width": width, "status": "PASS"})
        checks.append({"case": "keyboard_layout", "status": "PASS"})
        page.route(pattern, lambda route: route.fulfill(status=503, body="Unavailable"))
        click("Analyze archived history")
        absent()
        page.get_by_label("Timeline page size").select_option("2")
        expect(page.get_by_role("alert")).to_have_count(0)
        expect(
            page.get_by_role("button", name="Retry historical analysis", exact=True)
        ).to_have_count(0)
        page.unroute(pattern)
        click("Analyze archived history")
        expect(page.locator(".history-points > li")).to_have_count(2)
        checks.append({"case": "input_clears_retry", "status": "PASS"})
        assert {c["case"] for c in checks} == CASES
        assert not errors and all(r["method"] == "GET" for r in requests)
        assert page.evaluate("JSON.stringify(localStorage)") == original
        return {
            "status": "PASS",
            "cases": checks,
            "page_errors": errors,
            "no_network_writes": True,
            "browser_storage_unchanged": True,
            "fault_injection": (
                "Separate context: transport 503 and same-catalog wrong-window response"
            ),
            "accessibility": audits,
            "layouts": layouts,
            "download": {
                "file": target.name,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            },
            "captured_request": captured["request"],
        }
    finally:
        context.close()
