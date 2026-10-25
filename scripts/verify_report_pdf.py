"""Check Chromium report PDF artifacts against their captured JSON downloads.

Requires pdftotext (Poppler) on the verification machine, not in release images.
This checks text/pagination consistency, not physical printers or optical fidelity.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def compact(value):
    return re.sub(r"\s+", "", value)


def content_reading_order(raw, page_count):
    """Remove only validated running furniture at each raw page boundary.

    Poppler can place margin boxes between the two halves of a sentence when
    it crosses pages. Keep the independent layout/page-counter checks and all
    body text; do not globally remove strings resembling report content.
    """
    pages = raw.split("\f")
    if len(pages) != page_count + 1 or pages[-1].strip():
        raise ValueError("Raw PDF pagination does not match layout")
    bodies = []
    for number, page in enumerate(pages[:-1], 1):
        lines = page.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        header = "OrbitIQ / Investigation report"
        footer = f"OrbitIQ · Page {number} of {page_count}"
        start = [line.strip() for line in lines[:2]]
        end = [line.strip() for line in lines[-2:]]
        if start in ([header, footer], [footer, header]):
            body = lines[2:]
        elif end in ([header, footer], [footer, header]):
            body = lines[:-2]
        elif lines and lines[0].strip() == header and lines[-1].strip() == footer:
            body = lines[1:-1]
        else:
            raise ValueError(f"Missing or misplaced running furniture on page {number}")
        bodies.append("\n".join(body))
    return "\n".join(bodies)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = sorted(args.directory.glob("chromium-*.pdf"))
    if not files:
        raise ValueError("No Chromium report PDFs to verify")
    results = []
    for path in files:
        # Keep JavaScript's captured decimal spelling; parsing through a Python
        # float can choose another equivalent spelling of the same binary value.
        report = json.loads(path.with_suffix(".json").read_text(), parse_float=str)
        text = subprocess.check_output(
            ["pdftotext", "-layout", str(path), "-"], text=True, timeout=30
        )
        pages = text.split("\f")[:-1]
        assert len(pages) > 1, path.name
        for i, page in enumerate(pages, 1):
            assert f"Page {i} of {len(pages)}" in page, (path.name, i)
        # Raw reading order keeps wrapped table-cell digits together; layout
        # extraction interleaves columns on each visual line.
        raw = subprocess.check_output(
            ["pdftotext", "-raw", str(path), "-"], text=True, timeout=30
        )
        normalized = compact(content_reading_order(raw, len(pages)))
        expected = [
            report["report_id"],
            report["generated_at"],
            report["investigation"]["id"],
            report["validation"]["status"],
            *report["warnings"],
            *report["limitations"],
        ]
        for s in report["sources"]:
            expected.extend(
                [
                    s["payload_hash"]["value"],
                    s["reference"]["orbital_epoch"],
                    s["reference"]["retrieved_at"],
                ]
            )
        points = (report["calculation"]["data"] or {}).get("points", [])
        for point in points:
            expected.append(point["at"])
            expected.extend(str(v) for v in point["position_km"])
            expected.extend(
                str(point["geodetic"][key])
                for key in ("latitude_deg", "longitude_deg", "altitude_km")
            )
        for value in expected:
            assert compact(value) in normalized, (path.name, value)
        for title in [
            "Executive summary",
            "Investigation overview",
            "Results and comparisons",
            "Evidence and provenance",
            "Validation and data quality",
            "Scientific limitations",
            "Methodology and reproducibility",
        ]:
            assert title in text, (path.name, title)
        assert "Satellite explorer" not in text and "Backend connected" not in text
        assert "PRIVATE_LOCAL_REPORT_TEST_ONLY" not in text
        results.append(
            {
                "file": path.name,
                "pages": len(pages),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "report_sha256": hashlib.sha256(
                    path.with_suffix(".json").read_bytes()
                ).hexdigest(),
                "status": "PASS",
                "page_counters": True,
                "all_sections": True,
                "source_identity_and_warnings": True,
                "track_rows_checked": len(points),
                "application_excluded": True,
            }
        )
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results))


if __name__ == "__main__":
    main()
