import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, fmtShort, fmtT, usd } from "../lib/api";

describe("formatters", () => {
  it("formats times and money", () => {
    expect(fmtT(65.25)).toBe("1:05.3");
    expect(fmtShort(125.9)).toBe("2:05");
    expect(usd(null)).toBe("—");
    expect(usd(1.5)).toBe("$1.50");
  });
});

describe("api client", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("sends the CSRF header and JSON body", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "content-type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    const r = await api("/projects", { body: { title: "x" } });
    expect(r).toEqual({ ok: true });
    const [url, init] = fetchMock.mock.calls[0] as any;
    expect(url).toBe("/api/v1/projects");
    expect(init.method).toBe("POST");
    expect(init.headers["x-fda-request"]).toBe("1");
    expect(JSON.parse(init.body)).toEqual({ title: "x" });
  });
  it("surfaces server error detail", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ detail: "Paid provider needs a spending limit" }), { status: 400, headers: { "content-type": "application/json" } })));
    await expect(api("/x")).rejects.toEqual(new ApiError(400, "Paid provider needs a spending limit"));
  });
});
