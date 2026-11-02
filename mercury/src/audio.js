// Original space score + SFX, ducked under the (gently polished) voiceover, normalised to -14 LUFS.
//   node src/audio.js [path/to/voiceover.mp3]
const fs = require('fs'), path = require('path');
const { spawnSync } = require('child_process');
const A = require('./audio_base');
const T = require('./timing');
const { SR, N, END, mL, mR, sL, sR, rnd, n, put, piano, pluck, pad, bass, kick, shaker, heartbeat, noiseBurst, whoosh, tone, pop, ding, click, thud, tick, rumble, arp, reverb, OUT } = A;
const VO = process.argv[2] || path.join(__dirname, '..', 'voiceover.mp3');
const at = (p, a = 0) => T.at(p, a);

// ---------- extra sounds ----------
function boom(t, vel = .5) { kick(t, vel, 's'); rumble(t, t + 1.6, vel * .35, 32); noiseBurst(t, .5, vel * .3, { lp: .05, fade: 5 }); }
function braam(t, dur = 2.5, vel = .08) { pad(t, t + dur, [n('C2'), n('G2'), n('C3'), n('Eb3')], vel, .05, 1.5, .8); kick(t, .5); }
function riser(t, dur = 1.5, vel = .1) { noiseBurst(t - dur, dur, vel, { shape: 'swell', sweep: u => .01 + .35 * u * u }); tone(t - dur, 200, dur, vel * .4, { decay: 0, f2: 1200 }); }
function shimmer(t, vel = .05) { for (let i = 0; i < 10; i++) tone(t + i * .06, 1568 * Math.pow(2, (i % 5) / 5), 1.6, vel, { decay: 2.5, pan: (i % 2 ? .5 : -.5) }); }
function crackle(t, dur = .8, vel = .1) { for (let x = 0; x < dur; x += .02 + rnd() * .05) noiseBurst(t + x, .02, vel * (.4 + rnd()), { lp: .6, fade: 200, pan: rnd() - .5 }); }
function hiss(t, dur, vel = .06) { noiseBurst(t, dur, vel, { lp: .9, hp: .7, shape: 'swell' }); }
function wind(t0, t1, vel = .04) { const i0 = Math.floor(t0 * SR), L = Math.floor((t1 - t0) * SR); let a = 0; for (let k = 0; k < L; k++) { const tt = k / SR; a += .004 * ((rnd() * 2 - 1) - a); const env = Math.min(1, tt / 1.5) * Math.min(1, (L - k) / SR / 1.5); put(sL, sR, i0 + k, a * 9 * env * vel * (1 + .5 * Math.sin(tt * .7)), Math.sin(tt * .3) * .5); } }
function tapeStop(t, vel = .08) { tone(t, 440, .8, vel, { decay: 2, f2: 40 }); }
function reverseSwell(t, vel = .1) { noiseBurst(t - 1, 1, vel, { shape: 'swell', sweep: u => .02 + .3 * u }); }

// ---------- score ----------
const MIN = [['A3', 'C4', 'E4'], ['F3', 'A3', 'C4'], ['D3', 'F3', 'A3'], ['E3', 'G#3', 'B3']];
function pulse(t0, t1, bpm, root, vel = .07) { const b = 60 / bpm; for (let t = t0, i = 0; t < t1; t += b / 2, i++) { pluck(t, n(root) + (i % 4 === 3 ? 12 : 0), vel * (i % 2 ? .6 : 1), 0, 14, .6); if (i % 4 === 0) bass(t, n(root) - 12, vel * 1.4, b * 1.6); } }
function bells(t0, t1, notes, gap = 1.6, vel = .05) { for (let t = t0, i = 0; t < t1; t += gap, i++) pluck(t, n(notes[i % notes.length]), vel, (i % 2 ? .4 : -.4), 3, .3); }

