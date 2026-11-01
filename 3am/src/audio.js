// 3AM Thoughts soundtrack: soft piano theme + comic day SFX + quiet night SFX. No voice.
const fs = require('fs'), path = require('path');
const { spawnSync } = require('child_process');
const A = require('./audio_base');
const T = require('./tl');
const { SR, N, END, mL, mR, sL, sR, rnd, n, put, piano, pluck, pad, bass, kick, shaker, heartbeat, noiseBurst, whoosh, tone, pop, ding, click, tap, thud, tick, rumble, arp, reverb, OUT } = A;

// ---------------- extra SFX ----------------
function voiceBurst(t, f0, dur, vel, pan = 0, fc = 900, glide = -.25) { // a "ha" / "woo" syllable
  const i0 = Math.floor(t * SR), len = Math.floor(dur * SR); let ph = 0; const q = 2.5, w0 = 2 * Math.PI * fc / SR, al = Math.sin(w0) / (2 * q); const b0 = al, a0 = 1 + al, a1 = -2 * Math.cos(w0), a2 = 1 - al;
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  for (let k = 0; k < len; k++) { const u = k / len; const f = f0 * (1 + glide * u); ph += 2 * Math.PI * f / SR; let x = ((ph / (2 * Math.PI)) % 1) * 2 - 1 + (rnd() * 2 - 1) * .35;
    const y = (b0 * x - b0 * x2 - a1 * y1 - a2 * y2) / a0; x2 = x1; x1 = x; y2 = y1; y1 = y; const env = Math.min(1, u * 18) * Math.pow(1 - u, 1.5); put(sL, sR, i0 + k, (y * 2 + x * .08) * env * vel, pan); }
}
function laughter(t0, t1, voices = 8, vel = .05) { for (let v = 0; v < voices; v++) { const f0 = 180 + rnd() * 220, pan = rnd() * 1.6 - .8, rate = .15 + rnd() * .06; for (let t = t0 + rnd() * .3; t < t1; t += rate * (.85 + rnd() * .3)) { const fade = Math.min(1, (t1 - t) / 1.2); voiceBurst(t, f0 * (1 + rnd() * .1), .11, vel * fade * (.6 + rnd() * .5), pan, 700 + rnd() * 600); } } }
function giggle(t, vel = .06) { for (let i = 0; i < 4; i++) voiceBurst(t + i * .13, 330 + i * 10, .09, vel, .4, 1200); }
function chatter(t0, t1, vel = .02) { for (let t = t0; t < t1; t += .07 + rnd() * .08) voiceBurst(t, 140 + rnd() * 160, .1 + rnd() * .12, vel * (.5 + rnd() * .6), rnd() * 1.8 - .9, 500 + rnd() * 900, (rnd() - .5) * .4); }
function crowdRoar(t0, t1, vel = .14) { noiseBurst(t0, t1 - t0, vel, { shape: 'swell', sweep: u => .05 + .12 * Math.sin(Math.PI * u) }); for (let i = 0; i < 220; i++) { const t = t0 + rnd() * (t1 - t0); noiseBurst(t, .03, vel * .5, { lp: .6, fade: 140, pan: rnd() * 2 - 1 }); } for (let i = 0; i < 26; i++) voiceBurst(t0 + rnd() * (t1 - t0 - .6), 300 + rnd() * 200, .5, vel * .35, rnd() * 1.6 - .8, 900, .3); }
function engine(t0, t1, vel = .16) { const i0 = Math.floor(t0 * SR), L = Math.floor((t1 - t0) * SR); let ph = 0, lp = 0; for (let k = 0; k < L; k++) { const u = k / L; const f = 38 + 90 * Math.pow(Math.sin(u * Math.PI * .5), 2) + 6 * Math.sin(k / SR * 30); ph += 2 * Math.PI * f / SR; const saw = ((ph / (2 * Math.PI)) % 1) * 2 - 1; lp += .08 * (saw - lp); const env = Math.min(1, u * 8) * Math.min(1, (1 - u) * 5); put(sL, sR, i0 + k, lp * env * vel * 2.2, .2); } }
function ringtone(t0, t1, vel = .12) { const pat = ['E5', 'G5', 'C6', 'G5', 'E5', 'G5', 'C6', 'D6']; for (let t = t0, k = 0; t < t1; k++) { const i = k % 10; if (i < 8) pluck(t, n(pat[i]), vel, .1, 7, 1.4); t += i === 7 ? .9 : .14; if (i === 9) t += 0; } }
function rainAmb(t0, t1, vel = .06) { const i0 = Math.floor(t0 * SR), L = Math.floor((t1 - t0) * SR); let a = 0, b = 0; for (let k = 0; k < L; k++) { const w = rnd() * 2 - 1; a += .35 * (w - a); b += .02 * (a - b); const hp = a - b; const env = Math.min(1, k / SR / 1.2) * Math.min(1, (L - k) / SR / 1.2); put(sL, sR, i0 + k, hp * env * vel * 1.6, (rnd() - .5) * .6); } for (let t = t0; t < t1; t += .05 + rnd() * .2) tone(t, 1800 + rnd() * 2500, .03, vel * .25, { decay: 120, pan: rnd() * 2 - 1 }); }
function screech(t0, dur, vel = .1) { const i0 = Math.floor(t0 * SR), L = Math.floor(dur * SR); let ph = 0; for (let k = 0; k < L; k++) { const u = k / L; const f = 2400 * Math.pow(.15, u) + 300 * Math.sin(k / SR * 40); ph += 2 * Math.PI * f / SR; put(sL, sR, i0 + k, (Math.sin(ph) * .5 + (rnd() * 2 - 1) * .4) * Math.sin(Math.PI * u) * vel, 0); } }
function hum(t0, t1, vel = .03) { const i0 = Math.floor(t0 * SR), L = Math.floor((t1 - t0) * SR); for (let k = 0; k < L; k++) { const tt = k / SR; const env = Math.min(1, tt / .3) * Math.min(1, (L - k) / SR / .5); put(sL, sR, i0 + k, (Math.sin(2 * Math.PI * 60 * tt) + .5 * Math.sin(2 * Math.PI * 120 * tt) + .2 * Math.sin(2 * Math.PI * 180 * tt)) * env * vel, 0); } }
function breath(t, vel = .07) { noiseBurst(t, 1.3, vel, { shape: 'swell', sweep: u => .04 + .08 * u, pan: -.05 }); noiseBurst(t + 1.4, 1.5, vel * .8, { shape: 'swell', sweep: u => .1 - .07 * u, pan: .05 }); }
function penScratch(t, dur, vel = .04) { for (let x = 0; x < dur; x += .045 + rnd() * .03) noiseBurst(t + x, .035, vel * (.6 + rnd() * .5), { lp: .9, hp: .6, fade: 60 }); }
function alarmBeeps(t0, t1, vel = .08) { for (let t = t0; t < t1; t += .5) for (let k = 0; k < 4; k++) tone(t + k * .09, 2100, .06, vel, { decay: 6, type: 'square' }); }
function boing(t, vel = .12) { tone(t, 220, .5, vel, { decay: 5, f2: 520 }); tone(t, 330, .4, vel * .5, { decay: 7, f2: 780 }); }
function steps(t0, t1, rate, vel = .1) { for (let t = t0; t < t1; t += rate) noiseBurst(t, .05, vel * (.8 + rnd() * .3), { lp: .25, fade: 60, pan: (rnd() - .5) * .3 }); }
function wetSteps(t0, t1, rate, vel = .08) { for (let t = t0; t < t1; t += rate) { noiseBurst(t, .09, vel, { lp: .5, fade: 30 }); } }
function cricket(t0, t1, vel = .04) { for (let t = t0; t < t1; t += .62) for (let k = 0; k < 3; k++) tone(t + k * .05, 4400, .035, vel, { decay: 40, pan: .5 }); }
function scratchRec(t, vel = .14) { const i0 = Math.floor(t * SR), L = Math.floor(.35 * SR); let lp = 0; for (let k = 0; k < L; k++) { const u = k / L; const c = .05 + .4 * Math.abs(Math.sin(u * 9)); lp += c * ((rnd() * 2 - 1) - lp); put(sL, sR, i0 + k, lp * Math.sin(Math.PI * u) * vel * 2, 0); } }
function hiss(t, dur = .7, vel = .1) { noiseBurst(t, dur, vel, { lp: .9, hp: .7, shape: 'exp', fade: 4 }); }
function thunder(t, vel = .3) { noiseBurst(t, .25, vel, { lp: .5, fade: 12 }); rumble(t, t + 3, vel * .6, 34); noiseBurst(t + .1, 2.8, vel * .5, { lp: .03, fade: 1.2 }); }
function typing(t0, t1, vel = .05) { for (let t = t0; t < t1; t += 1 / 9 + (rnd() - .5) * .03) { tone(t, 1600 + rnd() * 300, .03, vel, { decay: 120 }); noiseBurst(t, .015, vel * .6, { lp: .8, fade: 300 }); } }
function bubbleBlip(t, vel = .05) { tone(t, 600, .08, vel, { decay: 40, f2: 900 }); }
function gulp(t, vel = .12) { for (let i = 0; i < 3; i++) tone(t + i * .32, 180, .14, vel, { decay: 20, f2: 90 }); }
function tapeStop(t, vel = .1) { tone(t, 330, .6, vel, { decay: 3, f2: 40 }); }

