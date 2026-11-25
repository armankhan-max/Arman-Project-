// Parallel, resumable frame renderer.
// Serves ./web, drives headful Chromium (ANGLE on Mesa llvmpipe under Xvfb), captures each frame
// and encodes 30-second chunks to out/chunks/cNNNN.mp4. Re-running skips finished chunks.
//   xvfb-run -a -s "-screen 0 1920x1080x24" node render.js [workers] [firstFrame] [lastFrame]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, 'web');
const OUT = path.join(__dirname, 'out', 'chunks');
fs.mkdirSync(OUT, { recursive: true });
const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'timeline.json')));
const FPS = TL.fps;
const TOTAL = Math.round(TL.duration * FPS);
const WORKERS = parseInt(process.argv[2] || '2');
const F0 = parseInt(process.argv[3] || '0');
const F1 = Math.min(TOTAL, parseInt(process.argv[4] || String(TOTAL)));
const CHUNK = 900;

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

const chunks = [];
for (let c = Math.floor(F0 / CHUNK); c * CHUNK < F1; c++) {
  const file = path.join(OUT, `c${String(c).padStart(4, '0')}.mp4`);
  if (fs.existsSync(file) && fs.existsSync(file + '.done')) continue;
  chunks.push({ c, a: Math.max(F0, c * CHUNK), b: Math.min(F1, (c + 1) * CHUNK), file });
}

async function worker(id, port) {
  const browser = await chromium.launch({ headless: false, args: ['--use-gl=angle', '--use-angle=gl', '--ignore-gpu-blocklist', '--enable-gpu', '--window-size=1920,1080', '--disable-renderer-backgrounding', '--disable-background-timer-throttling'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', (e) => console.log(`[w${id}] PAGEERROR ${e.message}`));
  page.on('console', (m) => { if (m.type() === 'error') console.log(`[w${id}] console ${m.text()}`); });
  await page.goto(`http://localhost:${port}/index.html`);
  await page.waitForFunction('window.ready', null, { timeout: 600000 });
  const cdp = await page.context().newCDPSession(page);
  while (chunks.length) {
    const ch = chunks.shift();
    const t0 = Date.now();
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-pix_fmt', 'yuv420p', '-threads', '2', ch.file]);
    ff.stderr.on('data', (d) => process.stdout.write(`[w${id} ffmpeg] ${d}`));
    for (let f = ch.a; f < ch.b; f++) {
      await page.evaluate((fr) => window.renderFrame(fr), f);
      const shot = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 95 });
      const buf = Buffer.from(shot.data, 'base64');
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
    fs.writeFileSync(ch.file + '.done', '');
    const dt = (Date.now() - t0) / 1000;
    console.log(`[w${id}] chunk ${ch.c} frames ${ch.a}-${ch.b} in ${dt.toFixed(0)}s (${((ch.b - ch.a) / dt).toFixed(2)} fps), ${chunks.length} left`);
  }
  await browser.close();
}

server.listen(0, async () => {
  const port = server.address().port;
  console.log(`rendering frames ${F0}-${F1} of ${TOTAL} in ${chunks.length} chunks with ${WORKERS} workers`);
  await Promise.all([...Array(WORKERS)].map((_, i) => worker(i, port)));
  server.close();
  console.log('ALL DONE');
});
