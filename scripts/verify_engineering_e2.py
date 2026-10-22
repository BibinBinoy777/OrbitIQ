"""Actual-browser E2 audit; synthetic E1 services only, no scientific evidence.

Timing is informational. Semantic, recovery and resource-lifecycle checks block.
--baseline records defects without asserting they have already been fixed.
"""

import argparse
import atexit
import json
import platform
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, build_opener

from browser_diagnostics import browser_session
from playwright.sync_api import expect, sync_playwright

INSTRUMENT = """() => {
  window.e2 = {contexts: [], draws: 0, uploads: 0};
  const original = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function(...args) {
    const gl = original.apply(this, args);
    if (gl && args[0] === 'webgl2' && !e2.contexts.some(c => c.gl === gl)) {
      e2.contexts.push({gl, canvas: this,
        created_ms:performance.now(), first_draw_ms:null});
      for (const key of ['drawElements', 'drawArrays', 'bufferData']) {
        const fn = gl[key];
        gl[key] = function(...values) {
          if (key === 'bufferData') e2.uploads++; else {
            e2.draws++;
            e2.contexts.find(c=>c.gl===gl).first_draw_ms ??= performance.now();
          }
          return fn.apply(this, values);
        };
      }
    }
    return gl;
  };
}"""

SAMPLE = """async ({interact}) => {
  const canvas = [...document.querySelectorAll('.globe-canvas canvas')]
    .find(c=>c.getBoundingClientRect().width>0);
  const before = {draws: e2.draws, uploads: e2.uploads};
  const start = performance.now(), frames = [];
  let last = start, actions = 0;
  await new Promise(resolve => {
    function tick(now) {
      frames.push(now - last); last = now;
      if (interact && actions < 12) {
        canvas?.dispatchEvent(new KeyboardEvent('keydown',
          {key:'ArrowRight', bubbles:true, cancelable:true}));
        actions++;
      }
      if (now - start < 2000) requestAnimationFrame(tick); else resolve();
    }
    requestAnimationFrame(tick);
  });
  const sorted = frames.slice(1).sort((a,b) => a-b);
  return {duration_ms: performance.now()-start, samples: sorted.length,
    raf_median_ms: sorted[Math.floor(sorted.length*.5)],
    raf_p95_ms: sorted[Math.floor(sorted.length*.95)],
    draw_calls: e2.draws-before.draws, buffer_uploads: e2.uploads-before.uploads,
    actions, heap_bytes: performance.memory?.usedJSHeapSize ?? null};
}"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine", choices=["chromium", "firefox", "webkit"], required=True
    )
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--axe", default="/opt/axe/axe.min.js")
    args = parser.parse_args()
    base = "http://127.0.0.1:8080"
    with build_opener(ProxyHandler({})).open(
        base + "/api/snapshots/1", timeout=10
    ) as r:
        source = json.loads(r.read())
    assert source["catalog_id"] == 6251
    assert source["object_name"] == "E1 SYNTHETIC UI FIXTURE - NOT OBSERVED HISTORY"
    query = dict(
        v=1,
        mode="ground-track",
        frame="ITRS",
        catalog=6251,
        snapshot=1,
        epoch=source["orbital_epoch"],
        retrieved=source["retrieved_at"],
        sha=source["response_sha256"],
        at=source["orbital_epoch"],
        start=source["orbital_epoch"],
        duration_minutes=2,
        step_seconds=60,
        selected_index=0,
    )
    link = base + "/#/investigation?" + urlencode(query)
    result = {
        "engine": args.engine,
        "os": platform.platform(),
        "baseline": args.baseline,
        "fixture": "E1 SYNTHETIC UI FIXTURE - NOT OBSERVED HISTORY",
        "scene": "3 calculated samples from public Vallado 6251 fixture",
        "viewport": {"width": 1440, "height": 1000},
        "dpr": 1,
        "timings": [],
        "accessibility": [],
        "layouts": [],
        "checks": [],
    }
    issues = []
    result["issues"] = issues
    atexit.register(
        lambda: Path("/results/evidence.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
    )

    def check(condition, description):
        result["checks"].append({"check": description, "pass": bool(condition)})
        if not condition:
            issues.append(description)

    with browser_session(sync_playwright) as p:
        browser = getattr(p, args.engine).launch(
            headless=True,
            **(
                {"args": ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]}
                if args.engine == "chromium"
                else {}
            ),
        )
        result["version"] = browser.version
        context = browser.new_context(
            viewport=result["viewport"], device_scale_factor=1
        )
        context.add_init_script("(" + INSTRUMENT + ")()")
        page = context.new_page()
        errors = []
        cpu = context.new_cdp_session(page) if args.engine == "chromium" else None
        if cpu:
            cpu.send("Performance.enable")

        def task_duration():
            if not cpu:
                return None
            return next(
                m["value"]
                for m in cpu.send("Performance.getMetrics")["metrics"]
                if m["name"] == "TaskDuration"
            )

        page.on("pageerror", lambda e: errors.append(str(e)))

        def scan(name):
            page.evaluate(Path(args.axe).read_text())
            data = page.evaluate("""async () => {
              const r = await axe.run(document, {runOnly: {type:'tag',
                values:['wcag2a','wcag2aa','wcag21aa']}});
              return {violations:r.violations.map(v => ({id:v.id,impact:v.impact,
                targets:v.nodes.map(n=>n.target)})),
                incomplete:r.incomplete.map(v=>({id:v.id,
                  targets:v.nodes.map(n=>n.target)})), passes:r.passes.length};
            }""")
            result["accessibility"].append({"view": name, **data})
            check(not data["violations"], "axe WCAG A/AA: " + name)

        # Keyboard access starts at the real document boundary, no mouse clicks.
        page.goto(base, wait_until="networkidle")
        page.keyboard.press("Tab")
        first = page.locator(":focus")
        check(first.inner_text() == "Skip to workspace", "keyboard skip link is first")
        if not args.baseline:
            page.keyboard.press("Enter")
            expect(page.locator("#workspace")).to_be_focused()
        nav = page.get_by_role("button", name="Satellite explorer", exact=True)
        nav.focus()
        color = nav.evaluate("e=>getComputedStyle(e).outlineColor")
        check(
            color == "rgb(255, 215, 130)",
            "current-page keyboard focus remains distinct",
        )
        scan("initial explorer")
        page.get_by_role("button", name="Scientific-data readiness", exact=True).click()
        expect(
            page.get_by_role("heading", name="Scientific-data readiness", exact=True)
        ).to_be_visible()
        scan("readiness")
        page.get_by_role("button", name="Saved investigations", exact=True).click()
        expect(
            page.get_by_role("heading", name="Saved investigations", exact=True)
        ).to_be_visible()
        scan("empty saved investigations")

        for repeat in range(3):
            page.goto(link.replace("/#", f"/?e2={repeat}#"), wait_until="networkidle")
            expect(
                page.get_by_label("Selected track sample", exact=True)
            ).to_have_value("0", timeout=30000)
            page.wait_for_function("""() =>
              document.querySelector('.globe-canvas canvas') ||
              [...document.querySelectorAll('.globe-fallback')].some(e=>e.textContent.includes('unavailable'))""")
            native = page.locator(".globe-canvas canvas:visible").count() > 0
            result["native_webgl2"] = native
            if native:
                # Let texture decoding and ResizeObserver settle before each sample.
                page.wait_for_function("""() => performance.getEntriesByType('resource')
                  .some(e=>e.name.endsWith('earth-atmosphere.jpg'))""")
                ready_ms = page.evaluate("performance.now()")
                init = page.evaluate(
                    """() => e2.contexts.filter(c=>c.canvas.isConnected)
                      .map(c=>({context_created_ms:c.created_ms,
                        first_draw_ms:c.first_draw_ms}))"""
                )
                gl = page.evaluate("""() => {
                  const gl=e2.contexts.at(-1).gl;
                  const ext=gl.getExtension('WEBGL_debug_renderer_info');
                  return {version:gl.getParameter(gl.VERSION), renderer:ext ?
                    gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'unavailable'};
                }""")
                result["graphics"] = gl
                cpu_before = task_duration()
                result["timings"].append(
                    {
                        "repeat": repeat,
                        "observed_ready_ms": ready_ms,
                        "initialization": init,
                        "stable": page.evaluate(SAMPLE, {"interact": False}),
                        "interaction": page.evaluate(SAMPLE, {"interact": True}),
                    }
                )
                cpu_after = task_duration()
                result["timings"][-1]["main_thread_task_seconds"] = (
                    cpu_after - cpu_before if cpu else None
                )
            else:
                result["fallback"] = page.locator(
                    ".globe-fallback:visible"
                ).inner_text()
        if result["timings"]:
            check(
                all(t["interaction"]["draw_calls"] > 0 for t in result["timings"]),
                "real camera interactions draw frames",
            )
            # Idle scene is demand-rendered; no hardware-dependent timing gate.
            check(
                all(t["stable"]["draw_calls"] == 0 for t in result["timings"]),
                "settled globe performs no idle draw calls",
            )
        scan("shared calculated ground track")
        result["loaded_assets"] = (
            page.evaluate("""() => performance.getEntriesByType('resource')
          .filter(e=>e.name.includes('/assets/')).map(e=>({
            name:e.name.split('/').at(-1), bytes:e.decodedBodySize}))""")
        )
        # Same-document navigation removes restored scenes; verify context release.
        for _ in range(3):
            page.evaluate("location.hash='' ")
            expect(page.get_by_label("Catalog ID", exact=True)).to_be_visible()
            page.evaluate("hash => location.hash=hash", link.split("#", 1)[1])
            expect(
                page.get_by_label("Selected track sample", exact=True)
            ).to_have_value("0", timeout=30000)
        result["resources"] = page.evaluate("""() => e2.contexts.map(c=>({
          connected:c.canvas.isConnected, lost:c.gl.isContextLost()}))""")
        if result["native_webgl2"]:
            check(
                all(c["lost"] for c in result["resources"] if not c["connected"]),
                "removed native scenes release their graphics contexts",
            )
        else:
            result["resource_check"] = "Not exercised: 2D fallback, no native scene"

        for width, height in [(1440, 1000), (768, 1024), (390, 844), (320, 740)]:
            page.set_viewport_size({"width": width, "height": height})
            layout = page.evaluate("""() => ({width:innerWidth,
              scrollWidth:document.documentElement.scrollWidth,
              globeWidth:[...document.querySelectorAll('.globe-card')].find(e=>e.getBoundingClientRect().width>0).getBoundingClientRect().width})""")
            result["layouts"].append(layout)
            check(layout["scrollWidth"] <= width + 1, f"track fits viewport {width}")
        actions = page.get_by_label("Calculated ground-track result", exact=True)
        actions.get_by_role(
            "button", name="Generate investigation report", exact=True
        ).click()
        open_report = page.get_by_role(
            "button", name="Open printable report", exact=True
        )
        expect(open_report).to_be_visible(timeout=30000)
        open_report.focus()
        page.keyboard.press("Enter")
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        print_button = dialog.get_by_role(
            "button", name="Print report / Save as PDF", exact=True
        )
        expect(print_button).to_be_focused()
        result["dialog_focus_color"] = print_button.evaluate(
            "e=>getComputedStyle(e).outlineColor"
        )
        check(
            result["dialog_focus_color"] == "rgb(12, 20, 36)",
            "print-dialog focus contrasts with white surface",
        )
        page.keyboard.press("Tab")
        expect(
            dialog.get_by_role("button", name="Close printable report", exact=True)
        ).to_be_focused()
        scan("mobile printable dialog")
        page.keyboard.press("Escape")
        expect(dialog).not_to_be_visible()
        expect(open_report).to_be_focused()
        check(True, "native dialog keyboard controls, Escape and opener focus work")
        # A denied browser download can retry the same captured evidence.
        page.evaluate(
            "() => { window.e2CreateURL=URL.createObjectURL; "
            "URL.createObjectURL=()=>{throw new Error('E2 download denial')}; }"
        )
        page.get_by_role("button", name="Download JSON evidence", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text(
            "could not prepare the download"
        )
        page.evaluate("() => { URL.createObjectURL=window.e2CreateURL; }")
        with page.expect_download() as download:
            page.get_by_role(
                "button", name="Download JSON evidence", exact=True
            ).click()
        check(
            download.value.failure() is None,
            "download denial exposes retry and native retry succeeds",
        )
        page.get_by_role("button", name="Discovery & history", exact=True).click()
        page.get_by_label("Name, NORAD ID or international identifier").fill("6251")
        page.get_by_role("button", name="Search stored records", exact=True).click()
        page.get_by_role("button", name="Inspect snapshot #1", exact=True).click()
        actions = page.get_by_role(
            "region", name="Save or share snapshot investigation", exact=True
        )
        title = actions.get_by_label("Investigation title", exact=True)
        title.fill("E2 synthetic keyboard save")
        page.evaluate(
            "() => { window.e2SetItem=Storage.prototype.setItem; "
            "Storage.prototype.setItem=()=>{throw new DOMException("
            "'E2 synthetic quota','QuotaExceededError')}; }"
        )
        title.press("Enter")
        expect(actions.get_by_role("alert")).to_be_visible()
        page.evaluate("() => { Storage.prototype.setItem=window.e2SetItem; }")
        title.press("Enter")
        expect(
            actions.get_by_role("status").filter(has_text="Saved “E2")
        ).to_be_visible()
        scan("mobile discovery and editable save form")
        check(
            page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),
            "editable investigation fits 320px viewport",
        )
        page.get_by_role("button", name="Saved investigations", exact=True).focus()
        page.keyboard.press("Enter")
        reopen = page.get_by_role(
            "button", name="Open E2 synthetic keyboard save", exact=True
        )
        expect(reopen).to_be_visible()
        reopen.focus()
        page.keyboard.press("Enter")
        expect(
            page.get_by_text("Investigation inputs restored:", exact=False)
        ).to_be_visible()
        check(True, "keyboard save failure, retry and reopen work on mobile")
        # Preserve E1's WebKit/CSP boundary; layout and focus still run there.
        result["screenshots_captured"] = args.engine != "webkit"
        if args.engine != "webkit":
            page.screenshot(path="/results/mobile.png", full_page=True)
        check(not errors, "no uncaught page errors")
        result["page_errors"] = errors
        result["issues"] = issues
        context.close()
        if args.engine == "chromium":
            delayed = browser.new_context()
            slow = delayed.new_page()
            slow.clock.install()
            held = []
            slow.route(
                "**/assets/globe-renderer-*.js", lambda route: held.append(route)
            )
            slow.goto(base, wait_until="domcontentloaded")
            expect(
                slow.get_by_text("Loading the 3D Earth…", exact=True)
            ).to_be_visible()
            slow.clock.run_for(16000)
            check(
                slow.get_by_role("button", name="Retry 3D", exact=True).is_visible(),
                "stalled renderer import terminates with explicit retry",
            )
            assert len(held) == 1
            held.pop().continue_()
            if not args.baseline:
                slow.get_by_role("button", name="Retry 3D", exact=True).click()
                expect(
                    slow.get_by_role("button", name="Rotate left", exact=True)
                ).to_be_enabled(timeout=30000)
                check(True, "stalled renderer retry recovers using the real renderer")
            delayed.close()
        browser.close()
    Path("/results/evidence.json").write_text(json.dumps(result, indent=2) + "\n")
    if issues and not args.baseline:
        raise AssertionError(issues)
    print(
        json.dumps({"engine": args.engine, "baseline": args.baseline, "issues": issues})
    )


if __name__ == "__main__":
    main()
