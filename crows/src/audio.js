// Original, royalty-free soundtrack synthesised in JS: score + SFX + ambience,
// auto-ducked under the (gently polished) voiceover, loudness-normalised to -14 LUFS.
//   node src/audio.js [path/to/voiceover.mp3]
const fs = require('fs'), path = require('path');
const { spawnSync } = require('child_process');
const { at, words, END } = require('./timing');

const SR = 44100, N = Math.ceil((END + 1) * SR);
const OUT = path.join(__dirname, '..', 'out'); fs.mkdirSync(OUT, { recursive: true });
const VO = process.argv[2] || path.join(__dirname, '..', 'voiceover.mp3');
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

// ---------------- the score (cue sheet) ----------------
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

const T = {
  title: at('so what if'), t7: at('7 in the morning'), sunset: at('sunset'), world: at('and around the world'), notice: at('then you notice'), seattle: at('researchers in seattle'),
  nf: at('a crow never forgets'), safe: at("you're safe"), quiet: at('then pip goes'), plan: at('the crows have a plan'), need: at('they need you'), t530: at('5:30'), tt: at('tap tap pip'), slow: at('time slows'),
  switchOff: at('you switch off'), never: at('the permit was never'), stays: at('the tree stays'), night2: at('that night the crows'), real: at('so how real'), tease: at('but tonight far'), out: at('what do you think'),
};
console.log('composing score...');
// 1. morning wonder
arp(0, 23.5, 88, [['C4', 'E4', 'G4', 'B4'], ['A3', 'C4', 'E4', 'G4'], ['F3', 'A3', 'C4', 'E4'], ['G3', 'B3', 'D4', 'G4']], { vel: .11, pattern: [0, 2, 1, 3, 2, 1, 3, 2], bassVel: .1, padVel: .03 });
// 2. curious science
arp(23.5, T.title - .2, 100, [['D4', 'F4', 'A4', 'C5'], ['G3', 'B3', 'D4', 'F4'], ['C4', 'E4', 'G4', 'B4'], ['A3', 'C4', 'E4', 'G4']], { vel: .12, inst: 'pluck', pattern: [0, 2, 1, 3, 2, 0, 3, 1], bassVel: .12, padVel: .025, shake: true });
// title hit
kick(T.title, .5); pad(T.title, T.t7 - .2, [n('C3'), n('G3'), n('E4'), n('B4')], .05, .2, 1.5, .5); for (let i = 0; i < 6; i++) pluck(T.title + .1 + i * .12, n('C6') + [0, 4, 7, 11, 12, 16][i], .06, (i % 2 ? .5 : -.5), 6);
// 3. playful day montage (with variation each hour)
arp(T.t7, T.sunset, 104, [['F4', 'A4', 'C5', 'E5'], ['C4', 'E4', 'G4', 'C5'], ['D4', 'F4', 'A4', 'C5'], ['Bb3', 'D4', 'F4', 'A4']], { vel: .11, inst: 'pluck', pattern: [0, 2, 3, 1, 2, 0, 3, 2], bassVel: .13, padVel: .02, shake: true });
// 4. roost wonder
pad(T.sunset, T.notice, [n('Eb3'), n('Bb3'), n('G4'), n('D5')], .06, 3, 2, .4);
arp(T.sunset + 2, T.notice, 70, [['Eb4', 'G4', 'Bb4', 'D5'], ['C4', 'Eb4', 'G4', 'Bb4'], ['Ab3', 'C4', 'Eb4', 'G4'], ['Bb3', 'D4', 'F4', 'Bb4']], { vel: .09, pattern: [0, 1, 2, 3], bassVel: .08, padVel: 0, step: 1 });
// 5. mystery / faces / Seattle (music-box)
pad(T.notice, T.safe, [n('A2'), n('E3'), n('C4')], .055, 2, 2, .2);
arp(T.notice, T.seattle, 76, [['A3', 'C4', 'E4'], ['F3', 'A3', 'C4']], { vel: .07, pattern: [0, 1, 2, 1], bassVel: 0, padVel: 0, step: 1 });
for (let t = T.seattle; t < T.nf; t += .42) pluck(t, n(['A5', 'E5', 'C6', 'B5', 'G5', 'E5'][Math.floor((t - T.seattle) / .42) % 6]), .045, .3, 5, .3);
arp(T.nf, T.safe, 76, [['A3', 'C4', 'E4', 'G4'], ['F3', 'A3', 'C4', 'E4'], ['D3', 'F3', 'A3', 'C4'], ['E3', 'G#3', 'B3', 'E4']], { vel: .08, pattern: [0, 2, 1, 3], bassVel: .1, padVel: 0, step: 1 });
// 6. tender: the peanut, Pip's thank you
arp(T.safe, T.quiet, 72, [['C4', 'E4', 'G4', 'C5'], ['B3', 'D4', 'G4', 'B4'], ['A3', 'C4', 'E4', 'A4'], ['F3', 'A3', 'C4', 'F4']], { vel: .11, pattern: [0, 1, 2, 3, 2, 1, 2, 3], bassVel: .09, padVel: .035 });
for (const [tt, m] of [[at('so thank you'), 'E5'], [at('so thank you') + .5, 'G5'], [at('so thank you') + 1.0, 'C6']]) piano(tt, n(m), .08, 2, .2);
// 7. the plan: tension ostinato, building
{ const bpm = 108, beat = 60 / bpm; const ch = [['D4', 'F4', 'A4'], ['Bb3', 'D4', 'F4'], ['G3', 'Bb3', 'D4'], ['A3', 'C#4', 'E4']]; let i = 0;
  pad(T.quiet, T.plan, [n('D3'), n('A3'), n('F4')], .05, 2, 1.5, .3);
  for (let t = T.plan; t < T.need - .1; t += beat / 2, i++) { const c = ch[Math.floor(i / 16) % 4]; const k = Math.min(1, (t - T.plan) / 18); pluck(t, n(c[i % 3]) + (i % 4 === 3 ? 12 : 0), .06 + .06 * k, (i % 2 ? .3 : -.3), 14); if (i % 8 === 0) bass(t, n(c[0]) - 24, .14 + .08 * k, beat * 3); if (k > .5 && i % 4 === 0) kick(t, .18 * k); }
  // "They need you." – suspended chord
  pad(T.need, T.t530, [n('D3'), n('G3'), n('A3'), n('D4')], .06, .3, 1, .3);
  for (let t = T.t530; t < T.tt; t += beat) { pluck(t, n('D3'), .08, 0, 12); if (Math.floor((t - T.t530) / beat) % 2 === 0) kick(t, .16); }
}
// 8. time slows: drone + clock + heartbeat (no melody)
pad(T.tt, T.switchOff, [n('D2'), n('A2'), n('D3')], .06, .5, 1, .1);
for (let t = T.slow; t < T.switchOff - .3; t += 1) { tick(t, .14); }
for (let t = T.slow + .3; t < T.switchOff - .3; t += 1.1) heartbeat(t, .26);
// 9. the stand: build → triumph on NOT SIGNED
{ const bpm = 96, beat = 60 / bpm; let i = 0;
  for (let t = T.switchOff + .5; t < T.never; t += beat / 2, i++) { const c = [['D4', 'F4', 'A4'], ['Bb3', 'D4', 'F4'], ['F3', 'A3', 'C4'], ['C4', 'E4', 'G4']][Math.floor(i / 8) % 4]; const k = Math.min(1, (t - T.switchOff) / 20); pluck(t, n(c[i % 3]), .05 + .07 * k, (i % 2 ? .3 : -.3), 12); if (i % 4 === 0) { bass(t, n(c[0]) - 24, .12 + .1 * k, beat * 1.8); kick(t, .12 + .2 * k); } if (i % 2) shaker(t, .03 * k); }
  // resolution
  kick(T.never + .7, .55); pad(T.never + .6, T.night2, [n('F3'), n('C4'), n('A4'), n('E5')], .07, .4, 2.5, .5);
  arp(T.stays - .2, T.night2, 92, [['F4', 'A4', 'C5', 'E5'], ['C4', 'E4', 'G4', 'C5']], { vel: .12, pattern: [0, 1, 2, 3, 2, 1, 2, 3], bassVel: .12, padVel: 0 });
}
// 10. town hall warmth + callback
arp(T.night2, T.real, 84, [['F4', 'A4', 'C5', 'E5'], ['D4', 'F4', 'A4', 'C5'], ['Bb3', 'D4', 'F4', 'A4'], ['C4', 'E4', 'G4', 'C5']], { vel: .11, pattern: [0, 2, 1, 3, 2, 1, 3, 2], bassVel: .11, padVel: .03 });
// 11. reality check: light curious
arp(T.real, T.tease, 100, [['D4', 'F4', 'A4', 'C5'], ['G3', 'B3', 'D4', 'F4'], ['C4', 'E4', 'G4', 'B4'], ['A3', 'C4', 'E4', 'G4']], { vel: .09, inst: 'pluck', pattern: [0, 2, 1, 3, 2, 0, 3, 1], bassVel: .1, padVel: .02, shake: true });
// 12. teaser: dark
pad(T.tease, T.out, [n('C2'), n('F#2'), n('C3')], .07, 1, 1, .1); for (let t = T.tease + 1; t < T.out; t += 2.2) piano(t, n('F#6'), .03, 1.5, .4);
// 13. outro: bright
arp(T.out, END, 112, [['C4', 'E4', 'G4', 'C5'], ['A3', 'C4', 'E4', 'A4'], ['F3', 'A3', 'C4', 'F4'], ['G3', 'B3', 'D4', 'G4']], { vel: .12, inst: 'pluck', pattern: [0, 2, 3, 1, 2, 0, 3, 2], bassVel: .13, padVel: .025, shake: true });
kick(T.out, .4);

