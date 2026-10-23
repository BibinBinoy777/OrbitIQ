import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import HistoricalAnalysis from "./HistoricalAnalysis";
import windows from "./test-fixtures/history-windows.json";
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
it("retries the newly selected failed window instead of the old successful parameters", async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 503 });
  vi.stubGlobal("fetch", fetchMock);
  render(<HistoricalAnalysis onInspect={vi.fn()} onCompare={vi.fn()} />);
  fireEvent.change(screen.getByLabelText("Historical satellite NORAD ID"), {
    target: { value: "6251" },
  });
  fireEvent.change(screen.getByLabelText("Timeline page size"), {
    target: { value: "1" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Analyze archived history" }),
  );
  await screen.findByRole("alert");
  expect(
    new URL(fetchMock.mock.calls[0][0], "http://localhost").searchParams.get(
      "limit",
    ),
  ).toBe("1");
  fireEvent.click(
    screen.getByRole("button", { name: "Retry historical analysis" }),
  );
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  expect(
    new URL(fetchMock.mock.calls[1][0], "http://localhost").searchParams.get(
      "limit",
    ),
  ).toBe("1");
  expect(screen.queryByText(/Historical coverage ·/)).not.toBeInTheDocument();
});

function response(body: unknown) {
  return {
    ok: true,
    headers: new Headers(),
    text: async () => JSON.stringify(body),
  };
}
function start(fetchMock: ReturnType<typeof vi.fn>) {
  vi.stubGlobal("fetch", fetchMock);
  render(<HistoricalAnalysis onInspect={vi.fn()} onCompare={vi.fn()} />);
  fireEvent.change(screen.getByLabelText("Historical satellite NORAD ID"), {
    target: { value: "6251" },
  });
  fireEvent.change(screen.getByLabelText("Timeline page size"), {
    target: { value: "1" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Analyze archived history" }),
  );
}
async function loaded() {
  await screen.findByRole("heading", {
    name: "Historical coverage · NORAD 6251",
  });
}
function query(mock: ReturnType<typeof vi.fn>, index: number) {
  return new URL(mock.mock.calls[index][0], "http://localhost").search;
}
it("retries failed Next and Previous with their original cursors and navigation stack", async () => {
  const mock = vi
    .fn()
    .mockResolvedValueOnce(response(windows.first))
    .mockResolvedValueOnce({ ok: false, status: 503 })
    .mockResolvedValueOnce(response(windows.older))
    .mockResolvedValueOnce({ ok: false, status: 503 })
    .mockResolvedValueOnce(response(windows.first))
    .mockResolvedValueOnce(response(windows.older));
  start(mock);
  await loaded();
  expect(
    screen.getByRole("button", { name: "Previous timeline page" }),
  ).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Next timeline page" }));
  await screen.findByRole("alert");
  expect(
    screen.queryByRole("button", { name: "Export historical analysis JSON" }),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Retry historical analysis" }),
  );
  await loaded();
  expect(query(mock, 2)).toBe(query(mock, 1));
  expect(query(mock, 2)).toContain("before_id=2");
  expect(screen.getByText(/Partial window:/)).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Next timeline page" }),
  ).toBeDisabled();
  fireEvent.click(
    screen.getByRole("button", { name: "Previous timeline page" }),
  );
  await screen.findByRole("alert");
  fireEvent.click(
    screen.getByRole("button", { name: "Retry historical analysis" }),
  );
  await loaded();
  expect(query(mock, 4)).toBe(query(mock, 3));
  expect(query(mock, 4)).toContain("limit=1");
  expect(query(mock, 4)).toContain("anchor_id=2");
  expect(query(mock, 4)).not.toContain("before_id=");
  expect(
    screen.getByRole("button", { name: "Previous timeline page" }),
  ).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Next timeline page" }));
  await loaded();
  expect(query(mock, 5)).toBe(query(mock, 1));
});
it("hides a mismatched window and recovers with a captured export without another request", async () => {
  const mock = vi
    .fn()
    .mockResolvedValueOnce(response(windows.full))
    .mockResolvedValueOnce(response(windows.first));
  const create = vi.fn().mockReturnValue("blob:e7");
  vi.stubGlobal(
    "URL",
    class extends URL {
      static createObjectURL = create;
      static revokeObjectURL = vi.fn();
    },
  );
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  start(mock);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /bounded contract/,
  );
  expect(screen.queryByText(/Historical coverage ·/)).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "Export historical analysis JSON" }),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Retry historical analysis" }),
  );
  await loaded();
  fireEvent.click(
    screen.getByRole("button", { name: "Export historical analysis JSON" }),
  );
  expect(mock).toHaveBeenCalledTimes(2);
  expect(create).toHaveBeenCalledOnce();
  // jsdom Blob lacks text(); FileReader verifies the actual download content.
  const text = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = reject;
    reader.readAsText(create.mock.calls[0][0]);
  });
  expect(JSON.parse(text)).toEqual(windows.first);
});
it("clears obsolete failure/retry on editing and ignores late responses after cancellation", async () => {
  let finish: (body: unknown) => void = () => {};
  const mock = vi
    .fn()
    .mockResolvedValueOnce({ ok: false, status: 503 })
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    )
    .mockResolvedValueOnce(response(windows.full));
  start(mock);
  await screen.findByRole("alert");
  fireEvent.click(
    screen.getByRole("button", { name: "Retry historical analysis" }),
  );
  await waitFor(() => expect(mock).toHaveBeenCalledTimes(2));
  fireEvent.change(screen.getByLabelText("Timeline page size"), {
    target: { value: "20" },
  });
  expect(mock.mock.calls[1][1].signal.aborted).toBe(true);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "Retry historical analysis" }),
  ).not.toBeInTheDocument();
  finish(response(windows.first));
  fireEvent.click(
    screen.getByRole("button", { name: "Analyze archived history" }),
  );
  await loaded();
  expect(
    screen.getAllByRole("heading", {
      name: /E7 SYNTHETIC CONTRACT FIXTURE ONLY/,
    }),
  ).toHaveLength(2);
  expect(query(mock, 2)).toContain("limit=20");
});