// ---------------- music ----------------
const THEME = ['E5', 'G5', 'A5', 'G5', 'E5', 'D5', 'C5', 'D5'];
const PROG = [['A3', 'C4', 'E4'], ['F3', 'A3', 'C4'], ['C4', 'E4', 'G4'], ['G3', 'B3', 'D4']];
function theme(t0, t1, { bpm = 66, vel = .1, melody = true, oct = 0, padV = .03 } = {}) {
  const beat = 60 / bpm; let bar = 0;
  for (let t = t0; t < t1 - .2; t += beat * 4, bar++) { const ch = PROG[bar % 4].map(x => n(x) + oct * 12); bass(t, ch[0] - 12, vel * .6, beat * 3.5);
    if (padV) pad(t, Math.min(t1, t + beat * 4), ch.map(m => m - 12), padV, 1.2, 2, .15);
    for (let s = 0; s < 4; s++) { const tt = t + s * beat; if (tt >= t1) break; piano(tt, ch[[0, 2, 1, 2][s]], vel * .55, beat * 1.4, -.25); }
    if (melody) { const m1 = THEME[(bar * 2) % 8], m2 = THEME[(bar * 2 + 1) % 8]; if (t < t1 - .2) piano(t + beat * .02, n(m1) + oct * 12, vel, beat * 2, .2); if (t + beat * 2 < t1 - .2) piano(t + beat * 2, n(m2) + oct * 12, vel * .85, beat * 2, .2); } }
}
function quirky(t0, t1, bpm = 140, vel = .09) { arp(t0, t1, bpm, [['C4', 'E4', 'G4', 'C5'], ['A3', 'C4', 'E4', 'A4'], ['F3', 'A3', 'C4', 'F4'], ['G3', 'B3', 'D4', 'G4']], { vel, inst: 'pizz', pattern: [0, 2, 1, 3, 2, 0, 3, 1], bassVel: .12, padVel: 0, shake: true });
  const beat = 60 / bpm; for (let t = t0; t < t1 - .05; t += beat) kick(t, (Math.round((t - t0) / beat) % 2 ? .07 : .14)); }

