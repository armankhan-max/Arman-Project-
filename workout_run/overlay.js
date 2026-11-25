// Renders the big move-cue overlay (600x520 RGBA PNGs, placed at x=660,y=0) into out/ov/f%06d.png.
// Frames without a cue are hard links to one transparent PNG. Run with: node overlay.js [workers]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, 'web');
const OUTD = path.join(__dirname, 'out', 'ov');
fs.mkdirSync(OUTD, { recursive: true });
const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'timeline.json')));
const TOTAL = Math.round(TL.duration * TL.fps);
const NW = parseInt(process.argv[2] || '3');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
let next = 0;
async function worker(port, blankPath) {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', (e) => console.log('PAGEERROR', e.message));
  await page.goto(`http://localhost:${port}/index.html?overlay=1`);
  await page.waitForFunction('window.ready', null, { timeout: 600000 });
  while (next < TOTAL) {
    const f0 = next; next = Math.min(TOTAL, next + 300);
    const urls = await page.evaluate(([a, z]) => { const o = []; for (let f = a; f < z; f++) o.push(window.renderOverlay(f)); return o; }, [f0, next]);
    urls.forEach((u, i) => {
      const fp = path.join(OUTD, `f${String(f0 + i).padStart(6, '0')}.png`);
      try { fs.unlinkSync(fp); } catch (e) { /* new */ }
      if (u) fs.writeFileSync(fp, Buffer.from(u.split(',')[1], 'base64'));
      else fs.linkSync(blankPath, fp);
    });
  }
  await b.close();
}
server.listen(0, async () => {
  const port = server.address().port;
  const blankPath = path.join(__dirname, 'out', 'blank.png');
  const { execSync } = require('child_process');
  execSync(`ffmpeg -v error -y -f lavfi -i color=c=black@0.0:s=600x520,format=rgba -frames:v 1 ${blankPath}`);
  const t0 = Date.now();
  await Promise.all([...Array(NW)].map(() => worker(port, blankPath)));
  server.close();
  console.log('OVERLAY DONE', ((Date.now() - t0) / 1000).toFixed(0) + 's');
});
