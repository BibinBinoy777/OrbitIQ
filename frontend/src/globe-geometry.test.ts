import { expect, it } from "vitest";
import {
  canConnect,
  canRenderPoint,
  displayVector,
  EARTH_RADIUS_KM,
} from "./globe-geometry";
import { explorerTrack } from "./test-fixtures/explorer";
it("maps the right-handed ITRS display basis without changing physical distances", () => {
  expect(displayVector([EARTH_RADIUS_KM, 0, 0])).toEqual([1, 0, -0]);
  expect(displayVector([0, EARTH_RADIUS_KM, 0])).toEqual([0, 0, -1]);
  expect(displayVector([0, 0, EARTH_RADIUS_KM])).toEqual([0, 1, -0]);
  expect(
    Math.hypot(...displayVector([7000, 1000, 2000])) * EARTH_RADIUS_KM,
  ).toBeCloseTo(Math.hypot(7000, 1000, 2000), 9);
});
it("rejects nonfinite display vectors", () => {
  expect(() => displayVector([NaN, 0, 0])).toThrow();
  expect(() => displayVector([1, 2])).toThrow();
});
it("requires both backend Cartesian vectors before displaying any marker", () => {
  const p = explorerTrack().points[0];
  expect(canRenderPoint(p)).toBe(true);
  expect(canRenderPoint({ ...p, position_km: undefined })).toBe(false);
  expect(canRenderPoint({ ...p, ground_position_km: [NaN, 0, 0] })).toBe(false);
});
it("preserves antimeridian breaks and avoids connecting coarse ground samples", () => {
  const p = explorerTrack().points;
  expect(canConnect(p[0], p[1])).toBe(false);
  expect(canConnect(p[1], p[2])).toBe(true);
  expect(canConnect(p[1], { ...p[2], at: "2024-01-01T00:10:00Z" })).toBe(false);
});
