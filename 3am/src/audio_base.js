// Original, royalty-free soundtrack synthesised in JS (no voice): score + SFX + ambience,
// loudness-normalised (two-pass, linear) for YouTube.   node src/audio.js
const fs = require('fs'), path = require('path');
const { spawnSync } = require('child_process');
const T = require('./tl');
const END = T.END;
const SR = 44100, N = Math.ceil((END + 1) * SR);
const OUT = path.join(__dirname, '..', 'out'); fs.mkdirSync(OUT, { recursive: true });
const mL = new Float32Array(N), mR = new Float32Array(N); // music bus
const sL = new Float32Array(N), sR = new Float32Array(N); // sfx bus
let seed = 7; const rnd = () => { seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5; return ((seed >>> 0) / 4294967296); };
const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
const NOTE = { C: 0, 'C#': 1, Db: 1, D: 2, 'D#': 3, Eb: 3, E: 4, F: 5, 'F#': 6, Gb: 6, G: 7, 'G#': 8, Ab: 8, A: 9, 'A#': 10, Bb: 10, B: 11 };
const n = s => { const m = s.match(/^([A-G][b#]?)(-?\d)$/); return 12 * (+m[2] + 1) + NOTE[m[1]]; };
function put(bufL, bufR, i, v, pan) { if (i < 0 || i >= N) return; bufL[i] += v * Math.cos((pan + 1) * Math.PI / 4); bufR[i] += v * Math.sin((pan + 1) * Math.PI / 4); }

// ---------------- instruments ----------------
function piano(t, midi, vel = .3, dur = 2.5, pan = 0, bus = 'm') {
  const f = mtof(midi), i0 = Math.floor(t * SR), len = Math.floor((dur + 1.2) * SR); const [L, R] = bus === 'm' ? [mL, mR] : [sL, sR];
  for (let k = 0; k < len; k++) {
    const tt = k / SR; const env = Math.min(1, tt * 400) * Math.exp(-tt * (2.2 + midi / 40)) * (tt > dur ? Math.exp(-(tt - dur) * 8) : 1);
    const v = Math.sin(2 * Math.PI * f * tt) + .35 * Math.sin(2 * Math.PI * f * 2.001 * tt) * Math.exp(-tt * 3) + .12 * Math.sin(2 * Math.PI * f * 3.003 * tt) * Math.exp(-tt * 5);
    put(L, R, i0 + k, v * env * vel, pan);
  }
}
function pluck(t, midi, vel = .25, pan = 0, decay = 9, bright = 1) { // marimba / pizzicato
  const f = mtof(midi), i0 = Math.floor(t * SR), len = Math.floor(.9 * SR);
  for (let k = 0; k < len; k++) { const tt = k / SR; const env = Math.min(1, tt * 800) * Math.exp(-tt * decay); const v = Math.sin(2 * Math.PI * f * tt) + .25 * bright * Math.sin(2 * Math.PI * f * 4 * tt) * Math.exp(-tt * 30); put(mL, mR, i0 + k, v * env * vel, pan); }
}
function pad(t0, t1, midis, vel = .06, att = 1.5, rel = 2, bright = .3) {
  const i0 = Math.floor(t0 * SR), len = Math.floor((t1 - t0 + rel) * SR);
  midis.forEach((m, j) => {
    const f = mtof(m), det = [-.12, .1, .02]; const pan = (j / Math.max(1, midis.length - 1)) * 1.2 - .6;
    for (let k = 0; k < len; k++) {
      const tt = k / SR; let env = Math.min(1, tt / att); if (tt > t1 - t0) env *= Math.max(0, 1 - (tt - (t1 - t0)) / rel);
      const lfo = 1 + .002 * Math.sin(2 * Math.PI * .3 * tt + j);
      let v = 0; for (const d of det) { const ff = f * Math.pow(2, d / 12) * lfo; v += Math.sin(2 * Math.PI * ff * tt) + bright * .3 * Math.sin(4 * Math.PI * ff * tt); }
      put(mL, mR, i0 + k, v * env * vel / 3, pan);
    }
  });
}
function bass(t, midi, vel = .25, dur = .5) { const f = mtof(midi), i0 = Math.floor(t * SR), len = Math.floor((dur + .3) * SR); for (let k = 0; k < len; k++) { const tt = k / SR; const env = Math.min(1, tt * 200) * (tt < dur ? 1 : Math.exp(-(tt - dur) * 12)) * Math.exp(-tt * 1.2); put(mL, mR, i0 + k, (Math.sin(2 * Math.PI * f * tt) + .2 * Math.sin(4 * Math.PI * f * tt)) * env * vel, 0); } }
function kick(t, vel = .4, bus = 'm') { const i0 = Math.floor(t * SR), len = Math.floor(.4 * SR); const [L, R] = bus === 'm' ? [mL, mR] : [sL, sR]; let ph = 0; for (let k = 0; k < len; k++) { const tt = k / SR; const f = 45 + 90 * Math.exp(-tt * 30); ph += 2 * Math.PI * f / SR; put(L, R, i0 + k, Math.sin(ph) * Math.exp(-tt * 8) * vel, 0); } }
function shaker(t, vel = .05, pan = .3) { const i0 = Math.floor(t * SR), len = Math.floor(.08 * SR); let p = 0; for (let k = 0; k < len; k++) { const w = rnd() * 2 - 1; const hp = w - p; p = w; put(mL, mR, i0 + k, hp * Math.exp(-k / SR * 60) * vel, pan); } }
function heartbeat(t, vel = .35) { kick(t, vel, 's'); kick(t + .2, vel * .7, 's'); }

// ---------------- SFX ----------------
function noiseBurst(t, dur, vel, { lp = 1, hp = 0, pan = 0, shape = 'exp', fade = 20, sweep = null } = {}) {
  const i0 = Math.floor(t * SR), len = Math.floor(dur * SR); let a = 0, b = 0;
  for (let k = 0; k < len; k++) {
    const tt = k / SR, u = k / len; const w = rnd() * 2 - 1;
    const c = sweep ? sweep(u) : lp; a += c * (w - a); const hpv = a - b; b += hp * (a - b);
    const env = shape === 'swell' ? Math.sin(Math.PI * u) ** 2 : shape === 'flat' ? Math.min(1, u * 40) * Math.min(1, (1 - u) * 20) : Math.exp(-tt * fade);
    put(sL, sR, i0 + k, (hp ? hpv : a) * env * vel, pan);
  }
}
const whoosh = (t, vel = .22, dur = .5) => noiseBurst(t - dur * .6, dur, vel, { shape: 'swell', sweep: u => .02 + .25 * Math.sin(Math.PI * u), pan: 0 });
const tone = (t, f, dur, vel, { decay = 12, pan = 0, f2 = null, type = 'sine' } = {}) => { const i0 = Math.floor(t * SR), len = Math.floor(dur * SR); let ph = 0; for (let k = 0; k < len; k++) { const tt = k / SR, u = k / len; const ff = f2 ? f + (f2 - f) * u : f; ph += 2 * Math.PI * ff / SR; let v = Math.sin(ph); if (type === 'square') v = Math.sign(v) * .6; if (type === 'tri') v = 2 / Math.PI * Math.asin(Math.sin(ph)); put(sL, sR, i0 + k, v * Math.min(1, tt * 500) * Math.exp(-tt * decay) * vel, pan); } };
const pop = (t, vel = .18, f = 700) => tone(t, f, .12, vel, { decay: 35, f2: f * 1.8 });
const ding = (t, vel = .14, f = 1320) => { tone(t, f, 1.2, vel, { decay: 5 }); tone(t, f * 2.01, .8, vel * .3, { decay: 8 }); };
const click = (t, vel = .25) => noiseBurst(t, .02, vel, { lp: .9, fade: 300 });
const tap = (t, vel = .4) => { tone(t, 2100, .06, vel * .5, { decay: 60 }); tone(t, 900, .08, vel * .5, { decay: 50 }); noiseBurst(t, .02, vel * .6, { lp: .7, fade: 250 }); };
const thud = (t, vel = .5) => { kick(t, vel, 's'); noiseBurst(t, .15, vel * .4, { lp: .05, fade: 30 }); };
const plop = (t, vel = .25) => tone(t, 380, .18, vel, { decay: 20, f2: 900 });
const flap = (t, n = 6, vel = .12, rate = .085) => { for (let i = 0; i < n; i++) noiseBurst(t + i * rate, .07, vel, { lp: .08, shape: 'swell', pan: .2 }); };
const buzz = (t, dur = .9, vel = .18) => { for (let k = 0; k < 2; k++) tone(t + k * .5, 180, .35, vel, { decay: 1, type: 'square' }); };
const tick = (t, vel = .12) => { tone(t, 3000, .03, vel, { decay: 100 }); noiseBurst(t, .01, vel, { lp: .9, fade: 500 }); };
function caw(t, vel = .22, pitch = 1, pan = 0, len = .38) {
  const i0 = Math.floor(t * SR), L = Math.floor(len * SR); let ph = 0, z1 = 0, z2 = 0;
  // resonant band-pass (formant) around 1.3 kHz
  const fc = 1300 * pitch, q = 3, w0 = 2 * Math.PI * fc / SR, al = Math.sin(w0) / (2 * q); const b0 = al, a0 = 1 + al, a1 = -2 * Math.cos(w0), a2 = 1 - al;
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  for (let k = 0; k < L; k++) {
    const u = k / L; const f = (520 - 160 * u + 60 * Math.sin(u * 9)) * pitch; ph += 2 * Math.PI * f / SR;
    let x = ((ph / (2 * Math.PI)) % 1) * 2 - 1; x = x * (1 + .6 * Math.sin(2 * Math.PI * 68 * k / SR)) + (rnd() * 2 - 1) * .5;
    const y = (b0 * x - b0 * x2 - a1 * y1 - a2 * y2) / a0; x2 = x1; x1 = x; y2 = y1; y1 = y;
    const env = Math.min(1, u * 25) * Math.pow(1 - u, 1.3);
    put(sL, sR, i0 + k, (y * 2.2 + x * .15) * env * vel, pan);
  }
}
function rumble(t0, t1, vel = .18, f = 42) { const i0 = Math.floor(t0 * SR), L = Math.floor((t1 - t0) * SR); let ph = 0, a = 0; for (let k = 0; k < L; k++) { const u = k / L; ph += 2 * Math.PI * (f + 3 * Math.sin(k / SR * 7)) / SR; a += .02 * ((rnd() * 2 - 1) - a); const env = Math.min(1, u * (t1 - t0) * 2) * Math.min(1, (1 - u) * (t1 - t0) * 3); const saw = ((ph / (2 * Math.PI)) % 1) * 2 - 1; put(sL, sR, i0 + k, (saw * .5 + a * 3) * env * vel * (1 + .3 * Math.sin(k / SR * 2 * Math.PI * 9)), 0); } }
function ambience(t0, t1, kind, vel) { // wind / night crickets / city hum
  const i0 = Math.floor(t0 * SR), L = Math.floor((t1 - t0) * SR); let a = 0;
  for (let k = 0; k < L; k++) {
    const u = k / L, tt = k / SR; const env = Math.min(1, tt / 1.5) * Math.min(1, (L - k) / SR / 1.5);
    a += .01 * ((rnd() * 2 - 1) - a); let v = a * 4;
    if (kind === 'night') v = a * 2 + (Math.sin(2 * Math.PI * 4200 * tt) * (Math.sin(2 * Math.PI * 22 * tt) > .6 ? 1 : 0) * (Math.sin(2 * Math.PI * .7 * tt) > 0 ? 1 : 0)) * .08;
    put(sL, sR, i0 + k, v * env * vel * (1 + .3 * Math.sin(tt * .5)), Math.sin(tt * .2) * .3);
  }
}


function arp(t0, t1, bpm, chords, { vel = .16, oct = 0, pattern = [0, 1, 2, 1], inst = 'piano', bassVel = .16, padVel = .035, shake = false, step = .5 } = {}) {
  const beat = 60 / bpm, bar = beat * 4; let t = t0, ci = 0;
  while (t < t1 - .05) {
    const ch = chords[ci % chords.length].map(x => n(x) + oct * 12);
    if (padVel) pad(t, Math.min(t1, t + bar), ch.map(m => m - 12), padVel, .6, 1.2, .2);
    if (bassVel) bass(t, ch[0] - 24, bassVel, beat * 1.6), bass(t + beat * 2, ch[0] - 24, bassVel * .7, beat * 1.2);
    for (let s = 0; s < 4 / step; s++) {
      const tt = t + s * beat * step; if (tt >= t1) break;
      const note = ch[pattern[s % pattern.length] % ch.length] + (pattern[s % pattern.length] >= ch.length ? 12 : 0);
      const sw = (s % 2 ? beat * step * .08 : 0); const v = vel * (s % 2 ? .75 : 1) * (.9 + rnd() * .2);
      if (inst === 'piano') piano(tt + sw, note, v, beat * 1.5, (s % 2 ? .25 : -.25)); else pluck(tt + sw, note, v, (s % 2 ? .3 : -.3), inst === 'pizz' ? 14 : 9);
      if (shake && s % 2) shaker(tt + sw, .035);
    }
    t += bar; ci++;
  }
}


function reverb(L, R, mix = .22) {
  const combs = [1116, 1188, 1277, 1356, 1422, 1491].map(d => Math.floor(d * SR / 44100 * 1.6));
  for (const [buf, off] of [[L, 0], [R, 23]]) {
    const dry = Float32Array.from(buf); const wet = new Float32Array(N);
    for (const d0 of combs) { const d = d0 + off; const line = new Float32Array(d); let idx = 0, lp = 0; for (let i = 0; i < N; i++) { const y = line[idx]; lp = y * .65 + lp * .35; line[idx] = dry[i] + lp * .82; wet[i] += y; idx = (idx + 1) % d; } }
    for (const d0 of [556, 441, 341]) { const d = d0 + off; const line = new Float32Array(d); let idx = 0; for (let i = 0; i < N; i++) { const b = line[idx]; const x = wet[i]; const y = -x + b; line[idx] = x + b * .5; wet[i] = y; idx = (idx + 1) % d; } }
    for (let i = 0; i < N; i++) buf[i] = dry[i] * (1 - mix * .5) + wet[i] * mix * .12;
  }
}

module.exports = { SR, N, END, mL, mR, sL, sR, rnd, mtof, n, put, piano, pluck, pad, bass, kick, shaker, heartbeat, noiseBurst, whoosh, tone, pop, ding, click, tap, thud, plop, flap, buzz, tick, caw, rumble, ambience, arp, reverb, OUT };
