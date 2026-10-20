"""Operator evidence bundles: bounded data, exact identities, no database on replay."""

import hashlib
import json
import os
import platform
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

import astropy_iers_data

from orbitiq.orbits import earth_orientation
from orbitiq.orbits.freshness import FreshnessPolicy, utc
from orbitiq.orbits.sampling import SamplingPolicy
from orbitiq.replay_contract import (
    MAX_TOTAL_BYTES,
    TOLERANCES,
    BundleError,
    BundleManifest,
    ReplaySettings,
)
from orbitiq.replay_isolation import ReplayIsolationError, offline_replay
from orbitiq.replay_json import decoded
from orbitiq.replay_validation import preflight
from orbitiq.reporting import InvestigationReport, parse_definition
from orbitiq.services import analysis, reports
from orbitiq.services.replay import compare_values, recalculate
from orbitiq.storage import StorageError, validate_snapshot

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FIELDS = {
    "id",
    "catalog_id",
    "object_name",
    "orbital_epoch",
    "retrieved_at",
    "source_url",
    "response_sha256",
    "raw_record",
    "normalized_record",
    "element_units",
    "validation_status",
    "validator_version",
    "sgp4_version",
    "snapshot_inserted_at",
}
PACKAGES = ("sgp4", "astropy", "pyerfa", "numpy", "astropy-iers-data")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


@contextmanager
def directory(path):
    path = Path(path)
    if not path.is_absolute():
        raise BundleError("Bundle directory must be absolute")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except NotADirectoryError:
        raise BundleError(
            "Expected a regular directory bundle, not an archive or link",
            "unsupported_format",
        ) from None
    try:
        yield fd
    finally:
        os.close(fd)


def read_file(fd, name, limit):
    if name != Path(name).name or name in {".", ".."}:
        raise BundleError("Unsafe bundle filename")
    try:
        handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    except FileNotFoundError:
        raise BundleError(
            "Required package member is missing", "missing_input", member=name
        ) from None
    try:
        info = os.fstat(handle)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
            raise BundleError("Bundle file is not a bounded regular file")
        with os.fdopen(handle, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
        if len(data) != info.st_size or len(data) > limit:
            raise BundleError("Bundle file changed or exceeds its limit")
        return data
    finally:
        os.close(handle)


def write_file(fd, name, data):
    handle = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
    )
    with os.fdopen(handle, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def environment():
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "packages": {name: version(name) for name in PACKAGES},
        "backend_sha256": {
            str(p.relative_to(ROOT)): digest(p.read_bytes())
            for p in sorted((ROOT / "backend/orbitiq").rglob("*.py"))
        },
        "uv_lock_sha256": digest((ROOT / "uv.lock").read_bytes()),
    }


def revision():
    def git(*args):
        result = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return result.stdout.strip()

    try:
        return {
            "head": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
            "platform": platform.system(),
            "machine": platform.machine(),
        }
    except (OSError, subprocess.SubprocessError):
        return {
            "head": None,
            "dirty": None,
            "platform": platform.system(),
            "machine": platform.machine(),
        }


def configured_settings():
    f, s = FreshnessPolicy.configured(), SamplingPolicy.configured()
    return ReplaySettings(
        eop_policy=os.environ.get("ORBITIQ_EOP_POLICY", "measured_or_predicted"),
        fresh_hours=float(f.fresh_hours),
        stale_hours=float(f.stale_hours),
        max_samples=s.max_samples,
        max_duration_seconds=s.max_duration_seconds,
    )


def references(definition):
    return [definition.source] + (
        [definition.comparison_source] if definition.mode == "comparison" else []
    )


def needs_eop(definition):
    return definition.mode == "ground-track" or (
        definition.mode == "comparison"
        and definition.at is not None
        and definition.frame == "ITRS"
    )


def allowed_files(count, eop):
    result = {"report.json": 8 * 1024 * 1024, "uv.lock": 2 * 1024 * 1024}
    for i in range(count):
        result[f"source-{i}.json"] = 128 * 1024
        result[f"source-{i}.response.json"] = 65536
    if eop:
        result.update({"iers-a.all": 8 * 1024 * 1024, "leap-seconds.dat": 128 * 1024})
    return result


