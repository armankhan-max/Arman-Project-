"use client";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ago, api, fmtShort } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import Chat from "@/components/Chat";
import Editor from "@/components/Editor";
import RunMonitor from "@/components/RunMonitor";
import { Empty, ErrorBox, Status, Tabs, toast, useBusy } from "@/components/ui";

const TABS: [string, string][] = [["director", "Director"], ["script", "Script & narration"], ["storyboard", "Storyboard"], ["editor", "Editor"], ["assets", "Assets"],
  ["renders", "Renders & QC"], ["research", "Research"], ["versions", "Versions"], ["jobs", "Jobs"], ["settings", "Project settings"]];

export default function Page() {
  return <Suspense fallback={<div className="p-6 text-dim">Loading…</div>}><Workspace /></Suspense>;
}

function Workspace() {
  const id = useSearchParams().get("id") || "";
  const { data: p, error, reload } = useApi<any>(id ? `/projects/${id}` : null);
  const { data: cat } = useApi<any>("/catalog");
  const [tab, setTab] = useState("director");
  const { busy, run } = useBusy();
  useEffect(() => { const t = new URLSearchParams(location.search).get("tab"); if (t) setTab(t); }, []);
  if (!id) return <div className="p-6 text-dim">No project selected.</div>;
  if (error) return <div className="p-6"><ErrorBox e={error} /></div>;
  if (!p) return <div className="p-6 text-dim">Loading…</div>;
  const active = p.runs.find((r: any) => ["pending", "running"].includes(r.status));
  const final = p.renders.find((r: any) => r.status === "succeeded" && r.asset);
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex flex-wrap items-center gap-3 border-b border-line bg-[#0e1014] px-4 py-3 md:px-6">
        <div className="min-w-0 flex-1">
          <div className="truncate text-lg font-bold">{p.title}</div>
          <div className="text-xs text-dim">{cat?.modes?.[p.mode]?.name || p.mode} · {p.language} · {p.settings.width}×{p.settings.height} @ {p.settings.fps}fps · version {p.current_version} · {p.scenes.length} scenes</div>
        </div>
        <Status s={p.status} />
        {!active && <button className="btn btn-pri" disabled={!!busy} onClick={() => run("p", async () => { await api(`/projects/${id}/produce`, { method: "POST" }); reload(); })}>{p.scenes.length ? "Re-run production" : "Produce video"}</button>}
        <a className="btn" href={`/api/v1/projects/${id}/export`}>Export project</a>
      </header>
      <div className="px-4 md:px-6"><Tabs tabs={TABS} value={tab} onChange={setTab} /></div>
      <div className="flex-1 p-4 md:p-6">
        {active && tab !== "jobs" && <div className="card mb-4"><div className="mb-2 text-sm font-semibold">Production in progress · {active.kind}</div><RunMonitor runId={active.id} onEnd={reload} /></div>}
        {tab === "director" && (
          <div className="grid gap-4 lg:grid-cols-[1fr_420px]">
            <div className="flex flex-col gap-4">
              {final ? (
                <div className="card p-2"><video key={final.asset.id} src={final.asset.url} controls className="aspect-video w-full rounded-lg bg-black" />
                  <div className="flex items-center justify-between px-2 pt-2 text-xs text-dim"><span>Render v{final.project_version} · {final.kind} · {ago(final.created_at)} · verified {final.verified ? "✓" : "✗"}</span><a className="text-acc" href={final.asset.url + "?download=1"}>Download MP4</a></div></div>
              ) : <Empty>No render yet. Press “Produce video” or ask the Director.</Empty>}
              {p.quality && <QC q={p.quality} />}
            </div>
            <div className="card h-[640px]"><Chat projectId={id} onAction={reload} /></div>
          </div>
        )}
        {tab === "script" && <ScriptTab p={p} reload={reload} />}
        {tab === "storyboard" && <Storyboard p={p} cat={cat} reload={reload} />}
        {tab === "editor" && <Editor projectId={id} cat={cat} onApplied={reload} busyRun={!!active} />}
        {tab === "assets" && <Assets p={p} reload={reload} />}
        {tab === "renders" && <Renders p={p} cat={cat} reload={reload} />}
        {tab === "research" && <Research p={p} />}
        {tab === "versions" && <Versions p={p} reload={reload} />}
        {tab === "jobs" && <Jobs p={p} />}
        {tab === "settings" && cat && <ProjectSettings p={p} cat={cat} reload={reload} />}
      </div>
    </div>
  );
}

