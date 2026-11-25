// POV cardio warm-up run: deterministic frame renderer (3D world + text-free pictogram overlay).
import * as THREE from 'three';
import { buildWorld, rng, spriteTex } from './world.js';
import * as F from './figure.js';

const TL = await (await fetch('timeline.json')).json();
const W = 1920, H = 1080;
const BEAT = TL.beat, BAR = TL.bar, FPS = TL.fps;
const SEC = Object.fromEntries(TL.sections.map((s) => [s.name, s]));
const LV_COL = ['#2bd67b', '#2ad1ff', '#ffcf2e', '#b06bff', '#ff3b5c'];
const MOVE_COL = { jump: '#ff3b5c', jump2: '#ff7a1f', duck: '#2bd67b', left: '#ffcf2e', right: '#ffcf2e', sprint: '#ff5a1f', run: '#2ad1ff', turnL: '#c58bff', turnR: '#c58bff' };

const glCanvas = document.getElementById('gl');
const Q = new URLSearchParams(location.search);
const renderer = new THREE.WebGLRenderer({ canvas: glCanvas, antialias: Q.get('aa') !== '0', preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace;
const ctx = document.getElementById('ui').getContext('2d');
const camera = new THREE.PerspectiveCamera(72, W / H, 0.1, 700);

const worlds = [null, null, null, null, null];
const world = (i) => (worlds[i] ||= setupDynamic(buildWorld(i, TL.levels[i], TL)));

// ------------------------------------------------------------------ math helpers
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const ss = (u) => { u = clamp(u); return u * u * (3 - 2 * u); };
const easeOutBack = (u) => { u = clamp(u); const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2; };
const easeOutCubic = (u) => 1 - (1 - clamp(u)) ** 3;
const easeInCubic = (u) => clamp(u) ** 3;
const lerp = (a, b, u) => a + (b - a) * u;
const beatPulse = (t, k = 9) => Math.exp(-((((t % BEAT) + BEAT) % BEAT)) * k);
const COIN_LEAD = 0.24; // coins are grabbed a few metres ahead and fly to the meter
const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

function sectionAt(t) {
  for (const s of TL.sections) if (t >= s.t0 && t < s.t1) return s;
  return TL.sections[TL.sections.length - 1];
}

// ------------------------------------------------------------------ camera track
function track(L, tau) {
  const tr = L.track, n = tr.s.length;
  let i = (tau - tr.t0) / tr.dt;
  i = clamp(i, 0, n - 1.0001);
  const i0 = Math.floor(i), f = i - i0;
  const g = (a) => a[i0] * (1 - f) + a[i0 + 1] * f;
  // yaw may jump by 2*pi only in theory; it is continuous in the generator
  return { s: g(tr.s), x: g(tr.px), y: g(tr.py), z: g(tr.pz), yaw: g(tr.yaw), roll: g(tr.roll), sprint: g(tr.sprint) };
}

function camState(li, t) {
  const L = TL.levels[li];
  const tau = t - L.t0;
  const k = track(L, tau);
  const ka = track(L, tau - 0.05), kb = track(L, tau + 0.05);
  const v = (kb.s - ka.s) / 0.1;
  const vf = clamp(v / L.speed, 0, 1.4);
  // lateral velocity relative to the heading (lane changes) -> look into the move
  const rx = Math.cos(k.yaw), rz = -Math.sin(k.yaw);
  const lat = ((kb.x - ka.x) * rx + (kb.z - ka.z) * rz) / 0.1;
  const ph = Math.PI * t / BEAT;
  const base = L.kind === 'skyrail' ? 3.69 : 0;
  const yrel = k.y - (L.kind === 'skyrail' ? roofBase(L, tau) : 0);
  const air = clamp(Math.abs(yrel) / 0.2);
  const sp = k.sprint;
  let bob = (Math.abs(Math.sin(ph)) - 0.64) * 0.075 * (1 - sp) + (Math.abs(Math.sin(2 * ph)) - 0.64) * 0.1 * sp;
  bob *= (1 - air) * clamp(vf);
  const sway = Math.sin(ph) * 0.03 * (1 - air) * clamp(vf);
  let pitch = -0.06 - Math.max(0, yrel) * 0.035 + Math.max(0, -yrel) * 0.07;
  if (L.kind === 'skyrail') pitch -= 0.03;
  let fov = 72 + 11 * sp;
  if (li === 4) {
    const up = ss((t - (TL.finish_cross + 2.2)) / 2.4);
    pitch += up * 0.34;
    fov += up * 4;
  }
  void base;
  return {
    pos: new THREE.Vector3(k.x + sway * rx, 1.62 + k.y + bob, k.z + sway * rz),
    yaw: k.yaw - lat * 0.02, pitch, roll: k.roll + Math.sin(ph) * 0.007 * (1 - air) * clamp(vf), fov, s: k.s, tau, sprint: sp, vf,
  };
}

// skyrail: roof height under the runner (for bob / pitch bookkeeping)
function roofBase(L, tau) {
  let h = 3.69;
  for (const e of L.events) {
    if (e.move !== 'jump' || e.h_to == null) continue;
    if (tau >= e.t) h = e.h_from + (e.h_to - e.h_from) * ss((tau - e.t) / 0.75);
  }
  return h;
}

function applyCam(cs, aspect = W / H) {
  camera.position.copy(cs.pos);
  camera.rotation.set(0, 0, 0, 'YXZ');
  camera.rotation.y = cs.yaw;
  camera.rotation.x = cs.pitch;
  camera.rotation.z = cs.roll;
  camera.fov = cs.fov;
  camera.aspect = aspect;
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);
}

// ------------------------------------------------------------------ dynamic world parts
const SPRITE = spriteTex();
function setupDynamic(w) {
  const sc = w.scene;
  if (w.index === 4) {
    // embers
    const n = 420;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    const cols = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { const c = new THREE.Color(hash(i) < 0.5 ? '#ffb02e' : '#ff5a1f'); cols.set([c.r, c.g, c.b], i * 3); }
    g.setAttribute('color', new THREE.BufferAttribute(cols, 3));
    const m = new THREE.PointsMaterial({ size: 0.28, map: SPRITE, vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
    w.embers = new THREE.Points(g, m);
    w.embers.frustumCulled = false;
    sc.add(w.embers);
    // fireworks
    const per = 120, nb = TL.fireworks.length;
    const fg = new THREE.BufferGeometry();
    fg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(per * nb * 3), 3));
    fg.setAttribute('color', new THREE.BufferAttribute(new Float32Array(per * nb * 3), 3));
    const fm = new THREE.PointsMaterial({ size: 1.5, map: SPRITE, vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false, fog: false });
    w.fireworks = new THREE.Points(fg, fm);
    w.fireworks.frustumCulled = false;
    w.fwPer = per;
    sc.add(w.fireworks);
    if (w.finish) w.finish.position.z = -track(TL.levels[4], TL.finish_cross - TL.levels[4].t0).s;
  }
  return w;
}

const tmpM = new THREE.Matrix4(), tmpQ = new THREE.Quaternion(), tmpE = new THREE.Euler(), tmpV = new THREE.Vector3(), tmpS = new THREE.Vector3();
function updateWorld(li, t, cs) {
  const w = world(li);
  const L = TL.levels[li];
  const tau = t - L.t0;
  w.sky.position.copy(cs.pos);
  w.sky.material.uniforms.time.value = t;
  // moving trains
  for (const g of w.trains) {
    const o = g.userData;
    if (o.speed > 0) g.position.z = -(o.s - o.speed * (tau - o.t_meet));
  }
  // coins
  const cm = w.coinMesh;
  L.coins.forEach((c, i) => {
    const vis = t < c.t - COIN_LEAD && c.t - t < 22;
    tmpE.set(0, t * 3.2 + i * 0.5, 0);
    tmpQ.setFromEuler(tmpE);
    const bob = Math.sin(t * 4 + i) * 0.05;
    tmpM.compose(tmpV.set(c.x, c.y + bob, c.z), tmpQ, tmpS.setScalar(vis ? 1 : 0));
    cm.setMatrixAt(i, tmpM);
  });
  cm.instanceMatrix.needsUpdate = true;
  for (const a of w.anims) {
    const o = a.obj, k = a.kind;
    if (k === 'blink') o.visible = Math.floor(t * 3 + a.seed * 0.7) % 2 === 0;
    else if (k === 'saw' || k === 'sawx') o.rotation.z = -t * 13 - a.seed;
    else if (k === 'elec') { o.visible = hash(Math.floor(t * 24) + a.seed) > 0.18; o.scale.y = 0.6 + 1.6 * hash(Math.floor(t * 30) * 1.3 + a.seed); }
    else if (k === 'elecglow') { const f = 0.6 + 0.6 * hash(Math.floor(t * 20) + a.seed); o.scale.set(f, f, 1); }
    else if (k === 'fire') { const f = 0.8 + 0.35 * Math.sin(t * 17 + a.seed * 3) + 0.15 * Math.sin(t * 31 + a.seed); o.scale.set(1.0 * (0.9 + 0.1 * f), 1.8 * f, 1); }
    else if (k === 'torch') { const f = 0.85 + 0.2 * Math.sin(t * 19 + a.seed) + 0.1 * Math.sin(t * 37 + a.seed); o.scale.set(0.7 * f, 1.2 * f, 1); }
    else if (k === 'chev') o.visible = (Math.floor(t / BEAT * 2) % 3) !== ((a.seed + 3) % 3);
  }
  if (w.scene.userData.mist) w.scene.userData.mist.offset.set(t * 0.004, t * 0.002);
  if (w.scene.userData.lava) {
    const [a, b] = w.scene.userData.lava;
    a.offset.set(Math.sin(t * 0.2) * 0.05, t * 0.012);
    b.offset.set(t * 0.01, -t * 0.02);
  }
  if (w.embers) {
    const p = w.embers.geometry.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const o = hash(i + 1) * 160;
      const sRel = ((o - cs.s) % 160 + 160) % 160;
      const s = cs.s + sRel - 6;
      const x = (hash(i + 7) - 0.5) * 34;
      const y = ((hash(i + 3) * 9 + t * (0.6 + hash(i + 5) * 1.2)) % 9) - 0.4;
      p.setXYZ(i, x + Math.sin(t * 1.3 + i) * 0.4, y, -s);
    }
    p.needsUpdate = true;
  }
  if (w.fireworks) {
    const per = w.fwPer;
    const pos = w.fireworks.geometry.attributes.position, colA = w.fireworks.geometry.attributes.color;
    const endS = track(L, 999).s;
    const pal = ['#ff3d7f', '#ffcf2e', '#2ad1ff', '#7b5cff', '#2bd67b', '#ffffff', '#ff8a1f'];
    TL.fireworks.forEach((ft, b) => {
      const c = new THREE.Color(pal[b % pal.length]);
      const cx = (hash(b * 3 + 1) - 0.5) * 60, cy = 30 + hash(b * 3 + 2) * 22, cz = -(endS + 70 + hash(b * 3 + 3) * 50);
      const u = t - ft;
      for (let k = 0; k < per; k++) {
        const i = b * per + k;
        if (u < -0.55 || u > 2.6) { pos.setXYZ(i, 0, -999, 0); colA.setXYZ(i, 0, 0, 0); continue; }
        if (u < 0) { // rocket
          const a = (u + 0.55) / 0.55;
          if (k < 6) { pos.setXYZ(i, cx, lerp(0, cy, easeOutCubic(a)) - k * 0.8, cz); const f = 1 - k / 6; colA.setXYZ(i, 1 * f, 0.85 * f, 0.6 * f); }
          else { pos.setXYZ(i, 0, -999, 0); colA.setXYZ(i, 0, 0, 0); }
          continue;
        }
        const th = hash(i * 1.7) * Math.PI * 2, ph = Math.acos(2 * hash(i * 2.3) - 1);
        const sp = 13 + hash(i * 3.1) * 4;
        const r = sp * (1 - Math.exp(-2.6 * u)) / 2.6;
        pos.setXYZ(i, cx + r * Math.sin(ph) * Math.cos(th), cy + r * Math.cos(ph) - 2.2 * u * u, cz + r * Math.sin(ph) * Math.sin(th));
        const fade = (1 - u / 2.6) ** 1.6 * (0.75 + 0.25 * Math.sin(u * 30 + i));
        const wh = Math.exp(-u * 5);
        colA.setXYZ(i, (c.r + wh) * fade, (c.g + wh) * fade, (c.b + wh) * fade);
      }
    });
    pos.needsUpdate = true; colA.needsUpdate = true;
  }
  return w;
}

