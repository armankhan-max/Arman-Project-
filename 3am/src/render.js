// Frame renderer: draws every frame with skia canvas and pipes raw RGBA into ffmpeg.
//   node src/render.js                 -> full render (parallel workers) + mux with audio
//   node src/render.js --still 12.5,40 -> PNG stills to out/stills
//   node src/render.js --range 0,20    -> quick preview clip of a time range
const fs = require('fs'), path = require('path'), os = require('os');
const { spawn, spawnSync } = require('child_process');
const L = require('./lib');
const T = require("./tl");
const { W, H, FPS, BAR, E, inv, clamp, lerp, text } = L;

const scenes = require('./scenes').sort((a, b) => a.s - b.s);
const OUT = path.join(__dirname, '..', 'out'); fs.mkdirSync(OUT, { recursive: true });
const DUR = T.END;
let CV = null;

// Gold time-of-day stamp in the top bar (like "DAY 3" in the reference)
const TAGS = [
  [0, '3:07 AM'], [T.rew, ''], [T.toDay, '7:42 AM'], [T.hop, '7:51 AM'], [T.run, '8:03 AM'], [T.enter, '9:15 AM'], [T.lwalk, '12:40 PM'], [T.approach, '1:10 PM'],
  [T.cafe, '4:05 PM'], [T.call, '6:12 PM'], [T.street, '7:40 PM'], [T.night, ''], [T.snap, '3:07 AM'], [T.jump319, '3:19 AM'], [T.replay, '3:20 AM'], [T.song, '3:22 AM'],
  [T.cheer, 'IMAGINATION MODE'], [T.real, '3:25 AM'], [T.drift, '3:26 AM'], [T.storm, '3:33 AM'], [T.dieClick, ''], [T.fridge, '3:47 AM'], [T.shrink, '3:58 AM'], [T.callback, '3:59 AM'],
  [T.next, 'NEXT NIGHT'], [T.tag307, '3:07 AM'], [T.card, ''],
];
function tagAt(t) { let cur = TAGS[0]; for (const g of TAGS) if (t >= g[0]) cur = g; return cur; }

function drawFrame(ctx, f) {
  const t = f / FPS;
  let sc = scenes[0]; for (const s of scenes) if (t >= s.s) sc = s;
  const lt = t - sc.s, dur = sc.e - sc.s;
  ctx.save();
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  // camera: slow push + handheld drift + "punch-in" settle after each cut
  const [z0, z1, cx, cy] = sc.cam || [1, 1, W / 2, H / 2];
  let z = lerp(z0, z1, E.inOut(clamp(lt / dur)));
  z *= 1 + .025 * (1 - E.out(clamp(lt / .35)));
  z = Math.max(z, 1.012);
  // keep the view inside the painted frame (no black edges)
  const hw = W / (2 * z), hh = H / (2 * z);
  const ccx = clamp(cx, hw + 8, W - hw - 8), ccy = clamp(cy, hh + 6, H - hh - 6);
  let dx = L.noise1(t * .35) * 7, dy = L.noise1(t * .3 + 50) * 5;
  for (const [ts, d, amp] of (sc.shake || [])) if (t >= ts && t < ts + d) { const k = 1 - (t - ts) / d; dx += (Math.random() - .5) * amp * 2 * k; dy += (Math.random() - .5) * amp * 2 * k; }
  ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(z, z); ctx.translate(-ccx, -ccy);
  sc.draw(ctx, t, f);
  ctx.restore();
  if (sc.post) sc.post(ctx, t, CV);
  // finishing
  L.vignette(ctx, sc.vig ?? .6);
  if (sc.flash && lt < .25) { ctx.fillStyle = `rgba(255,245,220,${(1 - lt / .25) * .7})`; ctx.fillRect(0, 0, W, H); }
  const fadeIn = sc.fadeIn ? clamp(lt / sc.fadeIn) : 1; const fadeOut = sc.fadeOut ? clamp((sc.e - t) / sc.fadeOut) : 1;
  const k = Math.min(fadeIn, fadeOut); if (k < 1) { ctx.fillStyle = `rgba(0,0,0,${1 - k})`; ctx.fillRect(0, 0, W, H); }
  if (t > DUR - 1.2) { ctx.fillStyle = `rgba(0,0,0,${clamp((t - (DUR - 1.2)) / 1.2)})`; ctx.fillRect(0, 0, W, H); }
  L.grain(ctx, f, .035);
  L.letterbox(ctx);
  // time stamp
  const [tg0, tag] = tagAt(t);
  if (tag) { const a = E.out(clamp((t - tg0) / .4)); ctx.save(); ctx.globalAlpha = a; ctx.beginPath(); ctx.rect(30, 0, 900, BAR); ctx.clip(); text(ctx, tag, 40 - (1 - a) * 60, BAR / 2 + 3, { size: 46, weight: 900, color: '#e9b949', align: 'left' }); ctx.restore(); }
}