@contextmanager
def resource_scope(files, settings, evaluated_at):
    if "iers-a.all" not in files:
        yield None
        return
    # Parse only the previously verified in-memory bytes; never reopen mutable inputs.
    with tempfile.TemporaryDirectory(prefix="orbitiq-replay-") as tmp:
        root = Path(tmp)
        for name in ("iers-a.all", "leap-seconds.dat"):
            (root / name).write_bytes(files[name])
        data = earth_orientation.load_resources(
            root / "iers-a.all",
            root / "leap-seconds.dat",
            version("astropy-iers-data"),
        )
        with earth_orientation.replay_orientation(
            data, settings.eop_policy, evaluated_at
        ):
            yield data


def capture(path, definition, destination):
    destination = Path(destination)
    if not destination.is_absolute():
        raise BundleError("Bundle directory must be absolute")
    if os.path.lexists(destination):
        raise FileExistsError("Evidence destination already exists")
    settings, evaluated_at, before = (
        configured_settings(),
        datetime.now(UTC),
        environment(),
    )
    files = {"uv.lock": (ROOT / "uv.lock").read_bytes()}
    terrestrial = needs_eop(definition)
    if terrestrial:
        files["iers-a.all"] = Path(astropy_iers_data.IERS_A_FILE).read_bytes()
        files["leap-seconds.dat"] = Path(
            astropy_iers_data.IERS_LEAP_SECOND_FILE
        ).read_bytes()
    with resource_scope(files, settings, evaluated_at):
        report = reports.build_report(path, definition)
    for i, ref in enumerate(references(definition)):
        item, _ = reports.checked_source(path, ref)
        if not reports.same_reference(ref, item):
            raise BundleError("Capture source identity changed")
        evidence = reports.source_evidence(
            ref, item, "primary" if i == 0 else "comparison", utc(report.generated_at)
        )
        if evidence != report.sources[i].model_dump(mode="json"):
            raise BundleError("Capture source metadata changed")
        files[f"source-{i}.json"] = encoded({k: item[k] for k in SOURCE_FIELDS})
        files[f"source-{i}.response.json"] = item["raw_response"]
    files["report.json"] = encoded(report.model_dump(mode="json"))
    for name, raw in files.items():
        if name.endswith(".json"):
            decoded(raw)  # A capture must obey the same JSON budgets as import.
    limits = allowed_files(len(report.sources), terrestrial)
    if set(files) != set(limits) or any(
        not 0 < len(v) <= limits[k] for k, v in files.items()
    ):
        raise BundleError("Capture exceeds file limits")
    if (
        sum(map(len, files.values())) > MAX_TOTAL_BYTES
        or environment() != before
        or configured_settings() != settings
    ):
        raise BundleError("Capture size exceeded or software changed during capture")
    manifest = BundleManifest(
        schema_version=1,
        kind="orbitiq_replay_bundle",
        capture_id=str(uuid4()),
        report_id=report.report_id,
        captured_at=datetime.now(UTC).isoformat(),
        policy_evaluated_at=evaluated_at.isoformat(),
        source_count=len(report.sources),
        eop_required=terrestrial,
        environment=before,
        source_revision=revision(),
        settings=settings,
        tolerances=TOLERANCES,
        files={
            name: {"sha256": digest(data), "bytes": len(data)}
            for name, data in files.items()
        },
    )
    raw_manifest = encoded(manifest.model_dump(mode="json"))
    if len(raw_manifest) > 128 * 1024:
        raise BundleError("Manifest exceeds its byte budget", "json_limit")
    decoded(raw_manifest, manifest=True)
    # All validation precedes exclusive creation. Never reuse or remove a destination.
    destination.mkdir(mode=0o700)
    with directory(destination) as fd:
        for name, data in files.items():
            write_file(fd, name, data)
        write_file(
            fd, "manifest.json", raw_manifest
        )  # Completion marker, written last.
        os.fsync(fd)
    return {
        "status": "captured",
        "capture_id": manifest.capture_id,
        "report_id": report.report_id,
        "report_status": report.status,
        "manifest_sha256": digest(raw_manifest),
        "files": len(files),
    }


