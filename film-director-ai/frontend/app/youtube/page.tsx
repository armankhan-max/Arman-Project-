"use client";
import Link from "next/link";
import { useState } from "react";
import { ago, api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Empty, ErrorBox, Status, Tabs, toast, useBusy } from "@/components/ui";

const n = (x: any) => (x == null ? "—" : Number(x) >= 1e6 ? (x / 1e6).toFixed(1) + "M" : Number(x) >= 1e3 ? Math.round(x / 1e3) + "K" : String(Math.round(x * 10) / 10));

export default function YouTube() {
  const [tab, setTab] = useState("channel");
  const { data: st, reload } = useApi<any>("/youtube/status");
  return (
    <div className="flex flex-col gap-4">
      <div><h1 className="h1">YouTube Intelligence</h1><p className="text-sm text-dim">Public research uses the YouTube Data API. Your own analytics use read-only OAuth. The two are never mixed up, and every number shows when it was retrieved.</p></div>
      <Tabs value={tab} onChange={setTab} tabs={[["channel", "My channel"], ["videos", "Video analytics"], ["research", "Public research"], ["competitors", "Competitors"], ["reports", "Reports"], ["api", "API status"]]} />
      {tab === "channel" && <MyChannel st={st} reload={reload} />}
      {tab === "videos" && <VideoAnalytics />}
      {tab === "research" && <PublicResearch />}
      {tab === "competitors" && <Competitors />}
      {tab === "reports" && <Reports />}
      {tab === "api" && st && (
        <div className="card grid gap-2 text-sm">
          <div className="flex items-center gap-2">Public Data API key <Status s={st.public_api.configured ? "ok" : "unconfigured"} /></div>
          <div className="flex items-center gap-2">OAuth client <Status s={st.oauth.configured ? "ok" : "unconfigured"} /> <span className="text-xs text-dim">Redirect URI to register in Google Cloud: <code>{st.oauth.redirect_uri}</code></span></div>
          <div className="flex items-center gap-2">Channel connection <Status s={st.connection?.status || "unconfigured"} /> {st.connection?.last_error && <span className="text-xs text-bad">{st.connection.last_error}</span>}</div>
          <Link className="text-acc" href="/settings">Configure keys in Settings → Providers</Link>
        </div>
      )}
    </div>
  );
}

function MyChannel({ st, reload }: { st: any; reload: () => void }) {
  const { busy, run } = useBusy();
  const { data: mt, reload: rm } = useApi<any>("/youtube/channel-metrics?days=90");
  if (!st) return null;
  if (!st.channel) return (
    <div className="card flex flex-col gap-3 text-sm">
      <p>Connect your channel with read-only permission (youtube.readonly + yt-analytics.readonly). Nothing is ever uploaded or changed.</p>
      {!st.oauth.configured && <ErrorBox e="Add your Google OAuth client ID and secret in Settings → Providers → Google OAuth first." />}
      <button className="btn btn-pri w-fit" disabled={!st.oauth.configured || !!busy} onClick={() => run("c", async () => { const r = await api("/youtube/oauth/start"); location.href = r.url; })}>Connect YouTube channel</button>
    </div>
  );
  const daily = mt?.daily || [];
  const max = Math.max(1, ...daily.map((d: any) => d.views || 0));
  const tot = (k: string) => daily.reduce((a: number, d: any) => a + (d[k] || 0), 0);
  return (
    <div className="flex flex-col gap-4">
      <div className="card flex flex-wrap items-center gap-3 text-sm">
        <b>{st.channel.title}</b><Status s={st.connection?.status} /><span className="text-xs text-dim">synced {ago(st.channel.last_synced_at)}</span>
        <button className="btn btn-sm ml-auto" disabled={!!busy} onClick={() => run("s", async () => { const r = await api("/youtube/sync", { body: { days: 90 } }); toast(`Synced ${r.rows} metric rows`); rm(); reload(); })}>Sync analytics</button>
        <button className="btn btn-sm" disabled={!!busy} onClick={() => run("a", async () => { await api("/youtube/analyze-own", { method: "POST" }); toast("Analysis saved to Reports and performance memory"); })}>Analyse performance</button>
        <button className="btn btn-sm btn-ghost" onClick={() => run("d", async () => { await api("/youtube/disconnect", { method: "POST" }); reload(); })}>Disconnect</button>
      </div>
      <div className="grid gap-3 sm:grid-cols-4">
        {[["Views (90d)", tot("views")], ["Watch time (min)", tot("estimatedMinutesWatched")], ["Subscribers gained", tot("subscribersGained")], ["Subscribers lost", tot("subscribersLost")]].map(([l, v]) => (
          <div key={l as string} className="card"><div className="text-xs text-dim">{l}</div><div className="text-xl font-bold tabnum">{n(v)}</div></div>
        ))}
      </div>
      <div className="card">
        <div className="mb-2 text-sm font-semibold">Daily views</div>
        {daily.length === 0 ? <Empty>No synced data yet.</Empty> : (
          <div className="flex h-40 items-end gap-px">{daily.map((d: any) => <div key={d.day} title={`${d.day}: ${d.views}`} className="flex-1 rounded-t bg-acc/80" style={{ height: `${(100 * (d.views || 0)) / max}%` }} />)}</div>
        )}
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="card text-sm"><b>Traffic sources</b>{(mt?.traffic || []).map(([k, v]: any) => <div key={k} className="flex justify-between border-b border-line py-1 text-xs"><span>{k}</span><span className="tabnum">{n(v)}</span></div>)}</div>
        <div className="card text-sm"><b>Not available</b><ul className="mt-1 list-disc pl-5 text-xs text-dim">{(mt?.unavailable || []).map((u: string, i: number) => <li key={i}>{u}</li>)}</ul></div>
      </div>
    </div>
  );
}