// ---------------- SFX & ambience cue sheet ----------------
console.log('placing sfx...');
const A = (p, after = 0) => at(p, after);
ambience(0, 23.5, 'wind', .05); ambience(T.t7, T.sunset, 'wind', .035); ambience(T.notice, T.quiet + 12, 'night', .06); ambience(T.night2, T.real, 'night', .05); ambience(T.tease, T.out, 'night', .04);
rumble(.2, 3.8, .12, 38); noiseBurst(3.4, .9, .1, { lp: .5, fade: 3 }); // bus engine + air-brake hiss
flap(A('crow lands') - .9, 9, .1); caw(A('it speaks') - .1, .18, 1.05);
tick(A('you blink') + .15, .2); tick(A('the crow blinks back') + .35, .2);
noiseBurst(A('another one is eating'), .5, .1, { lp: .4, fade: 10 }); noiseBurst(A('another one is eating') + .5, .3, .1, { lp: .4, fade: 14 });
// cuts: whoosh into each new section
for (const p of ['it tilts', 'behind it', 'yesterday crows', 'a crow weighs', 'the gap closes', '7 in the morning', 'noon', 'dev your dispatcher', 'sunset', 'and around the world', 'then you notice', 'researchers in seattle', 'a crow never forgets', 'the man who threw', "you're safe", 'then pip goes', 'at dawn a developer', 'the crows have a plan', 'do the math', '5:30', 'tap tap pip', 'you look at the bus', 'you walk to the tree', 'that night the crows', 'so how real', 'and how smart', 'but tonight far', 'what do you think']) whoosh(A(p), .14);
for (const p of [['8', 60], ['9', 75], ['1', 110], ['3', 120], ['5', 130], ['6', 138]]) { whoosh(at(p[0], p[1]), .14); ding(at(p[0], p[1]) + .05, .05, 1760); }
// science board pops & dings
for (const p of ['a crow weighs', 'size of a walnut', 'yours about', '86 billion']) pop(A(p) + .4, .12);
ding(A('overnight') + .2, .1, 1568);
for (const p of ['no hands', 'just a beak', 'two feet', 'two wings']) pop(A(p), .12, p === 'no hands' ? 300 : 800);
thud(A("that's the rule"), .4);
// day montage
click(A('your bins stay') + .3, .3); click(A('your bins stay') + .45, .25);
noiseBurst(A('file a complaint'), 1.1, .04, { lp: .6, fade: 1.5 }); // pen scribble
ding(A('8', 60) + .3, .08, 2093); // cafe door bell
caw(A('copy a few') + .2, .1, 1.1, -.3, .25); pop(A('orders your') + .2, .1); pop(A('asks for a receipt'), .1);
for (let i = 0; i < 5; i++) click(A('bend twigs') + .3 + i * .2, .12);
click(A('this morning a crow') + 1, .2); noiseBurst(A('and opens the park') + .4, .8, .08, { lp: .03, shape: 'swell' }); // door creak
flap(A('and opens the park') - .4, 6, .08);
for (let i = 0; i < 6; i++) plop(A('crows once drop') + .4 + i * .55, .12); for (let i = 0; i < 6; i++) plop(A('today one drops') + .2 + i * .55, .14);
for (let i = 0; i < 40; i++) noiseBurst(A('applause') + i * .03 + rnd() * .1, .03, .06, { lp: .6, fade: 120, pan: rnd() * 2 - 1 });
caw(A('are they') + .1, .14, 1, .4);
for (let i = 0; i < 8; i++) pop(A('in 2014') + .6 + i * .32, .07, 600 + i * 80);
flap(A('today a crow solves') + .3, 10, .06);
for (let i = 0; i < 23; i++) tick(A('the crows count') + i * .17, .08);
thud(A('late 11'), .3);
noiseBurst(A('then it sighs') + .2, .9, .07, { lp: .05, shape: 'swell' });
caw(A('the next green') - .1, .2, 1.15, .5, .45); ding(A('the next green') + .2, .06, 880);
// roost
for (let i = 0; i < 30; i++) caw(T.sunset + 1 + rnd() * 14, .03 + rnd() * .03, .85 + rnd() * .4, rnd() * 1.6 - .8, .25 + rnd() * .2);
flap(A('tonight the roost'), 20, .05, .06);
caw(A('a town hall') + .1, .1, .9, .2);
for (const p of ['every city', 'every rooftop', 'every wire']) whoosh(A(p), .1, .35);
tone(A('your face too'), 1200, .5, .06, { decay: 4, f2: 1210 });
// Seattle
for (let i = 0; i < 10; i++) caw(A('years later') + .3 + i * .28, .08 + rnd() * .04, .9 + rnd() * .3, rnd() * 1.4 - .7, .3);
for (const p of ['the man who threw', 'the kid who chased']) noiseBurst(A(p), .25, .1, { lp: .3, fade: 18 });
thud(A('no not one'), .45);
// peanut / Pip
tap(A('tap', A('you tap it twice') + .5), .35); tap(A('tap', A('tap', A('you tap it twice') + .5) + .1), .35);
flap(A('one crow always comes'), 10, .08); ding(A('pip', A('one crow always comes')), .06, 1568);
caw(A('you fed us') - .3, .06, 1.2, .3, .2);
// the plan
noiseBurst(A('to cut it down') + .2, 1.2, .07, { lp: .3, shape: 'flat' }); // saw hint
// 5:30 crew
rumble(A('the crew arrives'), A('your phone buzzes') + 1, .16, 40);
buzz(A('your phone buzzes') + .1); buzz(A('your phone buzzes') + 1.1);
tap(A('tap tap pip'), .45); tap(A('tap tap pip') + .35, .45);
// switch off, walk, stand
click(A('you switch off') + .5, .4); rumble(A('you switch off') - 1, A('you switch off') + .7, .08, 36);
for (let i = 0; i < 9; i++) noiseBurst(A('you walk to the tree') + i * .38, .05, .1, { lp: .2, fade: 60 });
noiseBurst(A('victor waves') + .1, .5, .06, { lp: .5, fade: 8 });
rumble(A('you walk to the tree'), A('engines stop'), .07, 44);
noiseBurst(A('then a crow drops') + .3, .7, .06, { lp: .5, shape: 'swell' }); flap(A('then a crow drops'), 8, .07);
for (let i = 0; i < 7; i++) noiseBurst(A('dev comes running') + i * .22, .05, .12, { lp: .2, fade: 60 });
noiseBurst(A('then he reads them again'), .4, .06, { lp: .5, fade: 8 });
thud(T.never + .7, .5);
for (let i = 0; i < 25; i++) caw(T.stays + rnd() * 3, .03 + rnd() * .04, .9 + rnd() * .4, rnd() * 1.6 - .8, .25);
// town hall + reality
for (const p of ['crows keep the roost', 'people keep the sidewalks', 'dev keeps your shift']) ding(A(p) + .1, .06, 1318);
pop(A('barely'), .1, 400);
for (const p of ['crows really bend', 'they really remember', 'some even copy']) ding(A(p) + .2, .06, 1568);
pop(A('but a walnut'), .1, 300); thud(A('impossible'), .4);
// teaser
tone(A('else opens its eyes') + .2, 90, 2.5, .2, { decay: .8, f2: 70 }); noiseBurst(A('quietly patiently'), 1.5, .03, { lp: .9, hp: .9, shape: 'swell' });
// outro
pop(A('tell us in the'), .1); click(A('hit like') + .5, .3); click(A('subscribe', 368) + .5, .3); ding(A('subscribe', 368) + .7, .1, 1760); ding(A('subscribe', 368) + .9, .08, 2349);
caw(END - 1.3, .2, 1, -.2, .5);

