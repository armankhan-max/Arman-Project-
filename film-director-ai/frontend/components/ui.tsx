"use client";
import { useEffect, useRef, useState } from "react";

export function Status({ s }: { s?: string | null }) {
  const c: Record<string, string> = {
    succeeded: "text-ok border-ok/30", ready: "text-ok border-ok/30", ok: "text-ok border-ok/30", passed: "text-ok border-ok/30", connected: "text-ok border-ok/30",
    running: "text-info border-info/30", producing: "text-info border-info/30", queued: "text-info border-info/30", generating: "text-info border-info/30",
    failed: "text-bad border-bad/30", invalid: "text-bad border-bad/30", error: "text-bad border-bad/30", needs_attention: "text-warn border-warn/30",
    cancelled: "text-mute", skipped: "text-mute", pending: "text-mute", unconfigured: "text-mute", draft: "text-dim",
  };
  return <span className={`tag ${c[s || ""] || ""}`}>{(s || "—").replace(/_/g, " ")}</span>;
}

export function Bar({ v, className = "" }: { v: number; className?: string }) {
  return (
    <div className={`h-1.5 overflow-hidden rounded bg-line ${className}`}>
      <div className="h-full bg-acc transition-all" style={{ width: `${Math.round(Math.max(0, Math.min(1, v)) * 100)}%` }} />
    </div>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-dashed border-line2 p-8 text-center text-sm text-dim">{children}</div>;
}

export function ErrorBox({ e }: { e?: string | null }) {
  if (!e) return null;
  return <div className="rounded-lg border border-bad/40 bg-bad/10 px-3 py-2 text-sm text-bad">{e}</div>;
}

let toastSet: ((t: { msg: string; kind: string }[]) => void) | null = null;
let toasts: { msg: string; kind: string }[] = [];
export function toast(msg: string, kind = "") {
  toasts = [...toasts, { msg, kind }];
  toastSet?.(toasts);
  setTimeout(() => { toasts = toasts.slice(1); toastSet?.(toasts); }, kind === "bad" ? 7000 : 3500);
}
export function Toasts() {
  const [t, set] = useState(toasts);
  useEffect(() => { toastSet = set; return () => { toastSet = null; }; }, []);
  return (
    <div className="fixed bottom-20 right-4 z-50 flex flex-col gap-2 md:bottom-4">
      {t.map((x, i) => (
        <div key={i} className={`max-w-sm rounded-lg border border-line2 bg-panel2 px-3 py-2 text-sm shadow-xl ${x.kind === "bad" ? "border-l-4 border-l-bad" : "border-l-4 border-l-acc"}`}>{x.msg}</div>
      ))}
    </div>
  );
}

export function useBusy() {
  const [busy, setBusy] = useState<string | null>(null);
  const run = async (key: string, fn: () => Promise<any>) => {
    setBusy(key);
    try { return await fn(); } catch (e: any) { toast(e.message, "bad"); } finally { setBusy(null); }
  };
  return { busy, run };
}

export function Tabs({ tabs, value, onChange }: { tabs: [string, string][]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex gap-1 overflow-x-auto border-b border-line">
      {tabs.map(([k, l]) => (
        <button key={k} onClick={() => onChange(k)} className={`whitespace-nowrap border-b-2 px-3 py-2.5 text-sm font-semibold ${value === k ? "border-acc text-ink" : "border-transparent text-dim hover:text-ink"}`}>{l}</button>
      ))}
    </div>
  );
}

export function useInterval(fn: () => void, ms: number | null) {
  const ref = useRef(fn);
  ref.current = fn;
  useEffect(() => {
    if (ms == null) return;
    const id = setInterval(() => ref.current(), ms);
    return () => clearInterval(id);
  }, [ms]);
}