function renderLevel(li, t, vp = null) {
  const cs = camState(li, t);
  const w = updateWorld(li, t, cs);
  if (vp) {
    renderer.setScissorTest(true);
    renderer.setViewport(vp.x, H - vp.y - vp.h, vp.w, vp.h);
    renderer.setScissor(vp.x, H - vp.y - vp.h, vp.w, vp.h);
    applyCam(cs, vp.w / vp.h);
  } else {
    renderer.setScissorTest(false);
    renderer.setViewport(0, 0, W, H);
    applyCam(cs);
  }
  renderer.render(w.scene, camera);
  renderer.setScissorTest(false);
  return cs;
}

function projectAt(li, t, p) {
  const cs = camState(li, t);
  applyCam(cs);
  const v = p.clone().project(camera);
  return [(v.x * 0.5 + 0.5) * W, (-v.y * 0.5 + 0.5) * H, v.z];
}

// ------------------------------------------------------------------ 2D drawing kit
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }

function burstBG(t, alpha = 1, cx = W / 2, cy = H / 2, color = '#000') {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color; ctx.fillRect(0, 0, W, H);
  const fr = Math.floor(t * 12);
  ctx.fillStyle = 'rgba(255,255,255,0.9)';
  for (let i = 0; i < 96; i++) {
    const a = (i / 96) * Math.PI * 2 + (hash(i + fr * 0.37) - 0.5) * 0.05;
    const inner = 470 + hash(i * 7 + fr) * 330 - beatPulse(t, 6) * 40;
    const outer = 1500;
    const wd = (0.004 + hash(i * 3 + fr) * 0.01);
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(a) * inner, cy + Math.sin(a) * inner);
    ctx.lineTo(cx + Math.cos(a - wd) * outer, cy + Math.sin(a - wd) * outer);
    ctx.lineTo(cx + Math.cos(a + wd) * outer, cy + Math.sin(a + wd) * outer);
    ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}

function star(x, y, r, fill, stroke, rot = 0) {
  ctx.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = -Math.PI / 2 + rot + i * Math.PI / 5, q = i % 2 ? r * 0.45 : r;
    ctx.lineTo(x + Math.cos(a) * q, y + Math.sin(a) * q);
  }
  ctx.closePath();
  ctx.fillStyle = fill; ctx.fill();
  if (stroke) { ctx.lineWidth = r * 0.12; ctx.strokeStyle = stroke; ctx.lineJoin = 'round'; ctx.stroke(); }
}

function coinIcon(x, y, r, a = 1) {
  ctx.save(); ctx.globalAlpha = a;
  const g = ctx.createRadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r);
  g.addColorStop(0, '#fff6b0'); g.addColorStop(0.5, '#ffc928'); g.addColorStop(1, '#d68a00');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
  ctx.lineWidth = r * 0.14; ctx.strokeStyle = '#b86e00'; ctx.beginPath(); ctx.arc(x, y, r * 0.8, 0, 7); ctx.stroke();
  star(x, y + r * 0.04, r * 0.5, '#ffe76a', '#c07400');
  ctx.restore();
}

function chevron(x, y, s, dir, color, lw) {
  // dir: 'left' | 'right' | 'up' | 'down'
  const rot = { right: 0, down: Math.PI / 2, left: Math.PI, up: -Math.PI / 2 }[dir];
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(-s * 0.4, -s * 0.6); ctx.lineTo(s * 0.35, 0); ctx.lineTo(-s * 0.4, s * 0.6); ctx.stroke();
  ctx.restore();
}

function flame(x, y, s, t, a = 1) {
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y);
  const layers = [['#ff3d00', 1], ['#ff9a1f', 0.72], ['#ffe76a', 0.42]];
  for (const [c, k] of layers) {
    const fl = 1 + 0.08 * Math.sin(t * 22 + k * 5);
    ctx.fillStyle = c;
    ctx.beginPath();
    ctx.moveTo(0, -s * k * 1.25 * fl);
    ctx.bezierCurveTo(s * k * 0.55, -s * k * 0.55, s * k * 0.75, s * k * 0.15, 0, s * k * 0.6);
    ctx.bezierCurveTo(-s * k * 0.75, s * k * 0.15, -s * k * 0.55, -s * k * 0.55, 0, -s * k * 1.25 * fl);
    ctx.fill();
  }
  ctx.restore();
}