function ffmpegOut(file, extra = []) {
  return spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', ...extra, file], { stdio: ['pipe', 'inherit', 'inherit'] });
}
async function renderRange(f0, f1, file) {
  const [c, ctx] = L.canvas(); CV = c; const ff = ffmpegOut(file);
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    drawFrame(ctx, f);
    const buf = c.data();
    if (!ff.stdin.write(Buffer.from(buf))) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 300 === 0) process.stderr.write(`[${path.basename(file)}] ${f - f0}/${f1 - f0} ${((Date.now() - t0) / Math.max(1, f - f0)).toFixed(0)}ms/f\n`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}

async function main() {
  const a = process.argv.slice(2);
  if (a[0] === '--still') {
    const dir = path.join(OUT, 'stills'); fs.mkdirSync(dir, { recursive: true }); const [c, ctx] = L.canvas(); CV = c;
    for (const s of a[1].split(',').map(Number)) { drawFrame(ctx, Math.round(s * FPS)); fs.writeFileSync(path.join(dir, `s_${s.toFixed(2)}.png`), c.toBuffer('image/png')); }
    return;
  }
  if (a[0] === '--worker') { await renderRange(+a[1], +a[2], a[3]); return; }
  let f0 = 0, f1 = Math.ceil(DUR * FPS), out = path.join(OUT, 'video_noaudio.mp4');
  if (a[0] === '--range') { const [s, e] = a[1].split(',').map(Number); f0 = Math.round(s * FPS); f1 = Math.round(e * FPS); out = path.join(OUT, `preview_${s}_${e}.mp4`); }
  const N = Math.max(1, Math.min(+(process.env.WORKERS || os.cpus().length), 8));
  const per = Math.ceil((f1 - f0) / N), parts = [];
  const jobs = [];
  for (let i = 0; i < N; i++) {
    const a0 = f0 + i * per, a1 = Math.min(f1, a0 + per); if (a0 >= a1) break;
    const pf = path.join(OUT, `part_${i}.mp4`); parts.push(pf);
    jobs.push(new Promise((res, rej) => { const p = spawn(process.execPath, [__filename, '--worker', a0, a1, pf], { stdio: 'inherit' }); p.on('close', c => c === 0 ? res() : rej(new Error('worker ' + i))); }));
  }
  await Promise.all(jobs);
  fs.writeFileSync(path.join(OUT, 'parts.txt'), parts.map(p => `file '${p}'`).join('\n'));
  spawnSync('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', path.join(OUT, 'parts.txt'), '-c', 'copy', out], { stdio: 'inherit' });
  parts.forEach(p => fs.unlinkSync(p));
  const mix = path.join(OUT, 'mix.wav');
  if (fs.existsSync(mix)) {
    const fin = a[0] === '--range' ? out.replace('.mp4', '_av.mp4') : path.join(__dirname, '..', '3am_thoughts.mp4');
    const ss = f0 / FPS, dd = (f1 - f0) / FPS;
    spawnSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', out, '-ss', String(ss), '-t', String(dd), '-i', mix, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', fin], { stdio: 'inherit' });
    console.log('wrote', fin);
  } else console.log('wrote', out, '(no audio yet: run node src/audio.js)');
}
main().catch(e => { console.error(e); process.exit(1); });
