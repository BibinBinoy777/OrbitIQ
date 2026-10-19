import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import Investigations from "./Investigations";
import App from "./App";
import { investigationFixtures } from "./test-fixtures/investigations";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function setup() {
  const data = investigationFixtures();
  const fetchMock = vi.fn().mockImplementation(async (path: string) => {
    const url = new URL(path, "https://example.test");
    let body: unknown = data.page;
    if (url.pathname === "/api/health")
      body = { status: "ok", service: "OrbitIQ" };
    else if (url.pathname === "/api/comparisons")
      body = url.searchParams.has("at")
        ? url.searchParams.get("frame") === "ITRS"
          ? data.itrs
          : data.teme
        : data.noState;
    else if (url.pathname === "/api/snapshots/1") body = data.detail;
    else if (url.searchParams.get("snapshot_id"))
      body = {
        ...data.page,
        snapshots: [data.page.snapshots[2]],
        returned_count: 1,
        total_count: 1,
      };
    return { ok: true, json: async () => body };
  });
  vi.stubGlobal("fetch", fetchMock);
  return { data, fetchMock };
}
async function search() {
  fireEvent.click(
    screen.getByRole("button", { name: "Search stored records" }),
  );
  await screen.findByRole("button", { name: "Inspect snapshot #1" });
}
function choose() {
  fireEvent.click(screen.getByRole("button", { name: "Use #1 as A" }));
  fireEvent.click(screen.getByRole("button", { name: "Use #2 as B" }));
  fireEvent.click(screen.getByRole("button", { name: "Compare snapshots" }));
}
it("searches with explicit bounded matching and snapshot scope", async () => {
  const { fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  fireEvent.change(screen.getByLabelText(/Name, NORAD/), {
    target: { value: "REFERENCE" },
  });
  fireEvent.change(screen.getByLabelText("Match", { exact: true }), {
    target: { value: "exact" },
  });
  fireEvent.change(screen.getByLabelText(/Selected snapshot context/), {
    target: { value: "1" },
  });
  fireEvent.click(screen.getByLabelText(/Only records/));
  await search();
  expect(fetchMock.mock.calls[0][0]).toContain("selected_only=true");
  expect(fetchMock.mock.calls[0][0]).toContain("match=exact");
  expect(screen.getByText("historical only")).toBeInTheDocument();
  expect(
    screen.getByText(
      /Total matching count unavailable|Total within selected history anchor/,
    ),
  ).toBeInTheDocument();
});
it("requires a selected context rather than silently widening scope", async () => {
  const { fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  fireEvent.click(screen.getByLabelText(/Only records/));
  fireEvent.click(
    screen.getByRole("button", { name: "Search stored records" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /Choose a snapshot context/,
  );
  expect(fetchMock).not.toHaveBeenCalled();
});
it("handles API failure and explicit retry", async () => {
  const { fetchMock } = setup();
  fetchMock.mockRejectedValueOnce(new Error("offline"));
  render(<Investigations active onExplore={vi.fn()} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Search stored records" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent("offline");
  fireEvent.click(
    screen.getByRole("button", { name: "Retry stored-data request" }),
  );
  await screen.findByRole("button", { name: "Inspect snapshot #1" });
});
it("shows an empty scan window with continuation and uses its anchor", async () => {
  const { data, fetchMock } = setup();
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      ...data.page,
      snapshots: [],
      returned_count: 0,
      has_more: true,
      next_before_id: 2,
      total_count: null,
      total_count_status: "not_computed_for_search",
    }),
  });
  render(<Investigations active onExplore={vi.fn()} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Search stored records" }),
  );
  expect(await screen.findByText(/More history remains/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Continue history" }));
  await screen.findByRole("button", { name: "Inspect snapshot #1" });
  expect(fetchMock.mock.calls[1][0]).toContain("before_id=2");
  expect(fetchMock.mock.calls[1][0]).toContain("anchor_id=3");
  fireEvent.click(screen.getByRole("button", { name: "Previous page" }));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
});
it("browses history and opens older source directly without requesting latest", async () => {
  const { fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Browse snapshot history" }),
  );
  await screen.findByRole("button", { name: "Inspect snapshot #1" });
  fireEvent.change(screen.getByLabelText(/Open snapshot ID directly/), {
    target: { value: "1" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Open snapshot" }));
  await screen.findByRole("heading", {
    name: "Snapshot #1: fixed source detail",
  });
  await screen.findByRole("region", { name: "Validated source mean elements" });
  expect(
    fetchMock.mock.calls.some((c) => String(c[0]).includes("snapshot_id=1")),
  ).toBe(true);
  expect(
    fetchMock.mock.calls.some((c) => String(c[0]).includes("/satellites/")),
  ).toBe(false);
});
it("shows safe missing-detail errors while retaining historical metadata", async () => {
  const { fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  await search();
  fetchMock.mockResolvedValueOnce({
    ok: false,
    status: 503,
    json: async () => ({ error: { message: "Stored source is invalid" } }),
  });
  fireEvent.click(screen.getByRole("button", { name: "Inspect snapshot #1" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /Metadata remain inspectable/,
  );
  expect(
    screen.getByText(/Snapshot #1: fixed source detail/),
  ).toBeInTheDocument();
});
it("compares fixed sources and keeps caution, provenance and element units visible", async () => {
  setup();
  render(<Investigations active onExplore={vi.fn()} />);
  await search();
  choose();
  fireEvent.click(
    screen.getByRole("button", { name: "Compare selected snapshots" }),
  );
  expect(
    await screen.findByRole("heading", { name: "Comparison A #1 / B #2" }),
  ).toBeInTheDocument();
  expect(screen.getByText(/do not, by themselves, prove/)).toBeInTheDocument();
  expect(
    screen.getByRole("region", { name: "Element differences" }),
  ).toHaveTextContent("RA_OF_ASC_NODE · deg");
  expect(
    screen.getByRole("region", { name: "Source metadata differences" }),
  ).toHaveTextContent("response_sha256");
  expect(
    screen.getByText(/Common-time state comparison not requested/),
  ).toBeInTheDocument();
});
it("shows added and removed records without inferring orbital existence", async () => {
  const { data, fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  await search();
  choose();
  fireEvent.change(screen.getByLabelText("Snapshot B", { exact: true }), {
    target: { value: "3" },
  });
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => data.different,
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Compare selected snapshots" }),
  );
  expect(await screen.findByText(/Only in B \(added/)).toBeInTheDocument();
  expect(screen.getByText(/Only in A \(removed/)).toBeInTheDocument();
  expect(
    screen.getByText(/Element differences unavailable/),
  ).toBeInTheDocument();
});
it("requests common-time ITRS, displays numerical results and useful WebGL fallback", async () => {
  const { data } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  await search();
  choose();
  fireEvent.change(screen.getByLabelText(/Common evaluation time/), {
    target: { value: data.itrs.state_comparison.evaluation_at },
  });
  fireEvent.change(screen.getByLabelText("State frame"), {
    target: { value: "ITRS" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Compare selected snapshots" }),
  );
  const region = await screen.findByRole("region", {
    name: "Common-time calculated state differences",
  });
  expect(region).toHaveTextContent("ITRS");
  expect(region).toHaveTextContent("Position difference (km)");
  expect(
    screen.getByText(/numerical comparison and source metadata remain usable/),
  ).toBeInTheDocument();
  expect(screen.getByText(/no connecting trajectory/)).toBeInTheDocument();
});
it("retains record inspection when state calculation is unavailable", async () => {
  const { data, fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  await search();
  choose();
  fireEvent.change(screen.getByLabelText(/Common evaluation time/), {
    target: { value: data.teme.state_comparison.evaluation_at },
  });
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      ...data.noState,
      state_comparison: {
        status: "unavailable",
        evaluation_at: data.teme.state_comparison.evaluation_at,
        frame: "TEME",
        errors: [
          {
            code: "epoch_window_exceeded",
            message: "Outside supported epoch window",
          },
        ],
      },
    }),
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Compare selected snapshots" }),
  );
  expect(
    await screen.findByText(/Common-time state comparison unavailable/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("region", { name: "Element differences" }),
  ).toBeInTheDocument();
});
it("cancels an in-flight comparison and ignores a late result", async () => {
  const { data, fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  await search();
  choose();
  let resolve: (v: unknown) => void = () => {};
  fetchMock.mockImplementationOnce(
    () =>
      new Promise((r) => {
        resolve = r;
      }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Compare selected snapshots" }),
  );
  expect(
    screen.getByText(/Comparing fixed stored sources/),
  ).toBeInTheDocument();
  const signal = fetchMock.mock.calls.at(-1)?.[1].signal;
  fireEvent.click(screen.getByRole("button", { name: "Cancel comparison" }));
  expect(signal.aborted).toBe(true);
  await act(async () => resolve({ ok: true, json: async () => data.noState }));
  expect(
    screen.queryByRole("heading", { name: "Comparison A #1 / B #2" }),
  ).not.toBeInTheDocument();
});
it("validates naive time without calling the backend", async () => {
  const { fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  await search();
  choose();
  fireEvent.change(screen.getByLabelText(/Common evaluation time/), {
    target: { value: "2026-10-19T00:00:00" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Compare selected snapshots" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(/timezone/);
  expect(fetchMock).toHaveBeenCalledTimes(1);
});
it("opens the exact source and retains comparison context on App return", async () => {
  const { fetchMock } = setup();
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Discovery & history" }));
  await screen.findByRole("button", { name: "Search stored records" });
  await search();
  choose();
  fireEvent.click(
    screen.getByRole("button", { name: "Compare selected snapshots" }),
  );
  await screen.findByRole("heading", { name: "Comparison A #1 / B #2" });
  fireEvent.click(screen.getByRole("button", { name: "Explore source A #1" }));
  await screen.findByRole("heading", {
    name: /REFERENCE TEST ONLY · Catalog 6251/,
  });
  expect(screen.getByLabelText("Saved snapshot")).toHaveValue("1");
  fireEvent.click(
    screen.getByRole("button", { name: "Return to discovery / comparison" }),
  );
  expect(
    await screen.findByRole("heading", { name: "Comparison A #1 / B #2" }),
  ).toBeVisible();
  expect(
    fetchMock.mock.calls.some((c) =>
      String(c[0]).includes("/satellites/6251/snapshots"),
    ),
  ).toBe(false);
});
it("provides keyboard-focusable search controls and semantic results", async () => {
  setup();
  render(<Investigations active onExplore={vi.fn()} />);
  const q = screen.getByLabelText(/Name, NORAD/);
  q.focus();
  expect(q).toHaveFocus();
  await search();
  const region = screen.getByRole("region", {
    name: "Stored satellite and snapshot results",
  });
  region.focus();
  expect(region).toHaveFocus();
  expect(within(region).getByRole("table")).toBeInTheDocument();
});
it("discloses unknown chronology and incompatible source metadata", async () => {
  const { data, fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  await search();
  choose();
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      ...data.noState,
      first: {
        ...data.noState.first,
        retrieved_at: null,
        metadata_issues: ["Retrieval time is unavailable."],
      },
      chronology: {
        status: "unknown",
        basis: "stored_retrieval_time",
        older_snapshot_id: null,
        newer_snapshot_id: null,
      },
      counts: { shared: 0, added: 0, removed: 0, incompatible: 1 },
      records: [
        {
          category: "incompatible",
          catalog_id: null,
          first_snapshot_id: 1,
          second_snapshot_id: 2,
        },
      ],
      element_differences: [],
      element_comparison_status: "incompatible_or_no_shared_record",
      source_errors: [
        {
          code: "snapshot_invalid",
          message: "Stored source metadata could not be verified.",
        },
        null,
      ],
    }),
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Compare selected snapshots" }),
  );
  expect(
    await screen.findByText(/older\/newer order cannot be established/),
  ).toBeInTheDocument();
  expect(
    screen.getByText(/Incompatible or unreliable record/),
  ).toBeInTheDocument();
  expect(
    screen.getByText(/Stored source metadata could not be verified/),
  ).toBeInTheDocument();
  expect(
    within(
      screen.getByRole("region", { name: "Comparison source A" }),
    ).getByText("Unavailable"),
  ).toBeInTheDocument();
});
it("distinguishes numeric range failure from missing compatible records", async () => {
  const { data, fetchMock } = setup();
  render(<Investigations active onExplore={vi.fn()} />);
  await search();
  choose();
  fetchMock.mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      ...data.noState,
      element_differences: [],
      element_comparison_status: "unavailable_numeric_range",
    }),
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Compare selected snapshots" }),
  );
  expect(
    await screen.findByText(/numerical range is not finite/),
  ).toBeInTheDocument();
  expect(screen.getByText(/Shared: 1/)).toBeInTheDocument();
});
