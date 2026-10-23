// Isolated reference-derived archive contract; never genuine application history.
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import HistoricalAnalysis from "./HistoricalAnalysis";
import { getHistory, parseHistory } from "./history-api";
import fixture from "./test-fixtures/history.json";
import invalidFixture from "./test-fixtures/history-invalid.json";
import windows from "./test-fixtures/history-windows.json";
type Fixture = Omit<typeof fixture, "pagination" | "coverage"> & {
  pagination: Omit<typeof fixture.pagination, "next_before_id"> & {
    next_before_id: number | null;
  };
  coverage: Omit<
    typeof fixture.coverage,
    | "oldest_verifiable_retrieval"
    | "newest_verifiable_retrieval"
    | "retrieval_span_seconds"
  > & {
    oldest_verifiable_retrieval: string | null;
    newest_verifiable_retrieval: string | null;
    retrieval_span_seconds: number | null;
  };
};
const data = (): Fixture => structuredClone(fixture);
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
function setup(body: unknown = data()) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    headers: new Headers(),
    text: async () => JSON.stringify(body),
  });
  vi.stubGlobal("fetch", fetchMock);
  const inspect = vi.fn(),
    compare = vi.fn();
  render(<HistoricalAnalysis onInspect={inspect} onCompare={compare} />);
  fireEvent.change(screen.getByLabelText("Historical satellite NORAD ID"), {
    target: { value: "6251" },
  });
  return { fetchMock, inspect, compare };
}
async function analyze() {
  fireEvent.click(screen.getByText("Analyze archived history"));
  await screen.findByText("Historical coverage · NORAD 6251");
}
it("shows actual points, source clocks, values and limits with selected comparison", async () => {
  const { compare, inspect, fetchMock } = setup();
  await analyze();
  expect(screen.getAllByText(/only pairwise changes/)[0]).toBeInTheDocument();
  expect(
    screen.getAllByRole("heading", { name: /ISOLATED REFERENCE FIXTURE/ }),
  ).toHaveLength(2);
  fireEvent.click(screen.getByText("Inspect archived orbital elements #1"));
  expect(screen.getAllByText("INCLINATION").length).toBeGreaterThan(0);
  fireEvent.click(screen.getByText("Open selected historical comparison"));
  expect(compare).toHaveBeenCalledWith(1, 2);
  fireEvent.click(screen.getByText("Open existing snapshot detail #1"));
  expect(inspect).toHaveBeenCalledWith(
    expect.objectContaining({ id: 1, catalog_id: 6251 }),
  );
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(screen.getByText(/No package has been captured/)).toBeInTheDocument();
});
it("exports the captured report without recalculation", async () => {
  const create = vi.fn().mockReturnValue("blob:history"),
    click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});
  URL.createObjectURL = create;
  URL.revokeObjectURL = vi.fn();
  const { fetchMock } = setup();
  await analyze();
  fireEvent.click(screen.getByText("Export historical analysis JSON"));
  expect(click).toHaveBeenCalledOnce();
  expect(create).toHaveBeenCalledOnce();
  expect(fetchMock).toHaveBeenCalledOnce();
  const blob = create.mock.calls[0][0] as Blob;
  expect(blob.type).toBe("application/json");
  expect(screen.getByRole("status")).toHaveTextContent(
    "no recalculation or ingestion",
  );
  fireEvent.click(
    screen.getByText(/Download existing replay capture definition/),
  );
  expect(create).toHaveBeenCalledTimes(2);
  expect(fetchMock).toHaveBeenCalledOnce();
});
it("shows source failure and can retry", async () => {
  const { fetchMock } = setup();
  fetchMock.mockResolvedValueOnce({ ok: false, status: 503 });
  fireEvent.click(screen.getByText("Analyze archived history"));
  expect(await screen.findByRole("alert")).toHaveTextContent("503");
  fireEvent.click(screen.getByText("Retry historical analysis"));
  await screen.findByText("Historical coverage · NORAD 6251");
});
it("rejects invalid identifiers before requesting", async () => {
  const { fetchMock } = setup();
  fireEvent.change(screen.getByLabelText("Historical satellite NORAD ID"), {
    target: { value: "340000" },
  });
  fireEvent.click(screen.getByText("Analyze archived history"));
  expect(await screen.findByRole("alert")).toHaveTextContent("1 to 339999");
  expect(fetchMock).not.toHaveBeenCalled();
});
it("paginates bounded windows with an anchor and partial coverage", async () => {
  const { fetchMock } = setup(windows.first);
  fireEvent.change(screen.getByLabelText("Timeline page size"), {
    target: { value: "1" },
  });
  await analyze();
  expect(screen.getByText(/Partial window:/)).toBeInTheDocument();
  fireEvent.click(screen.getByText("Next timeline page"));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  expect(fetchMock.mock.calls[1][0]).toContain("anchor_id=2");
  expect(fetchMock.mock.calls[1][0]).toContain("before_id=2");
});
it("aborts obsolete requests on editing and hides stale results", async () => {
  const { fetchMock } = setup();
  fetchMock.mockImplementation(
    (_url: string, opts: { signal: AbortSignal }) =>
      new Promise((_resolve, reject) => {
        opts.signal.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        );
      }),
  );
  fireEvent.click(screen.getByText("Analyze archived history"));
  expect(screen.getByRole("status")).toHaveTextContent("Analyzing");
  fireEvent.change(screen.getByLabelText("Historical satellite NORAD ID"), {
    target: { value: "12345" },
  });
  expect(fetchMock.mock.calls[0][1].signal.aborted).toBe(true);
  expect(screen.queryByText(/Historical coverage ·/)).not.toBeInTheDocument();
});
it("renders empty coverage honestly", async () => {
  setup(windows.empty);
  await analyze();
  expect(screen.getByText(/No archived records found/)).toBeInTheDocument();
  expect(
    screen.getByText("Open selected historical comparison"),
  ).toBeDisabled();
});
it("validates the existing backend fixture contract", () => {
  expect(parseHistory(data()).points).toHaveLength(2);
});
const mutations: [string, (v: ReturnType<typeof data>) => void][] = [
  [
    "unsupported version",
    (v) => {
      v.schema_version = 2;
    },
  ],
  [
    "extrapolated trend",
    (v) => {
      v.coverage.extrapolation = true;
    },
  ],
  [
    "invented points",
    (v) => {
      v.points.push(v.points[0]);
    },
  ],
  [
    "microsecond source-time mismatch",
    (v) => {
      v.points[0].reference.orbital_epoch =
        v.points[0].reference.orbital_epoch.replace("980096", "980097");
    },
  ],
  [
    "source hash mismatch",
    (v) => {
      v.points[0].reference.response_sha256 = "f".repeat(64);
    },
  ],
  [
    "wrong units",
    (v) => {
      v.comparisons[0].differences[0].unit = "km";
    },
  ],
  [
    "invalid arithmetic",
    (v) => {
      v.comparisons[0].differences[0].difference += 1;
    },
  ],
  [
    "wrong recipe identity",
    (v) => {
      v.comparisons[0].evidence.definition.source.snapshot_id = 999;
    },
  ],
  [
    "unknown finding source",
    (v) => {
      v.findings[0].sources[0].snapshot_id = 999;
    },
  ],
  [
    "unsupported rule version",
    (v) => {
      v.findings[0].rule_version = 2;
    },
  ],
  [
    "oversized findings",
    (v) => {
      v.findings = Array(201).fill(v.findings[0]);
    },
  ],
  [
    "impossible completeness",
    (v) => {
      v.pagination.has_more = true;
      v.pagination.next_before_id = 1;
    },
  ],
  [
    "unknown catalog",
    (v) => {
      v.catalog_id = 12345;
    },
  ],
];
it.each(mutations)("rejects %s", (_label, mutate) => {
  const v = data();
  mutate(v);
  expect(() => parseHistory(v)).toThrow("Unexpected historical");
});
it("refuses another catalog in the API response", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      text: async () => JSON.stringify(data()),
    }),
  );
  await expect(
    getHistory(25544, new URLSearchParams(), new AbortController().signal),
  ).rejects.toThrow("Unexpected historical");
});

it("preserves a damaged persisted row without directional change or zero substitution", async () => {
  setup(invalidFixture);
  await analyze();
  expect(
    screen.getByRole("heading", { name: "Comparison unavailable #1 / #2" }),
  ).toBeInTheDocument();
  expect(
    screen.getByText("Unusable for calculation / stale"),
  ).toBeInTheDocument();
  expect(
    screen.getByText("Open selected historical comparison"),
  ).toBeDisabled();
  expect(
    screen.queryByText(/Download existing replay capture definition/),
  ).not.toBeInTheDocument();
  expect(parseHistory(invalidFixture).points[0].elements).toBeNull();
});
