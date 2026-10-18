import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Timeline from "./Timeline";
import { explorerTrack } from "./test-fixtures/explorer";
const points = explorerTrack().points;
function Harness() {
  const [index, setIndex] = useState(0);
  return <Timeline points={points} index={index} onSelect={setIndex} />;
}
beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});
it("waits for play and advances only whole backend samples", () => {
  render(<Harness />);
  act(() => vi.advanceTimersByTime(2500));
  expect(screen.getByRole("slider")).toHaveValue("0");
  fireEvent.click(screen.getByText("Play"));
  act(() => vi.advanceTimersByTime(500));
  expect(screen.getByRole("slider")).toHaveValue("0");
  act(() => vi.advanceTimersByTime(500));
  expect(screen.getByRole("slider")).toHaveValue("1");
  expect(screen.getByRole("status")).toHaveTextContent("00:01:00");
  act(() => vi.advanceTimersByTime(1000));
  expect(screen.getByRole("slider")).toHaveValue("2");
  expect(screen.getByText("Play")).toBeDisabled();
  act(() => vi.advanceTimersByTime(5000));
  expect(screen.getByRole("slider")).toHaveValue("2");
});
it("pauses playback, provides previous/next and reset controls", () => {
  render(<Harness />);
  fireEvent.click(screen.getByText("Play"));
  fireEvent.click(screen.getByText("Pause"));
  act(() => vi.advanceTimersByTime(3000));
  expect(screen.getByRole("slider")).toHaveValue("0");
  fireEvent.click(screen.getByText("Next sample"));
  expect(screen.getByRole("slider")).toHaveValue("1");
  fireEvent.click(screen.getByText("Previous sample"));
  expect(screen.getByRole("slider")).toHaveValue("0");
  fireEvent.change(screen.getByRole("slider"), { target: { value: "2" } });
  expect(screen.getByRole("slider")).toHaveAttribute(
    "aria-valuetext",
    expect.stringContaining("00:02:00"),
  );
  fireEvent.click(screen.getByText("Reset timeline"));
  expect(screen.getByRole("slider")).toHaveValue("0");
});
it("clears its timer on unmount", () => {
  const view = render(<Harness />);
  fireEvent.click(screen.getByText("Play"));
  view.unmount();
  expect(vi.getTimerCount()).toBe(0);
});
it("stops when the document is hidden", () => {
  render(<Harness />);
  fireEvent.click(screen.getByText("Play"));
  vi.spyOn(document, "hidden", "get").mockReturnValue(true);
  act(() => document.dispatchEvent(new Event("visibilitychange")));
  act(() => vi.advanceTimersByTime(2000));
  expect(screen.getByRole("slider")).toHaveValue("0");
  expect(screen.getByText("Play")).toHaveAttribute("aria-pressed", "false");
});
it("disables automatic playback for reduced motion while preserving manual navigation", () => {
  vi.stubGlobal("matchMedia", () => ({
    matches: true,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
  render(<Harness />);
  expect(screen.getByText("Play")).toBeDisabled();
  expect(screen.getByText(/Reduced motion:/)).toBeInTheDocument();
  fireEvent.click(screen.getByText("Next sample"));
  expect(screen.getByRole("slider")).toHaveValue("1");
});
it("pauses when reduced motion is enabled and does not restart when it is disabled", () => {
  const listeners: Array<() => void> = [];
  const media = {
    matches: false,
    addEventListener: (_n: string, fn: () => void) => listeners.push(fn),
    removeEventListener: vi.fn(),
  };
  vi.stubGlobal("matchMedia", () => media);
  render(<Harness />);
  fireEvent.click(screen.getByText("Play"));
  act(() => {
    media.matches = true;
    listeners.forEach((f) => f());
  });
  act(() => {
    media.matches = false;
    listeners.forEach((f) => f());
    vi.advanceTimersByTime(2000);
  });
  expect(screen.getByText("Play")).toHaveAttribute("aria-pressed", "false");
  expect(screen.getByRole("slider")).toHaveValue("0");
});
