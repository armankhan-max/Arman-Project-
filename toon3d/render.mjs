// Renders frames with headless Chromium (software WebGL).
// node render.mjs --out DIR [--scale 0.5] [--times 1,2.5,4] [--from 0 --to 20.5] [--jobs 4]
import http from 'http'; import fs from 'fs'; import path from 'path'; import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const root = path.dirname(new URL(import.meta.url).pathname);
const outDir = arg('out', 'frames'), scale = parseFloat(arg('scale', '1')), jobs = parseInt(arg('jobs', '4'));
fs.mkdirSync(outDir, { recursive: true });
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript' };
const srv = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split('?')[0]).replace(/^\/$/, '/index.html'));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'content-type': mime[path.extname(f)] || 'application/octet-stream' }); r.end(d); } });
}).listen(0);
const port = srv.address().port;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const W = Math.round(1080 * scale), H = Math.round(1920 * scale);
async function worker(list) {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.setDefaultTimeout(0);
  page.on('pageerror', e => console.error('PAGE ERROR', e.message)); page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto(`http://localhost:${port}/?scale=${scale}`);
  await page.waitForFunction('window.READY'); await page.evaluate('window.READY');
  for (const [name, t] of list) {
    if (fs.existsSync(path.join(outDir, name))) continue;
    await page.evaluate(t => window.renderFrame(t), t);
    await page.locator('#out').screenshot({ path: path.join(outDir, name), type: 'jpeg', quality: 93 });
  }
  await page.close();
}
let list = [];
if (arg('times')) list = arg('times').split(',').map(s => [`t_${(+s).toFixed(2).padStart(5, '0')}.jpg`, +s]);
else {
  const fps = 30, a = parseFloat(arg('from', '0')), b = parseFloat(arg('to', '20.5'));
  for (let f = Math.round(a * fps); f < Math.round(b * fps); f++) list.push([`f_${String(f).padStart(5, '0')}.jpg`, f / fps]);
}
const t0 = Date.now();
const parts = Array.from({ length: jobs }, (_, j) => list.filter((_, i) => i % jobs === j));
await Promise.all(parts.filter(p => p.length).map(worker));
console.log(`rendered ${list.length} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
await browser.close(); srv.close();
