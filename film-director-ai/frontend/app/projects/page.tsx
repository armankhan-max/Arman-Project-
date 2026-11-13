"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ago, api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Empty, Status, toast, useBusy } from "@/components/ui";

export default function Projects() {
  const { data, reload } = useApi<any[]>("/projects");
  const { data: cat } = useApi<any>("/catalog");
  const [open, setOpen] = useState(false);
  useEffect(() => { if (typeof window !== "undefined" && location.search.includes("new=1")) setOpen(true); }, []);
  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between"><h1 className="h1">Projects</h1><button className="btn btn-pri" onClick={() => setOpen(!open)}>{open ? "Close" : "New project"}</button></div>
      {open && cat && <NewProject cat={cat} />}
      <div className="flex flex-col gap-1">
        {data?.length === 0 && <Empty>No projects yet.</Empty>}
        {data?.map((p) => (
          <Link key={p.id} href={`/project/?id=${p.id}`} className="grid grid-cols-[1fr_auto] items-center gap-3 rounded-xl border border-transparent px-3 py-3 hover:border-line hover:bg-panel">
            <div>
              <div className="font-semibold">{p.title}</div>
              <div className="text-xs text-dim">{cat?.modes?.[p.mode]?.name || p.mode} · {p.language} · {p.scenes} scenes · version {p.current_version} · updated {ago(p.updated_at)}</div>
            </div>
            <div className="flex items-center gap-2">{p.last_run && <span className="text-xs text-mute">{p.last_run.kind}: {p.last_run.status}</span>}<Status s={p.status} /></div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function NewProject({ cat }: { cat: any }) {
  const { busy, run } = useBusy();
  const [f, setF] = useState<any>({ title: "", brief: "", mode: "documentary", language: "en", target_minutes: 3, aspect: "16:9", fps: 30, preserve_narration: true, script: "" });
  const [vo, setVo] = useState<File | null>(null);
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
      <label className="label md:col-span-2">Title<input className="input text-base" value={f.title} onChange={(e) => set("title", e.target.value)} placeholder="What If Jupiter Disappeared?" /></label>
      <label className="label md:col-span-2">Brief (angle, must-cover points, tone)<textarea className="input min-h-[80px]" value={f.brief} onChange={(e) => set("brief", e.target.value)} /></label>
      <label className="label">Production style
        <select className="input" value={f.mode} onChange={(e) => set("mode", e.target.value)}>{Object.entries(cat.modes).map(([k, v]: any) => <option key={k} value={k}>{v.name}</option>)}</select>
      </label>
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
