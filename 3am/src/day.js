// COLD OPEN + THE DAY (fast, lots of movement). Every mistake here comes back at night.
const L = require('./lib');
const { W, H, E, inv, clamp, lerp, rng, circle, ell, rr, text, rgrad, vgrad } = L;
const G = require('./guy');
const S = require('./sets');
const S2 = require('./sets2');
const SC = require('./screens');
const T = require('./tl');
const F = require('./fx');
const { thought, pop, speech, bed, digitalText, RIM } = F;

const ME = { pants: '#3d5a80', backpack: '#e0703a' }; // our hero's day look
const stainAt = t => t < T.spill ? 0 : clamp((t - T.spill) / .4);
const wetAt = t => t > T.rain + .6 && t < T.night;
const me = (t, o = {}) => ({ t, seed: .2, pants: ME.pants, stain: stainAt(t), wet: wetAt(t), ...o });

function fmtClock(min) { min = ((Math.round(min) % 1440) + 1440) % 1440; let h = Math.floor(min / 60), m = min % 60; const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return `${h}:${String(m).padStart(2, '0')} ${ap}`; }
function speedLines(ctx, t, a = .5, dir = 1) { const r = rng(Math.floor(t * 12)); ctx.save(); ctx.strokeStyle = `rgba(255,255,255,${a})`; ctx.lineWidth = 4; for (let i = 0; i < 14; i++) { const y = 150 + r() * 780, x = r() * W; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - dir * (80 + r() * 160), y); ctx.stroke(); } ctx.restore(); }
function sweat(ctx, x, y, t, s = 1) { for (let i = 0; i < 2; i++) { const p = (t * 1.6 + i * .5) % 1; ctx.fillStyle = `rgba(150,210,255,${1 - p})`; ell(ctx, x + i * 30 * s, y + p * 60 * s, 8 * s, 12 * s); ctx.fill(); } }
function chipT(ctx, t, t0, s, x, y, o = {}) { L.chip(ctx, t, t0, s, x, y, { size: 40, ...o }); }