function VideoAnalytics() {
  const { data } = useApi<any>("/youtube/channel-metrics?days=90");
  if (!data?.videos?.length) return <Empty>Connect and sync your channel to see per-video analytics.</Empty>;
  return (
    <div className="card overflow-x-auto p-0">
      <table className="w-full text-sm">
        <thead className="text-left text-xs text-mute"><tr>{["Video", "Views", "Watch min", "Avg view %", "Avg view s", "Subs +"].map((h) => <th key={h} className="px-3 py-2">{h}</th>)}</tr></thead>
        <tbody>{data.videos.map((v: any) => (
          <tr key={v.id} className="border-t border-line"><td className="max-w-md truncate px-3 py-2">{v.title}</td><td className="px-3 tabnum">{n(v.views)}</td><td className="px-3 tabnum">{n(v.estimatedMinutesWatched)}</td>
            <td className="px-3 tabnum">{v.averageViewPercentage?.toFixed?.(1) ?? "—"}</td><td className="px-3 tabnum">{n(v.averageViewDuration)}</td><td className="px-3 tabnum">{n(v.subscribersGained)}</td></tr>
        ))}</tbody>
      </table>
      <div className="px-3 py-2 text-xs text-mute">Source: YouTube Analytics API (authorised) · retrieved {ago(data.retrieved_at)}</div>
    </div>
  );
}

function PublicResearch() {
  const [q, setQ] = useState("");
  const [days, setDays] = useState<string>("");
  const [rep, setRep] = useState<any>(null);
  const { busy, run } = useBusy();
  return (
    <div className="flex flex-col gap-3">
      <div className="card flex flex-wrap gap-2">
        <input className="input flex-1" placeholder="Topic or niche, e.g. 'what if planets disappeared'" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="input w-40" value={days} onChange={(e) => setDays(e.target.value)}><option value="">Any time</option><option value="30">Last 30 days</option><option value="180">Last 6 months</option><option value="365">Last year</option></select>
        <button className="btn btn-pri" disabled={!q || !!busy} onClick={() => run("r", async () => setRep(await api("/youtube/research", { body: { query: q, n: 30, days: days ? +days : null } })))}>{busy ? "Researching…" : "Research"}</button>
      </div>
      {rep && <Report r={rep} />}
    </div>
  );
}

function Competitors() {
  const [ref, setRef] = useState("");
  const [d, setD] = useState<any>(null);
  const { busy, run } = useBusy();
  return (
    <div className="flex flex-col gap-3">
      <div className="card flex gap-2"><input className="input flex-1" placeholder="@handle, channel URL or UC… id" value={ref} onChange={(e) => setRef(e.target.value)} />
        <button className="btn btn-pri" disabled={!ref || !!busy} onClick={() => run("c", async () => setD(await api("/youtube/channel", { body: { ref, n: 30 } })))}>Analyse channel</button></div>
      {d && (
        <div className="card">
          <div className="mb-2 font-semibold">{d.channel.title} <span className="text-xs text-dim">{n(d.channel.meta?.subscribers)} subscribers · {n(d.channel.meta?.videos)} videos · public data</span></div>
          <table className="w-full text-sm"><tbody>{d.videos.map((v: any) => (
            <tr key={v.id} className="border-t border-line"><td className="max-w-md truncate py-1.5">{v.title}</td><td className="tabnum">{n(v.views)}</td><td className="tabnum text-dim">{n(v.views_per_day)}/day</td><td className="text-dim">{v.duration_min}m</td><td className="text-xs text-mute">{v.published}</td></tr>
          ))}</tbody></table>
        </div>
      )}
    </div>
  );
}

function Reports() {
  const { data } = useApi<any[]>("/reports");
  if (!data?.length) return <Empty>No reports yet.</Empty>;
  return <div className="flex flex-col gap-3">{data.map((r) => <Report key={r.id} r={r} />)}</div>;
}

function Report({ r }: { r: any }) {
  return (
    <div className="card text-sm">
      <div className="text-xs text-dim">{r.kind.replace("_", " ")} · {r.query} · {ago(r.created_at)} · {r.data?.source || ""}</div>
      <p className="mt-2 whitespace-pre-wrap">{r.summary}</p>
      {r.data?.outliers?.length > 0 && <div className="mt-3"><b className="text-xs">Outliers vs their channel median</b>{r.data.outliers.map((o: any) => <div key={o.id} className="text-xs text-dim">{o.ratio_to_channel_median}× · {o.title}</div>)}</div>}
      {r.data?.correlations && <div className="mt-2 text-xs text-dim">Correlations (association only): {Object.entries(r.data.correlations).map(([k, v]) => `${k}: ${v ?? "n/a"}`).join(" · ")}</div>}
      {r.data?.unavailable?.length > 0 && <div className="mt-2 text-xs text-warn">Unavailable: {r.data.unavailable.join("; ")}</div>}
    </div>
  );
}
