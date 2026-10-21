"""Offline input qualification, never propagation or prediction-error calculation.

The original specimen inspector remains unchanged. Ordinary GPS timestamps may
be converted for diagnostics; source anomalies, missing historical provenance,
quality and realization gates cannot be promoted by a CLI option.
"""

import argparse
import json
import runpy
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from astropy.coordinates import ITRS, TEME, frame_transform_graph
from astropy.time import Time
from orbitiq import replay
from orbitiq.ingestion.celestrak import IngestionError, parse_response
from orbitiq.orbits.earth_orientation import (
    TransformationError,
    orientation,
    parameters,
)

SOURCE = runpy.run_path(str(Path(__file__).with_name("inspect_swarm_reference.py")))


class QualificationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def gps_value(parts, scale):
    if scale != "GPS":
        raise QualificationError("missing_or_unsupported_time_scale")
    try:
        value, flags = SOURCE["epoch"](parts)
    except (ValueError, TypeError, OverflowError):
        raise QualificationError("invalid_gps_calendar") from None
    if flags["seconds_field_60"]:
        raise QualificationError("source_second_60_requires_provider_clarification")
    if flags["submicrosecond"]:
        raise QualificationError("source_precision_exceeds_microsecond_contract")
    if value < 0:
        raise QualificationError("before_supported_gps_epoch")
    return value


def to_utc(value, data):
    # Split whole/fractional SI seconds to avoid converting a large epoch to one
    # float. GPS epoch/TAI semantics and historical leaps are provided by Astropy
    # under the existing explicit local-resource scope, never a fixed UTC offset.
    whole = int(value)
    at = Time(
        whole, float(value - Decimal(whole)), format="gps", scale="tai", precision=6
    ).utc
    if at >= data.leaps.expires:
        raise QualificationError("leap_resource_out_of_range")
    stamp = at.isot
    if stamp[17:19] == "60":
        raise QualificationError("utc_leap_second_not_supported_by_propagator_datetime")
    return stamp + "Z"


def gps_to_utc(parts, scale="GPS"):
    value = gps_value(parts, scale)
    try:
        with orientation() as (data, _):
            return to_utc(value, data)
    except TransformationError:
        raise QualificationError("required_local_time_resources_unavailable") from None


def time_audit(raw, scale):
    accepted, rejected, examples = 0, Counter(), {}
    first, last = None, None
    evaluated_at = datetime.now(UTC)
    with orientation() as (data, mode):
        for line in raw.decode("ascii").splitlines():
            if not line.startswith("*  "):
                continue
            try:
                converted = to_utc(gps_value(line.split()[1:], scale), data)
                accepted += 1
                if first is None:
                    first = converted
                last = converted
                examples.setdefault(
                    "ordinary", {"source_gps": line.strip(), "utc": converted}
                )
            except QualificationError as error:
                rejected[error.code] += 1
                examples.setdefault(
                    error.code, {"source_gps": line.strip(), "utc": None}
                )
        # Resource checks only, no spacecraft state or coordinate subtraction.
        checked = []
        for stamp in dict.fromkeys(x for x in (first, last) if x):
            checked.append(
                {
                    "at": stamp,
                    "parameters": parameters(
                        data, Time(stamp, scale="utc"), mode, now=evaluated_at
                    ),
                }
            )
        return {
            "status": "QUALIFIED_WITH_LIMITATIONS" if accepted else "BLOCKED",
            "scope": (
                "ordinary microsecond-representable epochs only; not dataset approval"
            ),
            "evaluated_at_utc": evaluated_at.isoformat(),
            "converted_count": accepted,
            "excluded_count": sum(rejected.values()),
            "exclusion_reasons": dict(rejected),
            "examples": examples,
            "first_converted_utc": first,
            "last_converted_utc": last,
            "source_epoch_order_preserved": True,
            "conversion_method": (
                "Astropy TimeGPS split seconds to UTC in existing orientation scope"
            ),
            "hard_coded_gps_utc_offset": False,
            "source_rounding_or_second_60_rollover": False,
            "resources": data.metadata,
            "eop_checks": {
                "scope": (
                    "converted interval endpoints with existing velocity support; "
                    "not all epochs"
                ),
                "results": checked,
            },
        }


