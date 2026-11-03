#!/usr/bin/env node
// Render "Why Perfect Banks Didn't Work" frame-by-frame: Three.js (headless Chromium via Playwright) -> raw RGBA -> ffmpeg.
//
//   node render.cjs preview 0,3,9.5 [--w 405 --h 720]     -> preview_<t>.png stills
//   node render.cjs video [--workers 4] [--from 0 --to 2400]  -> parts/ + why_perfect_banks.mp4 (with audio.py mix)
//   node render.cjs camtrack                               -> camtrack.json (used by audio.py for whooshes)
//
// Requires: playwright (global), ffmpeg, python3 + numpy/scipy for the soundtrack.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), { spawn, execFileSync } = require('child_process');

const ROOT = __dirname;
const args = process.argv.slice(2); const mode = args[0] || 'video';
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const W = +opt('w', 810), H = +opt('h', 1440);
const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'timeline.json')));
const NFR = Math.round(TL.duration * TL.fps) + 1; // inclusive: last frame == first frame (loop)

function serve() {
  const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json' };
  const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); if (!f.startsWith(ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
  return new Promise(res => srv.listen(0, () => res(srv)));
}
async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 400, height: 400 } });
  page.on('console', m => { if (m.type() === 'error') console.error('[page]', m.text()); });
  page.on('pageerror', e => console.error('[pageerror]', e.message));
  await page.goto(`http://127.0.0.1:${port}/index.html?w=${W}&h=${H}`);
  await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  return page;
}
const launch = () => chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
function ff(argv, input) { return new Promise((res, rej) => { const p = spawn('ffmpeg', argv, { stdio: ['pipe', 'ignore', 'inherit'] }); p.on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()); if (input) { p.stdin.end(input); } else res.stdin = p.stdin; p.stdinRef = p.stdin; ff.last = p; }); }

(async () => {
  const srv = await serve(); const port = srv.address().port;
  if (mode === 'preview' || mode === 'frames') {
    const b = await launch(); const page = await openPage(b, port);
    const list = (args[1] || '0').split(',');
    const outDir = opt('out', path.join(ROOT, 'previews')); fs.mkdirSync(outDir, { recursive: true });
    for (const s of list) {
      const t0 = Date.now();
      const isFrame = mode === 'frames';
      const res = isFrame ? await page.evaluate(f => window.renderFrame(f), +s) : { data: await page.evaluate(t => window.renderTime(t), +s) };
      const buf = Buffer.from(res.data, 'base64'); const name = path.join(outDir, (isFrame ? 'f_' : 't_') + s + '.png');
      await ff(['-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-i', '-', '-vf', 'vflip', name], buf);
      console.log(name, (Date.now() - t0) + 'ms', res.n ? 'sub=' + res.n : '');
    }
    await b.close(); srv.close(); return;
  }
  if (mode === 'camtrack') {
    const b = await launch(); const page = await openPage(b, port); const tr = await page.evaluate(() => window.camTrack());
    fs.writeFileSync(path.join(ROOT, 'camtrack.json'), JSON.stringify(tr)); await b.close(); srv.close(); console.log('camtrack frames', tr.length); return;
  }
  // ---- full video
  const workers = +opt('workers', 4), from = +opt('from', 0), to = +opt('to', NFR);
  const partsDir = path.join(ROOT, 'parts'); fs.mkdirSync(partsDir, { recursive: true });
  const n = to - from, per = Math.ceil(n / workers); const t0 = Date.now(); let done = 0;
  const jobs = [];
  for (let w = 0; w < workers; w++) {
    const a = from + w * per, z = Math.min(to, a + per); if (a >= z) continue;
    jobs.push((async () => {
      const out = path.join(partsDir, `part_${String(a).padStart(5, '0')}.mp4`);
      if (fs.existsSync(out + '.done')) { done += z - a; return out; }
      const b = await launch(); const page = await openPage(b, port);
      const p = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(TL.fps), '-i', '-', '-vf', 'vflip,format=yuv420p', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-g', '60', out], { stdio: ['pipe', 'ignore', 'inherit'] });
      const closed = new Promise(r => p.on('close', r));
      for (let f = a; f < z; f++) {
        const res = await page.evaluate(f => window.renderFrame(f), f);
        const buf = Buffer.from(res.data, 'base64'); if (!p.stdin.write(buf)) await new Promise(r => p.stdin.once('drain', r));
        done++; if (done % 30 === 0) { const el = (Date.now() - t0) / 1000; console.log(`frames ${done}/${n}  ${(el / done).toFixed(2)}s/f  eta ${((n - done) * el / done / 60).toFixed(1)} min`); }
      }
      p.stdin.end(); await closed; await b.close(); fs.writeFileSync(out + '.done', ''); return out;
    })());
  }
  const parts = (await Promise.all(jobs)).sort();
  srv.close();
  const list = path.join(partsDir, 'list.txt'); fs.writeFileSync(list, parts.map(p => `file '${p}'`).join('\n'));
  const silent = path.join(ROOT, 'parts', 'video_silent.mp4');
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', silent], { stdio: 'inherit' });
  // soundtrack (voiceover optional: --voice file)
  const voice = opt('voice', TL.voice ? path.join(ROOT, TL.voice) : null);
  execFileSync('node', [__filename, 'camtrack'], { stdio: 'inherit' });
  const mix = path.join(partsDir, 'mix.wav');
  execFileSync('python3', [path.join(ROOT, 'audio_banks.py'), '--out', mix, ...(voice ? ['--voice', voice] : [])], { stdio: 'inherit' });
  const final = path.join(ROOT, opt('name', 'why_perfect_banks_didnt_work.mp4'));
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', silent, '-i', mix, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(TL.fps), '-af', 'loudnorm=I=-14:TP=-1.0:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', final], { stdio: 'inherit' });
  console.log('done ->', final, ((Date.now() - t0) / 60000).toFixed(1), 'min');
})();
