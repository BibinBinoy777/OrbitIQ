"""Expected-failure diagnostic probe, never counted as a passing product flow."""

import argparse

from browser_diagnostics import browser_session
from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external", action="store_true")
    args = parser.parse_args()
    with browser_session(sync_playwright) as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("http://127.0.0.1:8080", wait_until="networkidle")
        if args.external:
            page.goto("https://example.invalid/e1-probe")
        else:
            expect(
                page.get_by_text("E1 INTENTIONAL MISSING ELEMENT", exact=True)
            ).to_be_visible(timeout=1000)


if __name__ == "__main__":
    main()
