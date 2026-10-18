export async function getHealth(signal?: AbortSignal): Promise<string> {
  const requestSignal = AbortSignal.any([
    AbortSignal.timeout(5000),
    ...(signal ? [signal] : []),
  ]);
  const response = await fetch("/api/health", { signal: requestSignal });
  if (!response.ok)
    throw new Error(`Health request failed (${response.status})`);
  const data: unknown = await response.json();
  if (
    typeof data !== "object" ||
    data === null ||
    !("status" in data) ||
    data.status !== "ok" ||
    !("service" in data) ||
    data.service !== "OrbitIQ"
  ) {
    throw new Error("Unexpected health response");
  }
  return "Backend connected";
}