def historical_candidate(raw=None, expected_sha256=None):
    if raw is None:
        return {
            "status": "BLOCKED",
            "reason": "historical_gp_not_supplied",
            "source_authenticated": False,
            "available_at": None,
            "retrieved_at": None,
            "forecast_eligible": False,
        }
    if (
        not isinstance(raw, bytes)
        or not 0 < len(raw) <= 65536
        or not isinstance(expected_sha256, str)
        or not SOURCE["HASH"].fullmatch(expected_sha256)
        or replay.digest(raw) != expected_sha256
    ):
        raise QualificationError("historical_input_integrity_or_size_invalid")
    try:
        _, elements = parse_response(raw, 39452)
    except (ValueError, IngestionError):
        raise QualificationError(
            "historical_input_not_supported_swarm_a_gp_json"
        ) from None
    return {
        "status": "PARTIAL",
        "reason": "parsed_candidate_is_not_authenticated_history",
        "catalog_id": elements.catalog_id,
        "orbital_epoch": elements.epoch.isoformat(),
        "payload_sha256": expected_sha256,
        "source_authenticated": False,
        "source_provenance": None,
        "retrieved_at": None,
        "available_at": None,
        "forecast_eligible": False,
        "scope": (
            "Existing one-record GP JSON parser only; no new TLE importer or DB write"
        ),
    }


def frame_qualification(declared):
    path = frame_transform_graph.find_shortest_path(TEME, ITRS)[0]
    return {
        "status": "BLOCKED" if declared == "IGb08" else "REJECTED",
        "source_frame": declared,
        "calculated_frame": "TEME",
        "existing_terrestrial_output": "ITRS",
        "existing_path": [cls.__name__ for cls in path] if path else [],
        "itrs_attributes": sorted(ITRS.frame_attributes),
        "installed_astropy_igb08_frame": frame_transform_graph.lookup_name("igb08")
        is not None,
        "reason": (
            "IGb08 datum alignment to ITRF2008 is documented, but no "
            "precision-scoped alignment from this pipeline is qualified"
        ),
        "identity_transform_assumed": False,
        "helmert_transform_implemented": False,
    }


