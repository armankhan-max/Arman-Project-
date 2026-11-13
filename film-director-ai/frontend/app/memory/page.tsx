"use client";
import { useState } from "react";
import { ago, api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Empty, Tabs, toast, useBusy } from "@/components/ui";

const CATS: [string, string][] = [["preference", "Creative preferences"], ["channel", "Channel"], ["project", "Projects"], ["production", "Production"], ["performance", "Performance"]];

export default function Memory() {
  const [cat, setCat] = useState("preference");
  const [hist, setHist] = useState(false);
  const { data, reload } = useApi<any[]>(`/memory?category=${cat}&include_superseded=${hist ? 1 : 0}`, [cat, hist]);
  const [key, setKey] = useState("");
  const [content, setContent] = useState("");
  const { busy, run } = useBusy();
  return (
    <div className="flex flex-col gap-4">
      <div><h1 className="h1">Memory & preferences</h1><p className="text-sm text-dim">What the Director remembers. Confirmed entries are never overwritten silently: a change creates a new entry and keeps the old one as history. Inferred entries can be confirmed or deleted. Secrets are refused.</p></div>
      <Tabs tabs={CATS} value={cat} onChange={setCat} />
      <div className="card grid gap-2 md:grid-cols-[200px_1fr_auto]">
        <input className="input" placeholder="Key (e.g. camera_style)" value={key} onChange={(e) => setKey(e.target.value)} />
        <input className="input" placeholder="Content (e.g. Prefer slow push-ins and minimal transitions)" value={content} onChange={(e) => setContent(e.target.value)} />
        <button className="btn btn-pri" disabled={!content || !!busy} onClick={() => run("a", async () => { await api("/memory", { body: { category: cat, key: key || content.slice(0, 40), content } }); setKey(""); setContent(""); toast("Saved"); reload(); })}>Save</button>
      </div>
      <label className="flex items-center gap-2 text-xs text-dim"><input type="checkbox" checked={hist} onChange={(e) => setHist(e.target.checked)} /> Show superseded history</label>
      <div className="flex flex-col gap-2">
        {data?.length === 0 && <Empty>Nothing stored in this category.</Empty>}
        {data?.map((m) => (
          <div key={m.id} className={`card flex items-start gap-3 text-sm ${m.status === "superseded" ? "opacity-50" : ""}`}>
            <div className="flex-1"><div className="flex items-center gap-2"><b>{m.key}</b><span className={`tag ${m.status === "confirmed" ? "text-ok" : m.status === "inferred" ? "text-warn" : ""}`}>{m.status}</span><span className="text-xs text-mute">{m.source} · {ago(m.updated_at)}</span></div>
              <p className="mt-1 whitespace-pre-wrap text-dim">{m.content}</p></div>
            {m.status === "inferred" && <button className="btn btn-sm" onClick={() => run("c", async () => { await api(`/memory/${m.id}/confirm`, { method: "POST" }); reload(); })}>Confirm</button>}
            <button className="btn btn-sm btn-ghost btn-bad" onClick={() => run("d", async () => { await api(`/memory/${m.id}`, { method: "DELETE" }); reload(); })}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}
