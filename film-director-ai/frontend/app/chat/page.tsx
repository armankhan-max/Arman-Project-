"use client";
import Chat from "@/components/Chat";

export default function DirectorChat() {
  return (
    <div className="flex h-[calc(100vh-3rem)] flex-col gap-3">
      <div>
        <h1 className="h1">AI Director</h1>
        <p className="text-sm text-dim">Describe the video you want, attach narration or references, or ask for research. The Director plans the production and runs it autonomously within your budget.</p>
      </div>
      <div className="card flex-1 overflow-hidden"><Chat /></div>
    </div>
  );
}
