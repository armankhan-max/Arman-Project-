import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0b0e", panel: "#13151b", panel2: "#1a1d25", line: "#262a34", line2: "#333845",
        ink: "#eceef3", dim: "#9aa1b0", mute: "#666e7d", acc: "#ff7a1a", ok: "#34c98a", bad: "#ff5468", warn: "#f5b942", info: "#5aa9ff",
      },
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"], mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"] },
    },
  },
  plugins: [],
} satisfies Config;
