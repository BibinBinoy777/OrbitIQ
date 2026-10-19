import { formatUtc } from "./time-presentation";
export type ReadinessStatus =
  "healthy" | "degraded" | "unavailable" | "unknown";
export const readinessKeys = [
  "database",
  "orbital_data",
  "ingestion",
  "eop",
  "leap_seconds",
] as const;
export interface ReadinessComponent {
  status: ReadinessStatus;
  code: string;
  message: string;
  [key: string]: unknown;
}
export interface ReadinessResult {
  status: ReadinessStatus;
  kind: "calculated_readiness_assessment";
  evaluated_at: string;
  requested_at: string;
  components: Record<(typeof readinessKeys)[number], ReadinessComponent>;
  automatic_updates: false;
  scope: string;
}
function object(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null;
}
function status(v: unknown): v is ReadinessStatus {
  return ["healthy", "degraded", "unavailable", "unknown"].includes(String(v));
}
export function parseReadiness(value: unknown): ReadinessResult {
  if (
    !object(value) ||
    !status(value.status) ||
    value.kind !== "calculated_readiness_assessment" ||
    value.automatic_updates !== false ||
    !object(value.components) ||
    typeof value.evaluated_at !== "string" ||
    formatUtc(value.evaluated_at) === "Unavailable" ||
    typeof value.requested_at !== "string" ||
    formatUtc(value.requested_at) === "Unavailable"
  )
    throw new Error("Unexpected readiness response. Try refreshing.");
  let partial = false;
  const components = Object.fromEntries(
    readinessKeys.map((key) => {
      const raw = value.components as Record<string, unknown>;
      const c = raw[key];
      if (
        !object(c) ||
        !status(c.status) ||
        typeof c.code !== "string" ||
        typeof c.message !== "string" ||
        c.message.length > 500
      ) {
        partial = true;
        return [
          key,
          {
            status: "unknown",
            code: "section_missing",
            message:
              "This section was not provided reliably. Retry or ask an operator to inspect the service.",
          },
        ];
      }
      return [key, c];
    }),
  ) as ReadinessResult["components"];
  return {
    status: partial ? "unknown" : value.status,
    kind: "calculated_readiness_assessment",
    evaluated_at: value.evaluated_at,
    requested_at: value.requested_at,
    components,
    automatic_updates: false,
    scope:
      typeof value.scope === "string"
        ? value.scope
        : "Resource assessment only; not an observation or orbit-accuracy guarantee.",
  };
}
export async function getReadiness(
  at: string,
  signal: AbortSignal,
): Promise<ReadinessResult> {
  const suffix = at ? `?${new URLSearchParams({ at })}` : "";
  const response = await fetch(`/api/readiness${suffix}`, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(5000)]),
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error(
      response.status === 422
        ? "Use a valid ISO timestamp with a timezone, then refresh."
        : `Readiness service unavailable (${response.status}). Retry or ask an operator to inspect it.`,
    );
  return parseReadiness(await response.json());
}
