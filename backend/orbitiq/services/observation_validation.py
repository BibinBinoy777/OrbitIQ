"""Operator-only immutable validation packages and read-only API inspection."""

import json
import os
import re
import shutil
from datetime import UTC, datetime

from pydantic import ValidationError

from orbitiq import observation_validation as science
from orbitiq import replay
from orbitiq.orbits.freshness import utc
from orbitiq.replay_contract import MAX_TOTAL_BYTES, BundleError, BundleManifest
from orbitiq.replay_json import decoded
from orbitiq.reporting import InvestigationReport, SourceReference, parse_definition
from orbitiq.services import analysis

MEMBERS = {"manifest.json", "observations.json", "report.json"}
ID = re.compile(r"[a-f0-9]{32}")


def source_reference(item):
    return SourceReference.model_validate(
        {
            "snapshot_id": item["id"],
            **{
                k: item[k]
                for k in (
                    "catalog_id",
                    "response_sha256",
                    "orbital_epoch",
                    "retrieved_at",
                )
            },
        }
    ).model_dump(mode="json")


def prediction_definition(ref, observation):
    d = {
        "schema_version": 1,
        "source": ref,
        "at": observation.observed_at.isoformat(),
        "frame": observation.frame,
    }
    if observation.frame == "TEME":
        return {**d, "mode": "position"}
    # Reuse an exact self-comparison to capture one supported ITRS prediction.
    # It is a propagation self-check, never a second independent observation.
    return {**d, "mode": "comparison", "comparison_source": ref, "category": "all"}


def summarize(samples):
    compatible = [s for s in samples if s["status"] == "compatible_with_warnings"]
    groups = {
        frame: science.statistics(
            [s["residual"] for s in compatible if s["frame"] == frame]
        )
        for frame in ("TEME", "ITRS")
    }
    epochs = sorted(utc(s["observation"]["observed_at"]) for s in compatible)
    return {
        "requested_count": len(samples),
        "compatible_coverage": {
            "oldest_observed_at": epochs[0].isoformat() if epochs else None,
            "newest_observed_at": epochs[-1].isoformat() if epochs else None,
            "sampling_intervals_seconds": [
                (b - a).total_seconds()
                for a, b in zip(epochs, epochs[1:], strict=False)
            ],
            "missing_intervals": "unknown_no_expected_measurement_cadence",
            "error_trend_statistic": None,
        },
        "compatible_count": len(compatible),
        "excluded_count": len(samples) - len(compatible),
        "independently_verified_count": 0,
        "all_candidates_unavailable": not compatible,
        "descriptive_discrepancy_by_frame": groups,
        "independent_error_metrics": None,
        "independent_validation_status": "not_established",
        "exclusion_policy": (
            "All incompatible, duplicate, invalid or failed samples are "
            "listed with reasons. Unknown independence does not become "
            "verified."
        ),
    }


def findings(samples, summary):
    result = []
    for sample in samples:
        f = {
            "schema_version": 1,
            "rule_id": "observation.position_discrepancy"
            if sample["residual"]
            else "observation.validation_unavailable",
            "rule_version": 1,
            "status": sample["status"],
            "severity": None,
            "confidence": None,
            "observation_index": sample["index"],
            "observation_reference": sample["observation"],
            "prediction_reference": sample["prediction_reference"],
            "checks": sample["checks"],
            "result": sample["residual"],
            "frame": sample.get("frame"),
            "unit": "km" if sample["residual"] else None,
            "uncertainty": sample.get("uncertainty"),
            "independence": sample["independence"],
            "explanation": (
                "Recorded position discrepancy is "
                + str(sample["residual"]["magnitude_km"])
                + (
                    " km at the common epoch. Independence and joint uncertainty "
                    "are not established; no physical cause or accuracy "
                    "classification is inferred."
                )
            )
            if sample["residual"]
            else "No residual was calculated: " + sample["reason"],
            "evidence": {
                "prediction_bundle": sample.get("prediction_bundle"),
                "manifest_sha256": sample.get("prediction_manifest_sha256"),
                "observation_input": "observations.json",
            },
            "limitations": science.LIMITATIONS,
        }
        f["finding_id"] = "observation-finding-sha256:" + science.identity(f)
        result.append(f)
    return result


