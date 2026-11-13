// UI end-to-end check against running servers (frontend :3000, backend :8000).
// Usage: FDA_PASSWORD=... node tests/e2e/ui.e2e.cjs   (needs Playwright with Chromium)
const { chromium } = require("playwright");
const BASE = process.env.FDA_WEB || "http://localhost:3000";
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 860 } });
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  const fail = (m) => { console.error("FAIL:", m); process.exitCode = 1; };
  await p.goto(BASE + "/login");
  await p.fill("input[type=password]", process.env.FDA_PASSWORD || "");
  await p.click("button");
  await p.waitForURL(BASE + "/");
  if (!(await p.textContent("h1")).includes("Dashboard")) fail("dashboard");
  await p.goto(BASE + "/projects?new=1");
  await p.fill("input.text-base", "UI test project");
  await p.click("text=Create only");
  await p.waitForURL(/\/projects\/[0-9a-f-]+/);
  for (const tab of ["Script & narration", "Storyboard", "Editor", "Assets", "Renders & QC", "Research", "Versions", "Jobs", "Project settings", "Director"]) {
    await p.click(`button:has-text("${tab}")`);
    await p.waitForTimeout(400);
  }
  await p.fill("textarea", "Remember that I like warm colour grades.");
  await p.keyboard.press("Enter");
  await p.waitForTimeout(500);
  for (const u of ["/chat", "/youtube", "/knowledge", "/memory", "/settings"]) {
    await p.goto(BASE + u);
    await p.waitForTimeout(800);
    if (!(await p.$("h1"))) fail("no heading on " + u);
  }
  await p.setViewportSize({ width: 390, height: 844 });
  await p.goto(BASE + "/");
  await p.waitForTimeout(800);
  const overflow = await p.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  if (overflow) fail("horizontal scroll on mobile dashboard");
  if (errors.length) fail("page errors: " + errors.join(" | "));
  await b.close();
  console.log(process.exitCode ? "UI e2e failed" : "UI e2e passed");
})();
