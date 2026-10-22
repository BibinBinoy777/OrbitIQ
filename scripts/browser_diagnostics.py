"""Opt-in diagnostics around the existing synchronous Playwright runners.

Only enable for isolated public/synthetic fixtures: traces contain DOM/network
data. Closing contexts saves traces before Playwright shuts down, including when
an existing runner's finally block closes the context during an assertion.
"""

import json
import os
import sys
import traceback
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit


@contextmanager
def browser_session(factory):
    with factory() as playwright:
        destination = os.environ.get("ORBITIQ_BROWSER_DIAGNOSTICS")
        if not destination:
            yield playwright
            return
        from playwright.sync_api import Browser, BrowserContext

        out = Path(destination)
        out.mkdir(parents=True, exist_ok=True)
        contexts, events, denied, finished = [], [], [], set()
        original_new, original_close = Browser.new_context, BrowserContext.close

        def save(context, failed):
            key = id(context)
            if key in finished:
                return
            finished.add(key)
            index = contexts.index(context)
            if failed:
                for number, page in enumerate(context.pages):
                    try:
                        page.screenshot(
                            path=str(out / f"failure-{index}-{number}.png"),
                            caret="initial",
                            timeout=3000,
                        )
                    except Exception as error:
                        events.append({"diagnostic_screenshot_error": str(error)})
            try:
                context.tracing.stop(path=str(out / f"trace-{index}.zip"))
            except Exception as error:
                events.append({"diagnostic_trace_error": str(error)})

        def close(context, **kwargs):
            save(context, sys.exc_info()[0] is not None)
            return original_close(context, **kwargs)

        def new(browser, **kwargs):
            context = original_new(browser, **kwargs)
            contexts.append(context)
            context.tracing.start(screenshots=True, snapshots=True, sources=False)

            def route(request):
                url = request.request.url
                parsed = urlsplit(url)
                if parsed.scheme in {"http", "https"} and parsed.hostname not in {
                    "localhost",
                    "127.0.0.1",
                }:
                    denied.append(url)
                    request.abort("blockedbyclient")
                else:
                    request.continue_()

            context.route("**/*", route)

            def page_watch(page):
                page.on("pageerror", lambda e: events.append({"pageerror": str(e)}))
                page.on(
                    "console",
                    lambda m: (
                        events.append({"console": m.type, "text": m.text})
                        if m.type in {"error", "warning"}
                        else None
                    ),
                )
                page.on(
                    "requestfailed",
                    lambda r: events.append(
                        {"request_failed": r.url, "reason": r.failure}
                    ),
                )

            context.on("page", page_watch)
            return context

        Browser.new_context, BrowserContext.close = new, close
        try:
            yield playwright
            if denied:
                raise AssertionError(
                    "External browser requests forbidden: " + str(denied)
                )
        except BaseException:
            (out / "failure.json").write_text(
                json.dumps(
                    {"status": "FAIL", "error": traceback.format_exc()}, indent=2
                )
                + "\n"
            )
            for context in contexts:
                save(context, True)
            raise
        finally:
            for context in contexts:
                save(context, False)
            (out / "console.json").write_text(
                json.dumps(
                    {"events": events, "denied_external_requests": denied}, indent=2
                )
                + "\n"
            )
            Browser.new_context, BrowserContext.close = original_new, original_close
