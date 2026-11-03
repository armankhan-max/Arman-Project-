// "Why Perfect Banks Didn't Work" — 2D billboard characters inside a stylized 3D Amsterdam bank (1600s).
// Stateless: every frame is a pure function of time, so frames can be rendered in parallel workers.
import * as THREE from './node_modules/three/build/three.module.js';

const TL = await (await fetch('./timeline.json')).json();
const Q = new URLSearchParams(location.search);
const W = +(Q.get('w') || 810), H = +(Q.get('h') || 1440);
const FPS = TL.fps, DUR = TL.duration;
const RS = W / 810; // resolution scale for pixel-sized effects
const TAU = Math.PI * 2;

// ------------------------------------------------------------------ utils
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const sstep = (a, b, x) => { const k = clamp((x - a) / (b - a), 0, 1); return k * k * (3 - 2 * k); };
const easeIO = k => k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
// periodic (40 s) smooth noise so the first and last frame match exactly
function pnoise(t, seed, k0 = 20, k1 = 70) { const r = rng(seed); let v = 0, n = 0; for (let i = 0; i < 4; i++) { const k = Math.round(lerp(k0, k1, r())); v += Math.sin(TAU * k * t / DUR + r() * TAU); n++; } return v / n; }

// ------------------------------------------------------------------ time: slow-mo + freezes
const SPEED_DT = 0.001;
function speedAt(t) {
  let k = 1;
  for (const [a, b, f] of TL.slowmo) { const r = 0.14; const w = sstep(a - r, a + r * 0.3, t) * (1 - sstep(b - r * 0.3, b + r, t)); k = Math.min(k, lerp(1, f, w)); }
  return k;
}
const STAB = (() => { const n = Math.ceil(DUR / SPEED_DT) + 2; const a = new Float64Array(n); for (let i = 1; i < n; i++) a[i] = a[i - 1] + speedAt((i - 0.5) * SPEED_DT) * SPEED_DT; return a; })();
function S(t) { const x = clamp(t, 0, DUR) / SPEED_DT; const i = Math.floor(x); const f = x - i; return STAB[i] + (STAB[Math.min(i + 1, STAB.length - 1)] - STAB[i]) * f; }
function frameTime(f) {
  let t = f / FPS;
  for (const F of TL.freezes) if (t >= F && t < F + 3 / FPS - 1e-6) t = F;
  return t;
}

// ------------------------------------------------------------------ renderer + targets
const canvas = document.createElement('canvas'); document.body.appendChild(canvas);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.shadowMap.autoUpdate = true;

const sceneRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4, depthTexture: new THREE.DepthTexture(W, H) });
const accRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthBuffer: false });
const nearRT = new THREE.WebGLRenderTarget(Math.ceil(W / 4), Math.ceil(H / 4), { type: THREE.HalfFloatType, depthBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
const nearRT2 = nearRT.clone();
const bloomA = new THREE.WebGLRenderTarget(Math.ceil(W / 4), Math.ceil(H / 4), { type: THREE.HalfFloatType, depthBuffer: false });
const bloomB = bloomA.clone();
const outRT = new THREE.WebGLRenderTarget(W, H, { depthBuffer: false });

const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const quadScene = new THREE.Scene();
const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2)); quadScene.add(quad);
const VS_Q = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }';
function pass(mat, target, clear = true) { quad.material = mat; renderer.setRenderTarget(target); if (clear) renderer.clear(); renderer.render(quadScene, quadCam); }

// ------------------------------------------------------------------ canvas textures
function ctex(w, h, draw, { srgb = true, rep = [1, 1], aniso = 4 } = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep[0], rep[1]); t.anisotropy = aniso; t.needsUpdate = true; return t;
}
const R0 = rng(7);
function veins(g, w, h, n, col) { g.strokeStyle = col; for (let i = 0; i < n; i++) { g.lineWidth = 0.5 + R0() * 2; g.beginPath(); let x = R0() * w, y = R0() * h; g.moveTo(x, y); for (let k = 0; k < 5; k++) { x += (R0() - 0.5) * 120; y += (R0() - 0.5) * 120; g.quadraticCurveTo(x + (R0() - 0.5) * 60, y + (R0() - 0.5) * 60, x, y); } g.stroke(); } }
const T = {};
T.hallFloor = ctex(512, 512, (g, w) => {
  const s = w / 2; [['#efe0bf', '#1d3d96'], ['#1d3d96', '#efe0bf']].forEach((row, j) => row.forEach((c, i) => { g.fillStyle = c; g.fillRect(i * s, j * s, s, s); }));
  veins(g, w, w, 26, 'rgba(255,255,255,0.16)'); veins(g, w, w, 18, 'rgba(20,20,60,0.12)');
  g.strokeStyle = '#d7a640'; g.lineWidth = 5; for (let i = 0; i <= 2; i++) { g.beginPath(); g.moveTo(i * s, 0); g.lineTo(i * s, w); g.moveTo(0, i * s); g.lineTo(w, i * s); g.stroke(); }
}, { rep: [6, 15] });
T.vaultFloor = ctex(512, 512, (g, w) => {
  const s = w / 2; [['#3a4566', '#252d46'], ['#252d46', '#3a4566']].forEach((row, j) => row.forEach((c, i) => { g.fillStyle = c; g.fillRect(i * s, j * s, s, s); }));
  veins(g, w, w, 20, 'rgba(255,255,255,0.07)');
  g.strokeStyle = '#b8892e'; g.lineWidth = 6; for (let i = 0; i <= 2; i++) { g.beginPath(); g.moveTo(i * s, 0); g.lineTo(i * s, w); g.moveTo(0, i * s); g.lineTo(w, i * s); g.stroke(); }
}, { rep: [8, 10] });
T.hallWall = ctex(512, 512, (g, w) => {
  g.fillStyle = '#1b3480'; g.fillRect(0, 0, w, w);
  for (let y = 0; y < w; y += 64) for (let x = (y / 64 % 2) * 32; x < w; x += 64) { g.fillStyle = 'rgba(255,205,110,0.10)'; g.beginPath(); g.arc(x, y, 14, 0, TAU); g.fill(); g.strokeStyle = 'rgba(255,205,110,0.12)'; g.lineWidth = 2; g.beginPath(); g.arc(x, y, 24, 0, TAU); g.stroke(); }
}, { rep: [12, 4] });
T.ceiling = ctex(512, 512, (g, w) => {
  g.fillStyle = '#c49a3e'; g.fillRect(0, 0, w, w); g.fillStyle = '#132a6b'; g.fillRect(24, 24, w - 48, w - 48); g.fillStyle = '#1b3a8a'; g.fillRect(60, 60, w - 120, w - 120);
  g.fillStyle = '#e8c160'; g.beginPath(); g.arc(w / 2, w / 2, 40, 0, TAU); g.fill();
}, { rep: [6, 15] });
T.steel = ctex(512, 512, (g, w) => {
  g.fillStyle = '#2d3a5e'; g.fillRect(0, 0, w, w);
  for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) { const x = i * 128, y = j * 128; const gr = g.createLinearGradient(x, y, x + 128, y + 128); gr.addColorStop(0, '#3e4f7c'); gr.addColorStop(1, '#27324f'); g.fillStyle = gr; g.fillRect(x + 4, y + 4, 120, 120); g.fillStyle = '#9aa6c4'; for (const [a, b] of [[12, 12], [116, 12], [12, 116], [116, 116]]) { g.beginPath(); g.arc(x + a, y + b, 4, 0, TAU); g.fill(); } }
  g.fillStyle = '#b8892e'; g.fillRect(0, 250, w, 12);
}, { rep: [8, 4] });
T.wood = ctex(256, 256, (g, w) => { g.fillStyle = '#6b3d1a'; g.fillRect(0, 0, w, w); for (let i = 0; i < 40; i++) { g.strokeStyle = `rgba(${40 + R0() * 40},${20 + R0() * 15},5,0.35)`; g.lineWidth = 1 + R0() * 3; const y = R0() * w; g.beginPath(); g.moveTo(0, y); g.bezierCurveTo(80, y + (R0() - .5) * 20, 160, y + (R0() - .5) * 20, w, y); g.stroke(); } for (let y = 0; y < w; y += 64) { g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(0, y, w, 3); } });
T.books = ctex(512, 512, (g, w) => {
  g.fillStyle = '#3a200c'; g.fillRect(0, 0, w, w); const pal = ['#9b1d1d', '#1e3f9b', '#2f7a3d', '#7a4b1f', '#5b2a7e', '#c08b2b', '#202848', '#a3461c'];
  for (let r = 0; r < 4; r++) { const y0 = r * 128 + 14; let x = 8; while (x < w - 10) { const bw = 12 + R0() * 20, bh = 86 + R0() * 26; const c = pal[Math.floor(R0() * pal.length)]; g.fillStyle = c; g.fillRect(x, y0 + 112 - bh, bw - 2, bh); g.fillStyle = '#e8c15e'; g.fillRect(x, y0 + 112 - bh + 8, bw - 2, 4); g.fillRect(x, y0 + 100, bw - 2, 4); g.fillStyle = 'rgba(255,255,255,0.12)'; g.fillRect(x + 2, y0 + 112 - bh, 3, bh); if (R0() < 0.12) { g.save(); g.translate(x, y0 + 112); g.rotate(-0.25); g.fillStyle = pal[Math.floor(R0() * pal.length)]; g.fillRect(0, -bh, bw, bh); g.restore(); x += 10; } x += bw; }
    g.fillStyle = '#5a3214'; g.fillRect(0, y0 + 112, w, 16); g.fillStyle = '#7d4a1f'; g.fillRect(0, y0 + 112, w, 4); }
}, { rep: [1, 1] });
function coinFace(gold) {
  return ctex(256, 256, (g, w) => {
    const c = w / 2; const gr = g.createRadialGradient(c - 30, c - 30, 10, c, c, c); if (gold) { gr.addColorStop(0, '#fff2b0'); gr.addColorStop(0.6, '#f0b93a'); gr.addColorStop(1, '#a8701a'); } else { gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.6, '#c9d2e3'); gr.addColorStop(1, '#7c879e'); }
    g.fillStyle = gr; g.fillRect(0, 0, w, w); g.strokeStyle = gold ? '#8a5a10' : '#5d6880'; g.lineWidth = 8; g.beginPath(); g.arc(c, c, c - 10, 0, TAU); g.stroke();
    g.fillStyle = gold ? '#9a6614' : '#66728c'; for (let i = 0; i < 36; i++) { const a = i / 36 * TAU; g.beginPath(); g.arc(c + Math.cos(a) * (c - 26), c + Math.sin(a) * (c - 26), 4, 0, TAU); g.fill(); }
    g.font = 'bold 120px DejaVu Serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = gold ? '#8a5a10' : '#56617a'; g.fillText('ƒ', c + 3, c + 5); g.fillStyle = gold ? '#ffe9a0' : '#f4f7ff'; g.fillText('ƒ', c, c);
    g.font = 'bold 22px DejaVu Serif'; g.fillText('1609', c, c + 78);
  });
}
T.coinG = coinFace(true); T.coinS = coinFace(false);
function coinEdge(gold) { return ctex(64, 64, (g, w) => { for (let y = 0; y < w; y += 8) { const gr = g.createLinearGradient(0, y, 0, y + 8); if (gold) { gr.addColorStop(0, '#ffe08a'); gr.addColorStop(0.5, '#d9a030'); gr.addColorStop(1, '#7a4c0c'); } else { gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.5, '#b8c2d6'); gr.addColorStop(1, '#5a6580'); } g.fillStyle = gr; g.fillRect(0, y, w, 8); } for (let x = 0; x < w; x += 4) { g.fillStyle = 'rgba(0,0,0,0.12)'; g.fillRect(x, 0, 1, w); } }); }
T.edgeG = coinEdge(true); T.edgeS = coinEdge(false);
T.door = ctex(1024, 1024, (g, w) => {
  const c = w / 2; const gr = g.createRadialGradient(c - 120, c - 160, 40, c, c, c); gr.addColorStop(0, '#7f93c2'); gr.addColorStop(0.7, '#3b4b78'); gr.addColorStop(1, '#232d4d'); g.fillStyle = gr; g.fillRect(0, 0, w, w);
  for (const [r, lw, col] of [[490, 22, '#d9a63a'], [430, 10, '#20294a'], [330, 14, '#c8952f'], [200, 8, '#20294a']]) { g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); g.arc(c, c, r, 0, TAU); g.stroke(); }
  g.fillStyle = '#e0b04a'; for (let i = 0; i < 24; i++) { const a = i / 24 * TAU; g.beginPath(); g.arc(c + Math.cos(a) * 460, c + Math.sin(a) * 460, 12, 0, TAU); g.fill(); }
  g.font = 'bold 64px DejaVu Serif'; g.textAlign = 'center'; g.fillStyle = '#f2c65a'; g.fillText('WISSELBANK', c, c - 360 + 20); g.fillText('1609', c, c + 395);
});
T.door.center.set(0.5, 0.5); T.door.rotation = Math.PI / 2;
T.plaque = ctex(1024, 320, (g, w, h) => {
  g.fillStyle = '#0f2160'; g.fillRect(0, 0, w, h); g.strokeStyle = '#e3b448'; g.lineWidth = 14; g.strokeRect(10, 10, w - 20, h - 20); g.lineWidth = 4; g.strokeRect(34, 34, w - 68, h - 68);
  const gr = g.createLinearGradient(0, 60, 0, 260); gr.addColorStop(0, '#fff1b0'); gr.addColorStop(0.5, '#f0b83a'); gr.addColorStop(1, '#b27818'); g.fillStyle = gr; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = 'bold 80px DejaVu Serif'; g.fillText('WHY PERFECT BANKS', w / 2, 118); g.font = 'bold 100px DejaVu Serif'; g.fillText("DIDN'T WORK", w / 2, 228);
}, { rep: [1, 1] });
T.banner = ctex(256, 512, (g, w, h) => {
  g.beginPath(); g.moveTo(0, 0); g.lineTo(w, 0); g.lineTo(w, h - 60); g.lineTo(w / 2, h); g.lineTo(0, h - 60); g.closePath(); g.fillStyle = '#183a9e'; g.fill(); g.strokeStyle = '#e2b244'; g.lineWidth = 14; g.stroke();
  g.fillStyle = '#e8b947'; g.beginPath(); g.arc(w / 2, 220, 70, 0, TAU); g.fill(); g.fillStyle = '#183a9e'; g.font = 'bold 110px DejaVu Serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('ƒ', w / 2, 226);
});
function archWin(top, bot) { return ctex(256, 512, (g, w, h) => { g.beginPath(); g.moveTo(0, h); g.lineTo(0, w / 2); g.arc(w / 2, w / 2, w / 2, Math.PI, 0); g.lineTo(w, h); g.closePath(); const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, top); gr.addColorStop(1, bot); g.fillStyle = gr; g.fill(); g.strokeStyle = 'rgba(60,40,20,0.85)'; g.lineWidth = 5; for (let x = 32; x < w; x += 48) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); } for (let y = 60; y < h; y += 56) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); } g.lineWidth = 16; g.strokeStyle = '#d6a845'; g.beginPath(); g.moveTo(8, h); g.lineTo(8, w / 2); g.arc(w / 2, w / 2, w / 2 - 8, Math.PI, 0); g.lineTo(w - 8, h); g.stroke(); }); }
T.winWarm = archWin('#fff6d8', '#ffc163'); T.winBlue = archWin('#9fb8ff', '#3d5ee0');
T.radial = ctex(128, 128, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, w); }, { srgb: false });
T.cobble = ctex(256, 256, (g, w) => { g.fillStyle = '#2a3552'; g.fillRect(0, 0, w, w); for (let y = 0; y < w; y += 32) for (let x = (y / 32 % 2) * 16; x < w + 16; x += 32) { g.fillStyle = `hsl(222,${20 + R0() * 10}%,${26 + R0() * 10}%)`; g.beginPath(); g.ellipse(x, y + 16, 14, 13, 0, 0, TAU); g.fill(); } }, { rep: [10, 20] });
function facade(col, seed) { const r = rng(seed); return ctex(256, 512, (g, w, h) => { g.fillStyle = col; g.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 12) { g.fillStyle = 'rgba(0,0,0,0.08)'; g.fillRect(0, y, w, 2); } for (let row = 0; row < 4; row++) for (let i = 0; i < 3; i++) { const x = 30 + i * 70, y = 150 + row * 85; const lit = r() < 0.55; g.fillStyle = '#f2ead8'; g.fillRect(x - 5, y - 5, 52, 68); g.fillStyle = lit ? '#ffcf6a' : '#1b2647'; g.fillRect(x, y, 42, 58); g.fillStyle = '#f2ead8'; g.fillRect(x + 19, y, 4, 58); g.fillRect(x, y + 27, 42, 4); } g.fillStyle = '#3a2210'; g.fillRect(100, 440, 56, 72); g.fillStyle = '#f2ead8'; g.fillRect(96, 436, 64, 6); }); }

