export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T = any>(path: string, opts: { method?: string; body?: any; form?: FormData } = {}): Promise<T> {
  const headers: Record<string, string> = { "x-fda-request": "1" };
  const init: RequestInit = { method: opts.method || (opts.body !== undefined || opts.form ? "POST" : "GET"), credentials: "include", headers };
  if (opts.form) init.body = opts.form;
  else if (opts.body !== undefined) {
    init.body = JSON.stringify(opts.body);
    headers["content-type"] = "application/json";
  }
  const r = await fetch("/api/v1" + path, init);
  if (r.status === 401 && typeof window !== "undefined" && !location.pathname.startsWith("/login")) location.href = "/login";
  if (!r.ok) {
    let msg = r.statusText;
    try {
      const j = await r.json();
      msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {}
    throw new ApiError(r.status, msg);
  }
  const ct = r.headers.get("content-type") || "";
  return (ct.includes("json") ? r.json() : (r.text() as any)) as T;
}

export const fmtT = (t: number) => {
  t = Math.max(0, t || 0);
  const m = Math.floor(t / 60);
  return `${m}:${(t - m * 60).toFixed(1).padStart(4, "0")}`;
};
export const fmtShort = (t: number) => {
  t = Math.max(0, Math.floor(t || 0));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
};
export const ago = (iso?: string | null) => {
  if (!iso) return "—";
  const d = (Date.now() - new Date(iso).getTime()) / 1000;
  return d < 90 ? "just now" : d < 3600 ? `${Math.round(d / 60)} min ago` : d < 86400 ? `${Math.round(d / 3600)} h ago` : `${Math.round(d / 86400)} d ago`;
};
export const usd = (n?: number | null) => (n == null ? "—" : `$${Number(n).toFixed(2)}`);
