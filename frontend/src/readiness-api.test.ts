import { afterEach, expect, it, vi } from "vitest";
import { getReadiness, parseReadiness } from "./readiness-api";
import { readinessFixture } from "./test-fixtures/readiness";
afterEach(() => vi.unstubAllGlobals());
it.each(["healthy", "degraded", "unavailable", "unknown"] as const)(
  "parses %s without changing meaning",
  (status) => {
    expect(parseReadiness(readinessFixture(status)).status).toBe(status);
  },
);
it("retains usable sections and labels a missing section unknown", () => {
  const value = readinessFixture();
  const components = { ...value.components, eop: undefined };
  const result = parseReadiness({ ...value, components });
  expect(result.status).toBe("unknown");
  expect(result.components.eop.code).toBe("section_missing");
  expect(result.components.database.status).toBe("healthy");
});
it.each([
  { kind: "observation" },
  { automatic_updates: true },
  { evaluated_at: "yesterday" },
  { requested_at: "2026-10-19T00:00:00" },
  { components: null },
  { status: "perfect" },
])("rejects invalid response envelope %o", (mutation) => {
  expect(() => parseReadiness({ ...readinessFixture(), ...mutation })).toThrow(
    /Unexpected/,
  );
});
it("sends requested time, cancellation and no-store", async () => {
  const mock = vi
    .fn()
    .mockResolvedValue({ ok: true, json: async () => readinessFixture() });
  vi.stubGlobal("fetch", mock);
  await getReadiness("2026-10-19T05:30:00+05:30", new AbortController().signal);
  const [url, options] = mock.mock.calls[0];
  expect(new URL(url, "https://example.test").searchParams.get("at")).toBe(
    "2026-10-19T05:30:00+05:30",
  );
  expect(options.cache).toBe("no-store");
  expect(options.signal).toBeInstanceOf(AbortSignal);
});
it.each([
  [422, /timezone/],
  [503, /unavailable/],
])("reports safe HTTP %s errors", async (status, message) => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status }));
  await expect(getReadiness("", new AbortController().signal)).rejects.toThrow(
    message,
  );
});
function stall() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(
      (_url, options) =>
        new Promise((_resolve, reject) => {
          options.signal.addEventListener("abort", () =>
            reject(options.signal.reason),
          );
        }),
    ),
  );
}
it("propagates caller cancellation", async () => {
  stall();
  const controller = new AbortController();
  const request = getReadiness("", controller.signal);
  controller.abort();
  await expect(request).rejects.toMatchObject({ name: "AbortError" });
});
it("terminates a stalled request", async () => {
  stall();
  await expect(
    getReadiness("", new AbortController().signal),
  ).rejects.toMatchObject({ name: "TimeoutError" });
}, 7000);

it("treats missing collection metadata as unknown while preserving orbital facts", () => {
  const value = readinessFixture();
  const result = parseReadiness({
    ...value,
    components: { ...value.components, ingestion: undefined },
  });
  expect(result.status).toBe("unknown");
  expect(result.components.ingestion.code).toBe("section_missing");
  expect(result.components.orbital_data.orbital_epoch).toBe(
    value.components.orbital_data.orbital_epoch,
  );
});
