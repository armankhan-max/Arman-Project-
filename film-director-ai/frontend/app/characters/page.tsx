"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Empty, toast, useBusy } from "@/components/ui";

const BLANK = { name: "", persona: { look: "", set: "", age: 65, one_liner: "", sign_off: "", bible: "" }, voice: "", voice_rate: -8, voice_pitch: -6 };

export default function Characters() {
  const { data, reload } = useApi<any[]>("/characters");
  const [ed, setEd] = useState<any>(null);
  const [topic, setTopic] = useState("");
  const [bible, setBible] = useState("");
  const [voices, setVoices] = useState<any[]>([]);
  const { busy, run } = useBusy();
  useEffect(() => { api("/voices?lang=en").then(setVoices).catch(() => {}); }, []);
  const P = (k: string, v: any) => setEd({ ...ed, persona: { ...ed.persona, [k]: v } });
  const save = (extra: any = {}) => run("save", async () => {
    if (!ed.name.trim()) throw new Error("Give the character a name");
    const c = await api("/characters", { body: { ...ed, ...extra } });
    toast("Character saved"); setEd(c); reload();
  });
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div><h1 className="h1">Characters</h1><p className="text-sm text-dim">Saved AI hosts. Each keeps a persona, one face and one voice, so every future video shows the same person. Pick a character when you create an AI avatar video.</p></div>
        <button className="btn btn-pri" onClick={() => setEd({ ...BLANK, persona: { ...BLANK.persona } })}>New character</button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {data?.length === 0 && !ed && <Empty>No characters yet.</Empty>}
        {data?.map((c) => (
          <div key={c.id} className="card flex flex-col gap-2 p-3">
            <div className="aspect-video overflow-hidden rounded-lg bg-panel2">{c.image_url ? <img src={c.image_url + "?v=" + c.updated_at} alt="" className="h-full w-full object-cover" /> : <div className="grid h-full place-items-center text-xs text-dim">No face yet</div>}</div>
            <b>{c.name}</b>
            <div className="line-clamp-2 text-xs text-dim">{c.persona?.one_liner || c.persona?.look}</div>
            <div className="text-xs text-mute">Voice: {c.voice || "not set"}{c.lipsync_ready ? " · lip-sync ready" : ""}</div>
            <div className="mt-auto flex gap-2"><button className="btn btn-sm" onClick={() => setEd(c)}>Edit</button>
              <a className="btn btn-sm btn-pri" href={`/projects/?new=1&character=${c.id}`}>Make a video</a>
              <button className="btn btn-sm btn-ghost btn-bad ml-auto" onClick={() => confirm(`Delete ${c.name}?`) && run("d", async () => { await api(`/characters/${c.id}`, { method: "DELETE" }); reload(); })}>Delete</button></div>
          </div>
        ))}
      </div>
      {ed && (
        <div className="card grid gap-3 md:grid-cols-2">
          <div className="flex flex-col gap-3 md:col-span-2">
            <b>{ed.id ? "Edit character" : "New character"}</b>
            {!ed.id && (
              <div className="grid gap-2 rounded-lg border border-line p-3 md:grid-cols-[1fr_1fr_auto]">
                <input className="input" placeholder="Channel topic, e.g. old-fashioned cleaning tricks" value={topic} onChange={(e) => setTopic(e.target.value)} />
                <textarea className="input min-h-[42px]" placeholder="…or paste your Persona Bible" value={bible} onChange={(e) => setBible(e.target.value)} />
                <button className="btn" disabled={!!busy || (!topic && !bible)} onClick={() => run("design", async () => { const p = await api("/characters/design", { body: { topic, bible } }); setEd({ ...ed, name: p.name, persona: p }); })}>{busy === "design" ? "Designing…" : "Design with AI"}</button>
              </div>
            )}
          </div>
          <label className="label">Name<input className="input" value={ed.name} onChange={(e) => setEd({ ...ed, name: e.target.value })} /></label>
          <label className="label">Age<input className="input" type="number" value={ed.persona.age || 65} onChange={(e) => P("age", +e.target.value)} /></label>
          <label className="label md:col-span-2">Who they are (one line)<input className="input" value={ed.persona.one_liner || ""} onChange={(e) => P("one_liner", e.target.value)} /></label>
          <label className="label">Look: face, hair, glasses, clothing, signature colour<textarea className="input min-h-[80px]" value={ed.persona.look || ""} onChange={(e) => P("look", e.target.value)} /></label>
          <label className="label">Filming set<textarea className="input min-h-[80px]" value={ed.persona.set || ""} onChange={(e) => P("set", e.target.value)} /></label>
          <label className="label md:col-span-2">Persona Bible (voice, recurring people, phrases, things they never say)<textarea className="input min-h-[110px]" value={ed.persona.bible || ""} onChange={(e) => P("bible", e.target.value)} /></label>
          <label className="label">Sign-off line<input className="input" value={ed.persona.sign_off || ""} onChange={(e) => P("sign_off", e.target.value)} /></label>
          <label className="label">Voice<select className="input" value={ed.voice || ""} onChange={(e) => setEd({ ...ed, voice: e.target.value })}><option value="">Project default</option>{voices.map((v) => <option key={v.id} value={v.id}>{v.name} · {v.locale} · {v.gender}</option>)}</select></label>
          <label className="label">Voice speed ({ed.voice_rate}%)<input type="range" min={-25} max={15} value={ed.voice_rate} onChange={(e) => setEd({ ...ed, voice_rate: +e.target.value })} /></label>
          <label className="label">Voice pitch ({ed.voice_pitch} Hz)<input type="range" min={-25} max={20} value={ed.voice_pitch} onChange={(e) => setEd({ ...ed, voice_pitch: +e.target.value })} /></label>
          <div className="md:col-span-2">
            {ed.image_url && <img src={ed.image_url + "?v=" + ed.updated_at} alt="" className="mb-2 max-h-72 rounded-lg" />}
            <div className="flex flex-wrap gap-2">
              <button className="btn btn-pri" disabled={!!busy} onClick={() => save()}>{busy === "save" ? "Saving…" : ed.id ? "Save" : "Save and generate face"}</button>
              {ed.id && <button className="btn" disabled={!!busy} onClick={() => save({ generate_portrait: true, seed: Math.floor(Math.random() * 90000) })}>Generate a new face</button>}
              {ed.id && <label className="btn cursor-pointer">Upload my own face image<input type="file" accept="image/*" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) run("up", async () => { const fd = new FormData(); fd.append("file", f); setEd(await api(`/characters/${ed.id}/image`, { form: fd })); reload(); }); }} /></label>}
              <button className="btn btn-ghost" onClick={() => setEd(null)}>Close</button>
            </div>
            <p className="mt-2 text-xs text-mute">The face is used for every on-camera scene and for thumbnails. With a HeyGen key (Settings → Providers) on-camera scenes are true lip-synced video; without one the built-in talking photo is used, which only approximates mouth movement. Only use faces you have the right to use.</p>
          </div>
        </div>
      )}
    </div>
  );
}