// ------------------------------------------------------------------ scene
const scene = new THREE.Scene();
const FOG = new THREE.Color('#0e1838');
scene.fog = new THREE.FogExp2(FOG, 0.0095);
scene.background = FOG.clone();
const camera = new THREE.PerspectiveCamera(50, W / H, 0.05, 400);

const SUN = V(0.55, -1, -0.14).normalize();
scene.add(new THREE.HemisphereLight('#7f8fe0', '#7a4418', 0.55));
const sun = new THREE.DirectionalLight('#ffbf5e', 4.6);
sun.position.copy(V(0, 0, -50).addScaledVector(SUN, -90)); sun.target.position.set(0, 0, -50); scene.add(sun, sun.target);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -62, right: 62, top: 62, bottom: -62, near: 1, far: 220 }); sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.04; sun.shadow.radius = 3;
const hallLamp = new THREE.PointLight('#ffa648', 110, 45, 1.1); hallLamp.position.set(0, 11, -36); scene.add(hallLamp);
const vaultLamp = new THREE.PointLight('#ffa850', 170, 50, 1.0); vaultLamp.position.set(0, 9, -80); scene.add(vaultLamp);
const vaultFill = new THREE.PointLight('#4f6cff', 30, 30, 1.0); vaultFill.position.set(0, 5, -66); scene.add(vaultFill);
const extLight = new THREE.PointLight('#5f86ff', 120, 50, 1.0); extLight.position.set(22, 10, -48); scene.add(extLight);

const lam = (o) => new THREE.MeshLambertMaterial(o);
const gold = new THREE.MeshPhongMaterial({ color: '#e0a634', specular: '#fff1b8', shininess: 60, emissive: '#3a2200' });
const steelM = new THREE.MeshPhongMaterial({ color: '#56658e', specular: '#a8b4d8', shininess: 40 });
function add(geo, mat, x, y, z, o = {}) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); if (o.rx) m.rotation.x = o.rx; if (o.ry) m.rotation.y = o.ry; if (o.rz) m.rotation.z = o.rz; m.castShadow = o.cast ?? true; m.receiveShadow = o.recv ?? true; (o.parent || scene).add(m); return m; }
const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);

// ---- hall (x -12..12, z 0..-60, h 18)
add(new THREE.PlaneGeometry(24, 61.4), lam({ map: T.hallFloor }), 0, 0, -30.7, { rx: -Math.PI / 2, cast: false });
add(new THREE.PlaneGeometry(24, 60), lam({ map: T.ceiling, color: '#d8d8ff' }), 0, 18, -30, { rx: Math.PI / 2, cast: false });
const wallM = lam({ map: T.hallWall });
add(box(0.6, 18, 60), wallM, -12.3, 9, -30);
add(box(0.6, 18, 8.4), wallM, 12.3, 9, -55.8); add(box(0.6, 18, 48.4), wallM, 12.3, 9, -24.2); add(box(0.6, 12.5, 3.2), wallM, 12.3, 11.75, -50);
add(box(24, 18, 0.6), wallM, 0, 9, 0.3);
// side door frame (gold) + entrance doors
add(box(0.8, 0.5, 4.2), gold, 11.9, 5.75, -50); add(box(0.8, 5.5, 0.5), gold, 11.9, 2.75, -52); add(box(0.8, 5.5, 0.5), gold, 11.9, 2.75, -48);
add(box(7, 9, 0.3), lam({ map: T.wood }), 0, 4.5, -0.05); add(box(7.8, 0.6, 0.5), gold, 0, 9.2, -0.1);
// wainscot
const woodM = lam({ map: T.wood });
add(box(0.4, 2.6, 60), woodM, -11.9, 1.3, -30); add(box(0.4, 2.6, 8.4), woodM, 11.9, 1.3, -55.8); add(box(0.4, 2.6, 48.4), woodM, 11.9, 1.3, -24.2);
add(box(0.3, 0.3, 60), gold, -11.7, 2.65, -30); add(box(0.3, 0.3, 48.4), gold, 11.7, 2.65, -24.2);
add(box(0.3, 0.5, 60), gold, -11.7, 17.5, -30); add(box(0.3, 0.5, 60), gold, 11.7, 17.5, -30);
// columns
const colM = lam({ color: '#f1e3c2' });
for (const x of [-9, 9]) for (let z = -6; z >= -54; z -= 8) { add(new THREE.CylinderGeometry(0.7, 0.75, 16.6, 20), colM, x, 8.3, z); add(box(2, 0.8, 2), gold, x, 0.4, z); add(box(2.1, 1.0, 2.1), gold, x, 17.5, z); add(new THREE.TorusGeometry(0.78, 0.12, 8, 20), gold, x, 2.5, z, { rx: Math.PI / 2 }); }
// ledger shelves between columns
const booksM = lam({ map: T.books }); const caseM = lam({ color: '#4a2810' });
function bookcase(x, z, side) { const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2; scene.add(g); add(box(6.2, 7.6, 1.0), caseM, 0, 3.8, -0.1, { parent: g }); const f = add(new THREE.PlaneGeometry(5.8, 7.0), booksM, 0, 3.7, 0.42, { parent: g, cast: false }); add(box(6.6, 0.5, 1.3), gold, 0, 7.75, 0, { parent: g }); return f; }
for (let z = -10; z >= -50; z -= 8) { bookcase(-11.4, z, -1); if (z !== -50) bookcase(11.4, z, 1); }
// arched windows (left warm sun, right dusk blue)
const winWarmM = new THREE.MeshBasicMaterial({ map: T.winWarm, transparent: true, fog: false }); winWarmM.color.setRGB(2.6, 2.2, 1.7);
const winBlueM = new THREE.MeshBasicMaterial({ map: T.winBlue, transparent: true, fog: false }); winBlueM.color.setRGB(1.1, 1.2, 1.6);
for (let z = -10; z >= -50; z -= 8) { add(new THREE.PlaneGeometry(3.2, 6.4), winWarmM, -11.95, 12.0, z, { ry: Math.PI / 2, cast: false, recv: false }); add(new THREE.PlaneGeometry(3.2, 6.4), winBlueM, 11.95, 12.0, z === -50 ? -42 + 4 : z, { ry: -Math.PI / 2, cast: false, recv: false }); }
// desks with ledgers + candles
const flameM = new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 3.2, 1.2), fog: false });
const candles = [];
function desk(x, z) { add(box(3.6, 1.1, 1.7), woodM, x, 0.55, z); add(box(3.8, 0.12, 1.9), lam({ color: '#3d200b' }), x, 1.16, z); add(box(1.1, 0.16, 0.8), lam({ color: '#9b1d1d' }), x - 0.7, 1.3, z, { ry: 0.2 }); add(box(0.9, 0.05, 0.7), lam({ color: '#f3e7c8' }), x - 0.7, 1.4, z, { ry: 0.2 }); add(box(0.8, 0.3, 0.6), lam({ color: '#1e3f9b' }), x + 0.9, 1.37, z, { ry: -0.3 }); add(new THREE.CylinderGeometry(0.06, 0.06, 0.4, 8), lam({ color: '#f5ecd2' }), x + 0.2, 1.42, z + 0.3); const f = add(new THREE.SphereGeometry(0.07, 8, 6), flameM, x + 0.2, 1.7, z + 0.3, { cast: false }); f.scale.y = 1.8; candles.push(f); }
for (const z of [-12, -24, -36]) { desk(-5, z); desk(5, z); }
// chandeliers
for (const z of [-18, -42]) { add(new THREE.TorusGeometry(1.7, 0.1, 8, 32), gold, 0, 11.5, z, { rx: Math.PI / 2 }); add(new THREE.CylinderGeometry(0.04, 0.04, 6.5, 6), gold, 0, 14.8, z); for (let i = 0; i < 8; i++) { const a = i / 8 * TAU; const f = add(new THREE.SphereGeometry(0.09, 8, 6), flameM, Math.cos(a) * 1.7, 11.85, z + Math.sin(a) * 1.7, { cast: false }); f.scale.y = 1.7; candles.push(f); } }
// banners
const bannerM = lam({ map: T.banner, transparent: true, alphaTest: 0.5, side: THREE.DoubleSide });
for (const z of [-20, -40]) for (const x of [-6, 6]) add(new THREE.PlaneGeometry(2.2, 4.4), bannerM, x, 14.6, z, { cast: false });

// ---- end wall with round vault opening (hole centre y=4.2 r=4.6), front face z=-60, back z=-61.4
const DOOR_Y = 4.2, HOLE_R = 4.6;
{ const s = new THREE.Shape(); s.moveTo(-16, -1); s.lineTo(16, -1); s.lineTo(16, 18); s.lineTo(-16, 18); s.closePath(); const h = new THREE.Path(); h.absarc(0, DOOR_Y, HOLE_R, 0, TAU, true); s.holes.push(h);
  const g = new THREE.ExtrudeGeometry(s, { depth: 1.4, bevelEnabled: false, curveSegments: 48 }); const t = T.steel.clone(); t.repeat.set(0.12, 0.12); t.needsUpdate = true;
  add(g, [lam({ map: t }), lam({ color: '#1b2547' })], 0, 0, -61.4); }
add(new THREE.TorusGeometry(HOLE_R + 0.2, 0.32, 12, 64), gold, 0, DOOR_Y, -59.85);
add(new THREE.TorusGeometry(HOLE_R + 0.2, 0.22, 12, 64), gold, 0, DOOR_Y, -61.5);
{ const m = new THREE.MeshLambertMaterial({ map: T.plaque }); m.emissive = new THREE.Color('#2a1d05'); add(new THREE.PlaneGeometry(7.4, 2.31), m, 0, 11.45, -59.9, { cast: false }); add(box(7.8, 0.25, 0.4), gold, 0, 10.2, -59.85); add(box(7.8, 0.25, 0.4), gold, 0, 12.7, -59.85); }
// big gold lion-ish emblems flanking door
for (const x of [-8, 8]) { add(new THREE.CylinderGeometry(1.0, 1.0, 0.3, 32), gold, x, 8.5, -59.85, { rx: Math.PI / 2 }); }

// vault door (pivot on the left of the hole)
const doorPivot = new THREE.Group(); doorPivot.position.set(-4.85, DOOR_Y, -59.35); scene.add(doorPivot);
const doorGrp = new THREE.Group(); doorGrp.position.set(4.85, 0, 0); doorPivot.add(doorGrp);
{ const g = new THREE.CylinderGeometry(4.85, 4.85, 1.0, 72); g.rotateX(Math.PI / 2); const faceM = new THREE.MeshPhongMaterial({ map: T.door, specular: '#8090c0', shininess: 30 }); add(g, [steelM, faceM, steelM], 0, 0, 0, { parent: doorGrp });
  for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; add(new THREE.CylinderGeometry(0.18, 0.18, 0.5, 12), gold, Math.cos(a) * 4.2, Math.sin(a) * 4.2, 0.6, { rx: Math.PI / 2, parent: doorGrp }); }
  for (const y of [2.6, -2.6]) add(box(1.4, 0.8, 1.3), gold, -4.6, y, 0, { parent: doorGrp }); }
