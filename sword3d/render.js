// Renders frames with headless Chromium (WebGL via SwiftShader).
// node render.js --out frames [--fps 30] [--dur 40.4] [--workers 3] [--times 1.0,5.2,...]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? a.concat([[v.slice(2), arr[i + 1]]]) : a), []));
const OUT = args.out || 'frames', FPS = +(args.fps || 30), DUR = +(args.dur || 40.4), WK = +(args.workers || 3);
fs.mkdirSync(OUT, { recursive: true });

const ROOT = __dirname;
const MAP = { '/three.module.js': 'node_modules/three/build/three.module.js', '/': 'index.html' };
const srv = http.createServer((q, r) => {
  let u = q.url.split('?')[0];
  let p = MAP[u] || (u.startsWith('/jsm/') ? 'node_modules/three/examples' + u : u.slice(1));
  p = path.join(ROOT, p);
  if (!fs.existsSync(p)) { r.statusCode = 404; return r.end(); }
  r.setHeader('Content-Type', p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : p.endsWith('.json') ? 'application/json' : 'application/octet-stream');
  r.end(fs.readFileSync(p));
}).listen(0, async () => {
  const port = srv.address().port;
  let times;
  if (args.times) times = args.times.split(',').map(Number).map((t, i) => [t, `t_${t.toFixed(2)}`]);
  else { const n = Math.round(DUR * FPS); times = Array.from({ length: n }, (_, i) => [i / FPS, `f${String(i).padStart(5, '0')}`]); }
  times = times.filter(([, n]) => !fs.existsSync(path.join(OUT, n + '.jpg')));
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const t0 = Date.now(); let done = 0;
  await Promise.all(Array.from({ length: WK }, async (_, w) => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
    page.on('pageerror', e => console.log('[pageerror]', e.message));
    await page.goto(`http://localhost:${port}/`);
    await page.waitForFunction('window.ready === true', null, { timeout: 60000 });
    const chunk = Math.ceil(times.length / WK);
    for (const [t, name] of times.slice(w * chunk, (w + 1) * chunk)) {
      await page.evaluate(t => window.renderFrame(t), t);
      const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
      fs.writeFileSync(path.join(OUT, name + '.jpg'), buf);
      if (++done % 60 === 0) console.log(`${done}/${times.length}  ${((Date.now() - t0) / done).toFixed(0)} ms/frame`);
    }
  }));
  await browser.close(); srv.close();
  console.log('done', done, 'frames in', ((Date.now() - t0) / 1000).toFixed(1), 's');
});
