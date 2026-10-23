// Local-only synthetic saves; file reads and browser download denial are explicit faults.
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import PortableImport, { PortableExport } from "./PortableInvestigations";
import { exportBundle } from "./portable-investigation";
import { loadSaved, parseSaved, STORAGE_KEY } from "./investigation-storage";
import { savedContext } from "./test-fixtures/saved-investigations";
const record = () =>
  parseSaved({
    schema_version: 1,
    id: "c7fcaa37-5da9-4bd5-8000-582c07b6683b",
    title: "E6 SYNTHETIC UI",
    description: "<script>TEST TEXT ONLY</script>",
    created_at: "2026-10-19T00:00:00Z",
    updated_at: "2026-10-19T00:00:00Z",
    investigation: savedContext("comparison"),
  });
function choose(raw = exportBundle(record(), true).json) {
  const bytes = new TextEncoder().encode(raw);
  const file = new File([raw], "local.json", { type: "application/json" });
  Object.defineProperty(file, "arrayBuffer", {
    value: async () => bytes.buffer,
  });
  fireEvent.change(screen.getByLabelText("Portable investigation file"), {
    target: { files: [file] },
  });
}
beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal("navigator", {
    locks: {
      request: (_key: string, fn: () => unknown) => Promise.resolve(fn()),
    },
  });
  vi.stubGlobal(
    "fetch",
    vi.fn(() => {
      throw new Error("No portability network");
    }),
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});
it("previews exact comparison provenance as text, focuses it, cancels without writing, then restores explicitly", async () => {
  render(<PortableImport />);
  choose();
  const heading = await screen.findByRole("heading", {
    name: "Preview portable investigation",
  });
  await waitFor(() => expect(heading).toHaveFocus());
  expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  expect(screen.getByText(/NORAD 25544 \/ snapshot #8/)).toBeInTheDocument();
  expect(screen.getByText("b".repeat(64))).toBeInTheDocument();
  expect(
    screen.getByText("<script>TEST TEXT ONLY</script>"),
  ).toBeInTheDocument();
  expect(document.querySelector("script")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Cancel import" }));
  expect(screen.getByLabelText("Portable investigation file")).toHaveFocus();
  expect(loadSaved()).toEqual([]);
  choose();
  await screen.findByRole("heading", {
    name: "Preview portable investigation",
  });
  fireEvent.click(screen.getByRole("button", { name: "Confirm local import" }));
  await screen.findByText(/Investigation restored in this browser/);
  expect(loadSaved()).toEqual([record()]);
  expect(
    screen.getByRole("heading", { name: "Restore a portable investigation" }),
  ).toHaveFocus();
  expect(fetch).not.toHaveBeenCalled();
});
it("rejects malformed input without mutation and permits choosing a valid file again", async () => {
  render(<PortableImport />);
  choose("{INVALID");
  expect(await screen.findByRole("alert")).toHaveTextContent(/version-1/);
  expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  choose();
  await screen.findByRole("heading", {
    name: "Preview portable investigation",
  });
  expect(
    screen.getByRole("button", { name: "Confirm local import" }),
  ).toBeEnabled();
});
it("requires an explicit collision copy and keeps original content intact", async () => {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ schema_version: 1, records: [record()] }),
  );
  const original = localStorage.getItem(STORAGE_KEY);
  render(<PortableImport />);
  choose(exportBundle({ ...record(), title: "COLLISION TEST" }, true).json);
  await screen.findByRole("heading", {
    name: "Preview portable investigation",
  });
  expect(
    screen.getByRole("button", { name: "Confirm local import" }),
  ).toBeDisabled();
  expect(localStorage.getItem(STORAGE_KEY)).toBe(original);
  fireEvent.click(
    screen.getByLabelText("Import as a separate copy with a new identifier"),
  );
  fireEvent.click(screen.getByRole("button", { name: "Confirm local import" }));
  await screen.findByText(/Investigation restored in this browser/);
  expect(loadSaved()).toHaveLength(2);
  expect(loadSaved().find((r) => r.id === record().id)).toEqual(record());
});
it("shows native quota failure, preserves saves and allows retry", async () => {
  render(<PortableImport />);
  choose();
  await screen.findByRole("heading", {
    name: "Preview portable investigation",
  });
  const write = vi
    .spyOn(Storage.prototype, "setItem")
    .mockImplementationOnce(() => {
      throw new DOMException("Full", "QuotaExceededError");
    });
  fireEvent.click(screen.getByRole("button", { name: "Confirm local import" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/storage|save/i);
  expect(loadSaved()).toEqual([]);
  write.mockRestore();
  fireEvent.click(screen.getByRole("button", { name: "Confirm local import" }));
  await screen.findByText(/Investigation restored in this browser/);
  expect(loadSaved()).toEqual([record()]);
});
it("refuses a destination changed since preview without losing newer saves", async () => {
  render(<PortableImport />);
  choose();
  await screen.findByRole("heading", {
    name: "Preview portable investigation",
  });
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      schema_version: 1,
      records: [
        { ...record(), id: crypto.randomUUID(), title: "NEWER TAB SAVE" },
      ],
    }),
  );
  const newer = localStorage.getItem(STORAGE_KEY);
  fireEvent.click(screen.getByRole("button", { name: "Confirm local import" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /changed since preview/,
  );
  expect(localStorage.getItem(STORAGE_KEY)).toBe(newer);
});
it("exposes export failure and retries without changing source or silently including notes", () => {
  const original = record(),
    before = structuredClone(original);
  const create = vi
    .fn()
    .mockImplementationOnce(() => {
      throw new Error("denied");
    })
    .mockReturnValue("blob:test");
  vi.stubGlobal(
    "URL",
    class extends URL {
      static createObjectURL = create;
      static revokeObjectURL = vi.fn();
    },
  );
  const click = vi
    .spyOn(HTMLAnchorElement.prototype, "click")
    .mockImplementation(() => {});
  render(<PortableExport record={original} />);
  expect(screen.getByRole("checkbox")).not.toBeChecked();
  fireEvent.click(
    screen.getByRole("button", { name: /Export portable bundle/ }),
  );
  expect(screen.getByRole("alert")).toHaveTextContent(/Retry/);
  fireEvent.click(
    screen.getByRole("button", { name: /Export portable bundle/ }),
  );
  expect(screen.getByRole("status")).toHaveTextContent(/notes are excluded/);
  expect(click).toHaveBeenCalledOnce();
  expect(original).toEqual(before);
  expect(fetch).not.toHaveBeenCalled();
});
