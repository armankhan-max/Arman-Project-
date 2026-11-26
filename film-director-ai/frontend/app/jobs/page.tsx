"use client";
import Link from "next/link";
import { ago, api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Bar, Empty, Status, toast, useInterval } from "@/components/ui";

export default function Jobs() {
  const { data, reload } = useApi<any[]>("/runs?limit=80");
  useInterval(reload, 4000);
  const act = (data || []).filter((r) => ["pending", "running"].includes(r.status));
  return (
    <div className="flex flex-col gap-4">
      <div><h1 className="h1">Job queue</h1><p className="text-sm text-dim">Everything the studio is producing, across all projects. Jobs keep running when you close the browser; renders take turns.</p></div>
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="card"><div className="text-xs text-dim">Running or queued</div><div className="text-2xl font-bold">{act.length}</div></div>
        <div className="card"><div className="text-xs text-dim">Finished (shown)</div><div className="text-2xl font-bold">{(data || []).filter((r) => r.status === "succeeded").length}</div></div>
        <div className="card"><div className="text-xs text-dim">Failed (shown)</div><div className="text-2xl font-bold text-bad">{(data || []).filter((r) => r.status === "failed").length}</div></div>
      </div>
      {data?.length === 0 && <Empty>No jobs yet.</Empty>}
      <div className="flex flex-col gap-2">
        {data?.map((r) => (
          <div key={r.id} className="card flex flex-wrap items-center gap-3 py-3">
            <Status s={r.status} />
            <div className="min-w-0 flex-1">
              <Link href={`/project/?id=${r.project_id}&tab=jobs`} className="font-semibold hover:text-acc">{r.project_title || "Project"}</Link>
              <div className="truncate text-xs text-dim">{r.kind} · {r.done}/{r.tasks} steps · started {ago(r.created_at)}{r.current ? ` · ${r.current}` : ""}</div>
              {r.error && <div className="truncate text-xs text-bad">{r.error}</div>}
            </div>
            <div className="w-40"><Bar v={r.status === "succeeded" ? 1 : r.progress} /></div>
            {["pending", "running"].includes(r.status) && <button className="btn btn-sm btn-bad" onClick={() => api(`/runs/${r.id}/cancel`, { method: "POST" }).then(() => { toast("Cancelling"); reload(); })}>Cancel</button>}
            {["failed", "cancelled"].includes(r.status) && <button className="btn btn-sm" onClick={() => api(`/runs/${r.id}/resume`, { method: "POST" }).then(() => { toast("Resumed"); reload(); })}>Resume</button>}
          </div>
        ))}
      </div>
    </div>
  );
}
