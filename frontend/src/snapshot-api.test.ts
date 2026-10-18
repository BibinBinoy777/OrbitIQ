import { afterEach, expect, it, vi } from "vitest";
import { getOrbitalElements } from "./snapshot-api";
import { source } from "./test-fixtures/ground-track";
afterEach(() => vi.unstubAllGlobals());
function payload() {
  return {
    id: source.id,
    catalog_id: source.catalog_id,
    response_sha256: source.response_sha256,
    orbital_epoch: source.orbital_epoch,
    normalized_record: {
      INCLINATION: 51.6,
      ECCENTRICITY: 0.0001,
      MEAN_MOTION: 15.5,
      OBJECT_ID: "TEST ONLY",
    },
    element_units: {
      INCLINATION: "deg",
      ECCENTRICITY: "dimensionless",
      MEAN_MOTION: "rev/day",
    },
  };
}
it("reads only existing normalized elements with explicit units and matching provenance", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValue({ ok: true, json: async () => payload() });
  vi.stubGlobal("fetch", fetch);
  expect(
    await getOrbitalElements(source, new AbortController().signal),
  ).toEqual({
    inclination_deg: 51.6,
    eccentricity: 0.0001,
    mean_motion_rev_day: 15.5,
    object_id: "TEST ONLY",
  });
  expect(fetch.mock.calls[0][0]).toBe("/api/snapshots/7");
});
it.each(["identity", "unit", "NaN", "eccentricity"])(
  "rejects bad %s source metadata",
  async (kind) => {
    const data = payload();
    if (kind === "identity") data.catalog_id = 1;
    if (kind === "unit") data.element_units.INCLINATION = "rad";
    if (kind === "NaN") data.normalized_record.MEAN_MOTION = NaN;
    if (kind === "eccentricity") data.normalized_record.ECCENTRICITY = 1;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => data }),
    );
    await expect(
      getOrbitalElements(source, new AbortController().signal),
    ).rejects.toThrow();
  },
);
it("forwards cancellation and sanitizes source HTTP failures", async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 });
  vi.stubGlobal("fetch", fetch);
  const c = new AbortController();
  await expect(getOrbitalElements(source, c.signal)).rejects.toThrow(
    /Source elements unavailable/,
  );
  c.abort();
  expect(fetch.mock.calls[0][1].signal.aborted).toBe(true);
});