// ---------------- reverb on music (soft room) ----------------
console.log('reverb...');
function reverb(L, R, mix = .22) {
  const combs = [1116, 1188, 1277, 1356, 1422, 1491].map(d => Math.floor(d * SR / 44100 * 1.6));
  for (const [buf, off] of [[L, 0], [R, 23]]) {
    const dry = Float32Array.from(buf); const wet = new Float32Array(N);
    for (const d0 of combs) { const d = d0 + off; const line = new Float32Array(d); let idx = 0, lp = 0; for (let i = 0; i < N; i++) { const y = line[idx]; lp = y * .65 + lp * .35; line[idx] = dry[i] + lp * .82; wet[i] += y; idx = (idx + 1) % d; } }
    for (const d0 of [556, 441, 341]) { const d = d0 + off; const line = new Float32Array(d); let idx = 0; for (let i = 0; i < N; i++) { const b = line[idx]; const x = wet[i]; const y = -x + b; line[idx] = x + b * .5; wet[i] = y; idx = (idx + 1) % d; } }
    for (let i = 0; i < N; i++) buf[i] = dry[i] * (1 - mix * .5) + wet[i] * mix * .12;
  }
}
reverb(mL, mR, .3); reverb(sL, sR, .12);

// ---------------- voice: decode, measure envelope for ducking ----------------
console.log('voice envelope...');
const raw = spawnSync('ffmpeg', ['-loglevel', 'error', '-i', VO, '-ac', '1', '-ar', String(SR), '-f', 'f32le', '-'], { maxBuffer: 1 << 30 }).stdout;
const vo = new Float32Array(raw.buffer, raw.byteOffset, raw.length / 4);
const duck = new Float32Array(N); { let env = 0; const att = Math.exp(-1 / (.03 * SR)), rel = Math.exp(-1 / (.45 * SR)); let g = 1;
  for (let i = 0; i < N; i++) { const x = i < vo.length ? Math.abs(vo[i]) : 0; env = x > env ? x : env * .9995; const target = env > .02 ? .42 : 1; g = target < g ? target + (g - target) * att : target + (g - target) * rel; duck[i] = g; } }

