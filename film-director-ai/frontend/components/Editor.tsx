"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { api, fmtT } from "@/lib/api";
import { Empty, toast, useBusy } from "./ui";

const MOTIONS = ["push_in", "pull_out", "pan_left", "pan_right", "pan_up", "pan_down", "drift", "orbit", "tilt", "parallax", "focus_pull", "ramp_push", "handheld", "card", "polaroid", "static"];
const FILTERS = ["none", "cinematic", "bw", "sepia", "cold", "warm", "vivid", "faded", "noir", "dream"];
const TRANS = ["cut", "fade", "dip", "flash", "zoom", "push", "slide", "wipe", "glitch", "burn", "pop"];
const COLORS: Record<string, string> = { video: "#2d4a6b", image: "#3b4a2d", motion_graphic: "#4a2d6b", avatar: "#6b4a2d", blender: "#2d6b62", placeholder: "#6b2d38", text: "#2d6b46" };

export default function Editor({ projectId, cat, onApplied, busyRun }: { projectId: string; cat: any; onApplied: () => void; busyRun: boolean }) {
  const [tl, setTl] = useState<any>(null);
  const [proj, setProj] = useState<any>(null);
  const [sel, setSel] = useState<any>(null);
  const [zoom, setZoom] = useState(24);
  const [t, setT] = useState(0);
  const [dirtyAudio, setDirtyAudio] = useState(false);
  const [dirty, setDirty] = useState(false);
  const video = useRef<HTMLVideoElement>(null);
  const { busy, run } = useBusy();
  const load = async () => { setTl(await api(`/projects/${projectId}/timeline`)); setProj(await api(`/projects/${projectId}`)); };
  useEffect(() => { load().catch((e) => toast(e.message, "bad")); }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps
  const render = proj?.renders?.find((r: any) => r.status === "succeeded" && r.asset);
  const tracks = useMemo(() => {
    if (!tl) return null;
    return { V1: tl.items.filter((i: any) => i.track === "V1"), V2: tl.items.filter((i: any) => i.track === "V2"), T1: tl.items.filter((i: any) => i.track === "T1") };
  }, [tl]);
  if (!tl || !tracks) return <div className="text-dim">Loading timeline…</div>;
  if (!tl.items.length) return <Empty>The timeline is built after the storyboard and visuals are ready.</Empty>;
  const W = Math.max(800, tl.duration * zoom + 40);
  const seek = (x: number) => { setT(x); if (video.current) video.current.currentTime = x; };
  const patchItem = (it: any, body: any) => run("p", async () => { await api(`/timeline/${it.id}`, { method: "PATCH", body }); setDirty(true); await load(); });
  const audioTrack = (role: string) => tl.audio.find((a: any) => a.role === role);
  const sfx = audioTrack("sfx");
  const clip = (it: any, track: string) => (
    <button key={it.id} onClick={() => setSel({ ...it, _track: track })} title={`${it.kind} ${fmtT(it.start_s)} (${it.duration_s.toFixed(1)}s)`}
      className={`absolute bottom-1 top-1 overflow-hidden rounded border text-left text-[10px] ${sel?.id === it.id ? "z-10 border-acc ring-1 ring-acc" : "border-black/50"}`}
      style={{ left: it.start_s * zoom, width: Math.max(4, it.duration_s * zoom - 1), background: COLORS[it.kind] || "#333" }}>
      {it.asset?.kind === "image" && <img src={it.asset.url} alt="" className="absolute inset-0 h-full w-full object-cover opacity-60" />}
      {it.props?.transition && it.props.transition !== "cut" && <span className="absolute inset-y-0 left-0 w-1.5 bg-acc" />}
      <span className="relative block truncate px-1 font-semibold text-white drop-shadow">{it.scene_idx ? `#${it.scene_idx} ` : ""}{it.props?.text || it.props?.type || it.kind}</span>
    </button>
  );
  const row = (label: string, children: React.ReactNode, h = "h-14") => (
    <div className={`relative border-b border-line/60 ${h}`}><span className="sticky left-0 z-20 inline-block rounded-br bg-black/70 px-1.5 text-[9px] font-bold text-mute">{label}</span>{children}</div>
  );
  return (
    <div className="flex flex-col gap-3">
      <div className="grid gap-3 lg:grid-cols-[1fr_360px]">
        <div className="card p-2">
          {render ? <video ref={video} src={render.asset.url} controls className="aspect-video w-full rounded bg-black" onTimeUpdate={(e) => setT(e.currentTarget.currentTime)} />
            : <div className="grid aspect-video place-items-center rounded bg-black text-sm text-dim">Render once to preview here</div>}
          <div className="flex items-center justify-between px-1 pt-2 text-xs text-dim">
            <span className="tabnum">{fmtT(t)} / {fmtT(tl.duration)} · timeline v{tl.version}{render ? ` · preview shows render v${render.project_version}` : ""}</span>
            <span>{dirty || dirtyAudio ? <b className="text-warn">Unapplied changes</b> : "Up to date"}</span>
          </div>
        </div>
        <div className="card flex max-h-[520px] flex-col gap-3 overflow-auto text-sm">
          {!sel && <div className="text-dim">Select a clip on the timeline to edit it. Main-track clips stay locked to the narration timing; overlays and text move freely.</div>}
          {sel && sel._track === "V1" && <ClipInspector it={sel} proj={proj} patch={(b: any) => patchItem(sel, b).then(() => setSel(null))} regenerate={() => run("r", async () => {
            const sc = proj.scenes.find((s: any) => s.idx === sel.scene_idx); await api(`/scenes/${sc.id}/regenerate`, { method: "POST" }); toast(`Regenerating scene ${sel.scene_idx}`); onApplied();
          })} />}
          {sel && sel._track !== "V1" && <OverlayInspector it={sel} cat={cat} patch={(b: any) => patchItem(sel, b)} remove={() => run("d", async () => { await api(`/timeline/${sel.id}`, { method: "DELETE" }); setSel(null); setDirty(true); load(); })} />}
        </div>
      </div>
      <div className="card flex flex-wrap items-center gap-2 p-2 text-sm">
        <button className="btn btn-sm" onClick={() => run("t", async () => { await api(`/projects/${projectId}/timeline`, { body: { kind: "text", start_s: t, duration_s: 3, props: { text: "New title", size: 72, anim: "pop", x: 0.5, y: 0.2 } } }); setDirty(true); load(); })}>+ Text at playhead</button>
        <select className="input w-44 py-1 text-xs" defaultValue="" onChange={(e) => { const ty = e.target.value; e.target.value = ""; if (ty) run("m", async () => { await api(`/projects/${projectId}/timeline`, { body: { kind: "motion_graphic", start_s: t, duration_s: 4, props: { mg: { type: ty, text: "Title", label: "Label", words: ["KEY", "WORDS"], value: 100 } } } }); setDirty(true); load(); }); }}>
          <option value="">+ Motion graphic…</option>{cat?.motion_graphics.map((m: string) => <option key={m}>{m}</option>)}
        </select>
        <span className="mx-2 h-5 w-px bg-line" />
        {["voice", "music", "sfx"].map((role) => { const a = audioTrack(role); if (!a) return null; return (
          <label key={role} className="flex items-center gap-1.5 text-xs text-dim">{role}
            {role === "voice" ? <input type="checkbox" checked={!!a.props?.enhance} onChange={(e) => run("a", async () => { await api(`/audio/${a.id}`, { method: "PATCH", body: { enhance: e.target.checked } }); setDirtyAudio(true); load(); })} title="Voice clean-up" />
              : <><input type="range" min={0} max={1.5} step={0.05} defaultValue={a.volume} onMouseUp={(e) => run("a", async () => { await api(`/audio/${a.id}`, { method: "PATCH", body: { volume: +(e.target as HTMLInputElement).value } }); setDirtyAudio(true); load(); })} className="w-20" />
                <input type="checkbox" checked={!a.muted} title="On/off" onChange={(e) => run("a", async () => { await api(`/audio/${a.id}`, { method: "PATCH", body: { muted: !e.target.checked } }); setDirtyAudio(true); load(); })} /></>}
          </label>); })}
        <span className="ml-auto flex items-center gap-2 text-xs text-dim">Zoom<input type="range" min={6} max={120} value={zoom} onChange={(e) => setZoom(+e.target.value)} /></span>
        <button className="btn btn-pri btn-sm" disabled={!!busy || busyRun} onClick={() => run("apply", async () => {
          await api(`/projects/${projectId}/apply`, { body: { remix: dirtyAudio, rebuild: true, kind: "final", reason: "Editor changes" } }); setDirty(false); setDirtyAudio(false); toast("Applying edits: rebuild → render → QC"); onApplied();
        })}>Apply & render</button>
      </div>
      <div className="card overflow-x-auto p-0">
        <div className="relative" style={{ width: W }}>
          <div className="relative h-6 border-b border-line bg-[#0e1014] text-[10px] text-mute" onClick={(e) => seek((e.clientX - (e.currentTarget.getBoundingClientRect().left)) / zoom)}>
            {Array.from({ length: Math.ceil(tl.duration / 5) + 1 }).map((_, i) => <span key={i} className="absolute top-1 border-l border-line2 pl-1" style={{ left: i * 5 * zoom }}>{fmtT(i * 5).replace(".0", "")}</span>)}
          </div>
          {row("V2 GRAPHICS", tracks.V2.map((it: any) => clip(it, "V2")), "h-9")}
          {row("T1 TEXT", tracks.T1.map((it: any) => clip(it, "T1")), "h-9")}
          {row("V1 SCENES", tracks.V1.map((it: any) => clip(it, "V1")), "h-16")}
          {row("SUBTITLES", tl.subtitles.map((s: any) => (
            <span key={s.id} title={s.text} className="absolute bottom-1 top-1 truncate rounded bg-[#23314a] px-1 text-[9px] leading-[18px] text-dim" style={{ left: s.start_s * zoom, width: Math.max(3, (s.end_s - s.start_s) * zoom - 1) }}>{s.text}</span>
          )), "h-7")}
          {row("VOICE", <div className="absolute bottom-1 top-1 rounded bg-[#1d3b2e]" style={{ left: 0, width: (audioTrack("voice")?.duration_s || tl.duration) * zoom }} />, "h-8")}
          {row("MUSIC", <div className={`absolute bottom-1 top-1 rounded ${audioTrack("music")?.muted ? "bg-line" : "bg-[#3a2950]"}`} style={{ left: 0, width: tl.duration * zoom }}>
            {(audioTrack("music")?.props?.sections || []).map((s: any, i: number) => <span key={i} className="absolute top-0 border-l border-white/40 pl-1 text-[9px] text-white/70" style={{ left: s[0] * zoom }}>{s[1]}</span>)}
          </div>, "h-8")}
          {row("SFX", (sfx?.props?.cues || []).map((c: any, i: number) => <span key={i} title={`${c.name}: ${c.why}`} className="absolute top-2 h-3 w-3 -translate-x-1/2 rounded-full bg-warn" style={{ left: c.t * zoom }} />), "h-8")}
          <div className="pointer-events-none absolute bottom-0 top-0 w-0.5 bg-bad" style={{ left: t * zoom }} />
          <div className="absolute inset-0 -z-0" />
        </div>
      </div>
      <Subtitles subs={tl.subtitles} onChange={() => { setDirty(true); load(); }} seek={seek} />
    </div>
  );
}

function ClipInspector({ it, proj, patch, regenerate }: { it: any; proj: any; patch: (b: any) => void; regenerate: () => void }) {
  const [p, setP] = useState<any>({ ...it.props });
  const [inS, setIn] = useState(it.in_s || 0);
  const [asset, setAsset] = useState("");
  const scene = proj?.scenes.find((s: any) => s.idx === it.scene_idx);
  const pool = [...(proj?.uploads || []).filter((a: any) => ["image", "video"].includes(a.kind)), ...(proj?.scenes || []).filter((s: any) => s.asset).map((s: any) => s.asset)];
  return (
    <div className="flex flex-col gap-2">
      <div className="font-semibold">Scene #{it.scene_idx} · {it.kind} · {fmtT(it.start_s)} for {it.duration_s.toFixed(1)}s</div>
      {scene && <p className="text-xs text-dim">{scene.narration}</p>}
      {it.props?.missing && <div className="text-xs text-bad">No visual: regenerate or pick an asset.</div>}
      <div className="grid grid-cols-2 gap-2">
        <label className="label">Camera move<select className="input py-1" value={p.motion} onChange={(e) => setP({ ...p, motion: e.target.value })}>{MOTIONS.map((x) => <option key={x}>{x}</option>)}</select></label>
        <label className="label">Look filter<select className="input py-1" value={p.filter} onChange={(e) => setP({ ...p, filter: e.target.value })}>{FILTERS.map((x) => <option key={x}>{x}</option>)}</select></label>
        <label className="label">Transition in<select className="input py-1" value={p.transition} onChange={(e) => setP({ ...p, transition: e.target.value })}>{TRANS.map((x) => <option key={x}>{x}</option>)}</select></label>
        <label className="label">Transition (s)<input className="input py-1" type="number" step={0.1} min={0.1} max={2} value={p.tdur} onChange={(e) => setP({ ...p, tdur: +e.target.value })} /></label>
        <label className="label">Focus X<input type="range" min={0} max={1} step={0.01} value={p.focus?.[0] ?? 0.5} onChange={(e) => setP({ ...p, focus: [+e.target.value, p.focus?.[1] ?? 0.45] })} /></label>
        <label className="label">Focus Y<input type="range" min={0} max={1} step={0.01} value={p.focus?.[1] ?? 0.45} onChange={(e) => setP({ ...p, focus: [p.focus?.[0] ?? 0.5, +e.target.value] })} /></label>
        {it.asset?.kind === "video" && <><label className="label">Clip in-point (s)<input className="input py-1" type="number" step={0.1} min={0} value={inS} onChange={(e) => setIn(+e.target.value)} /></label>
          <label className="label">Speed<select className="input py-1" value={p.speed} onChange={(e) => setP({ ...p, speed: +e.target.value })}>{[0.5, 0.75, 1, 1.25, 1.5, 2].map((x) => <option key={x}>{x}</option>)}</select></label></>}
      </div>
      <label className="label">Replace visual with an existing asset<select className="input py-1" value={asset} onChange={(e) => setAsset(e.target.value)}><option value="">— keep —</option>{pool.map((a: any) => <option key={a.id} value={a.id}>{a.kind}: {a.filename}</option>)}</select></label>
      <div className="flex gap-2">
        <button className="btn btn-pri btn-sm" onClick={() => patch({ props: p, in_s: inS, ...(asset ? { asset_id: asset } : {}) })}>Save clip</button>
        <button className="btn btn-sm" onClick={regenerate}>Regenerate scene</button>
      </div>
    </div>
  );
}

function OverlayInspector({ it, cat, patch, remove }: { it: any; cat: any; patch: (b: any) => void; remove: () => void }) {
  const [p, setP] = useState<any>({ ...it.props });
  const [start, setStart] = useState(it.start_s);
  const [dur, setDur] = useState(it.duration_s);
  const isText = it.kind === "text";
  return (
    <div className="flex flex-col gap-2">
      <div className="font-semibold">{isText ? "Text overlay" : `Motion graphic · ${p.type}`}</div>
      <div className="grid grid-cols-2 gap-2">
        <label className="label">Start (s)<input className="input py-1" type="number" step={0.1} value={start} onChange={(e) => setStart(+e.target.value)} /></label>
        <label className="label">Duration (s)<input className="input py-1" type="number" step={0.1} value={dur} onChange={(e) => setDur(+e.target.value)} /></label>
      </div>
      {isText ? (
        <div className="grid grid-cols-2 gap-2">
          <label className="label col-span-2">Text<input className="input py-1" value={p.text || ""} onChange={(e) => setP({ ...p, text: e.target.value })} /></label>
          <label className="label">Size<input className="input py-1" type="number" value={p.size || 72} onChange={(e) => setP({ ...p, size: +e.target.value })} /></label>
          <label className="label">Colour<input className="input h-9 py-1" type="color" value={p.color || "#ffffff"} onChange={(e) => setP({ ...p, color: e.target.value })} /></label>
          <label className="label">Animation<select className="input py-1" value={p.anim || "pop"} onChange={(e) => setP({ ...p, anim: e.target.value })}>{["pop", "rise", "type", "none"].map((x) => <option key={x}>{x}</option>)}</select></label>
          <label className="label">Align<select className="input py-1" value={p.align || "center"} onChange={(e) => setP({ ...p, align: e.target.value })}>{["left", "center", "right"].map((x) => <option key={x}>{x}</option>)}</select></label>
          <label className="label">X<input type="range" min={0} max={1} step={0.01} value={p.x ?? 0.5} onChange={(e) => setP({ ...p, x: +e.target.value })} /></label>
          <label className="label">Y<input type="range" min={0} max={1} step={0.01} value={p.y ?? 0.2} onChange={(e) => setP({ ...p, y: +e.target.value })} /></label>
        </div>
      ) : (
        <label className="label">Graphic data (JSON)<textarea className="input min-h-[140px] font-mono text-xs" defaultValue={JSON.stringify(p, null, 1)} onBlur={(e) => { try { setP(JSON.parse(e.target.value)); } catch { toast("Invalid JSON", "bad"); } }} /></label>
      )}
      <div className="flex gap-2">
        <button className="btn btn-pri btn-sm" onClick={() => patch({ props: p, start_s: start, duration_s: dur })}>Save</button>
        <button className="btn btn-sm btn-bad" onClick={remove}>Delete</button>
      </div>
    </div>
  );
}

function Subtitles({ subs, onChange, seek }: { subs: any[]; onChange: () => void; seek: (t: number) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card p-3">
      <button className="text-sm font-semibold" onClick={() => setOpen(!open)}>{open ? "▾" : "▸"} Subtitles ({subs.length}, synced from word timings)</button>
      {open && (
        <div className="mt-2 flex max-h-80 flex-col gap-1 overflow-auto">
          {subs.map((s) => (
            <div key={s.id} className="flex items-center gap-2 text-xs">
              <button className="tabnum w-28 shrink-0 text-left text-dim hover:text-acc" onClick={() => seek(s.start_s)}>{fmtT(s.start_s)}–{fmtT(s.end_s)}</button>
              <input className="input py-1 text-xs" defaultValue={s.text} onBlur={(e) => e.target.value !== s.text && api(`/subtitles/${s.id}`, { method: "PATCH", body: { text: e.target.value } }).then(onChange)} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
