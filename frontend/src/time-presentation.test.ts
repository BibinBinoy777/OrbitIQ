import { expect, it } from "vitest";
import { formatUtc } from "./ScientificExplorer";
it("preserves scientific microseconds while converting offsets to UTC", () => {
  expect(formatUtc("2000-01-01T05:30:00.123456+05:30")).toBe(
    "2000-01-01T00:00:00.123456Z (UTC)",
  );
  expect(formatUtc("2026-10-18T11:12:47.040768+00:00")).toBe(
    "2026-10-18T11:12:47.040768Z (UTC)",
  );
});
it.each([
  "2026-02-31T00:00:00Z",
  "2026-10-18T24:00:00Z",
  "bad",
  "2026-10-18T00:00:00",
])("does not turn invalid timestamp %s into a plausible one", (time) => {
  expect(formatUtc(time)).toBe("Unavailable");
});