function swapIcon(x, y, r, t, color) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(t * 2);
  ctx.strokeStyle = color; ctx.lineWidth = r * 0.18; ctx.lineCap = 'round';
  for (const k of [0, Math.PI]) {
    ctx.beginPath(); ctx.arc(0, 0, r, k + 0.35, k + Math.PI - 0.35); ctx.stroke();
    const a = k + Math.PI - 0.35;
    const px = Math.cos(a) * r, py = Math.sin(a) * r;
    ctx.save(); ctx.translate(px, py); ctx.rotate(a + Math.PI / 2);
    ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(r * 0.32, 0); ctx.lineTo(-r * 0.2, -r * 0.3); ctx.lineTo(-r * 0.2, r * 0.3); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
  ctx.restore();
}

function trophy(x, y, s, t) {
  ctx.save(); ctx.translate(x, y);
  const g = ctx.createLinearGradient(-s, -s, s, s);
  g.addColorStop(0, '#fff3a0'); g.addColorStop(0.45, '#ffc928'); g.addColorStop(1, '#c97a00');
  ctx.fillStyle = g; ctx.strokeStyle = '#7a4500'; ctx.lineWidth = s * 0.06; ctx.lineJoin = 'round';
  // handles
  ctx.lineWidth = s * 0.12; ctx.strokeStyle = '#e2a000';
  for (const sd of [-1, 1]) { ctx.beginPath(); ctx.arc(sd * s * 0.62, -s * 0.55, s * 0.28, sd > 0 ? -Math.PI / 2 : Math.PI / 2, sd > 0 ? Math.PI / 2 : Math.PI * 1.5, sd < 0); ctx.stroke(); }
  ctx.lineWidth = s * 0.06; ctx.strokeStyle = '#7a4500';
  // cup
  ctx.beginPath();
  ctx.moveTo(-s * 0.7, -s * 0.95); ctx.lineTo(s * 0.7, -s * 0.95);
  ctx.bezierCurveTo(s * 0.7, -s * 0.1, s * 0.35, s * 0.15, s * 0.12, s * 0.2);
  ctx.lineTo(s * 0.12, s * 0.5); ctx.lineTo(s * 0.45, s * 0.62); ctx.lineTo(s * 0.45, s * 0.8); ctx.lineTo(-s * 0.45, s * 0.8); ctx.lineTo(-s * 0.45, s * 0.62); ctx.lineTo(-s * 0.12, s * 0.5);
  ctx.lineTo(-s * 0.12, s * 0.2);
  ctx.bezierCurveTo(-s * 0.35, s * 0.15, -s * 0.7, -s * 0.1, -s * 0.7, -s * 0.95);
  ctx.closePath(); ctx.fill(); ctx.stroke();
  star(0, -s * 0.45, s * 0.26, '#fff6c0', '#c07400');
  // shine sweep
  ctx.save(); ctx.clip();
  const sx = ((t * 0.8) % 1.6 - 0.3) * s * 2.4 - s;
  ctx.fillStyle = 'rgba(255,255,255,0.45)';
  ctx.beginPath(); ctx.moveTo(sx, -s); ctx.lineTo(sx + s * 0.25, -s); ctx.lineTo(sx - s * 0.35, s); ctx.lineTo(sx - s * 0.6, s); ctx.fill();
  ctx.restore();
  ctx.restore();
}

function confetti(t0, t, n = 170, alpha = 1) {
  const u = t - t0;
  if (u < 0 || u > 6) return;
  const pal = ['#ff3d7f', '#ffcf2e', '#2ad1ff', '#7b5cff', '#2bd67b', '#ffffff', '#ff8a1f'];
  ctx.save(); ctx.globalAlpha = alpha * clamp((6 - u) / 1.2);
  for (let i = 0; i < n; i++) {
    const side = i % 2 ? 1 : -1;
    // two cannons from the bottom corners
    const vx = -side * (420 + hash(i) * 680), vy = -(1100 + hash(i + 9) * 900);
    const drag = 1.6;
    const e = (1 - Math.exp(-drag * u)) / drag;
    const x = (side > 0 ? W + 20 : -20) + vx * e + Math.sin(u * 3 + i) * 30 * u;
    const y = H + 20 + vy * e + 260 * u * u * 0.5 + 90 * u;
    if (y > H + 40) continue;
    const rot = u * (4 + hash(i + 3) * 8) + i;
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
    ctx.fillStyle = pal[i % pal.length];
    const fw = 16 * Math.abs(Math.cos(u * 7 + i));
    ctx.fillRect(-fw / 2, -6, fw + 2, 12);
    ctx.restore();
  }
  ctx.restore();
}

// ---------------- move badge (circle with an animated pictogram)
function moveFigure(move, t, x, y, sc, color, gap) {
  const ph = t / BEAT;
  if (move === 'run') F.drawFigure(ctx, F.runPose(Math.PI * ph), x, y, sc, color, { shadow: false, gap, farColor: color });
  else if (move === 'sprint') F.drawFigure(ctx, F.runPose(Math.PI * 2 * ph, 1), x, y, sc, color, { shadow: false, gap, farColor: color });
  else if (move === 'jump' || move === 'jump2') F.drawFigure(ctx, F.jumpPose(((ph / 2) % 1 + 1) % 1), x, y, sc, color, { shadow: false, gap, farColor: color });
  else if (move === 'duck') F.drawFigure(ctx, F.duckPose(((ph / 2) % 1 + 1) % 1), x, y, sc, color, { shadow: false, gap, farColor: color });
  else if (move === 'left' || move === 'right' || move === 'turnL' || move === 'turnR') F.drawFigure(ctx, F.sideStepPose(((ph / 2) % 1 + 1) % 1, (move === 'left' || move === 'turnL') ? -1 : 1), x, y, sc, color, { shadow: false, gap, farColor: color });
}

function curvedArrow(x, y, s, d, color, lw, t = 0) {
  // a quarter-turn arrow: up then bending to the side d (-1 left, +1 right)
  ctx.save(); ctx.translate(x, y); ctx.scale(d, 1);
  ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(-s * 0.55, s * 0.55); ctx.lineTo(-s * 0.55, 0); ctx.quadraticCurveTo(-s * 0.55, -s * 0.45, 0, -s * 0.45); ctx.lineTo(s * 0.35, -s * 0.45); ctx.stroke();
  ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(s * 0.7, -s * 0.45); ctx.lineTo(s * 0.3, -s * 0.78); ctx.lineTo(s * 0.3, -s * 0.12); ctx.closePath(); ctx.fill();
  ctx.restore();
}

function badge(move, x, y, r, t, opt = {}) {
  const c = MOVE_COL[move] || '#fff';
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(opt.scale ?? 1, opt.scale ?? 1);
  ctx.globalAlpha = opt.alpha ?? 1;
  // glow
  const g = ctx.createRadialGradient(0, 0, r * 0.6, 0, 0, r * 1.6);
  g.addColorStop(0, c + '88'); g.addColorStop(1, c + '00');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r * 1.6, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(14,16,24,0.88)'; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill();
  ctx.lineWidth = r * 0.13; ctx.strokeStyle = c; ctx.beginPath(); ctx.arc(0, 0, r - r * 0.065, 0, 7); ctx.stroke();
  if (opt.progress != null) {
    ctx.lineWidth = r * 0.13; ctx.strokeStyle = '#ffffff'; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.arc(0, 0, r + r * 0.2, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * opt.progress); ctx.stroke();
  }
  ctx.save(); ctx.beginPath(); ctx.arc(0, 0, r * 0.92, 0, 7); ctx.clip();
  if (move === 'sprint') flame(0, r * 0.15, r * 0.62, t, 0.9);
  const figY = move === 'jump' || move === 'jump2' ? r * 0.62 : r * 0.6;
  moveFigure(move, t, (move === 'left' ? r * 0.08 : move === 'right' ? -r * 0.08 : 0), figY, r * 0.29, '#ffffff', 'rgba(14,16,24,1)');
  if (move === 'left' || move === 'right') {
    const d = move === 'left' ? -1 : 1;
    const k = ((t / BEAT) % 1);
    for (let i = 0; i < 2; i++) chevron(d * (r * 0.5 + i * r * 0.17 + k * r * 0.06), -r * 0.05, r * 0.22, move, c, r * 0.07);
  }
  if (move === 'jump2') {
    for (let i = 0; i < 2; i++) chevron(r * 0.58, -r * 0.05 - i * r * 0.2, r * 0.2, 'up', c, r * 0.07);
  }
  if (move === 'turnL' || move === 'turnR') curvedArrow(0, -r * 0.42, r * 0.5, move === 'turnL' ? -1 : 1, c, r * 0.09, t);
  ctx.restore();
  ctx.restore();
}

