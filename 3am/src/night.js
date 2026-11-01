// THE NIGHT. Every mistake from the day comes back as a thought.
const L = require('./lib');
const { W, H, E, inv, clamp, lerp, rng, hash, circle, ell, rr, text, rgrad, vgrad } = L;
const G = require('./guy');
const S = require('./sets');
const S2 = require('./sets2');
const SC = require('./screens');
const T = require('./tl');
const F = require('./fx');
const D = require('./day');
const { thought, pop, factCard, bubbleDark, speech, bed, digitalText, countingHand, edgeBlur, stormBubbles, RIM, RIM_W } = F;
const { createCanvas } = require('@napi-rs/canvas');

// grey mini-flashbacks of the day, rendered from the day scenes themselves
const _snap = {};
function snapshot(at) {
  if (_snap[at]) return _snap[at];
  const big = createCanvas(W, H), b = big.getContext('2d'); const sc = D.scenes.filter(s => at >= s.s && at < s.e)[0];
  b.fillStyle = '#000'; b.fillRect(0, 0, W, H); sc.draw(b, at, Math.round(at * 30));
  const c = createCanvas(560, 315), x = c.getContext('2d'); x.drawImage(big, 0, 0, 560, 315);
  x.globalCompositeOperation = 'saturation'; x.fillStyle = '#808080'; x.fillRect(0, 0, 560, 315); x.globalCompositeOperation = 'source-over';
  x.fillStyle = 'rgba(20,20,30,.25)'; x.fillRect(0, 0, 560, 315);
  _snap[at] = c; return c;
}
function memory(ctx, t, t0, t1, at, caption, x, y, rot) {
  if (t < t0) return; const k = E.back(clamp((t - t0) / .4)); const out = 1 - clamp((t - t1) / .4); if (out <= 0) return;
  ctx.save(); ctx.translate(x, y + Math.sin(t * 1.3 + x) * 6); ctx.rotate(rot); ctx.scale(k * .82, k * .82); ctx.globalAlpha *= clamp(k) * out;
  ctx.shadowColor = 'rgba(0,0,0,.7)'; ctx.shadowBlur = 40; ctx.fillStyle = 'rgba(16,18,28,.96)'; rr(ctx, -300, -220, 600, 440, 30); ctx.fill(); ctx.shadowColor = 'transparent';
  ctx.strokeStyle = 'rgba(255,90,90,.6)'; ctx.lineWidth = 3; ctx.stroke();
  ctx.drawImage(snapshot(at), -280, -200, 560, 315);
  const r = rng(Math.floor(t * 20)); for (let i = 0; i < 2; i++) { ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(-280 + r() * 560, -200, 2, 315); }
  text(ctx, caption, 0, 165, { size: 32, weight: 800, color: '#fff' });
  ctx.restore();
}
const holdPhoneOff = { phone: false };

