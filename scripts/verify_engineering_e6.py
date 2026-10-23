"""E6 local-only browser recovery: public synthetic fixtures, isolated storage.

Normal round trips use the actual API and native downloads/File API/Web Locks.
Catalog and persistence fault injections are explicitly labelled in the receipt.
No provider requests, private data, scientific evidence or production services.
"""

import argparse
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from browser_diagnostics import browser_session
from playwright.sync_api import expect, sync_playwright

BASE = "http://127.0.0.1:8080"
KEY = "orbitiq.saved-investigations.v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine", choices=["chromium", "firefox", "webkit"], required=True
    )
    parser.add_argument("--output", type=Path, default=Path("/results"))
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    opener = build_opener(ProxyHandler({}))

    def get(path):
        with opener.open(BASE + path, timeout=10) as response:
            return json.loads(response.read(262144))

    sources = [get(f"/api/snapshots/{sid}") for sid in (1, 2)]
    assert all(
        s["catalog_id"] == 6251 and "SYNTHETIC" in s["object_name"] for s in sources
    )

    for source in sources:
        for field in ("orbital_epoch", "retrieved_at"):
            source[field] = (
                datetime.fromisoformat(source[field])
                .astimezone(UTC)
                .isoformat(timespec="microseconds")
                .replace("+00:00", "Z")
            )

    def ref(s):
        return {
            k: s["id"] if k == "snapshot_id" else s[k]
            for k in (
                "snapshot_id",
                "catalog_id",
                "orbital_epoch",
                "retrieved_at",
                "response_sha256",
            )
        }

    records = []
    for index, mode in enumerate(
        ("snapshot", "position", "ground-track", "comparison")
    ):
        investigation = {
            "schema_version": 1,
            "mode": mode,
            "frame": "TEME",
            "source": ref(sources[0]),
        }
        if mode != "snapshot":
            investigation["at"] = sources[0]["orbital_epoch"]
        if mode == "ground-track":
            investigation.update(
                frame="ITRS",
                track={
                    "start": sources[0]["orbital_epoch"],
                    "duration_minutes": 2,
                    "step_seconds": 60,
                    "selected_index": 0,
                },
            )
        if mode == "comparison":
            investigation.update(comparison_source=ref(sources[1]), category="all")
        records.append(
            {
                "schema_version": 1,
                "id": f"c7fcaa37-5da9-4bd5-8000-582c07b6683{index}",
                "title": f"E6 SYNTHETIC {mode}",
                "description": "PRIVATE TEST NOTE ONLY",
                "created_at": "2026-10-19T00:00:00.000000Z",
                "updated_at": "2026-10-19T00:00:00.000000Z",
                "investigation": investigation,
            }
        )
    result = {
        "engine": args.engine,
        "status": "RUNNING",
        "fixture": "PUBLIC SYNTHETIC INPUTS; NOT OBSERVED HISTORY",
        "cases": [],
        "accessibility": [],
        "round_trips": [],
        "layouts": [],
    }
    errors, writes = [], []
    downloaded_paths = {}

    def passed(name, **details):
        result["cases"].append({"case": name, "status": "PASS", **details})

    with browser_session(sync_playwright) as p:
        launch = {"headless": True}
        if args.engine == "chromium":
            launch["args"] = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
        browser = getattr(p, args.engine).launch(**launch)
        contexts = []

        def context():
            c = browser.new_context(
                viewport={"width": 1440, "height": 1000}, accept_downloads=True
            )
            c.on(
                "page",
                lambda page: page.on(
                    "pageerror", lambda error: errors.append(str(error))
                ),
            )
            c.on(
                "request",
                lambda r: (
                    writes.append(r.url) if r.method not in {"GET", "HEAD"} else None
                ),
            )
            contexts.append(c)
            return c

        def saved(page):
            return page.evaluate("key => localStorage.getItem(key)", KEY)

        def choose(page, bundle):
            if not isinstance(bundle, bytes):
                native = downloaded_paths.get(json.dumps(bundle, sort_keys=True))
                if native:
                    page.get_by_label(
                        "Portable investigation file", exact=True
                    ).set_input_files(str(native))
                    return
            raw = bundle if isinstance(bundle, bytes) else json.dumps(bundle).encode()
            page.get_by_label(
                "Portable investigation file", exact=True
            ).set_input_files(
                {"name": "e6-local.json", "mimeType": "application/json", "buffer": raw}
            )

        def preview(page, bundle):
            choose(page, bundle)
            heading = page.get_by_role(
                "heading", name="Preview portable investigation", exact=True
            )
            expect(heading).to_be_visible()
            expect(heading).to_be_focused()

        def confirm(page):
            page.get_by_role("button", name="Confirm local import", exact=True).click()
            expect(
                page.get_by_role(
                    "heading", name="Preview portable investigation", exact=True
                )
            ).to_have_count(0)

        downloads = []

        def download(page, title):
            with page.expect_download() as pending:
                page.get_by_role(
                    "button", name="Export portable bundle for " + title, exact=True
                ).click()
            file = pending.value
            assert file.failure() is None
            assert file.suggested_filename.startswith(
                "orbitiq-investigation-"
            ) and file.suggested_filename.endswith(".json")
            raw = Path(file.path()).read_bytes()
            assert 0 < len(raw) <= 16384
            bundles_dir = out / "bundles"
            bundles_dir.mkdir(exist_ok=True)
            name = f"{len(downloads):02d}-" + file.suggested_filename
            (bundles_dir / name).write_bytes(raw)
            downloads.append(name)
            data = json.loads(raw)
            downloaded_paths[json.dumps(data, sort_keys=True)] = bundles_dir / name
            assert set(data) == {"kind", "schema_version", "exported_at", "record"}
            assert (
                data["kind"] == "orbitiq_saved_investigation_bundle"
                and data["schema_version"] == 1
            )
            return data

        def scan(page, name):
            page.evaluate(Path("/opt/axe/axe.min.js").read_text())
            data = page.evaluate(
                """async () => {
                    const r=await axe.run(document,{runOnly:{type:'tag',
                        values:['wcag2a','wcag2aa','wcag21aa']}});
                    return {violations:r.violations.map(v=>({id:v.id,
                        targets:v.nodes.map(n=>n.target)})),
                        incomplete:r.incomplete.map(v=>({id:v.id,
                            targets:v.nodes.map(n=>n.target)})),
                        passes:r.passes.length};
                }"""
            )
            result["accessibility"].append({"view": name, **data})
            assert not data["violations"], data

        try:
            origin = context().new_page()
            origin.goto(BASE, wait_until="networkidle")
            expect(
                origin.get_by_role(
                    "heading", name="Start with stored satellite data", exact=True
                )
            ).to_be_visible()
            expect(
                origin.get_by_role("button", name="Open stored snapshot #1", exact=True)
            ).to_be_enabled()
            expect(
                origin.get_by_text("Not assessed globally.", exact=False)
            ).to_be_visible()
            scan(origin, "onboarding-desktop")
            origin.get_by_role(
                "button", name="Open stored snapshot #1", exact=True
            ).click()
            expect(
                origin.get_by_role("combobox", name="Saved snapshot", exact=True)
            ).to_have_value("1")
            passed(
                "actual stored catalog opens exact validated synthetic "
                "source without provider writes"
            )
            # Select deterministic pre-existing local saves using the
            # established schema.
            # These are browser-only synthetic input fixtures, never
            # inserted into the archive.
            origin.evaluate(
                "({key,records})=>localStorage.setItem(key,"
                "JSON.stringify({schema_version:1,records}))",
                {"key": KEY, "records": records},
            )
            original = saved(origin)
            origin.get_by_role(
                "button", name="Saved investigations", exact=True
            ).click()
            target_context = context()
            target = target_context.new_page()
            target.goto(BASE, wait_until="networkidle")
            target.get_by_role(
                "button", name="Saved investigations", exact=True
            ).click()
            expect(
                target.get_by_label("Portable investigation file", exact=True)
            ).to_be_visible()
            assert saved(target) is None

            def deny_http(route):
                if route.request.url.startswith(("http://", "https://")):
                    route.abort("internetdisconnected")
                else:
                    route.fallback()

            # Playwright WebKit's offline emulation rejects even in-memory
            # File.arrayBuffer/FileReader with NotReadableError. Block all HTTP
            # instead, and prove transport denial before the same native file IO.
            if args.engine == "webkit":
                target_context.route("**/*", deny_http)
                result["offline_mechanism"] = "all HTTP denied by browser routing"
            else:
                target_context.set_offline(True)
                result["offline_mechanism"] = "browser context offline"
            assert target.evaluate("""async () => {
                try {await fetch('/api/health');return false;}
                catch {return true;}
            }""")
            bundles = []
            for record in records:
                default = download(origin, record["title"])
                assert default["record"]["description"] == ""
                assert default["record"] == {**record, "description": ""}
                origin.get_by_label(
                    "Include private local notes for " + record["title"], exact=True
                ).check()
                bundle = download(origin, record["title"])
                expected = deepcopy(record)
                assert bundle["record"] == expected
                before = saved(target)
                preview(target, bundle)
                assert saved(target) == before
                expect(
                    target.get_by_text(
                        "Structural validation is not scientific qualification",
                        exact=False,
                    )
                ).to_be_visible()
                if not bundles:
                    scan(target, "import-preview")
                    target.get_by_role(
                        "button", name="Cancel import", exact=True
                    ).click()
                    expect(
                        target.get_by_label("Portable investigation file", exact=True)
                    ).to_be_focused()
                    assert saved(target) == before
                    preview(target, bundle)
                confirm(target)
                expect(
                    target.get_by_role(
                        "heading", name="Restore a portable investigation", exact=True
                    )
                ).to_be_focused()
                restored = json.loads(saved(target))["records"]
                assert next(r for r in restored if r["id"] == record["id"]) == expected
                if expected["description"]:
                    target.get_by_label(
                        "Include private local notes for " + record["title"], exact=True
                    ).check()
                assert download(target, record["title"])["record"] == expected
                assert saved(origin) == original
                result["round_trips"].append(
                    {
                        "mode": record["investigation"]["mode"],
                        "status": "PASS",
                        "independent_context": True,
                        "record_equal": True,
                        "original_unchanged": True,
                    }
                )
                bundles.append(bundle)
                passed(
                    "native export, independent-context restore and re-export: "
                    + record["investigation"]["mode"]
                )
            before = saved(target)
            preview(target, bundles[0])
            confirm(target)
            expect(
                target.get_by_text("This investigation is already saved.", exact=False)
            ).to_be_visible()
            assert saved(target) == before
            passed("repeated import is idempotent and cancel did not persist")
            collision = deepcopy(bundles[0])
            collision["record"]["title"] = "E6 COLLISION TEST"
            preview(target, collision)
            expect(
                target.get_by_role("button", name="Confirm local import", exact=True)
            ).to_be_disabled()
            assert saved(target) == before
            target.get_by_label(
                "Import as a separate copy with a new identifier", exact=True
            ).check()
            confirm(target)
            copied = next(
                r
                for r in json.loads(saved(target))["records"]
                if r["title"] == "E6 COLLISION TEST"
            )
            assert copied["id"] != records[0]["id"]
            before = saved(target)
            preview(target, collision)
            confirm(target)
            assert saved(target) == before
            passed(
                "explicit collision copy preserves original and repeated "
                "copy is idempotent"
            )
            if args.engine == "webkit":
                target_context.unroute("**/*", deny_http)
            else:
                target_context.set_offline(False)
            # The other cooperating tab writes under the same application lock.
            candidate = deepcopy(bundles[1])
            candidate["record"]["id"] = "a7fcaa37-5da9-4bd5-8000-582c07b66830"
            candidate["record"]["title"] = "E6 QUOTA AND STALE PREVIEW TEST"
            preview(target, candidate)
            sibling = target_context.new_page()
            sibling.goto(BASE, wait_until="networkidle")
            sibling.get_by_role(
                "button", name="Saved investigations", exact=True
            ).click()
            newer = deepcopy(bundles[1])
            newer["record"]["id"] = "b7fcaa37-5da9-4bd5-8000-582c07b66830"
            newer["record"]["title"] = "E6 NEWER TAB SAVE"
            preview(sibling, newer)
            confirm(sibling)
            before = saved(target)
            target.get_by_role(
                "button", name="Confirm local import", exact=True
            ).click()
            expect(
                target.get_by_role("alert").filter(has_text="changed since preview")
            ).to_be_visible()
            assert saved(target) == before
            target.get_by_role("button", name="Cancel import", exact=True).click()
            sibling.close()
            passed(
                "actual cooperating tab change rejects stale confirmation "
                "without overwrite"
            )
            rejected = []
            bad = deepcopy(bundles[0])
            invalid = [
                ("invalid JSON", b"{INVALID", "version-1"),
                ("empty file", b"", "empty"),
                ("oversized file", b"x" * 16385, "16 KiB"),
            ]
            for field, value in [("schema_version", 2), ("exported_at", "bad")]:
                value_bundle = deepcopy(bad)
                value_bundle[field] = value
                invalid.append(
                    (
                        "invalid bundle " + field,
                        json.dumps(value_bundle).encode(),
                        "version-1",
                    )
                )
            for field, value in [
                ("title", 42),
                ("id", "invalid"),
                ("created_at", "2026-02-30T00:00:00Z"),
            ]:
                value_bundle = deepcopy(bad)
                value_bundle["record"][field] = value
                invalid.append(
                    (
                        "invalid record " + field,
                        json.dumps(value_bundle).encode(),
                        "version-1",
                    )
                )
            for field, value in [("mode", "unsupported"), ("source", {})]:
                value_bundle = deepcopy(bad)
                value_bundle["record"]["investigation"][field] = value
                invalid.append(
                    (
                        "invalid input " + field,
                        json.dumps(value_bundle).encode(),
                        "version-1",
                    )
                )
            value_bundle = deepcopy(bad)
            del value_bundle["record"]["title"]
            invalid.append(
                (
                    "missing required field",
                    json.dumps(value_bundle).encode(),
                    "version-1",
                )
            )
            for name, raw, message in invalid:
                choose(target, raw)
                expect(
                    target.get_by_role("alert").filter(has_text=message)
                ).to_be_visible()
                assert saved(target) == before
                rejected.append(
                    {"case": name, "status": "PASS", "storage_unchanged": True}
                )
            result["rejected_imports"] = rejected
            preview(target, candidate)
            target.evaluate(
                """() => {
                    window.e6set=Storage.prototype.setItem;
                    Storage.prototype.setItem=function(k,v){
                        if(k==='orbitiq.saved-investigations.v1')
                            throw new DOMException('controlled test quota',
                                'QuotaExceededError');
                        return e6set.call(this,k,v);
                    }
                }"""
            )
            target.get_by_role(
                "button", name="Confirm local import", exact=True
            ).click()
            expect(
                target.get_by_role("alert").filter(has_text="Browser storage")
            ).to_be_visible()
            assert saved(target) == before
            target.evaluate("() => {Storage.prototype.setItem=window.e6set;}")
            confirm(target)
            denied = deepcopy(candidate)
            denied["record"].update(
                id="f7fcaa37-5da9-4bd5-8000-582c07b66830",
                title="E6 PERSISTENCE DENIED TEST",
            )
            preview(target, denied)
            before_denial = saved(target)
            target.evaluate("""() => {
                Storage.prototype.setItem=function(){
                    throw new DOMException('controlled test denial','SecurityError');
                }
            }""")
            target.get_by_role(
                "button", name="Confirm local import", exact=True
            ).click()
            expect(
                target.get_by_role("alert").filter(has_text="Browser storage")
            ).to_be_visible()
            assert saved(target) == before_denial
            target.evaluate("() => {Storage.prototype.setItem=window.e6set;}")
            target.get_by_role("button", name="Cancel import", exact=True).click()
            passed(
                "invalid/oversize files and injected quota error preserve "
                "existing saves; retry succeeds",
                fault_injection=True,
            )
            missing = deepcopy(bundles[0])
            missing["record"].update(
                id="d7fcaa37-5da9-4bd5-8000-582c07b66830",
                title="E6 MISSING SOURCE TEST",
            )
            missing["record"]["investigation"]["source"]["snapshot_id"] = 999999
            preview(target, missing)
            confirm(target)
            target.get_by_role(
                "button", name="Open E6 MISSING SOURCE TEST", exact=True
            ).click()
            expect(
                target.get_by_role("alert").filter(has_text="Restoration unavailable")
            ).to_be_visible()
            expect(
                target.get_by_text("Investigation inputs restored:", exact=False)
            ).to_have_count(0)
            passed(
                "missing exact source stays missing; no latest-source "
                "substitution or false recovery"
            )
            target.get_by_role(
                "button", name="Saved investigations", exact=True
            ).click()
            # Untrusted title/notes remain text; export denial does not alter storage.
            hostile = deepcopy(bundles[0])
            hostile["record"].update(
                id="e7fcaa37-5da9-4bd5-8000-582c07b66830",
                title="<img src=x onerror=alert(1)>",
                description="<script>TEST TEXT ONLY</script>",
            )
            preview(target, hostile)
            assert (
                target.locator(".portable-tools img, .portable-tools script").count()
                == 0
            )
            confirm(target)
            before = saved(target)
            target.evaluate(
                "() => {window.e6url=URL.createObjectURL;"
                "URL.createObjectURL=()=>{"
                "throw new Error('controlled export denial')};}"
            )
            target.get_by_role(
                "button",
                name="Export portable bundle for " + hostile["record"]["title"],
                exact=True,
            ).click()
            expect(
                target.get_by_role("alert").filter(
                    has_text="Portable export could not be prepared"
                )
            ).to_be_visible()
            assert saved(target) == before
            target.evaluate("() => {URL.createObjectURL=window.e6url;}")
            assert (
                download(target, hostile["record"]["title"])["record"]["description"]
                == ""
            )
            passed(
                "untrusted HTML stays text; injected export denial is "
                "actionable and retry works",
                fault_injection=True,
            )
            scan(target, "restored-saves")
            for width in (320, 390, 1440):
                target.set_viewport_size({"width": width, "height": 1000})
                preview(target, bundles[0])
                assert target.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth + 1"
                )
                result["layouts"].append({"width": width, "status": "PASS"})
                if width == 390:
                    scan(target, "import-mobile")
                    target.screenshot(
                        path=str(out / "mobile.png"), full_page=False, caret="initial"
                    )
                target.get_by_role("button", name="Cancel import", exact=True).click()
            passed("desktop/mobile import controls, focus and WCAG automated scans")
            # Explicit response/transport fault injection tests only,
            # never described as live data.
            fault = context().new_page()
            pending_catalog = []
            fault.route(
                "**/api/snapshots?*", lambda route: pending_catalog.append(route)
            )
            fault.goto(BASE, wait_until="domcontentloaded")
            expect(
                fault.get_by_text("Loading stored catalog information…", exact=True)
            ).to_be_visible()
            assert len(pending_catalog) == 1
            pending_catalog[0].abort("failed")
            expect(
                fault.get_by_role("alert").filter(has_text="Stored catalog unavailable")
            ).to_be_visible()
            fault.unroute("**/api/snapshots?*")
            fault.get_by_role(
                "button", name="Reload stored catalog", exact=True
            ).click()
            expect(
                fault.get_by_role("button", name="Open stored snapshot #1", exact=True)
            ).to_be_enabled()
            page_data = get("/api/snapshots?limit=5")
            empty = {
                **page_data,
                "snapshots": [],
                "returned_count": 0,
                "scanned_count": 0,
                "anchor_id": None,
                "next_before_id": None,
                "total_count": 0,
                "total_count_status": "exact_within_anchor",
                "has_more": False,
            }
            fault.route("**/api/snapshots?*", lambda route: route.fulfill(json=empty))
            fault.get_by_role(
                "button", name="Reload stored catalog", exact=True
            ).click()
            expect(
                fault.get_by_text("No stored snapshots are available.", exact=False)
            ).to_be_visible()
            fault.unroute("**/api/snapshots?*")
            incomplete = deepcopy(page_data)
            incomplete["snapshots"][0]["metadata_issues"] = [
                "CONTROLLED TEST INCOMPLETE METADATA"
            ]
            fault.route(
                "**/api/snapshots?*", lambda route: route.fulfill(json=incomplete)
            )
            audit = get("/api/readiness")
            audit["components"]["ingestion"].update(
                latest_attempt_failed=True,
                status="degraded",
                code="collection_failed",
                message="CONTROLLED TEST: collection failed; archive retained.",
            )
            fault.route("**/api/readiness", lambda route: route.fulfill(json=audit))
            fault.get_by_role(
                "button", name="Reload stored catalog", exact=True
            ).click()
            expect(
                fault.get_by_text(
                    "The latest provider collection attempt failed.", exact=False
                )
            ).to_be_visible()
            expect(
                fault.get_by_role(
                    "button",
                    name=f"Open stored snapshot #{incomplete['snapshots'][0]['id']}",
                    exact=True,
                )
            ).to_be_disabled()
            expect(
                fault.get_by_role("button", name="Open stored snapshot #1", exact=True)
            ).to_be_enabled()
            fault.unroute("**/api/snapshots?*")
            uncounted = {
                **page_data,
                "total_count": None,
                "total_count_status": "unknown_exceeds_bounded_count",
            }
            fault.route(
                "**/api/snapshots?*", lambda route: route.fulfill(json=uncounted)
            )
            fault.get_by_role(
                "button", name="Reload stored catalog", exact=True
            ).click()
            expect(
                fault.get_by_text(
                    "Unavailable — count exceeds the bounded assessment", exact=True
                )
            ).to_be_visible()
            fault.unroute("**/api/snapshots?*")
            fault.route("**/api/snapshots?*", lambda route: route.abort("failed"))
            fault.get_by_role(
                "button", name="Reload stored catalog", exact=True
            ).click()
            expect(
                fault.get_by_role("alert").filter(
                    has_text="Previously loaded metadata is retained"
                )
            ).to_be_visible()
            expect(
                fault.get_by_role("button", name="Open stored snapshot #1", exact=True)
            ).to_be_enabled()
            passed(
                "catalog empty/incomplete/provider-failure/transport-retry "
                "states with explicit fault injection",
                fault_injection=True,
            )
            assert saved(origin) == original
            assert not errors, errors
            assert not writes, writes
            result.update(
                status="PASS",
                offline_import=True,
                downloaded_bundles=downloads,
                original_browser_unchanged=True,
                no_network_writes=True,
                page_errors=errors,
            )
            (out / "evidence.json").write_text(json.dumps(result, indent=2) + "\n")
        finally:
            for c in reversed(contexts):
                c.close()
            browser.close()


if __name__ == "__main__":
    main()