const wheel = new THREE.Group(); wheel.position.set(0, 0, 0.85); doorGrp.add(wheel);
add(new THREE.TorusGeometry(1.35, 0.13, 10, 40), gold, 0, 0, 0, { parent: wheel }); add(new THREE.CylinderGeometry(0.35, 0.35, 0.5, 20), gold, 0, 0, 0, { rx: Math.PI / 2, parent: wheel });
for (let i = 0; i < 3; i++) { const sp = add(box(2.7, 0.14, 0.14), gold, 0, 0, 0, { parent: wheel }); sp.rotation.z = i / 3 * Math.PI; }
for (let i = 0; i < 6; i++) { const a = i / 6 * TAU; add(new THREE.SphereGeometry(0.17, 10, 8), gold, Math.cos(a) * 1.35, Math.sin(a) * 1.35, 0, { parent: wheel }); }

// ---- vault (x -16..16, z -61.4..-100, h 16)
add(new THREE.PlaneGeometry(32, 38.6), lam({ map: T.vaultFloor }), 0, 0, -80.7, { rx: -Math.PI / 2, cast: false });
const vWallM = lam({ map: T.steel });
add(box(0.6, 16, 39), vWallM, -16.3, 8, -80.7); add(box(0.6, 16, 39), vWallM, 16.3, 8, -80.7); add(box(32, 16, 0.6), vWallM, 0, 8, -100.3);
// ceiling with skylight hole at x -9..-3, z -81..-75
{ const cm = lam({ map: T.steel, color: '#9aa3c8' }); const y = 16.3; add(box(32, 0.6, 19.4), cm, 0, y, -90.7); add(box(32, 0.6, 13.6), cm, 0, y, -68.2); add(box(7, 0.6, 6), cm, -12.5, y, -78); add(box(19, 0.6, 6), cm, 6.5, y, -78); for (let i = 0; i < 5; i++) add(box(0.15, 0.4, 6), steelM, -8.5 + i * 1.25, y, -78); }
add(new THREE.CylinderGeometry(3.2, 3.2, 0.3, 48), gold, 0, 8, -99.9, { rx: Math.PI / 2 });
add(box(32, 0.5, 0.4), gold, 0, 6.2, -99.8);
// coin stacks
const R1 = rng(42); const stacks = [];
const coinTopG = lam({ map: T.coinG, color: '#ffffff' }); const coinTopS = lam({ map: T.coinS });
function mkStack(x, z, r, h, isGold) { const e = (isGold ? T.edgeG : T.edgeS).clone(); e.needsUpdate = true; const side = new THREE.MeshPhongMaterial({ map: e, specular: isGold ? '#ffe7a0' : '#ffffff', shininess: 50, emissive: isGold ? '#2a1800' : '#0a0e18' }); const g = new THREE.CylinderGeometry(r, r, 1, 28); g.translate(0, 0.5, 0); const m = add(g, [side, isGold ? coinTopG : coinTopS, side], x, 0, z); stacks.push({ m, tex: e, h, r }); return m; }
for (const z of [-66, -70.5, -75, -79.5, -84, -88.5, -93]) for (const x of [-11, -7.5, -4, 4, 7.5, 11]) {
  const back = (-z - 66) / 27; const h = 2.6 + R1() * 4 + back * 5 + (Math.abs(x) > 6 ? 1.5 : 0); const isGold = R1() < 0.28;
  mkStack(x + (R1() - .5) * 0.5, z + (R1() - .5) * 0.5, 0.9 + R1() * 0.4, h, isGold);
  if (R1() < 0.7) mkStack(x + Math.sign(x) * (1.2 + R1() * 0.3), z + (R1() - .5) * 1.5, 0.45 + R1() * 0.25, 0.8 + R1() * 2.5, R1() < 0.4);
}
// velvet rope stanchions along the aisle
const ropeM = lam({ color: '#b3122a' });
for (const x of [-1.75, 1.75]) { let prev = null; for (let z = -64; z >= -95; z -= 3.1) { add(new THREE.CylinderGeometry(0.06, 0.1, 1.0, 10), gold, x, 0.5, z); add(new THREE.SphereGeometry(0.11, 10, 8), gold, x, 1.05, z); add(new THREE.CylinderGeometry(0.22, 0.25, 0.08, 16), gold, x, 0.04, z); if (prev !== null) { const c = new THREE.QuadraticBezierCurve3(V(x, 0.92, prev), V(x, 0.62, (prev + z) / 2), V(x, 0.92, z)); add(new THREE.TubeGeometry(c, 12, 0.035, 6), ropeM, 0, 0, 0, { cast: false }); } prev = z; } }
// shelves on vault side walls with silver bars + bags (instanced so they can be emptied over time)
const shelfM = lam({ color: '#7a5a34' });
for (const x of [-15.3, 15.3]) for (const y of [0.45, 1.65, 2.85, 4.05]) add(box(1.3, 0.1, 32), shelfM, x, y, -80);
for (const x of [-15.3, 15.3]) for (let z = -64; z >= -96; z -= 4) add(box(1.3, 4.3, 0.12), shelfM, x, 2.15, z);
const barGeo = box(0.52, 0.2, 0.26); const barMat = new THREE.MeshPhongMaterial({ color: '#d6deec', specular: '#ffffff', shininess: 70, emissive: '#121826' });
const bagGeo = new THREE.SphereGeometry(0.3, 12, 10); bagGeo.scale(1, 0.85, 1); const bagMat = lam({ color: '#8a5a2b' });
const bars = [], bags = [];
{ const r = rng(5); for (const x of [-15.3, 15.3]) for (const y of [0.5, 1.7, 2.9, 4.1]) for (let z = -95.5; z <= -64.5; z += 0.55) {
  if (r() < 0.22) { bags.push({ p: V(x + (r() - .5) * 0.3, y + 0.25, z), rm: 21.5 + r() * 9.5, ry: r() * 3 }); z += 0.2; continue; }
  for (let k = 0; k < 2 + Math.floor(r() * 2); k++) bars.push({ p: V(x + (r() - .5) * 0.4, y + 0.1 + k * 0.2, z), rm: 21.5 + r() * 9.5, ry: (k % 2) * 0.1 });
} }
// keep one lonely bar on the shelf that the camera opens on at 26 s
bars.push({ p: V(-15.15, 3.0, -80.2), rm: 999, ry: 0.15, lone: true });
const barIM = new THREE.InstancedMesh(barGeo, barMat, bars.length); barIM.castShadow = true; scene.add(barIM);
const bagIM = new THREE.InstancedMesh(bagGeo, bagMat, bags.length); bagIM.castShadow = true; scene.add(bagIM);

// ---- exterior (dusk street + canal), seen through the side door
add(new THREE.PlaneGeometry(30, 80), lam({ map: T.cobble }), 27, -0.02, -50, { rx: -Math.PI / 2, cast: false });
{ const wm = new THREE.MeshPhongMaterial({ color: '#1f3f9a', specular: '#bcd0ff', shininess: 90, emissive: '#0a1640' }); add(new THREE.PlaneGeometry(8, 80), wm, 21, -0.5, -50, { rx: -Math.PI / 2, cast: false }); add(box(0.6, 0.6, 80), lam({ color: '#6b6f80' }), 16.8, -0.2, -50); add(box(0.6, 0.6, 80), lam({ color: '#6b6f80' }), 25.2, -0.2, -50); }
{ const cols = ['#8b3a2a', '#2b3f7e', '#2f6e4a', '#b5832f', '#7a2a4a', '#9a4a1e', '#3a5a8e']; let z = -70;
  for (let i = 0; z < -28; i++) { const w = 4.4 + (i % 3) * 0.6, h = 9 + ((i * 7) % 4); const s = new THREE.Shape(); s.moveTo(-w / 2, 0); s.lineTo(w / 2, 0); s.lineTo(w / 2, h); s.lineTo(w / 2 - 0.6, h); s.lineTo(w / 2 - 0.6, h + 1.2); s.lineTo(w / 4, h + 1.2); s.lineTo(w / 4, h + 2.4); s.lineTo(0.5, h + 2.4); s.lineTo(0, h + 3.4); s.lineTo(-0.5, h + 2.4); s.lineTo(-w / 4, h + 2.4); s.lineTo(-w / 4, h + 1.2); s.lineTo(-w / 2 + 0.6, h + 1.2); s.lineTo(-w / 2 + 0.6, h); s.lineTo(-w / 2, h); s.closePath();
    const g = new THREE.ShapeGeometry(s); const uv = g.attributes.uv; for (let k = 0; k < uv.count; k++) uv.setXY(k, (uv.getX(k) + w / 2) / w, uv.getY(k) / (h + 3.4)); const ft = facade(cols[i % cols.length], 100 + i); ft.wrapS = ft.wrapT = THREE.ClampToEdgeWrapping;
    const m = new THREE.MeshLambertMaterial({ map: ft, emissive: '#ffffff', emissiveMap: ft, emissiveIntensity: 0.35, side: THREE.DoubleSide }); add(g, m, 29, 0, z + w / 2, { ry: -Math.PI / 2 }); add(box(6, h, w - 0.1), lam({ color: '#181d33' }), 32.1, h / 2, z + w / 2); z += w + 0.15; } }
{ const sky = new THREE.Mesh(new THREE.SphereGeometry(180, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, fog: false, depthWrite: false, uniforms: {}, vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }', fragmentShader: 'varying vec3 vP; void main(){ float h = clamp(vP.y,0.,1.); vec3 c = mix(vec3(1.0,0.45,0.18), vec3(0.06,0.10,0.35), pow(h,0.45)); c = mix(c, vec3(0.03,0.05,0.2), smoothstep(0.4,1.,h)); gl_FragColor = vec4(c*1.2,1.); }' })); sky.position.set(0, 0, -50); scene.add(sky); }
{ const moon = add(new THREE.CircleGeometry(4, 32), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 2.9, 2.4), fog: false }), 120, 40, -60, { ry: -Math.PI / 2, cast: false, recv: false }); }
// VOC ship waiting in the canal (sinks when "the company started failing")
T.sail = ctex(256, 256, (g, w) => { g.fillStyle = '#f3ead2'; g.fillRect(0, 0, w, w); g.strokeStyle = '#c8b88e'; g.lineWidth = 3; for (let x = 0; x < w; x += 32) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, w); g.stroke(); } g.fillStyle = '#c0392b'; g.font = 'bold 120px DejaVu Serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('VOC', w / 2, w / 2 + 6); });
const ship = new THREE.Group(); ship.position.set(21, -0.35, -49); scene.add(ship);
{ const b = ship; add(box(2.6, 1.3, 8), woodM, 0, 0.3, 0, { parent: b }); add(box(2.8, 0.25, 8.2), gold, 0, 0.95, 0, { parent: b }); add(box(2.4, 1.2, 1.8), woodM, 0, 1.6, -3.2, { parent: b }); for (let i = 0; i < 4; i++) add(new THREE.SphereGeometry(0.4, 10, 8), bagMat, (i % 2 - 0.5) * 0.8, 1.35, 1.6 - i * 0.6, { parent: b });
  add(new THREE.CylinderGeometry(0.09, 0.12, 8, 8), woodM, 0, 5, 0.6, { parent: b }); add(new THREE.CylinderGeometry(0.05, 0.05, 3.6, 6), woodM, 0, 7.0, 0.6, { parent: b, rz: Math.PI / 2, rx: Math.PI / 2 });
  const sail = add(new THREE.PlaneGeometry(3.4, 3.6), lam({ map: T.sail, side: THREE.DoubleSide, emissive: '#30281a' }), 0, 5.1, 0.75, { parent: b, ry: Math.PI / 2 }); sail.name = 'sail';
  add(new THREE.PlaneGeometry(1.2, 0.7), lam({ color: '#e8742a', side: THREE.DoubleSide }), 0, 9.2, 0.9, { parent: b, ry: Math.PI / 2 });
  const l = add(new THREE.SphereGeometry(0.16, 10, 8), flameM, 0, 2.6, 3.6, { parent: b, cast: false }); candles.push(l); }

// ------------------------------------------------------------------ volumetric light shafts (additive)
const shaftMats = [];
function shaft(origin, dir, len, w, d, inten, col) {
  const g = box(w, len, d); g.translate(0, len / 2, 0);
  const m = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false,
    uniforms: { uI: { value: inten }, uC: { value: new THREE.Color(col) }, uT: { value: 0 }, uDim: { value: V(w, len, d) } },
    vertexShader: 'uniform vec3 uDim; varying vec3 vL; varying vec3 vN; varying vec3 vV; void main(){ vL = position/uDim; vec4 mv = modelViewMatrix*vec4(position,1.); vN = normalMatrix*normal; vV = -mv.xyz; gl_Position = projectionMatrix*mv; }',
    fragmentShader: 'uniform float uI; uniform vec3 uC; uniform float uT; varying vec3 vL; varying vec3 vN; varying vec3 vV; void main(){ float a = vL.y; float ex = 1.-smoothstep(0.2,0.5,abs(vL.x)); float ez = 1.-smoothstep(0.25,0.5,abs(vL.z)); float fr = pow(abs(dot(normalize(vN),normalize(vV))),1.6); float st = 0.7+0.3*sin(vL.z*23.+vL.x*9.+uT*0.94)*sin(vL.x*13.-uT*0.63); float k = uI*(0.25+0.75*(1.-a))*ex*ez*fr*st*smoothstep(0.,0.06,a)*(1.-smoothstep(0.8,1.,a)); gl_FragColor = vec4(uC*k,1.); }' });
  const mesh = new THREE.Mesh(g, m); mesh.position.copy(origin); mesh.quaternion.setFromUnitVectors(V(0, 1, 0), dir.clone()); mesh.renderOrder = 10; scene.add(mesh); shaftMats.push(m); return mesh;
}
for (let z = -10; z >= -50; z -= 8) shaft(V(-11.6, 12, z), SUN, 13.5, 4.6, 3.0, 0.16, '#ffc970');
shaft(V(-6, 16.4, -78), SUN, 19, 6, 6, 0.22, '#ffd27e');
shaft(V(12.2, 3.0, -50), V(-1, -0.35, 0.05).normalize(), 6, 4.5, 3, 0.10, '#6f8fff');

