"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Empty, useBusy } from "@/components/ui";

export default function Stock() {
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("video");
  const [res, setRes] = useState<any>(null);
  const [open, setOpen] = useState<any>(null);
  const { busy, run } = useBusy();
  const search = () => run("s", async () => setRes(await api(`/media/search?kind=${kind}&q=${encodeURIComponent(q)}`)));
  return (
    <div className="flex flex-col gap-4">
      <div><h1 className="h1">Stock footage library</h1><p className="text-sm text-dim">Search every connected source at once: Pexels, Pixabay, Wikimedia Commons, NASA, Openverse and Internet Archive public-domain film. Only licences that allow reuse are shown, with attribution. To put a clip in a video, open the project → Editor → select a clip → “Find stock footage”.</p></div>
      <div className="card flex flex-wrap gap-2">
        <div className="flex gap-1">{[["video", "Videos"], ["image", "Photos"], ["archive", "Archive & history"]].map(([k, l]) => <button key={k} className={`btn btn-sm ${kind === k ? "btn-pri" : ""}`} onClick={() => setKind(k)}>{l}</button>)}</div>
        <input className="input min-w-[200px] flex-1" placeholder="Search, e.g. ocean waves at sunset, Jupiter, 1940s newsreel" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && q.trim() && search()} />
        <button className="btn btn-pri" disabled={!!busy || !q.trim()} onClick={search}>{busy ? "Searching…" : "Search"}</button>
      </div>
      {res?.add_keys_for_more?.length > 0 && <div className="rounded-lg border border-info/30 bg-info/10 px-3 py-2 text-sm text-info">Add free API keys for {res.add_keys_for_more.join(" and ")} in Settings → Providers to search millions more clips.</div>}
      {res?.errors?.length > 0 && <div className="text-xs text-warn">{res.errors.join(" · ")}</div>}
      {res && (res.results.length === 0 ? <Empty>No results. Try simpler words.</Empty> : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{res.results.map((r: any) => (
          <button key={r.key} className="card overflow-hidden p-0 text-left" onClick={() => setOpen(r)}>
            <div className="aspect-video bg-panel2">{r.thumb && <img src={r.thumb} alt="" className="h-full w-full object-cover" loading="lazy" />}</div>
            <div className="p-2 text-xs"><div className="truncate font-semibold">{r.title || "Untitled"}</div><div className="text-dim">{r.kind === "video" ? "▶ video" : "photo"} · {r.provider}{r.duration ? ` · ${Math.round(r.duration)}s` : ""}{r.width ? ` · ${r.width}×${r.height}` : ""}</div><div className="truncate text-mute">{r.license}</div></div>
          </button>))}</div>))}
      {open && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/75 p-4" onClick={(e) => e.target === e.currentTarget && setOpen(null)}>
          <div className="card w-full max-w-3xl">
            {open.thumb && <img src={open.thumb} alt="" className="max-h-[60vh] w-full rounded-lg object-contain" />}
            <div className="mt-2 text-sm"><b>{open.title}</b><div className="text-dim">{open.provider} · {open.license}</div><div className="text-xs text-mute">{open.attribution}</div>
              {open.source_page && <a className="text-acc" href={open.source_page} target="_blank" rel="noreferrer">Open source page</a>}</div>
            <button className="btn btn-sm mt-3" onClick={() => setOpen(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
