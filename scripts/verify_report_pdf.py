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
        normalized = compact(raw)
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
