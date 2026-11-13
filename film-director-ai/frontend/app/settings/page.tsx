"use client";
import { useEffect, useState } from "react";
import { ago, api, usd } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { ErrorBox, Status, Tabs, toast, useBusy } from "@/components/ui";

export default function Settings() {
  const [tab, setTab] = useState("providers");
  return (
    <div className="flex flex-col gap-4">
      <h1 className="h1">Settings</h1>
      <Tabs value={tab} onChange={setTab} tabs={[["providers", "Providers & API keys"], ["budget", "Budget & limits"], ["usage", "Usage"], ["security", "Security"], ["system", "System"]]} />
      {tab === "providers" && <Providers />}
      {tab === "budget" && <Budget />}
      {tab === "usage" && <Usage />}
      {tab === "security" && <Security />}
      {tab === "system" && <System />}
    </div>
  );
}

function Providers() {
  const { data, reload } = useApi<any[]>("/providers");
  const [open, setOpen] = useState<string | null>(null);
  const caps = Array.from(new Set((data || []).flatMap((p) => p.caps)));
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm text-dim">Keys are encrypted on the server and never sent back to the browser. Paid providers only run when you have set a cost estimate per unit and a daily or monthly budget. “Unverified integration” means the adapter follows the vendor’s public docs but has not been exercised with real credentials yet.</p>
      <div className="flex flex-wrap gap-1 text-[11px] text-mute">{caps.map((c) => <span key={c} className="tag">{c}</span>)}</div>
      {data?.map((p) => (
        <div key={p.name} className="card">
          <button className="flex w-full flex-wrap items-center gap-2 text-left" onClick={() => setOpen(open === p.name ? null : p.name)}>
            <b>{p.label}</b><Status s={p.status} />{p.paid ? <span className="tag text-warn">paid</span> : <span className="tag text-ok">free</span>}
            {!p.verified_integration && <span className="tag">unverified integration</span>}{!p.enabled && <span className="tag text-bad">disabled</span>}
            <span className="ml-auto text-xs text-dim">{p.caps.join(", ")}</span>
          </button>
          {open === p.name && <ProviderForm p={p} done={reload} />}
        </div>
      ))}
    </div>
  );
}

function ProviderForm({ p, done }: { p: any; done: () => void }) {
  const [cred, setCred] = useState<any>({ ...p.credentials });
  const [cfg, setCfg] = useState<any>({ model: p.config?.model || "" });
  const [cost, setCost] = useState(p.usd_per_unit ?? "");
  const [enabled, setEnabled] = useState(p.enabled);
  const { busy, run } = useBusy();
  return (
    <div className="mt-3 grid gap-3 border-t border-line pt-3 text-sm md:grid-cols-2">
      <p className="text-xs text-dim md:col-span-2">{p.notes} {p.docs && <a className="text-acc" href={p.docs} target="_blank" rel="noreferrer">Docs</a>}{p.status_detail && <> · Last check: {p.status_detail} ({ago(p.checked_at)})</>}</p>
      {p.fields.map((f: any) => (
        <label key={f.name} className="label">{f.label}{f.env ? <span className="font-normal text-mute">or env {f.env}</span> : null}
          <input className="input" type={f.secret ? "password" : "text"} autoComplete="off" value={cred[f.name] || ""} onChange={(e) => setCred({ ...cred, [f.name]: e.target.value })} /></label>
      ))}
      {p.caps.some((c: string) => ["llm", "text_to_image", "tts", "image_to_video", "text_to_video"].includes(c)) && <label className="label">Model (blank = default)<input className="input" value={cfg.model} onChange={(e) => setCfg({ ...cfg, model: e.target.value })} /></label>}
      {p.paid && <label className="label">Your cost estimate, USD per {p.unit}<input className="input" type="number" step="0.0001" min={0} value={cost} onChange={(e) => setCost(e.target.value)} placeholder="from the vendor's pricing page" /></label>}
      <label className="flex items-center gap-2"><input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} /> Enabled</label>
      <div className="flex gap-2 md:col-span-2">
        <button className="btn btn-pri btn-sm" disabled={!!busy} onClick={() => run("s", async () => { await api(`/providers/${p.name}`, { method: "PUT", body: { credentials: cred, config: cfg, enabled, usd_per_unit: cost === "" ? null : +cost } }); toast("Saved"); done(); })}>Save</button>
        <button className="btn btn-sm" disabled={!!busy} onClick={() => run("c", async () => { const r = await api(`/providers/${p.name}/check`, { method: "POST" }); toast(`${r.status}: ${r.detail}`, r.status === "ok" ? "" : "bad"); done(); })}>Test connection</button>
      </div>
    </div>
  );
}