const scenes = [
  // ---------------- 10. EYES OPEN ----------------
  { s: T.night, e: T.eyesPOV, cam: [1.3, 1.42, 640, 600], fadeIn: .6, draw(ctx, t) {
      const snap = t > T.snap; const wide = snap && t < T.snap + .7;
      bed(ctx, t, { ...holdPhoneOff, guy: { mood: wide ? 'panic' : snap ? 'blank' : 'asleep', eye: wide ? 'wide' : null, look: .2, lookY: -.8 } });
      if (snap && t < T.snap + .3) { ctx.fillStyle = `rgba(255,255,255,${.25 * (1 - (t - T.snap) / .3)})`; ctx.fillRect(0, 0, W, H); }
    } },
  { s: T.eyesPOV, e: T.math, cam: [1.08, 1.0, 960, 600], vig: .8, draw(ctx, t) {
      ctx.fillStyle = '#04060b'; ctx.fillRect(0, 0, W, H); const b = E.out(clamp((t - T.eyesPOV) / .3));
      G.povPhone(ctx, 960, 610, .78, (x, w, h) => SC.lock(x, w, h, t, { time: '3:07', battery: 31, showPct: true }), { bright: b, glow: b });
      thought(ctx, t, T.notAgain, T.math, 'Not again.', 1460, 520, { size: 74 });
      pop(ctx, t, T.eyesPOV + .6, T.math, '31%', 470, 520, { size: 64, color: '#9fd4ff' });
    } },

  // ---------------- 11. THE MATH ----------------
  { s: T.math, e: T.replay, cam: [1.0, 1.08, 960, 560], fadeIn: .3, vig: .8, draw(ctx, t) {
      ctx.fillStyle = '#07070b'; ctx.fillRect(0, 0, W, H);
      ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, 300, 300, 10, 1300, [[0, 'rgba(255,60,50,.28)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(0, 0, W, H); ctx.restore();
      const jm = clamp((t - (T.jump319 - .8)) / .8); const mm = Math.round(lerp(7, 19, jm));
      ctx.save(); if (jm > 0 && jm < 1) ctx.translate(Math.sin(t * 80) * 6, 0); digitalText(ctx, `3:${String(mm).padStart(2, '0')}`, 330, 300, 130, .95); ctx.restore();
      const cnt = Math.max(0, Math.min(4, (t - (T.count + .4)) / .55));
      countingHand(ctx, t, cnt, 1060, 840);
      ['4', '5', '6', '7'].forEach((d, i) => { if (cnt > i) L.popText(ctx, t, T.count + .4 + i * .55, d, 1060 + [-105, -36, 34, 102][i], 420 - [0, 14, 10, -8][i], { size: 54, weight: 900, color: '#ffb0a8' }); });
      if (t > T.sleepEq) { const k = E.back(clamp((t - T.sleepEq) / .4)); ctx.save(); ctx.translate(1440, 330); ctx.scale(k, k);
        text(ctx, 'Sleep now =', 0, -50, { size: 46, weight: 700, color: 'rgba(255,255,255,.75)' });
        text(ctx, '3 hours 41 min.', 0, 30, { size: 72, weight: 900, color: '#fff', shadow: 'rgba(255,60,50,.6)' }); ctx.restore(); }
    } },

  // ---------------- 12. THE REPLAY BEGINS ----------------
  { s: T.replay, e: T.song, cam: [1.0, 1.1, 960, 520], draw(ctx, t) {
      const k = .08 + .22 * E.inOut(clamp((t - T.r1) / 1)) + .2 * E.inOut(clamp((t - T.r2) / 1)) + .25 * E.inOut(clamp((t - T.r3) / 1));
      bed(ctx, t, { ...holdPhoneOff, shadow: k, guy: { mood: t > T.r3 ? 'sad' : 'worried', look: .2, lookY: -.9 } });
      memory(ctx, t, T.r1, T.song - .3, 42.0, 'The whole class laughed.', 470, 470, -.05);
      memory(ctx, t, T.r2, T.song - .3, 58.6, 'She waved at him, not you.', 980, 400, .03);
      memory(ctx, t, T.r3, T.song - .3, 49.4, "They didn't even invite you.", 1480, 480, -.03);
    } },

  // ---------------- 13. JUST ONE SONG ----------------
  { s: T.song, e: T.songWide, cam: [1.0, 1.05, 960, 600], vig: .8, draw(ctx, t) {
      ctx.fillStyle = '#04060b'; ctx.fillRect(0, 0, W, H);
      const press = t > T.play - .25 && t < T.play + .15 ? 1 : 0; const playing = t > T.play;
      G.povPhone(ctx, 960, 610, .78, (x, w, h) => SC.music(x, w, h, t, { paused: !playing, progress: playing ? (t - T.play) * .02 : 0, time: '3:22', battery: 24, showPct: true }),
        { thumbR: t > T.play - 1.2 ? { x: 200, y: 680 + press * 6 } : null, press });
      thought(ctx, t, T.oneSong, T.songWide, 'One song. Then sleep.', 1460, 470, { size: 56, maxW: 640 });
      pop(ctx, t, T.song + .5, T.songWide, '24%', 470, 520, { size: 64, color: '#9fd4ff' });
    } },
  { s: T.songWide, e: T.imag, cam: [1.2, 1.3, 760, 520], draw(ctx, t) {
      bed(ctx, t, { buds: true, guy: { mood: 'soft', look: .2, lookY: -1 } });
      for (let i = 0; i < 6; i++) { const p = ((t - T.play) * .25 + i / 6) % 1; ctx.save(); ctx.globalAlpha = Math.sin(p * Math.PI) * .8; text(ctx, i % 2 ? '♪' : '♫', 520 + i * 40 + Math.sin(p * 8 + i) * 20, 600 - p * 320, { size: 44, weight: 700, color: '#b9c8ff' }); ctx.restore(); }
    } },

  // ---------------- 14. IMAGINATION MODE ----------------
  { s: T.spot, e: T.cheer, cam: [1.3, 1.6, 600, 560], draw(ctx, t) {
      const p = clamp((t - T.spot) / (T.cheer - T.spot));
      bed(ctx, t, { buds: true, glow: 1 + p * 2, guy: { mood: 'shy', look: .2, lookY: -1 }, dark: p * .5 });
      ctx.save(); ctx.globalCompositeOperation = 'screen'; const g = ctx.createLinearGradient(560, 90, 560, 700); g.addColorStop(0, `rgba(255,245,220,${.6 * p})`); g.addColorStop(1, 'rgba(255,245,220,0)'); ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(520, 90); ctx.lineTo(600, 90); ctx.lineTo(560 + 200 * p + 60, 720); ctx.lineTo(560 - 200 * p - 60, 720); ctx.closePath(); ctx.fill(); ctx.restore();
      if (t > T.cheer - .3) { ctx.fillStyle = `rgba(255,250,235,${clamp((t - (T.cheer - .3)) / .3)})`; ctx.fillRect(0, 0, W, H); }
    } },
  { s: T.cheer, e: T.car, cam: [1.0, 1.1, 960, 560], draw(ctx, t) {
      S2.classroom(ctx, t, { slide: 'win' });
      ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, 830, 700, 20, 420, [[0, 'rgba(255,240,200,.5)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(300, 200, 1100, 900); ctx.restore();
      G.guy(ctx, 830, 990, .52, { mood: 'dream', t, seed: .2, look: .5, rim: RIM_W, lh: [-200, -680 - Math.sin(t * 6) * 40], rh: [200, -680 - Math.cos(t * 6) * 40], bendB: -.5, bendF: -.5 });
      S2.teacher(ctx, 1040, 980, .44, t, { flip: 1, look: .8, clap: true, mood: 'happy' });
      for (let i = 0; i < 6; i++) S2.student(ctx, t, i, { mood: 'laugh', cheer: true, look: .8 });
      S.confetti(ctx, t, T.cheer + .2, 140);
      const b = 1 + .08 * Math.abs(Math.sin((t - T.cheer) * Math.PI * 1.6)); ctx.save(); ctx.translate(1300, 200); ctx.scale(b, b); text(ctx, 'YOU!  YOU!  YOU!', 0, 0, { size: 78, weight: 900, color: '#fff', shadow: 'rgba(255,120,60,.9)', alpha: clamp((t - T.cheer - .4) / .3) }); ctx.restore();
    } },
  { s: T.car, e: T.house, cam: [1.12, 1.0, 900, 640], flash: true, draw(ctx, t) {
      S.carSet(ctx, t); S.sportsCar(ctx, 1080, 900, 1.05, 0);
      G.guy(ctx, 560, 905, .55, { mood: 'happy', glasses: 1, t, look: .6, rim: RIM_W, lean: -.08, lh: [-160, -470], rh: [170, -300], footF: [120, 0] });
      L.chip(ctx, t, T.car + .4, 'NEW CAR', 560, 250, { size: 56, bg: '#ffb35c' });
    } },
  { s: T.house, e: T.crush2, cam: [1.0, 1.12, 960, 560], flash: true, draw(ctx, t) {
      S.houseSet(ctx, t);
      G.guy(ctx, 960, 960, .5, { mood: 'dream', t, rim: RIM_W, lh: [-260, -640], rh: [260, -640], bendB: -.5, bendF: -.5 });
      L.chip(ctx, t, T.house + .3, 'BIG HOUSE', 960, 230, { size: 56, bg: '#ffb35c' });
    } },
  { s: T.crush2, e: T.real, cam: [1.12, 1.2, 940, 560], flash: true, draw(ctx, t) {
      S.hallway(ctx, t, 0);
      G.guy(ctx, 660, 930, .55, { mood: 'happy', hair: 'pony', t, seed: .7, look: .7, blush: 1, rh: [150, -640 - Math.abs(Math.sin(t * 6)) * 60], bendF: -1 });
      G.guy(ctx, 1240, 930, .55, { mood: 'dream', t, flip: 1, look: .6, blush: 1, rh: [150, -660 - Math.abs(Math.sin(t * 6)) * 60], bendF: -1 });
      S.hearts(ctx, t, T.crush2 + .3, 660, 330, 7);
      L.chip(ctx, t, T.crush2 + .4, 'THIS TIME: AT YOU', 940, 220, { size: 46, bg: '#ff7a9a', color: '#fff' });
    } },
  { s: T.real, e: T.drift, cam: [1.32, 1.4, 740, 560], draw(ctx, t) {
      const playing = t < T.skip; const d = playing ? t * 9 : 0;
      const hands = [[720 + Math.sin(d) * 8, 640 - Math.abs(Math.sin(d)) * 46, 1], [800 + Math.cos(d) * 8, 640 - Math.abs(Math.cos(d)) * 46, 0]];
      bed(ctx, t, { buds: true, phone: false, hands, guy: { mood: playing ? 'dream' : 'awkward', eye: playing ? 'closed' : null, look: .3, lookY: playing ? -.6 : 0 } });
      thought(ctx, t, T.real + .5, T.drift, 'Real you:', 1180, 330, { size: 58 });
      thought(ctx, t, T.real + 1.2, T.drift, 'air-drumming on a blanket.', 1180, 410, { size: 50, maxW: 760 });
    } },

  // ---------------- 15. THE DRIFT ----------------
  { s: T.drift, e: T.hover, cam: [1.2, 1.32, 700, 560], draw(ctx, t) {
      const red = clamp((t - T.drift) / 1.6);
      bed(ctx, t, { buds: true, red, glowCol: '255,90,110', guy: { mood: 'blank', look: .2, lookY: -1 } });
    }, post(ctx, t, cv) { edgeBlur(ctx, cv, clamp((t - T.drift) / 2)); } },
  { s: T.hover, e: T.dark, cam: [1.0, 1.12, 960, 600], vig: .9, draw(ctx, t) {
      ctx.fillStyle = '#0a0204'; ctx.fillRect(0, 0, W, H);
      const hb = Math.max(0, Math.sin((t - T.hover) * Math.PI * 2 * (1 + (t - T.hover) * .08))) ** 8;
      const s = 1 + hb * .012; ctx.save(); ctx.translate(960, 610); ctx.scale(s, s); ctx.translate(-960, -610);
      const shake = (Math.sin(t * 31) + Math.sin(t * 23)) * 4;
      G.povPhone(ctx, 960, 610, .78, (x, w, h) => SC.home(x, w, h, t, { temptation: clamp((t - T.hover) / 1.5), time: '3:26' }), { thumbR: { x: 268 + shake, y: 360 + Math.sin(t * 2) * 6 } });
      ctx.restore();
      ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.fillStyle = 'rgba(255,30,50,.45)'; ctx.fillRect(0, 0, W, H); ctx.restore();
      thought(ctx, t, T.oneLook, T.dark - .2, 'Just one look.', 470, 470, { size: 60, glow: 'rgba(255,60,80,.8)' });
      thought(ctx, t, T.nobody, T.dark - .2, 'Nobody will know.', 1460, 560, { size: 56, glow: 'rgba(255,60,80,.8)' });
    }, post(ctx, t, cv) { edgeBlur(ctx, cv, .8); } },
  { s: T.dark, e: T.storm, cam: [1.0, 1.1, 960, 600], vig: .9, draw(ctx, t) {
      ctx.fillStyle = '#030305'; ctx.fillRect(0, 0, W, H);
      const pull = clamp((t - T.pull) / 1.2); const red = 1 - clamp((t - T.pull) / 1.5);
      G.povPhone(ctx, 960, 610 + E.inOut(pull) * 60, .78, null, { off: true, glow: 0, thumbR: { x: lerp(268, 406, E.inOut(pull)), y: lerp(360, 690, E.inOut(pull)) },
        reflect(ctx, sx, sy, sw, sh) { ctx.save(); ctx.globalAlpha = .28 * clamp((t - T.dark) / 1.2); G.head(ctx, sx + sw / 2, sy + sh * .4, 120, { mood: 'sad', t, seed: 2 }); ctx.restore(); } });
      if (red > 0) { ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.fillStyle = `rgba(255,30,50,${.35 * red})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
      thought(ctx, t, T.empty, T.pull - .2, 'Empty.', 1480, 380, { size: 64, instant: true, glow: 'rgba(0,0,0,0)' });
      thought(ctx, t, T.guilty, T.pull - .2, 'Guilty.', 1480, 480, { size: 64, instant: true, glow: 'rgba(0,0,0,0)' });
      thought(ctx, t, T.awake, T.pull - .2, 'Still awake.', 1480, 580, { size: 64, instant: true, glow: 'rgba(0,0,0,0)' });
      pop(ctx, t, T.pull + .5, T.storm - .1, 'You put it down.', 1460, 470, { size: 52, color: '#9fd4ff' });
    } },

  // ---------------- 16. THE STORM ----------------
  { s: T.storm, e: T.feed, cam: [1.0, 1.16, 860, 520], draw(ctx, t) {
      const k = clamp((t - T.storm) / (T.feed - T.storm)); const flick = .75 + .25 * Math.sin(t * 13) * Math.sin(t * 7);
      bed(ctx, t, { shadow: .35 + k * .55, glow: flick, guy: { mood: k > .5 ? 'panic' : 'worried', look: .2, lookY: -.8 } });
      stormBubbles(ctx, t, T.storm - .6, T.feed + .2, 1.4);
    } },
  { s: T.feed, e: T.flood, cam: [1.0, 1.1, 960, 600], vig: .8, draw(ctx, t) {
      ctx.fillStyle = '#04060b'; ctx.fillRect(0, 0, W, H);
      const sc = (a) => t > a ? E.inOut(clamp((t - a) / .6)) * 330 : 0; const scroll = sc(T.f1) + sc(T.f2) + (t > T.battery ? (t - T.battery) * 500 : 0);
      G.povPhone(ctx, 960, 610, .78, (x, w, h) => { SC.feed(x, w, h, t, { scroll, battery: t > T.battery ? 4 : 9, showPct: true, time: '3:36' }); if (t > T.battery) SC.lowBattery(x, w, h, E.out(clamp((t - T.battery) / .3))); }, { thumbR: { x: 300, y: 600 - ((t * 2.5) % 1) * 200 } });
      pop(ctx, t, T.f1 + .3, T.flood, 'Got the job!', 470, 330, { size: 52 }); pop(ctx, t, T.f2 + .3, T.flood, 'Engaged!', 1460, 380, { size: 52 });
      if (t > T.battery) pop(ctx, t, T.battery + .2, T.why, '4%', 470, 560, { size: 120, color: '#ff453a' });
      if (t > T.why) { ctx.save(); ctx.globalAlpha = clamp((t - T.why) / .2) * .6; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); ctx.restore(); }
      thought(ctx, t, T.why, T.flood, 'Why are you like this?', 960, 520, { size: 92, glow: 'rgba(255,60,60,.9)', cps: 40 });
    } },
  { s: T.flood, e: T.dies, cam: [1.12, 1.34, 760, 560], shake: [[T.flood, T.dies - T.flood, 7]], draw(ctx, t) {
      const k = clamp((t - T.flood) / (T.dies - T.flood));
      bed(ctx, t, { shadow: .9 + k * .25, glow: .6 + .4 * Math.random(), glowCol: '255,90,80', guy: { mood: 'panic', look: .1, lookY: -.4 } });
      stormBubbles(ctx, t, T.flood - 12, T.dies + 2, 2.6);
      ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.fillStyle = `rgba(255,30,40,${.3 * k})`; ctx.fillRect(0, 0, W, H); ctx.restore();
    } },

  // ---------------- 17. PHONE DIES ----------------
  { s: T.dies, e: T.fridge, cam: [1.0, 1.0, 960, 600], vig: .9, draw(ctx, t) {
      ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
      if (t < T.dieClick) G.povPhone(ctx, 960, 610, .78, (x, w, h) => SC.dying(x, w, h, t, clamp((t - (T.dieClick - .3)) / .3)), { glow: .3 * (1 - clamp((t - (T.dieClick - .3)) / .3)) });
      else { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); }
    } },

  // ---------------- 18. FRIDGE LIGHT ----------------
  { s: T.fridge, e: T.list, cam: [1.0, 1.12, 1000, 560], fadeIn: 1.2, draw(ctx, t) {
      const open = E.out(clamp((t - T.open) / .6));
      S.kitchen(ctx, t, open);
      // the chair you will hit
      ctx.fillStyle = '#1c2436'; ctx.fillRect(600, 760, 14, 180); ctx.fillRect(700, 760, 14, 180); ctx.fillRect(590, 740, 136, 22); ctx.fillRect(700, 560, 14, 190);
      // big shadow on the wall from the fridge light
      if (open > 0) S.wallShadow(ctx, t, (.6 - .2 * clamp((t - T.gulp) / 2)) * open, 560, 1000, [0, 86, 1240, 704]);
      const hop = t > T.toe && t < T.toe + 1.6; const walk1 = lerp(120, 560, clamp((t - T.fridge) / (T.toe - T.fridge)));
      const walk2 = lerp(560, 1010, clamp((t - (T.toe + 1.7)) / (T.open - T.toe - 1.9)));
      const x = t < T.toe ? walk1 : t < T.toe + 1.7 ? 560 - Math.sin((t - T.toe) * 3) * 30 : walk2;
      const drink = clamp((t - T.gulp) / .4) * (1 - clamp((t - T.gulp - 1.6) / .4));
      const walking = (t < T.toe) || (t > T.toe + 1.7 && t < T.open - .2);
      G.guy(ctx, x, 940 - (hop ? Math.abs(Math.sin((t - T.toe) * 10)) * 50 : 0), .55, { mood: hop ? 'cringe' : drink > .5 ? 'soft' : 'tired', eye: drink > .5 ? 'closed' : null, t, seed: .2, walk: walking ? t * 5 : null, look: .6,
        rim: open > 0 ? 'rgba(255,220,160,.9)' : 'rgba(110,150,255,.5)', rimDX: open > 0 ? 7 : -7, footF: hop ? [40, -220] : null, rh: hop ? [60, -250] : t > T.glass ? [150 - 40 * drink, -470 - 250 * drink] : null, bendF: -1, headRot: -.35 * drink,
        propFront(ctx, h) { if (t > T.glass && !hop) { ctx.save(); ctx.translate(h[0], h[1]); ctx.rotate(-.6 * drink); ctx.fillStyle = 'rgba(190,220,255,.55)'; rr(ctx, -26, -70, 52, 90, 8); ctx.fill(); ctx.fillStyle = 'rgba(150,200,255,.6)'; ctx.fillRect(-22, -40 + 30 * drink, 44, 56 - 30 * drink); ctx.restore(); } } });
      if (open > 0) { ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = `rgba(255,220,160,${.1 * open})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
      if (open < 1) { ctx.fillStyle = `rgba(0,0,0,${.45 * (1 - open)})`; ctx.fillRect(0, 0, W, H); }
      pop(ctx, t, T.ow, T.toe + 1.6, 'ow.', 560, 360, { size: 40, color: '#fff' });
      pop(ctx, t, T.ow + .55, T.toe + 1.6, 'OW.', 760, 300, { size: 96, color: '#ff8a80' });
      L.chip(ctx, t, T.chips, 'Cold water.', 470, 260, { size: 40, bg: '#9fd4ff', until: T.list - .4 });
      L.chip(ctx, t, T.chips + .5, 'Cold floor.', 470, 350, { size: 40, bg: '#9fd4ff', until: T.list - .4 });
      L.chip(ctx, t, T.chips + 1, 'Fridge hum.', 470, 440, { size: 40, bg: '#9fd4ff', until: T.list - .4 });
    }, post(ctx, t) { factCard(ctx, t, T.chips + 1.3, T.list - .3, 'GROUNDING', "Name 3 real things around you. It pulls your brain from 'what if' back to 'what is'.", { y: 960, w: 720 }); } },

  // ---------------- 19. THE LIST ----------------
  { s: T.list, e: T.shrink, cam: [1.08, 1.0, 980, 560], fadeIn: .3, draw(ctx, t) {
      S.desk(ctx, t);
      ctx.save(); ctx.translate(980, 560); ctx.rotate(-.03);
      const lines = [['Today:', T.today, 54, 800, '#22264a'], ['- late', T.l1, 44, 500, '#22264a'], ['- the presentation', T.l2, 44, 500, '#22264a'], ['- lunch alone', T.l3, 44, 500, '#22264a'], ["- 'you too'", T.l4, 44, 500, '#22264a'], ['One bad day.', T.bad, 58, 800, '#1b3a8f'], ['Not a bad life.', T.bad + 1.0, 58, 800, '#1b3a8f']];
      let pen = null;
      lines.forEach(([s, t0, size, wt, col], i) => { if (t < t0) return; const n = Math.min(s.length, Math.floor((t - t0) * 22)); const sub = s.slice(0, n);
        const y = -330 + i * 92 + (i >= 5 ? 40 : 0); ctx.font = `italic ${wt} ${size}px Inter`; const w = ctx.measureText(sub).width;
        text(ctx, sub, -330, y, { size, weight: wt, color: col, align: 'left', fam: 'Inter' }); if (n < s.length) pen = [-330 + w, y]; });
      if (t > T.underline) { const p = E.inOut(clamp((t - T.underline) / .6)); const y = -330 + 6 * 92 + 40 + 40; ctx.strokeStyle = '#d63a3a'; ctx.lineWidth = 8; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-336, y); ctx.lineTo(-336 + 440 * p, y + 4); ctx.stroke(); pen = [-336 + 440 * p, y]; }
      if (pen) { ctx.save(); ctx.translate(pen[0] + 6, pen[1] - 4 + Math.sin(t * 30) * 3); ctx.rotate(-.75); ctx.fillStyle = '#1c1c22'; rr(ctx, -6, -260, 22, 260, 8); ctx.fill(); ctx.fillStyle = '#e9b949'; ctx.fillRect(-6, -240, 22, 20); ctx.fillStyle = '#111'; ctx.beginPath(); ctx.moveTo(-6, 0); ctx.lineTo(16, 0); ctx.lineTo(5, 18); ctx.fill(); ctx.restore();
        G.finger(ctx, [pen[0] + 300, pen[1] + 300], [pen[0] + 110, pen[1] - 30], 120); }
      ctx.restore();
    } },
  { s: T.shrink, e: T.callback, cam: [1.0, 1.1, 860, 520], draw(ctx, t) {
      const k = .7 * (1 - E.inOut(clamp((t - T.shrink) / 2.6)));
      bed(ctx, t, { shadow: k, phone: false, clock: '3:58', guy: { mood: 'soft', look: .3, lookY: -.8 } });
      ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = rgrad(ctx, 210, 600, 10, 700, [[0, `rgba(255,190,110,${.25 * clamp((t - T.shrink) / 1.5)})`], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(0, 0, W, H); ctx.restore();
      thought(ctx, t, T.shrink + .6, T.callback, 'Back to normal size.', 1300, 280, { size: 56, glow: 'rgba(255,170,90,.7)' });
    }, post(ctx, t) { factCard(ctx, t, T.fact2, T.callback - .3, '3AM FACT', 'Worries on paper feel smaller than worries in your head. People who wrote a to-do list before bed fell asleep faster.', { y: 960, w: 860 }); } },

  // ---------------- 20. THE CALLBACK ----------------
  { s: T.callback, e: T.split, cam: [1.0, 1.08, 960, 600], vig: .8, draw(ctx, t) {
      ctx.fillStyle = '#04060b'; ctx.fillRect(0, 0, W, H);
      const msg = 'Sorry I missed your call. Love you.'; const typed = t < T.typeS ? '' : t < T.sent - .4 ? msg.slice(0, Math.floor((t - T.typeS) / (T.sent - .4 - T.typeS) * msg.length)) : t < T.sent ? msg : '';
      const typingNow = t > T.typeS && t < T.sent - .4; const tap = typingNow && ((t * 9) % 1) < .35;
      // charging cable
      ctx.strokeStyle = '#d8d8de'; ctx.lineWidth = 14; ctx.beginPath(); ctx.moveTo(960, 960); ctx.quadraticCurveTo(980, 1040, 1100, 1080); ctx.stroke();
      G.povPhone(ctx, 960, 610, .78, (x, w, h) => t < T.openChat ? SC.lock(x, w, h, t, { time: '3:59', battery: 2, showPct: true, charging: true }) : SC.chat(x, w, h, t, { typed, sent: t > T.sent ? clamp((t - T.sent) / .3) : 0, read: t > T.sent + .6, typing: t > T.typing ? clamp((t - T.typing) / .3) : 0, time: '3:59', battery: 2, charging: true }),
        { thumbR: typingNow ? { x: 120 + ((Math.floor(t * 9) * 97) % 200), y: 700 + (tap ? 6 : 0) } : t > T.sent - .4 && t < T.sent + .2 ? { x: 356, y: 762 } : null, press: tap ? 1 : 0 });
      pop(ctx, t, T.callback + .3, T.openChat, 'Charging.', 1440, 470, { size: 54, color: '#7fd99a' });
      thought(ctx, t, T.typing + .3, T.split, 'Mom is typing...', 1460, 430, { size: 54, glow: 'rgba(80,220,120,.6)' });
    } },
  { s: T.split, e: T.next, cam: [1.0, 1.04, 960, 540], fadeOut: .6, draw(ctx, t) {
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W / 2 - 4, H); ctx.clip(); ctx.translate(-210, -230); ctx.scale(1.38, 1.38); ctx.translate(-160, -110);
      bed(ctx, t, { shadow: 0, case: false, guy: { mood: t > T.reply + .5 ? 'soft' : 'tired', look: .3, lookY: -.7, tear: t > T.awakeToo ? clamp((t - T.awakeToo) / 2.5) : null } });
      ctx.restore();
      ctx.save(); ctx.beginPath(); ctx.rect(W / 2 + 4, 0, W / 2, H); ctx.clip(); ctx.translate(W / 2 - 140, 0);
      S.momRoom(ctx, t); ctx.translate(-80, 0);
      G.guy(ctx, 720, 1110, .62, { mood: t > T.reply ? 'smile' : 'soft', hair: 'bun', t, seed: 1.9, look: .5, lookY: .4, rim: RIM_W, rimDX: 6, rh: [150, -440], lh: [110, -450], bendF: -1, bendB: -1,
        outfit(ctx) { ctx.fillStyle = '#8c2f45'; ctx.beginPath(); ctx.moveTo(-108, -560); ctx.quadraticCurveTo(0, -500, 108, -580); ctx.lineTo(108, -500); ctx.quadraticCurveTo(0, -430, -108, -480); ctx.closePath(); ctx.fill(); },
        propFront(ctx, h) { ctx.save(); ctx.translate(h[0] + 10, h[1] - 30); ctx.rotate(-.2); ctx.fillStyle = '#0b0b0e'; rr(ctx, -30, -55, 60, 110, 10); ctx.fill(); ctx.fillStyle = '#3a6ad1'; rr(ctx, -24, -48, 48, 96, 6); ctx.fill(); ctx.restore(); } });
      S.phoneGlow(ctx, 860, 620, .9, '150,180,255', 380);
      ctx.fillStyle = '#4a2f22'; ctx.fillRect(0, 760, W, 400); ctx.fillStyle = '#8c3b3b'; rr(ctx, 280, 730, 900, 120, 40); ctx.fill();
      ctx.restore();
      ctx.fillStyle = '#000'; ctx.fillRect(W / 2 - 4, 0, 8, H);
      text(ctx, 'YOU', 120, 140, { size: 30, weight: 900, color: 'rgba(255,255,255,.55)', align: 'left', track: 6 });
      text(ctx, 'MOM', W / 2 + 60, 140, { size: 30, weight: 900, color: 'rgba(255,255,255,.55)', align: 'left', track: 6 });
      if (t > T.reply) { const k = E.back(clamp((t - T.reply) / .4)); ctx.save(); ctx.translate(960, 300); ctx.scale(k, k);
        ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 30; ctx.fillStyle = '#262a35'; rr(ctx, -400, -90, 800, 180, 40); ctx.fill(); ctx.shadowColor = 'transparent';
        text(ctx, 'Mom', -350, -46, { size: 28, weight: 800, color: '#7fd99a', align: 'left' });
        text(ctx, 'Bad day? Me too. Call tomorrow', -350, 12, { size: 42, weight: 600, color: '#fff', align: 'left' });
        S.heart(ctx, 330, 14, 20, '#ff5a7a'); ctx.restore(); }
      thought(ctx, t, T.awakeToo, T.next, "She's awake too.", 960, 520, { size: 76, glow: 'rgba(255,170,90,.8)' });
    } },

  // ---------------- 21. NEXT NIGHT ----------------
  { s: T.next, e: T.card, cam: [1.25, 1.55, 600, 580], fadeIn: .8, fadeOut: 1.2, draw(ctx, t) {
      const climb = E.inOut(clamp((t - T.tag307) / 2.6)) * .5; const fade = 1 - E.inOut(clamp((t - T.fade) / 1.2)); const k = climb * fade;
      const fl = clamp((t - T.flip) / .55); const lift = Math.sin(clamp((t - T.flip + .3) / 1.1) * Math.PI) * -38;
      const closed = t > T.fade + .6;
      bed(ctx, t, { phone: false, shadow: k, clock: '3:07', guy: { mood: closed ? 'asleep' : t > T.smirk ? 'smirk' : 'blank', headDY: lift, look: .2, lookY: -.6 },
        hands: [[lerp(560, 470, Math.sin(fl * Math.PI)), 690 - Math.sin(fl * Math.PI) * 50, 0]],
        pre(ctx) { if (t > T.flip - .1 && t < T.flip + .8) { ctx.save(); ctx.translate(470, 690); ctx.scale(1, Math.cos(fl * Math.PI)); ctx.fillStyle = fl > .5 ? '#cfe3ff' : '#dcdbe8'; ell(ctx, 0, 0, 120, 36); ctx.fill(); ctx.restore(); } } });
      if (t > T.flip + .5) { const r = rng(4); const a = clamp((t - T.flip - .5) * 2) * (1 - clamp((t - T.flip - 2) / .6)); for (let i = 0; i < 10; i++) { ctx.fillStyle = `rgba(190,225,255,${a * (.5 + .5 * Math.sin(t * 9 + i))})`; circle(ctx, 380 + r() * 200, 660 - r() * 40, 3 + r() * 3); ctx.fill(); } }
      bubbleDark(ctx, t, T.remember, "Remember when you said 'you too'...", 820, 420, { size: 34, until: T.smirk + .5, maxW: 520 });
      if (t > T.smirk + .5 && t < T.smirk + 1) { const p = (t - T.smirk - .5) / .5; ctx.strokeStyle = `rgba(255,255,255,${1 - p})`; ctx.lineWidth = 4; for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; ctx.beginPath(); ctx.moveTo(820 + Math.cos(a) * 60 * p, 420 + Math.sin(a) * 60 * p); ctx.lineTo(820 + Math.cos(a) * 110 * p, 420 + Math.sin(a) * 110 * p); ctx.stroke(); } }
      thought(ctx, t, T.notTonight, T.card - .8, 'Not tonight.', 820, 440, { size: 64, glow: 'rgba(255,190,120,.7)' });
      if (closed) for (let i = 0; i < 3; i++) { const p = ((t - T.fade) * .35 + i / 3) % 1; ctx.save(); ctx.globalAlpha = Math.sin(p * Math.PI) * .7; text(ctx, 'z', 560 + p * 80 + i * 10, 560 - p * 140, { size: 30 + p * 26, weight: 800, color: '#b9c8ff' }); ctx.restore(); }
    } },
  // ---------------- END CARD ----------------
  { s: T.card, e: T.END + 1, cam: [1, 1.03, 960, 540], draw(ctx, t) {
      ctx.fillStyle = '#030305'; ctx.fillRect(0, 0, W, H);
      thought(ctx, t, T.c1, T.END - 1, 'One bad day at 3 AM feels like forever.', 960, 440, { size: 60, cps: 32, maxW: 1400 });
      thought(ctx, t, T.c2, T.END - 1, "It isn't.", 960, 560, { size: 92, cps: 14, glow: 'rgba(255,190,120,.7)' });
      if (t > T.c3) { const a = clamp((t - T.c3) / .8) * (1 - clamp((t - (T.END - 1)) / .8));
        text(ctx, 'Save this for the next 3 AM.', 960, 760, { size: 32, weight: 600, color: 'rgba(255,255,255,.6)', alpha: a, track: 2 });
        digitalText(ctx, '3AM', 800, 880, 54, a * .8); text(ctx, 'THOUGHTS', 1040, 880, { size: 36, weight: 300, color: 'rgba(244,241,234,.8)', alpha: a, track: 10 }); }
    } },
];

module.exports = scenes;
