import { afterEach, expect, it, vi } from "vitest";
import { getGroundTrack, parseTrack } from "./ground-track-api";
import { fixture, source } from "./test-fixtures/ground-track";
afterEach(() => vi.unstubAllGlobals());
it("accepts complete backend results with chronological antimeridian segments", () => {
  const result = parseTrack(fixture(), source);
  expect(result.points.map((p) => p.segment_id)).toEqual([0, 1, 1]);
  expect(result.points[0].geodetic.longitude_deg).toBe(179);
});
it.each(["partial", "failed"])(
  "rejects %s status without displaying points",
  (status) => {
    expect(() => parseTrack({ ...fixture(), status }, source)).toThrow(
      /partial/,
    );
  },
);
it.each([
  [
    "latitude",
    (d: ReturnType<typeof fixture>) => {
      d.points[0].geodetic.latitude_deg = 91;
    },
  ],
  [
    "longitude",
    (d: ReturnType<typeof fixture>) => {
      d.points[0].geodetic.longitude_deg = 180;
    },
  ],
  [
    "NaN",
    (d: ReturnType<typeof fixture>) => {
      d.points[0].geodetic.altitude_km = NaN;
    },
  ],
  [
    "frame",
    (d: ReturnType<typeof fixture>) => {
      d.points[0].frame = "ECI";
    },
  ],
  [
    "units",
    (d: ReturnType<typeof fixture>) => {
      d.points[0].units.altitude = "m";
    },
  ],
  [
    "provenance",
    (d: ReturnType<typeof fixture>) => {
      d.points[0].teme.response_sha256 = "x";
    },
  ],
  [
    "sample count",
    (d: ReturnType<typeof fixture>) => {
      d.sample_count = 2;
    },
  ],
  [
    "unordered",
    (d: ReturnType<typeof fixture>) => {
      d.points.reverse();
    },
  ],
  [
    "gap",
    (d: ReturnType<typeof fixture>) => {
      d.points[2].at = "2024-01-01T00:04:00+00:00";
    },
  ],
  [
    "connected antimeridian",
    (d: ReturnType<typeof fixture>) => {
      d.points[1].segment_id = 0;
    },
  ],
  [
    "EOP state",
    (d: ReturnType<typeof fixture>) => {
      d.points[0].earth_orientation.status = "unknown";
    },
  ],
  [
    "degraded EOP",
    (d: ReturnType<typeof fixture>) => {
      d.points[0].earth_orientation.degraded_results_allowed = true;
    },
  ],
  [
    "transformation status",
    (d: ReturnType<typeof fixture>) => {
      d.points[0].transformation_status = "failed";
    },
  ],
  [
    "empty track",
    (d: ReturnType<typeof fixture>) => {
      d.points = [];
    },
  ],
] as const)("rejects invalid %s response", (_name, mutate) => {
  const data = fixture();
  mutate(data);
  expect(() => parseTrack(data, source)).toThrow();
});
it("uses an explicit snapshot, times, frame and sampling step in the backend request", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValue({ ok: true, json: async () => fixture() });
  vi.stubGlobal("fetch", fetchMock);
  const d = fixture();
  await getGroundTrack(
    source,
    d.requested_start,
    d.requested_end,
    60,
    new AbortController().signal,
  );
  const url = new URL(fetchMock.mock.calls[0][0], "https://example.test");
  expect(url.pathname).toBe("/api/satellites/25544/ground-track");
  expect(url.searchParams.get("snapshot_id")).toBe("7");
  expect(url.searchParams.get("frame")).toBe("ITRS");
  expect(url.searchParams.get("step_seconds")).toBe("60");
});
it("propagates safe structured resource errors", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({
        error: {
          code: "eop_unavailable",
          message: "Required local resource is unavailable",
        },
      }),
    }),
  );
  await expect(
    getGroundTrack(source, "x", "y", 60, new AbortController().signal),
  ).rejects.toThrow(/Required local resource/);
});

it("rejects a valid track returned for a different requested interval", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => fixture() }),
  );
  await expect(
    getGroundTrack(
      source,
      "2024-01-01T00:01:00Z",
      fixture().requested_end,
      60,
      new AbortController().signal,
    ),
  ).rejects.toThrow(/do not match/);
});

it.each(["position_km", "ground_position_km"])(
  "rejects invalid optional %s before 3D rendering",
  (key) => {
    const data = fixture();
    const points = data.points.map((p) => ({ ...p, [key]: [NaN, 0, 0] }));
    expect(() => parseTrack({ ...data, points }, source)).toThrow();
  },
);
it("keeps old valid 2D responses usable without inventing missing 3D vectors", () => {
  const result = parseTrack(fixture(), source);
  expect(result.points[0].position_km).toBeUndefined();
  expect(result.points[0].ground_position_km).toBeUndefined();
});
