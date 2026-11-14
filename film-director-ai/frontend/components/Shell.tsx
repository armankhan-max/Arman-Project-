"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";
import { Toasts } from "./ui";

const NAV = [
  ["/", "Dashboard"],
  ["/chat", "AI Director"],
  ["/projects", "Projects"],
  ["/characters", "Characters"],
  ["/youtube", "YouTube Intelligence"],
  ["/knowledge", "Knowledge"],
  ["/memory", "Memory & Preferences"],
  ["/settings", "Settings"],
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname() || "/";
  if (path.startsWith("/login")) return <>{children}<Toasts /></>;
  const wide = path.startsWith("/project/");
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-56 shrink-0 flex-col gap-1 border-r border-line bg-[#0e1014] p-3 md:flex">
        <Link href="/" className="mb-4 flex items-center gap-2 px-2 pt-1 text-[15px] font-bold">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-acc text-xs text-black">▶</span> Film Director AI
        </Link>
        {NAV.map(([href, label]) => {
          const on = href === "/" ? path === "/" : (path.startsWith(href) && !(href === "/projects" && path.startsWith("/project/")));
          return (
            <Link key={href} href={href} className={`rounded-lg px-3 py-2 text-sm font-medium ${on ? "bg-panel2 text-ink" : "text-dim hover:bg-panel hover:text-ink"}`}>
              {label}
            </Link>
          );
        })}
        <button className="btn-ghost btn btn-sm mt-auto justify-start" onClick={async () => { await api("/auth/logout", { method: "POST" }); location.href = "/login"; }}>
          Sign out
        </button>
      </aside>
      <nav className="fixed inset-x-0 bottom-0 z-30 flex border-t border-line bg-[#0e1014] md:hidden">
        {NAV.slice(0, 5).map(([href, label]) => (
          <Link key={href} href={href} className={`flex-1 px-1 py-2.5 text-center text-[11px] ${path === href ? "text-acc" : "text-dim"}`}>{label.split(" ")[0]}</Link>
        ))}
      </nav>
      <Toasts />
      <main className={`min-w-0 flex-1 pb-20 md:pb-0 ${wide ? "" : "mx-auto max-w-6xl px-4 py-6 md:px-8"}`}>{children}</main>
    </div>
  );
}
