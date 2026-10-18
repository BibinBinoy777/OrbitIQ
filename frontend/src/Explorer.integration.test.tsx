// Deterministic component integration only, separate from the real-browser audit.
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import GroundTrack from "./GroundTrack";
import ScientificExplorer from "./ScientificExplorer";
import { getGroundTrack } from "./ground-track-api";
import { getSnapshots, getPosition } from "./scientific-api";
import { getOrbitalElements } from "./snapshot-api";
import { explorerTrack } from "./test-fixtures/explorer";
import { source } from "./test-fixtures/ground-track";
vi.mock("./ground-track-api", async (original) => ({
  ...(await original<typeof import("./ground-track-api")>()),
  getGroundTrack: vi.fn(),
}));
vi.mock("./scientific-api", () => ({
  getSnapshots: vi.fn(),
  getPosition: vi.fn(),
}));
vi.mock("./snapshot-api", () => ({ getOrbitalElements: vi.fn() }));
const get = vi.mocked(getGroundTrack),
  list = vi.mocked(getSnapshots),
  elements = vi.mocked(getOrbitalElements);
beforeEach(() => {
  vi.resetAllMocks();
  get.mockResolvedValue(explorerTrack());
  list.mockResolvedValue([source]);
  elements.mockResolvedValue({
    inclination_deg: 51.6,
    eccentricity: 0.0001,
    mean_motion_rev_day: 15.5,
    object_id: "TEST ONLY",
  });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});