// ---------------- HUD during levels
function hud(li, t, cs, alpha = 1) {
  const L = TL.levels[li];
  const lv = SEC['lvl' + (li + 1)];
  const end = li === 4 ? TL.finish_cross : lv.t1;
  const prog = clamp((t - lv.t0) / (end - lv.t0));
  const c = LV_COL[li];
  ctx.save(); ctx.globalAlpha = alpha;
  // vignette
  const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.42, W / 2, H / 2, H * 1.0);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.38)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  // top shade
  const tg = ctx.createLinearGradient(0, 0, 0, 130);
  tg.addColorStop(0, 'rgba(0,0,0,0.35)'); tg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 130);
  // progress bar
  const x0 = 560, x1 = 1360, y = 46;
  rr(x0 - 6, y - 13, x1 - x0 + 12, 26, 13); ctx.fillStyle = 'rgba(10,12,20,0.6)'; ctx.fill();
  rr(x0, y - 7, x1 - x0, 14, 7); ctx.fillStyle = 'rgba(255,255,255,0.22)'; ctx.fill();
  const px = lerp(x0, x1, prog);
  const pg = ctx.createLinearGradient(x0, 0, px, 0); pg.addColorStop(0, c + 'aa'); pg.addColorStop(1, c);
  rr(x0, y - 7, Math.max(14, px - x0), 14, 7); ctx.fillStyle = pg; ctx.fill();
  // finish flag at the end
  ctx.save(); ctx.translate(x1 + 34, y);
  ctx.fillStyle = '#ddd'; ctx.fillRect(-2, -20, 4, 36);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 3; j++) { ctx.fillStyle = (i + j) % 2 ? '#111' : '#fff'; ctx.fillRect(2 + i * 6, -20 + j * 6, 6, 6); }
  ctx.restore();
  // runner head
  ctx.fillStyle = 'rgba(14,16,24,0.92)'; ctx.beginPath(); ctx.arc(px, y, 24, 0, 7); ctx.fill();
  ctx.lineWidth = 4; ctx.strokeStyle = c; ctx.stroke();
  moveFigure(cs.sprint > 0.5 ? 'sprint' : 'run', t, px - 1, y + 15, 8, '#fff', 'rgba(14,16,24,1)');
  // level pips
  for (let i = 0; i < 5; i++) {
    const cx = 60 + i * 38;
    ctx.beginPath(); ctx.arc(cx, y, 13, 0, 7);
    ctx.fillStyle = i <= li ? LV_COL[i] : 'rgba(255,255,255,0.15)'; ctx.fill();
    ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(255,255,255,0.9)'; ctx.stroke();
  }
  // coin meter
  const got = L.coins.filter((cc) => cc.t <= t).length;
  const frac = got / Math.max(1, L.coins.length);
  const lastHit = L.coins.reduce((m, cc) => (cc.t + 0.42 <= t ? Math.max(m, cc.t + 0.42) : m), -9);
  const pop = Math.exp(-(t - lastHit) * 9);
  const cx = 1840, cy = y;
  ctx.fillStyle = 'rgba(14,16,24,0.6)'; ctx.beginPath(); ctx.arc(cx, cy, 34, 0, 7); ctx.fill();
  ctx.lineWidth = 6; ctx.strokeStyle = 'rgba(255,255,255,0.18)'; ctx.beginPath(); ctx.arc(cx, cy, 30, 0, 7); ctx.stroke();
  ctx.strokeStyle = '#ffd21f'; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(cx, cy, 30, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * frac); ctx.stroke();
  coinIcon(cx, cy, 21 * (1 + pop * 0.3));
  if (pop > 0.02) { ctx.globalAlpha = alpha * pop; star(cx + 30, cy - 26, 12, '#fff7c2', null, t * 4); ctx.globalAlpha = alpha; }
  ctx.restore();
}

// ---------------- coin fly-to-meter sparkles
function coinFX(li, t) {
  const L = TL.levels[li];
  for (const c of L.coins) {
    const u = t - (c.t - COIN_LEAD);
    if (u < 0 || u > 0.42) continue;
    const p = projectAt(li, c.t - COIN_LEAD, new THREE.Vector3(c.x, c.y, c.z));
    const sx = clamp(p[0], 100, W - 100), sy = clamp(p[1], 120, H - 60);
    const k = easeInCubic(u / 0.42);
    const x = lerp(sx, 1840, k) + Math.sin(k * Math.PI) * -120, y = lerp(sy, 46, k) - Math.sin(k * Math.PI) * 80;
    coinIcon(x, y, lerp(34, 16, k), 1);
    if (u < 0.2) {
      ctx.save(); ctx.globalAlpha = 1 - u / 0.2;
      for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2 + c.t; star(sx + Math.cos(a) * u * 500, sy + Math.sin(a) * u * 500, 12, '#fff7c2', null, a); }
      ctx.restore();
    }
  }
}

// ---------------- move cues
function cues(li, t) {
  const L = TL.levels[li];
  const lead = li === 4 ? 3 : 4;
  for (const e of L.events) {
    const te = e.t_abs;
    const ta = te - lead * BEAT;
    const tEnd = e.move === 'sprint' ? e.t_end_abs : te + 0.55;
    if (t < ta || t > tEnd + 0.3) continue;
    const a = t - ta;
    const c = MOVE_COL[e.move];
    let scale = easeOutBack(a / 0.28);
    let alpha = 1;
    if (t > tEnd) { alpha = 1 - (t - tEnd) / 0.3; scale *= 1 + (t - tEnd) * 0.6; }
    const go = t >= te;
    if (go) scale *= 1 + 0.28 * Math.exp(-(t - te) * 7);
    else scale *= 1 + 0.06 * beatPulse(t);
    const prog = go ? null : 1 - clamp((t - ta) / (te - ta));
    const bx = W / 2, by = 162, r = 76;
    badge(e.move, bx, by, r, t, { scale, alpha, progress: prog });
    // countdown pips on the beats
    if (!go) {
      const nP = lead - 1;
      for (let k = 0; k < nP; k++) {
        const tk = te - (nP - k) * BEAT;
        const on = t >= tk;
        const pk = on ? Math.exp(-(t - tk) * 8) : 0;
        const px = bx + (k - (nP - 1) / 2) * 34, py = by + r + 40;
        ctx.save(); ctx.globalAlpha = alpha;
        ctx.beginPath(); ctx.arc(px, py, 10 + pk * 6, 0, 7);
        ctx.fillStyle = on ? c : 'rgba(255,255,255,0.25)'; ctx.fill();
        ctx.lineWidth = 3; ctx.strokeStyle = '#fff'; ctx.stroke();
        ctx.restore();
      }
    }
    // GO burst + big direction chevrons
    const hits = e.move === 'jump2' ? [te, te + 2 * BEAT] : e.move === 'sprint' ? [te] : [te];
    for (const th of hits) {
      const u = t - th;
      if (u < 0 || u > 0.6) continue;
      ctx.save();
      ctx.globalAlpha = (1 - u / 0.6);
      ctx.lineWidth = 10 * (1 - u / 0.6) + 2; ctx.strokeStyle = c;
      ctx.beginPath(); ctx.arc(bx, by, r + 20 + u * 260, 0, 7); ctx.stroke();
      // screen-edge colour flash
      const eg = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95);
      eg.addColorStop(0, c + '00'); eg.addColorStop(1, c + '99');
      ctx.globalAlpha = 0.9 * Math.exp(-u * 5);
      ctx.fillStyle = eg; ctx.fillRect(0, 0, W, H);
      ctx.globalAlpha = 0.85 * (1 - u / 0.6);
      const dir = (e.move === 'left' || e.move === 'turnL') ? 'left' : (e.move === 'right' || e.move === 'turnR') ? 'right' : e.move === 'duck' ? 'down' : 'up';
      if (e.move !== 'sprint') {
        for (let i = 0; i < 3; i++) {
          const k = easeOutCubic(u / 0.6) * 220 + i * 70;
          const [ox, oy] = { left: [-k, 0], right: [k, 0], up: [0, -k * 0.6], down: [0, k * 0.6] }[dir];
          chevron(W / 2 + ox, H * 0.56 + oy, 90, dir, '#ffffff', 22);
        }
      }
      ctx.restore();
    }
  }
}

