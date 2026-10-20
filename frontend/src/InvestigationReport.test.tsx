import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import InvestigationReport from "./InvestigationReport";
import { ReportAction } from "./InvestigationActions";
import { getInvestigationReport } from "./report-api";
import { reportFixture } from "./test-fixtures/reports";
vi.mock("./report-api", async (original) => ({
  ...(await original<typeof import("./report-api")>()),
  getInvestigationReport: vi.fn(),
}));
let downloads: Blob[], click: ReturnType<typeof vi.spyOn>;
beforeEach(() => {
  vi.resetAllMocks();
  downloads = [];
  const OriginalURL = URL;
  vi.stubGlobal(
    "URL",
    class extends OriginalURL {
      static createObjectURL(blob: Blob) {
        downloads.push(blob);
        return `blob:report-${downloads.length}`;
      }
      static revokeObjectURL = vi.fn();
    },
  );
  click = vi
    .spyOn(HTMLAnchorElement.prototype, "click")
    .mockImplementation(() => {});
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value: function (this: HTMLDialogElement) {
      this.setAttribute("open", "");
    },
  });
  vi.spyOn(window, "print").mockImplementation(() => {});
  vi.mocked(getInvestigationReport).mockResolvedValue(reportFixture());
});
afterEach(() => {
  cleanup();
  click.mockRestore();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
const readBlob = (blob: Blob) =>
  new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.readAsText(blob);
  });

it("generates once, downloads both captured formats and prints only report content", async () => {
  const r = reportFixture();
  render(<InvestigationReport investigation={r.investigation.definition} />);
  expect(getInvestigationReport).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("Generate investigation report"));
  fireEvent.click(await screen.findByText("Download JSON evidence"));
  fireEvent.click(screen.getByText("Download printable HTML"));
  expect(getInvestigationReport).toHaveBeenCalledTimes(1);
  expect(JSON.parse(await readBlob(downloads[0]))).toEqual(r);
  expect(await readBlob(downloads[1])).toContain(r.report_id);
  fireEvent.click(screen.getByText("Open printable report"));
  const dialog = await screen.findByRole("dialog");
  expect(within(dialog).getByText(r.investigation.title)).toBeVisible();
  expect(document.body).toHaveClass("report-printing");
  fireEvent.click(within(dialog).getByText("Print report / Save as PDF"));
  expect(window.print).toHaveBeenCalledOnce();
  fireEvent.click(within(dialog).getByText("Close printable report"));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(document.body).not.toHaveClass("report-printing");
  expect(getInvestigationReport).toHaveBeenCalledOnce();
});
it("suppresses duplicate generation and allows explicit cancellation", async () => {
  vi.mocked(getInvestigationReport).mockImplementation(
    () => new Promise(() => {}),
  );
  render(
    <InvestigationReport
      investigation={reportFixture().investigation.definition}
    />,
  );
  const button = screen.getByText("Generate investigation report");
  fireEvent.click(button);
  fireEvent.click(button);
  expect(getInvestigationReport).toHaveBeenCalledOnce();
  expect(button).toBeDisabled();
  fireEvent.click(screen.getByText("Cancel report generation"));
  expect(vi.mocked(getInvestigationReport).mock.calls[0][1].aborted).toBe(true);
  expect(screen.getByRole("status")).toHaveTextContent("cancelled");
  expect(screen.queryByText("Download JSON evidence")).not.toBeInTheDocument();
});
it("handles missing sources with retry and no stale download", async () => {
  vi.mocked(getInvestigationReport).mockRejectedValueOnce(
    new Error("Snapshot not found"),
  );
  render(
    <InvestigationReport
      investigation={reportFixture().investigation.definition}
    />,
  );
  fireEvent.click(screen.getByText("Generate investigation report"));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Snapshot not found",
  );
  expect(screen.queryByText("Download JSON evidence")).not.toBeInTheDocument();
  fireEvent.click(screen.getByText("Retry report generation"));
  expect(await screen.findByText("Download JSON evidence")).toBeVisible();
});
it("aborts changed contexts and refuses a late previous response", async () => {
  let finish!: (v: ReturnType<typeof reportFixture>) => void;
  vi.mocked(getInvestigationReport).mockImplementationOnce(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const first = reportFixture("position"),
    second = reportFixture("snapshot");
  const ui = render(
    <ReportAction investigation={first.investigation.definition} />,
  );
  fireEvent.click(await screen.findByText("Generate investigation report"));
  const signal = vi.mocked(getInvestigationReport).mock.calls[0][1];
  ui.rerender(<ReportAction investigation={second.investigation.definition} />);
  await act(async () => {
    finish(first);
  });
  expect(signal.aborted).toBe(true);
  expect(screen.queryByText("Download JSON evidence")).not.toBeInTheDocument();
});
it("cleans download URLs and print state on unmount", async () => {
  const ui = render(
    <InvestigationReport
      investigation={reportFixture().investigation.definition}
    />,
  );
  fireEvent.click(screen.getByText("Generate investigation report"));
  fireEvent.click(await screen.findByText("Download JSON evidence"));
  fireEvent.click(screen.getByText("Open printable report"));
  await waitFor(() => expect(document.body).toHaveClass("report-printing"));
  ui.unmount();
  expect(URL.revokeObjectURL).toHaveBeenCalled();
  expect(document.body).not.toHaveClass("report-printing");
});
it("keeps partial results labelled as unavailable in preview", async () => {
  const r = reportFixture();
  r.status = "partial";
  r.calculation = {
    status: "unavailable",
    data: null,
    errors: [{ code: "eop_unavailable", message: "EOP unavailable" }],
  };
  vi.mocked(getInvestigationReport).mockResolvedValue(r);
  render(<InvestigationReport investigation={r.investigation.definition} />);
  fireEvent.click(screen.getByText("Generate investigation report"));
  expect(
    await screen.findByText(/some calculations unavailable/),
  ).toBeVisible();
  fireEvent.click(screen.getByText("Open printable report"));
  const dialog = await screen.findByRole("dialog");
  expect(within(dialog).getByText("EOP unavailable")).toBeVisible();
  expect(within(dialog).getByText(/Missing values are not zero/)).toBeVisible();
});
