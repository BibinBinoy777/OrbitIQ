import printStyles from "./report-print.css?raw";
import type {
  InvestigationReport,
  ReportObject,
  ReportValue,
} from "./report-api";
import { reportObject } from "./report-api";

export interface ReportTable {
  caption: string;
  columns: string[];
  rows: string[][];
}
export interface ReportSection {
  id: string;
  title: string;
  paragraphs: string[];
  tables: ReportTable[];
}
export const showReportValue = (v: unknown): string =>
  v === null || v === undefined
    ? "Unavailable / not recorded"
    : typeof v === "object"
      ? JSON.stringify(v)
      : String(v);
const table = (
  caption: string,
  rows: string[][],
  columns = ["Field", "Recorded value"],
): ReportTable => ({ caption, columns, rows });
function fields(value: ReportObject, prefix = ""): string[][] {
  return Object.entries(value).flatMap(([key, v]) => {
    const name = prefix + key;
    return reportObject(v)
      ? fields(v, name + ".")
      : [[name, showReportValue(v)]];
  });
}
function stateTable(
  caption: string,
  value: ReportValue | undefined,
): ReportTable {
  return table(
    caption,
    reportObject(value)
      ? fields(value)
      : [["State", "Unavailable; no successful state is claimed."]],
  );
}
export function reportSections(report: InvestigationReport): ReportSection[] {
  const d = report.investigation.definition,
    c = report.calculation;
  const comparison = d.mode === "comparison" && c.data ? c.data : null;
  const results: ReportTable[] = [];
  const resultNotes = [
    `Calculation availability: ${c.status}. Report coverage: ${report.status}; this is not a scientific certification.`,
  ];
  if (d.mode === "snapshot")
    resultNotes.push(
      "Source inspection only. No position or transformation was requested.",
    );
  if (c.status === "unavailable")
    resultNotes.push(
      "One or more requested results are unavailable. Missing values are not zero. Available source evidence is retained.",
    );
  if (c.errors.length)
    results.push(
      table(
        "Unavailable calculation reasons",
        c.errors.map((e) => [e.code, e.message]),
        ["Code", "Explanation"],
      ),
    );
  if (d.mode === "position" && c.data)
    results.push(stateTable("Backend TEME position and derivation", c.data));
  if (d.mode === "ground-track" && c.data) {
    const { points, ...metadata } = c.data;
    results.push(table("Track scope and sampling", fields(metadata)));
    if (Array.isArray(points)) {
      results.push(
        stateTable(
          `Selected sample #${d.track.selected_index}`,
          points[d.track.selected_index],
        ),
      );
      results.push(
        table(
          "All returned ITRS track samples",
          points.map((p) => {
            if (!reportObject(p)) return [];
            const g = reportObject(p.geodetic) ? p.geodetic : {};
            const teme = reportObject(p.teme) ? p.teme : {};
            return [
              `${showReportValue(p.sample_index)}\n${showReportValue(p.at)}\n${showReportValue(teme.calculated_at)}`,
              showReportValue(p.position_km),
              showReportValue(p.velocity_km_s),
              [g.latitude_deg, g.longitude_deg, g.altitude_km]
                .map(showReportValue)
                .join(", "),
              showReportValue(p.transformation_status),
            ];
          }),
          [
            "Index / evaluation UTC / calculation UTC",
            "ITRS position (km)",
            "ITRS velocity (km/s)",
            "WGS84 latitude, longitude (deg), ellipsoidal height (km)",
            "EOP status",
          ],
        ),
      );
      resultNotes.push(
        "The selected sample includes full backend derivation metadata. The track table contains every returned ITRS/geodetic sample; full per-sample TEME/EOP/validation metadata are retained in the same JSON package.",
      );
    }
  }
  if (comparison) {
    results.push(
      table(
        "Comparison scope",
        [
          "is_self_comparison",
          "chronology",
          "counts",
          "filter",
          "matching_basis",
          "element_comparison_status",
        ].map((k) => [k, showReportValue(comparison[k])]),
      ),
    );
    if (Array.isArray(comparison.element_differences))
      results.push(
        table(
          "Orbital element differences",
          comparison.element_differences.map((row) =>
            reportObject(row)
              ? [
                  row.field,
                  row.first_value,
                  row.second_value,
                  row.difference,
                  row.unit,
                  row.convention,
                ].map(showReportValue)
              : [],
          ),
          ["Element", "A", "B", "B − A", "Unit", "Convention"],
        ),
      );
    const state = comparison.state_comparison;
    if (reportObject(state)) {
      const { first, second, ...summary } = state;
      results.push(table("Common-time state comparison", fields(summary)));
      if (first || second) {
        results.push(
          stateTable("Source A state", first),
          stateTable("Source B state", second),
        );
      }
    }
    if (typeof comparison.caution === "string")
      resultNotes.push(comparison.caution);
    if (Array.isArray(comparison.assumptions))
      resultNotes.push(...comparison.assumptions.map(showReportValue));
  }
  const provenanceKeys = [
    "role",
    "source_type",
    "provider",
    "reference",
    "source_url",
    "object_name",
    "object_id",
    "source_frame",
    "epoch_time_system",
    "snapshot_created_at",
    "snapshot_creation_status",
    "observation_at",
    "observation_time_status",
    "publication_at",
    "publication_time_status",
    "payload_hash",
    "provider_published_hash",
    "provider_hash_status",
    "source_authenticity",
    "validation_status",
    "validator_version",
    "ingestion_sgp4_version",
    "checks_performed_for_report",
    "freshness_info",
  ];
  const rows = provenanceKeys.flatMap((key) => {
    const flat = fields({ [key]: report.sources[0][key] });
    return flat.map(([name, value]) => [
      name,
      value,
      ...(report.sources[1]
        ? [
            fields({ [key]: report.sources[1][key] }).find(
              ([n]) => n === name,
            )?.[1] ?? "Unavailable / not recorded",
          ]
        : []),
    ]);
  });
  return [
    {
      id: "summary",
      title: "1. Executive summary",
      paragraphs: [
        `${d.mode} investigation using ${report.sources.length} exact source reference${report.sources.length === 1 ? "" : "s"} for NORAD ${d.source.catalog_id}.`,
        `Available content: validated source elements and ${c.status === "not_requested" ? "no requested calculated state" : c.status === "complete" ? "the requested backend calculation/comparison" : "explicit unavailable calculation reasons"}.`,
        "No saved narrative or independent interpretation is available from the backend. This summary describes report contents, not a scientific finding.",
      ],
      tables: [],
    },
    {
      id: "overview",
      title: "2. Investigation overview",
      paragraphs: [
        "This report captures the current configuration and current backend results from exact archived sources. It is not the original saved numerical state.",
        "Browser-only saved title, UUID, notes and creation time are excluded; no server-owned investigation record is implied.",
      ],
      tables: [
        table("Investigation identity", [
          ["Configuration identifier", report.investigation.id],
          ["Identifier kind", report.investigation.id_kind],
          ["Title origin", report.investigation.title_origin],
          [
            "Saved investigation creation time",
            "Unavailable on backend; browser-only metadata excluded",
          ],
          [
            "Description / local notes",
            "Excluded; not sent to the report service",
          ],
        ]),
        table("Requested configuration", fields(d as unknown as ReportObject)),
        ...report.sources.map((s) =>
          table(
            `Source ${s.role}: OMM inputs`,
            Object.entries(s.elements).map(([k, v]) => [
              k,
              showReportValue(v),
              showReportValue(s.element_units[k]),
            ]),
            ["Element", "Source value", "Unit"],
          ),
        ),
      ],
    },
    {
      id: "results",
      title: "3. Results and comparisons",
      paragraphs: resultNotes,
      tables: results,
    },
    {
      id: "provenance",
      title: "4. Evidence and provenance",
      paragraphs: [
        "These source payloads are archived mean-element datasets. They are not direct observations. Source identifiers, epochs, retrievals and hashes below are distinct from derived calculations and report generation.",
        "A payload SHA-256 identifies exact stored response-body bytes, not provider-published authentication or scientific correctness.",
      ],
      tables: [
        table("Exact archived source evidence", rows, [
          "Field",
          "Primary source",
          ...(report.sources.length === 2 ? ["Comparison source"] : []),
        ]),
      ],
    },
    {
      id: "validation",
      title: "5. Validation and data quality",
      paragraphs: [
        "Source validation, stored byte integrity, source authenticity, calculation availability and physical interpretation are different properties.",
        ...report.warnings,
      ],
      tables: [
        table(
          "Validation and missing-data disclosures",
          fields(report.validation),
        ),
      ],
    },
    {
      id: "limitations",
      title: "6. Scientific limitations",
      paragraphs: report.limitations,
      tables: [],
    },
    {
      id: "methodology",
      title: "7. Methodology and reproducibility",
      paragraphs: [
        "All orbital calculations and transformations were performed by existing backend services. This renderer formats their captured output without recalculating coordinates.",
        "JSON and this report use the same report ID, generation time, configuration, source evidence and results. Regenerating creates a new report and can use different execution times/resources.",
        "Use browser printing / Save as PDF. Page counters use paged CSS where supported; enable browser headers/footers for page numbers when your print engine lacks margin-box support.",
      ],
      tables: [
        table(
          "Methods, versions, units and policy",
          fields(report.methodology),
        ),
      ],
    },
  ];
}
export function escapeReportHtml(value: string): string {
  return value.replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ]!,
  );
}
export function reportHtml(report: InvestigationReport): string {
  const e = escapeReportHtml;
  const tables = (t: ReportTable) =>
    `<table><caption>${e(t.caption)}</caption><thead><tr>${t.columns.map((s) => `<th scope="col">${e(s)}</th>`).join("")}</tr></thead><tbody>${t.rows.map((row) => `<tr>${row.map((s) => `<td>${e(s)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>${e(report.investigation.title)} | OrbitIQ report</title><style>${printStyles}</style></head><body class="report-standalone"><article class="report-sheet" aria-label="OrbitIQ investigation report"><header><p class="report-brand">ORBITIQ / INVESTIGATION REPORT</p><h1>${e(report.investigation.title)}</h1><p>Report ${e(report.report_id)} · schema ${report.schema_version} / template ${report.template_version}</p><p>Generated (UTC): ${e(report.generated_at)}</p><p class="report-callout">Coverage: ${e(report.status)}. Validation: ${e(String(report.validation.status))}. Calculated data are not observations.</p></header>${reportSections(
    report,
  )
    .map(
      (s) =>
        `<section id="${e(s.id)}"><h2>${e(s.title)}</h2>${s.paragraphs.map((p) => `<p>${e(p)}</p>`).join("")}${s.tables.map(tables).join("")}</section>`,
    )
    .join(
      "",
    )}<footer>OrbitIQ · Report ${e(report.report_id)} · Generated ${e(report.generated_at)} · schema ${report.schema_version} / template ${report.template_version}. Scientific certification is not implied.</footer></article></body></html>`;
}
export function reportJson<T>(report: T): string {
  return JSON.stringify(report, null, 2) + "\n";
}
