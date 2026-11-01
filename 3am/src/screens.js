// Phone UI screens, drawn into the 400x820 phone canvas.
const L = require('./lib');
const { clamp, E, inv, rr, circle, ell, vgrad, rgrad, text } = L;
const G = require('./guy');

function status(x, w, o = {}) {
  text(x, o.time || '3:07', 44, 30, { size: 20, weight: 700, color: '#fff', align: 'left' });
  const bat = o.battery ?? 31; const low = bat <= 5;
  x.strokeStyle = low ? '#ff453a' : 'rgba(255,255,255,.85)'; x.lineWidth = 2; rr(x, w - 70, 21, 36, 18, 5); x.stroke();
  x.fillStyle = low ? '#ff453a' : '#fff'; rr(x, w - 67, 24, Math.max(2, 30 * bat / 100), 12, 3); x.fill(); x.fillRect(w - 33, 27, 3, 6);
  if (o.showPct) text(x, bat + '%', w - 80, 30, { size: 17, weight: 700, color: low ? '#ff453a' : '#fff', align: 'right' });
  if (o.charging) { x.fillStyle = '#34c759'; x.beginPath(); x.moveTo(w - 50, 22); x.lineTo(w - 58, 32); x.lineTo(w - 51, 32); x.lineTo(w - 55, 40); x.lineTo(w - 45, 29); x.lineTo(w - 52, 29); x.closePath(); x.fill(); }
}
function wallpaper(x, w, h) {
  x.fillStyle = vgrad(x, 0, h, [[0, '#1b1f4a'], [.55, '#2b1a4a'], [1, '#0c0d1c']]); x.fillRect(0, 0, w, h);
  x.fillStyle = rgrad(x, w * .7, h * .25, 5, 260, [[0, 'rgba(160,140,255,.35)'], [1, 'rgba(0,0,0,0)']]); x.fillRect(0, 0, w, h);
  x.fillStyle = 'rgba(0,0,0,.35)'; x.beginPath(); x.moveTo(0, h * .78); x.quadraticCurveTo(w * .4, h * .7, w, h * .8); x.lineTo(w, h); x.lineTo(0, h); x.fill();
}
function notifCard(x, w, y, app, title, body, a = 1, o = {}) {
  x.save(); x.globalAlpha *= a; x.fillStyle = 'rgba(255,255,255,.16)'; rr(x, 16, y, w - 32, 96, 22); x.fill();
  x.fillStyle = o.icon || '#34c759'; rr(x, 30, y + 16, 36, 36, 9); x.fill();
  text(x, app, 78, y + 26, { size: 15, weight: 600, color: 'rgba(255,255,255,.7)', align: 'left' });
  text(x, o.when || 'now', w - 34, y + 26, { size: 14, weight: 500, color: 'rgba(255,255,255,.6)', align: 'right' });
  text(x, title, 78, y + 52, { size: 19, weight: 800, color: '#fff', align: 'left' });
  text(x, body, 78, y + 76, { size: 17, weight: 500, color: 'rgba(255,255,255,.9)', align: 'left' });
  x.restore();
}
function lock(x, w, h, t, o = {}) {
  wallpaper(x, w, h); status(x, w, o);
  if (o.charging) { text(x, `Charging  ${o.battery}%`, w / 2, 250, { size: 18, weight: 600, color: '#34c759' }); }
  text(x, o.day || 'Tuesday', w / 2, 120, { size: 22, weight: 600, color: 'rgba(255,255,255,.85)' });
  text(x, o.time || '3:07', w / 2, 200, { size: 104, weight: 300, color: '#fff' });
  if (o.notifs) o.notifs(x, w, h);
  x.fillStyle = 'rgba(255,255,255,.8)'; rr(x, w / 2 - 70, h - 22, 140, 6, 3); x.fill();
}
function music(x, w, h, t, o = {}) {
  x.fillStyle = vgrad(x, 0, h, [[0, o.romance ? '#5a1f3a' : '#22305e'], [1, '#08090f']]); x.fillRect(0, 0, w, h); status(x, w, o);
  const ax = 50, ay = 110, as = w - 100;
  x.fillStyle = vgrad(x, ay, ay + as, [[0, o.romance ? '#ff7a9a' : '#6c7dff'], [1, o.romance ? '#7a1c48' : '#1f1b4d']]); rr(x, ax, ay, as, as, 20); x.fill();
  x.fillStyle = 'rgba(255,255,255,.9)'; circle(x, ax + as * .65, ay + as * .35, 40); x.fill(); x.fillStyle = o.romance ? '#c23c6b' : '#3a3f9a'; circle(x, ax + as * .65 + 16, ay + as * .35 - 10, 36); x.fill();
  text(x, o.romance ? 'feelings at 3am' : 'slow songs for 3am', w / 2, ay + as + 50, { size: 26, weight: 800, color: '#fff' });
  text(x, 'Playlist', w / 2, ay + as + 84, { size: 19, weight: 500, color: 'rgba(255,255,255,.6)' });
  const p = o.progress ?? ((t * .01) % 1); x.fillStyle = 'rgba(255,255,255,.2)'; rr(x, 40, ay + as + 130, w - 80, 6, 3); x.fill(); x.fillStyle = '#fff'; rr(x, 40, ay + as + 130, (w - 80) * p, 6, 3); x.fill(); circle(x, 40 + (w - 80) * p, ay + as + 133, 9); x.fill();
  // controls
  const cy = ay + as + 220; x.fillStyle = '#fff';
  if (o.paused) { x.beginPath(); x.moveTo(w / 2 - 20, cy - 30); x.lineTo(w / 2 + 30, cy); x.lineTo(w / 2 - 20, cy + 30); x.fill(); }
  else { x.fillRect(w / 2 - 22, cy - 28, 14, 56); x.fillRect(w / 2 + 8, cy - 28, 14, 56); }
  for (const s of [-1, 1]) { x.beginPath(); x.moveTo(w / 2 + s * 110, cy - 18); x.lineTo(w / 2 + s * 110 + s * 26, cy); x.lineTo(w / 2 + s * 110, cy + 18); x.fill(); }
  // eq bars
  if (!o.paused) for (let i = 0; i < 18; i++) { const v = .3 + .7 * Math.abs(Math.sin(t * 3 + i * .8) * Math.sin(t * 1.7 + i)); x.fillStyle = 'rgba(255,255,255,.5)'; x.fillRect(48 + i * 17, h - 70 - v * 50, 9, v * 50); }
}
const APPS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#a855f7', '#14b8a6', '#eab308', '#6366f1', '#ec4899', '#0ea5e9', '#84cc16', '#f97316', '#64748b', '#10b981', '#8b5cf6', '#06b6d4'];
function home(x, w, h, t, o = {}) {
  wallpaper(x, w, h); status(x, w, o);
  const cols = 4, size = 66, gx = (w - cols * size) / (cols + 1);
  for (let i = 0; i < 16; i++) { const cx = gx + (i % cols) * (size + gx), cy = 90 + Math.floor(i / cols) * 112;
    if (i === 10 && o.temptation != null) continue;
    x.fillStyle = APPS[i]; x.globalAlpha = 1 - (o.temptation || 0) * .55; rr(x, cx, cy, size, size, 16); x.fill(); x.globalAlpha = 1;
    x.fillStyle = 'rgba(255,255,255,.55)'; rr(x, cx + size * .25, cy + size * .25, size * .5, size * .5, 6); x.fill(); }
  if (o.temptation != null) { // the app we don't name: a dark icon with a lock, glowing red
    const i = 10, cx = gx + (i % cols) * (size + gx), cy = 90 + Math.floor(i / cols) * 112, k = o.temptation;
    x.save(); x.shadowColor = `rgba(255,40,60,${.9 * k})`; x.shadowBlur = 40 * k; x.fillStyle = '#16060a'; rr(x, cx, cy, size, size, 16); x.fill(); x.restore();
    x.strokeStyle = `rgba(255,60,80,${.4 + .6 * k})`; x.lineWidth = 3; rr(x, cx, cy, size, size, 16); x.stroke();
    x.fillStyle = '#ff4d63'; rr(x, cx + 21, cy + 32, 24, 20, 4); x.fill(); x.beginPath(); x.arc(cx + 33, cy + 32, 9, Math.PI, 0); x.lineWidth = 5; x.strokeStyle = '#ff4d63'; x.stroke();
  }
  x.fillStyle = 'rgba(255,255,255,.18)'; rr(x, 16, h - 120, w - 32, 96, 30); x.fill();
  for (let i = 0; i < 4; i++) { x.fillStyle = APPS[i + 8]; rr(x, 36 + i * 88, h - 104, 64, 64, 16); x.fill(); }
}
const FEED = [
  ['Rohan', '#4f8cff', 'Got the job!! Senior Designer at Studio North', 'job'],
  ['Priya', '#ff7aa8', "He said YES. We're engaged!!", 'ring'],
  ['Kabir', '#ffb547', 'New car, new me', 'car'],
  ['Sana', '#7ad48a', 'Finally moved to Berlin', 'plane'],
  ['Aditya', '#a98bff', '1 year of my startup today', 'chart'],
  ['Meera', '#4fd1c5', 'Graduated with honours!', 'cap'],
];
function feed(x, w, h, t, o = {}) {
  x.fillStyle = '#0d0f14'; x.fillRect(0, 0, w, h);
  const scroll = o.scroll || 0; x.save(); x.translate(0, -scroll);
  for (let i = 0; i < 12; i++) { const [name, col, msg, pic] = FEED[i % FEED.length]; const y = 70 + i * 330;
    x.fillStyle = col; circle(x, 40, y + 24, 20); x.fill(); text(x, name, 72, y + 18, { size: 18, weight: 800, color: '#fff', align: 'left' }); text(x, '2h', 72, y + 40, { size: 14, weight: 500, color: 'rgba(255,255,255,.5)', align: 'left' });
    text(x, msg, 20, y + 76, { size: 17, weight: 600, color: '#fff', align: 'left' });
    x.fillStyle = vgrad(x, y + 100, y + 300, [[0, col], [1, '#1a1c25']]); rr(x, 16, y + 98, w - 32, 190, 14); x.fill();
    feedPic(x, pic, w / 2, y + 196);
    text(x, '♥ ' + (120 + i * 37), 24, y + 310, { size: 15, weight: 700, color: 'rgba(255,255,255,.75)', align: 'left' });
  }
  x.restore();
  x.fillStyle = '#0d0f14'; x.fillRect(0, 0, w, 56); status(x, w, o);
}
function feedPic(x, kind, cx, cy) {
  x.fillStyle = 'rgba(255,255,255,.85)'; x.strokeStyle = 'rgba(255,255,255,.85)'; x.lineWidth = 8; x.lineCap = 'round';
  if (kind === 'ring') { x.beginPath(); x.arc(cx, cy + 14, 34, 0, Math.PI * 2); x.stroke(); x.beginPath(); x.moveTo(cx - 14, cy - 24); x.lineTo(cx, cy - 44); x.lineTo(cx + 14, cy - 24); x.closePath(); x.fill(); }
  else if (kind === 'car') { rr(x, cx - 70, cy - 10, 140, 34, 12); x.fill(); rr(x, cx - 38, cy - 38, 76, 34, 12); x.fill(); x.fillStyle = '#1a1c25'; circle(x, cx - 40, cy + 26, 14); x.fill(); circle(x, cx + 40, cy + 26, 14); x.fill(); }
  else if (kind === 'chart') { x.beginPath(); x.moveTo(cx - 70, cy + 40); x.lineTo(cx - 30, cy + 10); x.lineTo(cx, cy + 22); x.lineTo(cx + 60, cy - 40); x.stroke(); }
  else if (kind === 'cap') { x.beginPath(); x.moveTo(cx - 70, cy - 10); x.lineTo(cx, cy - 40); x.lineTo(cx + 70, cy - 10); x.lineTo(cx, cy + 20); x.closePath(); x.fill(); rr(x, cx - 36, cy, 72, 34, 6); x.fill(); }
  else if (kind === 'plane') { x.beginPath(); x.moveTo(cx - 70, cy); x.lineTo(cx + 70, cy - 20); x.lineTo(cx + 50, cy + 6); x.closePath(); x.fill(); x.beginPath(); x.moveTo(cx, cy - 8); x.lineTo(cx - 20, cy + 40); x.lineTo(cx + 10, cy - 4); x.fill(); }
  else { rr(x, cx - 50, cy - 30, 100, 70, 10); x.fill(); x.fillStyle = '#1a1c25'; x.fillRect(cx - 50, cy - 8, 100, 6); rr(x, cx - 18, cy - 44, 36, 18, 6); x.lineWidth = 6; x.stroke(); }
}
function lowBattery(x, w, h, a) {
  x.save(); x.globalAlpha = a; x.fillStyle = 'rgba(0,0,0,.45)'; x.fillRect(0, 0, w, h);
  x.fillStyle = 'rgba(40,40,46,.96)'; rr(x, 40, h / 2 - 90, w - 80, 180, 26); x.fill();
  text(x, 'Low Battery', w / 2, h / 2 - 44, { size: 24, weight: 800, color: '#fff' }); text(x, '4% battery remaining', w / 2, h / 2 - 8, { size: 18, weight: 500, color: 'rgba(255,255,255,.75)' });
  x.fillStyle = 'rgba(255,255,255,.15)'; x.fillRect(40, h / 2 + 30, w - 80, 2); text(x, 'Close', w / 2, h / 2 + 62, { size: 20, weight: 700, color: '#0a84ff' });
  x.restore();
}
// chat with Mom. o.typed, o.sent (0..1), o.read, o.typing (0..1), o.reply (0..1)
function chat(x, w, h, t, o = {}) {
  x.fillStyle = '#0b0d12'; x.fillRect(0, 0, w, h); status(x, w, o);
  x.fillStyle = '#16181f'; x.fillRect(0, 50, w, 84); x.fillStyle = '#e7e2d4'; circle(x, 64, 92, 26); x.fill(); x.fillStyle = '#2a2622'; x.beginPath(); x.arc(64, 92, 26, Math.PI, 0); x.fill(); circle(x, 58, 64, 12); x.fill();
  text(x, 'Mom', 104, 82, { size: 22, weight: 800, color: '#fff', align: 'left' });
  text(x, o.typing > .5 && !(o.reply > 0) ? 'typing...' : 'online', 104, 108, { size: 15, weight: 600, color: o.typing > .5 ? '#34c759' : 'rgba(255,255,255,.5)', align: 'left' });
  let y = 170;
  text(x, 'Yesterday', w / 2, y, { size: 14, weight: 600, color: 'rgba(255,255,255,.45)' }); y += 28;
  x.fillStyle = '#1f2230'; rr(x, w / 2 - 120, y, 240, 40, 20); x.fill(); x.fillStyle = '#ff453a'; circle(x, w / 2 - 92, y + 20, 7); x.fill();
  text(x, 'Missed call  6:12 PM', w / 2 + 10, y + 20, { size: 15, weight: 600, color: 'rgba(255,255,255,.75)' }); y += 58;
  const y0 = y; y = msg(x, w, y, "Call me when you're free", false, 1, '6:14 PM'); require('./sets').heart(x, 268, y0 + 26, 9, '#ff5a7a');
  if (o.sent) { text(x, 'Today', w / 2, y + 6, { size: 14, weight: 600, color: 'rgba(255,255,255,.45)' }); y += 34; y = msg(x, w, y, "Sorry I missed your call. Love you.", true, o.sent, '3:59 AM', o.read); }
  if (o.typing > 0 && !(o.reply > 0)) { x.save(); x.globalAlpha = o.typing; x.fillStyle = '#262a35'; rr(x, 16, y, 90, 46, 22); x.fill(); for (let i = 0; i < 3; i++) { const b = Math.max(0, Math.sin(t * 7 - i * .9)); x.fillStyle = `rgba(255,255,255,${.4 + .5 * b})`; circle(x, 40 + i * 21, y + 23 - b * 5, 6); x.fill(); } x.restore(); }
  if (o.reply > 0) { const yr = y; y = msg(x, w, y, 'Bad day? Me too. Call tomorrow', false, o.reply, '4:00 AM'); x.save(); x.globalAlpha = o.reply; require('./sets').heart(x, 300, yr + 50, 9, '#ff5a7a'); x.restore(); }
  x.fillStyle = '#16181f'; x.fillRect(0, h - 96, w, 96); x.fillStyle = '#232633'; rr(x, 16, h - 82, w - 92, 50, 25); x.fill();
  const typed = o.typed || ''; const shown = typed.length > 24 ? '...' + typed.slice(-24) : typed;
  text(x, shown || 'Message', 34, h - 57, { size: 17, weight: 500, color: typed ? '#fff' : 'rgba(255,255,255,.4)', align: 'left' });
  if (typed && (t * 2) % 1 < .5) { x.font = L.font(17, 500); const cw = x.measureText(shown).width; x.fillStyle = '#0a84ff'; x.fillRect(36 + cw, h - 70, 2, 26); }
  x.fillStyle = typed ? '#0a84ff' : '#2c3040'; circle(x, w - 44, h - 57, 24); x.fill(); x.fillStyle = '#fff'; x.beginPath(); x.moveTo(w - 54, h - 57); x.lineTo(w - 34, h - 66); x.lineTo(w - 40, h - 57); x.lineTo(w - 34, h - 48); x.closePath(); x.fill();
}
// incoming call
function callScreen(x, w, h, t, o = {}) {
  x.fillStyle = vgrad(x, 0, h, [[0, '#3a4a5c'], [1, '#141a22']]); x.fillRect(0, 0, w, h); status(x, w, o);
  const pulse = 1 + .06 * Math.sin(t * 6);
  x.fillStyle = 'rgba(255,255,255,.08)'; circle(x, w / 2, 250, 90 * pulse); x.fill();
  x.fillStyle = '#e7e2d4'; circle(x, w / 2, 250, 64); x.fill(); x.fillStyle = '#2a2622'; x.beginPath(); x.arc(w / 2, 250, 64, Math.PI, 0); x.fill(); circle(x, w / 2 - 12, 182, 26); x.fill();
  text(x, 'Mom', w / 2, 380, { size: 40, weight: 700, color: '#fff' }); text(x, o.declined ? 'Call declined' : 'incoming call...', w / 2, 425, { size: 19, weight: 500, color: o.declined ? '#ff453a' : 'rgba(255,255,255,.7)' });
  if (!o.declined) for (const [cx, col, rot] of [[100, '#ff3b30', 2.36], [300, '#34c759', 0]]) { x.fillStyle = col; circle(x, cx, h - 150, 42); x.fill(); x.save(); x.translate(cx, h - 150); x.rotate(rot); x.fillStyle = '#fff'; rr(x, -22, -8, 44, 16, 8); x.fill(); x.fillRect(-22, -8, 10, 22); x.fillRect(12, -8, 10, 22); x.restore(); }
  if (!o.declined) { text(x, 'Decline', 100, h - 88, { size: 16, weight: 600, color: '#fff' }); text(x, 'Accept', 300, h - 88, { size: 16, weight: 600, color: '#fff' }); }
  if (o.notif) notifCard(x, w, 60 - (1 - o.notif) * 120, 'Messages', 'Mom', "Call me when you're free \u2764", o.notif, { when: 'now' });
}
// group chat with a photo you're not in
function groupChat(x, w, h, t, o = {}) {
  x.fillStyle = '#0b0d12'; x.fillRect(0, 0, w, h); status(x, w, o);
  x.fillStyle = '#16181f'; x.fillRect(0, 50, w, 84); x.fillStyle = '#ff7a3d'; circle(x, 64, 92, 26); x.fill();
  text(x, 'Squad', 104, 82, { size: 22, weight: 800, color: '#fff', align: 'left' }); fire(x, 196, 80, 11);
  text(x, 'Aarav, Riya, Kabir, Zoya', 104, 108, { size: 14, weight: 500, color: 'rgba(255,255,255,.5)', align: 'left' });
  const a = o.photo ?? 1; x.save(); x.globalAlpha = a;
  x.fillStyle = '#262a35'; rr(x, 16, 190, w - 90, 330, 18); x.fill();
  x.save(); rr(x, 26, 200, w - 110, 250, 12); x.clip(); x.fillStyle = vgrad(x, 200, 450, [[0, '#ffb36b'], [1, '#e0567a']]); x.fillRect(26, 200, w - 110, 250);
  [[90, '#7ad48a'], [160, '#4f8cff'], [230, '#ff7aa8'], [300, '#a98bff']].forEach(([px, col], i) => { const G = require('./guy'); G.guy(x, px, 470, .2, { mood: 'laugh', shirt: col, hair: i === 2 ? 'pony' : null, look: 0, lh: [-180, -650], rh: [180, -650], bendB: -1, bendF: -1 }); });
  x.restore();
  text(x, 'Squad', 40, 478, { size: 19, weight: 800, color: '#fff', align: 'left' }); fire(x, 110, 476, 9);
  text(x, '4:58 PM', w - 92, 500, { size: 12, weight: 600, color: 'rgba(255,255,255,.5)', align: 'right' });
  x.restore();
  if (o.notif) notifCard(x, w, 560, 'Squad', 'Riya', 'best day ever!!', o.notif, { icon: '#ff7a3d' });
}
function fire(x, cx, cy, s) { x.fillStyle = '#ff7a1a'; x.beginPath(); x.moveTo(cx, cy - s * 1.4); x.quadraticCurveTo(cx + s, cy - s * .3, cx + s * .7, cy + s * .6); x.quadraticCurveTo(cx, cy + s * 1.2, cx - s * .7, cy + s * .6); x.quadraticCurveTo(cx - s, cy - s * .2, cx, cy - s * 1.4); x.fill(); x.fillStyle = '#ffd34a'; circle(x, cx, cy + s * .35, s * .38); x.fill(); }
// dying phone
function dying(x, w, h, t, k) {
  x.fillStyle = '#000'; x.fillRect(0, 0, w, h);
  x.save(); x.globalAlpha = 1 - clamp(k);
  x.strokeStyle = '#ff453a'; x.lineWidth = 5; rr(x, w / 2 - 70, h / 2 - 36, 130, 72, 12); x.stroke(); x.fillStyle = '#ff453a'; x.fillRect(w / 2 + 64, h / 2 - 14, 10, 28); x.fillRect(w / 2 - 60, h / 2 - 26, 10, 52);
  text(x, '1%', w / 2, h / 2 + 90, { size: 30, weight: 700, color: '#ff453a' }); text(x, 'Shutting down...', w / 2, h / 2 + 130, { size: 18, weight: 500, color: 'rgba(255,255,255,.6)' });
  x.restore();
}