// ------------------------------------------------------------------ particles (dust motes, coin dust, poofs)
const MAXP = 4000;
const pGeo = new THREE.BufferGeometry(); const pPos = new Float32Array(MAXP * 3), pCol = new Float32Array(MAXP * 4), pSize = new Float32Array(MAXP);
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3)); pGeo.setAttribute('color', new THREE.BufferAttribute(pCol, 4)); pGeo.setAttribute('size', new THREE.BufferAttribute(pSize, 1));
const pMat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uScale: { value: H * 0.5 } },
  vertexShader: 'attribute vec4 color; attribute float size; uniform float uScale; varying vec4 vC; varying float vSoft; void main(){ vec4 mv = modelViewMatrix*vec4(position,1.); float d = -mv.z; gl_PointSize = clamp(size*uScale/d, 1., 160.); vSoft = clamp(1.2/d,0.,1.); vC = color; vC.a *= clamp(d*2.-0.2,0.,1.) / (1.+ max(0., 0.6/d - 0.2)); gl_Position = projectionMatrix*mv; }',
  fragmentShader: 'varying vec4 vC; varying float vSoft; void main(){ vec2 p = gl_PointCoord*2.-1.; float r = dot(p,p); if(r>1.) discard; float a = mix(1.-r, smoothstep(1.,0.6,r)*0.7, vSoft); gl_FragColor = vec4(vC.rgb*vC.a*a,1.); }' });
const points = new THREE.Points(pGeo, pMat); points.frustumCulled = false; points.renderOrder = 11; scene.add(points);
const motes = []; { const r = rng(99); for (let i = 0; i < 700; i++) { const inVault = i % 2; motes.push({ b: inVault ? V((r() - .5) * 30, r() * 14, -62 - r() * 36) : V((r() - .5) * 22, r() * 16, -2 - r() * 57), k: [1 + Math.floor(r() * 3), 1 + Math.floor(r() * 3), 1 + Math.floor(r() * 3)], ph: [r() * TAU, r() * TAU, r() * TAU], s: 0.02 + r() * 0.035 }); } }

// ------------------------------------------------------------------ 2D characters (canvas sprites as billboards)
const CW = 512, CH = 900, PX = 1.6 / CW; // world units per sprite pixel
const OUTFIT = {
  clerk: { coat: '#3f9cf0', coat2: '#2a78c8', hood: true, badge: true },
  official: { coat: '#c4202f', coat2: '#8e1220', ruff: true, hat: 'capotain' },
  porter: { coat: '#3fae5a', coat2: '#2b8442', hood: true, hair: '#6b4220' },
};
const CROWD_COLS = [['#f08a2a', 'none', null, '#5a3418'], ['#8a4ad0', 'bonnet'], ['#26b5b0', 'none', null, '#2a2a33'], ['#e04a6a', 'cap', '#2a2a2a'], ['#8ab52a', 'none', null, '#7a4a20'], ['#f0c030', 'bonnet'], ['#2a2a3a', 'none', null, '#3a2414'], ['#c06a32', 'beret', '#a01a3a']];
CROWD_COLS.forEach((c, i) => { OUTFIT['crowd' + i] = { coat: c[0], coat2: shade(c[0], -0.25), hat: c[1], capCol: c[2] || '#333', hood: true, hair: c[3] || null }; });
function shade(hex, k) { const c = new THREE.Color(hex); c.offsetHSL(0, 0, k * 0.5); return '#' + c.getHexString(); }

const spriteVS = `varying vec2 vUv; varying float vFog; void main(){ vUv = uv; vec4 mv = modelViewMatrix*vec4(position,1.); vFog = -mv.z; gl_Position = projectionMatrix*mv; }`;
const spriteFS = `uniform sampler2D map; uniform vec2 uRim; uniform vec3 uRimC; uniform vec3 uRim2C; uniform vec3 uTint; uniform vec3 fogC; uniform float fogD; uniform float uOp; uniform vec2 uTexel; varying vec2 vUv; varying float vFog;
void main(){ vec4 c = texture2D(map, vUv); if(c.a < 0.02) discard;
  float a1 = texture2D(map, vUv + uRim*uTexel*9.).a; float a2 = texture2D(map, vUv - uRim*uTexel*7.).a;
  float r1 = c.a*(1.-a1); float r2 = c.a*(1.-a2);
  vec3 col = c.rgb*uTint + uRimC*r1*1.6 + uRim2C*r2*0.7;
  float f = 1. - exp(-fogD*fogD*vFog*vFog); col = mix(col, fogC, f);
  gl_FragColor = vec4(col, c.a*uOp); }`;
const shadowGeo = new THREE.PlaneGeometry(1, 1); shadowGeo.rotateX(-Math.PI / 2);
class Char {
  constructor(name) {
    this.name = name; this.o = OUTFIT[name]; this.cv = document.createElement('canvas'); this.cv.width = CW; this.cv.height = CH; this.g = this.cv.getContext('2d');
    this.tex = new THREE.CanvasTexture(this.cv); this.tex.colorSpace = THREE.SRGBColorSpace; this.tex.anisotropy = 4;
    this.mat = new THREE.ShaderMaterial({ vertexShader: spriteVS, fragmentShader: spriteFS, alphaToCoverage: true, side: THREE.DoubleSide,
      uniforms: { map: { value: this.tex }, uRim: { value: new THREE.Vector2(1, 0) }, uRimC: { value: new THREE.Color('#ffd47a') }, uRim2C: { value: new THREE.Color('#5c7dff') }, uTint: { value: new THREE.Color(1, 1, 1) }, fogC: { value: FOG }, fogD: { value: scene.fog.density }, uOp: { value: 1 }, uTexel: { value: new THREE.Vector2(1 / CW, 1 / CH) } } });
    const g = new THREE.PlaneGeometry(CW * PX, CH * PX); g.translate(0, CH * PX / 2 - 16 * PX, 0);
    this.mesh = new THREE.Mesh(g, this.mat); this.mesh.frustumCulled = false; scene.add(this.mesh);
    this.sh = new THREE.Mesh(shadowGeo, new THREE.MeshBasicMaterial({ map: T.radial, transparent: true, depthWrite: false, color: '#000000', opacity: 0.6, fog: false })); this.sh.renderOrder = 5; scene.add(this.sh);
  }
  hide() { this.mesh.visible = false; this.sh.visible = false; }
}
const chars = {}; for (const n of Object.keys(OUTFIT)) chars[n] = new Char(n);