def create(path, raw, destination, *, now=None):
    records = science.parse_input(raw)
    if not destination.is_absolute() or not ID.fullmatch(destination.name):
        raise ValueError(
            "Use a new absolute package directory named by 32 lowercase hex characters"
        )
    now = utc(now) if now else datetime.now(UTC)
    if now is None:
        raise ValueError("Evaluation time must be timezone-aware")
    # Prediction source is provided separately in the operator's path tuple.
    database, snapshot_id = path
    item, _ = analysis.load_snapshot(database, snapshot_id)
    ref = source_reference(item)
    destination.mkdir(
        mode=0o700
    )  # Exclusive reservation; no overwrites or implicit DB setup.
    samples = []
    duplicates = science.duplicate_indices(records)
    for index, record in enumerate(records):
        sample = {
            "index": index,
            "observation": None,
            "original_record": record,
            "status": "invalid_input",
            "reason": "Observation does not meet the bounded version-1 schema.",
            "checks": {},
            "prediction_reference": ref,
            "prediction": None,
            "residual": None,
            "independence": {"status": "unverified", "eligible": False},
            "uncertainty": None,
        }
        samples.append(sample)
        try:
            observation = science.Observation.model_validate(record)
        except ValidationError:
            continue
        sample["observation"] = observation.model_dump(mode="json")
        sample["frame"] = observation.frame
        checks = science.compatible(observation, item, now)
        sample["checks"] = checks
        sample["independence"] = science.independence(observation, item)
        if index in duplicates:
            sample.update(
                status="duplicate_observation",
                reason=(
                    "Observation ID or underlying source record is "
                    "duplicated/ambiguous in this run; all copies excluded."
                ),
            )
            continue
        if not all(checks.values()):
            sample.update(
                status="incompatible_input",
                reason="Failed compatibility checks: "
                + ", ".join(k for k, v in checks.items() if not v),
            )
            continue
        if sample["independence"]["status"] == "reused_prediction_payload":
            sample.update(
                status="reused_input",
                reason=(
                    "Observation declares the same payload as the prediction "
                    "input; no independent validation is possible."
                ),
            )
            continue
        definition = prediction_definition(ref, observation)
        folder = destination / f"prediction-{index}"
        try:
            captured = replay.capture(
                database, parse_definition(json.dumps(definition)), folder
            )
            sample.update(
                prediction_bundle=folder.name,
                prediction_manifest_sha256=captured["manifest_sha256"],
            )
            report = decoded((folder / "report.json").read_bytes())
            state = report["calculation"]["data"]
            if definition["mode"] == "comparison":
                state = (state or {}).get("state_comparison", {}).get("first")
            if report["calculation"]["status"] == "unavailable" or state is None:
                sample.update(
                    status="calculation_failed",
                    reason=(
                        "Existing propagation or strict resource policy rejected this"
                        " epoch; captured report records exact errors."
                    ),
                    prediction_bundle=folder.name,
                    prediction_manifest_sha256=captured["manifest_sha256"],
                )
                continue
            if (
                state["frame"] != observation.frame
                or utc(state["at"]) != observation.observed_at
                or state["units"]["position"] != "km"
                or state["kind"] != "calculated"
            ):
                raise ValueError(
                    "Prediction state does not match requested epoch/frame/units"
                )
            factor = 0.001 if observation.unit == "m" else 1.0
            observed = [v * factor for v in observation.position]
            delta = science.residual(state["position_km"], observed)
            delta["rac"] = science.rac(
                delta["xyz_km"],
                state["position_km"],
                state["velocity_km_s"],
                state["frame"],
            )
            sigma = observation.uncertainty
            sample.update(
                status="compatible_with_warnings",
                reason=(
                    "Compatible discrepancy; independently validated prediction "
                    "accuracy is not established."
                ),
                prediction=state,
                residual=delta,
                prediction_bundle=folder.name,
                prediction_manifest_sha256=captured["manifest_sha256"],
                prediction_definition=definition,
                prediction_id=report["report_id"],
                prediction_generated_at=report["generated_at"],
                prediction_horizon_from_input_epoch_seconds=(
                    observation.observed_at - utc(item["orbital_epoch"])
                ).total_seconds(),
                holdout_from_retrieval_seconds=(
                    observation.observed_at - utc(item["retrieved_at"])
                ).total_seconds(),
                normalized_observation_position_km=observed,
                uncertainty={
                    "observation": sigma.model_dump(mode="json") if sigma else None,
                    "normalized_sigma_km": [
                        v * (0.001 if sigma.unit == "m" else 1) for v in sigma.values
                    ]
                    if sigma
                    else None,
                    "prediction": None,
                    "joint_status": "unavailable_prediction_uncertainty",
                    "weighted_statistics": False,
                },
            )
        except (
            BundleError,
            analysis.AnalysisError,
            ValueError,
            OSError,
            KeyError,
            TypeError,
        ):
            if folder.exists() and not sample.get("prediction_bundle"):
                shutil.rmtree(folder)  # Only a newly reserved child of our private run.
            sample.update(
                status="calculation_failed",
                reason=(
                    "Required propagation/capture inputs are unavailable or "
                    "invalid; no substitute calculation was used."
                ),
            )
    current, _ = analysis.load_snapshot(database, snapshot_id)
    if source_reference(current) != ref:
        raise ValueError(
            "Prediction source changed during validation; package is incomplete"
        )
    summary = summarize(samples)
    report = {
        "kind": "orbitiq_observation_validation_report",
        "schema_version": 1,
        "rule_set_version": 1,
        "report_id": destination.name,
        "generated_at": now.isoformat(),
        "status": "discrepancies_with_unverified_independence"
        if summary["compatible_count"]
        else "unavailable",
        "prediction_source": ref,
        "prediction_kind": "retrospective_SGP4_WGS72_from_archived_GP",
        "input_sha256": replay.digest(raw),
        "input_representation": (
            "operator_normalized_observations_not_authenticated_provider_payload"
        ),
        "samples": samples,
        "summary": summary,
        "findings": findings(samples, summary),
        "software": replay.environment(),
        "limitations": science.LIMITATIONS,
        "reproduction": {
            "status": "captured_not_yet_replayed",
            "prediction_scope": (
                "Exact nested Phase 10 packages; arithmetic can be checked "
                "against preserved states and observation input."
            ),
            "original_observation_bytes": "observations.json",
        },
    }
    content = replay.encoded(report)
    if len(content) > science.MAX_REPORT:
        raise ValueError("Validation report exceeds limit; package incomplete")
    with replay.directory(destination) as fd:
        replay.write_file(fd, "observations.json", raw)
        replay.write_file(fd, "report.json", content)
        manifest = {
            "kind": "orbitiq_observation_validation_package",
            "schema_version": 1,
            "files": {
                name: {"sha256": replay.digest(data), "bytes": len(data)}
                for name, data in (("observations.json", raw), ("report.json", content))
            },
            "predictions": {
                s["prediction_bundle"]: s["prediction_manifest_sha256"]
                for s in samples
                if s.get("prediction_bundle")
            },
        }
        replay.write_file(fd, "manifest.json", replay.encoded(manifest))
    return report