function sprintFX(t, k) {
  if (k <= 0.01) return;
  ctx.save();
  for (let i = 0; i < 70; i++) {
    const a = hash(i) * Math.PI * 2;
    const ph = ((t * (1.6 + hash(i + 1)) + hash(i + 2)) % 1);
    const r0 = 380 + ph * 900, len = 140 + hash(i + 4) * 200;
    ctx.globalAlpha = k * 0.55 * Math.sin(ph * Math.PI);
    ctx.strokeStyle = i % 3 ? '#ffffff' : '#ffb02e';
    ctx.lineWidth = 3 + hash(i + 6) * 4;
    ctx.beginPath();
    ctx.moveTo(W / 2 + Math.cos(a) * r0, H / 2 + Math.sin(a) * r0 * 0.6);
    ctx.lineTo(W / 2 + Math.cos(a) * (r0 + len), H / 2 + Math.sin(a) * (r0 + len) * 0.6);
    ctx.stroke();
  }
  const eg = ctx.createRadialGradient(W / 2, H / 2, H * 0.4, W / 2, H / 2, H);
  eg.addColorStop(0, 'rgba(255,90,31,0)'); eg.addColorStop(1, 'rgba(255,90,31,0.45)');
  ctx.globalAlpha = k * (0.7 + 0.3 * beatPulse(t));
  ctx.fillStyle = eg; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// ---------------- rest card: recover (breathe + water) then guided stretches
function heartIcon(x, y, r, color) {
  ctx.save(); ctx.translate(x, y); ctx.scale(r / 50, r / 50);
  ctx.fillStyle = color;
  ctx.beginPath(); ctx.moveTo(0, 38);
  ctx.bezierCurveTo(-60, -5, -38, -52, 0, -22);
  ctx.bezierCurveTo(38, -52, 60, -5, 0, 38);
  ctx.fill(); ctx.restore();
}

function bottleIcon(x, y, s, fill, t) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(Math.sin(t * 2) * 0.06);
  ctx.fillStyle = '#141414';
  rr(-s * 0.18, -s * 1.05, s * 0.36, s * 0.22, s * 0.05); ctx.fill();
  rr(-s * 0.42, -s * 0.85, s * 0.84, s * 1.75, s * 0.2); ctx.fill();
  ctx.save(); rr(-s * 0.34, -s * 0.77, s * 0.68, s * 1.59, s * 0.15); ctx.clip();
  ctx.fillStyle = '#7fd8ff'; ctx.fillRect(-s, -s * 0.77 + s * 1.59 * (1 - fill) + Math.sin(t * 3) * s * 0.03, s * 2, s * 2);
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.fillRect(-s * 0.26, -s * 0.7, s * 0.1, s * 1.4);
  ctx.restore();
  ctx.restore();
}

function restPhases(s) {
  const B = BAR;
  if (s.cooldown) return [
    { kind: 'stretch', name: s.stretches[0], t0: s.t0, t1: s.t0 + 8 * B },
    { kind: 'stretch', name: s.stretches[1], t0: s.t0 + 8 * B, t1: s.t1 },
  ];
  return [
    { kind: 'recover', name: 'recover', t0: s.t0, t1: s.t0 + 4 * B },
    { kind: 'stretch', name: s.stretches[0], t0: s.t0 + 4 * B, t1: s.t0 + 12 * B },
    { kind: 'stretch', name: s.stretches[1], t0: s.t0 + 12 * B, t1: s.t1 },
  ];
}

function restCard(s, t, rect) {
  const phases = restPhases(s);
  const ph = phases.find((p) => t >= p.t0 && t < p.t1) || phases[phases.length - 1];
  ctx.save();
  ctx.translate(rect.x, rect.y); ctx.scale(rect.w / W, rect.h / H);
  rr(0, 0, W, H, rect.r * W / rect.w); ctx.save(); ctx.clip();
  const recover = ph.kind === 'recover';
  const bg = ctx.createRadialGradient(W / 2, H * 0.55, 80, W / 2, H * 0.55, W * 0.7);
  if (recover) { bg.addColorStop(0, '#bff3ff'); bg.addColorStop(0.55, '#5fd0ff'); bg.addColorStop(1, '#2a9de0'); }
  else { bg.addColorStop(0, '#fff07a'); bg.addColorStop(0.55, '#ffd21f'); bg.addColorStop(1, '#ffb300'); }
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(W / 2, H * 0.55); ctx.rotate(t * 0.08);
  ctx.fillStyle = 'rgba(255,255,255,0.16)';
  for (let i = 0; i < 18; i++) { ctx.rotate(Math.PI * 2 / 18); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(1500, -110); ctx.lineTo(1500, 110); ctx.fill(); }
  ctx.restore();
  const accent = recover ? '#2a9de0' : '#ffd21f';
  // breathing guide: in for a bar, out for a bar
  const br = 0.5 - 0.5 * Math.cos((t - ph.t0) * Math.PI * 2 / (2 * BAR));
  ctx.lineWidth = 10; ctx.strokeStyle = 'rgba(255,255,255,0.7)';
  ctx.beginPath(); ctx.arc(W / 2, H * 0.54, 300 + br * 90, 0, 7); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.22)';
  ctx.beginPath(); ctx.arc(W / 2, H * 0.54, 280 + br * 90, 0, 7); ctx.fill();
  ctx.fillStyle = recover ? 'rgba(0,60,110,0.18)' : 'rgba(120,70,0,0.18)';
  ctx.beginPath(); ctx.ellipse(W / 2, H * 0.86, 420, 40, 0, 0, 7); ctx.fill();
  // figure (pops in at each phase start; mirrored halfway through a stretch)
  const flipAt = ph.kind === 'stretch' ? (ph.t0 + ph.t1) / 2 : 1e9;
  const fu = (t - flipAt) / 0.35;
  let sx = t < flipAt ? 1 : -1;
  if (fu > -1 && fu < 1) sx = Math.cos(clamp((fu + 1) / 2) * Math.PI);
  const pop = easeOutBack((t - ph.t0) / 0.45);
  ctx.save(); ctx.translate(W / 2, H * 0.86); ctx.scale((Math.abs(sx) < 0.02 ? 0.02 : sx) * pop, pop); ctx.translate(-W / 2, -H * 0.86);
  const pose = F.stretchPose(ph.name, t - ph.t0);
  const fsc = ph.name === 'lunge_twist' ? 170 : ph.name === 'hamstring' ? 165 : 150;
  F.drawFigure(ctx, pose, W / 2, H * 0.86, fsc, '#141414', { shadow: false, gap: recover ? '#5fd0ff' : '#ffd21f', farColor: '#2c2c2c' });
  ctx.restore();
  // swap-sides icon around the flip
  const sw = t - flipAt;
  if (sw > -BEAT * 2 && sw < BEAT * 3) {
    ctx.save(); ctx.globalAlpha = clamp(1 - Math.abs(sw) / (BEAT * 2.5));
    ctx.fillStyle = '#141414'; ctx.beginPath(); ctx.arc(W / 2, 140, 64, 0, 7); ctx.fill();
    swapIcon(W / 2, 140, 36, t, accent);
    ctx.restore();
  }
  // countdown ring (right) — one segment per beat of this phase
  const total = ph.t1 - ph.t0, el = clamp((t - ph.t0) / total);
  const cx = 1660, cy = 540, R = 120;
  ctx.fillStyle = 'rgba(20,20,20,0.9)'; ctx.beginPath(); ctx.arc(cx, cy, R + 22, 0, 7); ctx.fill();
  const nseg = Math.round(total / BEAT);
  const gone = Math.floor(el * nseg + 1e-6);
  for (let i = 0; i < nseg; i++) {
    const a0 = -Math.PI / 2 + i / nseg * Math.PI * 2 + 0.02, a1 = -Math.PI / 2 + (i + 1) / nseg * Math.PI * 2 - 0.02;
    ctx.strokeStyle = i < gone ? 'rgba(255,255,255,0.14)' : accent;
    ctx.lineWidth = 22; ctx.beginPath(); ctx.arc(cx, cy, R - 6, a0, a1); ctx.stroke();
  }
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, R - 22, 0, 7); ctx.clip();
  F.drawFigure(ctx, pose, cx, cy + 62, 34, accent, { shadow: false, gap: 'rgba(20,20,20,1)', farColor: accent, flip: t >= flipAt });
  ctx.restore();
  // left panel: recover = slowing heart + water bottle; stretch = breathing rings
  const lx = 260, ly = 540;
  ctx.fillStyle = 'rgba(20,20,20,0.9)'; ctx.beginPath(); ctx.arc(lx, ly, 142, 0, 7); ctx.fill();
  if (recover) {
    const u = t - ph.t0;
    const rate = lerp(2.4, 1.0, clamp(u / (total * 0.8))); // beats per second slowing down
    const hp = Math.exp(-(((u * rate) % 1)) * 7);
    heartIcon(lx - 40, ly - 10, 46 * (1 + 0.18 * hp), '#ff3b5c');
    bottleIcon(lx + 58, ly + 10, 62, 1 - clamp(u / total) * 0.6, t);
  } else {
    for (let i = 0; i < 3; i++) {
      ctx.strokeStyle = `rgba(255,210,31,${0.9 - i * 0.25})`; ctx.lineWidth = 10;
      ctx.beginPath(); ctx.arc(lx, ly, 30 + i * 28 + br * 24, 0, 7); ctx.stroke();
    }
    ctx.fillStyle = '#ffd21f'; ctx.beginPath(); ctx.arc(lx, ly, 18 + br * 14, 0, 7); ctx.fill();
  }
  // phase dots (which part of the break we are in) + upcoming level pips
  phases.forEach((p, i) => {
    const on = p === ph, done = t >= p.t1;
    ctx.beginPath(); ctx.arc(W / 2 + (i - (phases.length - 1) / 2) * 46, H - 70, on ? 15 : 11, 0, 7);
    ctx.fillStyle = on ? '#141414' : done ? 'rgba(20,20,20,0.55)' : 'rgba(255,255,255,0.55)'; ctx.fill();
  });
  if (!s.cooldown) {
    const nxt = s.world + 1;
    const tl = s.t1 - 2 * BEAT;
    const a = clamp((t - tl) / 0.3);
    if (a > 0) {
      for (let i = 0; i < 5; i++) {
        const x = W / 2 + (i - 2) * 52, y = 70;
        ctx.save(); ctx.globalAlpha = a;
        ctx.beginPath(); ctx.arc(x, y, i === nxt ? 18 + 6 * beatPulse(t) : 13, 0, 7);
        ctx.fillStyle = i < nxt ? 'rgba(20,20,20,0.6)' : i === nxt ? LV_COL[nxt] : 'rgba(255,255,255,0.5)'; ctx.fill();
        ctx.lineWidth = 4; ctx.strokeStyle = '#141414'; ctx.stroke();
        ctx.restore();
      }
    }
  }
  ctx.restore();
  ctx.lineWidth = 14 * W / rect.w; ctx.strokeStyle = '#ffffff';
  rr(0, 0, W, H, rect.r * W / rect.w); ctx.stroke();
  ctx.restore();
}

