// Synthetic UI fixture, never an observation or a live resource assessment.
import type { ReadinessResult, ReadinessStatus } from "../readiness-api";
export function readinessFixture(
  status: ReadinessStatus = "healthy",
): ReadinessResult {
  const base = {
    status,
    code: "fixture",
    message: "Synthetic fixture assessment.",
  };
  return {
    status,
    kind: "calculated_readiness_assessment",
    automatic_updates: false,
    evaluated_at: "2026-10-19T00:00:00+00:00",
    requested_at: "2026-10-19T00:00:00+00:00",
    scope:
      "Metadata assessment only; not an observation or orbit accuracy guarantee.",
    components: {
      database: {
        ...base,
        reachable: true,
        schema_available: true,
        reads_available: true,
        latest_stored_retrieved_at: "2026-10-18T23:00:00Z",
      },
      orbital_data: {
        ...base,
        snapshots_present: true,
        global_latest_known: true,
        latest_retrieval_at: "2026-10-18T23:00:00Z",
        orbital_epoch: "2026-10-18T22:00:00Z",
        retrieval_age_seconds: 3600,
        freshness: {
          state: "recent",
          epoch_age_seconds: 7200,
          fresh_hours: 24,
          stale_hours: 72,
        },
      },
      ingestion: {
        ...base,
        latest_attempt_outcome: "deduplicated",
        latest_payload_outcome: "deduplicated",
        last_attempt_at: "2026-10-18T23:00:00Z",
        last_attempt_completed_at: "2026-10-18T23:00:02Z",
        last_successful_acquisition_at: "2026-10-18T23:00:01Z",
        last_successful_validation_at: "2026-10-18T23:00:02Z",
        last_snapshot_insertion_at: "2026-10-18T21:00:00Z",
        consecutive_failures: 0,
        retry_budget_exhausted: false,
        next_allowed_at: "2026-10-19T01:00:01Z",
        orbital_freshness_state: "fresh",
      },
      eop: {
        ...base,
        source: "Fixture EOP",
        package_version: "fixture-only",
        covered: true,
        first_covered_at: "1973-01-02T00:00:00Z",
        last_covered_at: "2027-10-03T00:00:00Z",
        prediction_starts_at: "2026-10-02T00:00:00Z",
        prediction_table_age_days: 17,
        max_prediction_table_age_days: 30,
        sha256: "a".repeat(64),
        requested_eop_type: "measured",
      },
      leap_seconds: {
        ...base,
        source: "Fixture leap file",
        package_version: "fixture-only",
        expiry_known: true,
        expires_at: "2027-06-27T23:59:23Z",
        expires_in_days: 250,
        source_expiry_label: "2027-06-28",
        source_expiry_scale: "tai",
        sha256: "b".repeat(64),
      },
    },
  };
}