function QC({ q }: { q: any }) {
  const sev: Record<string, string> = { critical: "text-bad", major: "text-bad", minor: "text-warn", info: "text-dim" };
  return (
    <div className="card">
      <div className="mb-2 flex items-center gap-2"><b>Quality control</b><Status s={q.passed ? "passed" : "failed"} /><span className="text-xs text-mute">{ago(q.created_at)} · loudness {q.stats?.lufs ?? "—"} LUFS · peak {q.stats?.peak_db ?? "—"} dB</span></div>
      {q.issues.length === 0 ? <div className="text-sm text-ok">No issues found.</div> : (
        <div className="flex flex-col gap-1 text-sm">
          {q.issues.map((i: any, k: number) => (
            <div key={k} className="flex gap-2"><span className={`w-14 shrink-0 text-xs font-bold uppercase ${sev[i.severity]}`}>{i.severity}</span>
              <span className="flex-1">{i.description}{i.repair ? <span className="text-dim"> → {i.repair}</span> : null}</span>
              {i.repaired && <span className="tag text-info">{i.repaired === true ? "repaired" : i.repaired}</span>}</div>
          ))}
        </div>
      )}
    </div>
  );
}

function ScriptTab({ p, reload }: { p: any; reload: () => void }) {
  const [text, setText] = useState(p.script?.text || "");
  const { busy, run } = useBusy();
  const vo = p.voiceover;
  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
      <div className="card flex flex-col gap-2">
        <div className="flex items-center justify-between"><b>Script</b><span className="text-xs text-dim">{p.script ? `${p.script.origin} · version ${p.script.version} of ${p.script.versions} · ${text.split(/\s+/).filter(Boolean).length} words` : "none yet"}</span></div>
        <textarea className="input min-h-[420px] font-[inherit] leading-relaxed" value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste or write the narration script…" />
        <div className="flex justify-end gap-2"><button className="btn" disabled={!!busy} onClick={() => run("s", async () => { await api(`/projects/${p.id}/script`, { method: "PUT", body: { text } }); toast("Script saved as a new version"); reload(); })}>Save script</button></div>
        {p.voiceover && <p className="text-xs text-mute">Narration already exists. Saving a new script does not change it; re-run production with a new voice upload or delete narration to re-voice.</p>}
      </div>
      <div className="flex flex-col gap-4">
        <div className="card text-sm">
          <b>Narration</b>
          {!vo ? <p className="mt-2 text-dim">No narration yet. Upload a voiceover in Assets or let the Director voice the script.</p> : (
            <div className="mt-2 flex flex-col gap-2">
              <div className="text-xs text-dim">{vo.origin === "upload" ? "Your upload (original preserved)" : "Synthetic voice " + (vo.analysis?.voice || "")} · {fmtShort(vo.duration_s)} · {vo.analysis?.words_per_minute} wpm</div>
              {vo.processed && <audio controls src={vo.processed.url} className="w-full" />}
              {vo.analysis?.integrated_lufs != null && <div className="text-xs text-dim">Loudness {vo.analysis.integrated_lufs} LUFS · peak {vo.analysis.peak_db} dB{vo.analysis.clipping ? " · clipping detected" : ""}</div>}
              {vo.analysis?.long_pauses?.length > 0 && <div className="text-xs text-dim">Long pauses: {vo.analysis.long_pauses.slice(0, 8).map((x: any) => `${fmtShort(x[0])} (${x[1]}s)`).join(", ")}</div>}
            </div>
          )}
        </div>
        {p.transcript && <div className="card text-sm"><b>Transcript</b><div className="mt-1 text-xs text-dim">{p.transcript.provider} · {p.transcript.words} words · {p.transcript.word_level ? "word-level timing" : "approximate timing"}</div><p className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap text-dim">{p.transcript.text}</p></div>}
      </div>
    </div>
  );
}

