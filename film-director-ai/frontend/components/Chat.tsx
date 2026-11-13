"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import RunMonitor from "./RunMonitor";
import { toast } from "./ui";

type Msg = { id: string; role: string; content: string; data?: any; created_at: string };

export default function Chat({ projectId, onAction }: { projectId?: string; onAction?: () => void }) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [att, setAtt] = useState<{ id: string; filename: string }[]>([]);
  const end = useRef<HTMLDivElement>(null);
  const load = () => api<Msg[]>("/chat" + (projectId ? `?project_id=${projectId}` : "")).then(setMsgs).catch(() => {});
  useEffect(() => { load(); }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs.length]);
  const send = async () => {
    if (!text.trim() || busy) return;
    setBusy(true);
    const t = text;
    setText("");
    setMsgs((m) => [...m, { id: "tmp", role: "user", content: t, created_at: new Date().toISOString() }]);
    try {
      const r = await api("/chat", { body: { text: t, project_id: projectId, attachments: att.map((a) => a.id) } });
      setAtt([]);
      await load();
      if (r.actions?.length) onAction?.();
    } catch (e: any) {
      toast(e.message, "bad");
    } finally {
      setBusy(false);
    }
  };
  const upload = async (f: File) => {
    const fd = new FormData();
    fd.append("file", f);
    if (projectId) {
      const purpose = f.type.startsWith("audio") ? "voiceover" : f.type.startsWith("image") ? "reference" : f.type.startsWith("video") ? "footage" : "document";
      fd.append("purpose", purpose);
      await api(`/projects/${projectId}/uploads`, { form: fd });
      toast(`Uploaded ${f.name} as ${purpose}`);
      onAction?.();
    } else {
      const a = await api("/uploads", { form: fd });
      setAtt((x) => [...x, a]);
    }
  };
  return (
    <div className="flex h-full min-h-[420px] flex-col">
      <div className="flex-1 space-y-3 overflow-auto p-1">
        {msgs.length === 0 && (
          <div className="text-sm text-dim">
            Talk to your Director in English, Hindi or Hinglish. Examples:
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {projectId ? (
                <><li>Scene 4 ka camera movement change kar</li><li>Background music thoda lower kar</li><li>Make the opening 10 seconds more engaging</li><li>Use more 3D animation in the explanation</li></>
              ) : (
                <><li>Create a documentary titled What If Jupiter Disappeared? 8 minutes, cinematic, scientifically accurate</li><li>Research the most-watched videos about deep sea creatures</li><li>Remember: I prefer slow push-ins and minimal transitions</li></>
              )}
            </ul>
          </div>
        )}
        {msgs.map((m) => (
          <div key={m.id + m.created_at} className={`flex ${m.role === "user" ? "justify-end" : ""}`}>
            <div className={`max-w-[85%] whitespace-pre-wrap rounded-xl px-3.5 py-2.5 text-sm ${m.role === "user" ? "bg-acc/15 text-ink" : "border border-line bg-panel2"}`}>
              {m.content}
              {(m.data?.actions || []).map((a: any, i: number) => (
                <div key={i} className="mt-2 rounded-lg border border-line bg-bg p-2 text-xs">
                  {a.type === "production_started" && <><Link className="font-semibold text-acc" href={`/project/?id=${a.project_id}`}>Open project →</Link><div className="mt-2"><RunMonitor runId={a.run_id} compact /></div></>}
                  {(a.type === "edit_started" || a.type === "render_started") && <RunMonitor runId={a.run_id} compact onEnd={onAction} />}
                  {a.type === "remembered" && <span className="text-ok">Saved to memory: {a.content}</span>}
                  {a.type === "not_remembered" && <span className="text-warn">Not saved: {a.reason}</span>}
                  {(a.type === "research_report" || a.type === "youtube_report") && <span className="text-dim">Report saved in YouTube Intelligence → Reports</span>}
                </div>
              ))}
            </div>
          </div>
        ))}
        {busy && <div className="text-xs text-dim">Director is thinking…</div>}
        <div ref={end} />
      </div>
      {att.length > 0 && <div className="flex flex-wrap gap-1 px-1 pb-1">{att.map((a) => <span key={a.id} className="tag">{a.filename}</span>)}</div>}
      <div className="mt-2 flex items-end gap-2">
        <label className="btn cursor-pointer" title="Attach file">
          +<input type="file" className="hidden" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0]).catch((er) => toast(er.message, "bad"))} />
        </label>
        <textarea className="input min-h-[44px] flex-1 resize-none" rows={2} value={text} placeholder="Tell the Director what to do…" onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} />
        <button className="btn btn-pri" disabled={busy || !text.trim()} onClick={send}>Send</button>
      </div>
    </div>
  );
}