def read_package(path, expected_manifest_sha256=None):
    with replay.directory(path) as fd:
        manifest_bytes = replay.read_file(fd, "manifest.json", 16384)
        if (
            expected_manifest_sha256 is not None
            and replay.digest(manifest_bytes) != expected_manifest_sha256
        ):
            raise ValueError("Trusted validation manifest hash mismatch")
        manifest = decoded(manifest_bytes)
        if (
            manifest.get("kind") != "orbitiq_observation_validation_package"
            or type(manifest.get("schema_version")) is not int
            or manifest["schema_version"] != 1
            or set(manifest.get("files", {})) != {"observations.json", "report.json"}
        ):
            raise ValueError("Unsupported validation package")
        predictions = manifest.get("predictions", {})
        if (
            not isinstance(predictions, dict)
            or len(predictions) > science.MAX_SAMPLES
            or any(
                not re.fullmatch(r"prediction-[0-9]", k)
                or not re.fullmatch(r"[a-f0-9]{64}", str(v))
                for k, v in predictions.items()
            )
        ):
            raise ValueError("Invalid nested prediction references")
        allowed = MEMBERS | set(predictions)
        names = []
        with os.scandir(fd) as entries:
            for e in entries:
                names.append(e.name)
                if len(names) > len(allowed) or e.name not in allowed or e.is_symlink():
                    raise ValueError("Unexpected package member")
        if set(names) != allowed:
            raise ValueError("Incomplete package")
        values = {}
        for name, bound in (
            ("observations.json", science.MAX_INPUT),
            ("report.json", science.MAX_REPORT),
        ):
            raw = replay.read_file(fd, name, bound)
            if manifest["files"][name] != {
                "sha256": replay.digest(raw),
                "bytes": len(raw),
            }:
                raise ValueError("Validation package integrity mismatch")
            values[name] = decoded(raw)
        report = values["report.json"]
        if (
            report.get("kind") != "orbitiq_observation_validation_report"
            or report.get("schema_version") != 1
            or report.get("report_id") != path.name
            or not isinstance(report.get("samples"), list)
            or not 1 <= len(report["samples"]) <= science.MAX_SAMPLES
            or report["input_sha256"]
            != manifest["files"]["observations.json"]["sha256"]
            or [s["original_record"] for s in report["samples"]]
            != values["observations.json"].get("observations")
        ):
            raise ValueError("Validation report input lineage mismatch")
        if report["summary"] != summarize(report["samples"]) or report[
            "findings"
        ] != findings(report["samples"], report["summary"]):
            raise ValueError("Report findings/summary do not match captured samples")
        nested = {
            name: inspect_prediction(path / name, sha)
            for name, sha in predictions.items()
        }
        duplicate_set = science.duplicate_indices(
            values["observations.json"]["observations"]
        )
        for sample in report["samples"]:
            if sample["residual"] is None:
                continue
            obs = science.Observation.model_validate(sample["original_record"])
            expected_ref = SourceReference.model_validate(report["prediction_source"])
            source = {
                **expected_ref.model_dump(mode="json"),
                "id": expected_ref.snapshot_id,
            }
            if (
                sample["index"] in duplicate_set
                or sample["observation"] != obs.model_dump(mode="json")
                or sample["checks"]
                != science.compatible(obs, source, utc(report["generated_at"]))
                or not all(sample["checks"].values())
                or sample["independence"] != science.independence(obs, source)
            ):
                raise ValueError("Observation input or compatibility lineage mismatch")
            inner = nested[sample["prediction_bundle"]]
            definition = prediction_definition(
                expected_ref.model_dump(mode="json"), obs
            )
            if inner["investigation"]["definition"] != parse_definition(
                json.dumps(definition)
            ).model_dump(mode="json"):
                raise ValueError("Nested prediction definition mismatch")
            state = inner["calculation"]["data"]
            if definition["mode"] == "comparison":
                state = state["state_comparison"]["first"]
            observed = [v * (0.001 if obs.unit == "m" else 1) for v in obs.position]
            if (
                sample["prediction"] != state
                or sample["normalized_observation_position_km"] != observed
            ):
                raise ValueError(
                    "Prediction/observation values differ from preserved inputs"
                )
            delta = science.residual(state["position_km"], observed)
            delta["rac"] = science.rac(
                delta["xyz_km"],
                state["position_km"],
                state["velocity_km_s"],
                state["frame"],
            )
            if delta != sample["residual"]:
                raise ValueError("Residual differs from preserved inputs")
        return report, manifest