def qualify(
    kinematic,
    validation,
    kinematic_sha256,
    validation_sha256,
    gp_raw=None,
    gp_sha256=None,
    *,
    csv_raw=None,
    csv_sha256=None,
    csv_provenance=None,
):
    if csv_raw is not None and gp_raw is not None:
        raise QualificationError("choose_one_explicit_gp_format")
    if (csv_raw is None) != (csv_sha256 is None):
        raise QualificationError("paired_csv_bytes_and_hash_required")
    inspected = SOURCE["inspect"](
        kinematic, validation, kinematic_sha256, validation_sha256
    )
    _, raw = SOURCE["unpack"](kinematic, kinematic_sha256, "KIN")
    temporal = time_audit(raw, inspected["sp3"]["time_system"])
    if csv_raw is not None:
        if not isinstance(csv_sha256, str) or replay.digest(csv_raw) != csv_sha256:
            raise QualificationError("csv_integrity_invalid")
        csv_tool = runpy.run_path(
            str(Path(__file__).with_name("inspect_historical_csv.py"))
        )
        historical = csv_tool["inspect_attachment"](csv_raw, csv_provenance)
        bounds = [
            datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            for stamp in (
                temporal["first_converted_utc"],
                temporal["last_converted_utc"],
            )
            if stamp
        ]
        historical["actual_reference_epoch_bound_diagnostics"] = [
            {
                "source_index": row["source_index"],
                "reference_bounds_utc": [point.isoformat() for point in bounds],
                "entire_converted_span_within_seven_days": bool(bounds)
                and all(
                    abs(
                        (
                            point - datetime.fromisoformat(row["orbital_epoch_utc"])
                        ).total_seconds()
                    )
                    <= 7 * 86400
                    for point in bounds
                ),
                "pairing_approved": False,
            }
            for row in historical["records"]
            if row["status"] == "CANDIDATE"
        ]
    else:
        historical = historical_candidate(gp_raw, gp_sha256)
    frame = frame_qualification(inspected["sp3"]["frame_declaration"])
    mandatory = {
        "source_integrity_and_identity_checked": True,
        "historical_input_authenticated_and_paired": False,
        "all_source_times_qualified": temporal["excluded_count"] == 0,
        "realization_alignment_qualified": frame["status"] == "QUALIFIED",
        "interval_quality_accepted": False,
        "product_documentation_discrepancies_resolved": False,
        "lineage_and_availability_assessed_for_actual_pair": False,
    }
    result = {
        "kind": "orbitiq_swarm_input_qualification",
        "schema_version": 1,
        "status": "BLOCKED",
        "comparison_ready": all(mandatory.values()),
        "qualification_tool_sha256": replay.digest(Path(__file__).read_bytes()),
        "source_inspector_sha256": inspected["tool_sha256"],
        "source_products": {
            k: inspected[k] for k in ("kinematic", "validation", "catalog_mapping")
        },
        "source_record_count": inspected["sp3"]["epoch_count"],
        "historical_input": historical,
        "time": temporal,
        "frame": frame,
        "mandatory_conditions": mandatory,
        "documentation_discrepancies": [
            "General ESA specification describes SP3-c; acquired file declares SP3-d.",
            "Nominal interval is zero; SP3-d specifies positive intervals.",
            "GPS second-60 encodings are not approved as GPS calendar timestamps.",
        ],
        "independence": "uncertain_without_actual_gp_lineage",
        "quality": (
            "Existing plots/header codes do not establish acceptance of KIN epochs"
        ),
        "adapter_operational": False,
        "normalized_observations": [],
        "residuals": None,
        "prediction_evaluations": 0,
        "prediction_uncertainty": "not_quantified",
        "environment": replay.environment(),
        "scope": (
            "Input qualification diagnostics only; no acquisition or accuracy benchmark"
        ),
    }
    if csv_raw is not None:
        result["qualification_gates"] = historical["qualification_gates"]
    return result


def read(path, bound=SOURCE["MAX_ZIP"]):
    if not path.is_absolute():
        raise QualificationError("absolute_input_path_required")
    with replay.directory(path.parent) as fd:
        return replay.read_file(fd, path.name, bound)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kinematic", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--kinematic-sha256", required=True)
    parser.add_argument("--validation-sha256", required=True)
    parser.add_argument("--gp-json", type=Path)
    parser.add_argument("--gp-sha256")
    parser.add_argument("--gp-csv", type=Path)
    parser.add_argument("--csv-sha256")
    parser.add_argument("--csv-metadata", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if not args.output.is_absolute() or bool(args.gp_json) != bool(args.gp_sha256):
            raise QualificationError("explicit_output_and_paired_gp_arguments_required")
        if (
            bool(args.gp_csv) != bool(args.csv_sha256)
            or (args.gp_csv and args.gp_json)
            or (args.csv_metadata and not args.gp_csv)
        ):
            raise QualificationError("explicit_paired_csv_arguments_required")
        result = qualify(
            read(args.kinematic),
            read(args.validation),
            args.kinematic_sha256,
            args.validation_sha256,
            read(args.gp_json, 65536) if args.gp_json else None,
            args.gp_sha256,
            csv_raw=read(args.gp_csv, 2 * 1024 * 1024) if args.gp_csv else None,
            csv_sha256=args.csv_sha256,
            csv_provenance=(
                json.loads(read(args.csv_metadata, 16384))
                if args.csv_metadata
                else None
            ),
        )
        if args.output != args.output.resolve():
            raise QualificationError("output_symlinks_not_supported")
        with replay.directory(args.output.parent) as fd:
            replay.write_file(fd, args.output.name, replay.encoded(result))
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "comparison_ready": False,
                    "ordinary_epochs_converted": result["time"]["converted_count"],
                }
            )
        )
        return 0  # Audit success, never comparison authorization.
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        RuntimeError,
        TransformationError,
        replay.BundleError,
    ):
        print('{"status":"qualification_audit_refused","comparison_ready":false}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
