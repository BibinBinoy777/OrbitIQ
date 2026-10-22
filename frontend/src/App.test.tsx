import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";
import { getHealth } from "./api";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("shows a successful backend response", async () => {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ status: "ok", service: "OrbitIQ" }),
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<App />);
  expect(await screen.findByText("Backend connected")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/health",
    expect.objectContaining({ signal: expect.any(AbortSignal) }),
  );
});
it("shows a connection failure", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  render(<App />);
  expect(await screen.findByText(/Backend unavailable/)).toBeInTheDocument();
});
it("rejects unsuccessful HTTP responses", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
  await expect(getHealth()).rejects.toThrow("503");
});
it("rejects an invalid health payload", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ status: "wrong" }) }),
  );
  await expect(getHealth()).rejects.toThrow("Unexpected health response");
});
it("terminates a stalled health request", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(
      (_url, options) =>
        new Promise((_resolve, reject) => {
          options.signal.addEventListener("abort", () =>
            reject(options.signal.reason),
          );
        }),
    ),
  );
  await expect(getHealth()).rejects.toMatchObject({ name: "TimeoutError" });
}, 7000);
it("passes caller cancellation to the network request", async () => {
  let requestSignal: AbortSignal | undefined;
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((_url, options) => {
      requestSignal = options.signal;
      return new Promise((_resolve, reject) => {
        requestSignal!.addEventListener("abort", () =>
          reject(requestSignal!.reason),
        );
      });
    }),
  );
  const controller = new AbortController();
  const request = getHealth(controller.signal);
  controller.abort();
  await expect(request).rejects.toMatchObject({ name: "AbortError" });
  expect(requestSignal!.aborted).toBe(true);
});

it("skips repeated navigation without changing the investigation fragment", () => {
  window.history.replaceState(null, "", "/#/saved");
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  render(<App />);
  fireEvent.click(screen.getByRole("link", { name: "Skip to workspace" }));
  expect(document.getElementById("workspace")).toHaveFocus();
  expect(window.location.hash).toBe("#/saved");
  window.history.replaceState(null, "", "/");
});