def archive_listing(root):
    if root is None:
        return {
            "status": "not_configured",
            "runs": [],
            "observation_count": None,
            "genuine_observations_verified": 0,
            "message": (
                "No observation validation archive is configured. Orbital "
                "snapshots are not independent observations."
            ),
        }
    names = []
    with os.scandir(root) as entries:
        for entry in entries:
            if (
                len(names) >= 100
                or not ID.fullmatch(entry.name)
                or not entry.is_dir(follow_symlinks=False)
            ):
                raise ValueError(
                    (
                        "Validation archive must contain at most 100 fixed-name run "
                        "directories"
                    )
                )
            names.append(entry.name)
    return {
        "status": "available" if names else "empty",
        "runs": sorted(names),
        "observation_count": None,
        "genuine_observations_verified": 0,
        "message": (
            "Select a captured run. Counts and independence must be "
            "assessed from its actual evidence."
        ),
    }


def inspect_prediction(path, expected_manifest_sha256):
    """Reuse fixed replay member budgets; inspect saved results across code versions.

    This verifies byte integrity only. The existing replay verifier separately
    enforces exact runtime/scientific preflight when the operator requests replay.
    """
    with replay.directory(path) as fd:
        raw = replay.read_file(fd, "manifest.json", 128 * 1024)
        if replay.digest(raw) != expected_manifest_sha256:
            raise ValueError("Nested manifest hash mismatch")
        manifest = BundleManifest.model_validate(decoded(raw, manifest=True))
        limits = replay.allowed_files(manifest.source_count, manifest.eop_required)
        if (
            set(manifest.files) != set(limits)
            or sum(v.bytes for v in manifest.files.values()) > MAX_TOTAL_BYTES
        ):
            raise ValueError("Invalid nested prediction layout")
        names = set()
        with os.scandir(fd) as entries:
            for e in entries:
                if e.name not in set(limits) | {"manifest.json"}:
                    raise ValueError("Unexpected nested member")
                names.add(e.name)
        if names != set(limits) | {"manifest.json"}:
            raise ValueError("Missing nested prediction member")
        report = None
        for name, identity in manifest.files.items():
            content = replay.read_file(fd, name, limits[name])
            if (
                len(content) != identity.bytes
                or replay.digest(content) != identity.sha256
            ):
                raise ValueError("Nested prediction file hash mismatch")
            if name == "report.json":
                report = InvestigationReport.model_validate(
                    decoded(content)
                ).model_dump(mode="json")
        return report