const sc = [...require('./scenes1'), ...require('./scenes2')].map(s => s.s).sort((a, b) => a - b);
console.log('composing...');
// HOOK
pulse(0, at('why mercury is the coldest') - .3, 120, 'A2', .07); pad(0, at('but the moment'), [n('A2'), n('E3'), n('A3')], .04, .5, 1, .4);
for (const w of ['burning', 'glowing', 'melting']) { boom(at(w), .45); }
wind(at('but the moment'), at('why mercury is the coldest'), .05); tapeStop(at('leaves'), .05);
riser(at('why mercury is the coldest'), 1.4, .1); braam(at('why mercury is the coldest'), 2.2, .09); boom(at('coldest', 11.6), .4);
heartbeat(at('peaceful', 13), .3); boom(at('peaceful', 13), .35); crackle(at('peaceful', 13), 1, .12); boom(at('repeat'), .4); crackle(at('repeat'), 1.2, .14);
pad(at('stay with me'), at("let's start with where"), [n('D3'), n('A3'), n('F4')], .04, 1, 1, .3); bells(at('stay with me'), at("let's start with where"), ['A5', 'E5', 'C6', 'B5'], .7, .04); shimmer(at('should not exist'), .03);
// WHERE / DAY / NIGHT: curious explainer
arp(at("let's start with where"), at('now imagine you land'), 100, [['C4', 'E4', 'G4', 'B4'], ['A3', 'C4', 'E4', 'G4'], ['F3', 'A3', 'C4', 'E4'], ['G3', 'B3', 'D4', 'G4']], { vel: .07, inst: 'pluck', pattern: [0, 2, 1, 3, 2, 0, 3, 1], bassVel: .08, padVel: .025, shake: true });
arp(at('now imagine you land'), at('now walk away'), 92, [['D4', 'F#4', 'A4', 'C#5'], ['B3', 'D4', 'F#4', 'A4'], ['G3', 'B3', 'D4', 'F#4'], ['A3', 'C#4', 'E4', 'A4']], { vel: .07, inst: 'pluck', pattern: [0, 1, 2, 3], bassVel: .09, padVel: .03 });
rumble(at('land') - .5, at('land') + 1.2, .1, 40); thud(at('land') + .8, .35); noiseBurst(at('430') - .3, 2, .05, { lp: .4, shape: 'swell' }); hiss(at('melt lead'), 2.4, .05); boom(at('blinding'), .3); shimmer(at('blinding'), .04);
pad(at('now walk away'), at('on the night side'), [n('A2'), n('E3'), n('C4')], .04, 2, 1.5, .2); for (let t = at('now walk away'); t < at('turns strange'); t += .62) noiseBurst(t, .06, .06, { lp: .2, fade: 50 });
tapeStop(at('turns strange') + .5, .05);
wind(at('on the night side'), at('so the big question'), .06); bells(at('on the night side'), at('so the big question'), ['E5', 'B4', 'G5', 'D5'], 1.4, .05);
pad(at('on the night side'), at('so the big question'), [n('E2'), n('B2'), n('G3')], .045, 1, 1, .2); hiss(at('180'), 1.5, .05);
boom(at('600'), .3); for (let i = 0; i < 14; i++) tick(at('600') - .3 + i * .09, .06);
riser(at('get this cold'), 1.2, .08); boom(at('get this cold') + .1, .35);
// REASON 1: AIR
arp(at('the first answer'), at("here's something that sounds"), 96, [['C4', 'E4', 'G4', 'C5'], ['G3', 'B3', 'D4', 'G4'], ['A3', 'C4', 'E4', 'A4'], ['F3', 'A3', 'C4', 'F4']], { vel: .065, inst: 'pluck', pattern: [0, 2, 1, 3, 2, 1, 3, 2], bassVel: .08, padVel: .025, shake: false });
noiseBurst(at('air.') - .4, .9, .08, { shape: 'swell', sweep: u => .05 + .1 * u }); boom(at('air.'), .25);
for (let i = 0; i < 12; i++) pop(at('blanket') + i * .05, .03, 500 + i * 60);
noiseBurst(at('charged particles') - .5, 4, .06, { lp: .9, hp: .5, shape: 'swell' }); whoosh(at("can't hold onto") + .5, .14, .8);
for (const p of ['no air to slow', 'no clouds']) boom(at(p), .2); boom(at('no blanket', 135), .25);
for (let t = at('when night comes'); t < at('just rock in a very'); t += .25) tone(t, 900 + rnd() * 600, .2, .02, { decay: 10, f2: 2400 });
// REASON 2: TIME
for (let t = at('this one is about time'); t < at("but there's one more trick"); t += .5) tick(t, .045);
boom(at('second problem'), .3); boom(at('176'), .3); for (let i = 0; i < 16; i++) tick(at('176') + i * .08, .05);
for (let i = 0; i < 3; i++) pop(at('three months of darkness') + i * .3, .08, 400 - i * 40);
boom(at('brutally cold'), .4); hiss(at('brutally cold'), 1.6, .06);
// REASON 3: SOIL
pad(at("but there's one more trick"), at('now i have to be honest'), [n('D3'), n('A3'), n('F4')], .035, 1.5, 1.5, .2); bells(at("but there's one more trick"), at('now i have to be honest'), ['D5', 'A4', 'F5', 'E5'], 1.5, .04);
rumble(at('dig down'), at('dig down') + 1.4, .08, 60); crackle(at('surface is violent'), .8, .08); thud(at("you'd hide underground") + .9, .3);
// HONEST PART
for (let i = 0; i < 6; i++) piano(at('now i have to be honest') + i * 1.6, n(['E4', 'G4', 'A4', 'G4', 'E4', 'D4'][i]), .06, 2.2, .1);
pop(at("and that's the feeling"), .1, 900); riser(at('record belongs to uranus'), .9, .07); boom(at('record belongs to uranus'), .35); ding(at('record belongs to uranus') + .3, .06, 1568);
pulse(at("so mercury doesn't win"), at("and i haven't even told"), 104, 'D3', .05); boom(at('it wins by shock'), .4); boom(at('so disturbing'), .35);
boom(at('not peaceful', 245), .4); crackle(at('not peaceful', 245), 1, .12);
// SUNRISE
pad(at("let's talk about the sunrise"), at('and the surface is even stranger'), [n('F3'), n('C4'), n('A4'), n('E5')], .035, 2, 2, .3);
bells(at('the sun comes up'), at('simple'), ['C5', 'E5', 'G5', 'C6'], .5, .05); ding(at('simple'), .06, 2093);
for (const p of [['then it stops', 257], ['stops once more', 262]]) { tapeStop(at(...p), .06); }
reverseSwell(at('slowly moves backward') + .8, .1); reverseSwell(at('appears to change direction') + .6, .08);
boom(at('the orbit wins'), .3);
// SHRINKING
rumble(at('when scientists'), at('when scientists') + 3, .05, 70); pulse(at('they found long cliffs'), at('so think about what this planet'), 90, 'E2', .05);
boom(at('by shrinking'), .4); for (let i = 0; i < 6; i++) crackle(at('as it cools') + i * .7, .3, .05);
boom(at('getting smaller'), .35); boom(at('right now', 313), .35);
for (const p of ['burning heat', 'deep freezing', 'cracking from the inside', ['moves backward', 320]]) boom(Array.isArray(p) ? at(...p) : at(p), .25);
pop(at('peaceful', 322), .1, 600); boom(at('not even close'), .45);
// THE ICE
pad(at('but i promised you'), at('then messenger arrived'), [n('A2'), n('E3'), n('B3'), n('C4')], .045, 1.5, 1, .25); click(at("and now it's time"), .3); shimmer(at("and now it's time") + .2, .03);
for (let t = at('for decades'); t < at('ice on the planet'); t += .55) tone(t, 1200, .25, .025, { decay: 12, f2: 900 }); // radar pings
boom(at('ice on the planet'), .3); for (let i = 0; i < 3; i++) pop(at('no way') + i * .15, .07, 500);
arp(at('then messenger arrived'), at('mercury has water ice'), 100, [['A3', 'C4', 'E4', 'A4'], ['F3', 'A3', 'C4', 'F4'], ['G3', 'B3', 'D4', 'G4'], ['E3', 'G#3', 'B3', 'E4']], { vel: .06, inst: 'pluck', pattern: [0, 2, 1, 3], bassVel: .08, padVel: .03 });
riser(at('mercury has water ice'), 2, .1); boom(at('mercury has water ice'), .45); shimmer(at('mercury has water ice'), .07); braam(at('mercury has water ice'), 3, .05);
arp(at("here's how it's possible"), at('so was the title true'), 84, [['C4', 'E4', 'G4', 'B4'], ['A3', 'C4', 'E4', 'G4'], ['F3', 'A3', 'C4', 'E4'], ['G3', 'B3', 'D4', 'F4']], { vel: .06, pattern: [0, 2, 1, 3, 2, 1, 3, 2], bassVel: .08, padVel: .03 });
for (const p of ['not for a day', 'not for a year', 'not for billions']) boom(at(p), .2);
whoosh(at('delivered by comets') + 1.2, .2, 1.2); boom(at('delivered by comets') + 1.3, .45); hiss(at('frozen in the dark'), 1.4, .05); shimmer(at('frozen in the dark'), .04);
boom(at('fire and ice'), .4); shimmer(at('fire and ice') + .45, .05);
// VERDICT + TEASER
braam(at('so was the title true'), 2, .05); boom(at("isn't the coldest") + .3, .35);
for (const p of [['no air to save'], ['no blanket', 420], ['no mercy']]) boom(at(...p), .4);
boom(at("you'll know the truth"), .3);
pad(at('and if mercury already feels'), END, [n('C2'), n('F#2'), n('C3')], .06, 1, 1.5, .2); heartbeat(at('which planet'), .3); heartbeat(at('which planet') + 1, .3); riser(at('even more terrifying'), 1.6, .1); boom(at('even more terrifying') + .6, .5);
// whoosh into every new scene
for (const s of sc) if (s > .5) whoosh(s + .08, .1, .45);