// ---------------- mixdown of music + sfx bed ----------------
console.log('mixdown...');
const out = Buffer.alloc(N * 8);
for (let i = 0; i < N; i++) {
  const t = i / SR; const fadeOut = t > END - .4 ? Math.max(0, (END + .6 - t)) : 1;
  let l = (mL[i] * .9 * duck[i] + sL[i] * .85) * fadeOut, r = (mR[i] * .9 * duck[i] + sR[i] * .85) * fadeOut;
  l = Math.tanh(l * 1.2) / 1.2; r = Math.tanh(r * 1.2) / 1.2;
  out.writeFloatLE(l, i * 8); out.writeFloatLE(r, i * 8 + 4);
}
const bed = path.join(OUT, 'bed.f32'); fs.writeFileSync(bed, out);
// voice polish (soft + warm) and final loudness
const vchain = 'highpass=f=80,lowpass=f=14500,equalizer=f=180:t=q:w=1:g=2,equalizer=f=3200:t=q:w=1.4:g=-2,equalizer=f=7000:t=q:w=2:g=-2.5,deesser=i=0.35,acompressor=threshold=-21dB:ratio=2.5:attack=10:release=150:makeup=2,aecho=0.85:0.6:38|61:0.10|0.06';
const r = spawnSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', VO, '-f', 'f32le', '-ar', String(SR), '-ac', '2', '-i', bed,
  '-filter_complex', `[0:a]aresample=${SR},${vchain},pan=stereo|c0=c0|c1=c0[v];[1:a]volume=0.9[b];[v][b]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11[o]`,
  '-map', '[o]', '-ar', String(SR), '-t', String(END + .5), path.join(OUT, 'mix.wav')], { stdio: 'inherit' });
fs.unlinkSync(bed);
console.log(r.status === 0 ? 'wrote out/mix.wav' : 'ffmpeg failed');
