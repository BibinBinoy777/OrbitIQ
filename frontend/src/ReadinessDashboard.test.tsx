import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import ReadinessDashboard from "./ReadinessDashboard";
import { readinessFixture } from "./test-fixtures/readiness";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function responds(value: unknown = readinessFixture()) {
  const mock = vi.fn().mockResolvedValue({ ok: true, json: async () => value });
  vi.stubGlobal("fetch", mock);
  return mock;
}
it("shows loading while the assessment is outstanding", () => {
  vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));
  render(<ReadinessDashboard onExplore={vi.fn()} />);
  expect(screen.getByRole("status")).toHaveTextContent(/Assessing/);
});
it.each(["healthy", "degraded", "unavailable", "unknown"] as const)(
  "communicates %s with text and four labelled sections",
  async (status) => {
    responds(readinessFixture(status));
    render(<ReadinessDashboard onExplore={vi.fn()} />);
    expect(
      await screen.findByText(`Overall readiness: ${status}`),
    ).toBeInTheDocument();
    for (const name of [
      "Database availability",
      "Orbital snapshot freshness",
      "Earth orientation",
      "Leap seconds",
    ]) {
      expect(
        within(screen.getByRole("region", { name })).getByText(status),
      ).toBeInTheDocument();
    }
    expect(screen.getByText(/Last status refresh:.*UTC/)).toBeInTheDocument();
    expect(
      screen.getByText(/not a current satellite observation/),
    ).toBeInTheDocument();
  },
);
it("shows partial data as unknown without hiding successful reads", async () => {
  const value = readinessFixture();
  responds({
    ...value,
    components: { ...value.components, leap_seconds: undefined },
  });
  render(<ReadinessDashboard onExplore={vi.fn()} />);
  expect(
    await screen.findByText("Overall readiness: unknown"),
  ).toBeInTheDocument();
  expect(screen.getByText(/not provided reliably/)).toBeInTheDocument();
  expect(screen.getByText(/validity cannot be asserted/)).toBeInTheDocument();
  expect(
    within(
      screen.getByRole("region", { name: "Database availability" }),
    ).getByText("healthy"),
  ).toBeInTheDocument();
});
it("explains stale stored data and bounded history from backend facts", async () => {
  const value = readinessFixture("degraded");
  value.components.orbital_data.message =
    "Newest epoch is stale; obtain a new source snapshot explicitly.";
  value.components.orbital_data.global_latest_known = false;
  responds(value);
  render(<ReadinessDashboard onExplore={vi.fn()} />);
  expect(await screen.findByText(/Newest epoch is stale/)).toBeInTheDocument();
  expect(screen.getByText(/Unknown — bounded history/)).toBeInTheDocument();
});
it("explains an empty archive without inventing freshness", async () => {
  const value = readinessFixture("degraded");
  value.components.orbital_data = {
    status: "degraded",
    code: "empty",
    message: "No source snapshots stored; ingest explicitly.",
    snapshots_present: false,
  };
  responds(value);
  render(<ReadinessDashboard onExplore={vi.fn()} />);
  expect(await screen.findByText("No snapshots")).toBeInTheDocument();
  expect(screen.getByText(/No source snapshots stored/)).toBeInTheDocument();
});
it("retries after API failure and replaces the error", async () => {
  const mock = responds();
  mock.mockRejectedValueOnce(new Error("offline"));
  render(<ReadinessDashboard onExplore={vi.fn()} />);
  expect(await screen.findByRole("alert")).toHaveTextContent(/retry/);
  fireEvent.click(screen.getByRole("button", { name: "Refresh readiness" }));
  expect(
    await screen.findByText("Overall readiness: healthy"),
  ).toBeInTheDocument();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(mock).toHaveBeenCalledTimes(2);
});
it("clears old results on edit and assesses the submitted time only", async () => {
  const mock = responds();
  render(<ReadinessDashboard onExplore={vi.fn()} />);
  await screen.findByText("Overall readiness: healthy");
  fireEvent.change(screen.getByLabelText(/Calculation time/), {
    target: { value: "2004-04-06T07:51:28Z" },
  });
  expect(
    screen.queryByText("Overall readiness: healthy"),
  ).not.toBeInTheDocument();
  expect(mock).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Refresh readiness" }));
  await screen.findByText("Overall readiness: healthy");
  expect(mock.mock.calls[1][0]).toContain("at=2004-04-06T07%3A51%3A28Z");
});
it("rejects a naive timestamp before sending it", async () => {
  const mock = responds();
  render(<ReadinessDashboard onExplore={vi.fn()} />);
  await screen.findByText("Overall readiness: healthy");
  fireEvent.change(screen.getByLabelText(/Calculation time/), {
    target: { value: "2026-10-19T00:00:00" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Refresh readiness" }));
  expect(screen.getByRole("alert")).toHaveTextContent(/timezone/);
  expect(mock).toHaveBeenCalledTimes(1);
});
it("aborts an outstanding request on unmount", async () => {
  const mock = vi.fn().mockReturnValue(new Promise(() => {}));
  vi.stubGlobal("fetch", mock);
  const view = render(<ReadinessDashboard onExplore={vi.fn()} />);
  await waitFor(() => expect(mock).toHaveBeenCalledTimes(1));
  const signal = mock.mock.calls[0][1].signal;
  view.unmount();
  expect(signal.aborted).toBe(true);
});
it("provides labelled native keyboard controls and a return action", async () => {
  responds();
  const explore = vi.fn();
  render(<ReadinessDashboard onExplore={explore} />);
  await screen.findByText("Overall readiness: healthy");
  const input = screen.getByRole("textbox", { name: /Calculation time/ });
  input.focus();
  expect(input).toHaveFocus();
  const back = screen.getByRole("button", {
    name: /Return to satellite explorer/,
  });
  back.focus();
  expect(back).toHaveFocus();
  fireEvent.click(back);
  expect(explore).toHaveBeenCalledOnce();
});
