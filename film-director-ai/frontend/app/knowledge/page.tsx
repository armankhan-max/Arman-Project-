"use client";
import { useState } from "react";
import { ago, api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Empty, toast, useBusy } from "@/components/ui";

export default function Knowledge() {
  const { data, reload } = useApi<any[]>("/knowledge");
  const [q, setQ] = useState("");
  const [res, setRes] = useState<any[] | null>(null);
  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const { busy, run } = useBusy();
  return (
    <div className="flex flex-col gap-4">
      <div><h1 className="h1">Knowledge</h1><p className="text-sm text-dim">Everything the agents can retrieve: research, scripts, your documents, YouTube reports. Each item keeps its source, trust level and retrieval date. Retrieved text is treated as data, never as instructions.</p></div>
      <div className="card flex gap-2"><input className="input flex-1" placeholder="Search the knowledge base…" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && run("s", async () => setRes(await api(`/knowledge/search?q=${encodeURIComponent(q)}`)))} />
        <button className="btn" onClick={() => run("s", async () => setRes(await api(`/knowledge/search?q=${encodeURIComponent(q)}`)))}>Search</button></div>
      {res && <div className="flex flex-col gap-2">{res.length === 0 && <Empty>No matches.</Empty>}{res.map((r, i) => (
        <div key={i} className="card text-sm"><div className="text-xs text-dim">[{i + 1}] {r.title} · <b>{r.trust}</b> · {r.source_type} · score {r.score} · retrieved {ago(r.retrieved_at)} {r.source_url && <a className="text-acc" href={r.source_url} target="_blank" rel="noreferrer">source</a>}</div><p className="mt-1 line-clamp-4 text-dim">{r.text}</p></div>
      ))}</div>}
      <div className="card grid gap-2">
        <b className="text-sm">Add knowledge</b>
        <input className="input" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <textarea className="input min-h-[90px]" placeholder="Paste notes, facts, a brief…" value={text} onChange={(e) => setText(e.target.value)} />
        <div className="flex flex-wrap items-center gap-2">
          <button className="btn btn-pri" disabled={!text || !!busy} onClick={() => run("a", async () => { const fd = new FormData(); fd.append("text", text); fd.append("title", title); const r = await api("/knowledge", { form: fd }); toast(r.new ? `Indexed in ${r.chunks} chunks` : "Already in the knowledge base"); setText(""); reload(); })}>Add text</button>
          <label className="btn cursor-pointer">Upload document (PDF, DOCX, TXT, MD)<input type="file" className="hidden" accept=".pdf,.docx,.txt,.md,.srt,.vtt" onChange={(e) => { const f = e.target.files?.[0]; if (f) run("u", async () => { const fd = new FormData(); fd.append("file", f); await api("/knowledge", { form: fd }); toast("Document indexed"); reload(); }); }} /></label>
          <button className="btn btn-ghost ml-auto" onClick={() => run("r", async () => { const r = await api("/knowledge/reindex", { method: "POST" }); toast(`Re-indexed ${r.chunks} chunks`); })}>Re-index all</button>
        </div>
      </div>
      <div className="card divide-y divide-line p-0">
        {data?.length === 0 && <div className="p-4"><Empty>Empty.</Empty></div>}
        {data?.map((d) => (
          <div key={d.id} className="flex items-center gap-3 px-4 py-2 text-sm"><span className="tag">{d.trust}</span><span className="tag">{d.source_type}</span><span className="flex-1 truncate">{d.title}</span>
            <span className="text-xs text-dim">{d.chunks} chunks · {ago(d.retrieved_at)}{d.expires_at ? ` · expires ${ago(d.expires_at)}` : ""}</span>
            <button className="btn btn-ghost btn-sm btn-bad" onClick={() => confirm("Delete this document from the knowledge base?") && run("d", async () => { await api(`/knowledge/${d.id}`, { method: "DELETE" }); reload(); })}>Delete</button></div>
        ))}
      </div>
    </div>
  );
}