console.log('reverb...'); reverb(mL, mR, .3); reverb(sL, sR, .12);

console.log('voice envelope...');
const raw = spawnSync('ffmpeg', ['-loglevel', 'error', '-i', VO, '-ac', '1', '-ar', String(SR), '-f', 'f32le', '-'], { maxBuffer: 1 << 30 }).stdout;
const vo = new Float32Array(raw.buffer, raw.byteOffset, raw.length / 4);
const duck = new Float32Array(N); { let env = 0; const att = Math.exp(-1 / (.03 * SR)), rel = Math.exp(-1 / (.45 * SR)); let g = 1;
  for (let i = 0; i < N; i++) { const x = i < vo.length ? Math.abs(vo[i]) : 0; env = x > env ? x : env * .9995; const target = env > .02 ? .4 : 1; g = target < g ? target + (g - target) * att : target + (g - target) * rel; duck[i] = g; } }

console.log('mixdown...');
const out = Buffer.alloc(N * 8);
for (let i = 0; i < N; i++) { const t = i / SR; const fo = t > END - .6 ? Math.max(0, (END + .4 - t)) : 1;
  let l = (mL[i] * .9 * duck[i] + sL[i] * .8 * (.6 + .4 * duck[i])) * fo, r = (mR[i] * .9 * duck[i] + sR[i] * .8 * (.6 + .4 * duck[i])) * fo;
  l = Math.tanh(l * 1.2) / 1.2; r = Math.tanh(r * 1.2) / 1.2; out.writeFloatLE(l, i * 8); out.writeFloatLE(r, i * 8 + 4); }
const bed = path.join(OUT, 'bed.f32'); fs.writeFileSync(bed, out);
const vchain = 'highpass=f=80,lowpass=f=14500,equalizer=f=180:t=q:w=1:g=2,equalizer=f=3200:t=q:w=1.4:g=-2,equalizer=f=7000:t=q:w=2:g=-2.5,deesser=i=0.35,acompressor=threshold=-21dB:ratio=2.5:attack=10:release=150:makeup=2,aecho=0.85:0.6:38|61:0.10|0.06';
const r = spawnSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', VO, '-f', 'f32le', '-ar', String(SR), '-ac', '2', '-i', bed,
  '-filter_complex', `[0:a]aresample=${SR},${vchain},pan=stereo|c0=c0|c1=c0[v];[1:a]volume=0.85[b];[v][b]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11[o]`,
  '-map', '[o]', '-ar', String(SR), '-t', String(END + .5), path.join(OUT, 'mix.wav')], { stdio: 'inherit' });
fs.unlinkSync(bed);
console.log(r.status === 0 ? 'wrote out/mix.wav' : 'ffmpeg failed');
