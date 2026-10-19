// Controlled component fixtures; these are not presented as live observations.
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import ScientificExplorer from "./ScientificExplorer";
import { getPosition, getSnapshots } from "./scientific-api";
import type { PositionResult, SnapshotSummary } from "./scientific-api";
vi.mock("./scientific-api", () => ({
  getSnapshots: vi.fn(),
  getPosition: vi.fn(),
}));
const snapshots = vi.mocked(getSnapshots);
const position = vi.mocked(getPosition);
const row: SnapshotSummary = {
  id: 7,
  catalog_id: 25544,
  object_name: "TEST FIXTURE ONLY",
  orbital_epoch: "2026-10-01T00:00:00Z",
  retrieved_at: "2026-10-02T00:00:00Z",
  frame: "TEME",
  source_url:
    "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=JSON",
  response_sha256: "a".repeat(64),
  validation_status: "structural_and_epoch_propagation_passed",
  freshness_info: { state: "stale", evaluated_at: "2026-10-18T00:00:00Z" },
};
const calculated: PositionResult = {
  snapshot_id: 7,
  catalog_id: 25544,
  kind: "calculated",
  model: "SGP4",
  gravity_model: "WGS72",
  time_system: "UTC",
  frame: "TEME",
  position_km: [1, 2, 3],
  velocity_km_s: [4, 5, 6],
  units: { position: "km", velocity: "km/s" },
  at: row.orbital_epoch,
  orbital_epoch: row.orbital_epoch,
  retrieved_at: row.retrieved_at,
  calculated_at: "2026-10-18T00:00:00Z",
  response_sha256: row.response_sha256,
  warnings: ["Verification fixture warning"],
  sgp4_version: "test-version",
};
beforeEach(() => {
  vi.resetAllMocks();
  snapshots.mockResolvedValue([row]);
  position.mockResolvedValue(calculated);
});
afterEach(cleanup);
async function load() {
  render(<ScientificExplorer />);
  fireEvent.click(screen.getByRole("button", { name: "Load snapshots" }));
  await screen.findByRole("heading", { name: /TEST FIXTURE ONLY/ });
}
it("waits for an explicit user request and shows a loading state", async () => {
  snapshots.mockReturnValue(new Promise(() => {}));
  render(<ScientificExplorer />);
  expect(snapshots).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Load snapshots" }));
  expect(screen.getByText("Loading saved snapshots…")).toBeInTheDocument();
});
it("shows an empty catalog without inventing data", async () => {
  snapshots.mockResolvedValue([]);
  render(<ScientificExplorer />);
  fireEvent.click(screen.getByText("Load snapshots"));
  expect(await screen.findByText(/No stored snapshots/)).toBeInTheDocument();
  expect(screen.queryByText("Calculate position")).not.toBeInTheDocument();
});
it.each(["fresh", "aging", "stale", "unknown", "future_epoch"] as const)(
  "labels %s freshness explicitly",
  async (state) => {
    snapshots.mockResolvedValue([{ ...row, freshness_info: { state } }]);
    await load();
    const labels = {
      fresh: "Fresh",
      aging: "Aging",
      stale: "Stale",
      unknown: "Unknown",
      future_epoch: "Future epoch",
    };
    expect(
      screen.getByText(labels[state], { exact: true }),
    ).toBeInTheDocument();
    if (state === "stale")
      expect(screen.getByText(/Stale orbital elements/)).toBeInTheDocument();
  },
);
it("distinguishes epoch and retrieval timestamps and source identity", async () => {
  await load();
  expect(
    screen.getByText("2026-10-01T00:00:00.000Z (UTC)"),
  ).toBeInTheDocument();
  expect(
    screen.getByText("2026-10-02T00:00:00.000Z (UTC)"),
  ).toBeInTheDocument();
  expect(screen.getByText("Orbital epoch")).toBeInTheDocument();
  expect(screen.getByText("First retrieved")).toBeInTheDocument();
  expect(screen.getByText("a".repeat(64))).toBeInTheDocument();
  expect(
    screen.getByText(/Latest stored does not mean current/),
  ).toBeInTheDocument();
});
it("uses unknown labels for missing metadata", async () => {
  snapshots.mockResolvedValue([
    { id: 7, catalog_id: 25544, object_name: "TEST FIXTURE ONLY" },
  ]);
  await load();
  expect(screen.getByText("Unknown", { exact: true })).toBeInTheDocument();
  expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
  expect(screen.getByText("Unknown / unsupported")).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Calculate position" }),
  ).toBeDisabled();
});
it("shows a safe snapshot API error", async () => {
  snapshots.mockRejectedValue(new Error("Orbital storage is unavailable"));
  render(<ScientificExplorer />);
  fireEvent.click(screen.getByText("Load snapshots"));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Snapshot load failed: Orbital storage is unavailable",
  );
});
it("shows calculated status, frame, units and unquantified uncertainty", async () => {
  await load();
  fireEvent.click(screen.getByText("Calculate position"));
  expect(
    await screen.findByRole("heading", { name: "Calculated position · TEME" }),
  ).toBeInTheDocument();
  expect(screen.getByText("Position (km)")).toBeInTheDocument();
  expect(screen.getByText("Velocity (km/s)")).toBeInTheDocument();
  expect(screen.getByText(/Not a direct observation/)).toBeInTheDocument();
  expect(screen.getByText(/Uncertainty is not quantified/)).toBeInTheDocument();
  expect(screen.getByText(/Not Earth-fixed coordinates/)).toBeInTheDocument();
  expect(position).toHaveBeenCalledWith(
    7,
    row.orbital_epoch,
    expect.any(AbortSignal),
  );
});
it("removes previous values when a new calculation fails", async () => {
  await load();
  fireEvent.click(screen.getByText("Calculate position"));
  await screen.findByText("Calculated position · TEME");
  position.mockRejectedValue(new Error("Time exceeds supported epoch window"));
  fireEvent.click(screen.getByText("Calculate position"));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Calculation failed",
  );
  expect(
    screen.queryByText("Calculated position · TEME"),
  ).not.toBeInTheDocument();
});
it("selects historical input explicitly and clears earlier results", async () => {
  snapshots.mockResolvedValue([
    row,
    { ...row, id: 6, orbital_epoch: "2026-09-01T00:00:00Z" },
  ]);
  await load();
  fireEvent.click(screen.getByText("Calculate position"));
  await screen.findByText("Calculated position · TEME");
  fireEvent.change(screen.getByLabelText("Saved snapshot"), {
    target: { value: "6" },
  });
  expect(screen.getByLabelText(/Requested propagation time/)).toHaveValue(
    "2026-09-01T00:00:00Z",
  );
  expect(
    screen.queryByText("Calculated position · TEME"),
  ).not.toBeInTheDocument();
});
it("cancels abandoned calculations and never displays their late result", async () => {
  let resolve: (r: PositionResult) => void = () => {};
  position.mockReturnValue(
    new Promise((done) => {
      resolve = done;
    }),
  );
  await load();
  fireEvent.click(screen.getByText("Calculate position"));
  expect(
    screen.getByText("Calculating backend SGP4 state…"),
  ).toBeInTheDocument();
  const signal = position.mock.calls[0][2];
  fireEvent.change(screen.getByLabelText(/Requested propagation time/), {
    target: { value: "2026-10-01T00:01:00Z" },
  });
  expect(signal.aborted).toBe(true);
  resolve(calculated);
  await waitFor(() =>
    expect(
      screen.queryByText("Calculating backend SGP4 state…"),
    ).not.toBeInTheDocument(),
  );
  expect(
    screen.queryByText("Calculated position · TEME"),
  ).not.toBeInTheDocument();
});
it("refuses a calculation whose source hash differs from the selected input", async () => {
  position.mockResolvedValue({
    ...calculated,
    response_sha256: "b".repeat(64),
  });
  await load();
  fireEvent.click(screen.getByText("Calculate position"));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Calculation source does not match",
  );
  expect(
    screen.queryByText("Calculated position · TEME"),
  ).not.toBeInTheDocument();
});
it("retains an explicitly inspected historical source when browsing the same catalog", async () => {
  const newer = { ...row, id: 8, object_name: "NEWER TEST FIXTURE ONLY" };
  snapshots.mockResolvedValue([newer]);
  render(<ScientificExplorer initialSource={row} />);
  fireEvent.click(screen.getByRole("button", { name: "Load snapshots" }));
  await screen.findByText(/retained separately from this bounded history page/);
  expect(screen.getByLabelText("Saved snapshot")).toHaveValue("7");
  expect(
    screen.getByRole("heading", { name: /TEST FIXTURE ONLY · Catalog/ }),
  ).toHaveTextContent("TEST FIXTURE ONLY · Catalog 25544");
  fireEvent.change(screen.getByLabelText("Saved snapshot"), {
    target: { value: "8" },
  });
  expect(screen.getByLabelText("Saved snapshot")).toHaveValue("8");
});

it("shows recorded insertion time separately from retrieval and source epoch", async () => {
  snapshots.mockResolvedValue([
    { ...row, snapshot_created_at: "2026-10-19T07:58:23.415+00:00" },
  ]);
  await load();
  expect(
    screen.getByText("2026-10-19T07:58:23.415Z (UTC)"),
  ).toBeInTheDocument();
  expect(
    screen.queryByText("Not recorded separately for this legacy source"),
  ).not.toBeInTheDocument();
});