// ---------------- level card (black burst + 3D window + move list)
function holeRect(rect) {
  ctx.save();
  ctx.globalCompositeOperation = 'destination-out';
  rr(rect.x, rect.y, rect.w, rect.h, rect.r); ctx.fillStyle = '#000'; ctx.fill();
  ctx.restore();
}

function levelCard(li, t, s) {
  const u = t - s.t0, dur = s.t1 - s.t0;
  const ex = ss((u - (dur - 0.6)) / 0.6); // expand into the run
  const full = { x: 0, y: 0, w: W, h: H, r: 0 };
  const tile = { x: 410, y: 120, w: 1100, h: 619, r: 36 };
  const intro = easeOutBack(u / 0.45);
  const tw = tile.w * lerp(0.6, 1, intro), th = tile.h * lerp(0.6, 1, intro);
  const t0r = { x: W / 2 - tw / 2, y: tile.y + tile.h / 2 - th / 2, w: tw, h: th, r: tile.r };
  const R = { x: lerp(t0r.x, full.x, ex), y: lerp(t0r.y, full.y, ex), w: lerp(t0r.w, full.w, ex), h: lerp(t0r.h, full.h, ex), r: lerp(t0r.r, 0, ex) };
  burstBG(t, 1);
  holeRect(R);
  ctx.save();
  ctx.globalAlpha = 1 - ex;
  // tile frame
  ctx.lineWidth = 10; ctx.strokeStyle = LV_COL[li];
  ctx.shadowColor = LV_COL[li]; ctx.shadowBlur = 40;
  rr(R.x, R.y, R.w, R.h, R.r); ctx.stroke();
  ctx.shadowBlur = 0;
  // level pips on the tile
  for (let i = 0; i < 5; i++) {
    const cx = W / 2 + (i - 2) * 52, cy = R.y + 4;
    ctx.beginPath(); ctx.arc(cx, cy, 19, 0, 7);
    ctx.fillStyle = i <= li ? LV_COL[i] : '#222'; ctx.fill();
    ctx.lineWidth = 5; ctx.strokeStyle = '#fff'; ctx.stroke();
  }
  // move list popping in on the beats
  const ev = TL.levels[li].events.map((e) => e.move);
  const moves = ['run'];
  for (const m of ['jump', 'jump2', 'duck', 'left', 'turnL', 'sprint']) {
    if (ev.includes(m) || (m === 'left' && ev.includes('right')) || (m === 'turnL' && ev.includes('turnR'))) moves.push(m);
  }
  const n = moves.length, gapX = 200, x0 = W / 2 - (n - 1) * gapX / 2;
  moves.forEach((m, i) => {
    const tb = s.t0 + BEAT * (1 + i * 0.5);
    const a = easeOutBack((t - tb) / 0.3);
    if (t < tb) return;
    const x = x0 + i * gapX, y = 900;
    badge(m, x, y, 70, t + i * 0.3, { scale: a * (1 + 0.06 * beatPulse(t)) });
    if (m === 'left' || m === 'turnL') {
      ctx.save(); ctx.translate(x, y); ctx.scale(a, a);
      if (m === 'left') for (let k = 0; k < 2; k++) chevron(-44 + k * 14 + 100, -6, 18, 'right', MOVE_COL.right, 6);
      else curvedArrow(40, -30, 30, 1, MOVE_COL.turnR, 6);
      ctx.restore();
    }
    if (i < n - 1) {
      const pa = clamp((t - tb - 0.15) / 0.2);
      ctx.save(); ctx.globalAlpha = (1 - ex) * pa;
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 12; ctx.lineCap = 'round';
      const mx = x + gapX / 2;
      ctx.beginPath(); ctx.moveTo(mx - 16, y); ctx.lineTo(mx + 16, y); ctx.moveTo(mx, y - 16); ctx.lineTo(mx, y + 16); ctx.stroke();
      ctx.restore();
    }
  });
  ctx.restore();
  readySetGo(t, s, R, ex);
}

// ready - set - go lights over the preview window (beats 4, 5, 6 of the card), no text
function readySetGo(t, s, R, ex) {
  const cols = ['#ff3b30', '#ffcc00', '#2bd67b'];
  const t4 = s.t0 + 4 * BEAT;
  if (t < t4 - 0.2) return;
  const a = clamp((t - t4 + 0.2) / 0.2) * (1 - ex);
  if (a <= 0) return;
  const cx = R.x + R.w / 2, cy = R.y + R.h / 2;
  ctx.save(); ctx.globalAlpha = a;
  rr(cx - 230, cy - 90, 460, 180, 90); ctx.fillStyle = 'rgba(12,14,20,0.82)'; ctx.fill();
  ctx.lineWidth = 6; ctx.strokeStyle = '#ffffff'; ctx.stroke();
  for (let i = 0; i < 3; i++) {
    const ti = t4 + i * BEAT;
    const on = t >= ti;
    const go = i === 2 && on;
    const p = on ? Math.exp(-(t - ti) * 6) : 0;
    const x = cx + (i - 1) * 145;
    ctx.beginPath(); ctx.arc(x, cy, 56 + p * 10, 0, 7);
    ctx.fillStyle = on ? cols[i] : 'rgba(255,255,255,0.12)';
    if (on) { ctx.shadowColor = cols[i]; ctx.shadowBlur = 50; }
    ctx.fill(); ctx.shadowBlur = 0;
    if (go) { ctx.lineWidth = 8 * p; ctx.strokeStyle = cols[2]; ctx.beginPath(); ctx.arc(x, cy, 70 + (1 - p) * 120, 0, 7); ctx.stroke(); }
  }
  ctx.restore();
}

