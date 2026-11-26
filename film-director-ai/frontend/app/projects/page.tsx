"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ago, api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Empty, Status, toast, useBusy } from "@/components/ui";

export default function Projects() {
  const { data, reload } = useApi<any[]>("/projects");
  const { data: cat } = useApi<any>("/catalog");
  const [open, setOpen] = useState<"" | "new" | "bulk">("");
  const [q, setQ] = useState("");
  const [st, setSt] = useState("");
  const { busy, run } = useBusy();
  useEffect(() => { if (typeof window !== "undefined" && location.search.includes("new=1")) setOpen("new"); }, []);
  const list = (data || []).filter((p) => (!q || p.title.toLowerCase().includes(q.toLowerCase())) && (!st || p.status === st));
  const statuses = Array.from(new Set((data || []).map((p) => p.status)));
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-2"><h1 className="h1">Projects</h1>
        <div className="flex gap-2"><button className="btn" onClick={() => setOpen(open === "bulk" ? "" : "bulk")}>{open === "bulk" ? "Close" : "Bulk create"}</button>
          <button className="btn btn-pri" onClick={() => setOpen(open === "new" ? "" : "new")}>{open === "new" ? "Close" : "New project"}</button></div></div>
      {open === "new" && cat && <NewProject cat={cat} />}
      {open === "bulk" && cat && <BulkCreate cat={cat} done={() => { setOpen(""); reload(); }} />}
      <div className="flex flex-wrap gap-2">
        <input className="input max-w-xs" placeholder="Search projects…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="input w-44" value={st} onChange={(e) => setSt(e.target.value)}><option value="">All statuses</option>{statuses.map((x) => <option key={x}>{x}</option>)}</select>
        <span className="self-center text-xs text-mute">{list.length} of {data?.length || 0}</span>
      </div>
      <div className="flex flex-col gap-1">
        {data?.length === 0 && <Empty>No projects yet.</Empty>}
        {list.map((p) => (
          <div key={p.id} className="grid grid-cols-[1fr_auto] items-center gap-3 rounded-xl border border-transparent px-3 py-3 hover:border-line hover:bg-panel">
            <Link href={`/project/?id=${p.id}`}>
              <div className="font-semibold">{p.title}</div>
              <div className="text-xs text-dim">{cat?.modes?.[p.mode]?.name || p.mode} · {p.language} · {p.scenes} scenes · version {p.current_version} · updated {ago(p.updated_at)}</div>
            </Link>
            <div className="flex flex-wrap items-center justify-end gap-2">
              {p.last_run && <span className="hidden text-xs text-mute sm:inline">{p.last_run.kind}: {p.last_run.status}</span>}<Status s={p.status} />
              {p.last_render?.asset_id && <a className="btn btn-sm" href={`/api/v1/assets/${p.last_render.asset_id}/file?download=1`}>MP4</a>}
              <button className="btn btn-sm" disabled={!!busy} title="Copy settings and script into a new project" onClick={() => run(p.id, async () => { await api(`/projects/${p.id}/duplicate`, { body: {} }); toast("Duplicated"); reload(); })}>Duplicate</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function BulkCreate({ cat, done }: { cat: any; done: () => void }) {
  const { busy, run } = useBusy();
  const [f, setF] = useState<any>({ titles: "", mode: "documentary", language: "en", target_minutes: 3, aspect: "16:9", start: true });
  const n = f.titles.split(/\n+/).filter((t: string) => t.trim()).length;
  return (
    <div className="card grid gap-3 md:grid-cols-4">
      <div className="md:col-span-4"><b>Bulk create</b><p className="text-xs text-dim">One title per line (up to 50). Every video is produced in the background; renders take turns so the server stays responsive.</p></div>
      <textarea className="input min-h-[150px] md:col-span-4" placeholder={"What If Jupiter Disappeared?\nThe Untold Story of the Titanic's Last Hour\n10 Things Your Grandmother Never Threw Away"} value={f.titles} onChange={(e) => setF({ ...f, titles: e.target.value })} />
      <label className="label">Style<select className="input" value={f.mode} onChange={(e) => setF({ ...f, mode: e.target.value })}>{Object.entries(cat.modes).map(([k, v]: any) => <option key={k} value={k}>{v.name}</option>)}</select></label>
      <label className="label">Language<select className="input" value={f.language} onChange={(e) => setF({ ...f, language: e.target.value })}>{Object.entries(cat.languages).map(([k, v]: any) => <option key={k} value={k}>{v}</option>)}</select></label>
      <label className="label">Minutes each<input className="input" type="number" min={0.25} max={60} step={0.25} value={f.target_minutes} onChange={(e) => setF({ ...f, target_minutes: +e.target.value })} /></label>
      <label className="label">Aspect<select className="input" value={f.aspect} onChange={(e) => setF({ ...f, aspect: e.target.value })}>{Object.keys(cat.resolutions).map((a) => <option key={a}>{a}</option>)}</select></label>
      <label className="flex items-center gap-2 text-sm md:col-span-2"><input type="checkbox" checked={f.start} onChange={(e) => setF({ ...f, start: e.target.checked })} /> Start producing immediately</label>
      <div className="flex justify-end md:col-span-2"><button className="btn btn-pri" disabled={!!busy || !n} onClick={() => run("b", async () => {
        const r = await api("/projects/bulk", { body: f }); toast(`${r.created.length} videos created${f.start ? " and queued" : ""}`); done();
      })}>{busy ? "Creating…" : `Create ${n || ""} video${n === 1 ? "" : "s"}`}</button></div>
    </div>
  );
}

const TEMPLATES: { name: string; mode: string; minutes: number; title: string; brief: string }[] = [
  { name: "What If…", mode: "science", minutes: 8, title: "What If the Moon Disappeared Tonight?", brief: "Escalate hour by hour, then day by day. Real physics, scale comparisons, end on the biggest consequence." },
  { name: "Final 24 hours", mode: "historical", minutes: 12, title: "The Final 24 Hours of …", brief: "Minute-by-minute reconstruction with clock times, maps and archive photos. Respectful and factual." },
  { name: "Top 10 countdown", mode: "faceless", minutes: 10, title: "10 Things Nobody Tells You About …", brief: "Countdown to number one, one surprising fact per item, tease number one early." },
  { name: "Grandma tricks (avatar)", mode: "avatar", minutes: 12, title: "Stop Throwing Away … Try This Old Trick Instead", brief: "Warm older host, kitchen-table talk, the why behind every trick, safe methods only." },
  { name: "History documentary", mode: "documentary", minutes: 15, title: "What They Found on … an Hour Before …", brief: "Cold open at the key moment, rewind, timeline, archive footage and maps, payoff at the end." },
  { name: "Science explainer", mode: "educational", minutes: 6, title: "Why Does … Actually Happen?", brief: "One driving question, everyday analogies, diagrams and numbers on screen." },
  { name: "Vertical short", mode: "short", minutes: 0.75, title: "The 1 Thing You Didn't Know About …", brief: "Hook in the first five words, one idea, end on the payoff." },
];

function NewProject({ cat }: { cat: any }) {
  const { busy, run } = useBusy();
  const [f, setF] = useState<any>({ title: "", brief: "", mode: "documentary", language: "en", target_minutes: 3, aspect: "16:9", fps: 30, preserve_narration: true, script: "" });
  const [vo, setVo] = useState<File | null>(null);
  const { data: chars } = useApi<any[]>("/characters");
  useEffect(() => {
    const qs = new URLSearchParams(location.search);
    const c = qs.get("character"), t = qs.get("title");
    if (c) setF((x: any) => ({ ...x, mode: "avatar", character_id: c }));
    if (t) setF((x: any) => ({ ...x, title: t, brief: qs.get("brief") || x.brief, mode: qs.get("mode") || x.mode }));
  }, []);
  const [refs, setRefs] = useState<File[]>([]);
  const set = (k: string, v: any) => setF({ ...f, [k]: v });
  const create = (start: boolean) => run("create", async () => {
    if (!f.title.trim()) throw new Error("Give the video a title");
    const [w, h] = cat.resolutions[f.aspect][0];
    const p = await api("/projects", { body: { ...f, width: w, height: h, script: f.script || undefined } });
    if (vo) { const fd = new FormData(); fd.append("file", vo); fd.append("purpose", "voiceover"); await api(`/projects/${p.id}/uploads`, { form: fd }); }
    for (const r of refs) { const fd = new FormData(); fd.append("file", r); fd.append("purpose", r.type.startsWith("video") ? "footage" : "reference"); await api(`/projects/${p.id}/uploads`, { form: fd }); }
    if (start) await api(`/projects/${p.id}/produce`, { method: "POST" });
    toast(start ? "Production started" : "Project created");
    location.href = `/project/?id=${p.id}`;
  });
  return (
    <div className="card grid gap-4 md:grid-cols-2">
      <div className="flex flex-wrap gap-1.5 md:col-span-2"><span className="self-center text-xs text-dim">Templates:</span>
        {TEMPLATES.map((t) => <button key={t.name} className="btn btn-sm" onClick={() => setF({ ...f, mode: t.mode, target_minutes: t.minutes, title: f.title || t.title, brief: t.brief, aspect: t.mode === "short" ? "9:16" : f.aspect })}>{t.name}</button>)}</div>
      <label className="label md:col-span-2">Title<input className="input text-base" value={f.title} onChange={(e) => set("title", e.target.value)} placeholder="What If Jupiter Disappeared?" /></label>
      <label className="label md:col-span-2">Brief (angle, must-cover points, tone)<textarea className="input min-h-[80px]" value={f.brief} onChange={(e) => set("brief", e.target.value)} /></label>
      <label className="label">Production style
        <select className="input" value={f.mode} onChange={(e) => set("mode", e.target.value)}>{Object.entries(cat.modes).map(([k, v]: any) => <option key={k} value={k}>{v.name}</option>)}</select>
      </label>
      {f.mode === "avatar" && <label className="label md:col-span-2">Host character
        <select className="input" value={f.character_id || ""} onChange={(e) => set("character_id", e.target.value || undefined)}><option value="">Let the Director invent a host for this video</option>{chars?.map((c) => <option key={c.id} value={c.id}>{c.name}{c.voice ? " · " + c.voice : ""}</option>)}</select>
        <span className="font-normal text-mute">Save hosts on the Characters page to reuse the same face and voice.</span></label>}
      <label className="label">Language
        <select className="input" value={f.language} onChange={(e) => set("language", e.target.value)}>{Object.entries(cat.languages).map(([k, v]: any) => <option key={k} value={k}>{v}</option>)}</select>
      </label>
      <label className="label">Target length (minutes, used when writing a script)<input className="input" type="number" min={0.25} max={120} step={0.25} value={f.target_minutes} onChange={(e) => set("target_minutes", +e.target.value)} /></label>
      <div className="grid grid-cols-2 gap-3">
        <label className="label">Aspect<select className="input" value={f.aspect} onChange={(e) => set("aspect", e.target.value)}>{Object.keys(cat.resolutions).map((a) => <option key={a}>{a}</option>)}</select></label>
        <label className="label">FPS<select className="input" value={f.fps} onChange={(e) => set("fps", +e.target.value)}>{cat.fps.map((x: number) => <option key={x}>{x}</option>)}</select></label>
      </div>
      <label className="label">Narration (optional audio upload)<input type="file" accept="audio/*" className="input" onChange={(e) => setVo(e.target.files?.[0] || null)} /></label>
      <label className="label">Reference images / footage (optional)<input type="file" multiple accept="image/*,video/*" className="input" onChange={(e) => setRefs(Array.from(e.target.files || []))} /></label>
      <label className="label md:col-span-2">Script (optional; paste to skip script writing)<textarea className="input min-h-[90px]" value={f.script} onChange={(e) => set("script", e.target.value)} /></label>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.preserve_narration} onChange={(e) => set("preserve_narration", e.target.checked)} /> Preserve uploaded narration exactly</label>
      <div className="flex justify-end gap-2 md:col-span-2">
        <button className="btn" disabled={!!busy} onClick={() => create(false)}>Create only</button>
        <button className="btn btn-pri" disabled={!!busy} onClick={() => create(true)}>{busy ? "Working…" : "Create and produce"}</button>
      </div>
    </div>
  );
}