console.log('composing...');
// COLD OPEN: heartbeat, one low note, tape rewind
for (let t = .3; t < T.rew; t += .95) heartbeat(t, .3);
piano(.2, n('A2'), .16, 4, 0); piano(T.coldQ, n('E3'), .08, 3, .2);
screech(T.rew, 2.4, .08); for (let i = 0; i < 18; i++) tick(T.rew + i * .13, .06);
whoosh(T.toDay + .1, .2, .6);

// THE DAY
alarmBeeps(T.alarm, T.jump, .07);
pluck(T.wake, n('C6'), .1, 0, 6); pluck(T.wake + .12, n('G5'), .08, 0, 6);
quirky(T.jump, T.trip, 150, .1); steps(T.jump + .3, T.trip, .17, .1);
thud(T.fall, .6); boing(T.fall + .3, .08);
quirky(T.hop, T.doors, 150, .09);
for (let t = T.hop; t < T.toastS; t += .222) noiseBurst(t, .06, .08, { lp: .3, fade: 50 }); // hops
noiseBurst(T.hop + .2, 3.5, .03, { lp: .9, hp: .8, shape: 'flat' }); // brushing
noiseBurst(T.toastS, 2.5, .03, { lp: .9, hp: .8, shape: 'flat' }); boing(T.burn, .1); pop(T.burn + .05, .12, 500);
noiseBurst(T.spill, .4, .2, { lp: .3, fade: 10 }); scratchRec(T.spill + .05, .06);
steps(T.run, T.doors, .14, .1);
hiss(T.doors, .6, .14); thud(T.doors + .2, .25); scratchRec(T.doors + .15, .12);
rumble(T.drive, T.rain + 1, .14, 40); engine(T.drive, T.rain + .4, .1);
thunder(T.thunder, .3); rainAmb(T.rain, T.cls + .5, .05);
piano(T.ofc, n('A3'), .1, 3, -.1); piano(T.ofc, n('C4'), .08, 3, .1); piano(T.ofc + .5, n('E4'), .07, 3, .2);
// class
tone(T.enter + .5, 2900, .35, .025, { decay: 4, f2: 3150 }); tone(T.enter + 1, 3100, .25, .02, { decay: 5, f2: 2850 }); // chalk squeak
for (let t = T.enter; t < T.blank; t += .5) tick(t, .05);
for (let t = T.front; t < T.blank; t += 60 / 100 / 2) pluck(t, n(['A3', 'C4', 'E4', 'C4'][Math.floor((t - T.front) / .3) % 4]), .05, 0, 14);
tone(T.blank, 4200, 3, .02, { decay: .3 }); // tinnitus blank
giggle(T.giggle, .12); laughter(T.laugh, T.lunch - .2, 12, .085); thud(T.laugh, .2);
// lunch alone
chatter(T.lwalk, T.crushS - .3, .026);
for (let i = 0; i < 6; i++) piano(T.lwalk + .2 + i * 1.3, n(['E5', 'D5', 'C5', 'B4', 'A4', 'B4'][i]), .06, 1.8, .2);
pad(T.lwalk, T.crushS, [n('A2'), n('E3'), n('C4')], .025, 1.5, 1.5, .1);
ding(T.ping, .07, 1760); ding(T.ping + .12, .05, 2349);
// crush
arp(T.approach, T.reveal, 100, [['C4', 'E4', 'G4', 'C5'], ['F3', 'A3', 'C4', 'F4']], { vel: .07, inst: 'pluck', pattern: [0, 2, 1, 3], bassVel: .07, padVel: .02 });
pluck(T.wave, n('E6'), .06, .3, 6); pluck(T.waveBack, n('G6'), .06, .3, 6);
scratchRec(T.reveal, .1); cricket(T.reveal + .6, T.cafe - .2, .03);
piano(T.drop, n('C4'), .06, 2, 0); piano(T.drop + .8, n('B3'), .05, 2, 0); piano(T.drop + 1.6, n('A3'), .05, 2.5, 0);
// cafe
arp(T.cafe, T.pause, 96, [['D4', 'F#4', 'A4', 'C#5'], ['B3', 'D4', 'F#4', 'A4'], ['E4', 'G4', 'B4', 'D5'], ['A3', 'C#4', 'E4', 'G4']], { vel: .07, inst: 'pluck', pattern: [0, 2, 1, 3, 2, 1, 3, 2], bassVel: .1, padVel: .015, shake: true });
chatter(T.cafe, T.call, .008); scratchRec(T.pause, .16); cricket(T.pause + .4, T.speed, .04);
quirky(T.speed, T.bell, 170, .08); steps(T.speed, T.bell, .11, .09);
ding(T.bell, .08, 2637); ding(T.bell + .1, .06, 3136);
// Mom calls
rainAmb(T.call, T.night - .4, .06); ringtone(T.ring, T.decline, .1);
tone(T.decline, 620, .25, .1, { decay: 8, type: 'square' }); tone(T.decline + .15, 440, .3, .1, { decay: 8, type: 'square' });
bubbleBlip(T.momText, .06); piano(T.notnow + .2, n('A3'), .06, 3, 0); piano(T.momText + .4, n('E4'), .05, 3, .2);
// walk home: the main theme, first time (title)
theme(T.street, T.doorShut + 1, { bpm: 64, vel: .09, padV: .03 });
wetSteps(T.street + .3, T.doorShut, .63, .05);
thud(T.doorShut, .35); click(T.doorShut + .1, .2);
wetSteps(T.doorShut + .3, T.flop - .2, .5, .05);
thud(T.flop + .25, .45); noiseBurst(T.flop + .25, .5, .1, { lp: .08, fade: 8 });