// ---------------- intro
const INTRO_TILES = [0, 1, 2, 3, 4].map((i) => ({ x: 960 + (i - 2) * 364 - 166, y: 330, w: 332, h: 236, r: 24 }));
function introUI(t) {
  const s = SEC.intro;
  const u = t - s.t0;
  burstBG(t, 1);
  const half = 2 * BAR;
  if (u < half + 0.3) {
    // big runner with heartbeat line
    const out = ss((u - half) / 0.3);
    ctx.save(); ctx.globalAlpha = 1 - out;
    const p = beatPulse(t, 7);
    ctx.fillStyle = '#000'; ctx.beginPath(); ctx.arc(W / 2, H / 2, 330 + p * 18, 0, 7); ctx.fill();
    ctx.lineWidth = 12; ctx.strokeStyle = '#2ad1ff'; ctx.stroke();
    ctx.lineWidth = 6; ctx.strokeStyle = `rgba(42,209,255,${0.6 * p})`;
    ctx.beginPath(); ctx.arc(W / 2, H / 2, 350 + p * 60, 0, 7); ctx.stroke();
    F.drawFigure(ctx, F.runPose(Math.PI * t / BEAT), W / 2, H / 2 + 230, 118, '#ffffff', { shadow: false, gap: '#000', farColor: '#bfc8d6' });
    // ECG line
    ctx.lineWidth = 8; ctx.strokeStyle = '#ff3b5c'; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.beginPath();
    for (let x = 0; x <= W; x += 6) {
      const ph = ((x / W) * 2 - t / BEAT * 0.5) % 1;
      const q = ((ph % 1) + 1) % 1;
      let yy = 0;
      if (q > 0.40 && q < 0.44) yy = -60 * Math.sin((q - 0.40) / 0.04 * Math.PI);
      if (q > 0.44 && q < 0.48) yy = 150 * Math.sin((q - 0.44) / 0.04 * Math.PI) * -1 * -1;
      if (q > 0.48 && q < 0.52) yy = -40 * Math.sin((q - 0.48) / 0.04 * Math.PI);
      const k = clamp(x / 300) * clamp((W - x) / 300);
      ctx.lineTo(x, 960 + yy * k * 0.6);
    }
    ctx.globalAlpha = (1 - out) * clamp(u / 0.5);
    ctx.stroke();
    ctx.restore();
  }
  if (u >= half) {
    const v = u - half;
    INTRO_TILES.forEach((T, i) => {
      const a = easeOutBack((v - i * BEAT * 0.5) / 0.4);
      if (a <= 0) return;
      const R = { x: T.x, y: T.y + (1 - a) * 500, w: T.w, h: T.h, r: T.r };
      holeRect(R);
      ctx.save();
      ctx.lineWidth = 9; ctx.strokeStyle = LV_COL[i]; ctx.shadowColor = LV_COL[i]; ctx.shadowBlur = 30;
      rr(R.x, R.y, R.w, R.h, R.r); ctx.stroke(); ctx.shadowBlur = 0;
      // pips under the tile + play button
      for (let k = 0; k < 5; k++) {
        ctx.beginPath(); ctx.arc(R.x + R.w / 2 + (k - 2) * 30, R.y + R.h + 46, 10, 0, 7);
        ctx.fillStyle = k <= i ? LV_COL[i] : '#222'; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = '#fff'; ctx.stroke();
      }
      const bp = 1 + 0.08 * beatPulse(t + i * 0.1);
      ctx.translate(R.x + R.w / 2, R.y + R.h + 112); ctx.scale(bp * 0.8, bp * 0.8);
      rr(-74, -34, 148, 68, 34); ctx.fillStyle = LV_COL[i]; ctx.fill(); ctx.lineWidth = 5; ctx.strokeStyle = '#fff'; ctx.stroke();
      ctx.fillStyle = '#111'; ctx.beginPath(); ctx.moveTo(-14, -18); ctx.lineTo(20, 0); ctx.lineTo(-14, 18); ctx.closePath(); ctx.fill();
      ctx.restore();
    });
  }
  const fin = clamp(1 - u / 0.5);
  if (fin > 0) { ctx.fillStyle = `rgba(0,0,0,${fin})`; ctx.fillRect(0, 0, W, H); }
}

function introGL(t) {
  const u = t - SEC.intro.t0 - 2 * BAR;
  if (u < 0) return false;
  renderer.setScissorTest(false);
  renderer.setClearColor(0x000000, 1);
  renderer.clear();
  INTRO_TILES.forEach((T, i) => {
    const a = easeOutBack((u - i * BEAT * 0.5) / 0.4);
    if (a <= 0) return;
    const y = Math.round(T.y + (1 - a) * 500);
    if (y > H) return;
    const L = TL.levels[i];
    const tt = L.t0 - 4.2 + u * 0.6;
    const vy = Math.max(0, y), vh = Math.min(T.h, H - vy);
    if (vh <= 4) return;
    renderLevel(i, tt, { x: T.x, y: vy, w: T.w, h: vh });
  });
  return true;
}

// ------------------------------------------------------------------ frame
function flash(t, at, k = 8, color = '255,255,255') {
  const u = t - at;
  if (u < 0 || u > 0.8) return;
  ctx.fillStyle = `rgba(${color},${Math.exp(-u * k)})`;
  ctx.fillRect(0, 0, W, H);
}

function renderFrame(f) {
  const t = f / FPS;
  const s = sectionAt(t);
  ctx.clearRect(0, 0, W, H);
  renderer.setClearColor(0x000000, 1);
  if (s.kind === 'intro') {
    introGL(t);
    introUI(t);
  } else if (s.kind === 'card') {
    renderLevel(s.world, t);
    levelCard(s.world, t, s);
  } else if (s.kind === 'level' || s.kind === 'finish') {
    const li = s.world;
    const cs = renderLevel(li, t);
    sprintFX(t, cs.sprint);
    coinFX(li, t);
    hud(li, t, cs, s.kind === 'finish' ? clamp(1 - (t - TL.finish_cross) / 0.6) : 1);
    if (s.kind === 'level') cues(li, t);
    if (s.kind === 'finish') {
      flash(t, TL.finish_cross, 6);
      confetti(TL.finish_cross, t);
      TL.stars.forEach((ts, i) => {
        const a = easeOutBack((t - ts) / 0.35);
        if (a <= 0) return;
        const x = W / 2 + (i - 1) * 190, y = 190 - (i === 1 ? 30 : 0);
        ctx.save(); ctx.translate(x, y); ctx.scale(a, a); ctx.rotate((1 - a) * 2);
        ctx.shadowColor = '#ffcf2e'; ctx.shadowBlur = 40;
        star(0, 0, i === 1 ? 96 : 78, '#ffcf2e', '#8a5200');
        ctx.restore();
      });
    }
  } else if (s.kind === 'rest') {
    const u = t - s.t0;
    let rect = { x: 0, y: 0, w: W, h: H, r: 0 };
    if (u < 0.75) {
      const li = s.world;
      renderLevel(li, t);
      if (!s.cooldown) hud(li, t, camState(li, t), 1 - clamp(u / 0.4));
      const k = easeOutBack(u / 0.75);
      const w = lerp(60, W, k), h = lerp(34, H, k);
      rect = { x: W / 2 - w / 2, y: lerp(470, H / 2, k) - h / 2, w, h, r: lerp(20, 0, clamp(u / 0.75)) };
    }
    restCard(s, t, rect);
    if (s.cooldown) confetti(TL.finish_cross, t, 170, 0.8);
  } else if (s.kind === 'outro') {
    const u = t - s.t0;
    burstBG(t, 1);
    const a = easeOutBack(u / 0.5);
    ctx.save(); ctx.translate(W / 2, H / 2 + 60 + Math.sin(t * 3) * 10); ctx.scale(a, a);
    ctx.fillStyle = '#ffcf2e33'; ctx.beginPath(); ctx.arc(0, -40, 330 + 20 * beatPulse(t), 0, 7); ctx.fill();
    trophy(0, 0, 230, t);
    ctx.restore();
    [0, 1, 2].forEach((i) => {
      const ap = easeOutBack((u - 0.3 - i * BEAT * 0.5) / 0.35);
      if (ap <= 0) return;
      ctx.save(); ctx.translate(W / 2 + (i - 1) * 200, 150 - (i === 1 ? 30 : 0)); ctx.scale(ap, ap);
      star(0, 0, i === 1 ? 90 : 72, '#ffcf2e', '#8a5200', Math.sin(t * 2 + i) * 0.1);
      ctx.restore();
    });
    confetti(s.t0 + 0.2, t, 170);
    const out = clamp((u - (s.t1 - s.t0 - 0.9)) / 0.9);
    if (out > 0) { ctx.fillStyle = `rgba(0,0,0,${out})`; ctx.fillRect(0, 0, W, H); }
  }
  // section-entry flashes
  for (const nm of ['card1', 'card2', 'card3', 'card4', 'card5', 'outro']) flash(t, SEC[nm].t0, 9);
}

