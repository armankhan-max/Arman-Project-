import "./globals.css";
import type { Metadata } from "next";
import Shell from "@/components/Shell";

export const metadata: Metadata = { title: "Film Director AI", description: "Private autonomous AI film production studio" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg font-sans text-ink">
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
