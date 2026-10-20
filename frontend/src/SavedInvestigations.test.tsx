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
import InvestigationActions, { ShareAction } from "./InvestigationActions";
import SavedInvestigations from "./SavedInvestigations";
import {
  loadSaved,
  saveInvestigation,
  STORAGE_KEY,
} from "./investigation-storage";
import { parseShareLink } from "./saved-investigation";
import { savedContext } from "./test-fixtures/saved-investigations";
beforeEach(() => {
  localStorage.clear();
});
afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
it("confirms a local save only after persistence and opens it from a fresh list", async () => {
  const value = savedContext("position"),
    onOpen = vi.fn();
  const view = render(<InvestigationActions build={() => value} />);
  fireEvent.change(screen.getByLabelText("Investigation title"), {
    target: { value: "My local position" },
  });
  fireEvent.change(screen.getByLabelText(/Private local notes/), {
    target: { value: "Not shared" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save in this browser" }));
  await screen.findByText(/Saved “My local position” in this browser/);
  view.unmount();
  render(<SavedInvestigations onOpen={onOpen} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Open My local position" }),
  );
  expect(onOpen).toHaveBeenCalledWith(value);
  expect(loadSaved()[0].description).toBe("Not shared");
});
it("renames and updates evaluation parameters, then confirms local deletion", async () => {
  await saveInvestigation(
    savedContext("position"),
    "Original",
    "",
    localStorage,
  );
  render(<SavedInvestigations onOpen={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Edit Original" }));
  fireEvent.change(screen.getByLabelText("Saved title"), {
    target: { value: "Renamed" },
  });
  fireEvent.change(screen.getByLabelText("Saved evaluation time"), {
    target: { value: "2024-01-01T00:05:00Z" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
  await screen.findByRole("heading", { name: "Renamed" });
  expect(loadSaved()[0].investigation).toMatchObject({
    at: "2024-01-01T00:05:00.000000Z",
  });
  fireEvent.click(screen.getByRole("button", { name: "Delete Renamed" }));
  expect(loadSaved()).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Keep investigation" }));
  expect(
    screen.queryByRole("button", { name: "Confirm local deletion" }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Delete Renamed" }));
  fireEvent.click(
    screen.getByRole("button", { name: "Confirm local deletion" }),
  );
  await screen.findByText(/Deleted from this browser/);
  expect(loadSaved()).toHaveLength(0);
  expect(
    screen.getByRole("heading", { name: "Saved investigations" }),
  ).toHaveFocus();
});
it("updates bounded track sampling and preserves exact source provenance", async () => {
  const original = await saveInvestigation(
    savedContext("ground-track"),
    "Track",
    "",
  );
  render(<SavedInvestigations onOpen={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Edit Track" }));
  fireEvent.change(screen.getByLabelText("Saved step (seconds)"), {
    target: { value: "120" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
  await screen.findByText(/Local investigation updated/);
  expect(loadSaved()[0].investigation.source).toEqual(
    original.investigation.source,
  );
  expect(loadSaved()[0].investigation).toMatchObject({
    at: "2024-01-01T00:02:00.000000Z",
    track: { step_seconds: 120, selected_index: 1 },
  });
});
it("shows a useful empty state and preserves corrupt local data", () => {
  const view = render(<SavedInvestigations onOpen={vi.fn()} />);
  expect(screen.getByText(/No saved investigations yet/)).toBeInTheDocument();
  view.unmount();
  localStorage.setItem(STORAGE_KEY, "bad-json");
  render(<SavedInvestigations onOpen={vi.fn()} />);
  expect(screen.getByRole("alert")).toHaveTextContent(/not been overwritten/);
  fireEvent.click(screen.getByText("Refresh local saves"));
  expect(localStorage.getItem(STORAGE_KEY)).toBe("bad-json");
});
it("announces storage failure without claiming success", async () => {
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("quota", "QuotaExceededError");
  });
  render(<InvestigationActions build={() => savedContext()} />);
  fireEvent.click(screen.getByRole("button", { name: "Save in this browser" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /No save was confirmed/,
  );
  expect(screen.queryByText(/Saved “/)).not.toBeInTheDocument();
});
it("confirms actual clipboard success and excludes titles and notes from sharing", async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal("navigator", { clipboard: { writeText } });
  const v = savedContext("comparison");
  render(<ShareAction investigation={v} />);
  fireEvent.click(screen.getByRole("button", { name: "Copy share link" }));
  await screen.findByText(/Share link copied/);
  expect(parseShareLink(writeText.mock.calls[0][0])).toEqual(v);
});
it("provides an actionable manual link when clipboard access is denied", async () => {
  vi.stubGlobal("navigator", {
    clipboard: { writeText: vi.fn().mockRejectedValue(new Error("denied")) },
  });
  render(<ShareAction investigation={savedContext()} />);
  fireEvent.click(screen.getByRole("button", { name: "Copy share link" }));
  await screen.findByText(/copying has not been confirmed/);
  fireEvent.click(
    screen.getByRole("button", { name: "Select link for manual copying" }),
  );
  expect(screen.getByLabelText("Shareable investigation link")).toHaveFocus();
});
it("does not show mutation or sharing controls inside read-only shared views", async () => {
  const spy = vi.spyOn(Storage.prototype, "setItem");
  render(<InvestigationActions readOnly build={() => savedContext()} />);
  expect(
    screen.queryByRole("button", { name: "Save in this browser" }),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: /Copy share link/ }),
  ).not.toBeInTheDocument();
  expect(
    await screen.findByRole("heading", {
      name: "Investigation report & evidence",
    }),
  ).toBeInTheDocument();
  expect(spy).not.toHaveBeenCalled();
});
it("refreshes a mounted local list when another tab changes storage", async () => {
  const view = render(<SavedInvestigations onOpen={vi.fn()} />);
  await act(async () => {
    await saveInvestigation(savedContext(), "Other tab", "");
  });
  await waitFor(() =>
    expect(
      within(view.container).getByRole("heading", { name: "Other tab" }),
    ).toBeInTheDocument(),
  );
  act(() => {
    window.dispatchEvent(new StorageEvent("storage", { key: STORAGE_KEY }));
  });
  expect(screen.getAllByRole("heading", { name: "Other tab" })).toHaveLength(1);
});