it("shows supported elements, timestamps and units without inventing a marker", async () => {
  render(<GroundTrack source={source} initialTime={source.orbital_epoch!} />);
  expect(await screen.findByText("51.6000°")).toBeInTheDocument();
  expect(screen.getByText("15.50000000 rev/day")).toBeInTheDocument();
  expect(
    screen.getByText(/No calculated position selected/),
  ).toBeInTheDocument();
  expect(
    screen.getByText(/Orbital uncertainty is unquantified/),
  ).toBeInTheDocument();
});
it("shares timeline selection with the map, Cartesian information and saved-sample selector", async () => {
  render(<GroundTrack source={source} initialTime={source.orbital_epoch!} />);
  fireEvent.click(screen.getByText("Generate ground track"));
  await screen.findByRole("slider");
  fireEvent.click(screen.getByText("Next sample"));
  expect(screen.getByLabelText("Selected track sample")).toHaveValue("1");
  expect(screen.getByText("-179.00000")).toBeInTheDocument();
  expect(
    screen.getByText(/Calculated at: 2026-10-18T18:00:00/),
  ).toBeInTheDocument();
  expect(get).toHaveBeenCalledOnce();
});
it("rejects late track results after an interval edit cancels the request", async () => {
  let resolve: (r: ReturnType<typeof explorerTrack>) => void = () => {};
  get.mockReturnValue(
    new Promise((done) => {
      resolve = done;
    }),
  );
  render(<GroundTrack source={source} initialTime={source.orbital_epoch!} />);
  fireEvent.click(screen.getByText("Generate ground track"));
  const signal = get.mock.calls[0][4];
  fireEvent.change(screen.getByLabelText("Duration (minutes)"), {
    target: { value: "30" },
  });
  expect(signal.aborted).toBe(true);
  await act(async () => resolve(explorerTrack()));
  expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  expect(screen.getByText(/No ground track calculated/)).toBeInTheDocument();
});
it("pauses playback and clears the dataset when the window changes", async () => {
  render(<GroundTrack source={source} initialTime={source.orbital_epoch!} />);
  fireEvent.click(screen.getByText("Generate ground track"));
  await screen.findByRole("slider");
  vi.useFakeTimers();
  fireEvent.click(screen.getByText("Play"));
  fireEvent.change(screen.getByLabelText("Duration (minutes)"), {
    target: { value: "30" },
  });
  act(() => vi.advanceTimersByTime(5000));
  expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  expect(get).toHaveBeenCalledOnce();
});
it("resets the window to the documented source time, 90 minutes and 60 seconds", () => {
  render(<GroundTrack source={source} initialTime={source.orbital_epoch!} />);
  fireEvent.change(screen.getByLabelText("Duration (minutes)"), {
    target: { value: "30" },
  });
  fireEvent.change(screen.getByLabelText("Sample step (seconds)"), {
    target: { value: "120" },
  });
  fireEvent.click(screen.getByText("Reset track window"));
  expect(screen.getByLabelText("Duration (minutes)")).toHaveValue(90);
  expect(screen.getByLabelText("Sample step (seconds)")).toHaveValue(60);
  expect(screen.getByLabelText(/Track start/)).toHaveValue(
    source.orbital_epoch,
  );
});
it("does not let an old satellite search replace a newer selection", async () => {
  let resolve: (r: (typeof source)[]) => void = () => {};
  list
    .mockReturnValueOnce(
      new Promise((done) => {
        resolve = done;
      }),
    )
    .mockResolvedValueOnce([
      {
        ...source,
        id: 8,
        catalog_id: 12345,
        object_name: "NEW RESULT FIXTURE",
      },
    ]);
  render(<ScientificExplorer />);
  fireEvent.click(screen.getByText("Load snapshots"));
  const abandoned = list.mock.calls[0][1];
  fireEvent.change(screen.getByLabelText("Catalog ID"), {
    target: { value: "12345" },
  });
  fireEvent.click(screen.getByText("Load snapshots"));
  await screen.findByRole("heading", {
    name: "NEW RESULT FIXTURE · Catalog 12345",
  });
  expect(abandoned.aborted).toBe(true);
  await act(async () =>
    resolve([{ ...source, object_name: "ABANDONED RESULT" }]),
  );
  expect(
    screen.queryByRole("heading", { name: /ABANDONED/ }),
  ).not.toBeInTheDocument();
  expect(vi.mocked(getPosition)).not.toHaveBeenCalled();
});
it("announces a safe source-detail failure and preserves identity information", async () => {
  elements.mockRejectedValue(new Error("/secret/internal"));
  render(<GroundTrack source={source} initialTime={source.orbital_epoch!} />);
  expect(
    await screen.findByText(/Source element details unavailable/),
  ).toBeInTheDocument();
  expect(screen.getByText("NORAD 25544 · snapshot #7")).toBeInTheDocument();
  expect(screen.queryByText(/secret/)).not.toBeInTheDocument();
});
it("cancels source-detail loading when switching satellites", async () => {
  elements.mockReturnValue(new Promise(() => {}));
  const view = render(
    <GroundTrack source={source} initialTime={source.orbital_epoch!} />,
  );
  await waitFor(() => expect(elements).toHaveBeenCalled());
  const signal = elements.mock.calls[0][1];
  view.unmount();
  expect(signal.aborted).toBe(true);
});

it("rejects impossible calendar dates before requesting a track", () => {
  render(<GroundTrack source={source} initialTime={source.orbital_epoch!} />);
  fireEvent.change(screen.getByLabelText(/Track start/), {
    target: { value: "2024-02-30T00:00:00Z" },
  });
  fireEvent.click(screen.getByText("Generate ground track"));
  expect(screen.getByRole("alert")).toHaveTextContent(/aware ISO timestamp/);
  expect(get).not.toHaveBeenCalled();
});

it("keeps the track default tied to the selected source when the separate TEME query changes", async () => {
  render(<ScientificExplorer />);
  fireEvent.click(screen.getByText("Load snapshots"));
  await screen.findByText("NORAD 25544 · snapshot #7");
  fireEvent.change(screen.getByLabelText(/Requested propagation time/), {
    target: { value: "2024-01-01T00:15:00Z" },
  });
  fireEvent.change(screen.getByLabelText(/Track start/), {
    target: { value: "2024-01-01T00:10:00Z" },
  });
  fireEvent.click(screen.getByText("Reset track window"));
  expect(screen.getByLabelText(/Track start/)).toHaveValue(
    source.orbital_epoch,
  );
  expect(elements).toHaveBeenCalledOnce();
  expect(get).not.toHaveBeenCalled();
});
