"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Tabs, toast, useBusy } from "@/components/ui";

export default function Tools() {
  const [tab, setTab] = useState("titles");
  return (
    <div className="flex flex-col gap-4">
      <div><h1 className="h1">Creator tools</h1><p className="text-sm text-dim">Find ideas and titles, then turn any of them into a video in one click.</p></div>
      <Tabs tabs={[["titles", "Title lab"], ["ideas", "Idea lab"]]} value={tab} onChange={setTab} />
      {tab === "titles" ? <TitleLab /> : <IdeaLab />}
    </div>
  );
}

const make = (title: string, brief = "", mode = "documentary") => { location.href = `/projects/?new=1&title=${encodeURIComponent(title)}&brief=${encodeURIComponent(brief)}&mode=${mode}`; };

function TitleLab() {
  const [f, setF] = useState({ topic: "", mode: "documentary", language: "en", n: 12 });
  const [out, setOut] = useState<any[]>([]);
  const { busy, run } = useBusy();
  return (
    <div className="flex flex-col gap-3">
      <div className="card grid gap-3 md:grid-cols-[1fr_180px_160px_auto]">
        <input className="input" placeholder="Topic, e.g. the submarine sunk an hour before Pearl Harbor" value={f.topic} onChange={(e) => setF({ ...f, topic: e.target.value })} />
        <select className="input" value={f.mode} onChange={(e) => setF({ ...f, mode: e.target.value })}>{["documentary", "historical", "science", "avatar", "faceless", "educational", "short"].map((x) => <option key={x}>{x}</option>)}</select>
        <select className="input" value={f.language} onChange={(e) => setF({ ...f, language: e.target.value })}><option value="en">English</option><option value="hi">Hindi</option><option value="hinglish">Hinglish</option></select>
        <button className="btn btn-pri" disabled={!!busy || !f.topic.trim()} onClick={() => run("t", async () => setOut((await api("/tools/titles", { body: f })).titles))}>{busy ? "Thinking…" : "Generate titles"}</button>
      </div>
      {out.map((t, i) => (
        <div key={i} className="card flex flex-wrap items-center gap-3">
          <div className="min-w-0 flex-1"><b className="text-base">{t.title}</b><div className="text-xs text-dim">{t.angle} · {t.title.length} characters</div></div>
          <span className="tabnum text-xl font-bold">{t.score}</span>
          <button className="btn btn-sm" onClick={() => navigator.clipboard?.writeText(t.title).then(() => toast("Copied"))}>Copy</button>
          <button className="btn btn-sm btn-pri" onClick={() => make(t.title, "", f.mode)}>Make this video</button>
        </div>
      ))}
    </div>
  );
}

function IdeaLab() {
  const [niche, setNiche] = useState("");
  const [out, setOut] = useState<any[]>([]);
  const { busy, run } = useBusy();
  return (
    <div className="flex flex-col gap-3">
      <div className="card flex flex-col gap-2 md:flex-row">
        <textarea className="input min-h-[60px] flex-1" placeholder="Describe your channel: who watches, what it covers, the style. e.g. 'Mysteries of WW2 told as cinematic documentaries for adults 35+'" value={niche} onChange={(e) => setNiche(e.target.value)} />
        <button className="btn btn-pri" disabled={!!busy || !niche.trim()} onClick={() => run("i", async () => setOut((await api("/tools/ideas", { body: { niche } })).ideas))}>{busy ? "Researching…" : "Get 10 ideas"}</button>
      </div>
      {out.map((x, i) => (
        <div key={i} className="card flex flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2"><span className="tag">{x.format}</span><b>{i + 1}. {x.title}</b></div>
          <div className="text-sm text-dim">{x.why}</div>
          <div className="text-sm"><b>Hook:</b> {x.hook}</div>
          {x.thumbnail_text && <div className="text-xs text-mute">Thumbnail text: {x.thumbnail_text}</div>}
          <div className="mt-1 flex gap-2"><button className="btn btn-sm btn-pri" onClick={() => make(x.title, `${x.hook} Format: ${x.format}.`)}>Make this video</button></div>
        </div>
      ))}
    </div>
  );
}