const scenes = [
  // ---------------- COLD OPEN ----------------
  { s: T.cold, e: T.toDay, cam: [1.3, 1.12, 760, 470], draw(ctx, t, f) {
      const rw = clamp((t - T.rew) / (T.toDay - T.rew));
      const shadow = .95 - rw * .9;
      bed(ctx, t, { shadow, phone: false, clock: rw > 0 ? fmtClock(187 - E.in(rw) * (19 * 60 + 25)).replace(/ (AM|PM)/, '') : '3:07', guy: { mood: 'panic', look: .1, lookY: -.9 } });
      thought(ctx, t, T.coldQ, T.rew - .1, 'How did today get this bad?', 800, 300, { size: 56, maxW: 1100, glow: 'rgba(255,60,60,.7)' });
      if (rw > 0) { // VHS rewind
        for (let i = 0; i < 8; i++) { ctx.fillStyle = `rgba(255,255,255,${.08 + .08 * Math.random()})`; ctx.fillRect(0, (t * 1400 + i * 140) % H, W, 4 + Math.random() * 8); }
        ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = `rgba(255,0,80,${.12 * rw})`; ctx.fillRect(6, 0, W, H); ctx.fillStyle = `rgba(0,200,255,${.12 * rw})`; ctx.fillRect(-6, 0, W, H); ctx.restore();
        text(ctx, '◀◀  REWIND', 1500, 200, { size: 54, weight: 900, color: '#fff', alpha: (Math.floor(t * 4) % 2) ? 1 : .6 });
        const mins = 187 - E.in(rw) * (19 * 60 + 25); digitalText(ctx, fmtClock(mins), 1500, 300, 70, 1);
        if (t > T.toDay - .4) { ctx.fillStyle = `rgba(255,250,235,${clamp((t - (T.toDay - .4)) / .4)})`; ctx.fillRect(0, 0, W, H); }
      }
    } },

  // ---------------- 1. ALARM ----------------
  { s: T.toDay, e: T.rush, cam: [1.05, 1.12, 900, 560], flash: true, shake: [[T.fall, .4, 16]], draw(ctx, t) {
      const ring = t < T.jump; const shk = ring ? Math.sin(t * 60) * 4 : 0;
      const inBed = t < T.jump;
      bed(ctx, t, { day: true, phone: false, noGuy: !inBed, clock: '7:42', guy: { mood: t > T.wake ? 'shock' : 'asleep', look: .2, lookY: t > T.wake ? -.2 : 0, headDY: t > T.wake ? -14 : 0 } });
      L.rays(ctx, 1540, 300, t, { n: 7, len: 1500, a: .16, dir: Math.PI * .8, spread: .7 });
      if (ring) { ctx.save(); ctx.translate(shk, 0); digitalText(ctx, '7:42', 205, 661, 40, 1); ctx.restore(); for (let i = 0; i < 3; i++) { ctx.strokeStyle = 'rgba(255,90,60,.8)'; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(205, 655, 80 + i * 26 + (t * 60 % 26), -1.2, -.3); ctx.stroke(); ctx.beginPath(); ctx.arc(205, 655, 80 + i * 26 + (t * 60 % 26), Math.PI + .3, Math.PI + 1.2); ctx.stroke(); } }
      // shoes on the floor
      ctx.fillStyle = '#2c2c34'; rr(ctx, 1170, 905, 90, 34, 14); ctx.fill(); rr(ctx, 1270, 912, 90, 30, 14); ctx.fill(); ctx.fillStyle = '#e8e8ee'; ctx.fillRect(1170, 930, 90, 8); ctx.fillRect(1270, 934, 90, 8);
      if (!inBed) {
        const air = clamp((t - T.jump) / .35);
        if (t < T.trip) { const x = lerp(640, 1140, E.inOut(clamp((t - T.jump) / (T.trip - T.jump)))); const y = 930 - Math.sin(air * Math.PI) * 120 * (air < 1 ? 1 : 0);
          G.guy(ctx, x, y, .5, me(t, { mood: 'panic', walk: t * 17, lean: .18, look: .6 })); speedLines(ctx, t, .35);
        } else { const k = E.in(clamp((t - T.trip) / (T.fall - T.trip))); const bounce = t > T.fall ? Math.abs(Math.sin((t - T.fall) * 14)) * Math.exp(-(t - T.fall) * 6) * 10 : 0;
          G.guy(ctx, 1150, 935 - bounce, .5, me(t, { mood: t > T.fall + .3 ? 'cringe' : 'shock', lean: lerp(.18, 1.5, k), look: .6, footF: [60, -40 * k], lh: [-40, -900], rh: [60, -880], bendB: -1, bendF: -1 }));
          if (t > T.fall) { const p = clamp((t - T.fall) / .6); for (let i = 0; i < 8; i++) { ctx.fillStyle = `rgba(200,180,150,${.6 * (1 - p)})`; circle(ctx, 1380 + Math.cos(i) * 140 * p + i * 20, 930 - Math.abs(Math.sin(i)) * 60 * p, 20 + p * 30); ctx.fill(); }
            for (let i = 0; i < 3; i++) { const a = t * 4 + i * 2.1; text(ctx, '✦', 1560 + Math.cos(a) * 60, 780 + Math.sin(a) * 18, { size: 34, color: '#f2c14e', alpha: clamp((t - T.fall) / .3) }); } }
        }
      }
      chipT(ctx, t, T.alarmNote, 'ALARM SET FOR 7:00', 1100, 230, { bg: '#ff5a4f', color: '#fff', until: T.jump });
      thought(ctx, t, T.nono, T.jump + .4, 'No no no.', 1100, 330, { size: 70, color: '#1b1b22', glow: 'rgba(255,255,255,.0)' });
    } },

  // ---------------- 2. THE RUSH ----------------
  { s: T.hop, e: T.toastS, cam: [1.0, 1.08, 960, 560], flash: true, draw(ctx, t) {
      S2.bathroom(ctx);
      const hop = Math.abs(Math.sin(t * 9)); const x = 820 + Math.sin(t * 2.2) * 160;
      G.guy(ctx, x, 940 - hop * 60, .55, me(t, { mood: 'panic', look: .5, footB: [-40, 0], footF: [90, -260], lean: Math.sin(t * 4.5) * .12, lh: [70, -300], bendB: -1, rh: [80, -650], bendF: -1.4,
        propFront(ctx, h) { ctx.fillStyle = '#4fb3ff'; ctx.save(); ctx.translate(h[0] + 20, h[1] - 10); ctx.rotate(-.3); rr(ctx, -6, -110, 14, 120, 6); ctx.fill(); ctx.restore(); ctx.fillStyle = '#fff'; for (let i = 0; i < 6; i++) { circle(ctx, h[0] + 40 + Math.sin(t * 9 + i) * 20, h[1] - 60 + i * 6, 10 + (i % 3) * 4); ctx.fill(); } } }));
      speedLines(ctx, t, .25);
      chipT(ctx, t, T.hop + .5, 'LATE BY 51 MIN', 960, 200, { bg: '#ff5a4f', color: '#fff', size: 44 });
    } },
  { s: T.toastS, e: T.bus, cam: [1.05, 1.15, 980, 600], flash: true, shake: [[T.spill, .3, 10]], draw(ctx, t) {
      S2.kitchenDay(ctx);
      const pop = t > T.burn ? (t - T.burn) / .9 : 0; S2.toaster(ctx, 1320, 640, t, clamp((t - T.toastS) / .8), pop);
      const sp = clamp((t - T.spill) / .25);
      G.guy(ctx, 820, 960, .56, me(t, { mood: t > T.spill + .2 ? 'panic' : t > T.burn ? 'shock' : 'tired', look: t > T.burn && t < T.spill ? .8 : .2, rh: [150 + sp * 30, -520 + sp * 60], bendF: -1,
        propFront(ctx, h) { ctx.save(); ctx.translate(h[0] + 20, h[1] - 20); ctx.rotate(-sp * 1.6); ctx.fillStyle = '#f4ece0'; rr(ctx, -34, -40, 68, 80, 10); ctx.fill(); ctx.strokeStyle = '#f4ece0'; ctx.lineWidth = 12; ctx.beginPath(); ctx.arc(40, 0, 20, -1.2, 1.2); ctx.stroke(); ctx.restore(); } }));
      if (t > T.spill) { const p = clamp((t - T.spill) / .6); for (let i = 0; i < 14; i++) { const a = -1.2 - i * .12; ctx.fillStyle = `rgba(110,64,28,${1 - p})`; circle(ctx, 900 + Math.cos(a) * 160 * p - 40, 640 + Math.sin(a) * -120 * p + p * p * 200, 9 + (i % 3) * 3); ctx.fill(); } }
      chipT(ctx, t, T.burn + .2, 'BURNT', 1320, 300, { bg: '#2b2b2b', color: '#fff' });
      chipT(ctx, t, T.spill + .5, 'COFFEE 1  –  WHITE SHIRT 0', 820, 220, { bg: '#7a4f34', color: '#fff' });
    } },

  // ---------------- 3. MISSED BUS ----------------
  { s: T.run, e: T.cls, cam: [1.0, 1.04, 960, 560], shake: [[T.thunder, .5, 10]], draw(ctx, t) {
      const rk = clamp((t - T.rain) / 1);
      S2.street(ctx, t, 'morning'); if (rk > 0) { ctx.save(); ctx.globalAlpha = rk; S2.street(ctx, t, 'rain'); ctx.restore(); }
      const doorK = clamp((t - T.doors) / .3); const bx = 1150 + (t > T.drive ? Math.pow(t - T.drive, 2) * 420 : 0);
      S2.bus(ctx, bx, 960, t, doorK, t > T.drive ? Math.pow(t - T.drive, 2) : 0);
      if (t > T.drive) { for (let i = 0; i < 6; i++) { const p = ((t - T.drive) * 1.5 + i / 6) % 1; ctx.fillStyle = `rgba(90,90,90,${.35 * (1 - p)})`; circle(ctx, bx - 80 - p * 200, 920 - p * 60, 20 + p * 40); ctx.fill(); } }
      const arrive = t >= T.doors + .15; const x = arrive ? 1075 - (t < T.doors + .5 ? Math.sin(clamp((t - T.doors - .15) / .35) * Math.PI) * 30 : 0) : lerp(-80, 1075, clamp((t - T.run) / (T.doors + .15 - T.run)));
      G.guy(ctx, x, 950, .5, me(t, { backpack: ME.backpack, mood: t > T.drive ? 'blank' : arrive ? 'shock' : 'panic', walk: arrive ? null : t * 15, lean: arrive ? 0 : .22, look: t > T.drive ? .2 : .6, lh: arrive && t < T.drive + .5 ? [60, -560] : null }));
      if (!arrive) speedLines(ctx, t, .3);
      if (t > T.doors + .15 && t < T.doors + .9) text(ctx, 'BONK', 1150, 520, { size: 56, weight: 900, color: '#fff', stroke: '#1b1b22', sw: 10, alpha: 1 - clamp((t - T.doors - .6) / .3) });
      S2.rain(ctx, t, rk);
      if (t > T.thunder && t < T.thunder + .35) { ctx.fillStyle = `rgba(255,255,255,${.8 * (1 - (t - T.thunder) / .35)})`; ctx.fillRect(0, 0, W, H); }
      thought(ctx, t, T.ofc, T.cls, 'Of course.', 960, 330, { size: 78 });
    } },

  // ---------------- 4. THE PRESENTATION ----------------
  { s: T.enter, e: T.front, cam: [1.0, 1.06, 960, 560], draw(ctx, t) {
      S2.classroom(ctx, t);
      const x = lerp(-60, 180, E.out(clamp((t - T.enter) / 1.2)));
      G.guy(ctx, x, 980, .5, me(t, { backpack: ME.backpack, mood: 'blank', walk: t < T.enter + 1.2 ? t * 8 : null, look: .6 }));
      ctx.fillStyle = 'rgba(120,170,230,.35)'; ell(ctx, x + 10, 985, 90, 12); ctx.fill(); // puddle
      S2.teacher(ctx, 780, 980, .48, t, { flip: 1, look: .8, point: t > T.point, mood: 'tired' });
      for (let i = 0; i < 6; i++) S2.student(ctx, t, i, { look: t > T.enter + .5 ? .9 : .2, mood: 'blank' });
      speech(ctx, t, T.point + .2, T.front, "You're late. You're up.", 620, 380, 700, 470, { size: 40 });
    } },
  { s: T.front, e: T.lunch, cam: [1.0, 1.0, 960, 560], shake: [[T.laugh, 1.2, 5]], draw(ctx, t) {
      const blank = t > T.blank;
      S2.classroom(ctx, t, { slide: t > T.frozen ? 'frozen' : null });
      const laugh = t > T.laugh;
      G.guy(ctx, 830, 990, .52, me(t, { backpack: ME.backpack, mood: laugh ? 'cringe' : blank ? 'blank' : 'worried', eye: blank && !laugh ? 'wide' : null, look: .5, lh: [-130, -330], rh: [130, -330] }));
      if (laugh) sweat(ctx, 960, 560, t, 1.2);
      for (let i = 0; i < 6; i++) S2.student(ctx, t, i, { mood: laugh || (i === 1 && t > T.giggle) ? 'laugh' : 'blank', laugh: laugh || (i === 1 && t > T.giggle), look: .8 });
      if (blank && t < T.giggle) { const a = clamp((t - T.blank) / .3); ctx.save(); ctx.globalAlpha = a * .35 * (t < T.blank + .3 ? 2 : 1); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H); ctx.restore(); F.bubbleDark(ctx, t, T.blank, '. . .', 900, 300, { size: 60, edge: 'rgba(255,255,255,.4)', until: T.giggle }); }
      thought(ctx, t, T.say, T.giggle, 'Say something. Anything.', 1160, 180, { size: 56, color: '#1b1b22', glow: 'rgba(255,255,255,.0)' });
      if (t > T.giggle) pop(ctx, t, T.giggle, T.laugh, 'hehe', 1430, 560, { size: 36, color: '#1b1b22', shadow: null });
      if (laugh) { const r = rng(3); for (let i = 0; i < 7; i++) pop(ctx, t, T.laugh + i * .12, T.lunch, 'HA' + 'HA'.repeat(1 + (i % 3)), 1050 + r() * 760, 200 + r() * 380, { size: 44 + r() * 30, color: '#1b1b22', shadow: null, rot: (r() - .5) * .3 }); }
    } },

  // ---------------- 5. LUNCH ALONE ----------------
  { s: T.lwalk, e: T.chatPOV, cam: [1.0, 1.05, 960, 560], draw(ctx, t) {
      S2.cafeteria(ctx);
      const fr = [[300, '#7ad48a', null], [500, '#4f8cff', null], [700, '#ff7aa8', 'pony']];
      fr.forEach(([x, col, hair], i) => G.guy(ctx, x, 900, .42, { mood: 'laugh', t, seed: i, shirt: col, hair, look: i === 2 ? -.6 : .5, talk: Math.abs(Math.sin(t * 6 + i)), mouth: Math.sin(t * 3 + i) > 0 ? 'o' : null, lh: [-80, -380], rh: [90, -420] }));
      S2.bagOnSeat(ctx, 900, 770);
      S2.lunchTable(ctx, 200, 740, 820);
      for (const x of [380, 600]) { ctx.fillStyle = '#fff'; ell(ctx, x, 740, 40, 10); ctx.fill(); }
      // small table for one
      S2.lunchTable(ctx, 1480, 800, 300);
      const sat = t > T.sit; const x = sat ? 1640 : lerp(-60, 1560, clamp((t - T.lwalk) / (T.sit - T.lwalk - .2)));
      const slow = t > T.pass - .4 && t < T.pass + .8;
      if (!sat) G.guy(ctx, x, 1040, .52, me(t, { mood: slow ? 'sad' : 'tired', walk: t * (slow ? 4 : 7), look: slow ? -.8 : .5, headRot: slow ? -.1 : 0, rh: [170, -420], bendF: -1, propFront(ctx, h) { S2.tray(ctx, h[0] + 40, h[1] + 10, 1); } }));
      else { G.guy(ctx, x, 960, .44, me(t, { mood: 'sad', sit: 1, look: .2, lookY: .5 })); S2.lunchTable(ctx, 1480, 800, 300); S2.tray(ctx, 1600, 798, .8); }
      chipT(ctx, t, T.pass, 'SAVED.  (not for you)', 900, 560, { bg: '#6a4fb3', color: '#fff', size: 34, until: T.sit + .6 });
    } },
  { s: T.chatPOV, e: T.crushS, cam: [1.0, 1.06, 960, 600], vig: .7, draw(ctx, t) {
      S2.cafeteria(ctx); ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillRect(0, 0, W, H);
      G.povPhone(ctx, 960, 610, .78, (x, w, h) => SC.groupChat(x, w, h, t, { time: '12:41', photo: 1, notif: t > T.ping ? E.out(clamp((t - T.ping) / .3)) : 0 }), { glow: .5 });
      thought(ctx, t, T.ping + .8, T.crushS, "You're not in it.", 1480, 480, { size: 56 });
    } },

  // ---------------- 6. THE CRUSH ----------------
  { s: T.approach, e: T.reveal, cam: [1.28, 1.32, 920, 560], draw(ctx, t) {
      S.hallway(ctx, t, 0);
      const gx = lerp(300, 640, clamp((t - T.approach) / (T.wave - T.approach)));
      G.guy(ctx, gx, 930, .55, { mood: t > T.waveBack ? 'happy' : 'tired', hair: 'pony', t, seed: .7, look: .6, walk: t < T.wave ? t * 6 : null, rh: t > T.waveBack ? [150, -640 - Math.abs(Math.sin(t * 6)) * 60] : null, bendF: -1 });
      const waving = t > T.wave;
      G.guy(ctx, 1220, 930, .55, me(t, { mood: waving ? 'happy' : 'shy', flip: 1, look: .6, blush: waving ? 1 : .4, rh: waving ? [150, -660 - Math.abs(Math.sin(t * 6)) * 60] : null, bendF: -1 }));
    } },
  { s: T.reveal, e: T.cafe, cam: [1.0, 1.04, 1000, 560], draw(ctx, t) {
      S.hallway(ctx, t, 0);
      const walk = clamp((t - T.reveal - .3) / 2.4); const gx = lerp(640, 1420, E.inOut(walk));
      const drop = E.inOut(clamp((t - T.drop) / 2));
      G.guy(ctx, 1220, 930, .55, me(t, { mood: drop > .5 ? 'sad' : 'awkward', flip: 1, look: drop > .3 ? -.5 : .6, blush: 1 - drop, rh: [lerp(150, 90, drop), lerp(-680, -260, drop)], bendF: -1 }));
      G.guy(ctx, gx, 930, .55, { mood: 'happy', hair: 'pony', t, seed: .7, look: .6, walk: walk > 0 && walk < 1 ? t * 6 : null, rh: walk < .3 ? [150, -640 - Math.abs(Math.sin(t * 6)) * 60] : null, bendF: -1 });
      G.guy(ctx, 1640, 930, .6, { mood: 'cool', hair: 'cap', capCol: '#1f2a44', t, seed: 2.2, flip: 1, look: .6, shirt: '#2b2b33', pants: '#1f2a44', rh: walk < .8 ? [150, -660 - Math.abs(Math.sin(t * 5)) * 50] : null, bendF: -1 });
      pop(ctx, t, T.drop + .6, T.cafe, '. . .', 1220, 300, { size: 64, color: '#1b1b22', shadow: null });
    } },

  // ---------------- 7. "YOU TOO" ----------------
  { s: T.cafe, e: T.call, cam: [1.12, 1.18, 960, 560], shake: [[T.pause, .25, 8]], draw(ctx, t) {
      S2.cafe(ctx, t);
      const frozen = t > T.pause && t < T.speed;
      G.guy(ctx, 1260, 905, .62, { mood: t > T.pause ? 'blank' : 'happy', hair: 'bun', t: frozen ? T.pause : t, seed: 4, flip: 1, look: .5, shirt: '#2f6b4f', rh: t < T.enjoy + .9 ? [170, -470] : null, bendF: -1,
        propFront(ctx, h) { if (t < T.enjoy + .9) S2.coffeeCup(ctx, h[0] + 40, h[1] + 10, 1.4); } });
      ctx.fillStyle = '#7a4f34'; ctx.fillRect(0, 640, W, 40); ctx.fillStyle = '#5c3b2a'; ctx.fillRect(0, 680, W, 260); // counter front over her legs
      const out = clamp((t - T.speed) / 1.5); const x = t < T.speed ? 760 : lerp(760, -120, out);
      const hasCup = t > T.enjoy + .9;
      G.guy(ctx, x, 1060, .56, me(t, { mood: t > T.speed ? 'cringe' : t > T.pause + .4 ? 'cringe' : 'happy', flip: t > T.speed ? 1 : 0, look: .5, walk: t > T.speed ? t * 16 : null, lean: t > T.speed ? .12 : 0, rh: hasCup ? [160, -470] : null, bendF: -1,
        propFront(ctx, h) { if (hasCup) S2.coffeeCup(ctx, h[0] + 40, h[1] + 10, 1.4); } }));
      if (t > T.speed) { sweat(ctx, x + 60, 470, t, 1.2); speedLines(ctx, t, .25, -1); }
      speech(ctx, t, T.enjoy, T.pause + 1, 'Enjoy your coffee!', 1300, 250, 1270, 360, { size: 44 });
      speech(ctx, t, T.youtoo, T.speed, 'You too!', 700, 340, 760, 460, { size: 58 });
      if (frozen) { pop(ctx, t, T.pause + .3, T.speed, '. . .', 1560, 330, { size: 60 }); ctx.save(); ctx.globalCompositeOperation = 'saturation'; ctx.fillStyle = `rgba(128,128,128,${clamp((t - T.pause) / .2) * .8})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
      if (t > T.bell) { const a = 1 - clamp((t - T.bell) / .8); text(ctx, '♪ ding', 280, 200, { size: 40, weight: 800, color: '#f2c14e', alpha: a }); }
    } },

  // ---------------- 8. MOM CALLS ----------------
  { s: T.call, e: T.home, cam: [1.0, 1.06, 960, 600], vig: .75, draw(ctx, t) {
      ctx.drawImage(S.cached('rainBlur', x => { x.filter = 'blur(12px)'; S2.street(x, 0, 'rain'); x.filter = 'none'; x.fillStyle = 'rgba(10,14,24,.45)'; x.fillRect(0, 0, W, H); }), 0, 0);
      const ringing = t > T.ring && t < T.decline; const buzz = ringing ? Math.sin(t * 70) * 5 * (Math.sin(t * 6) > 0 ? 1 : 0) : 0;
      ctx.save(); ctx.translate(buzz, 0);
      G.povPhone(ctx, 960, 610, .78, (x, w, h) => { SC.callScreen(x, w, h, t, { time: '6:12', declined: t > T.decline, notif: t > T.momText ? E.out(clamp((t - T.momText) / .35)) : 0 });
        const r = rng(8); for (let i = 0; i < 22; i++) { x.fillStyle = 'rgba(200,220,255,.28)'; ell(x, r() * w, r() * h, 5 + r() * 7, 7 + r() * 9); x.fill(); } },
        { thumbL: t > T.decline - .5 && t < T.decline + .3 ? { x: 100, y: 670 } : null, press: 0 });
      ctx.restore();
      S2.rain(ctx, t, .8, 5);
      thought(ctx, t, T.ring + .8, T.decline - .1, 'Mom.', 1460, 440, { size: 64 });
      thought(ctx, t, T.notnow, T.home, 'Not now.', 470, 470, { size: 66 });
    } },

  // ---------------- 9. WALK HOME ----------------
  { s: T.street, e: T.doorShut, cam: [1.0, 1.12, 960, 620], fadeIn: .4, draw(ctx, t) {
      S2.street(ctx, t, 'night');
      const x = lerp(160, 1500, clamp((t - T.street) / (T.doorShut - T.street))); const ph = t * 5;
      G.guy(ctx, x, 880, .3, me(t, { backpack: ME.backpack, mood: 'sad', walk: ph, look: .4, lookY: .6, headRot: .1, rim: 'rgba(255,200,120,.6)', rimDX: -4, rimDY: -3 }));
      for (let k = 0; k < 12; k++) { const tt = T.street + k * Math.PI / 5; const px = lerp(160, 1500, clamp((tt - T.street) / (T.doorShut - T.street))); if (Math.abs(px - 420) < 160 || Math.abs(px - 1180) < 220) S2.splash(ctx, t, tt, px, 900); }
      S2.rain(ctx, t, .9, 7);
      const ta = clamp((t - (T.street + 1)) / .9) * (1 - clamp((t - (T.doorShut - 1.2)) / .8));
      if (ta > 0) { ctx.save(); ctx.globalAlpha = ta * .45; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); ctx.restore();
        F.digitalText(ctx, '3AM', 960, 360, 170, ta); text(ctx, 'THOUGHTS', 960, 500, { size: 86, weight: 300, color: '#f4f1ea', alpha: ta, track: 24 });
        text(ctx, 'an animated short film', 960, 580, { size: 28, weight: 500, color: 'rgba(244,241,234,.65)', alpha: ta, track: 6 }); }
    } },
  { s: T.doorShut, e: T.night, cam: [1.05, 1.15, 1100, 600], fadeOut: .9, shake: [[T.flop + .25, .3, 8]], draw(ctx, t) {
      bed(ctx, t, { phone: false, noGuy: true, case: false, shadow: 0 });
      if (t < T.flop) { const x = lerp(1880, 1440, clamp((t - T.doorShut) / (T.flop - T.doorShut - .3)));
        G.guy(ctx, x, 935, .5, me(t, { backpack: ME.backpack, mood: 'sad', flip: 1, walk: t < T.flop - .3 ? t * 5 : null, look: .3, lookY: .5, rim: RIM })); }
      else { const k = E.in(clamp((t - T.flop) / .25)); const b = t > T.flop + .25 ? Math.abs(Math.sin((t - T.flop - .25) * 12)) * Math.exp(-(t - T.flop) * 5) * 14 : 0;
        G.guy(ctx, 1350, 660 - b, .5, me(t, { backpack: ME.backpack, mood: 'sad', flip: 1, lean: lerp(.7, 1.5708, k), back: k > .6, look: .3, lh: [-60, -880], rh: [60, -880], bendB: -1, bendF: -1, rim: RIM }));
        pop(ctx, t, T.flop + .4, T.night, 'flop.', 900, 460, { size: 54, color: 'rgba(255,255,255,.85)' }); }
    } },
];

module.exports = { scenes, ME, me, fmtClock };