// THE NIGHT
for (let t = T.night + .5; t < T.math; t += 1) tick(t, .05);
tone(T.eyesPOV, 1700, .6, .06, { decay: 6 }); tone(T.eyesPOV + .08, 2550, .5, .04, { decay: 7 }); // screen ting
piano(T.notAgain, n('A2'), .08, 4, 0);
for (let t = T.math; t < T.replay; t += .5) tick(t, .05); for (let i = 0; i < 12; i++) tick(T.jump319 - .8 + i * .066, .08);
piano(T.sleepEq, n('C3'), .08, 3, 0); piano(T.sleepEq, n('Eb3'), .06, 3, 0);
// replay
for (const [rt, k] of [[T.r1, 0], [T.r2, 1], [T.r3, 2]]) { pop(rt, .14, 500 - k * 60); piano(rt + .1, n(['E4', 'Eb4', 'D4'][k]), .06, 3, 0); piano(rt + .1, n('A2'), .07, 4, 0); }
for (let t = T.r1, i = 0; t < T.song; i++) { heartbeat(t, .14 + i * .012); t += Math.max(.55, 1.1 - i * .035); }
// one song
click(T.play, .3); tone(T.play + .05, 1200, .05, .05, { decay: 60 });
theme(T.play + .3, T.cheer - .6, { bpm: 72, vel: .08, padV: .035 });
// imagination
noiseBurst(T.cheer - .9, .9, .14, { shape: 'swell', sweep: u => .02 + .3 * u }); kick(T.cheer, .5);
theme(T.cheer, T.real, { bpm: 96, vel: .11, oct: 0, padV: .05 }); for (let t = T.cheer; t < T.real; t += 60 / 96) kick(t, .16);
crowdRoar(T.cheer, T.car + .5, .12);
engine(T.car, T.house, .14); ding(T.house + .2, .05, 2093); ding(T.crush2 + .3, .05, 2637); ding(T.crush2 + .5, .04, 3136);
theme(T.real, T.skip, { bpm: 96, vel: .045, padV: 0 });
for (let t = T.real; t < T.skip; t += .11) noiseBurst(t, .04, .06, { lp: .15, fade: 60 }); // blanket drumming
scratchRec(T.skip, .18); tapeStop(T.skip, .06);
// drift
for (let i = 0; i < 6; i++) { const t = T.drift + .4 + i * 1.3; piano(t, n(['E4', 'G4', 'A4', 'G4', 'E4', 'D4'][i]), .05, 2.5, 0); }
pad(T.drift, T.dark, [n('F3'), n('A3'), n('C4'), n('E4')], .03, 2, 1, .2);
for (let t = T.hover, i = 0; t < T.dark; i++) { heartbeat(t, .16 + i * .02); t += Math.max(.5, .95 - i * .05); }
tapeStop(T.dark, .05);
piano(T.empty, n('A2'), .06, 2, 0); piano(T.guilty, n('G2'), .06, 2, 0); piano(T.awake, n('F2'), .06, 3, 0);
pad(T.pull + .4, T.storm, [n('C4'), n('E4'), n('G4')], .035, .5, 1, .3); piano(T.pull + .5, n('C5'), .07, 2, .2);
// storm
for (let t = T.storm, i = 0; t < T.dies; i++) { heartbeat(t, Math.min(.4, .2 + i * .01)); t += Math.max(.38, .8 - i * .02); }
{ const r = (a, b) => a + rnd() * (b - a); let tt = T.storm - .6 + 1; let i = 0; while (tt < T.feed + .2 && i < 140) { pop(tt, .07, r(380, 900)); const gap = Math.max(.12, 1.9 * Math.pow(.86, i)) / 1.4; tt += gap; i++; } }
{ let tt = T.flood - 12 + 1; let i = 0; while (tt < T.dies && i < 140) { if (tt > T.flood) pop(tt, .06, 300 + rnd() * 700); const gap = Math.max(.12, 1.9 * Math.pow(.86, i)) / 2.6; tt += gap; i++; } }
for (const tt of [T.f1, T.f2]) whoosh(tt + .3, .08, .3);
for (let k = 0; k < 2; k++) tone(T.battery + k * .3, 880, .18, .08, { decay: 6, type: 'tri' });
thud(T.why, .35); piano(T.why, n('C2'), .12, 3, 0); piano(T.why, n('F#2'), .1, 3, 0);
for (let t = T.storm; t < T.dies; t += 60 / 120 / 2) { const k = (t - T.storm) / (T.dies - T.storm); pluck(t, n(['D3', 'Eb3'][Math.floor((t - T.storm) * 4) % 2]), .04 + .06 * k, 0, 12, .5); }
noiseBurst(T.flood, T.dies - T.flood, .08, { shape: 'swell', sweep: u => .02 + .2 * u });
// phone dies
tone(T.dieClick - .4, 520, .3, .06, { decay: 8, f2: 260 }); click(T.dieClick, .45);
breath(T.br1, .08); breath(T.br2, .075); breath(T.br3, .07);
// fridge
steps(T.fridge + .3, T.toe, .55, .06); thud(T.toe, .45); boing(T.toe + .05, .06);
steps(T.toe + 1.8, T.open - .2, .55, .06);
click(T.open, .3); noiseBurst(T.open + .02, .3, .08, { lp: .2, fade: 12 }); hum(T.open, T.list + .3, .02);
tone(T.glass, 2600, .4, .03, { decay: 10 }); gulp(T.gulp, .1);
for (let i = 0; i < 3; i++) pop(T.chips + i * .5, .07, 700 + i * 120);
piano(T.chips + .3, n('C5'), .06, 3, .2); piano(T.chips + .3, n('E4'), .05, 3, -.2);
// list
for (const tt of [T.today, T.l1, T.l2, T.l3, T.l4, T.bad, T.bad + 1]) penScratch(tt, .7, .05);
penScratch(T.underline, .6, .06);
piano(T.bad, n('C4'), .1, 4, 0); piano(T.bad, n('E4'), .08, 4, 0); piano(T.bad, n('G4'), .07, 4, 0); piano(T.bad + 1, n('C5'), .09, 4, .2);
theme(T.shrink, T.callback, { bpm: 64, vel: .07, padV: .03, melody: false });
// callback
click(T.callback + .2, .15); tone(T.openChat, 1400, .05, .04, { decay: 60 });
typing(T.typeS, T.sent - .4, .04); whoosh(T.sent + .15, .12, .35); tone(T.sent + .1, 1500, .12, .05, { decay: 20, f2: 2100 });
for (let t = T.typing; t < T.reply; t += .45) bubbleBlip(t, .03);
ding(T.reply, .08, 1568); ding(T.reply + .14, .06, 2093);
theme(T.typeS, T.next + .5, { bpm: 64, vel: .085, padV: .035 });
// next night
for (let t = T.next + .5; t < T.flip; t += 1) tick(t, .05);
piano(T.remember, n('A2'), .07, 3, 0); piano(T.remember, n('Eb3'), .05, 3, 0);
pop(T.smirk + .5, .12, 900);
noiseBurst(T.flip, .5, .08, { lp: .06, shape: 'swell' });
piano(T.notTonight, n('C4'), .09, 5, -.2); piano(T.notTonight, n('G4'), .07, 5, 0); piano(T.notTonight + .3, n('E5'), .08, 5, .2);
// end card
theme(T.c1 - .3, T.END - 1.5, { bpm: 60, vel: .08, padV: .03 });
piano(T.END - 2.5, n('A3'), .07, 5, -.2); piano(T.END - 2.5, n('C4'), .06, 5, 0); piano(T.END - 2.5, n('E4'), .06, 5, .2);