// ---------------- big move cues (overlay pass): larger badge + clearer mimic figure
const OV = { x: 660, y: 0, w: 600, h: 520 };
const easeOutElastic = (u) => { u = clamp(u); if (u === 0 || u === 1) return u; return 2 ** (-10 * u) * Math.sin((u * 10 - 0.75) * (2 * Math.PI / 3)) + 1; };

function bigFigure(move, t, te, x, y, sc) {
  const P = 2 * BEAT;
  const fr = (v) => ((v % 1) + 1) % 1;
  let pose;
  if (move === 'jump' || move === 'jump2') pose = F.jumpPose(fr((t - te) / P + 0.25));
  else if (move === 'duck') pose = F.duckPose(fr((t - te) / P));
  else if (move === 'sprint') pose = F.runPose(Math.PI * 2 * t / BEAT, 1);
  else if (move === 'run') pose = F.runPose(Math.PI * t / BEAT);
  else pose = F.sideStepPose(fr((t - te) / P), (move === 'left' || move === 'turnL') ? -1 : 1);
  F.drawFigure(ctx, pose, x, y, sc, '#ffffff', { shadow: false, gap: 'rgba(16,18,26,1)', farColor: '#dfe6f2' });
}

function bigCues(li, t) {
  const L = TL.levels[li];
  const lead = li === 4 ? 3 : 4;
  let drew = false;
  for (const e of L.events) {
    const te = e.t_abs, ta = te - lead * BEAT;
    const tEnd = e.move === 'sprint' ? e.t_end_abs : te + 0.6;
    if (t < ta || t > tEnd + 0.3) continue;
    drew = true;
    const c = MOVE_COL[e.move];
    const a = t - ta;
    const go = t >= te;
    let sc = easeOutElastic(a / 0.55);
    let alpha = 1;
    if (t > tEnd) { const u = (t - tEnd) / 0.3; alpha = 1 - u; sc *= 1 + u * 0.35; }
    if (go) sc *= 1 + 0.22 * Math.exp(-(t - te) * 6);
    else sc *= 1 + 0.05 * beatPulse(t);
    const rot = 0.22 * (1 - clamp(a / 0.55)) * Math.sin(a * 22);
    const cx = 960, cy = 205, r = 142;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(cx, cy); ctx.rotate(rot); ctx.scale(sc, sc);
    // soft colour glow
    const g = ctx.createRadialGradient(0, 0, r * 0.7, 0, 0, r * 1.55);
    g.addColorStop(0, c + 'aa'); g.addColorStop(1, c + '00');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r * 1.55, 0, 7); ctx.fill();
    // disc
    const dg = ctx.createRadialGradient(-r * 0.3, -r * 0.35, r * 0.1, 0, 0, r);
    dg.addColorStop(0, '#2a2f3d'); dg.addColorStop(1, '#10121a');
    ctx.fillStyle = dg; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill();
    ctx.lineWidth = r * 0.12; ctx.strokeStyle = c; ctx.beginPath(); ctx.arc(0, 0, r - r * 0.06, 0, 7); ctx.stroke();
    // countdown arc
    if (!go) {
      const prog = 1 - clamp((t - ta) / (te - ta));
      ctx.lineWidth = r * 0.1; ctx.strokeStyle = '#ffffff'; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.arc(0, 0, r * 1.16, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * prog); ctx.stroke();
    } else {
      const u = t - te;
      ctx.fillStyle = `rgba(255,255,255,${0.55 * Math.exp(-u * 8)})`; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill();
    }
    // figure + direction marks
    ctx.save(); ctx.beginPath(); ctx.arc(0, 0, r * 0.9, 0, 7); ctx.clip();
    if (e.move === 'sprint') flame(0, r * 0.12, r * 0.6, t, 0.95);
    const lat = e.move === 'left' || e.move === 'turnL' ? -1 : e.move === 'right' || e.move === 'turnR' ? 1 : 0;
    bigFigure(e.move, t, te, -lat * r * 0.12, r * 0.64, r * 0.34);
    if (e.move === 'left' || e.move === 'right') {
      const k = ((t / BEAT) % 1);
      for (let i = 0; i < 2; i++) chevron(lat * (r * 0.5 + i * r * 0.17 + k * r * 0.05), -r * 0.02, r * 0.22, e.move, c, r * 0.075);
    }
    if (e.move === 'turnL' || e.move === 'turnR') curvedArrow(lat * r * 0.42, -r * 0.3, r * 0.42, lat, c, r * 0.085, t);
    if (e.move === 'jump' || e.move === 'jump2') {
      const n = e.move === 'jump2' ? 2 : 1;
      for (let i = 0; i < n; i++) chevron(r * 0.55, -r * 0.1 - i * r * 0.2 - ((t / BEAT) % 1) * r * 0.06, r * 0.2, 'up', c, r * 0.075);
    }
    if (e.move === 'duck') for (let i = 0; i < 2; i++) chevron(r * 0.55, -r * 0.25 + i * r * 0.2 + ((t / BEAT) % 1) * r * 0.06, r * 0.2, 'down', c, r * 0.075);
    ctx.restore();
    ctx.restore();
    // beat pips under the badge
    if (!go) {
      const nP = lead - 1;
      for (let k = 0; k < nP; k++) {
        const tk = te - (nP - k) * BEAT;
        const on = t >= tk;
        const pk = on ? Math.exp(-(t - tk) * 7) : 0;
        const px = cx + (k - (nP - 1) / 2) * 50, py = cy + r + 52;
        ctx.save(); ctx.globalAlpha = alpha * clamp(a / 0.3);
        ctx.beginPath(); ctx.arc(px, py, 15 + pk * 8, 0, 7);
        ctx.fillStyle = on ? c : 'rgba(16,18,26,0.85)'; ctx.fill();
        ctx.lineWidth = 4; ctx.strokeStyle = '#fff'; ctx.stroke();
        ctx.restore();
      }
    }
    // GO burst rings (kept inside the overlay window)
    const hits = e.move === 'jump2' ? [te, te + 2 * BEAT] : [te];
    for (const th of hits) {
      const u = t - th;
      if (u < 0 || u > 0.5) continue;
      ctx.save(); ctx.globalAlpha = (1 - u / 0.5) * alpha;
      ctx.lineWidth = 14 * (1 - u / 0.5) + 2; ctx.strokeStyle = c;
      ctx.beginPath(); ctx.arc(cx, cy, Math.min(r + 20 + u * 240, 196), 0, 7); ctx.stroke();
      ctx.restore();
    }
  }
  return drew;
}

window.renderOverlay = (f) => {
  const t = f / FPS;
  const s = sectionAt(t);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, OV.w, OV.h);
  if (s.kind !== 'level') return null;
  ctx.translate(-OV.x, -OV.y);
  const drew = bigCues(s.world, t);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  return drew ? ctx.canvas.toDataURL('image/png') : null;
};
if (Q.get('overlay') === '1') { ctx.canvas.width = OV.w; ctx.canvas.height = OV.h; }

window.renderFrame = (f) => { renderFrame(f); return true; };
window.TL = TL;
window.ready = true;
window.__dbg = { renderLevel, hud, cues, coinFX, camState, renderer, world };
