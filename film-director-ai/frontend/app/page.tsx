"use client";
import Link from "next/link";
import { ago, usd } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import RunMonitor from "@/components/RunMonitor";
import { Empty, ErrorBox, Status, useInterval } from "@/components/ui";

export default function Dashboard() {
  const { data, error, reload } = useApi<any>("/dashboard");
  useInterval(reload, 8000);
  if (error) return <ErrorBox e={error} />;
  if (!data) return <div className="text-dim">Loading…</div>;
  const b = data.budget;
  const prov = data.providers as any[];
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="h1">Dashboard</h1><p className="text-sm text-dim">Your production company at a glance.</p></div>
        <div className="flex gap-2"><Link className="btn" href="/projects?new=1">New project</Link><Link className="btn btn-pri" href="/chat">Talk to the Director</Link></div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card"><div className="text-xs text-dim">Active jobs</div><div className="text-2xl font-bold">{data.active.length}</div></div>
        <div className="card"><div className="text-xs text-dim">Spent today / limit</div><div className="text-2xl font-bold tabnum">{usd(b.daily.spent)} <span className="text-sm text-dim">/ {b.daily.limit == null ? "no limit set" : usd(b.daily.limit)}</span></div></div>
        <div className="card"><div className="text-xs text-dim">This month</div><div className="text-2xl font-bold tabnum">{usd(b.monthly.spent)} <span className="text-sm text-dim">/ {b.monthly.limit == null ? "—" : usd(b.monthly.limit)}</span></div></div>
        <div className="card"><div className="text-xs text-dim">YouTube channel</div><div className="mt-1"><Status s={data.youtube.connected ? "connected" : "unconfigured"} /></div><div className="mt-1 text-xs text-mute">Workers: {data.workers.celery ? "Celery" : "in-process"}</div></div>
      </div>
      <section>
        <h2 className="h2 mb-2">Active production</h2>
        {data.active.length === 0 ? <Empty>No jobs running.</Empty> : data.active.map((r: any) => (
          <div key={r.id} className="card mb-3">
            <div className="mb-2 flex items-center justify-between"><Link href={`/projects/${r.project_id}`} className="font-semibold hover:text-acc">{r.project_title}</Link><span className="text-xs text-dim">{r.kind} · started {ago(r.started_at)}</span></div>
            <RunMonitor runId={r.id} compact onEnd={reload} />
          </div>
        ))}
      </section>
      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="h2 mb-2">Recent projects</h2>
          <div className="flex flex-col gap-1">
            {data.projects.length === 0 && <Empty>No projects yet. Ask the Director to make your first video.</Empty>}
            {data.projects.map((p: any) => (
              <Link key={p.id} href={`/projects/${p.id}`} className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-panel">
                <div><div className="font-medium">{p.title}</div><div className="text-xs text-dim">{p.mode} · v{p.current_version} · {ago(p.updated_at)}</div></div><Status s={p.status} />
              </Link>
            ))}
          </div>
        </section>
        <section>
          <h2 className="h2 mb-2">Completed renders</h2>
          <div className="flex flex-col gap-1">
            {data.renders.length === 0 && <Empty>No renders yet.</Empty>}
            {data.renders.map((r: any) => (
              <Link key={r.id} href={`/projects/${r.project_id}?tab=renders`} className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-panel">
                <div><div className="font-medium">{r.project_title}</div><div className="text-xs text-dim">{r.kind} · v{r.project_version} · {r.settings?.width}×{r.settings?.height} · {ago(r.created_at)}</div></div>
                <Status s={r.verified ? "passed" : r.status} />
              </Link>
            ))}
          </div>
        </section>
      </div>
      {data.failed_tasks.length > 0 && (
        <section>
          <h2 className="h2 mb-2">Recent failures</h2>
          <div className="card divide-y divide-line p-0">
            {data.failed_tasks.map((t: any) => (
              <div key={t.id} className="px-4 py-2 text-sm"><b>{t.project_title}</b> · <span className="font-mono text-xs">{t.key}</span><div className="text-xs text-bad">{(t.error || "").slice(0, 240)}</div></div>
            ))}
          </div>
        </section>
      )}
      <section>
        <div className="mb-2 flex items-center justify-between"><h2 className="h2">Providers</h2><Link href="/settings" className="text-xs text-acc">Configure →</Link></div>
        <div className="flex flex-wrap gap-2">
          {prov.map((p) => <span key={p.name} className="flex items-center gap-1.5 rounded-lg border border-line bg-panel px-2.5 py-1.5 text-xs">{p.label} <Status s={p.status} /></span>)}
        </div>
      </section>
    </div>
  );
}