console.log('reverb...');
reverb(mL, mR, .35); reverb(sL, sR, .12);

console.log('mixdown...');
const out = Buffer.alloc(N * 8);
for (let i = 0; i < N; i++) { const t = i / SR; const fo = t > END - 1.2 ? Math.max(0, (END - t) / 1.2) : 1;
  let l = (mL[i] * .95 + sL[i] * .9) * fo, r = (mR[i] * .95 + sR[i] * .9) * fo; l = Math.tanh(l * 1.15) / 1.15; r = Math.tanh(r * 1.15) / 1.15;
  out.writeFloatLE(l, i * 8); out.writeFloatLE(r, i * 8 + 4); }
const raw = path.join(OUT, 'mix.f32'); fs.writeFileSync(raw, out);
// two-pass loudness normalisation (linear, keeps the quiet moments quiet)
const inArgs = ['-f', 'f32le', '-ar', String(SR), '-ac', '2', '-i', raw];
const p1 = spawnSync('ffmpeg', ['-hide_banner', ...inArgs, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=18:print_format=json', '-f', 'null', '-'], { encoding: 'utf8' });
const m = JSON.parse(p1.stderr.slice(p1.stderr.lastIndexOf('{'), p1.stderr.lastIndexOf('}') + 1));
console.log('measured', m.input_i, 'LUFS, TP', m.input_tp);
const ln = `loudnorm=I=-16:TP=-1.5:LRA=18:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`;
const r2 = spawnSync('ffmpeg', ['-loglevel', 'error', '-y', ...inArgs, '-af', ln + ',aresample=44100', '-t', String(END + .5), path.join(OUT, 'mix.wav')], { stdio: 'inherit' });
fs.unlinkSync(raw);
console.log(r2.status === 0 ? 'wrote out/mix.wav' : 'ffmpeg failed');