function msg(x, w, y, s, mine, a, when, read) {
  x.save(); x.globalAlpha *= clamp(a); x.font = L.font(18, 500);
  const words = s.split(' '); const lines = []; let cur = ''; for (const wd of words) { const tt = cur ? cur + ' ' + wd : wd; if (x.measureText(tt).width > w * .62 && cur) { lines.push(cur); cur = wd; } else cur = tt; } lines.push(cur);
  const bw = Math.max(...lines.map(l => x.measureText(l).width)) + 36, bh = lines.length * 26 + 40; const bx = mine ? w - 16 - bw : 16;
  const k = E.back(clamp(a)); x.translate(bx + (mine ? bw : 0), y); x.scale(k, k); x.translate(-(bx + (mine ? bw : 0)), -y);
  x.fillStyle = mine ? '#0a84ff' : '#262a35'; rr(x, bx, y, bw, bh, 20); x.fill();
  lines.forEach((l, i) => text(x, l, bx + 18, y + 24 + i * 26, { size: 18, weight: 500, color: '#fff', align: 'left' }));
  text(x, when + (mine ? (read ? '  ✓✓' : '  ✓') : ''), bx + bw - 14, y + bh - 12, { size: 12, weight: 600, color: mine && read ? '#bfe0ff' : 'rgba(255,255,255,.55)', align: 'right' });
  x.restore(); return y + bh + 14;
}

module.exports = { status, wallpaper, notifCard, lock, music, home, feed, lowBattery, chat, callScreen, groupChat, dying, fire };