def verified_inputs(destination, expected_manifest_sha256):
    with directory(destination) as fd:
        raw_manifest = read_file(fd, "manifest.json", 128 * 1024)
        manifest_hash = digest(raw_manifest)
        if (
            expected_manifest_sha256 is not None
            and expected_manifest_sha256 != manifest_hash
        ):
            raise BundleError("Trusted manifest checksum does not match")
        document = decoded(raw_manifest, manifest=True)
        if not isinstance(document, dict):
            raise BundleError("Manifest must be an object", "manifest_invalid")
        if (
            type(document.get("schema_version")) is not int
            or document["schema_version"] != 1
        ):
            raise BundleError(
                "Missing or unsupported manifest version",
                "unsupported_manifest_version",
            )
        if document.get("kind") != "orbitiq_replay_bundle":
            raise BundleError(
                "Missing or unsupported evidence format", "unsupported_format"
            )
        manifest = BundleManifest.model_validate(document)
        limits = allowed_files(manifest.source_count, manifest.eop_required)
        if set(manifest.files) != set(limits):
            missing = set(limits) - set(manifest.files)
            raise BundleError(
                "Manifest member set is incomplete or unsupported",
                "member_set_invalid",
                member=sorted(missing)[0] if missing else None,
            )
        found = set()
        with os.scandir(fd) as entries:
            for entry in entries:
                # Stop at the first unexpected member, without allocating an
                # unbounded directory listing or echoing untrusted filenames.
                if entry.name not in set(limits) | {"manifest.json"}:
                    raise BundleError("Unexpected package member", "unexpected_member")
                found.add(entry.name)
        missing = set(limits) - found
        if missing:
            name = sorted(missing)[0]
            raise BundleError(
                "Required package member is missing", "missing_input", member=name
            )
        if sum(v.bytes for v in manifest.files.values()) > MAX_TOTAL_BYTES:
            raise BundleError("Bundle total size exceeds limit")
        files = {}
        for name, identity in manifest.files.items():
            raw = read_file(fd, name, limits[name])
            if len(raw) != identity.bytes or digest(raw) != identity.sha256:
                raise BundleError(
                    "Bundle file checksum or size mismatch",
                    "file_integrity_mismatch",
                    member=name,
                )
            files[name] = raw
    if manifest.tolerances != TOLERANCES:
        raise BundleError("Unsupported replay tolerances")
    if (
        manifest.environment != environment()
        or digest(files["uv.lock"]) != manifest.environment["uv_lock_sha256"]
    ):
        raise BundleError(
            "Installed software, backend code or dependency lock differs",
            "runtime_incompatible",
        )
    FreshnessPolicy(manifest.settings.fresh_hours, manifest.settings.stale_hours)
    report_document = decoded(files["report.json"])
    if not isinstance(report_document, dict) or any(
        type(report_document.get(k)) is not int or report_document[k] != 1
        for k in ("schema_version", "template_version")
    ):
        raise BundleError(
            "Missing or unsupported report format version", "unsupported_report_version"
        )
    if set(report_document) != set(InvestigationReport.model_fields):
        raise BundleError(
            "Report fields are incomplete or unsupported", "report_contract_invalid"
        )
    report = InvestigationReport.model_validate(report_document)
    if (
        report.methodology.get("software_versions")
        != {
            k: manifest.environment["packages"][k]
            for k in ("sgp4", "astropy", "pyerfa")
        }
        or report.validation.get("prediction_uncertainty") != "unquantified"
        or report.validation.get("independent_observation_validation") != "blocked"
        or report.validation.get("report_generation_is_scientific_certification")
        is not False
    ):
        raise BundleError(
            "Recorded software or scientific limitations are contradictory",
            "report_contract_invalid",
        )
    d = parse_definition(
        json.dumps(report.investigation.definition.model_dump(mode="json"))
    )
    refs = references(d)
    if (
        report.report_id != manifest.report_id
        or len(refs) != manifest.source_count
        or len(report.sources) != len(refs)
        or needs_eop(d) != manifest.eop_required
        or utc(report.generated_at) is None
    ):
        raise BundleError("Report identity or applicability differs from manifest")
    if report.methodology.get("eop_applicability") != (
        "required" if manifest.eop_required else "not_applicable"
    ) or report.methodology.get("configured_eop_policy") != (
        manifest.settings.eop_policy if manifest.eop_required else None
    ):
        raise BundleError(
            "Declared EOP configuration differs from saved settings",
            "scientific_input_invalid",
            field="methodology",
        )
    if not mtime_order(manifest, report):
        raise BundleError("Capture and report clocks are inconsistent")
    canonical = json.dumps(
        d.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    if report.investigation.id != "configuration-sha256:" + digest(canonical.encode()):
        raise BundleError("Investigation configuration identity differs")
    expected_status = (
        "not_requested"
        if d.mode == "snapshot" or (d.mode == "comparison" and d.at is None)
        else "complete"
    )
    if report.status == "complete" and report.calculation.status != expected_status:
        raise BundleError("Report calculation status is inconsistent")
    captured = []
    for i, ref in enumerate(refs):
        item = decoded(files[f"source-{i}.json"])
        if not isinstance(item, dict) or set(item) != SOURCE_FIELDS:
            raise BundleError("Unexpected archived source fields")
        if type(item["id"]) is not int or type(item["catalog_id"]) is not int:
            raise BundleError("Source identity must use integer identifiers")
        item["raw_response"] = files[f"source-{i}.response.json"]
        decoded(item["raw_response"])  # Reject duplicate fields/nonfinite literals too.
        elements = validate_snapshot(item)
        if not reports.same_reference(ref, item):
            raise BundleError("Exact source identity differs from definition")
        evidence = reports.source_evidence(
            ref,
            item,
            "primary" if i == 0 else "comparison",
            utc(report.generated_at),
            freshness_policy=FreshnessPolicy(
                manifest.settings.fresh_hours, manifest.settings.stale_hours
            ),
        )
        if evidence != report.sources[i].model_dump(mode="json"):
            raise BundleError("Report source evidence differs from validated source")
        captured.append((item, elements))
    return manifest, manifest_hash, files, report, d, captured


def mtime_order(manifest, report):
    """Historical policy evaluation is fixed before the captured calculation."""
    return (
        manifest.policy_evaluated_at <= utc(report.generated_at) <= manifest.captured_at
    )


def verify(destination, expected_manifest_sha256=None, *, validation_only=False):
    """Validate first, then replay inside an explicit scoped offline policy."""
    with offline_replay() as attempts:
        result = _verify(destination, expected_manifest_sha256, validation_only)
    result["verification_completed_at"] = datetime.now(UTC).isoformat()
    result["offline_policy"] = {
        "scope": "scoped_python_audit_socket_sqlite_process_denial_v1",
        "attempts": attempts,
        "os_sandbox": False,
    }
    if any(attempts.values()):
        result.update(
            status="blocked",
            numerical_outcome="unverifiable",
            code="offline_operation_forbidden",
        )
    return result


def _verify(destination, expected_manifest_sha256, validation_only):
    result = {
        "schema_version": 1,
        "status": "blocked",
        "numerical_outcome": "unverifiable",
        "verified_at": datetime.now(UTC).isoformat(),
        "integrity_scope": "trusted_manifest_sha256"
        if expected_manifest_sha256
        else "self_consistency_only",
        "provider_authenticity": "not_independently_verified",
        "prediction_uncertainty": "unquantified",
        "independent_observation_validation": "blocked",
        "current_eop_readiness_checked": False,
        "numeric_values_checked": 0,
        "validation": {"status": "pending", "stage": "package_validation"},
        "replay_started_at": None,
    }
    try:
        m, sha, files, report, definition, captured = verified_inputs(
            destination, expected_manifest_sha256
        )
        result.update(
            capture_id=m.capture_id,
            report_id=m.report_id,
            manifest_sha256=sha,
            policy_evaluated_at=m.policy_evaluated_at.isoformat(),
            tolerances=TOLERANCES,
            runtime_code_lock_match=True,
            provenance={
                "package_created_at": m.captured_at.isoformat(),
                "original_report_generated_at": report.generated_at,
                "source_references": [
                    r.model_dump(mode="json") for r in references(definition)
                ],
                "requested_calculation": definition.model_dump(mode="json"),
                "original_calculation_times": None,
            },
        )
        result["validation"] = {"status": "pending", "stage": "scientific_preflight"}
        with resource_scope(files, m.settings, m.policy_evaluated_at) as resource:
            expected, clocks = preflight(m, report, definition, captured, resource)
            result["provenance"]["original_calculation_times"] = clocks
            result["resources"] = {
                "status": "validated" if resource else "not_applicable",
                "metadata": resource.metadata if resource else None,
                "files": {
                    k: v.model_dump()
                    for k, v in m.files.items()
                    if k in {"iers-a.all", "leap-seconds.dat"}
                },
            }
            result["validation"] = {
                "status": "passed",
                "stage": "before_orbital_replay",
                "checks": [
                    "format_and_version",
                    "bounded_files_and_json",
                    "file_hashes",
                    "runtime_code_lock",
                    "exact_sources",
                    "definition_and_clocks",
                    "result_frames_units_and_lineage",
                    "applicable_resource_identities",
                ],
            }
            if validation_only:
                return {
                    **result,
                    "status": "validated",
                    "numerical_outcome": "not_performed",
                }
            if (
                report.status != "complete"
                or report.calculation.status == "unavailable"
            ):
                return {
                    **result,
                    "status": "unavailable",
                    "reason": "Original report calculation unavailable; "
                    "no numerical pass",
                }
            result["replay_started_at"] = datetime.now(UTC).isoformat()
            actual = recalculate(definition, captured, m.settings)
        comparison = compare_values(expected, actual)
        source_only = definition.mode == "snapshot" or (
            definition.mode == "comparison" and definition.at is None
        )
        status = (
            "mismatch"
            if comparison["mismatch_count"]
            else ("verified_source_only" if source_only else "matched")
        )
        result.update(
            comparison,
            status=status,
            numerical_outcome=comparison["outcome"]
            if not source_only or status == "mismatch"
            else "not_applicable_source_only",
            expected_projection_sha256=digest(encoded(expected)),
            actual_projection_sha256=digest(encoded(actual)),
        )
        if environment() != m.environment:
            raise BundleError(
                "Installed runtime changed during verification", "runtime_incompatible"
            )
        return result
    except BundleError as error:
        result.update(
            status="blocked",
            numerical_outcome="unverifiable",
            reason=str(error),
            code=error.code,
        )
        result["validation"]["status"] = "failed"
        if error.member:
            result["required_member"] = error.member
            result["affected_calculation"] = (
                "terrestrial_transform"
                if error.member in {"iers-a.all", "leap-seconds.dat"}
                else "source_based_calculation"
                if error.member.startswith("source-")
                else "package_verification"
            )
        if error.field:
            result["field"] = error.field
        return result
    except ReplayIsolationError as error:
        return {
            **result,
            "status": "blocked",
            "numerical_outcome": "unverifiable",
            "code": "offline_operation_forbidden",
            "reason": str(error),
        }
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        OverflowError,
        AttributeError,
        analysis.AnalysisError,
        StorageError,
        RecursionError,
        IndexError,
    ):
        result["validation"]["status"] = "failed"
        return {
            **result,
            "status": "blocked",
            "numerical_outcome": "unverifiable",
            "code": "invalid_or_unavailable_input",
            "reason": "Required package input, runtime or calculation "
            "is invalid or unavailable",
        }
