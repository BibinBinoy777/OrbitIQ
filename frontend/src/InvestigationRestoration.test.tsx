// Isolated restoration contracts; no fake snapshots enter the real application DB.
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import GroundTrack from "./GroundTrack";
import ScientificExplorer from "./ScientificExplorer";
import App from "./App";
import { getGroundTrack } from "./ground-track-api";
import { getPosition, getSnapshots } from "./scientific-api";
import { getOrbitalElements } from "./snapshot-api";
import { explorerTrack } from "./test-fixtures/explorer";
import { source } from "./test-fixtures/ground-track";
import { savedContext } from "./test-fixtures/saved-investigations";
import { parseInvestigation, shareLink } from "./saved-investigation";
import type { PositionResult } from "./scientific-api";
vi.mock("./ground-track-api", async (original) => ({
  ...(await original<typeof import("./ground-track-api")>()),
  getGroundTrack: vi.fn(),
}));
vi.mock("./scientific-api", () => ({
  getPosition: vi.fn(),
  getSnapshots: vi.fn(),
}));
vi.mock("./snapshot-api", () => ({ getOrbitalElements: vi.fn() }));
beforeEach(() => {
  vi.resetAllMocks();
  window.history.replaceState(null, "", "/");
  localStorage.clear();
  vi.mocked(getGroundTrack).mockResolvedValue(explorerTrack());
  vi.mocked(getOrbitalElements).mockResolvedValue({
    inclination_deg: 51.6,
    eccentricity: 0.0001,
    mean_motion_rev_day: 15.5,
    object_id: "TEST ONLY",
  });
});
afterEach(() => {
  cleanup();
  window.history.replaceState(null, "", "/");
  vi.unstubAllGlobals();
});
it("restores exact track range, frame, sample index and backend-derived visuals", async () => {
  const v = savedContext("ground-track");
  if (v.mode !== "ground-track") throw new Error();
  render(
    <GroundTrack
      source={{ ...source, frame: "TEME" }}
      initialTime={source.orbital_epoch!}
      initialInvestigation={v}
      readOnly
    />,
  );
  await waitFor(() =>
    expect(screen.getByLabelText("Selected track sample")).toHaveValue("1"),
  );
  expect(vi.mocked(getGroundTrack).mock.calls[0].slice(1, 4)).toEqual([
    "2024-01-01T00:00:00.000000Z",
    "2024-01-01T00:02:00.000000Z",
    60,
  ]);
  expect(screen.getByLabelText("Duration (minutes)")).toBeDisabled();
  expect(screen.getByLabelText(/Track start/)).toBeDisabled();
  expect(
    screen.queryByRole("button", { name: "Save in this browser" }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByText("Next sample"));
  expect(screen.getByLabelText("Selected track sample")).toHaveValue("2");
  expect(localStorage.length).toBe(0);
});
it("shows EOP/resource errors without fabricating a restored track", async () => {
  vi.mocked(getGroundTrack).mockRejectedValue(
    new Error("Policy requires measured Earth-orientation data"),
  );
  const v = savedContext("ground-track");
  if (v.mode !== "ground-track") throw new Error();
  render(
    <GroundTrack
      source={{ ...source, frame: "TEME" }}
      initialTime={source.orbital_epoch!}
      initialInvestigation={v}
      readOnly
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /measured Earth-orientation/,
  );
  expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  expect(
    screen.queryByLabelText("Calculated ground-track result"),
  ).not.toBeInTheDocument();
});
it("does not replace an unavailable saved sample with sample zero", async () => {
  const v = savedContext("ground-track");
  if (v.mode !== "ground-track") throw new Error();
  const points = explorerTrack();
  points.points = points.points.slice(0, 1);
  vi.mocked(getGroundTrack).mockResolvedValue(points);
  render(
    <GroundTrack
      source={{ ...source, frame: "TEME" }}
      initialTime={source.orbital_epoch!}
      initialInvestigation={v}
      readOnly
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(/No substitute/);
  expect(screen.queryByRole("slider")).not.toBeInTheDocument();
});
it("recomputes a saved TEME position at the exact requested time with locked inputs", async () => {
  const v = savedContext("position"),
    s = { ...source, frame: "TEME" };
  const result: PositionResult = {
    snapshot_id: 7,
    catalog_id: 25544,
    frame: "TEME",
    kind: "calculated",
    model: "SGP4",
    gravity_model: "WGS72",
    time_system: "UTC",
    position_km: [1, 2, 3],
    velocity_km_s: [4, 5, 6],
    units: { position: "km", velocity: "km/s" },
    at: "2024-01-01T00:00:00Z",
    orbital_epoch: s.orbital_epoch,
    retrieved_at: s.retrieved_at,
    response_sha256: s.response_sha256,
    warnings: [],
  };
  vi.mocked(getPosition).mockResolvedValue(result);
  render(
    <ScientificExplorer initialSource={s} initialInvestigation={v} readOnly />,
  );
  expect(
    await screen.findByRole("heading", { name: "Calculated position · TEME" }),
  ).toBeVisible();
  expect(getPosition).toHaveBeenCalledWith(
    7,
    "2024-01-01T00:00:00.000000Z",
    expect.any(AbortSignal),
  );
  expect(screen.getByLabelText(/Requested propagation time/)).toBeDisabled();
  expect(getSnapshots).not.toHaveBeenCalled();
});
it("rejects a mismatched response time rather than calling it the restored calculation", async () => {
  const v = savedContext("position");
  vi.mocked(getPosition).mockResolvedValue({
    ...source,
    snapshot_id: 7,
    frame: "TEME",
    at: "2024-01-01T00:01:00Z",
  } as unknown as PositionResult);
  render(
    <ScientificExplorer
      initialSource={{ ...source, frame: "TEME" }}
      initialInvestigation={v}
      readOnly
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /time does not match/,
  );
  expect(
    screen.queryByRole("heading", { name: "Calculated position · TEME" }),
  ).not.toBeInTheDocument();
});
it("rejects invalid initial share links before any snapshot request", async () => {
  window.history.replaceState(null, "", "/#/investigation?v=2");
  const fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ status: "ok", service: "OrbitIQ" }),
  });
  vi.stubGlobal("fetch", fetch);
  render(<App />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /Unsupported investigation link version/,
  );
  expect(fetch.mock.calls.every(([path]) => path === "/api/health")).toBe(true);
  expect(getSnapshots).not.toHaveBeenCalled();
});
it("restores the saved-list route after application restart", async () => {
  window.history.replaceState(null, "", "/#/saved");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok", service: "OrbitIQ" }),
    }),
  );
  render(<App />);
  expect(
    await screen.findByRole("heading", { name: "Saved investigations" }),
  ).toBeVisible();
  expect(getSnapshots).not.toHaveBeenCalled();
});
it("serializes track selection without changing orbital epochs or retrieval times", () => {
  const value = savedContext("ground-track"),
    link = shareLink(parseInvestigation(value), window.location.href);
  expect(link).toContain("selected_index=1");
  expect(value.source.orbital_epoch).not.toBe(value.source.retrieved_at);
});
it("keeps accessible region labels attached to their own retained and reopened views", () => {
  const s = { ...source, frame: "TEME" };
  const { container } = render(
    <>
      <div hidden>
        <ScientificExplorer initialSource={s} />
      </div>
      <ScientificExplorer initialSource={s} readOnly />
    </>,
  );
  const ids = [...container.querySelectorAll("[id]")].map((node) => node.id);
  expect(new Set(ids).size).toBe(ids.length);
  for (const region of container.querySelectorAll("section[aria-labelledby]")) {
    const label = document.getElementById(
      region.getAttribute("aria-labelledby")!,
    );
    expect(label).not.toBeNull();
    expect(region.contains(label)).toBe(true);
  }
  expect(
    screen.getByRole("region", { name: "Stored orbital data" }),
  ).toBeVisible();
  expect(
    screen.getByRole("region", { name: "Earth-relative ground track" }),
  ).toBeVisible();
});