function Storyboard({ p, cat, reload }: { p: any; cat: any; reload: () => void }) {
  const [edit, setEdit] = useState<any>(null);
  const { busy, run } = useBusy();
  if (!p.scenes.length) return <Empty>No storyboard yet.</Empty>;
  return (
    <div className="flex flex-col gap-3">
      {p.storyboard?.continuity && Object.keys(p.storyboard.continuity).length > 0 && (
        <details className="card text-sm"><summary className="cursor-pointer font-semibold">Continuity bible</summary><pre className="mt-2 whitespace-pre-wrap text-xs text-dim">{JSON.stringify(p.storyboard.continuity, null, 1)}</pre></details>
      )}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {p.scenes.map((s: any) => (
          <div key={s.id} className="card flex flex-col gap-2 p-3">
            <div className="relative aspect-video overflow-hidden rounded-lg bg-panel2">
              {s.asset?.kind === "image" && <img src={s.asset.url} alt="" className="h-full w-full object-cover" />}
              {s.asset?.kind === "video" && <video src={s.asset.url} muted loop playsInline className="h-full w-full object-cover" onMouseEnter={(e) => e.currentTarget.play()} onMouseLeave={(e) => e.currentTarget.pause()} />}
              {!s.asset && <div className="grid h-full place-items-center p-3 text-center text-xs text-dim">{s.visual_type === "motion_graphic" ? `Motion graphic: ${s.plan?.motion_graphic?.type}` : s.asset_status}</div>}
              <span className="absolute left-2 top-2 rounded bg-black/70 px-1.5 py-0.5 text-xs font-bold">#{s.idx}</span>
              <span className="absolute right-2 top-2 rounded bg-black/70 px-1.5 py-0.5 text-[10px] tabnum">{fmtShort(s.start_s)}–{fmtShort(s.end_s)}</span>
            </div>
            <p className="text-sm">{s.narration}</p>
            <div className="flex flex-wrap gap-1"><span className="tag">{s.visual_type.replace("_", " ")}</span><span className="tag">{s.plan?.shot?.replace("_", " ")}</span><span className="tag">{s.plan?.movement?.replace("_", " ")}</span>
              {s.plan?.transition && s.plan.transition !== "cut" && <span className="tag">{s.plan.transition}</span>}<Status s={s.asset_status} />{s.quality_status !== "unchecked" && <Status s={s.quality_status} />}</div>
            {s.plan?.substitution && <div className="text-xs text-warn">Requested {s.plan.substitution.requested}, used {s.plan.substitution.used}</div>}
            {s.last_error && <div className="text-xs text-bad">{s.last_error.slice(0, 200)}</div>}
            <div className="text-xs text-dim">{s.plan?.description}</div>
            {s.plan?.sfx?.length > 0 && <div className="text-xs text-mute">SFX: {s.plan.sfx.join(", ")}</div>}
            {s.asset?.license && <div className="text-[11px] text-mute">{s.asset.source?.provider} · {s.asset.license.license}{s.asset.license.attribution ? ` · ${s.asset.license.attribution}` : ""}</div>}
            <div className="mt-auto flex gap-2">
              <button className="btn btn-sm" onClick={() => setEdit({ ...s, plan: { ...s.plan } })}>Edit plan</button>
              <button className="btn btn-sm" disabled={!!busy} onClick={() => run(s.id, async () => { await api(`/scenes/${s.id}/regenerate`, { method: "POST" }); toast(`Scene ${s.idx} is being regenerated`); reload(); })}>Regenerate</button>
            </div>
          </div>
        ))}
      </div>
      {edit && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/70 p-4" onClick={(e) => e.target === e.currentTarget && setEdit(null)}>
          <div className="card max-h-[90vh] w-full max-w-2xl overflow-auto">
            <div className="mb-3 font-semibold">Scene {edit.idx}</div>
            <div className="grid gap-3 md:grid-cols-2">
              <label className="label">Visual type<select className="input" value={edit.visual_type} onChange={(e) => setEdit({ ...edit, visual_type: e.target.value })}>
                {["stock_video", "ai_video", "ai_image", "archive", "stock_image", "blender", "motion_graphic", "avatar"].map((t) => <option key={t}>{t}</option>)}</select></label>
              <label className="label">Camera movement<select className="input" value={edit.plan.movement} onChange={(e) => setEdit({ ...edit, plan: { ...edit.plan, movement: e.target.value } })}>
                {cat?.movements.map((t: string) => <option key={t}>{t}</option>)}</select></label>
              <label className="label">Transition in<select className="input" value={edit.plan.transition} onChange={(e) => setEdit({ ...edit, plan: { ...edit.plan, transition: e.target.value } })}>
                {cat?.transitions.map((t: string) => <option key={t}>{t}</option>)}</select></label>
              <label className="label">Search query<input className="input" value={edit.plan.search_query || ""} onChange={(e) => setEdit({ ...edit, plan: { ...edit.plan, search_query: e.target.value } })} /></label>
              {edit.visual_type === "blender" && <label className="label">Blender template<select className="input" value={edit.plan.blender_template || "planet"} onChange={(e) => setEdit({ ...edit, plan: { ...edit.plan, blender_template: e.target.value } })}>
                {cat?.blender.templates.map((t: string) => <option key={t}>{t}</option>)}</select></label>}
              <label className="label md:col-span-2">Generation prompt<textarea className="input min-h-[90px]" value={edit.plan.prompt || ""} onChange={(e) => setEdit({ ...edit, plan: { ...edit.plan, prompt: e.target.value } })} /></label>
              {edit.visual_type === "motion_graphic" && <label className="label md:col-span-2">Motion graphic (JSON)<textarea className="input min-h-[90px] font-mono text-xs" defaultValue={JSON.stringify(edit.plan.motion_graphic || { type: "keywords", words: [] }, null, 1)}
                onBlur={(e) => { try { setEdit({ ...edit, plan: { ...edit.plan, motion_graphic: JSON.parse(e.target.value) } }); } catch { toast("Invalid JSON", "bad"); } }} /></label>}
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button className="btn" onClick={() => setEdit(null)}>Cancel</button>
              <button className="btn btn-pri" disabled={!!busy} onClick={() => run("save", async () => {
                await api(`/scenes/${edit.id}`, { method: "PATCH", body: { visual_type: edit.visual_type, plan: edit.plan } });
                await api(`/scenes/${edit.id}/regenerate`, { method: "POST" });
                toast("Saved; regenerating this scene only"); setEdit(null); reload();
              })}>Save & regenerate</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Assets({ p, reload }: { p: any; reload: () => void }) {
  const { busy, run } = useBusy();
  const [purpose, setPurpose] = useState("voiceover");
  const up = (f: File) => run("up", async () => { const fd = new FormData(); fd.append("file", f); fd.append("purpose", purpose); await api(`/projects/${p.id}/uploads`, { form: fd }); toast("Uploaded"); reload(); });
  const sceneAssets = p.scenes.filter((s: any) => s.asset).map((s: any) => ({ ...s.asset, scene: s.idx }));
  return (
    <div className="flex flex-col gap-4">
      <div className="card flex flex-wrap items-end gap-3">
        <label className="label">Upload as<select className="input" value={purpose} onChange={(e) => setPurpose(e.target.value)}>{["voiceover", "script", "reference", "footage", "document", "avatar"].map((x) => <option key={x}>{x}</option>)}</select></label>
        <label className="label flex-1">File<input type="file" className="input" disabled={!!busy} onChange={(e) => e.target.files?.[0] && up(e.target.files[0])} /></label>
        <p className="w-full text-xs text-mute">Originals are stored untouched; processing always works on copies. Uploaded footage can be assigned to a scene from the Editor.</p>
      </div>
      <h3 className="h2">Uploads</h3>
      <AssetGrid items={p.uploads} />
      <h3 className="h2">Scene assets</h3>
      <AssetGrid items={sceneAssets} />
    </div>
  );
}

function AssetGrid({ items }: { items: any[] }) {
  if (!items.length) return <Empty>Nothing here.</Empty>;
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((a) => (
        <div key={a.id + (a.scene || "")} className="card p-2 text-xs">
          <div className="mb-2 aspect-video overflow-hidden rounded bg-panel2">
            {a.kind === "image" && <img src={a.url} alt="" className="h-full w-full object-cover" />}
            {a.kind === "video" && <video src={a.url} muted className="h-full w-full object-cover" />}
            {a.kind === "audio" && <div className="grid h-full place-items-center"><audio controls src={a.url} className="w-[95%]" /></div>}
            {!["image", "video", "audio"].includes(a.kind) && <div className="grid h-full place-items-center text-dim">{a.kind}</div>}
          </div>
          <div className="truncate font-semibold">{a.scene ? `Scene ${a.scene} · ` : ""}{a.filename}</div>
          <div className="text-dim">{a.source?.provider || a.source?.origin} · {a.license?.license || "no licence record"} · commercial: {a.license?.commercial_use || "unknown"}</div>
          {a.source?.source_url && <a className="text-acc" href={a.source.source_url} target="_blank" rel="noreferrer">source</a>}
          {a.source?.prompt && <div className="mt-1 line-clamp-2 text-mute">{a.source.prompt}</div>}
        </div>
      ))}
    </div>
  );
}

function Renders({ p, cat, reload }: { p: any; cat: any; reload: () => void }) {
  const { busy, run } = useBusy();
  const [exp, setExp] = useState({ width: p.settings.width, height: p.settings.height, fps: p.settings.fps, crf: 19 });
  return (
    <div className="flex flex-col gap-4">
      <div className="card flex flex-wrap items-end gap-3">
        <label className="label">Resolution<select className="input" value={`${exp.width}x${exp.height}`} onChange={(e) => { const [w, h] = e.target.value.split("x").map(Number); setExp({ ...exp, width: w, height: h }); }}>
          {cat && Object.values(cat.resolutions).flat().map((r: any) => <option key={r.join("x")} value={r.join("x")}>{r[0]}×{r[1]}</option>)}</select></label>
        <label className="label">FPS<select className="input" value={exp.fps} onChange={(e) => setExp({ ...exp, fps: +e.target.value })}>{cat?.fps.map((f: number) => <option key={f}>{f}</option>)}</select></label>
        <label className="label">Quality (CRF, lower = better)<input className="input w-24" type="number" min={14} max={30} value={exp.crf} onChange={(e) => setExp({ ...exp, crf: +e.target.value })} /></label>
        <button className="btn btn-pri" disabled={!!busy || !p.scenes.length} onClick={() => run("r", async () => { await api(`/projects/${p.id}/apply`, { body: { kind: "final", rebuild: false, ...exp } }); toast("Render started"); reload(); })}>Render</button>
        <button className="btn" disabled={!!busy || !p.scenes.length} onClick={() => run("pv", async () => { await api(`/projects/${p.id}/apply`, { body: { kind: "preview", rebuild: false } }); reload(); })}>Fast preview</button>
        <p className="w-full text-xs text-mute">Changing aspect ratio needs a new storyboard (Project settings). Output is H.264/AAC MP4 and is verified with ffprobe before it is recorded.</p>
      </div>
      {p.quality && <QC q={p.quality} />}
      {p.renders.length === 0 && <Empty>No renders.</Empty>}
      {p.renders.map((r: any) => (
        <div key={r.id} className="card flex flex-wrap items-center gap-3 text-sm">
          <Status s={r.status} /><b>{r.kind}</b><span className="text-dim">v{r.project_version} · {r.settings?.width}×{r.settings?.height} @ {r.settings?.fps}fps · {ago(r.created_at)}</span>
          {r.verified && <span className="tag text-ok">verified {r.probe?.video?.codec}/{r.probe?.audio?.codec} {r.probe?.duration?.toFixed?.(1)}s</span>}
          {r.error && <span className="text-xs text-bad">{r.error.slice(0, 300)}</span>}
          {r.asset && <a className="btn btn-sm ml-auto" href={r.asset.url + "?download=1"}>Download</a>}
        </div>
      ))}
    </div>
  );
}

function Research({ p }: { p: any }) {
  if (!p.research.length) return <Empty>No research for this project (it is skipped when you supply your own script).</Empty>;
  const col: Record<string, string> = { confirmed: "text-ok", disputed: "text-bad", speculative: "text-warn", unverified: "text-dim" };
  return (
    <div className="flex flex-col gap-4">
      {p.research.map((r: any) => (
        <div key={r.id} className="card text-sm">
          <div className="text-xs text-dim">{r.kind} · {ago(r.created_at)} · {r.query}</div>
          <p className="mt-2 whitespace-pre-wrap">{r.summary}</p>
          <div className="mt-3 flex flex-col gap-1">{r.findings.map((f: any, i: number) => (
            <div key={i}><b className={`text-xs uppercase ${col[f.status]}`}>{f.status}</b> {f.claim} {f.source_ids?.length ? <span className="text-mute">[{f.source_ids.map((sid: string) => (r.sources.findIndex((s: any) => s.id === sid) + 1)).join(", ")}]</span> : null}</div>
          ))}</div>
          {r.data?.conflicts?.length > 0 && <div className="mt-2 text-xs text-warn">Conflicts: {r.data.conflicts.join("; ")}</div>}
          <ol className="mt-3 list-decimal pl-5 text-xs text-dim">{r.sources.map((s: any) => <li key={s.id}><a className="text-acc" href={s.url} target="_blank" rel="noreferrer">{s.title || s.url}</a> · {s.publisher} {s.published_at} · retrieved {ago(s.retrieved_at)}</li>)}</ol>
        </div>
      ))}
    </div>
  );
}

function Versions({ p, reload }: { p: any; reload: () => void }) {
  const { busy, run } = useBusy();
  if (!p.versions.length) return <Empty>No saved versions yet.</Empty>;
  return (
    <div className="card divide-y divide-line p-0">
      {p.versions.map((v: any) => (
        <div key={v.version} className="flex items-center gap-3 px-4 py-3 text-sm">
          <b className="w-12">v{v.version}</b><span className="flex-1">{v.reason}</span><span className="text-xs text-dim">{ago(v.created_at)}</span>
          {v.version !== p.current_version && <button className="btn btn-sm" disabled={!!busy} onClick={() => run("v", async () => { await api(`/projects/${p.id}/versions/${v.version}/restore`, { method: "POST" }); toast("Restored as a new version; render to see it"); reload(); })}>Restore</button>}
        </div>
      ))}
    </div>
  );
}

function Jobs({ p }: { p: any }) {
  const [open, setOpen] = useState<string | null>(p.runs[0]?.id || null);
  return (
    <div className="flex flex-col gap-2">
      {p.runs.length === 0 && <Empty>No jobs yet.</Empty>}
      {p.runs.map((r: any) => (
        <div key={r.id} className="card">
          <button className="flex w-full items-center gap-3 text-left text-sm" onClick={() => setOpen(open === r.id ? null : r.id)}>
            <Status s={r.status} /><b>{r.kind}</b><span className="text-dim">{ago(r.created_at)}</span>{r.error && <span className="truncate text-xs text-bad">{r.error}</span>}
          </button>
          {open === r.id && <div className="mt-3"><RunMonitor runId={r.id} /></div>}
        </div>
      ))}
    </div>
  );
}

function ProjectSettings({ p, cat, reload }: { p: any; cat: any; reload: () => void }) {
  const [st, setSt] = useState<any>(p.settings.style);
  const [f, setF] = useState<any>({ title: p.title, brief: p.brief, mode: p.mode, language: p.language, target_minutes: p.settings.target_minutes, preserve_narration: p.preserve_narration });
  const { busy, run } = useBusy();
  const [voices, setVoices] = useState<any[]>([]);
  useEffect(() => { api(`/voices?lang=${p.language}`).then(setVoices).catch(() => setVoices([])); }, [p.language]);
  const S = (k: string, v: any) => setSt({ ...st, [k]: v });
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="card grid gap-3">
        <b>Project</b>
        <label className="label">Title<input className="input" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></label>
        <label className="label">Brief<textarea className="input min-h-[80px]" value={f.brief} onChange={(e) => setF({ ...f, brief: e.target.value })} /></label>
        <div className="grid grid-cols-2 gap-3">
          <label className="label">Style<select className="input" value={f.mode} onChange={(e) => setF({ ...f, mode: e.target.value })}>{Object.entries(cat.modes).map(([k, v]: any) => <option key={k} value={k}>{v.name}</option>)}</select></label>
          <label className="label">Language<select className="input" value={f.language} onChange={(e) => setF({ ...f, language: e.target.value })}>{Object.entries(cat.languages).map(([k, v]: any) => <option key={k} value={k}>{v}</option>)}</select></label>
          <label className="label">Target minutes<input className="input" type="number" value={f.target_minutes} onChange={(e) => setF({ ...f, target_minutes: +e.target.value })} /></label>
          <label className="label">Research<select className="input" value={st.research || "auto"} onChange={(e) => S("research", e.target.value)}><option value="auto">auto</option><option value="on">always</option><option value="off">off</option></select></label>
        </div>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.preserve_narration} onChange={(e) => setF({ ...f, preserve_narration: e.target.checked })} /> Preserve uploaded narration</label>
      </div>
      <div className="card grid gap-3">
        <b>Look & sound</b>
        <div className="grid grid-cols-2 gap-3">
          <label className="label">Look<select className="input" value={st.look} onChange={(e) => S("look", e.target.value)}>{Object.entries(cat.looks).map(([k, v]: any) => <option key={k} value={k}>{v.name}</option>)}</select></label>
          <label className="label">Captions<select className="input" value={st.captions} onChange={(e) => S("captions", e.target.value)}>{cat.captions.map((c: string) => <option key={c}>{c}</option>)}</select></label>
          <label className="label">Music mood<select className="input" value={st.music} onChange={(e) => S("music", e.target.value)}>{cat.music.map((c: string) => <option key={c}>{c}</option>)}</select></label>
          <label className="label">Scene length (s)<input className="input" type="number" step={0.5} min={2} max={10} value={st.pace} onChange={(e) => S("pace", +e.target.value)} /></label>
          <label className="label">Music level<input type="range" min={0} max={1.5} step={0.05} value={st.music_volume} onChange={(e) => S("music_volume", +e.target.value)} /></label>
          <label className="label">SFX level<input type="range" min={0} max={1.5} step={0.05} value={st.sfx_volume} onChange={(e) => S("sfx_volume", +e.target.value)} /></label>
          <label className="label col-span-2">Narration voice (used only when there is no uploaded voiceover)<select className="input" value={st.voice} onChange={(e) => S("voice", e.target.value)}>
            <option value={st.voice}>{st.voice}</option>{voices.map((v) => <option key={v.id} value={v.id}>{v.name} · {v.locale} · {v.gender}</option>)}</select></label>
        </div>
        <div className="flex flex-wrap gap-3 text-sm">
          {Object.keys(st.sources || {}).map((k) => <label key={k} className="flex items-center gap-1.5"><input type="checkbox" checked={!!st.sources[k]} onChange={(e) => S("sources", { ...st.sources, [k]: e.target.checked })} />{k.replace("_", " ")}</label>)}
          <label className="flex items-center gap-1.5"><input type="checkbox" checked={!!st.sfx} onChange={(e) => S("sfx", e.target.checked)} />sound effects</label>
          <label className="flex items-center gap-1.5"><input type="checkbox" checked={!!st.voice_enhance} onChange={(e) => S("voice_enhance", e.target.checked)} />voice clean-up</label>
        </div>
        <label className="label">Never show (comma separated)<input className="input" value={st.blocklist || ""} onChange={(e) => S("blocklist", e.target.value)} /></label>
      </div>
      <div className="flex justify-end gap-2 lg:col-span-2">
        <button className="btn btn-pri" disabled={!!busy} onClick={() => run("s", async () => { await api(`/projects/${p.id}`, { method: "PATCH", body: { ...f, style: st } }); toast("Saved. Use Editor → Apply to remix and re-render."); reload(); })}>Save settings</button>
      </div>
    </div>
  );
}
