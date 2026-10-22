// Explicit synthetic/reference-derived examples; never genuine observations.
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import ObservationValidation, {
  parseValidation,
} from "./ObservationValidation";
import fixture from "./test-fixtures/observation-validation.json";
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
function setup(body: unknown = fixture) {
  const fetchMock = vi.fn().mockImplementation(async (url: string) => ({
    ok: true,
    text: async () =>
      JSON.stringify(
        url.endsWith("/observation-validations")
          ? {
              status: "available",
              runs: [fixture.report_id],
              message: "SYNTHETIC TEST EVIDENCE ONLY",
            }
          : body,
      ),
  }));
  vi.stubGlobal("fetch", fetchMock);
  render(<ObservationValidation />);
  return fetchMock;
}
async function open() {
  fireEvent.click(screen.getByText("Inspect available validation evidence"));
  await screen.findByLabelText("Captured prediction / observation run");
  fireEvent.change(
    screen.getByLabelText("Captured prediction / observation run"),
    { target: { value: fixture.report_id } },
  );
  fireEvent.click(screen.getByText("Open captured validation"));
  await screen.findByText("Captured validation · NORAD 6251");
}
it("shows the compatible discrepancy, unknown independence and original source evidence", async () => {
  setup();
  await open();
  expect(
    screen.getByText(
      /2 requested records; 2 compatible discrepancies; 0 excluded; 0 independently/,
    ),
  ).toBeInTheDocument();
  expect(
    screen.getByText(/Joint prediction\/observation uncertainty/),
  ).toBeInTheDocument();
  expect(screen.getByText(/Input snapshot SHA-256/)).toHaveTextContent(
    fixture.prediction_source.response_sha256,
  );
  expect(screen.getAllByText("5")).toHaveLength(2);
  expect(
    screen.getAllByText(/not a historically issued forecast/)[0],
  ).toBeInTheDocument();
});
it("handles zero configured observations without fabricating selection controls", async () => {
  const mock = setup();
  mock.mockResolvedValue({
    ok: true,
    text: async () =>
      JSON.stringify({
        status: "not_configured",
        runs: [],
        message:
          "No observation archive configured. Snapshots are not observations.",
      }),
  });
  fireEvent.click(screen.getByText("Inspect available validation evidence"));
  expect(await screen.findByText(/Status: not_configured/)).toBeInTheDocument();
  expect(
    screen.queryByLabelText("Captured prediction / observation run"),
  ).not.toBeInTheDocument();
});
it("exports the captured authoritative report through the shared JSON serializer", async () => {
  const mock = setup();
  const create = vi.fn().mockReturnValue("blob:validation");
  URL.createObjectURL = create;
  URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  await open();
  fireEvent.click(
    screen.getByText("Export captured observation validation JSON"),
  );
  expect(create).toHaveBeenCalledOnce();
  expect(mock).toHaveBeenCalledTimes(2);
  expect(
    screen.getByText(/Captured JSON download requested/),
  ).toBeInTheDocument();
});
it("shows failed evidence reads and retries", async () => {
  const mock = setup();
  mock.mockResolvedValueOnce({ ok: false, status: 503 });
  fireEvent.click(screen.getByText("Inspect available validation evidence"));
  expect(await screen.findByRole("alert")).toHaveTextContent("503");
  fireEvent.click(screen.getByText("Retry observation evidence"));
  await screen.findByLabelText("Captured prediction / observation run");
});
it("aborts requests on unmount", async () => {
  const mock = setup();
  mock.mockImplementation(
    (_url: string, opts: { signal: AbortSignal }) =>
      new Promise((_resolve, reject) =>
        opts.signal.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        ),
      ),
  );
  fireEvent.click(screen.getByText("Inspect available validation evidence"));
  await waitFor(() => expect(mock).toHaveBeenCalledOnce());
  cleanup();
  expect(mock.mock.calls[0][1].signal.aborted).toBe(true);
});
it("validates a bounded synthetic backend report", () => {
  expect(parseValidation(fixture).summary.compatible_count).toBe(2);
});
it.each([
  "schema",
  "independence",
  "sampleCount",
  "residual",
  "frame",
  "checks",
  "findingConfidence",
  "identity",
])("rejects contradictory %s", (key) => {
  const v = structuredClone(fixture);
  if (key === "schema") v.schema_version = 2;
  if (key === "independence") v.summary.independently_verified_count = 1;
  if (key === "sampleCount") v.summary.compatible_count = 3;
  if (key === "residual") v.samples[0].residual.magnitude_km = Number.NaN;
  if (key === "frame") v.samples[0].frame = "GCRS";
  if (key === "checks") v.samples[0].checks.unit = false;
  if (key === "findingConfidence")
    Object.assign(v.findings[0], { confidence: 0.99 });
  if (key === "identity") v.report_id = "../private";
  expect(() => parseValidation(v)).toThrow("Unexpected observation-validation");
});