function drawChar(C, st) {
  const g = C.g, o = C.o; g.clearRect(0, 0, CW, CH); g.save();
  g.translate(CW / 2, CH - 16); const sq = st.squash || 1; g.scale((st.flip ? -1 : 1) / Math.sqrt(sq), sq);
  const K = '#101018'; g.lineCap = 'round'; g.lineJoin = 'round';
  const ph = st.walk ?? null, bob = ph === null ? Math.sin(st.a * 2.2) * 3 : -Math.abs(Math.sin(ph)) * 10;
  const run = st.run ? 1.4 : 1;
  // thick white legs + round feet (outlined tubes, not sticks)
  const feet = [[-30, 0], [30, Math.PI]].map(([x, off]) => { if (ph === null) return [x * 1.15, 0]; const s = Math.sin(ph + off); return [x + s * 48 * run, Math.max(0, Math.cos(ph + off)) * 22 * run]; });
  feet.forEach(([fx, lift], i) => { g.beginPath(); g.ellipse(fx + 14, -28 - lift, 42, 26, 0, 0, TAU); g.fillStyle = '#ffffff'; g.fill(); g.strokeStyle = K; g.lineWidth = 9; g.stroke(); });
  feet.forEach(([fx, lift], i) => { const hx = i ? 28 : -28; g.beginPath(); g.moveTo(hx, -300 + bob); g.lineTo(fx, -48 - lift); g.strokeStyle = K; g.lineWidth = 46; g.stroke(); g.strokeStyle = '#ffffff'; g.lineWidth = 32; g.stroke(); g.fillStyle = 'rgba(30,40,80,0.10)'; });
  feet.forEach(([fx, lift]) => { g.beginPath(); g.ellipse(fx + 14, -28 - lift, 34, 18, 0, Math.PI * 1.05, Math.PI * 1.95, true); g.fillStyle = '#ffffff'; g.fill(); });
  g.save(); g.translate(0, bob);
  const hands = poseHands(st);
  // neck
  g.fillStyle = '#ffffff'; g.strokeStyle = K; g.lineWidth = 7; g.beginPath(); g.rect(-11, -495, 22, 60); g.fill(); g.stroke();
  // hoodie / coat body
  g.beginPath(); g.moveTo(-64, -452); g.quadraticCurveTo(0, -474, 64, -452); g.quadraticCurveTo(84, -380, 82, -292); g.quadraticCurveTo(0, -272, -82, -292); g.quadraticCurveTo(-84, -380, -64, -452); g.closePath(); g.fillStyle = o.coat; g.fill();
  g.save(); g.clip(); g.fillStyle = 'rgba(0,0,40,0.20)'; g.fillRect(28, -500, 80, 260); g.fillStyle = 'rgba(255,255,255,0.14)'; g.fillRect(-90, -500, 28, 260); g.fillStyle = o.coat2; g.fillRect(-100, -312, 200, 40); g.restore();
  g.lineWidth = 10; g.strokeStyle = K; g.stroke();
  if (o.hood) {
    g.beginPath(); g.ellipse(0, -452, 66, 24, 0, 0, TAU); g.fillStyle = o.coat2; g.fill(); g.lineWidth = 7; g.stroke();
    g.beginPath(); g.ellipse(0, -456, 26, 11, 0, 0, TAU); g.fillStyle = '#0d1020'; g.fill();
    g.strokeStyle = '#f4f6ff'; g.lineWidth = 6; for (const x of [-15, 15]) { g.beginPath(); g.moveTo(x, -440); g.lineTo(x * 1.1, -392); g.stroke(); }
    g.fillStyle = o.coat2; g.strokeStyle = 'rgba(0,0,20,0.6)'; g.lineWidth = 4; g.beginPath(); g.roundRect(-46, -362, 92, 46, 8); g.fill(); g.stroke();
  }
  if (o.badge) { g.fillStyle = '#f2c14a'; g.strokeStyle = K; g.lineWidth = 5; g.beginPath(); g.arc(46, -414, 15, 0, TAU); g.fill(); g.stroke(); g.fillStyle = '#7a4c0c'; g.font = 'bold 22px DejaVu Serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('ƒ', 46, -413); }
  if (!o.hood) { g.fillStyle = '#f2c14a'; g.strokeStyle = K; g.lineWidth = 3; for (const y of [-420, -385, -350, -315]) { g.beginPath(); g.arc(0, y, 8, 0, TAU); g.fill(); g.stroke(); } }
  if (o.ruff) { g.fillStyle = '#ffffff'; g.strokeStyle = K; g.lineWidth = 6; g.beginPath(); g.ellipse(0, -458, 100, 30, 0, 0, TAU); g.fill(); g.stroke(); g.lineWidth = 3; for (let i = -4; i <= 4; i++) { g.beginPath(); g.moveTo(i * 20, -434); g.lineTo(i * 22, -482); g.stroke(); } }
  if (st.pose === 'carry') drawBag(g, 0, -345, 1);
  if (st.pose === 'scroll') { g.save(); g.translate(150, -420); g.rotate(-0.12); g.fillStyle = '#f6ecd0'; g.strokeStyle = K; g.lineWidth = 6; g.beginPath(); g.rect(-62, -82, 124, 164); g.fill(); g.stroke(); g.fillStyle = '#e8d8a8'; for (const y of [-86, 86]) { g.beginPath(); g.ellipse(0, y, 70, 12, 0, 0, TAU); g.fill(); g.stroke(); } g.fillStyle = '#7a1a1a'; g.font = 'bold 38px DejaVu Serif'; g.textAlign = 'center'; g.fillText('LOAN', 0, -22); g.fillStyle = '#2a2a2a'; for (let i = 0; i < 3; i++) g.fillRect(-42, 0 + i * 16, 84, 4); g.fillStyle = '#c41a2a'; g.beginPath(); g.arc(28, 58, 16, 0, TAU); g.fill(); g.restore(); }
  // sleeves (thick, coat colour) + big white hands
  for (const [sx, h] of [[58, hands.R], [-58, hands.L]]) { g.beginPath(); g.moveTo(sx, -432); const mx = (sx + h[0]) / 2 + Math.sign(sx) * 20, my = (-432 + h[1]) / 2 + 16; g.quadraticCurveTo(mx, my, h[0] * 0.9 + sx * 0.1, h[1] + (h[1] < -432 ? 12 : -12)); g.strokeStyle = K; g.lineWidth = 42; g.stroke(); g.strokeStyle = o.coat; g.lineWidth = 29; g.stroke(); }
  for (const h of [hands.R, hands.L]) { g.beginPath(); g.arc(h[0], h[1], 28, 0, TAU); g.fillStyle = '#ffffff'; g.fill(); g.strokeStyle = K; g.lineWidth = 8; g.stroke(); }
  if (st.pose === 'shh') { g.fillStyle = '#fff'; g.strokeStyle = K; g.lineWidth = 7; g.beginPath(); g.roundRect(hands.R[0] - 9, hands.R[1] - 62, 18, 52, 9); g.fill(); g.stroke(); }
  if (st.pose === 'flip') { g.fillStyle = '#fff'; g.strokeStyle = K; g.lineWidth = 7; g.beginPath(); g.roundRect(hands.R[0] - 30, hands.R[1] - 18, 32, 16, 8); g.fill(); g.stroke(); }
  // head
  const hx = 0, hy = -600, hr = 122;
  g.beginPath(); g.arc(hx, hy, hr, 0, TAU); g.fillStyle = '#dde2ef'; g.fill(); g.save(); g.clip(); g.beginPath(); g.arc(hx - 18, hy - 18, hr - 6, 0, TAU); g.fillStyle = '#ffffff'; g.fill(); g.restore();
  g.lineWidth = 11; g.strokeStyle = K; g.stroke();
  if (o.hair) { g.save(); g.beginPath(); g.arc(hx, hy, hr - 4, 0, TAU); g.clip(); g.fillStyle = o.hair; g.beginPath(); g.ellipse(hx, hy - 70, 140, 82, 0, 0, TAU); g.fill(); g.fillStyle = 'rgba(255,255,255,0.18)'; g.fillRect(hx - 6, hy - 160, 12, 80); g.restore(); g.beginPath(); g.arc(hx, hy, hr, Math.PI * 1.08, Math.PI * 1.92); g.lineWidth = 11; g.stroke(); g.beginPath(); g.moveTo(hx - hr + 6, hy - 40); g.quadraticCurveTo(hx, hy + 2 - 30, hx + hr - 6, hy - 40); g.lineWidth = 6; g.stroke(); }
  drawFace(g, st, hx, hy + (o.hair ? 12 : 0));
  drawHat(g, o, hx, hy, hr);
  g.restore(); g.restore();
  C.tex.needsUpdate = true;
}
function drawBag(g, x, y, s) { g.save(); g.translate(x, y); g.scale(s, s); g.fillStyle = '#9a6430'; g.strokeStyle = '#101018'; g.lineWidth = 9; g.beginPath(); g.moveTo(-30, -78); g.quadraticCurveTo(-100, -40, -92, 20); g.quadraticCurveTo(-80, 80, 0, 82); g.quadraticCurveTo(80, 80, 92, 20); g.quadraticCurveTo(100, -40, 30, -78); g.closePath(); g.fill(); g.stroke(); g.fillStyle = '#7a4a1e'; g.beginPath(); g.moveTo(-34, -78); g.lineTo(-48, -112); g.lineTo(48, -112); g.lineTo(34, -78); g.closePath(); g.fill(); g.stroke(); g.fillStyle = '#f2c14a'; g.font = 'bold 70px DejaVu Serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('ƒ', 0, 10); g.restore(); }
function poseHands(st) {
  const a = st.a, ph = st.walk;
  const sw = ph === null || ph === undefined ? 0 : Math.sin(ph) * 30;
  switch (st.pose) {
    case 'crossed': return { R: [-34, -372], L: [36, -366] };
    case 'flip': return { R: [104, -455 + (st.flipK || 0) * -20], L: [-92, -300] };
    case 'carry': return { R: [86, -372], L: [-86, -372] };
    case 'shh': return { R: [12, -500], L: [-92, -300] };
    case 'scroll': return { R: [96, -360], L: [-92, -300] };
    case 'holdout': return { R: [30, -352], L: [-30, -352] };
    case 'panic': return { R: [128, -585 + Math.sin(a * 30) * 6], L: [-128, -585 - Math.sin(a * 30) * 6] };
    case 'fists': return { R: [140, -660 + Math.sin(a * 13 + st.seed) * 24], L: [-140, -650 - Math.sin(a * 13 + st.seed) * 24] };
    case 'cheer': return { R: [120, -690 + Math.sin(a * 9 + st.seed) * 18], L: [-120, -690 - Math.sin(a * 9 + st.seed) * 18] };
    case 'catch': return { R: [70, -370], L: [-92, -300] };
    default: return { R: [96 + sw, -292], L: [-96 - sw, -292] };
  }
}
function drawFace(g, st, hx, hy) {
  const K = '#101018'; const ex = 14, e = st.expr; g.strokeStyle = K; g.fillStyle = K;
  const eyes = [[hx - 40 + ex, hy - 6], [hx + 40 + ex, hy - 6]];
  const blink = st.blink || 0;
  const look = st.look || [0, 0];
  if (e === 'shock' || e === 'panic') {
    const R = e === 'shock' ? 32 : 28; const jit = e === 'panic' ? Math.sin(st.a * 47) * 3 : 0;
    for (const [x, y] of eyes) { g.beginPath(); g.arc(x, y, R, 0, TAU); g.fillStyle = '#fff'; g.fill(); g.lineWidth = 7; g.stroke(); g.fillStyle = K; g.beginPath(); g.arc(x + look[0] * 8 + jit, y + look[1] * 8, e === 'shock' ? 7 : 8, 0, TAU); g.fill(); }
    g.lineWidth = 8; if (e === 'shock') { for (const [x, y] of eyes) { g.beginPath(); g.arc(x, y - 30, 30, -2.4, -0.7); g.stroke(); } g.beginPath(); g.ellipse(hx + ex, hy + 66, 14, 18, 0, 0, TAU); g.fillStyle = K; g.fill(); }
    else { g.beginPath(); g.moveTo(eyes[0][0] - 26, eyes[0][1] - 34); g.lineTo(eyes[0][0] + 18, eyes[0][1] - 48); g.moveTo(eyes[1][0] + 26, eyes[1][1] - 34); g.lineTo(eyes[1][0] - 18, eyes[1][1] - 48); g.stroke();
      g.beginPath(); g.moveTo(hx + ex - 40, hy + 52); for (let i = 0; i <= 8; i++) g.lineTo(hx + ex - 40 + i * 10, hy + 52 + (i % 2 ? -6 : 6) + Math.sin(st.a * 40) * 2); g.lineTo(hx + ex + 34, hy + 86); g.quadraticCurveTo(hx + ex, hy + 100, hx + ex - 34, hy + 86); g.closePath(); g.fillStyle = K; g.fill();
      g.fillStyle = '#7fd0ff'; g.strokeStyle = K; g.lineWidth = 4; for (const [x, y, s] of [[hx + 118, hy - 40, 1], [hx - 104, hy - 10, 0.8]]) { g.beginPath(); g.moveTo(x, y - 22 * s); g.quadraticCurveTo(x + 14 * s, y, x, y + 10 * s); g.quadraticCurveTo(x - 14 * s, y, x, y - 22 * s); g.fill(); g.stroke(); } }
    return;
  }
  // dot eyes
  for (const [x, y] of eyes) { g.save(); g.translate(x + look[0] * 6, y + look[1] * 6); g.scale(1, Math.max(0.12, 1 - blink)); g.beginPath(); g.ellipse(0, 0, 12, 18, 0, 0, TAU); g.fillStyle = K; g.fill(); g.fillStyle = '#fff'; g.beginPath(); g.arc(-3, -7, 4, 0, TAU); g.fill(); g.restore(); }
  g.lineWidth = 7; g.strokeStyle = K;
  if (e === 'smirk') {
    for (const [x, y] of eyes) { g.fillStyle = '#ffffff'; g.fillRect(x - 16, y - 24, 32, 20); g.beginPath(); g.moveTo(x - 17, y - 4); g.lineTo(x + 17, y - 6); g.stroke(); }
    g.beginPath(); g.moveTo(eyes[1][0] - 20, eyes[1][1] - 44); g.quadraticCurveTo(eyes[1][0], eyes[1][1] - 62, eyes[1][0] + 22, eyes[1][1] - 48); g.stroke();
    g.beginPath(); g.moveTo(eyes[0][0] - 18, eyes[0][1] - 34); g.lineTo(eyes[0][0] + 18, eyes[0][1] - 32); g.stroke();
    g.beginPath(); g.moveTo(hx + ex - 26, hy + 62); g.quadraticCurveTo(hx + ex + 10, hy + 74, hx + ex + 38, hy + 46); g.stroke();
  } else if (e === 'happy') {
    for (const [x, y] of eyes) { g.fillStyle = '#ffffff'; g.fillRect(x - 16, y - 22, 32, 44); g.beginPath(); g.arc(x, y + 4, 14, Math.PI * 1.1, Math.PI * 1.9); g.lineWidth = 7; g.stroke(); }
    g.beginPath(); g.moveTo(hx + ex - 26, hy + 50); g.quadraticCurveTo(hx + ex, hy + 92, hx + ex + 26, hy + 50); g.closePath(); g.fillStyle = K; g.fill(); g.fillStyle = '#ff7a8a'; g.beginPath(); g.arc(hx + ex, hy + 70, 9, 0, Math.PI); g.fill();
  } else if (e === 'angry') {
    g.lineWidth = 9; g.beginPath(); g.moveTo(eyes[0][0] - 22, eyes[0][1] - 44); g.lineTo(eyes[0][0] + 18, eyes[0][1] - 26); g.moveTo(eyes[1][0] + 22, eyes[1][1] - 44); g.lineTo(eyes[1][0] - 18, eyes[1][1] - 26); g.stroke();
    g.fillStyle = '#fff'; g.lineWidth = 6; g.beginPath(); g.roundRect(hx + ex - 34, hy + 50, 68, 28, 8); g.fill(); g.stroke(); for (let i = 1; i < 4; i++) { g.beginPath(); g.moveTo(hx + ex - 34 + i * 17, hy + 50); g.lineTo(hx + ex - 34 + i * 17, hy + 78); g.stroke(); }
  } else if (e === 'worried') {
    g.beginPath(); g.moveTo(eyes[0][0] - 20, eyes[0][1] - 32); g.lineTo(eyes[0][0] + 16, eyes[0][1] - 44); g.moveTo(eyes[1][0] + 20, eyes[1][1] - 32); g.lineTo(eyes[1][0] - 16, eyes[1][1] - 44); g.stroke();
    g.beginPath(); g.moveTo(hx + ex - 24, hy + 68); g.quadraticCurveTo(hx + ex - 12, hy + 58, hx + ex, hy + 68); g.quadraticCurveTo(hx + ex + 12, hy + 78, hx + ex + 24, hy + 66); g.stroke();
  } else { // neutral
    g.beginPath(); g.moveTo(eyes[0][0] - 16, eyes[0][1] - 38); g.lineTo(eyes[0][0] + 14, eyes[0][1] - 40); g.moveTo(eyes[1][0] - 14, eyes[1][1] - 40); g.lineTo(eyes[1][0] + 16, eyes[1][1] - 38); g.stroke();
    g.beginPath(); g.moveTo(hx + ex - 22, hy + 62); g.quadraticCurveTo(hx + ex, hy + 72, hx + ex + 22, hy + 62); g.stroke();
  }
}
function drawHat(g, o, hx, hy, hr) {
  const K = '#101018'; g.strokeStyle = K; g.lineWidth = 9;
  if (o.hat === 'capotain') { g.fillStyle = '#1a1a22'; g.beginPath(); g.moveTo(-84, hy - 92); g.lineTo(-70, hy - 270); g.quadraticCurveTo(0, hy - 290, 70, hy - 270); g.lineTo(84, hy - 92); g.closePath(); g.fill(); g.stroke(); g.beginPath(); g.ellipse(0, hy - 92, 150, 26, 0, 0, TAU); g.fill(); g.stroke(); g.fillStyle = '#e2b244'; g.fillRect(-80, hy - 140, 160, 22); g.strokeStyle = '#1a1a22'; g.lineWidth = 6; g.fillStyle = '#e2b244'; g.fillRect(-20, hy - 150, 40, 42); g.strokeRect(-10, hy - 140, 20, 22); }
  else if (o.hat === 'cap') { g.fillStyle = o.capCol; g.beginPath(); g.ellipse(0, hy - 88, 118, 52, 0, Math.PI, 0); g.closePath(); g.fill(); g.stroke(); g.beginPath(); g.ellipse(40, hy - 86, 110, 18, 0, 0, TAU); g.fill(); g.stroke(); }
  else if (o.hat === 'bonnet') { g.fillStyle = '#ffffff'; g.beginPath(); g.arc(0, hy - 30, hr + 12, Math.PI * 1.05, Math.PI * 1.95); g.lineTo(150, hy - 10); g.lineTo(hr + 6, hy - 30); g.lineTo(-hr - 6, hy - 30); g.lineTo(-150, hy - 10); g.closePath(); g.fill(); g.stroke(); }
  else if (o.hat === 'beret') { g.fillStyle = o.capCol; g.beginPath(); g.ellipse(-10, hy - 100, 130, 44, -0.12, 0, TAU); g.fill(); g.stroke(); }
}

// ------------------------------------------------------------------ props: flipped coin, coins in hands
function coinMesh(goldC) { const g = new THREE.CylinderGeometry(0.17, 0.17, 0.03, 40); const side = new THREE.MeshPhongMaterial({ color: goldC ? '#e8b040' : '#cfd6e4', specular: '#ffffff', shininess: 80, emissive: goldC ? '#3a2200' : '#101420' }); const face = new THREE.MeshPhongMaterial({ map: goldC ? T.coinG : T.coinS, specular: '#ffffff', shininess: 60, emissive: '#1a1000' }); const m = new THREE.Mesh(g, [side, face, face]); m.castShadow = true; scene.add(m); return m; }
const flipCoin = coinMesh(true);
const handCoins = []; for (let i = 0; i < 6; i++) { const c = coinMesh(i % 2 === 0); c.scale.set(0.75, 1, 0.75); handCoins.push(c); }

// ------------------------------------------------------------------ choreography
const A = (t) => S(t); // animation clock (slow-mo aware)
function path(keys) { // keys: [realTime, x, z]; evaluated on the animation clock
  const ks = keys.map(k => [A(k[0]), k[1], k[2]]);
  const segLen = []; let tot = 0; const cum = [0];
  for (let i = 1; i < ks.length; i++) { const d = Math.hypot(ks[i][1] - ks[i - 1][1], ks[i][2] - ks[i - 1][2]); segLen.push(d); tot += d; cum.push(tot); }
  return (a) => {
    if (a <= ks[0][0]) return { x: ks[0][1], z: ks[0][2], vx: 0, vz: 0, dist: 0, moving: false };
    for (let i = 1; i < ks.length; i++) if (a <= ks[i][0]) { const k = (a - ks[i - 1][0]) / (ks[i][0] - ks[i - 1][0]); const d = segLen[i - 1]; const dt = ks[i][0] - ks[i - 1][0]; return { x: lerp(ks[i - 1][1], ks[i][1], k), z: lerp(ks[i - 1][2], ks[i][2], k), vx: (ks[i][1] - ks[i - 1][1]) / dt, vz: (ks[i][2] - ks[i - 1][2]) / dt, dist: cum[i - 1] + d * k, moving: d > 0.01 }; }
    const l = ks[ks.length - 1]; return { x: l[1], z: l[2], vx: 0, vz: 0, dist: tot, moving: false };
  };
}
const P_off = path([[17.5, 0, -62.2], [23.0, 0, -62.2], [24.1, 0.4, -58.6], [25.9, 6.5, -52.8], [26.8, 11.0, -50.3], [29.0, 11.0, -50.3], [29.7, 15.5, -50.0]]);
const P_clk = path([[18.6, 0.6, -74], [21.2, 0.4, -66.6], [23.2, 0.4, -66.6], [24.4, 0.2, -60.5], [25.9, 5.2, -54.4], [26.9, 9.6, -51.4], [29.0, 9.6, -51.4], [29.9, 14.6, -50.4]]);
const P_por = path([[21.0, -0.6, -68.8], [21.6, -0.6, -66.4], [23.3, -0.6, -66.4], [24.6, -0.3, -61.5], [26.0, 3.6, -56.2], [27.0, 8.0, -52.6], [29.1, 8.0, -52.6], [30.0, 13.8, -51.0]]);
const crowdSeeds = CROWD_COLS.map((_, i) => { const r = rng(300 + i); return { sx: (r() - 0.5) * 3.2, sz: -57.5 - r() * 1.5, tx: (i - 3.5) * 0.95 + (r() - .5) * 0.4, tz: -64.2 - (i % 3) * 1.1 - r() * 0.4, d: r() * 0.25, seed: r() * 10, mx: [-1.2, 1.1, -0.1, 1.4, -1.4][i % 5] + (r() - .5) * 0.3, mz: -79 - (i % 3) * 1.6 - r() }; });

function pop(a, events, amp = 0.16) { let s = 1; for (const e of events) { const d = a - A(e); if (d >= 0 && d < 1.2) s += amp * Math.exp(-d * 7) * Math.cos(d * 26) * (d < 0.03 ? -1 : 1); } return s; }

function charStates(t) {
  const a = A(t); const out = {};
  // CLERK
  if (t < 31.4 || t >= 38.9) {
    let st = { a, pose: 'idle', expr: 'neutral', x: 0.6, z: -74, flip: false };
    if (t < 31.4) {
      if (t < 3.45) { st.pose = 'idle'; st.expr = 'smirk'; }
      else if (t < 6.75) { st.pose = 'flip'; st.expr = 'smirk'; st.flipK = sstep(3.45, 3.7, t) - sstep(3.7, 3.9, t); }
      else if (t < 9.3) { st.pose = t < 7.0 ? 'catch' : 'crossed'; st.expr = t < 8.0 ? 'neutral' : 'smirk'; }
      else if (t < 12.4) { st.pose = 'crossed'; st.expr = t < 10.9 ? 'smirk' : 'happy'; }
      else if (t < 15.6) { st.pose = 'crossed'; st.expr = 'smirk'; }
      else if (t < 18.6) { st.pose = 'idle'; st.expr = t < 17.6 ? 'neutral' : 'worried'; st.look = [0, -1]; }
      const p = P_clk(a);
      if (t >= 18.6) { st.x = p.x; st.z = p.z; if (p.moving) st.walk = p.dist * 5.4; st.expr = t < 21.0 ? 'worried' : 'smirk'; st.pose = t >= 21.0 ? 'carry' : (p.moving ? 'walk' : 'idle'); }
      st.squash = pop(a, [6.75, 8.0, 10.9, 21.0], 0.14);
      st.blink = (t > 7 && t < 9.3 && (a % 3.1) < 0.12) ? 1 : 0;
    } else {
      st.x = 0; st.z = -71;
      if (t < 40.4) { st.pose = 'holdout'; st.expr = 'panic'; }
      else if (t < 42.9) { st.pose = 'holdout'; st.expr = 'shock'; st.look = [0, 1]; }
      else { st.pose = 'idle'; st.expr = 'worried'; st.look = [0, 0.4]; }
      st.squash = pop(a, [39.35, 40.4, 42.9], 0.16);
    }
    out.clerk = st;
  }
  // OFFICIAL
  if (t >= 17.5 && t < 31.4) {
    const p = P_off(a); const st = { a, x: p.x, z: p.z, pose: t < 19.9 ? 'idle' : 'scroll', expr: 'smirk', flip: false };
    if (t >= 23.0) { st.pose = p.moving ? 'walk' : 'idle'; if (p.moving) st.walk = p.dist * 5.4; }
    if (t >= 27.2 && t < 29.0) { st.pose = 'shh'; st.expr = 'smirk'; }
    st.squash = pop(a, [18.4, 19.9, 27.5], 0.15);
    out.official = st;
  }
  // PORTER
  if (t >= 21.0 && t < 31.4) { const p = P_por(a); out.porter = { a, x: p.x, z: p.z, pose: 'carry', expr: 'worried', walk: p.moving ? p.dist * 5.4 : null, flip: false }; }
  // MERCHANTS (happy, 9.3–18.2) then the CROWD (panic run, 39.0–43.2)
  if (t >= 9.3 && t < 18.2) crowdSeeds.slice(0, 5).forEach((c, i) => { out['crowd' + i] = { a, x: c.mx, z: c.mz, pose: (i % 2 ? 'cheer' : 'idle'), expr: 'happy', seed: c.seed, flip: c.mx > 0, squash: pop(a, [10.9 + i * 0.08], 0.12) }; });
  if (t >= 39.0 && t < 43.5) crowdSeeds.forEach((c, i) => {
    const k = sstep(39.0 + c.d, 40.0, t); const x = lerp(c.sx, c.tx, k), z = lerp(c.sz, c.tz, k);
    const poofT = 42.7 + i * 0.07; if (t >= poofT + 0.12) return;
    const st = { a, x, z, pose: k < 1 ? 'walk' : 'fists', run: true, walk: k < 1 ? k * 30 + i : null, expr: t < 40.4 ? 'angry' : 'shock', seed: c.seed, flip: c.tx < 0 };
    st.squash = pop(a, [40.0], 0.2) * (t > poofT ? 1 + (t - poofT) * 6 : 1); st.op = t > poofT ? 1 - (t - poofT) / 0.12 : 1;
    out['crowd' + i] = st;
  });
  return out;
}
const DOOR_OPEN = -1.83;
function doorAngle(t) { if (t < 1.6) return 0; if (t < 49.3) { const k = clamp((t - 1.6) / 1.3, 0, 1); const e = 1 - Math.pow(1 - k, 3); return DOOR_OPEN * e; } const k = clamp((t - 49.3) / 0.7, 0, 1); return DOOR_OPEN * (1 - k * k * k); }
function wheelAngle(t) { return -sstep(0.7, 1.55, t) * Math.PI * 1.5 + sstep(50.0, 50.45, t) * Math.PI * 1.5; }
function stackScale(t) { return lerp(1, 0.22, sstep(21.5, 31.5, t)) * lerp(1, 0.45, sstep(40.4, 42.9, t)); }
const aL = A(3.7), aC = A(6.75); const CF_H = 1.65, CF_G = 8 * CF_H / Math.pow(aC - aL, 2), CF_V = CF_G * (aC - aL) / 2;
function coinPos(t) { const a = clamp(A(t), aL, aC); const d = a - aL; return V(0.88, 1.34 + CF_V * d - 0.5 * CF_G * d * d, -73.7); }
const SHIP_SINK = (t) => sstep(29.5, 31.4, t);

// ------------------------------------------------------------------ camera path (one continuous move)
const KEYS = [];
function K(t, p, look, o = {}) { KEYS.push({ t, p: V(...p), look: V(...look), ...o }); }
const C0P = [0, 2.0, -35], C0L = [0, 6.0, -60];
K(0.0, C0P, C0L, { fov: 52, ap: 3, roll: 0 });
K(0.9, [0, 2.1, -37.2], [0, 5.7, -60], { fov: 52, ap: 3 });
K(1.9, [0, 2.5, -44.5], [0, 5.0, -60], { fov: 53 });
K(2.9, [0.1, 3.2, -53.5], [0.2, 4.0, -63], { fov: 57, roll: -2 });
K(3.45, [0.2, 3.5, -61.8], [0.4, 3.1, -70], { fov: 62, ap: 4, roll: -5 });
K(3.85, [0.5, 3.2, -69.6], [0.85, 2.6, -73.7], { fov: 50, ap: 8, roll: 6 });
for (let t = 4.15; t <= 6.66; t += 0.3) { const c = coinPos(t); const k = (t - 4.15) / 2.5; K(t, [c.x - 0.35 + k * 0.1, c.y + 0.12 - k * 0.05, c.z + 1.05 - k * 0.12], [c.x, c.y, c.z], { fov: 38, ap: 12, roll: lerp(3, -2, k) }); }
K(6.75, [0.62, 1.55, -72.55], [0.88, 1.36, -73.75], { fov: 38, ap: 12 });
K(7.2, [-2.15, 0.38, -78.4], [0.6, 1.5, -74], { fov: 48, ap: 6, roll: 4 });
K(8.3, [-2.25, 0.42, -75.0], [0.6, 1.7, -74.1], { fov: 48, ap: 6, roll: 1 });
K(9.3, [-1.95, 0.46, -71.2], [0.6, 1.8, -74], { fov: 48, ap: 6, roll: -2 });
{ const O = V(0.6, 1.8, -74);
  const orb = (t) => { let ang, r, y, fov; if (t < 9.7) { const k = easeIO((t - 9.3) / 0.4); ang = lerp(-40, 38, k); r = lerp(3.8, 2.7, k); y = lerp(0.46, 1.45, k); fov = lerp(48, 46, k); } else { const k = (t - 9.7) / 2.7; const e = 1 - Math.pow(1 - k, 2); ang = lerp(38, 0, e); r = lerp(2.7, 0.8, e); y = lerp(1.45, 1.8, e); fov = lerp(46, 34, e); } const rad = ang * Math.PI / 180; return { p: [O.x + Math.sin(rad) * r, y, O.z + Math.cos(rad) * r], fov }; };
  for (const t of [9.4, 9.5, 9.6, 9.7, 10.0, 10.4, 10.8, 11.2, 11.6, 12.0, 12.4]) { const q = orb(t); K(t, q.p, [O.x, 1.8, O.z], { fov: q.fov, ap: t < 9.8 ? 7 : 10, roll: t < 9.8 ? -4 : 0 }); } }
K(13.4, [0.75, 2.0, -72.3], [0.6, 1.7, -74.5], { fov: 44, ap: 7 });
K(15.3, [1.3, 2.4, -69.4], [0.3, 1.6, -78.5], { fov: 52, ap: 5, roll: -2 });
K(16.4, [0.8, 6.3, -68.3], [0.6, 2.4, -82], { fov: 56, ap: 4, roll: 0 });
K(17.95, [0.6, 9.6, -67.6], [0.6, 3.0, -90], { fov: 60, ap: 3 });
K(18.15, [0.45, 8.7, -67.3], [6, 6, -66], { fov: 56, ap: 3, roll: 8, yaw: 90 });
K(18.4, [0.3, 6.6, -66.9], [0, 1.9, -62.2], { fov: 46, ap: 6, roll: 2 });
K(18.9, [0.2, 3.4, -65.6], [0, 1.9, -62.2], { fov: 40, ap: 8, roll: 0 });
K(21.0, [0.1, 2.15, -64.3], [0, 1.85, -62.2], { fov: 36, ap: 10 });
K(23.0, [-1.5, 1.3, -65.2], [0.2, 1.5, -61], { fov: 46, ap: 7 });
K(24.0, [-1.3, 0.85, -62.8], [0.8, 1.3, -57], { fov: 52, ap: 7 });
K(24.8, [-0.7, 0.8, -59.6], [3.0, 1.3, -55], { fov: 52, ap: 7 });
K(25.8, [0.6, 0.75, -55.8], [5.5, 1.4, -52.8], { fov: 50, ap: 7, roll: -2 });
K(26.8, [5.0, 0.8, -53.0], [11, 1.5, -50.3], { fov: 52, ap: 6, roll: 0 });
K(27.5, [9.2, 1.75, -48.8], [11.0, 1.85, -50.3], { fov: 44, ap: 10, roll: -3 });
K(29.2, [9.05, 1.7, -49.1], [11.0, 1.85, -50.3], { fov: 41, ap: 10, roll: 0 });
K(30.1, [8.4, 1.0, -50.0], [20, 1.8, -49.5], { fov: 50, ap: 4 });
K(31.2, [9.4, 1.0, -50.0], [20, 1.2, -49.5], { fov: 45, ap: 4 });
K(31.6, [6.0, 2.0, -52.6], [0, 3.4, -62], { fov: 58, ap: 3, roll: -6 });
K(32.0, [1.2, 3.3, -58.8], [-3, 3.3, -72], { fov: 62, ap: 3, roll: -4 });
K(32.45, [-5.0, 3.45, -71.5], [-14, 2.8, -80], { fov: 58, ap: 4, roll: 3 });
K(33.0, [-13.0, 3.05, -80.0], [-15.2, 3.05, -80.2], { fov: 44, ap: 10, roll: 0 });
K(34.4, [-11.6, 3.1, -80.1], [-15.2, 2.95, -80.2], { fov: 46, ap: 8 });
K(36.8, [-8.0, 3.3, -81.4], [-15.3, 2.6, -78.2], { fov: 54, ap: 5, roll: 2 });
K(38.85, [-5.0, 3.4, -80.9], [-15.3, 2.5, -79.2], { fov: 58, ap: 4, roll: 0 });
K(39.12, [-4.2, 3.0, -81.2], [-6, 3.0, -70], { fov: 56, ap: 3, roll: 6, yaw: -10 });
K(39.35, [-3.6, 2.5, -81.5], [0, 2.6, -62], { fov: 52, ap: 4, roll: 3 });
K(39.8, [-2.6, 2.0, -78.0], [0, 1.8, -66], { fov: 50, ap: 5, roll: -4 });
K(40.1, [-0.9, 1.45, -74.6], [0, 1.3, -71], { fov: 44, ap: 7, roll: -2 });
K(40.45, [-0.1, 1.28, -72.55], [0, 1.2, -71.1], { fov: 38, ap: 12, roll: 0 });
K(42.6, [0.12, 1.36, -72.25], [0, 1.25, -71.1], { fov: 36, ap: 12 });
K(43.5, [0, 2.0, -76.0], [0, 2.0, -66], { fov: 46, ap: 6 });
K(45.0, [0, 3.2, -85.5], [0, 3.0, -62], { fov: 56, ap: 3 });
K(47.0, [0, 3.4, -88.5], [0, 3.0, -62], { fov: 58, ap: 3 });
K(47.6, [0, 3.9, -80.0], [0, 3.9, -50], { fov: 60, ap: 2 });
K(48.7, [0, 4.2, -62.5], [0, 4.2, -40], { fov: 62, ap: 2 });
K(48.95, [0.1, 4.25, -57.4], [10, 4.4, -57.4], { fov: 62, ap: 2, roll: 7, yaw: 90 });
K(49.4, [0, 3.9, -53.2], [0, 4.6, -60], { fov: 56, ap: 2, roll: 2 });
K(49.9, [0, 2.8, -41.5], [0, 5.6, -60], { fov: 52, ap: 3, roll: 0 });
K(50.4, [0, 2.04, -35.3], C0L, { fov: 52, ap: 3 });
K(51.0, C0P, C0L, { fov: 52, ap: 3, roll: 0 });

// channels: x y z yaw pitch roll fov ap focus ; monotone cubic (Fritsch–Carlson) — no overshoot, C1
KEYS.sort((a, b) => a.t - b.t);
let prevYaw = null; let last = {};
for (const k of KEYS) { const d = k.look.clone().sub(k.p); k.focus = d.length(); d.normalize(); let yaw = k.yaw !== undefined ? k.yaw * Math.PI / 180 : Math.atan2(d.x, d.z); if (k.yaw !== undefined) { /* explicit world yaw */ } if (prevYaw !== null) { while (yaw - prevYaw > Math.PI) yaw -= TAU; while (yaw - prevYaw < -Math.PI) yaw += TAU; } k.yawR = yaw; prevYaw = yaw; k.pitchR = Math.asin(clamp(d.y, -1, 1)); for (const c of ['fov', 'ap', 'roll']) { if (k[c] === undefined) k[c] = last[c]; last[c] = k[c]; } }
const CH_KEYS = ['x', 'y', 'z', 'yawR', 'pitchR', 'roll', 'fov', 'ap', 'focus'];
const chan = {}; for (const c of CH_KEYS) { const ys = KEYS.map(k => c === 'x' ? k.p.x : c === 'y' ? k.p.y : c === 'z' ? k.p.z : k[c]); chan[c] = monotone(KEYS.map(k => k.t), ys); }
function monotone(xs, ys) {
  const n = xs.length, d = [], m = new Array(n).fill(0);
  for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]));
  for (let i = 1; i < n - 1; i++) { if (d[i - 1] * d[i] <= 0) m[i] = 0; else { const w1 = 2 * (xs[i + 1] - xs[i]) + (xs[i] - xs[i - 1]), w2 = (xs[i + 1] - xs[i]) + 2 * (xs[i] - xs[i - 1]); m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]); } }
  m[0] = 0; m[n - 1] = 0; // start + end at rest (loop)
  return (x) => { if (x <= xs[0]) return ys[0]; if (x >= xs[n - 1]) return ys[n - 1]; let i = 0; while (x > xs[i + 1]) i++; const h = xs[i + 1] - xs[i], s = (x - xs[i]) / h; const h00 = 2 * s ** 3 - 3 * s ** 2 + 1, h10 = s ** 3 - 2 * s ** 2 + s, h01 = -2 * s ** 3 + 3 * s ** 2, h11 = s ** 3 - s ** 2; return h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]; };
}
function camAt(t) {
  const c = {}; for (const k of CH_KEYS) c[k] = chan[k](t);
  const sh = 0.6 + 0.4 * Math.abs(pnoise(t, 5, 3, 9));
  const p = V(c.x + pnoise(t, 11) * 0.012 * sh, c.y + pnoise(t, 12) * 0.012 * sh, c.z + pnoise(t, 13) * 0.01 * sh);
  const yaw = c.yawR + pnoise(t, 14, 15, 50) * 0.0035, pitch = c.pitchR + pnoise(t, 15, 15, 50) * 0.003;
  const dir = V(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
  return { p, dir, roll: (c.roll || 0) * Math.PI / 180, fov: c.fov, ap: c.ap, focus: c.focus };
}
function applyCam(cs) { camera.position.copy(cs.p); camera.up.set(0, 1, 0); camera.lookAt(cs.p.clone().add(cs.dir)); camera.rotateZ(cs.roll); camera.fov = cs.fov; camera.updateProjectionMatrix(); camera.updateMatrixWorld(); }

// ------------------------------------------------------------------ world update for time t
const tmpM = new THREE.Matrix4(), tmpQ = new THREE.Quaternion(), tmpS = new THREE.Vector3(), tmpE = new THREE.Euler();
const crowdEmit = [];
function updateWorld(t, cs) {
  const a = A(t);
  { const k = SHIP_SINK(t); ship.position.y = -0.35 - k * 2.2; ship.rotation.z = k * 0.45; ship.rotation.x = Math.sin(t * TAU * 6 / DUR) * 0.02 + k * 0.12; }
  doorPivot.rotation.y = doorAngle(t); wheel.rotation.z = wheelAngle(t);
  for (const m of shaftMats) m.uniforms.uT.value = TAU * 3 * t / DUR * 10;
  candles.forEach((c, i) => { const f = 1 + 0.18 * pnoise(t, 50 + i, 60, 140); c.scale.set(f, 1.8 * f, f); });
  hallLamp.intensity = 60 * (1 + 0.06 * pnoise(t, 3, 60, 140));
  // stacks shrink as the bank lends; last stack crumbles in the 1790 run
  const sc = stackScale(t); for (const s of stacks) { const h = Math.max(0.03, s.h * sc); s.m.scale.y = h; s.tex.repeat.set(3, h / 0.09); }
  // shelves emptied
  bars.forEach((b, i) => { const on = t < b.rm; tmpQ.setFromEuler(tmpE.set(0, b.ry, 0)); tmpS.setScalar(on ? 1 : 0); tmpM.compose(b.p, tmpQ, tmpS); barIM.setMatrixAt(i, tmpM); }); barIM.instanceMatrix.needsUpdate = true;
  bags.forEach((b, i) => { const on = t < b.rm; tmpQ.setFromEuler(tmpE.set(0, b.ry, 0)); tmpS.setScalar(on ? 1 : 0); tmpM.compose(b.p, tmpQ, tmpS); bagIM.setMatrixAt(i, tmpM); }); bagIM.instanceMatrix.needsUpdate = true;
  // flipped coin
  flipCoin.visible = t >= 3.7 && t < 6.75; if (flipCoin.visible) { flipCoin.position.copy(coinPos(t)); flipCoin.rotation.set(A(t) * 17, 0.3, 0.2); }
  
  // characters
  const states = charStates(t);
  const camRight = V(1, 0, 0).applyQuaternion(camera.quaternion);
  const sunScreen = V().copy(SUN).negate().applyQuaternion(camera.quaternion.clone().invert());
  for (const [n, C] of Object.entries(chars)) {
    const st = states[n]; if (!st) { C.hide(); continue; }
    C.mesh.visible = true; C.sh.visible = true;
    // facing: walk direction projected on screen
    if (st.walk !== undefined && st.walk !== null) { const p = n === 'official' ? P_off(a) : n === 'clerk' ? P_clk(a) : n === 'porter' ? P_por(a) : null; if (p && (p.vx || p.vz)) st.flip = (p.vx * camRight.x + p.vz * camRight.z) < 0; }
    if (n === 'official' && st.pose === 'shh') st.flip = false;
    drawChar(C, st);
    C.mesh.position.set(st.x, 0, st.z);
    // billboard: face the camera (yaw fully, pitch partially so it stays planted)
    const to = camera.position.clone().sub(C.mesh.position); const yaw = Math.atan2(to.x, to.z); const pitch = Math.atan2(to.y - 1.4, Math.hypot(to.x, to.z));
    C.mesh.rotation.set(0, 0, 0); C.mesh.rotation.order = 'YXZ'; C.mesh.rotation.y = yaw; C.mesh.rotation.x = -clamp(pitch, -1.2, 1.2) * 0.35;
    C.mat.uniforms.uOp.value = st.op ?? 1;
    // rim light direction in sprite space from the key light
    const inVault = st.z < -61.4, outside = st.x > 12.3;
    let lightScr = inVault ? V(-6, 16, -78).sub(C.mesh.position).applyQuaternion(camera.quaternion.clone().invert()) : sunScreen.clone();
    if (outside) lightScr = V(1, 0.4, 0);
    const rd = new THREE.Vector2(lightScr.x, lightScr.y); if (rd.lengthSq() < 1e-6) rd.set(1, 0); rd.normalize(); if (st.flip) rd.x *= -1;
    C.mat.uniforms.uRim.value.copy(rd);
    C.mat.uniforms.uRimC.value.set(outside ? '#7fa0ff' : '#ffcf73');
    C.mat.uniforms.uTint.value.setRGB(...(outside ? [0.62, 0.7, 0.95] : inVault ? [0.93, 0.88, 0.8] : [0.98, 0.93, 0.85]));
    const s = (st.squash || 1); C.sh.position.set(st.x, 0.015, st.z); C.sh.scale.set(1.5 / Math.sqrt(s), 1, 0.65); C.sh.material.opacity = 0.62 * (st.op ?? 1);
  }
  // coins in the clerk's hands (crumble to dust 33.2–35.4)
  const cl = states.clerk; const showHC = cl && t >= 38.9 && t < 42.9;
  handCoins.forEach((c, i) => {
    if (!showHC) { c.visible = false; return; }
    const k0 = A(40.4) + (5 - i) * (A(42.4) - A(40.4)) / 6; const dk = A(t) - k0; const life = dk < 0 ? 1 : Math.max(0, 1 - dk / 0.35);
    c.visible = life > 0.01; const base = V(cl.x, 0, cl.z); const to = camera.position.clone().sub(base).setY(0).normalize();
    c.position.copy(base).addScaledVector(to, 0.22).add(V(0, 1.2 + i * 0.03 + (dk > 0 ? dk * 0.1 : 0), 0)); c.rotation.set(0.12, i * 0.7, Math.sin(i) * 0.08); c.scale.set(0.75 * life, life, 0.75 * life);
  });
  // particles
  let n = 0;
  const put = (x, y, z, r, g, b, al, s) => { if (n >= MAXP) return; pPos[n * 3] = x; pPos[n * 3 + 1] = y; pPos[n * 3 + 2] = z; pCol[n * 4] = r; pCol[n * 4 + 1] = g; pCol[n * 4 + 2] = b; pCol[n * 4 + 3] = al; pSize[n] = s; n++; };
  for (const m of motes) { const x = m.b.x + 0.6 * Math.sin(TAU * m.k[0] * t / DUR + m.ph[0]), y = m.b.y + 0.5 * Math.sin(TAU * m.k[1] * t / DUR + m.ph[1]), z = m.b.z + 0.6 * Math.sin(TAU * m.k[2] * t / DUR + m.ph[2]); const tw = 0.5 + 0.5 * Math.sin(TAU * (m.k[0] + 3) * t / DUR + m.ph[2]); put(x, y, z, 1.0, 0.8, 0.45, 0.35 + 0.4 * tw, m.s); }
  // coin dust
  if (cl && t >= 40.4 && t < 44.5) { const r = rng(777); for (let i = 0; i < 6; i++) { const k0 = A(40.4) + (5 - i) * (A(42.4) - A(40.4)) / 6; const dk = A(t) - k0; if (dk < 0) continue; const base = handCoins[i].position.clone(); for (let j = 0; j < 220; j++) { const rv = V(r() - .5, r() * 0.9 + 0.1, r() - .5); const born = r() * 0.3; const age = dk - born; if (age < 0 || age > 2.4) continue; const al = Math.min(1, age * 8) * (1 - age / 2.4); put(base.x + rv.x * age * 0.9, base.y + rv.y * age * 0.55 - 0.08 * age * age, base.z + rv.z * age * 0.9, 1.0, 0.72 + r() * 0.2, 0.25, al * 0.9, 0.012 + r() * 0.018); } } }
  // crowd poof
  if (t >= 42.7 && t < 44.1) crowdSeeds.forEach((c, i) => { const p0 = 42.7 + i * 0.07; const age = A(t) - A(p0); if (age < 0 || age > 1.0) return; const r = rng(900 + i); for (let j = 0; j < 120; j++) { const th = r() * TAU, ph = r() * Math.PI, sp = 0.8 + r() * 1.6; const al = (1 - age) * Math.min(1, age * 10); put(c.tx + Math.cos(th) * Math.sin(ph) * sp * age, 1.2 + Math.cos(ph) * sp * age * 0.8 + r() * 0.8, c.tz + Math.sin(th) * Math.sin(ph) * sp * age, 1.0, 0.78, 0.35, al, 0.03 + r() * 0.04); } });
  // door dust puff when it swings open
  if (t > 1.6 && t < 3.55) { const age = t - 1.6; const r = rng(55); for (let j = 0; j < 160; j++) { const x = (r() - .5) * 9, y = r() * 0.4, z = -59 + r() * 2; const al = (1 - age / 1.95) * 0.5; put(x + (r() - .5) * age, y + age * 0.5 * r(), z + age * 1.2 * r(), 0.9, 0.8, 0.6, al, 0.05 + r() * 0.05); } }
  for (let i = n; i < MAXP; i++) pCol[i * 4 + 3] = 0, pPos[i * 3 + 1] = -999;
  pGeo.attributes.position.needsUpdate = true; pGeo.attributes.color.needsUpdate = true; pGeo.attributes.size.needsUpdate = true; pGeo.setDrawRange(0, Math.max(1, n));
}

// ------------------------------------------------------------------ post: DOF (per sub-frame), accumulate (motion blur), bloom, grade, captions
const dofNearMat = new THREE.ShaderMaterial({ vertexShader: VS_Q, uniforms: { tDepth: { value: sceneRT.depthTexture }, uRes: { value: new THREE.Vector2(W, H) }, uN: { value: 0.05 }, uF: { value: 400 }, uFocus: { value: 5 }, uAp: { value: 5 }, uMax: { value: 40 } },
  fragmentShader: `uniform sampler2D tDepth; uniform vec2 uRes; uniform float uN, uF, uFocus, uAp, uMax; varying vec2 vUv;
  float lz(float d){ float z = d*2.-1.; return 2.*uN*uF/(uF+uN-z*(uF-uN)); }
  void main(){ float m = 0.; for(int j=0;j<4;j++) for(int i=0;i<4;i++){ vec2 uv = vUv + (vec2(float(i),float(j))-1.5)/uRes*1.0*4./4.; float z = lz(texture2D(tDepth, uv).r); float c = uAp*(z-uFocus)/z; m = max(m, clamp(-c,0.,uMax)); } gl_FragColor = vec4(m,0.,0.,1.); }` });
const dofDilateMat = new THREE.ShaderMaterial({ vertexShader: VS_Q, uniforms: { tIn: { value: null }, uTex: { value: new THREE.Vector2(4 / W, 4 / H) } },
  fragmentShader: `uniform sampler2D tIn; uniform vec2 uTex; varying vec2 vUv; void main(){ float m = 0.; for(int j=-4;j<=4;j++) for(int i=-4;i<=4;i++){ vec2 o = vec2(float(i),float(j)); float c = texture2D(tIn, vUv + o*uTex*1.5).r; float d = length(o)*1.5*4.; if (d <= c + 4.) m = max(m, c); } gl_FragColor = vec4(m,0.,0.,1.); }` });
const dofMat = new THREE.ShaderMaterial({ vertexShader: VS_Q, transparent: true, blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor, blendEquation: THREE.AddEquation, depthTest: false, depthWrite: false,
  uniforms: { tColor: { value: sceneRT.texture }, tDepth: { value: sceneRT.depthTexture }, tNear: { value: nearRT2.texture }, uRes: { value: new THREE.Vector2(W, H) }, uN: { value: 0.05 }, uF: { value: 400 }, uFocus: { value: 5 }, uAp: { value: 5 }, uMax: { value: 40 }, uW: { value: 1 } },
  fragmentShader: `uniform sampler2D tColor, tDepth, tNear; uniform vec2 uRes; uniform float uN, uF, uFocus, uAp, uMax, uW; varying vec2 vUv;
  float lz(float d){ float z = d*2.-1.; return 2.*uN*uF/(uF+uN-z*(uF-uN)); }
  float coc(float z){ return clamp(uAp*(z-uFocus)/z, -uMax, uMax); }
  void main(){
    float zc = lz(texture2D(tDepth, vUv).r); float cc = coc(zc); float R = max(abs(cc), texture2D(tNear, vUv).r);
    vec3 c0 = texture2D(tColor, vUv).rgb;
    if (R < 0.7) { gl_FragColor = vec4(c0*uW, 1.); return; }
    vec3 acc = c0; float ws = 1.;
    const int NT = 40;
    for (int i = 0; i < NT; i++) { float fi = float(i)+0.5; float r = sqrt(fi/float(NT)); float th = fi*2.39996323; vec2 o = vec2(cos(th), sin(th))*r*R; vec2 uv = vUv + o/uRes;
      vec3 c = texture2D(tColor, uv).rgb; float zs = lz(texture2D(tDepth, uv).r); float cs = coc(zs); float d = r*R;
      float cov = zs < zc ? abs(cs) : (cc < 0. ? abs(cc) : min(abs(cs), abs(cc)));
      float w = clamp(cov - d + 1.0, 0., 1.); acc += c*w; ws += w; }
    gl_FragColor = vec4(acc/ws*uW, 1.); }` });
const brightMat = new THREE.ShaderMaterial({ vertexShader: VS_Q, uniforms: { tIn: { value: accRT.texture }, uTex: { value: new THREE.Vector2(1 / W, 1 / H) } }, fragmentShader: `uniform sampler2D tIn; uniform vec2 uTex; varying vec2 vUv; void main(){ vec3 s = vec3(0.); for(int j=-1;j<=1;j++) for(int i=-1;i<=1;i++) s += texture2D(tIn, vUv + vec2(float(i),float(j))*uTex*1.5).rgb; s/=9.; float l = dot(s, vec3(0.3,0.59,0.11)); gl_FragColor = vec4(s*smoothstep(0.85,1.8,l), 1.); }` });
const blurMat = new THREE.ShaderMaterial({ vertexShader: VS_Q, uniforms: { tIn: { value: null }, uDir: { value: new THREE.Vector2() } }, fragmentShader: `uniform sampler2D tIn; uniform vec2 uDir; varying vec2 vUv; void main(){ vec3 s = vec3(0.); float ws = 0.; for(int i=-8;i<=8;i++){ float w = exp(-float(i*i)/24.); s += texture2D(tIn, vUv + uDir*float(i)).rgb*w; ws += w; } gl_FragColor = vec4(s/ws,1.); }` });
const capCanvas = document.createElement('canvas'); capCanvas.width = W; capCanvas.height = H; const capG = capCanvas.getContext('2d');
const capTex = new THREE.CanvasTexture(capCanvas); capTex.colorSpace = THREE.NoColorSpace; capTex.flipY = true;
const finalMat = new THREE.ShaderMaterial({ vertexShader: VS_Q, uniforms: { tIn: { value: accRT.texture }, tBloom: { value: bloomA.texture }, tCap: { value: capTex }, uT: { value: 0 }, uExp: { value: 1 }, uRes: { value: new THREE.Vector2(W, H) } },
  fragmentShader: `uniform sampler2D tIn, tBloom, tCap; uniform float uT, uExp; uniform vec2 uRes; varying vec2 vUv;
  vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.,1.); }
  float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)))*43758.5453); }
  void main(){ vec2 d = (vUv-0.5);
    vec3 c = vec3(texture2D(tIn, vUv - d*0.0025).r, texture2D(tIn, vUv).g, texture2D(tIn, vUv + d*0.0025).b);
    c += texture2D(tBloom, vUv).rgb*0.75;
    c *= uExp*1.25; c = aces(c);
    float l = dot(c, vec3(0.299,0.587,0.114)); c = mix(vec3(l), c, 1.32); c = mix(c, smoothstep(0.,1.,c), 0.35);
    c = mix(c, c*vec3(0.86,0.95,1.18), (1.-smoothstep(0.,0.45,l))*0.45); c = mix(c, c*vec3(1.08,1.0,0.86), smoothstep(0.5,1.,l)*0.35);
    float v = smoothstep(0.95, 0.25, length(d*vec2(1.0,0.82))); c *= mix(0.62, 1.0, v);
    c = pow(c, vec3(1./2.2));
    c += (h(vUv*uRes + fract(uT)*91.7) - 0.5)*0.028;
    vec4 cap = texture2D(tCap, vUv); c = mix(c, cap.rgb, cap.a);
    gl_FragColor = vec4(c, 1.); }` });

// captions: 1–3 word pop-in chunks
const GOLDW = /^(1609|perfect|ideal|silver|vault|secret|lending|lent|'79|1819|trust|nothing|money|coin|panic|company|tempting)/i;
const CAPS = (() => { const ws = TL.words; const out = []; let cur = [];
  ws.forEach((w, i) => { cur.push(w); const nxt = ws[i + 1]; const brk = cur.length >= 3 || /[.,?!:]$/.test(w[0]) || (cur.length >= 2 && w[0].length > 7) || !nxt || (nxt && nxt[1] - w[1] > 0.8);
    if (brk) { const t0 = cur[0][1] - 0.04; const t1 = nxt ? Math.min(nxt[1] - 0.04, w[1] + 0.9) : w[1] + 0.7; out.push({ t0, t1, words: cur.map(x => x[0]) }); cur = []; } });
  return out; })();
function drawCaption(t) {
  capG.clearRect(0, 0, W, H); const ch = CAPS.find(c => t >= c.t0 && t < c.t1); if (!ch) { capTex.needsUpdate = true; return; }
  const k = clamp((t - ch.t0) / 0.09, 0, 1); const sc = lerp(1.28, 1, 1 - Math.pow(1 - k, 3)) * (k < 1 ? 1 : 1);
  capG.save(); capG.translate(W / 2, H * 0.655); capG.scale(sc, sc); const fs = Math.round(64 * RS); capG.font = `900 ${fs}px Inter`; capG.textAlign = 'center'; capG.textBaseline = 'middle'; capG.lineJoin = 'round';
  const txt = ch.words.join(' ').toUpperCase(); let total = capG.measureText(txt).width; let sc2 = Math.min(1, (W * 0.86) / total); capG.scale(sc2, sc2);
  let x = -total / 2; for (const w of ch.words) { const ww = capG.measureText(w.toUpperCase() + ' ').width; const cx = x + capG.measureText(w.toUpperCase()).width / 2; capG.lineWidth = 14 * RS; capG.strokeStyle = '#0b0b14'; capG.shadowColor = 'rgba(0,0,0,0.5)'; capG.shadowBlur = 10 * RS; capG.shadowOffsetY = 6 * RS; capG.strokeText(w.toUpperCase(), cx, 0); capG.shadowColor = 'transparent'; capG.fillStyle = GOLDW.test(w) ? '#ffd23f' : '#ffffff'; capG.fillText(w.toUpperCase(), cx, 0); x += ww; }
  capG.restore(); capTex.needsUpdate = true;
}

// ------------------------------------------------------------------ frame render
function motionPx(t0, t1) { const a = camAt(t0), b = camAt(t1); const ang = Math.acos(clamp(a.dir.dot(b.dir), -1, 1)) + Math.abs(a.roll - b.roll) * 0.4; const tr = a.p.distanceTo(b.p) / Math.max(0.8, Math.min(a.focus, 6)); return (ang + tr) * H / (a.fov * Math.PI / 180); }
const SHUTTER = 0.5 / FPS;
function renderAt(t, frozen) {
  let n = 1; if (!frozen) { const mp = motionPx(clamp(t - SHUTTER / 2, 0, DUR), clamp(t + SHUTTER / 2, 0, DUR)); n = clamp(Math.ceil(mp / (4 * RS)), 1, 14); }
  renderer.setRenderTarget(accRT); renderer.setClearColor(0x000000, 1); renderer.clear();
  for (let i = 0; i < n; i++) {
    const ts = n === 1 ? t : clamp(t + (i / (n - 1) - 0.5) * SHUTTER, 0, DUR);
    const cs = camAt(ts); applyCam(cs); updateWorld(ts, cs); if (i === 0) drawCaption(t);
    renderer.setRenderTarget(sceneRT); renderer.setClearColor(FOG, 1); renderer.clear(); renderer.render(scene, camera);
    const ap = cs.ap * RS * 1.0, mx = 34 * RS;
    for (const m of [dofNearMat, dofMat]) { m.uniforms.uFocus.value = cs.focus; m.uniforms.uAp.value = ap; m.uniforms.uMax.value = mx; m.uniforms.uN.value = camera.near; m.uniforms.uF.value = camera.far; }
    pass(dofNearMat, nearRT); dofDilateMat.uniforms.tIn.value = nearRT.texture; pass(dofDilateMat, nearRT2);
    dofMat.uniforms.uW.value = 1 / n; pass(dofMat, accRT, false);
  }
  pass(brightMat, bloomA); blurMat.uniforms.tIn.value = bloomA.texture; blurMat.uniforms.uDir.value.set(1.6 / bloomA.width, 0); pass(blurMat, bloomB); blurMat.uniforms.tIn.value = bloomB.texture; blurMat.uniforms.uDir.value.set(0, 1.6 / bloomA.height); pass(blurMat, bloomA);
  finalMat.uniforms.uT.value = (t % DUR); pass(finalMat, outRT);
  return n;
}
const pix = new Uint8Array(W * H * 4);
function b64(u8) { let s = ''; const CHK = 0x8000; for (let i = 0; i < u8.length; i += CHK) s += String.fromCharCode.apply(null, u8.subarray(i, i + CHK)); return btoa(s); }
window.renderFrame = (f) => { const t = frameTime(f); const frozen = f / FPS !== t || f === 0 || f === Math.round(DUR * FPS); const n = renderAt(t, frozen); renderer.readRenderTargetPixels(outRT, 0, 0, W, H, pix); return { n, data: b64(pix) }; };
window.renderTime = (t) => { renderAt(t, false); renderer.readRenderTargetPixels(outRT, 0, 0, W, H, pix); return b64(pix); };
window.camTrack = () => { const out = []; for (let f = 0; f <= DUR * FPS; f++) { const t = frameTime(f); const c = camAt(t); out.push([t, c.p.x, c.p.y, c.p.z, Math.atan2(c.dir.x, c.dir.z), Math.asin(c.dir.y), c.fov]); } return out; };
window.READY = true;