function Budget() {
  const { data, reload } = useApi<any>("/budget");
  const [d, setD] = useState("");
  const [mo, setMo] = useState("");
  const [pw, setPw] = useState("");
  const { busy, run } = useBusy();
  if (!data) return null;
  const set = (scope: string, v: string) => run(scope, async () => { await api("/budget", { method: "PUT", body: { scope, limit_usd: v === "" ? null : +v } }); toast("Budget updated"); reload(); });
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {!data.configured && <div className="md:col-span-2"><ErrorBox e="No spending limit is set, so paid providers will not run. Free providers keep working." /></div>}
      <div className="card flex flex-col gap-2 text-sm"><b>Daily limit</b><div className="text-dim">Spent today {usd(data.daily.spent)} of {data.daily.limit == null ? "no limit" : usd(data.daily.limit)}</div>
        <div className="flex gap-2"><input className="input" type="number" min={0} step="0.5" placeholder="USD" value={d} onChange={(e) => setD(e.target.value)} /><button className="btn" disabled={!!busy} onClick={() => set("daily", d)}>Set</button><button className="btn btn-ghost" onClick={() => set("daily", "")}>Remove</button></div></div>
      <div className="card flex flex-col gap-2 text-sm"><b>Monthly limit</b><div className="text-dim">Spent this month {usd(data.monthly.spent)} of {data.monthly.limit == null ? "no limit" : usd(data.monthly.limit)}</div>
        <div className="flex gap-2"><input className="input" type="number" min={0} step="1" placeholder="USD" value={mo} onChange={(e) => setMo(e.target.value)} /><button className="btn" disabled={!!busy} onClick={() => set("monthly", mo)}>Set</button><button className="btn btn-ghost" onClick={() => set("monthly", "")}>Remove</button></div></div>
      <div className="card flex flex-col gap-2 text-sm md:col-span-2">
        <b>Owner unlimited mode</b>
        <p className="text-dim">Turn off all spending blocks so every provider you have connected can run without limits or cost estimates. Usage is still recorded. Your own provider accounts are still billed by their vendors. Needs your password.</p>
        <div className="flex items-center gap-2"><span className={`tag ${data.owner_override ? "text-ok" : ""}`}>{data.owner_override ? "unlimited ON" : "limits apply"}</span>
          <input className="input max-w-xs" type="password" placeholder="Owner password" value={pw} onChange={(e) => setPw(e.target.value)} />
          <button className="btn" disabled={!!busy || !pw} onClick={() => run("o", async () => { await api("/budget/override", { method: "PUT", body: { on: !data.owner_override, password: pw } }); setPw(""); toast(data.owner_override ? "Limits are back on" : "Unlimited mode on"); reload(); })}>{data.owner_override ? "Turn off" : "Turn on"}</button></div>
      </div>
      <div className="card text-sm text-dim md:col-span-2">The Director can never change limits or this mode by itself. Per-project and per-provider limits can be set through the API (<code>PUT /api/v1/budget</code> with scope project/provider). Retries per task and concurrency are capped by <code>FDA_MAX_RETRIES</code> and <code>FDA_MAX_CONCURRENT_JOBS</code>.</div>
    </div>
  );
}

