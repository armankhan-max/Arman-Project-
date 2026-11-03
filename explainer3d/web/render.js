// node render.js out.mp4 [jobs] -- workers pull 4-second chunks from a queue (heavy shots get shared),
// each chunk -> its own mp4 (resumable), then everything is concatenated in order.
const { chromium } = require('playwright'); const { spawn } = require('child_process'); const fs = require('fs'); const path = require('path');
const FPS = 25, DUR = 251.0, CHUNK = 100;
(async () => {
  const [out, jobsS = '4'] = process.argv.slice(2); const jobs = +jobsS;
  const dir = out.replace(/\.mp4$/, '_parts'); fs.mkdirSync(dir, { recursive: true });
  const total = Math.round(DUR * FPS); const chunks = [];
  for (let f = 0; f < total; f += CHUNK) chunks.push([f, Math.min(total, f + CHUNK)]);
  let next = 0, doneN = 0; const t0 = Date.now();
  async function worker(id) {
    const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
    const p = await b.newPage({ viewport: { width: 1280, height: 720 } }); p.on('pageerror', (e) => console.log(`[w${id}] ERR`, e.message));
    await p.goto('http://127.0.0.1:8765/web/index.html'); await p.waitForFunction('window.ready', null, { timeout: 180000 });
    while (next < chunks.length) {
      const ci = next++; const [a, z] = chunks[ci]; const o = path.join(dir, `c${String(ci).padStart(3, '0')}.mp4`);
      if (fs.existsSync(o) && fs.statSync(o).size > 1000) { doneN++; continue; }
      const tmp = o.replace(/\.mp4$/, '.tmp.mp4');
      const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS), tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
      for (let f = a; f < z; f++) {
        const d = await p.evaluate(`(window.frame(${(f / FPS).toFixed(5)}), window.grab(.95))`);
        if (!ff.stdin.write(Buffer.from(d.slice(d.indexOf(',') + 1), 'base64'))) await new Promise((r) => ff.stdin.once('drain', r));
      }
      ff.stdin.end(); await new Promise((r) => ff.on('close', r)); fs.renameSync(tmp, o); doneN++;
      console.log(`[w${id}] chunk ${ci + 1}/${chunks.length} (${doneN} done, ${((Date.now() - t0) / 60000).toFixed(1)} min)`);
    }
    await b.close();
  }
  await Promise.all([...Array(jobs)].map((_, i) => worker(i)));
  fs.writeFileSync(path.join(dir, 'list.txt'), chunks.map((_, i) => `file '${path.resolve(dir, `c${String(i).padStart(3, '0')}.mp4`)}'`).join('\n'));
  await new Promise((r) => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(dir, 'list.txt'), '-c', 'copy', out], { stdio: 'inherit' }).on('close', r));
  console.log('done', out);
})();
