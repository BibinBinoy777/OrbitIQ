import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import GroundTrack, { TrackMap } from "./GroundTrack";
import { getGroundTrack, parseTrack } from "./ground-track-api";
import { fixture, source } from "./test-fixtures/ground-track";
vi.mock("./ground-track-api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./ground-track-api")>();
  return { ...actual, getGroundTrack: vi.fn() };
});
const get = vi.mocked(getGroundTrack);
beforeEach(() => {
  vi.resetAllMocks();
  get.mockResolvedValue(parseTrack(fixture(), source));
});
afterEach(cleanup);
function show() {
  render(<GroundTrack source={source} initialTime={source.orbital_epoch!} />);
}
it("shows an empty state without an automatic request", () => {
  show();
  expect(get).not.toHaveBeenCalled();
  expect(screen.getByText(/No ground track calculated/)).toBeInTheDocument();
});
it("shows a loading state", () => {
  get.mockReturnValue(new Promise(() => {}));
  show();
  fireEvent.click(screen.getByText("Generate ground track"));
  expect(screen.getByText(/Generating backend/)).toBeInTheDocument();
});
it("displays backend points, EOP status, historical source, times and WGS84 height", async () => {
  show();
  fireEvent.click(screen.getByText("Generate ground track"));
  expect(
    await screen.findByRole("img", {
      name: /Calculated satellite ground track/,
    }),
  ).toBeInTheDocument();
  expect(screen.getByText(/Completed using predicted EOP/)).toBeInTheDocument();
  expect(screen.getByText(/Source freshness:/)).toHaveTextContent("stale");
  expect(screen.getByText("179.00000")).toBeInTheDocument();
  expect(screen.getByText(/not terrain or mean sea level/)).toBeInTheDocument();
  expect(screen.getByText("a".repeat(64))).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Selected track sample"), {
    target: { value: "1" },
  });
  expect(screen.getByText("-179.00000")).toBeInTheDocument();
  expect(screen.getAllByText(/2024-01-01T00:01:00/).length).toBeGreaterThan(0);
});
it("splits polylines at the backend antimeridian break", () => {
  const points = parseTrack(fixture(), source).points;
  render(<TrackMap points={points} selected={0} />);
  const segments = screen.getAllByTestId("track-segment");
  expect(segments).toHaveLength(2);
  expect(segments[0]).toHaveAttribute("points", "179,0");
  expect(segments[1]).toHaveAttribute("points", "-179,-5 -178,-10");
});
it("shows resource errors and clears the previous track", async () => {
  show();
  fireEvent.click(screen.getByText("Generate ground track"));
  await screen.findByRole("img");
  get.mockRejectedValue(new Error("Earth-orientation data unavailable"));
  fireEvent.click(screen.getByText("Generate ground track"));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Earth-orientation data unavailable",
  );
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
});
it("clears rendered data when sampling inputs change", async () => {
  show();
  fireEvent.click(screen.getByText("Generate ground track"));
  await screen.findByRole("img");
  fireEvent.change(screen.getByLabelText("Duration (minutes)"), {
    target: { value: "30" },
  });
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
});
it("does not render partial results rejected by the client contract", async () => {
  get.mockRejectedValue(
    new Error("Incomplete or partial track received. No track is displayed."),
  );
  show();
  fireEvent.click(screen.getByText("Generate ground track"));
  expect(await screen.findByRole("alert")).toHaveTextContent(/partial/);
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
});
it("cancels in-flight requests on unmount", () => {
  get.mockReturnValue(new Promise(() => {}));
  const view = render(
    <GroundTrack source={source} initialTime={source.orbital_epoch!} />,
  );
  fireEvent.click(screen.getByText("Generate ground track"));
  const signal = get.mock.calls[0][4];
  view.unmount();
  expect(signal.aborted).toBe(true);
});
it("preserves source microseconds in interval queries", async () => {
  render(
    <GroundTrack source={source} initialTime="2024-01-01T00:00:00.123456Z" />,
  );
  fireEvent.click(screen.getByText("Generate ground track"));
  expect(get.mock.calls[0][1]).toBe("2024-01-01T00:00:00.123456Z");
  expect(get.mock.calls[0][2]).toBe("2024-01-01T01:30:00.123456Z");
  await screen.findByRole("img");
});

it("shows widely spaced samples as unconnected points", () => {
  const points = parseTrack(fixture(), source).points;
  points[2] = { ...points[2], at: "2024-01-01T00:12:00+00:00" };
  render(<TrackMap points={points} selected={0} />);
  expect(screen.getAllByTestId("track-segment")).toHaveLength(3);
});