function Usage() {
  const { data } = useApi<any>("/usage?days=30");
  if (!data) return null;
  return (
    <div className="flex flex-col gap-3">
      <div className="card overflow-x-auto p-0"><table className="w-full text-sm"><thead className="text-left text-xs text-mute"><tr><th className="px-3 py-2">Provider</th><th>Operations</th><th>Estimated</th><th>Actual</th></tr></thead>
        <tbody>{data.by_provider.map((r: any) => <tr key={r.provider} className="border-t border-line"><td className="px-3 py-2">{r.provider}</td><td>{r.operations}</td><td className="tabnum">{usd(r.estimated_usd)}</td><td className="tabnum">{r.actual_usd == null ? "not reported" : usd(r.actual_usd)}</td></tr>)}</tbody></table></div>
      <div className="card overflow-x-auto p-0"><table className="w-full text-sm"><thead className="text-left text-xs text-mute"><tr><th className="px-3 py-2">Reasoning model</th><th>Calls</th><th>Input tokens</th><th>Output tokens</th></tr></thead>
        <tbody>{data.llm.map((r: any) => <tr key={r.provider} className="border-t border-line"><td className="px-3 py-2">{r.provider}</td><td>{r.calls}</td><td className="tabnum">{r.input_tokens.toLocaleString()}</td><td className="tabnum">{r.output_tokens.toLocaleString()}</td></tr>)}</tbody></table></div>
      <div className="card max-h-96 overflow-auto p-0"><table className="w-full text-xs"><tbody>{data.records.map((r: any) => (
        <tr key={r.id} className="border-t border-line"><td className="px-3 py-1.5 text-mute">{ago(r.created_at)}</td><td>{r.provider}</td><td>{r.operation}</td><td className="tabnum">{Number(r.units).toFixed(2)} {r.unit}</td><td className="tabnum">{usd(r.estimated_usd)}</td><td>{r.status}</td></tr>
      ))}</tbody></table></div>
    </div>
  );
}

function Security() {
  const [cur, setCur] = useState("");
  const [nw, setNw] = useState("");
  const { busy, run } = useBusy();
  return (
    <div className="card flex max-w-md flex-col gap-2 text-sm">
      <b>Change owner password</b>
      <input className="input" type="password" placeholder="Current password" value={cur} onChange={(e) => setCur(e.target.value)} />
      <input className="input" type="password" placeholder="New password (10+ characters)" value={nw} onChange={(e) => setNw(e.target.value)} />
      <button className="btn btn-pri w-fit" disabled={!!busy} onClick={() => run("p", async () => { await api("/auth/password", { body: { current: cur, new: nw } }); toast("Password changed"); setCur(""); setNw(""); })}>Change password</button>
      <p className="text-xs text-dim">Sessions are signed, HTTP-only, SameSite=strict cookies. Every state-changing request needs a custom header (CSRF protection). Credentials are encrypted at rest with a key derived from FDA_SECRET_KEY.</p>
    </div>
  );
}

function System() {
  const [h, setH] = useState<any>(null);
  useEffect(() => { fetch("/api/health").then((r) => r.json()).then(setH).catch(() => {}); }, []);
  const { data: cat } = useApi<any>("/catalog");
  return (
    <div className="card grid gap-2 text-sm">
      {h && Object.entries(h).map(([k, v]) => <div key={k} className="flex gap-2"><b className="w-24">{k}</b><span className={String(v) === "ok" ? "text-ok" : "text-warn"}>{String(v)}</span></div>)}
      {cat && <div className="flex gap-2"><b className="w-24">Blender</b><span>{cat.blender.available ? "available · templates: " + cat.blender.templates.join(", ") : "not installed"}</span></div>}
      <div className="mt-2 flex items-center gap-2 border-t border-line pt-3">
        <button className="btn btn-sm" onClick={async () => { try { const r = await api("/maintenance/cleanup", { body: {} }); toast(`Purged ${r.projects_purged} deleted projects, removed ${r.scratch_removed} scratch folders`); } catch (e: any) { toast(e.message, "bad"); } }}>Clean up storage</button>
        <span className="text-xs text-dim">Removes projects deleted more than 7 days ago and old scratch files. Runs automatically every 6 hours with Celery beat.</span>
      </div>
    </div>
  );
}
