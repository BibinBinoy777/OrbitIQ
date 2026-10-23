import { afterEach, expect, it, vi } from "vitest";
import { getPosition, getSnapshots } from "./scientific-api";
afterEach(() => vi.unstubAllGlobals());
const signal = () => new AbortController().signal;
it("rejects nonfinite position values without rendering plausible replacements", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        snapshot_id: 1,
        catalog_id: 5,
        kind: "calculated",
        model: "SGP4",
        gravity_model: "WGS72",
        time_system: "UTC",
        frame: "TEME",
        position_km: [1, Infinity, 2],
        velocity_km_s: [1, 2, 3],
        units: { position: "km", velocity: "km/s" },
      }),
    }),
  );
  await expect(
    getPosition(1, "2000-01-01T00:00:00Z", signal()),
  ).rejects.toThrow("invalid identity, frame, units or numbers");
});
it("preserves safe structured API errors", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        error: {
          code: "epoch_window_exceeded",
          message: "Time is outside the supported epoch window",
        },
      }),
    }),
  );
  await expect(getPosition(1, "bad", signal())).rejects.toThrow(
    "Time is outside",
  );
});
it("rejects mismatched snapshot identities", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ snapshots: [{ id: 1, catalog_id: 6 }] }),
    }),
  );
  await expect(getSnapshots(5, signal())).rejects.toThrow("mismatched");
});
it("normalizes missing optional metadata to unknown instead of fabricating it", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ snapshots: [{ id: 1, catalog_id: 5 }] }),
    }),
  );
  const rows = await getSnapshots(5, signal());
  expect(rows[0].orbital_epoch).toBeUndefined();
  expect(rows[0].freshness_info).toBeUndefined();
});
it("accepts a valid TEME state without inventing missing timestamps", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        snapshot_id: 1,
        catalog_id: 5,
        kind: "calculated",
        frame: "TEME",
        model: "SGP4",
        gravity_model: "WGS72",
        time_system: "UTC",
        position_km: [1, 2, 3],
        velocity_km_s: [4, 5, 6],
        units: { position: "km", velocity: "km/s" },
      }),
    }),
  );
  const result = await getPosition(1, "2000-01-01T00:00:00Z", signal());
  expect(result.position_km).toEqual([1, 2, 3]);
  expect(result.at).toBeUndefined();
  expect(result.calculated_at).toBeUndefined();
});

it.each(["2026-10-19T07:58:23.415+00:00", "invalid"])(
  "keeps only valid separate insertion metadata: %s",
  async (stamp) => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          snapshots: [{ id: 1, catalog_id: 5, snapshot_created_at: stamp }],
        }),
      }),
    );
    const [item] = await getSnapshots(5, signal());
    expect(item.snapshot_created_at).toBe(
      stamp === "invalid" ? undefined : stamp,
    );
  },
);

// An otherwise valid response for another instant must not become evidence
// for the requested time. Fractions below Date's millisecond precision matter.
it.each([
  "2000-01-01T00:00:01.123456Z",
  "2000-01-01T00:00:00.123457Z",
  "2000-01-01T00:00:00",
  "invalid",
])(
  "rejects a mismatched or invalid returned calculation time: %s",
  async (at) => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          snapshot_id: 1,
          catalog_id: 5,
          kind: "calculated",
          frame: "TEME",
          model: "SGP4",
          gravity_model: "WGS72",
          time_system: "UTC",
          position_km: [1, 2, 3],
          velocity_km_s: [4, 5, 6],
          units: { position: "km", velocity: "km/s" },
          at,
        }),
      }),
    );
    await expect(
      getPosition(1, "2000-01-01T00:00:00.123456Z", signal()),
    ).rejects.toThrow("Calculation time does not match the requested time");
  },
);

it("accepts the same calculation instant expressed with a UTC offset", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        snapshot_id: 1,
        catalog_id: 5,
        kind: "calculated",
        frame: "TEME",
        model: "SGP4",
        gravity_model: "WGS72",
        time_system: "UTC",
        position_km: [1, 2, 3],
        velocity_km_s: [4, 5, 6],
        units: { position: "km", velocity: "km/s" },
        at: "2000-01-01T05:30:00.123456+05:30",
      }),
    }),
  );
  const result = await getPosition(1, "2000-01-01T00:00:00.123456Z", signal());
  expect(result.at).toBe("2000-01-01T05:30:00.123456+05:30");
});
