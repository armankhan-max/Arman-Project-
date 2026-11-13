"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Bar, Status } from "./ui";

type Task = { key: string; status: string; progress: number; message: string; error?: string | null };
type Log = { id: number; task: string | null; level: string; message: string; at: string };

/** Live view of one workflow run. Polls the run (works through any proxy); events are fetched incrementally. */
export default function RunMonitor({ runId, onEnd, compact = false }: { runId: string; onEnd?: () => void; compact?: boolean }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [status, setStatus] = useState("…");
  const [logs, setLogs] = useState<Log[]>([]);
  const last = useRef(0);
  const ended = useRef(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let stop = false;
    last.current = 0;
    ended.current = false;
    setLogs([]);
    const tick = async () => {
      try {
        const d = await api(`/runs/${runId}?after=${last.current}`);
        if (stop) return;
        setStatus(d.status);
        setTasks(d.tasks);
        if (d.events?.length) {
          last.current = d.events[d.events.length - 1].id;
          setLogs((l) => [...l, ...d.events].slice(-400));
        }
        if (["succeeded", "failed", "cancelled"].includes(d.status)) {
          if (!ended.current) { ended.current = true; onEnd?.(); }
          return;
        }
      } catch {}
      if (!stop) setTimeout(tick, 2500);
    };
    tick();
    return () => { stop = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);
  useEffect(() => { box.current?.scrollTo(0, box.current.scrollHeight); }, [logs.length]);
  const isVis = (k: string) => /visual:/.test(k);
  const main = tasks.filter((t) => !isVis(t.key));
  const vis = tasks.filter((t) => isVis(t.key));
  const done = (t: Task) => ["succeeded", "skipped"].includes(t.status);
  const overall = tasks.length ? tasks.reduce((a, t) => a + (done(t) ? 1 : t.progress || 0), 0) / tasks.length : 0;
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <Status s={status} />
        <Bar v={overall} className="flex-1" />
        <span className="tabnum text-xs text-dim">{Math.round(overall * 100)}%</span>
        {["running", "pending"].includes(status) && <button className="btn btn-sm btn-bad" onClick={() => api(`/runs/${runId}/cancel`, { method: "POST" })}>Cancel</button>}
        {["failed", "cancelled"].includes(status) && <button className="btn btn-sm" onClick={() => api(`/runs/${runId}/resume`, { method: "POST" }).then(() => location.reload())}>Resume from checkpoint</button>}
      </div>
      <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 lg:grid-cols-5">
        {main.map((t) => (
          <div key={t.key} className="rounded-lg border border-line bg-panel2 px-2.5 py-2" title={t.error || t.message}>
            <div className="flex items-center justify-between gap-1"><span className="truncate text-xs font-semibold">{t.key}</span><Status s={t.status} /></div>
            {t.status === "running" && <Bar v={t.progress} className="mt-1.5" />}
            {t.status === "running" && t.message && <div className="mt-1 truncate text-[11px] text-dim">{t.message}</div>}
            {t.status === "failed" && t.error && <div className="mt-1 line-clamp-2 text-[11px] text-bad">{t.error}</div>}
          </div>
        ))}
      </div>
      {vis.length > 0 && (
        <div>
          <div className="mb-1 text-xs text-dim">Scene visuals: {vis.filter(done).length}/{vis.length} ready{vis.some((t) => t.status === "failed") ? ", some failed" : ""}
            {vis.filter((t) => t.status === "running" && t.message).slice(0, 2).map((t) => <span key={t.key} className="ml-2 text-mute">· {t.message}</span>)}</div>
          <div className="flex flex-wrap gap-1">
            {vis.map((t) => <span key={t.key} title={`${t.key} ${t.status} ${t.message || ""}`} className={`h-3 w-3 rounded-sm ${done(t) ? "bg-ok" : t.status === "running" ? "animate-pulse bg-info" : t.status === "failed" ? "bg-bad" : "bg-line2"}`} />)}
          </div>
        </div>
      )}
      {!compact && (
        <div ref={box} className="max-h-56 overflow-auto rounded-lg border border-line bg-[#0c0d11] p-2 font-mono text-[11.5px]">
          {logs.length === 0 && <div className="text-mute">Waiting for events…</div>}
          {logs.map((l) => (
            <div key={l.id} className={l.level === "error" ? "text-bad" : l.level === "warn" ? "text-warn" : "text-dim"}>
              <span className="text-mute">{new Date(l.at).toLocaleTimeString()}</span> {l.task ? <b className="text-ink">[{l.task}]</b> : null} {l.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
