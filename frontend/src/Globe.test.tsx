// Renderer lifecycle is mocked here; actual WebGL is verified separately in Chromium.
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Globe from "./Globe";
import { createGlobe } from "./globe-renderer";
import { explorerTrack } from "./test-fixtures/explorer";
vi.mock("./globe-renderer", () => ({ createGlobe: vi.fn() }));
const create = vi.mocked(createGlobe);
const engine = { setData: vi.fn(), camera: vi.fn(), dispose: vi.fn() };
beforeEach(() => {
  vi.resetAllMocks();
  vi.stubGlobal("WebGL2RenderingContext", class {});
  create.mockImplementation((_host, callbacks) => {
    callbacks.ready();
    return engine;
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("provides a useful fallback without initializing WebGL when unsupported", () => {
  vi.stubGlobal("WebGL2RenderingContext", undefined);
  render(<Globe />);
  expect(screen.getByText(/3D graphics are unavailable/)).toBeInTheDocument();
  expect(create).not.toHaveBeenCalled();
  expect(screen.getByText("Rotate left")).toBeDisabled();
});
it("initializes once, shares actual selected samples and disposes on unmount", async () => {
  const points = explorerTrack().points;
  const view = render(<Globe points={points} selected={0} />);
  await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
  expect(engine.setData).toHaveBeenCalledWith(points, 0);
  view.rerender(<Globe points={points} selected={1} />);
  expect(engine.setData).toHaveBeenLastCalledWith(points, 1);
  expect(create).toHaveBeenCalledTimes(1);
  view.unmount();
  expect(engine.dispose).toHaveBeenCalledTimes(1);
});
it("exposes camera actions and accessible inspection", async () => {
  const inspect = vi.fn();
  render(<Globe points={explorerTrack().points} onInspect={inspect} />);
  await waitFor(() => expect(screen.getByText("Rotate left")).toBeEnabled());
  fireEvent.click(screen.getByText("Rotate left"));
  expect(engine.camera).toHaveBeenCalledWith("left");
  fireEvent.click(screen.getByText("Reset camera"));
  expect(engine.camera).toHaveBeenCalledWith("reset");
  fireEvent.click(screen.getByText("Inspect satellite"));
  expect(inspect).toHaveBeenCalledOnce();
});
it("handles context loss, restored context and explicit recovery", async () => {
  render(<Globe points={explorerTrack().points} />);
  await waitFor(() => expect(create).toHaveBeenCalledOnce());
  act(() => create.mock.calls[0][1].lost());
  expect(screen.getByText(/Graphics context lost/)).toBeInTheDocument();
  expect(screen.getByText("Zoom in")).toBeDisabled();
  act(() => create.mock.calls[0][1].ready());
  expect(screen.getByText("Zoom in")).toBeEnabled();
  act(() => create.mock.calls[0][1].lost());
  fireEvent.click(screen.getByText("Retry 3D"));
  await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
  expect(engine.dispose).toHaveBeenCalledTimes(1);
});
it("shows safe initialization failure without exposing internal errors", async () => {
  const log = vi.spyOn(console, "error").mockImplementation(() => {});
  create.mockImplementation(() => {
    throw new Error("/secret/driver/path");
  });
  render(<Globe />);
  expect(
    await screen.findByText(/3D graphics are unavailable/),
  ).toBeInTheDocument();
  expect(screen.queryByText(/secret/)).not.toBeInTheDocument();
  expect(log).toHaveBeenCalledWith(
    "OrbitIQ globe initialization failed",
    expect.any(Error),
  );
  create.mockImplementation((_host, callbacks) => {
    callbacks.ready();
    return engine;
  });
  fireEvent.click(screen.getByText("Retry 3D"));
  await waitFor(() => expect(screen.getByText("Rotate left")).toBeEnabled());
  expect(create).toHaveBeenCalledTimes(2);
  log.mockRestore();
});
it("does not invent a marker when valid vectors are unavailable", async () => {
  const points = explorerTrack().points.map((p) => ({
    ...p,
    position_km: undefined,
  }));
  render(<Globe points={points} />);
  await waitFor(() => expect(create).toHaveBeenCalledOnce());
  expect(screen.getByText(/No validated ITRS position/)).toBeInTheDocument();
  expect(screen.getByText("Focus satellite")).toBeDisabled();
});
it("passes two disconnected common-time comparison markers and clears them", async () => {
  const pairEngine = { ...engine, setComparison: vi.fn() };
  create.mockImplementation((_host, callbacks) => {
    callbacks.ready();
    return pairEngine;
  });
  const point = explorerTrack().points[0];
  const pair = [1, 2].map((snapshot_id) => ({ ...point, snapshot_id }));
  const view = render(<Globe comparison={pair} />);
  await waitFor(() =>
    expect(pairEngine.setComparison).toHaveBeenCalledWith(pair),
  );
  expect(screen.getByText(/sphere.*diamond/)).toHaveTextContent(
    "no connecting trajectory",
  );
  expect(screen.queryByText(/Surface track/)).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Focus source A" })).toBeEnabled();
  view.rerender(<Globe comparison={[]} />);
  expect(pairEngine.setComparison).toHaveBeenLastCalledWith([]);
  view.unmount();
  expect(pairEngine.dispose).toHaveBeenCalledOnce();
});
