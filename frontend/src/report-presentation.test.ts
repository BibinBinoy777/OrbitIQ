import { expect, it } from "vitest";
import { reportFixture } from "./test-fixtures/reports";
import { parseReport } from "./report-api";
import {
  reportHtml,
  reportJson,
  reportSections,
  showReportValue,
} from "./report-presentation";

it.each(["snapshot", "position", "ground-track", "comparison"])(
  "keeps %s identity, evidence, policy and results consistent across formats",
  (mode) => {
    const r = reportFixture(mode);
    parseReport(r, r.investigation.definition);
    const html = reportHtml(r),
      json = JSON.parse(reportJson(r));
    const doc = new DOMParser().parseFromString(html, "text/html"),
      text = doc.body.textContent!;
    expect(json).toEqual(r);
    for (const value of [
      r.report_id,
      r.generated_at,
      r.investigation.id,
      r.investigation.title,
      r.validation.status,
      r.validation.prediction_uncertainty,
    ])
      expect(text).toContain(String(value));
    for (const source of r.sources) {
      for (const value of [
        source.reference.snapshot_id,
        source.reference.orbital_epoch,
        source.reference.retrieved_at,
        source.payload_hash.value,
        source.payload_hash.scope,
        source.validation_status,
      ])
        expect(text).toContain(String(value));
    }
    for (const warning of [...r.warnings, ...r.limitations])
      expect(text).toContain(warning);
    if (r.methodology.configured_eop_policy)
      expect(text).toContain(String(r.methodology.configured_eop_policy));
    if (mode === "position")
      expect(text).toContain(JSON.stringify(r.calculation.data!.position_km));
    if (mode === "comparison") {
      const state = r.calculation.data!.state_comparison as Record<
        string,
        unknown
      >;
      expect(text).toContain(String(state.separation_km));
      expect(text).toContain(JSON.stringify(state.difference_velocity_km_s));
    }
    expect(
      doc.querySelectorAll("script, iframe, img, link, form"),
    ).toHaveLength(0);
    expect(doc.querySelectorAll("section")).toHaveLength(7);
    expect(
      doc
        .querySelector("meta[http-equiv='Content-Security-Policy']")
        ?.getAttribute("content"),
    ).toContain("default-src 'none'");
    expect(html).toContain("counter(page)");
    expect(html).toContain("table-header-group");
    expect(html).toContain("overflow-wrap: anywhere");
  },
);
it("preserves every returned track row and the full selected derivation", () => {
  const r = reportFixture("ground-track");
  const sections = reportSections(r),
    tables = sections.find((s) => s.id === "results")!.tables;
  const track = tables.find(
    (t) => t.caption === "All returned ITRS track samples",
  )!;
  const points = r.calculation.data!.points as Record<string, unknown>[];
  expect(track.rows).toHaveLength(points.length);
  points.forEach((p, i) =>
    expect(track.rows[i][1]).toBe(JSON.stringify(p.position_km)),
  );
  expect(tables.some((t) => t.caption === "Selected sample #0")).toBe(true);
});
it("escapes untrusted source names and identifiers as text", () => {
  const r = reportFixture();
  r.sources[0].object_name =
    '<img src=x onerror="alert(1)"><script>bad()</script>&';
  const html = reportHtml(r),
    doc = new DOMParser().parseFromString(html, "text/html");
  expect(doc.querySelectorAll("img,script")).toHaveLength(0);
  expect(doc.body.textContent).toContain(r.sources[0].object_name);
  expect(html).toContain("&lt;img");
});
it("does not label missing calculations or missing dates as zero", () => {
  const r = reportFixture();
  r.status = "partial";
  r.calculation = {
    status: "unavailable",
    data: null,
    errors: [
      { code: "eop_unavailable", message: "Required local EOP unavailable" },
    ],
  };
  const doc = new DOMParser().parseFromString(reportHtml(r), "text/html");
  expect(doc.body.textContent).toContain("Missing values are not zero");
  expect(doc.body.textContent).toContain("Required local EOP unavailable");
  expect(doc.body.textContent).toContain("Unavailable / not recorded");
  expect(doc.body.textContent).not.toContain("position_km");
  expect(showReportValue(0)).toBe("0");
});
