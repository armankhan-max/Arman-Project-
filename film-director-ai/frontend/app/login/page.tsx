"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox } from "@/components/ui";

export default function Login() {
  const [email, setEmail] = useState("owner@localhost");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const go = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api("/auth/login", { body: { email, password: pw } });
      location.href = "/";
    } catch (x: any) {
      setErr(x.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="grid min-h-screen place-items-center px-4">
      <form onSubmit={go} className="card flex w-full max-w-sm flex-col gap-4">
        <div className="flex items-center gap-2 text-lg font-bold"><span className="grid h-8 w-8 place-items-center rounded-md bg-acc text-black">▶</span> Film Director AI</div>
        <p className="text-sm text-dim">Private studio. Owner sign-in only.</p>
        <label className="label">Email<input className="input" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" /></label>
        <label className="label">Password<input className="input" type="password" value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="current-password" autoFocus /></label>
        <ErrorBox e={err} />
        <button className="btn btn-pri" disabled={busy || !pw}>Sign in</button>
        <p className="text-xs text-mute">First run: the password is in storage/OWNER_CREDENTIALS.txt unless FDA_OWNER_PASSWORD was set.</p>
      </form>
    </div>
  );
}
