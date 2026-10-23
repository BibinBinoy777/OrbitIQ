// Deterministic stored-data UI fixtures; no live provider request.
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import StoredCatalog from "./StoredCatalog";
import { getDetail, getSnapshotPage, parsePage } from "./investigation-api";
import { getReadiness } from "./readiness-api";
import { investigationFixtures } from "./test-fixtures/investigations";
import { readinessFixture } from "./test-fixtures/readiness";
vi.mock("./investigation-api", async (original) => ({
  ...(await original<typeof import("./investigation-api")>()),
  getSnapshotPage: vi.fn(),
  getDetail: vi.fn(),
}));
vi.mock("./readiness-api", async (original) => ({
  ...(await original<typeof import("./readiness-api")>()),
  getReadiness: vi.fn(),
}));
const get = vi.mocked(getSnapshotPage),
  audit = vi.mocked(getReadiness),
  detail = vi.mocked(getDetail);
const page = () => parsePage(investigationFixtures().page);
function mount() {
  const onExplore = vi.fn(),
    onBrowse = vi.fn(),
    onReadiness = vi.fn();
  render(<StoredCatalog {...{ onExplore, onBrowse, onReadiness }} />);
  return { onExplore, onBrowse, onReadiness };
}
beforeEach(() => {
  vi.resetAllMocks();
  get.mockResolvedValue(page());
  audit.mockResolvedValue(readinessFixture());
  detail.mockResolvedValue({ values: {}, units: {} });
});
afterEach(cleanup);
it("loads stored information and reports bounded records without claiming unique or usable satellite counts", async () => {
  let resolve!: (v: ReturnType<typeof page>) => void;
  get.mockReturnValue(
    new Promise((done) => {
      resolve = done;
    }),
  );
  mount();
  expect(
    screen.getByText("Loading stored catalog information…"),
  ).toBeInTheDocument();
  await act(async () => resolve(page()));
  expect(
    screen.getByText(/Not a count of unique satellites/),
  ).toBeInTheDocument();
  expect(screen.getByText(/Not assessed globally/)).toBeInTheDocument();
  expect(get).toHaveBeenCalledWith(
    new URLSearchParams({ limit: "5" }),
    expect.any(AbortSignal),
  );
  expect(screen.getAllByText(/First retrieval:/)).toHaveLength(3);
});
it("validates a selected source before opening the existing explorer", async () => {
  const { onExplore, onBrowse, onReadiness } = mount();
  const button = await screen.findByRole("button", {
    name: "Open stored snapshot #3",
  });
  fireEvent.click(button);
  await waitFor(() =>
    expect(onExplore).toHaveBeenCalledWith(
      expect.objectContaining({ id: 3, catalog_id: 12345 }),
    ),
  );
  expect(detail).toHaveBeenCalledWith(
    expect.objectContaining({ id: 3 }),
    expect.any(AbortSignal),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Browse stored catalog" }),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect data readiness" }),
  );
  expect(onBrowse).toHaveBeenCalledOnce();
  expect(onReadiness).toHaveBeenCalledOnce();
});
it("labels an empty archive only from a reliable empty result and gives operator guidance", async () => {
  get.mockResolvedValue({
    ...page(),
    snapshots: [],
    returned_count: 0,
    total_count: 0,
    has_more: false,
    next_before_id: null,
    anchor_id: null,
  });
  mount();
  expect(
    await screen.findByText(/No stored snapshots are available/),
  ).toBeInTheDocument();
  expect(
    screen.getByText(
      /explicit operator action with a shared two-hour cooldown/,
    ),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: /Open stored snapshot/ }),
  ).not.toBeInTheDocument();
});
it("preserves stored access when a collection has failed and never calls it an empty catalog", async () => {
  const data = readinessFixture();
  data.components.ingestion = {
    ...data.components.ingestion,
    latest_attempt_failed: true,
    message: "Last fixture collection failed.",
    last_successful_acquisition_at: "2026-10-18T12:00:00Z",
  };
  audit.mockResolvedValue(data);
  mount();
  await screen.findByText(/latest provider collection attempt failed/);
  expect(
    screen.getByRole("button", { name: "Open stored snapshot #3" }),
  ).toBeEnabled();
  expect(
    screen.queryByText(/No stored snapshots are available/),
  ).not.toBeInTheDocument();
  expect(
    screen.getByText(/A successful acquisition may reuse an existing snapshot/),
  ).toBeInTheDocument();
});
it("reuses backend freshness categories rather than refreshing stale elements", async () => {
  mount();
  await screen.findByRole("button", { name: "Open stored snapshot #3" });
  expect(screen.getAllByText("stale", { exact: true })).toHaveLength(3);
  expect(
    screen.getAllByText(/Stale elements: use as historical input/),
  ).toHaveLength(3);
});
it("discloses incomplete records and refuses to offer them as calculation sources", async () => {
  const data = page();
  data.snapshots[0].metadata_issues = ["Malformed provenance"];
  get.mockResolvedValue(data);
  mount();
  expect(
    await screen.findByRole("button", { name: "Open stored snapshot #3" }),
  ).toBeDisabled();
  expect(
    screen.getByText(/not offered as a validated calculation source/),
  ).toBeInTheDocument();
  expect(detail).not.toHaveBeenCalled();
});
it("reports initial storage failure separately from empty or provider failure", async () => {
  get.mockRejectedValue(new Error("Orbital storage is unavailable"));
  mount();
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /not an empty-catalog result/,
  );
  expect(
    screen.queryByText(/No stored snapshots are available/),
  ).not.toBeInTheDocument();
});
it("retains useful metadata on reload failure and recovers on explicit retry", async () => {
  mount();
  await screen.findByRole("button", { name: "Open stored snapshot #3" });
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Reload stored catalog" }),
    ).toBeEnabled(),
  );
  get.mockRejectedValueOnce(new Error("Timed out"));
  fireEvent.click(
    screen.getByRole("button", { name: "Reload stored catalog" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /Previously loaded metadata is retained/,
  );
  expect(
    screen.getByRole("button", { name: "Open stored snapshot #3" }),
  ).toBeEnabled();
  fireEvent.click(
    screen.getByRole("button", { name: "Reload stored catalog" }),
  );
  await waitFor(() =>
    expect(screen.queryByRole("alert")).not.toBeInTheDocument(),
  );
});
it("keeps catalog usable if readiness fails and never invents an unbounded count", async () => {
  get.mockResolvedValue({
    ...page(),
    total_count: null,
    total_count_status: "unknown_exceeds_bounded_count",
  });
  audit.mockRejectedValue(new Error("Readiness unavailable"));
  mount();
  await screen.findByText(/Collection status unavailable/);
  expect(
    screen.getByText(/count exceeds the bounded assessment/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Open stored snapshot #3" }),
  ).toBeEnabled();
});
it("exposes full-source validation errors without opening or substituting another snapshot", async () => {
  detail.mockRejectedValue(
    new Error("Stored snapshot failed scientific provenance validation"),
  );
  const { onExplore } = mount();
  fireEvent.click(
    await screen.findByRole("button", { name: "Open stored snapshot #3" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /Source could not be opened/,
  );
  expect(onExplore).not.toHaveBeenCalled();
});
it("cancels abandoned requests on unmount", async () => {
  get.mockReturnValue(new Promise(() => {}));
  const view = render(
    <StoredCatalog
      onExplore={vi.fn()}
      onBrowse={vi.fn()}
      onReadiness={vi.fn()}
    />,
  );
  await waitFor(() => expect(get).toHaveBeenCalledOnce());
  const signal = get.mock.calls[0][1];
  view.unmount();
  expect(signal.aborted).toBe(true);
});
