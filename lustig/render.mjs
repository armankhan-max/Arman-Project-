// Usage:
//   node render.mjs stills OUTDIR t1 t2 ...       -> PNG stills at given times
//   node render.mjs seq OUTDIR t0 t1 step         -> frame sequence (for checking camera moves)
//   node render.mjs events events.json            -> dump sound-event timeline
//   node render.mjs video out_silent.mp4 [from] [to]
import http from 'http';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.png': 'image/png', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}/index.html`;

const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-device-scale-factor=1'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
page.on('console', m => { if (m.type() === 'error') console.error('PAGE:', m.text()); });
page.on('pageerror', e => console.error('PAGEERR:', e.message));
await page.goto(url);
await page.waitForFunction(() => window.READY || window.INIT_ERROR, null, { timeout: 180000 });
const err = await page.evaluate(() => window.INIT_ERROR);
if (err) { console.error(err); process.exit(1); }

const [mode, outp, ...rest] = process.argv.slice(2);
const grab = async (t, fmt = 'image/png', q = 0.95) => {
  const data = await page.evaluate(([t, fmt, q]) => { window.renderFrame(t); return document.getElementById('c').toDataURL(fmt, q); }, [t, fmt, q]);
  return Buffer.from(data.split(',')[1], 'base64');
};

if (mode === 'events') {
  fs.writeFileSync(outp, JSON.stringify(await page.evaluate(() => window.EVENTS), null, 0));
} else if (mode === 'stills' || mode === 'seq') {
  fs.mkdirSync(outp, { recursive: true });
  let times = rest.map(Number);
  if (mode === 'seq') { const [a, b, s] = times; times = []; for (let t = a; t <= b + 1e-9; t += s) times.push(+t.toFixed(4)); }
  for (const t of times) fs.writeFileSync(path.join(outp, `t${t.toFixed(2).padStart(6, '0')}.png`), await grab(t));
} else if (mode === 'video') {
  const fps = await page.evaluate(() => window.FPS), dur = await page.evaluate(() => window.DURATION);
  const from = rest[0] ? +rest[0] : 0, to = rest[1] ? +rest[1] : dur;
  const n0 = Math.round(from * fps), n1 = Math.round(to * fps);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), outp], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let n = n0; n < n1; n++) {
    const buf = await grab(n / fps, 'image/jpeg', 0.94);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (n % 120 === 0) console.log(`frame ${n}/${n1}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
await browser.close(); server.close();
