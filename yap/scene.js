// "The Island That Paid With Stones" (Yap rai stones) — 2D billboard characters inside a stylized 3D tropical world.
// Stateless: every frame is a pure function of time, so frames can be rendered in parallel workers.
import * as THREE from '../banks/node_modules/three/build/three.module.js';

const TL = await (await fetch('./timeline.json')).json();
await Promise.all(['900 20px Inter', 'bold 20px "DejaVu Serif"'].map(f => document.fonts.load(f)));
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
renderer.toneMapping = THREE.NoToneMapping; renderer.autoClear = false;
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
T.radial = ctex(128, 128, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, w); }, { srgb: false });

// ------------------------------------------------------------------ textures (island)
T.sand = ctex(512, 512, (g, w) => { g.fillStyle = '#f2d59a'; g.fillRect(0, 0, w, w); for (let i = 0; i < 9000; i++) { const v = R0(); g.fillStyle = v < 0.5 ? 'rgba(180,140,80,0.18)' : 'rgba(255,250,230,0.25)'; g.fillRect(R0() * w, R0() * w, 2, 2); } for (let i = 0; i < 30; i++) { g.strokeStyle = 'rgba(200,160,100,0.18)'; g.lineWidth = 3; g.beginPath(); const y = R0() * w; g.moveTo(0, y); g.bezierCurveTo(150, y + 20, 350, y - 20, w, y + 5); g.stroke(); } }, { rep: [40, 40] });
T.grass = ctex(512, 512, (g, w) => { g.fillStyle = '#4fb63a'; g.fillRect(0, 0, w, w); for (let i = 0; i < 5000; i++) { g.fillStyle = R0() < 0.5 ? 'rgba(30,110,30,0.35)' : 'rgba(170,230,90,0.3)'; const x = R0() * w, y = R0() * w; g.fillRect(x, y, 2, 6); } }, { rep: [30, 30] });
T.seabed = ctex(512, 512, (g, w) => { g.fillStyle = '#d8c48e'; g.fillRect(0, 0, w, w); for (let i = 0; i < 7000; i++) { g.fillStyle = R0() < 0.5 ? 'rgba(120,100,60,0.2)' : 'rgba(255,255,230,0.2)'; g.fillRect(R0() * w, R0() * w, 3, 3); } for (let i = 0; i < 40; i++) { g.strokeStyle = 'rgba(150,120,70,0.25)'; g.lineWidth = 6; g.beginPath(); const y = R0() * w; g.moveTo(0, y); for (let x = 0; x <= w; x += 32) g.lineTo(x, y + Math.sin(x * 0.05 + i) * 8); g.stroke(); } }, { rep: [120, 120] });
T.caustic = ctex(256, 256, (g, w) => { g.fillStyle = '#000'; g.fillRect(0, 0, w, w); g.strokeStyle = 'rgba(255,255,255,0.9)'; const r = rng(3); for (let i = 0; i < 46; i++) { g.lineWidth = 1.5 + r() * 3; g.beginPath(); const cx = r() * w, cy = r() * w, rad = 14 + r() * 26; for (let k = 0; k <= 7; k++) { const a = k / 7 * TAU; const rr = rad * (0.7 + r() * 0.5); const x = cx + Math.cos(a) * rr, y = cy + Math.sin(a) * rr; k ? g.lineTo(x, y) : g.moveTo(x, y); } g.closePath(); g.stroke(); } }, { srgb: false, rep: [60, 60] });
T.lime = ctex(512, 512, (g, w) => { g.fillStyle = '#d9cfb8'; g.fillRect(0, 0, w, w); for (let i = 0; i < 1400; i++) { const r = 1 + R0() * 7; g.fillStyle = R0() < 0.6 ? 'rgba(140,125,100,0.35)' : 'rgba(255,250,235,0.4)'; g.beginPath(); g.arc(R0() * w, R0() * w, r, 0, TAU); g.fill(); } for (let i = 0; i < 20; i++) { g.strokeStyle = 'rgba(110,95,75,0.35)'; g.lineWidth = 2; g.beginPath(); let x = R0() * w, y = R0() * w; g.moveTo(x, y); for (let k = 0; k < 6; k++) { x += (R0() - .5) * 60; y += (R0() - .5) * 60; g.lineTo(x, y); } g.stroke(); } });
T.cliff = ctex(512, 512, (g, w) => { g.fillStyle = '#cfc6b2'; g.fillRect(0, 0, w, w); for (let y = 0; y < w; y += 24 + R0() * 20) { g.fillStyle = `rgba(${120 + R0() * 40},${110 + R0() * 30},${90 + R0() * 20},0.35)`; g.fillRect(0, y, w, 4 + R0() * 8); } for (let i = 0; i < 1500; i++) { g.fillStyle = R0() < 0.5 ? 'rgba(90,80,60,0.25)' : 'rgba(255,255,240,0.3)'; g.fillRect(R0() * w, R0() * w, 3, 3); } for (let i = 0; i < 25; i++) { g.fillStyle = 'rgba(60,140,50,0.55)'; g.beginPath(); g.ellipse(R0() * w, R0() * w * 0.3, 20 + R0() * 30, 8 + R0() * 10, 0, 0, TAU); g.fill(); } }, { rep: [2, 1] });
T.frond = ctex(512, 128, (g, w, h) => { g.fillStyle = '#3f9a2a'; g.beginPath(); g.moveTo(0, h / 2); g.quadraticCurveTo(w * 0.3, 0, w, h / 2); g.quadraticCurveTo(w * 0.3, h, 0, h / 2); g.fill(); g.strokeStyle = '#2a6a1c'; g.lineWidth = 5; g.beginPath(); g.moveTo(0, h / 2); g.lineTo(w, h / 2); g.stroke(); g.globalCompositeOperation = 'destination-out'; for (let x = 30; x < w; x += 18) { g.beginPath(); g.moveTo(x, h / 2 - 3); g.lineTo(x + 26, 0); g.lineTo(x + 30, 0); g.lineTo(x + 6, h / 2 - 3); g.fill(); g.beginPath(); g.moveTo(x, h / 2 + 3); g.lineTo(x + 26, h); g.lineTo(x + 30, h); g.lineTo(x + 6, h / 2 + 3); g.fill(); } g.globalCompositeOperation = 'source-over'; g.fillStyle = 'rgba(190,255,120,0.25)'; g.fillRect(0, h / 2 - 12, w, 8); });
T.trunk = ctex(128, 256, (g, w, h) => { g.fillStyle = '#9a6b3c'; g.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 16) { g.fillStyle = '#6e4622'; g.fillRect(0, y, w, 4); g.fillStyle = 'rgba(255,220,160,0.25)'; g.fillRect(0, y + 5, w, 3); } }, { rep: [2, 6] });
T.thatch = ctex(256, 256, (g, w) => { g.fillStyle = '#c99a4a'; g.fillRect(0, 0, w, w); for (let i = 0; i < 900; i++) { g.strokeStyle = R0() < 0.5 ? 'rgba(120,80,30,0.45)' : 'rgba(250,220,140,0.4)'; g.lineWidth = 2; const x = R0() * w, y = R0() * w; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (R0() - .5) * 6, y + 18); g.stroke(); } }, { rep: [4, 2] });
T.bamboo = ctex(256, 256, (g, w) => { for (let x = 0; x < w; x += 16) { const gr = g.createLinearGradient(x, 0, x + 16, 0); gr.addColorStop(0, '#9c7a3c'); gr.addColorStop(0.5, '#e0c27a'); gr.addColorStop(1, '#8a6a30'); g.fillStyle = gr; g.fillRect(x, 0, 16, w); } for (let y = 30; y < w; y += 64) { g.fillStyle = 'rgba(90,60,20,0.6)'; g.fillRect(0, y, w, 4); } }, { rep: [2, 1] });
T.hull = ctex(512, 128, (g, w, h) => { g.fillStyle = '#7a4a24'; g.fillRect(0, 0, w, h); for (let i = 0; i < 30; i++) { g.strokeStyle = 'rgba(50,25,10,0.35)'; g.lineWidth = 2; const y = R0() * h; g.beginPath(); g.moveTo(0, y); g.lineTo(w, y + (R0() - .5) * 10); g.stroke(); } g.fillStyle = '#d63a2a'; g.fillRect(0, 14, w, 14); g.fillStyle = '#f2d24a'; for (let x = 10; x < w; x += 40) { g.beginPath(); g.moveTo(x, 40); g.lineTo(x + 14, 56); g.lineTo(x + 28, 40); g.fill(); } });
T.sail = ctex(512, 512, (g, w) => { g.fillStyle = '#f4e6c4'; g.fillRect(0, 0, w, w); g.strokeStyle = 'rgba(160,130,80,0.5)'; g.lineWidth = 3; for (let x = 0; x < w; x += 40) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, w); g.stroke(); } g.fillStyle = '#e0562a'; g.beginPath(); g.arc(w * 0.38, w * 0.55, 70, 0, TAU); g.fill(); g.fillStyle = '#1a2a6a'; g.font = '900 64px Inter'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('THINK', w * 0.42, w * 0.74); g.fillText('ODD', w * 0.42, w * 0.86); });
T.coconut = ctex(256, 128, (g, w, h) => { g.fillStyle = '#a8763e'; g.fillRect(0, 0, w, h); for (let i = 0; i < 900; i++) { g.strokeStyle = R0() < 0.5 ? 'rgba(40,20,5,0.5)' : 'rgba(170,120,70,0.4)'; g.lineWidth = 1.5; const x = R0() * w, y = R0() * h; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (R0() - .5) * 10, y + 6); g.stroke(); } });
T.awning = ctex(256, 64, (g, w, h) => { for (let x = 0; x < w; x += 32) { g.fillStyle = (x / 32) % 2 ? '#ffffff' : '#ff4a6a'; g.fillRect(x, 0, 32, h); } });
T.stallSign = ctex(512, 160, (g, w, h) => { g.fillStyle = '#8a5a2a'; g.fillRect(0, 0, w, h); g.strokeStyle = '#4a2a10'; g.lineWidth = 10; g.strokeRect(5, 5, w - 10, h - 10); g.fillStyle = '#fff3c4'; g.font = '900 66px Inter'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('COCONUTS', w / 2, 62); g.fillStyle = '#ffd23f'; g.font = '900 34px Inter'; g.fillText('THINK ODD MARKET', w / 2, 122); }, { rep: [1, 1] });
T.bus = ctex(1024, 512, (g, w, h) => { g.fillStyle = '#ffc61a'; g.fillRect(0, 0, w, h); g.fillStyle = '#1d2747'; for (let x = 60; x < w - 120; x += 150) g.fillRect(x, 60, 120, 140); g.fillStyle = 'rgba(255,255,255,0.35)'; for (let x = 60; x < w - 120; x += 150) g.fillRect(x + 10, 70, 30, 120); g.fillStyle = '#1d2747'; g.fillRect(w - 110, 60, 80, 300); g.fillStyle = '#e8332a'; g.fillRect(0, 240, w, 26); g.fillStyle = '#101018'; g.font = '900 120px Inter'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('THINK ODD', w * 0.44, 360); g.font = '900 40px Inter'; g.fillText('BUS', w * 0.44, 450); }, { rep: [1, 1] });
T.board = (txt, sub) => ctex(512, 256, (g, w, h) => { g.fillStyle = '#a0703a'; g.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 64) { g.fillStyle = 'rgba(60,30,10,0.35)'; g.fillRect(0, y, w, 4); } g.strokeStyle = '#4a2a10'; g.lineWidth = 14; g.strokeRect(7, 7, w - 14, h - 14); g.fillStyle = '#fff6d6'; g.font = '900 96px Inter'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(txt, w / 2, h / 2 - 16); g.fillStyle = '#ffd23f'; g.font = '900 30px Inter'; g.fillText(sub, w / 2, h - 40); }, { rep: [1, 1] });
T.fish = (c1, c2) => ctex(128, 64, (g, w, h) => { g.fillStyle = c1; g.beginPath(); g.ellipse(52, 32, 44, 22, 0, 0, TAU); g.fill(); g.beginPath(); g.moveTo(90, 32); g.lineTo(124, 10); g.lineTo(124, 54); g.closePath(); g.fill(); g.fillStyle = c2; g.fillRect(40, 12, 10, 40); g.fillRect(64, 14, 8, 36); g.fillStyle = '#fff'; g.beginPath(); g.arc(26, 26, 7, 0, TAU); g.fill(); g.fillStyle = '#111'; g.beginPath(); g.arc(25, 26, 4, 0, TAU); g.fill(); g.strokeStyle = '#111'; g.lineWidth = 3; g.beginPath(); g.ellipse(52, 32, 44, 22, 0, 0, TAU); g.stroke(); });
T.kelp = ctex(64, 512, (g, w, h) => { g.fillStyle = '#2f8a3a'; g.beginPath(); g.moveTo(w / 2 - 6, h); for (let y = h; y > 0; y -= 32) g.quadraticCurveTo(w / 2 + (y % 64 ? 22 : -22), y - 16, w / 2 - 4, y - 32); g.lineTo(w / 2 + 4, 0); for (let y = 0; y < h; y += 32) g.quadraticCurveTo(w / 2 + (y % 64 ? -18 : 18) + 8, y + 16, w / 2 + 6, y + 32); g.fill(); });
T.cloud = ctex(256, 128, (g, w, h) => { g.fillStyle = '#fff'; for (const [x, y, r] of [[60, 80, 40], [110, 60, 52], [170, 70, 44], [210, 88, 30], [130, 92, 40]]) { g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); } g.globalCompositeOperation = 'source-atop'; const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(1, 'rgba(150,175,230,0.6)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }, { srgb: true });
T.bolt = ctex(128, 512, (g, w, h) => { g.strokeStyle = '#fff'; g.lineWidth = 8; g.shadowColor = '#9fc4ff'; g.shadowBlur = 20; g.beginPath(); let x = w / 2; g.moveTo(x, 0); const r = rng(8); for (let y = 0; y < h; y += 40) { x += (r() - 0.5) * 60; g.lineTo(clamp(x, 10, w - 10), y); } g.stroke(); }, { srgb: false });
T.slate = ctex(256, 192, (g, w, h) => { g.fillStyle = '#2a3a2a'; g.fillRect(0, 0, w, h); g.strokeStyle = '#8a5a2a'; g.lineWidth = 16; g.strokeRect(8, 8, w - 16, h - 16); g.strokeStyle = '#f4f4e8'; g.lineWidth = 6; for (let i = 0; i < 4; i++) for (let k = 0; k < 4; k++) { g.beginPath(); g.moveTo(34 + i * 52 + k * 9, 40); g.lineTo(34 + i * 52 + k * 9, 92); g.stroke(); } for (let i = 0; i < 4; i++) { g.beginPath(); g.moveTo(28 + i * 52, 80); g.lineTo(70 + i * 52, 50); g.stroke(); } g.fillStyle = '#ffd23f'; g.font = '900 30px Inter'; g.textAlign = 'center'; g.fillText('OUR STONE', w / 2, 140); g.font = '900 18px Inter'; g.fillStyle = '#fff'; g.fillText('THINK ODD', w / 2, 170); });

// ------------------------------------------------------------------ scene + environment
const scene = new THREE.Scene();
const FOG = new THREE.Color('#9fd3ff');
scene.fog = new THREE.FogExp2(FOG.clone(), 0.006);
scene.background = FOG.clone();
const camera = new THREE.PerspectiveCamera(50, W / H, 0.05, 900);
const SUN = V(-0.45, -0.75, -0.5).normalize();
const hemi = new THREE.HemisphereLight('#bfe4ff', '#d9b27a', 1.1); scene.add(hemi);
const sun = new THREE.DirectionalLight('#fff0cf', 3.2); scene.add(sun, sun.target);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -32, right: 32, top: 32, bottom: -32, near: 1, far: 200 }); sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.05; sun.shadow.radius = 3;
const fill = new THREE.PointLight('#ffffff', 0, 30, 1); scene.add(fill);

const lam = (o) => new THREE.MeshLambertMaterial(o);
function add(geo, mat, x, y, z, o = {}) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); if (o.rx) m.rotation.x = o.rx; if (o.ry) m.rotation.y = o.ry; if (o.rz) m.rotation.z = o.rz; if (o.s) m.scale.setScalar(o.s); m.castShadow = o.cast ?? true; m.receiveShadow = o.recv ?? true; (o.parent || scene).add(m); return m; }
const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);

// ---- zones
const YAP = V(0, 0, 0), PAL = V(300, 0, 0), STORM = V(-300, 0, 0), SEA_STONE = V(-4, -14, 80);
const TOP = 0.8, SEABED = -14;
function islandH(r, R0_ = 32, R1 = 46) { if (r < R0_) return TOP; if (r < R1) { const k = (r - R0_) / (R1 - R0_); return lerp(TOP, -0.9, k * k * (3 - 2 * k)); } if (r < R1 + 34) { const k = (r - R1) / 34; return lerp(-0.9, SEABED, Math.sqrt(k)); } return SEABED; }
function groundAt(x, z) { const r1 = Math.hypot(x - YAP.x, z - YAP.z), r2 = Math.hypot(x - PAL.x, z - PAL.z); return Math.max(islandH(r1), islandH(r2, 26, 38), SEABED); }
function islandMesh(c, R0_, R1, seed) {
  const pts = []; const N = 64, M = 48; const r = rng(seed); const wob = Array.from({ length: 6 }, () => [r() * TAU, 1 + Math.floor(r() * 4), r()]);
  const g = new THREE.BufferGeometry(); const pos = [], col = [], uv = [], idx = [];
  const cS = new THREE.Color('#f2d59a'), cG = new THREE.Color('#5cc43e'), cW = new THREE.Color('#c9a86a'), cU = new THREE.Color('#b9a27a');
  for (let j = 0; j <= M; j++) { const rr = (j / M) ** 1.3 * (R1 + 36); for (let i = 0; i <= N; i++) { const a = i / N * TAU; let w = 0; for (const [p, k, amp] of wob) w += Math.sin(a * k + p) * amp; const rad = rr * (1 + 0.04 * w); const y = islandH(rr, R0_, R1); const x = c.x + Math.cos(a) * rad, z = c.z + Math.sin(a) * rad; pos.push(x, y, z); uv.push(x / 6, z / 6);
    const cc = rr < R0_ - 4 ? cG.clone().lerp(cS, sstep(R0_ - 10, R0_ - 4, rr)) : rr < R1 - 6 ? cS : rr < R1 + 4 ? cS.clone().lerp(cW, sstep(R1 - 6, R1 + 2, rr)) : cW.clone().lerp(cU, sstep(R1 + 4, R1 + 20, rr)); col.push(cc.r, cc.g, cc.b); } }
  for (let j = 0; j < M; j++) for (let i = 0; i < N; i++) { const a = j * (N + 1) + i, b = a + N + 1; idx.push(a, a + 1, b, b, a + 1, b + 1); }
  g.setIndex(idx); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.computeVertexNormals();
  const t = T.sand.clone(); t.repeat.set(1, 1); t.needsUpdate = true; const m = new THREE.Mesh(g, lam({ map: t, vertexColors: true })); m.receiveShadow = true; scene.add(m); return m;
}
islandMesh(YAP, 32, 46, 1); islandMesh(PAL, 26, 38, 2);
// seabed + caustics
add(new THREE.PlaneGeometry(1600, 1600), lam({ map: T.seabed }), 0, SEABED - 0.05, 0, { rx: -Math.PI / 2, cast: false });
const causticM = new THREE.MeshBasicMaterial({ map: T.caustic, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, color: new THREE.Color(0.55, 0.75, 0.8) });
const causticM2 = causticM.clone(); causticM2.map = T.caustic.clone(); causticM2.map.repeat.set(47, 47); causticM2.map.needsUpdate = true;
add(new THREE.PlaneGeometry(1600, 1600), causticM, 0, SEABED + 0.02, 0, { rx: -Math.PI / 2, cast: false, recv: false });
add(new THREE.PlaneGeometry(1600, 1600), causticM2, 0, SEABED + 0.04, 0, { rx: -Math.PI / 2, cast: false, recv: false });

// ---- ocean (follows camera; waves in world space)
const oceanGeo = (() => { const N = 150, R = 420; const g = new THREE.BufferGeometry(); const pos = [], idx = []; for (let j = 0; j <= N; j++) for (let i = 0; i <= N; i++) { const u = i / N * 2 - 1, v = j / N * 2 - 1; pos.push(Math.sign(u) * u * u * R, 0, Math.sign(v) * v * v * R); } for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { const a = j * (N + 1) + i, b = a + N + 1; idx.push(a, b, a + 1, b, b + 1, a + 1); } g.setIndex(idx); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); return g; })();
const WAVES = [[0.9, 0.11, 0.6, 1.1], [0.6, 0.17, -0.5, 1.4], [0.35, 0.31, 1.3, 1.9], [0.18, 0.53, -1.8, 2.6], [0.09, 0.9, 2.4, 3.4]];
const WAVE_GLSL = WAVES.map(([a, k, d, w], i) => `{ vec2 dd = vec2(cos(${d.toFixed(2)}), sin(${d.toFixed(2)})); float ph = dot(dd, p)*${k.toFixed(3)} + uT*${w.toFixed(2)}; h += ${a.toFixed(3)}*uAmp*sin(ph); gr += ${(a * k).toFixed(4)}*uAmp*cos(ph)*dd; }`).join('\n');
function waveH(x, z, t, amp) { let h = 0; for (const [a, k, d, w] of WAVES) h += a * amp * Math.sin((Math.cos(d) * x + Math.sin(d) * z) * k + t * w); return h; }
const oceanMat = new THREE.ShaderMaterial({ side: THREE.DoubleSide, fog: false,
  uniforms: { uT: { value: 0 }, uAmp: { value: 0.35 }, uSun: { value: SUN.clone().negate() }, uSky: { value: new THREE.Color('#7cc4ff') }, uDeep: { value: new THREE.Color('#0a4f9a') }, uShallow: { value: new THREE.Color('#1fd6d0') }, fogC: { value: scene.fog.color }, fogD: { value: 0.006 }, uIsl: { value: [new THREE.Vector2(0, 0), new THREE.Vector2(300, 0)] }, uUnder: { value: 0 }, uSunC: { value: new THREE.Color('#fff4d6') } },
  vertexShader: `uniform float uT, uAmp; varying vec3 vW; varying vec3 vN; void main(){ vec4 w = modelMatrix*vec4(position,1.); vec2 p = w.xz; float h = 0.; vec2 gr = vec2(0.);
  ${WAVE_GLSL}
  w.y += h; vW = w.xyz; vN = normalize(vec3(-gr.x, 1., -gr.y)); gl_Position = projectionMatrix*viewMatrix*w; }`,
  fragmentShader: `uniform vec3 uSun, uSky, uDeep, uShallow, fogC, uSunC; uniform float fogD, uUnder, uT; uniform vec2 uIsl[2]; varying vec3 vW; varying vec3 vN;
  void main(){ vec3 V = normalize(cameraPosition - vW); vec3 N = normalize(vN); if (!gl_FrontFacing) N = -N;
    float d = min(length(vW.xz-uIsl[0]) - 44., length(vW.xz-uIsl[1]) - 36.); float sh = 1.-smoothstep(0., 34., d);
    vec3 base = mix(uDeep, uShallow, sh*0.85 + 0.12);
    float fr = pow(1.-max(dot(N,V),0.),4.);
    vec3 R = reflect(-V, N); float sp = pow(max(dot(R, uSun),0.), 180.)*3.5 + pow(max(dot(R,uSun),0.),20.)*0.25;
    float foam = smoothstep(0.55, 1.0, vW.y + 0.25*sin(vW.x*1.7+uT)*sin(vW.z*1.3-uT*0.7)) * 0.8 + (1.-smoothstep(0., 2.2, d+0.8))*0.9*(0.6+0.4*sin(vW.x*3.+vW.z*2.+uT*2.));
    vec3 col = mix(base, uSky, fr*0.7) + uSunC*sp; col = mix(col, vec3(0.95,0.98,1.0), clamp(foam,0.,1.)*0.85);
    col *= 0.85 + 0.3*max(dot(N, uSun), 0.);
    if (!gl_FrontFacing || uUnder > 0.5) { float win = pow(max(dot(-V, vec3(0.,-1.,0.)) ,0.), 3.); col = mix(vec3(0.03,0.32,0.42), vec3(0.55,0.95,1.0), win) + uSunC*pow(max(dot(-V, -uSun),0.),40.)*1.5; }
    float dist = length(cameraPosition - vW); float f = 1.-exp(-fogD*fogD*dist*dist); col = mix(col, fogC, f);
    gl_FragColor = vec4(col, 1.); }` });
const ocean = new THREE.Mesh(oceanGeo, oceanMat); ocean.frustumCulled = false; ocean.receiveShadow = false; scene.add(ocean);

// ---- sky dome + clouds (follow camera)
const skyMat = new THREE.ShaderMaterial({ side: THREE.BackSide, fog: false, depthWrite: false, uniforms: { uTop: { value: new THREE.Color('#2f7fe6') }, uHor: { value: new THREE.Color('#bfe6ff') }, uSun: { value: SUN.clone().negate() }, uSunC: { value: new THREE.Color('#fff2c8') }, uUnder: { value: 0 } },
  vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: 'uniform vec3 uTop, uHor, uSun, uSunC; uniform float uUnder; varying vec3 vP; void main(){ float h = clamp(vP.y,0.,1.); vec3 c = mix(uHor, uTop, pow(h,0.55)); float s = max(dot(normalize(vP), uSun),0.); c += uSunC*(pow(s,600.)*8. + pow(s,12.)*0.35); if (vP.y < 0.) c = uHor*0.9; if (uUnder>0.5) c = vec3(0.02,0.25,0.33); gl_FragColor = vec4(c,1.); }' });
const sky = new THREE.Mesh(new THREE.SphereGeometry(800, 32, 16), skyMat); sky.frustumCulled = false; sky.renderOrder = -10; scene.add(sky);
const clouds = new THREE.Group(); scene.add(clouds);
{ const cm = new THREE.MeshBasicMaterial({ map: T.cloud, transparent: true, depthWrite: false, fog: false }); cm.color.setRGB(1.25, 1.25, 1.3); const r = rng(77); for (let i = 0; i < 26; i++) { const a = r() * TAU, d = 380 + r() * 220; const s = 70 + r() * 90; const m = add(new THREE.PlaneGeometry(s, s * 0.5), cm, Math.cos(a) * d, 50 + r() * 90, Math.sin(a) * d, { cast: false, recv: false }); m.lookAt(0, m.position.y, 0); m.renderOrder = -9; } }

// ---- palms
const trunkM = lam({ map: T.trunk }); const frondM = lam({ map: T.frond, alphaTest: 0.5, side: THREE.DoubleSide }); const nutM = lam({ map: T.coconut });
const frondGeo = (() => { const g = new THREE.PlaneGeometry(5.2, 1.3, 12, 1); g.translate(2.6, 0, 0); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i); p.setY(i, p.getY(i) - 0.09 * x * x); p.setZ(i, p.getY(i) * 0.0); } g.rotateX(-Math.PI / 2 + 0.0); g.computeVertexNormals(); return g; })();
const fronds = [];
function palm(x, z, h, lean, dirA, seed) {
  const r = rng(seed); const y0 = groundAt(x, z); const top = V(x + Math.cos(dirA) * lean, y0 + h, z + Math.sin(dirA) * lean);
  const curve = new THREE.QuadraticBezierCurve3(V(x, y0 - 0.3, z), V(x + Math.cos(dirA) * lean * 0.2, y0 + h * 0.6, z + Math.sin(dirA) * lean * 0.2), top);
  const g = new THREE.TubeGeometry(curve, 14, 0.28, 8); add(g, trunkM, 0, 0, 0);
  const grp = new THREE.Group(); grp.position.copy(top); scene.add(grp);
  for (let i = 0; i < 9; i++) { const f = new THREE.Mesh(frondGeo, frondM); f.rotation.order = 'YZX'; f.rotation.y = i / 9 * TAU + r() * 0.3; f.rotation.z = 0.25 + r() * 0.35; f.castShadow = true; grp.add(f); fronds.push({ f, base: f.rotation.z, ph: r() * TAU }); }
  for (let i = 0; i < 4; i++) add(new THREE.SphereGeometry(0.26, 10, 8), nutM, Math.cos(i * 1.7) * 0.35, -0.3, Math.sin(i * 1.7) * 0.35, { parent: grp });
}
{ const r = rng(12); for (let i = 0; i < 30; i++) { const a = r() * TAU, d = 18 + r() * 20; const x = Math.cos(a) * d, z = Math.sin(a) * d; if (Math.abs(x) < 7 && z > 15 && z < 30) continue; palm(x, z, 7 + r() * 5, 1 + r() * 2.5, a, 100 + i); }
  for (const [x, z] of [[6, 20], [-6, 18], [9, 30], [-11, 31], [17, 4], [-17, 6], [2, -14], [-9, -16], [-13, 17], [12, 13]]) palm(x, z, 8 + r() * 3, 1.4 + r(), r() * TAU, 300 + x * 7 + z);
  for (let i = 0; i < 10; i++) { const a = r() * TAU, d = 10 + r() * 18; palm(PAL.x + Math.cos(a) * d, PAL.z + 6 + Math.abs(Math.sin(a)) * d, 7 + r() * 4, 1.5 + r() * 2, a, 500 + i); } }
// ---- huts
const thatchM = lam({ map: T.thatch }); const bambooM = lam({ map: T.bamboo });
function hut(x, z, ry) { const y = groundAt(x, z); const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = ry; scene.add(g); add(box(4.4, 2.6, 3.6), bambooM, 0, 1.3, 0, { parent: g }); add(new THREE.ConeGeometry(3.9, 3.2, 4, 1), thatchM, 0, 4.1, 0, { parent: g, ry: Math.PI / 4 }); add(box(1.1, 1.8, 0.1), lam({ color: '#2a1a0a' }), 0, 0.9, 1.81, { parent: g, cast: false }); for (const sx of [-1, 1]) for (const sz of [-1, 1]) add(new THREE.CylinderGeometry(0.12, 0.12, 2.8, 6), lam({ color: '#6b4220' }), sx * 2.2, 1.4, sz * 1.8, { parent: g }); }
for (const [x, z, ry] of [[-7, 26, 0.3], [9, 24, -0.4], [-19, 2, 1.3], [19, -6, -1.2], [-12, -18, 0.5], [6, -20, -0.2], [25, 3, -1.0], [-20, 22, 0.9]]) hut(x, z, ry);

// ---- rai stones
const limeM = lam({ map: T.lime, color: '#f0e8d8' });
function raiGeo(R, th, hole = 0.24) { const s = new THREE.Shape(); s.absarc(0, 0, R, 0, TAU, false); const h = new THREE.Path(); h.absarc(0, 0, R * hole, 0, TAU, true); s.holes.push(h); const g = new THREE.ExtrudeGeometry(s, { depth: th, bevelEnabled: true, bevelThickness: th * 0.25, bevelSize: R * 0.06, bevelSegments: 3, curveSegments: 40 }); g.translate(0, 0, -th / 2); const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) / (R * 2) + 0.5, uv.getY(i) / (R * 2) + 0.5); return g; }
function rai(x, z, R, ry = 0, o = {}) { const y = o.y ?? (groundAt(x, z) + R * 0.98); const m = add(raiGeo(R, R * 0.26, o.hole), limeM, x, y, z, { ry, rx: o.rx, rz: o.rz, parent: o.parent }); return m; }
const G1 = rai(0, 22, 2.4, 0.15);   // hero stone (opening)
const G2 = rai(14, 8, 2.0, -0.2);   // thief stone
const G3 = rai(-9.0, 15.6, 2.2, 0.5); // buyer's stone at the market
const G4 = rai(-4, -10, 2.8, 0);    // meeting stone (name changes)
for (const [x, z, R, ry] of [[-16, 10, 1.4, 1.2], [15, 20, 1.2, -0.6], [-3, 30.5, 1.0, 0.2], [10, -10, 1.7, 0.9], [-20, -10, 1.3, 0.4], [4, 2, 1.1, -1]]) rai(x, z, R, ry);
const SEA_R = 3.4; const seaStone = rai(SEA_STONE.x, 0, SEA_R, 0.4, { y: SEABED + 1.25, rx: -1.25 });
// support rocks + tags
const rockM = lam({ color: '#8a8478' });
for (const S of [G1, G2, G3, G4]) for (const sx of [-1, 1]) add(new THREE.DodecahedronGeometry(0.35, 0), rockM, S.position.x + sx * 0.9, groundAt(S.position.x, S.position.z) + 0.15, S.position.z + 0.5);
const tag4 = add(new THREE.PlaneGeometry(1.3, 0.65), lam({ map: T.board('4 TONS', 'THINK ODD'), side: THREE.DoubleSide }), 14.6, 1.55, 8.75, { ry: -0.2, cast: false });
const boardA = T.board('TAMAG', 'OWNER'), boardB = T.board('FALAN', 'NEW OWNER');
const nameBoardM = lam({ map: boardA }); const nameBoard = add(new THREE.PlaneGeometry(2.0, 1.0), nameBoardM, -4, 1.75, -9.33, { cast: false });
add(new THREE.CylinderGeometry(0.02, 0.02, 1.2, 4), lam({ color: '#5a3a1a' }), -4.6, 2.5, -9.36, { rz: 0.5, cast: false }); add(new THREE.CylinderGeometry(0.02, 0.02, 1.2, 4), lam({ color: '#5a3a1a' }), -3.4, 2.5, -9.36, { rz: -0.5, cast: false });

// ---- market stall
{ const x = -14, z = 12, y = groundAt(x, z); const woodM = lam({ color: '#8a5a2a' }); add(box(3.4, 1.0, 1.4), woodM, x, y + 0.5, z); for (const sx of [-1.6, 1.6]) for (const sz of [-0.6, 0.6]) add(new THREE.CylinderGeometry(0.08, 0.08, 3.2, 6), woodM, x + sx, y + 1.6, z + sz);
  add(box(3.8, 0.12, 2.0), lam({ map: T.awning }), x, y + 3.25, z, { rx: 0.08 });
  add(new THREE.PlaneGeometry(2.6, 0.8), lam({ map: T.stallSign }), x, y + 2.75, z + 0.72, { cast: false });
  const r = rng(9); for (let l = 0; l < 3; l++) for (let i = 0; i < 5 - l * 2; i++) for (let k = 0; k < 2 - (l > 1 ? 1 : 0); k++) add(new THREE.SphereGeometry(0.2, 12, 10), nutM, x - 0.5 + (i - (4 - l * 2) / 2) * 0.38 + l * 0.0, y + 1.2 + l * 0.32, z + 0.2 + k * 0.36 - (l ? 0.18 : 0));
  for (let i = 0; i < 3; i++) { const c = add(new THREE.SphereGeometry(0.22, 12, 10), lam({ color: '#5fa83a' }), x + 1.0 + i * 0.25, y + 1.2, z + 0.3 - i * 0.2); } }
// ---- bus (gag)
const bus = new THREE.Group(); scene.add(bus);
{ const bm = [lam({ color: '#ffc61a' }), lam({ color: '#ffc61a' }), lam({ color: '#ffd84a' }), lam({ color: '#c79a10' }), lam({ map: T.bus }), lam({ map: T.bus })]; add(box(5.2, 2.2, 2.1), bm, 0, 1.1, 0, { parent: bus }); for (const sx of [-1.7, 1.7]) for (const sz of [-1.06, 1.06]) add(new THREE.CylinderGeometry(0.42, 0.42, 0.3, 16), lam({ color: '#1a1a1a' }), sx, 0.1, sz, { rx: Math.PI / 2, parent: bus }); }

// ---- Palau quarry (limestone cliffs + half carved wheel)
const cliffM = lam({ map: T.cliff });
{ const r = rng(21); for (let i = 0; i < 9; i++) { const w = 6 + r() * 5, h = 9 + r() * 7, d = 5 + r() * 3; const m = add(box(w, h, d), cliffM, PAL.x - 22 + i * 5.2, TOP + h / 2 - 0.5, PAL.z - 13 - r() * 3, { ry: (r() - .5) * 0.4 }); }
  for (let i = 0; i < 14; i++) add(new THREE.DodecahedronGeometry(0.3 + r() * 0.5, 0), lam({ color: '#d8cfb8' }), PAL.x - 7 + r() * 14, TOP + 0.2, PAL.z - 9.5 + r() * 2.2); }
const carveWheel = rai(PAL.x, PAL.z - 8.6, 2.2, 0, {});
const halfWheel = rai(PAL.x - 6, PAL.z - 9.2, 1.8, 0.1, {});
// ---- canoes (outrigger + sail)
function canoe() { const g = new THREE.Group(); scene.add(g); const hullG = new THREE.CapsuleGeometry(0.55, 5.2, 6, 14); hullG.rotateZ(Math.PI / 2); hullG.scale(1, 0.62, 0.8); add(hullG, lam({ map: T.hull }), 0, 0.15, 0, { parent: g }); add(box(5.0, 0.12, 0.8), lam({ color: '#a8743a' }), 0, 0.5, 0, { parent: g });
  const flt = new THREE.CapsuleGeometry(0.22, 3.6, 4, 8); flt.rotateZ(Math.PI / 2); add(flt, lam({ color: '#6b4220' }), 0, 0.05, -2.3, { parent: g }); for (const x of [-1.4, 1.4]) add(new THREE.CylinderGeometry(0.06, 0.06, 2.6, 6), lam({ color: '#c49a5a' }), x, 0.55, -1.2, { rx: Math.PI / 2, parent: g });
  add(new THREE.CylinderGeometry(0.07, 0.09, 5.2, 8), lam({ color: '#6b4220' }), 0.3, 3.0, 0, { parent: g });
  const s = new THREE.Shape(); s.moveTo(0, 0); s.lineTo(3.4, 0); s.lineTo(0.2, 4.4); s.closePath(); const sg = new THREE.ShapeGeometry(s); const uv = sg.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) / 3.4, uv.getY(i) / 4.4);
  const sm = lam({ map: T.sail }); const a = add(sg, sm, -1.4, 0.9, 0.06, { parent: g, cast: false }); const b = add(sg, sm, 2.0, 0.9, -0.06, { parent: g, ry: Math.PI, cast: false }); return g; }
const canoeV = canoe(); // voyage
const canoeT = canoe(); // towing
const raft = new THREE.Group(); scene.add(raft); for (let i = 0; i < 7; i++) add(new THREE.CylinderGeometry(0.2, 0.2, 3.6, 8), lam({ map: T.bamboo }), -1.2 + i * 0.4, 0.15, 0, { rx: Math.PI / 2, parent: raft });
const raftStone = rai(0, 0, 2.0, 0, { y: 2.45, parent: raft, hole: 0.3 });
const rope = add(new THREE.CylinderGeometry(0.03, 0.03, 1, 5), lam({ color: '#d8c08a' }), 0, 0, 0, { cast: false });
const canoeS = canoe(); // storm
const stormStone = rai(0, 0, 1.7, 0, { y: 2.2, parent: canoeS });
const boltM = new THREE.MeshBasicMaterial({ map: T.bolt, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }); boltM.color.setRGB(3, 3.4, 4);
const bolt = add(new THREE.PlaneGeometry(14, 60), boltM, STORM.x - 30, 30, STORM.z - 70, { cast: false, recv: false });
// ---- underwater life near the sea stone
const kelps = []; { const km = lam({ map: T.kelp, alphaTest: 0.5, side: THREE.DoubleSide }); const r = rng(31); for (let i = 0; i < 46; i++) { const a = r() * TAU, d = 4.5 + r() * 14; const h = 4 + r() * 6; const m = add(new THREE.PlaneGeometry(0.8, h), km, SEA_STONE.x + Math.cos(a) * d, SEABED + h / 2, SEA_STONE.z + Math.sin(a) * d, { ry: r() * 3, cast: false }); kelps.push({ m, ph: r() * TAU }); }
  const cols = ['#ff6a8a', '#ffb03a', '#a06aff', '#3ae0c0', '#ff4a4a']; for (let i = 0; i < 40; i++) { const a = r() * TAU, d = 4 + r() * 12; const c = cols[i % 5]; const kind = i % 3; const geo = kind === 0 ? new THREE.SphereGeometry(0.4 + r() * 0.6, 10, 8) : kind === 1 ? new THREE.ConeGeometry(0.3 + r() * 0.3, 1 + r() * 1.5, 8) : new THREE.TorusKnotGeometry(0.35, 0.12, 30, 6); add(geo, lam({ color: c, emissive: c, emissiveIntensity: 0.15 }), SEA_STONE.x + Math.cos(a) * d, SEABED + 0.4, SEA_STONE.z + Math.sin(a) * d, { cast: false }); }
  for (let i = 0; i < 18; i++) add(new THREE.DodecahedronGeometry(0.4 + r() * 1.1, 0), rockM, SEA_STONE.x + (r() - .5) * 30, SEABED + 0.2, SEA_STONE.z + (r() - .5) * 30, { cast: false }); }
const fishTex = [T.fish('#ffb020', '#ffffff'), T.fish('#ff5a7a', '#fff2a0'), T.fish('#3ad0ff', '#1a3a8a')];
const fishes = []; { const r = rng(41); for (let i = 0; i < 26; i++) { const m = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.45), new THREE.MeshLambertMaterial({ map: fishTex[i % 3], alphaTest: 0.5, side: THREE.DoubleSide, emissive: '#223344' })); scene.add(m); fishes.push({ m, r: 3.5 + r() * 7, y: SEABED + 1.5 + r() * 5, sp: (0.25 + r() * 0.3) * (r() < 0.5 ? 1 : -1), ph: r() * TAU, c: i % 2 ? SEA_STONE : V(STORM.x, 0, STORM.z - 3) }); } }

// ---- underwater god rays
const shaftMats = [];
function shaft(origin, dir, len, w, d, inten, col) {
  const g = box(w, len, d); g.translate(0, len / 2, 0);
  const m = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false,
    uniforms: { uI: { value: inten }, uC: { value: new THREE.Color(col) }, uT: { value: 0 }, uDim: { value: V(w, len, d) } },
    vertexShader: 'uniform vec3 uDim; varying vec3 vL; varying vec3 vN; varying vec3 vV; void main(){ vL = position/uDim; vec4 mv = modelViewMatrix*vec4(position,1.); vN = normalMatrix*normal; vV = -mv.xyz; gl_Position = projectionMatrix*mv; }',
    fragmentShader: 'uniform float uI; uniform vec3 uC; uniform float uT; varying vec3 vL; varying vec3 vN; varying vec3 vV; void main(){ float a = vL.y; float ex = 1.-smoothstep(0.2,0.5,abs(vL.x)); float ez = 1.-smoothstep(0.25,0.5,abs(vL.z)); float fr = pow(abs(dot(normalize(vN),normalize(vV))),1.6); float st = 0.7+0.3*sin(vL.z*23.+vL.x*9.+uT*0.94)*sin(vL.x*13.-uT*0.63); float k = uI*(0.25+0.75*(1.-a))*ex*ez*fr*st*smoothstep(0.,0.06,a)*(1.-smoothstep(0.8,1.,a)); gl_FragColor = vec4(uC*k,1.); }' });
  const mesh = new THREE.Mesh(g, m); mesh.position.copy(origin); mesh.quaternion.setFromUnitVectors(V(0, 1, 0), dir.clone()); mesh.renderOrder = 10; scene.add(mesh); shaftMats.push(m); return mesh;
}
{ const r = rng(51); for (let i = 0; i < 9; i++) shaft(V(SEA_STONE.x - 12 + r() * 24, -0.6, SEA_STONE.z - 14 + r() * 24), V(0.25, -1, 0.3).normalize(), 15, 1.6 + r() * 2.5, 1.6 + r() * 2.5, 0.12, '#bff6ff'); }

// ------------------------------------------------------------------ 2D characters (canvas sprites as billboards)
const CW = 512, CH = 900, PX = 1.6 / CW;
function shade(hex, k) { const c = new THREE.Color(hex); c.offsetHSL(0, 0, k * 0.5); return '#' + c.getHexString(); }
const O = (coat, x = {}) => ({ coat, coat2: shade(coat, -0.25), hood: true, ...x });
const OUTFIT = {
  hero: O('#3f9cf0', { brand: true }),
  thief: O('#2a2a35', { mask: true, hat: 'beanie', capCol: '#16161e', brand: true, brandCol: '#ff4a4a' }),
  pusher: O('#3fae5a', { hair: '#6b4220', brand: true, brandCol: '#ffffff' }),
  seller: O('#f2c230', { hat: 'straw', brand: true, brandCol: '#1a2a6a' }),
  elderA: O('#f08a2a', { hair: '#eeeeee' }), elderB: O('#8a4ad0', { hair: '#eeeeee', brand: true, brandCol: '#fff' }),
  traderA: O('#26b5b0', { hair: '#2a2a33' }), traderB: O('#e04a6a', { hat: 'straw', brand: true, brandCol: '#fff' }),
  vil1: O('#8ab52a', { hair: '#7a4a20' }), vil2: O('#d83a3a', { hat: 'beanie', capCol: '#f2c230', brand: true, brandCol: '#fff' }),
  vil3: O('#4ac0ff', { hair: '#3a2414' }), vil4: O('#a0643a', { hat: 'straw' }),
  dad: O('#ff6a3a', { hair: '#2a1a10', brand: true, brandCol: '#fff' }), mom: O('#ff7ab0', { hair: '#3a2414', hat: 'flower' }), kid: O('#b8e04a', { hair: '#5a3418' }),
};
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
      uniforms: { map: { value: this.tex }, uRim: { value: new THREE.Vector2(1, 0) }, uRimC: { value: new THREE.Color('#ffd47a') }, uRim2C: { value: new THREE.Color('#5c7dff') }, uTint: { value: new THREE.Color(1, 1, 1) }, fogC: { value: scene.fog.color }, fogD: { value: scene.fog.density }, uOp: { value: 1 }, uTexel: { value: new THREE.Vector2(1 / CW, 1 / CH) } } });
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
  if (o.brand) { g.save(); g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = '900 25px Inter'; g.lineWidth = 6; g.strokeStyle = K; g.fillStyle = o.brandCol || '#ffd23f'; g.strokeText('THINK', 0, -392); g.fillText('THINK', 0, -392); g.strokeText('ODD', 0, -368); g.fillText('ODD', 0, -368); g.restore(); }
  if (!o.hood) { g.fillStyle = '#f2c14a'; g.strokeStyle = K; g.lineWidth = 3; for (const y of [-420, -385, -350, -315]) { g.beginPath(); g.arc(0, y, 8, 0, TAU); g.fill(); g.stroke(); } }
  if (o.ruff) { g.fillStyle = '#ffffff'; g.strokeStyle = K; g.lineWidth = 6; g.beginPath(); g.ellipse(0, -458, 100, 30, 0, 0, TAU); g.fill(); g.stroke(); g.lineWidth = 3; for (let i = -4; i <= 4; i++) { g.beginPath(); g.moveTo(i * 20, -434); g.lineTo(i * 22, -482); g.stroke(); } }
  if (st.pose === 'shrug') { g.fillStyle = '#ffffff'; g.strokeStyle = K; g.lineWidth = 6; for (const sx of [-1, 1]) { g.beginPath(); g.moveTo(sx * 70, -300); g.lineTo(sx * 104, -270); g.lineTo(sx * 80, -248); g.closePath(); g.fill(); g.stroke(); } }
  // sleeves (thick, coat colour) + big white hands
  for (const [sx, h] of [[58, hands.R], [-58, hands.L]]) { g.beginPath(); g.moveTo(sx, -432); const mx = (sx + h[0]) / 2 + Math.sign(sx) * 20, my = (-432 + h[1]) / 2 + 16; g.quadraticCurveTo(mx, my, h[0] * 0.9 + sx * 0.1, h[1] + (h[1] < -432 ? 12 : -12)); g.strokeStyle = K; g.lineWidth = 42; g.stroke(); g.strokeStyle = o.coat; g.lineWidth = 29; g.stroke(); }
  for (const h of [hands.R, hands.L]) { g.beginPath(); g.arc(h[0], h[1], 28, 0, TAU); g.fillStyle = '#ffffff'; g.fill(); g.strokeStyle = K; g.lineWidth = 8; g.stroke(); }
  if (st.pose === 'shh') { g.fillStyle = '#fff'; g.strokeStyle = K; g.lineWidth = 7; g.beginPath(); g.roundRect(hands.R[0] - 9, hands.R[1] - 62, 18, 52, 9); g.fill(); g.stroke(); }
  if (st.pose === 'hammer') { const h = hands.R; const ang = -0.9 + (st.hk || 0) * 1.9; g.save(); g.translate(h[0], h[1]); g.rotate(ang); g.fillStyle = '#8a5a2a'; g.strokeStyle = K; g.lineWidth = 6; g.beginPath(); g.roundRect(-8, -150, 16, 150, 6); g.fill(); g.stroke(); g.fillStyle = '#9a9a9a'; g.beginPath(); g.roundRect(-46, -190, 92, 48, 12); g.fill(); g.stroke(); g.restore(); }
  if (st.pose === 'paddle') { const h1 = hands.R, h2 = hands.L; g.save(); g.strokeStyle = K; g.lineWidth = 18; g.beginPath(); g.moveTo(h2[0] - 40, h2[1] - 60); g.lineTo(h1[0] + 60, h1[1] + 220); g.stroke(); g.strokeStyle = '#b8803a'; g.lineWidth = 10; g.stroke(); g.translate(h1[0] + 60, h1[1] + 220); g.rotate(Math.atan2(h1[1] + 220 - h2[1] + 60, h1[0] + 100 - h2[0])); g.fillStyle = '#b8803a'; g.strokeStyle = K; g.lineWidth = 6; g.beginPath(); g.ellipse(30, 0, 50, 22, 0, 0, TAU); g.fill(); g.stroke(); g.restore(); }
  if (st.pose === 'count') { const h = hands.L; g.save(); g.translate(h[0] - 20, h[1] - 70); g.rotate(0.1); g.drawImage(SLATE_IMG, -80, -60, 160, 120); g.strokeStyle = K; g.lineWidth = 6; g.strokeRect(-80, -60, 160, 120); g.restore(); g.beginPath(); g.arc(hands.L[0], hands.L[1], 28, 0, TAU); g.fillStyle = '#fff'; g.fill(); g.strokeStyle = K; g.lineWidth = 8; g.stroke(); g.fillStyle = '#fff'; g.strokeStyle = K; g.lineWidth = 7; g.beginPath(); g.roundRect(hands.R[0] - 9, hands.R[1] - 62, 18, 52, 9); g.fill(); g.stroke(); }
  if (st.pose === 'point') { g.fillStyle = '#fff'; g.strokeStyle = K; g.lineWidth = 7; g.beginPath(); g.roundRect(hands.R[0], hands.R[1] - 10, 52, 18, 9); g.fill(); g.stroke(); }
  if (st.pose === 'flip') { g.fillStyle = '#fff'; g.strokeStyle = K; g.lineWidth = 7; g.beginPath(); g.roundRect(hands.R[0] - 30, hands.R[1] - 18, 32, 16, 8); g.fill(); g.stroke(); }
  // head
  const hx = 0, hy = -600, hr = 122;
  g.beginPath(); g.arc(hx, hy, hr, 0, TAU); g.fillStyle = '#dde2ef'; g.fill(); g.save(); g.clip(); g.beginPath(); g.arc(hx - 18, hy - 18, hr - 6, 0, TAU); g.fillStyle = '#ffffff'; g.fill(); g.restore();
  g.lineWidth = 11; g.strokeStyle = K; g.stroke();
  if (o.hair) { g.save(); g.beginPath(); g.arc(hx, hy, hr - 4, 0, TAU); g.clip(); g.fillStyle = o.hair; g.beginPath(); g.ellipse(hx, hy - 70, 140, 82, 0, 0, TAU); g.fill(); g.fillStyle = 'rgba(255,255,255,0.18)'; g.fillRect(hx - 6, hy - 160, 12, 80); g.restore(); g.beginPath(); g.arc(hx, hy, hr, Math.PI * 1.08, Math.PI * 1.92); g.lineWidth = 11; g.stroke(); g.beginPath(); g.moveTo(hx - hr + 6, hy - 40); g.quadraticCurveTo(hx, hy + 2 - 30, hx + hr - 6, hy - 40); g.lineWidth = 6; g.stroke(); }
  if (o.mask) { g.save(); g.beginPath(); g.arc(hx, hy, hr - 5, 0, TAU); g.clip(); g.fillStyle = '#16161e'; g.fillRect(hx - hr, hy - 40, hr * 2, 62); g.restore(); g.fillStyle = '#ffffff'; for (const ex of [-26, 54]) { g.beginPath(); g.ellipse(hx + ex, hy - 6, 24, 20, 0, 0, TAU); g.fill(); } }
  drawFace(g, st, hx, hy + (o.hair ? 12 : 0));
  drawHat(g, o, hx, hy, hr);
  g.restore(); g.restore();
  C.tex.needsUpdate = true;
}

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
    case 'lift': return { R: [80, -230 + Math.sin(a * 40) * 4], L: [-80, -230 - Math.sin(a * 40) * 4] };
    case 'push': return { R: [150, -400 + Math.sin(a * 35) * 5], L: [130, -350] };
    case 'hammer': { const k = st.hk || 0; return { R: [lerp(60, 150, k), lerp(-560, -360, k)], L: [-92, -300] }; }
    case 'shrug': return { R: [160, -420], L: [-160, -420] };
    case 'shake': return { R: [165, -360 + Math.sin(a * 14) * 18], L: [-92, -300] };
    case 'count': return { R: [70, -520], L: [-110, -400] };
    case 'paddle': { const k = Math.sin(a * 5 + (st.seed || 0)); return { R: [60 + k * 20, -330], L: [-40 + k * 20, -470] }; }
    case 'point': return { R: [170, -470], L: [-92, -300] };
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
  } else if (e === 'strain') {
    g.lineWidth = 8; for (const [x, y, s] of [[eyes[0][0], eyes[0][1], 1], [eyes[1][0], eyes[1][1], -1]]) { g.beginPath(); g.moveTo(x - 16 * s, y - 14); g.lineTo(x + 12 * s, y); g.lineTo(x - 16 * s, y + 14); g.stroke(); }
    g.fillStyle = '#fff'; g.lineWidth = 6; g.beginPath(); g.roundRect(hx + ex - 38, hy + 46, 76, 30, 10); g.fill(); g.stroke(); g.beginPath(); g.moveTo(hx + ex - 38, hy + 61); g.lineTo(hx + ex + 38, hy + 61); g.stroke(); for (let i = 1; i < 4; i++) { g.beginPath(); g.moveTo(hx + ex - 38 + i * 19, hy + 46); g.lineTo(hx + ex - 38 + i * 19, hy + 76); g.stroke(); }
    g.fillStyle = 'rgba(255,80,80,0.35)'; for (const x of [hx - 70, hx + 96]) { g.beginPath(); g.ellipse(x, hy + 30, 22, 12, 0, 0, TAU); g.fill(); }
    g.fillStyle = '#7fd0ff'; g.strokeStyle = K; g.lineWidth = 4; for (const [x, y, s] of [[hx + 120, hy - 50, 1], [hx - 108, hy - 20, 0.8]]) { g.beginPath(); g.moveTo(x, y - 22 * s); g.quadraticCurveTo(x + 14 * s, y, x, y + 10 * s); g.quadraticCurveTo(x - 14 * s, y, x, y - 22 * s); g.fill(); g.stroke(); }
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
  else if (o.hat === 'straw') { g.fillStyle = '#f0d27a'; g.beginPath(); g.ellipse(0, hy - 92, 175, 34, 0, 0, TAU); g.fill(); g.stroke(); g.beginPath(); g.ellipse(0, hy - 120, 90, 52, 0, Math.PI, 0); g.closePath(); g.fill(); g.stroke(); g.fillStyle = '#e0562a'; g.fillRect(-88, hy - 112, 176, 16); }
  else if (o.hat === 'beanie') { g.fillStyle = o.capCol; g.beginPath(); g.ellipse(0, hy - 74, 124, 74, 0, Math.PI, 0); g.closePath(); g.fill(); g.stroke(); g.fillRect(-124, hy - 82, 248, 26); g.strokeRect(-124, hy - 82, 248, 26); }
  else if (o.hat === 'flower') { for (let i = 0; i < 5; i++) { const a = i / 5 * TAU; g.fillStyle = '#ff3a6a'; g.beginPath(); g.ellipse(96 + Math.cos(a) * 22, hy - 70 + Math.sin(a) * 22, 20, 14, a, 0, TAU); g.fill(); g.stroke(); } g.fillStyle = '#ffd23f'; g.beginPath(); g.arc(96, hy - 70, 12, 0, TAU); g.fill(); }
  else if (o.hat === 'beret') { g.fillStyle = o.capCol; g.beginPath(); g.ellipse(-10, hy - 100, 130, 44, -0.12, 0, TAU); g.fill(); g.stroke(); }
}



// ------------------------------------------------------------------ choreography (animation clock A = slow-mo aware)
const A = (t) => S(t);
function path(keys) {
  const ks = keys.map(k => [A(k[0]), k[1], k[2]]); const segLen = []; let tot = 0; const cum = [0];
  for (let i = 1; i < ks.length; i++) { const d = Math.hypot(ks[i][1] - ks[i - 1][1], ks[i][2] - ks[i - 1][2]); segLen.push(d); tot += d; cum.push(tot); }
  return (a) => { if (a <= ks[0][0]) return { x: ks[0][1], z: ks[0][2], vx: 0, vz: 0, dist: 0, moving: false };
    for (let i = 1; i < ks.length; i++) if (a <= ks[i][0]) { const k = (a - ks[i - 1][0]) / (ks[i][0] - ks[i - 1][0]); const dt = ks[i][0] - ks[i - 1][0]; return { x: lerp(ks[i - 1][1], ks[i][1], k), z: lerp(ks[i - 1][2], ks[i][2], k), vx: (ks[i][1] - ks[i - 1][1]) / dt, vz: (ks[i][2] - ks[i - 1][2]) / dt, dist: cum[i - 1] + segLen[i - 1] * k, moving: segLen[i - 1] > 0.01 }; }
    const l = ks[ks.length - 1]; return { x: l[1], z: l[2], vx: 0, vz: 0, dist: tot, moving: false }; };
}
function pop(a, events, amp = 0.16) { let s = 1; for (const e of events) { const d = a - A(e); if (d >= 0 && d < 1.2) s += amp * Math.exp(-d * 7) * Math.cos(d * 26) * (d < 0.03 ? -1 : 1); } return s; }
const HITS = [13.02, 13.36, 13.74, 14.31];
function hammerK(t, off = 0) { let best = 1; for (const h of HITS) { const d = t - (h + off); if (d > -0.34 && d < 0.1) best = Math.min(best, d < 0 ? 1 - sstep(-0.34, -0.12, d) * 1 + sstep(-0.12, 0, d) : sstep(0, 0.1, d)); } return 1 - best; }
// canoe motions
const cxV = (t) => 40 + 5.2 * (t - 9.55);
const rzT = (t) => PAL.z + 26 + 3.2 * (t - 14.4);
const P_thief = path([[16.85, 18.6, 12.6], [18.35, 14.1, 9.45]]);
const P_push = path([[21.2, 19.5, 12.5], [22.2, 16.7, 8.5]]);
const BUS_T0 = 26.95, BUS_T1 = 27.41;
function heroSquash(t) { return t < BUS_T1 ? 1 : lerp(0.62, 0.72, sstep(BUS_T1, BUS_T1 + 0.3, t)); }

function charStates(t) {
  const a = A(t), o = {}; const G = (x, z) => groundAt(x, z);
  const put = (n, x, z, st) => { o[n] = { a, x, z, y: st.y ?? G(x, z), pose: 'idle', expr: 'neutral', flip: false, ...st }; };
  // A + C: hero by the big stone
  if (t < 9.6) {
    if (t < 7.15) { put('hero', 3.1, 23.4, { pose: 'point', expr: 'smirk', flip: true, squash: pop(a, [2.82], 0.12) }); put('elderA', -3.3, 23.1, { pose: 'idle', expr: 'happy' }); }
    else put('hero', 3.1, 23.4, { pose: t < 7.95 ? 'idle' : 'shrug', expr: t < 7.95 ? 'smirk' : t < 8.48 ? 'neutral' : 'worried', squash: pop(a, [7.26, 7.95, 8.48], 0.14), look: t > 8.48 ? [0, 0.5] : [0, 0] });
  }
  // D voyage
  if (t >= 9.5 && t < 12.95) { const cx = cxV(t), cz = -140; const yy = waveH(cx, cz, t, 0.35) * 0.6 + 0.45; put('vil1', cx - 1.7, cz, { y: yy, pose: 'paddle', seed: 0, expr: 'happy' }); put('vil2', cx - 0.2, cz, { y: yy, pose: 'paddle', seed: 1.6, expr: 'smirk' }); put('traderA', cx + 1.6, cz, { y: yy, pose: 'point', expr: 'happy' }); }
  // E quarry + towing
  if (t >= 12.8 && t < 14.6) { put('vil3', PAL.x + 2.75, PAL.z - 7.55, { pose: 'hammer', hk: hammerK(t), expr: 'strain', flip: true }); put('vil4', PAL.x - 2.7, PAL.z - 7.5, { pose: 'hammer', hk: hammerK(t, 0.17), expr: 'smirk' }); }
  if (t >= 14.3 && t < 16.95) { const rz = rzT(t), cz = rz + 9.5; const yy = waveH(PAL.x, cz, t, 0.35) * 0.6 + 0.45; put('vil1', PAL.x - 0.15, cz - 1.6, { y: yy, pose: 'paddle', seed: 0, expr: 'strain' }); put('vil2', PAL.x + 0.15, cz + 0.4, { y: yy, pose: 'paddle', seed: 1.7, expr: 'happy' }); }
  // F + G thief + pusher
  if (t >= 16.8 && t < 24.5) {
    const p = P_thief(a); let st = { pose: p.moving ? 'walk' : 'lift', walk: p.moving ? p.dist * 5 : null, expr: p.moving ? 'smirk' : 'strain', flip: true };
    if (t >= 21.0) { st = { pose: 'idle', expr: 'panic', squash: 0.55, flip: true }; }
    st.squash = (st.squash || 1) * pop(a, [18.4, 21.09], 0.16); put('thief', p.x, p.z, st);
    if (t >= 21.1) { const q = P_push(a); let s2 = { pose: q.moving ? 'walk' : 'push', walk: q.moving ? q.dist * 5.4 : null, expr: q.moving ? 'smirk' : 'strain', flip: true }; if (t >= 23.95) { s2 = { pose: 'idle', expr: 'shock', squash: 0.6, flip: true }; } s2.squash = (s2.squash || 1) * pop(a, [23.95], 0.18); put('pusher', q.x + (t >= 23.95 ? sstep(23.95, 24.2, t) * 0.7 : 0), q.z, s2); }
  }
  // H market
  if (t >= 24.4 && t < 28.6) {
    put('seller', -14, 11.0, { pose: t < 25.9 ? 'idle' : 'shrug', expr: t < 25.9 ? 'happy' : 'shock', squash: pop(a, [25.9], 0.16) });
    put('hero', -11.4, 14.1, { pose: t < 26.9 ? 'point' : 'idle', expr: t < 26.9 ? 'smirk' : t < BUS_T1 ? 'shock' : 'strain', flip: true, squash: heroSquash(t) * pop(a, [BUS_T1], 0.12) });
  }
  // I meeting
  if (t >= 28.4 && t < 34.7) {
    const flipK = t >= 33.1; put('traderA', -6.0, -7.6, { pose: t < 31.2 ? 'shake' : 'idle', expr: 'happy' }); put('traderB', -2.0, -7.6, { pose: t < 31.2 ? 'shake' : 'idle', expr: flipK ? 'happy' : 'smirk', flip: true });
    put('elderA', -7.9, -8.7, { expr: 'happy', squash: pop(a, [29.4, 33.1], 0.08) }); put('elderB', -0.1, -8.9, { expr: flipK ? 'shock' : 'neutral', flip: true, squash: pop(a, [33.1], 0.14) }); put('vil3', -5.4, -5.6, { expr: 'smirk' }); put('vil4', -2.6, -5.9, { expr: 'happy', flip: true });
  }
  // J storm crew
  if (t >= 34.5 && t < 36.4) { const yy = 0.45; put('traderB', STORM.x - 1.5, STORM.z + 0.3, { y: yy, pose: 'panic', expr: 'panic', parent: 'storm' }); put('vil2', STORM.x + 1.6, STORM.z + 0.3, { y: yy, pose: 'panic', expr: 'panic', flip: true, parent: 'storm' }); }
  // K beach line + L family
  if (t >= 38.4) {
    const line = [['elderA', 6.5], ['vil1', 4.6], ['traderA', 2.7], ['vil4', 0.9], ['elderB', -1.0], ['vil3', -2.9], ['traderB', -4.7], ['vil2', -6.4]];
    line.forEach(([n, x], i) => { const z = 35.6 + (i % 2) * 0.5; put(n, x, z, { pose: i % 3 === 0 ? 'point' : 'idle', expr: i % 2 ? 'happy' : 'smirk', flip: x > 0, squash: pop(a, [38.8 + i * 0.12, 39.73 + i * 0.05], 0.1) }); });
    put('dad', -9.3, 36.6, { pose: 'count', expr: 'smirk', squash: pop(a, [42.72], 0.12) }); put('mom', -10.7, 36.3, { pose: 'idle', expr: 'happy' }); put('kid', -8.2, 37.0, { pose: 'cheer', expr: 'happy', scale: 0.68, seed: 2 });
  }
  return o;
}

// ------------------------------------------------------------------ camera: shots (each a continuous move), joined by whip / flash transitions
const SHOTS = [];
let CUR = null;
function SHOT(t0, t1, tr) { CUR = { t0, t1, tr, keys: [] }; SHOTS.push(CUR); }
function K(t, p, look, o = {}) { CUR.keys.push({ t, p: V(...p), look: V(...look), ...o }); }
// A: rush over the sea to the island, low-angle reveal of the giant stone wheel
SHOT(0, 3.75, { type: 'whip', axis: 'pitch', dir: -1 });
K(0.0, [1.5, 1.1, 96], [0, 2.4, 22], { fov: 58, ap: 2 });
K(1.0, [1.2, 1.15, 70], [0, 2.4, 22]);
K(1.9, [0.9, 1.6, 45], [0, 2.4, 22], { fov: 56 });
K(2.55, [1.6, 1.5, 31], [0.6, 2.6, 22], { fov: 52, ap: 4, roll: -2 });
K(3.3, [-1.6, 0.95, 27.0], [0.6, 2.9, 22], { fov: 48, ap: 6, roll: 2 });
K(3.75, [-2.1, 1.0, 26.4], [0.2, 2.6, 22], { fov: 48, ap: 6, roll: 0 });
// B: dive to the richest stone on the sea floor
SHOT(3.75, 7.15, { type: 'whip', axis: 'pitch', dir: 1 });
K(3.75, [-2.2, -2.2, 64.0], [-2.6, -10, 70], { fov: 56, ap: 2 });
K(4.4, [-2.6, -7.6, 67.0], [-4, -12.6, 78], { fov: 54, ap: 4 });
K(4.95, [-3.1, -10.4, 71.6], [-4, -13, 80], { fov: 50, ap: 6 });
K(6.0, [0.8, -11.0, 74.8], [-4, -13.1, 80], { fov: 48, ap: 7, roll: -3 });
K(7.15, [2.6, -11.5, 79.0], [-4, -13.1, 80], { fov: 46, ap: 7, roll: 0 });
// C: ECU "Easy." -> pull back, empty pockets "Yap had no metal"
SHOT(7.15, 9.55, { type: 'whip', axis: 'yaw', dir: 1 });
K(7.15, [3.15, 2.0, 25.3], [3.1, 3.2, 23.4], { fov: 40, ap: 9 });
K(7.45, [3.2, 2.6, 24.45], [3.12, 2.62, 23.4], { fov: 36, ap: 12 });
K(7.95, [3.28, 2.58, 24.5], [3.12, 2.62, 23.4], { fov: 36, ap: 12 });
K(8.45, [4.7, 1.8, 28.2], [2.9, 1.8, 23.4], { fov: 46, ap: 5, roll: -2 });
K(9.55, [4.3, 1.7, 27.2], [3.0, 1.8, 23.4], { fov: 44, ap: 6, roll: 0 });
// D: voyage — low tracking with the outrigger canoe, crane up to the open ocean
SHOT(9.55, 12.85, { type: 'whip', axis: 'yaw', dir: 1 });
K(9.55, [cxV(9.55) - 8.5, 0.9, -145.8], [cxV(9.55), 1.4, -140], { fov: 54, ap: 3 });
K(10.4, [cxV(10.4) - 4.8, 0.75, -144.6], [cxV(10.4) + 0.4, 1.4, -140], { fov: 50, ap: 5, roll: 2 });
K(11.25, [cxV(11.25) - 2.4, 1.3, -144.9], [cxV(11.25) + 0.6, 1.6, -140], { fov: 48, ap: 6, roll: 0 });
K(12.5, [cxV(12.5) - 1, 8.0, -152], [cxV(12.5) + 2, 0, -138], { fov: 58, ap: 2 });
K(12.85, [cxV(12.85) - 0.8, 8.6, -152.5], [cxV(12.85) + 2.4, 0, -138], { fov: 60, ap: 2 });
// E: Palau quarry, hammer strikes, then fly through the towed stone's hole
SHOT(12.85, 16.85, { type: 'whip', axis: 'yaw', dir: -1 });
K(12.85, [PAL.x + 6.5, 1.2, PAL.z + 0.5], [PAL.x + 1, 2.1, PAL.z - 8], { fov: 52, ap: 4 });
K(13.6, [PAL.x + 4.6, 0.75, PAL.z - 3.2], [PAL.x + 1.6, 2.3, PAL.z - 8], { fov: 48, ap: 6, roll: 3 });
K(14.25, [PAL.x + 3.6, 2.35, PAL.z - 5.0], [PAL.x + 2.6, 2.4, PAL.z - 7.4], { fov: 42, ap: 10, roll: 0 });
K(14.75, [PAL.x + 2.2, 3.0, PAL.z + 4], [PAL.x, 2.5, rzT(14.75)], { fov: 54, ap: 3, roll: -4 });
K(15.25, [PAL.x + 0.15, 2.5, rzT(15.25) - 4.0], [PAL.x, 2.45, rzT(15.25) + 6], { fov: 56, ap: 2, roll: 0 });
K(15.65, [PAL.x, 2.45, rzT(15.65)], [PAL.x, 2.4, rzT(15.65) + 8], { fov: 58, ap: 2 });
K(16.15, [PAL.x - 0.2, 2.3, rzT(16.15) + 3.6], [PAL.x, 1.4, rzT(16.15) + 10], { fov: 54, ap: 4 });
K(16.85, [PAL.x - 1.4, 2.2, rzT(16.85) + 5.4], [PAL.x, 1.4, rzT(16.85) + 10], { fov: 52, ap: 5 });
// F + G: thief can't lift it; pusher can't roll it
SHOT(16.85, 24.45, { type: 'whip', axis: 'yaw', dir: 1 });
K(16.85, [21.5, 1.3, 16.0], [17.5, 1.6, 11.0], { fov: 52, ap: 4 });
K(17.9, [18.2, 0.85, 14.4], [15.6, 1.5, 10.2], { fov: 50, ap: 6, roll: 2 });
K(18.4, [16.4, 1.2, 13.0], [14.2, 1.7, 9.5], { fov: 48, ap: 6 });
K(18.95, [14.6, 2.25, 11.15], [14.1, 2.35, 9.45], { fov: 38, ap: 12, roll: 0 });
K(20.0, [15.6, 0.85, 11.8], [14.1, 1.9, 9.3], { fov: 44, ap: 8, roll: 3 });
K(21.0, [13.0, 0.8, 12.0], [14.0, 1.6, 9.3], { fov: 46, ap: 7, roll: -2 });
K(21.9, [12.2, 1.6, 15.0], [14.5, 1.5, 9.4], { fov: 50, ap: 5, roll: 0 });
K(23.0, [19.6, 0.75, 12.3], [16.3, 1.5, 8.6], { fov: 48, ap: 6 });
K(24.45, [18.4, 1.05, 11.0], [16.2, 1.2, 8.6], { fov: 46, ap: 7 });
// H: market — coconut product POV, then the bus on the head
SHOT(24.45, 28.5, { type: 'whip', axis: 'yaw', dir: -1 });
K(24.45, [-12.4, 2.55, 14.3], [-14.2, 2.15, 12.5], { fov: 42, ap: 11 });
K(25.0, [-12.8, 2.45, 13.9], [-14.3, 2.15, 12.5], { fov: 40, ap: 12 });
K(25.6, [-10.6, 1.7, 18.8], [-12.4, 1.8, 13.2], { fov: 48, ap: 5, roll: 2 });
K(26.5, [-10.2, 1.4, 19.4], [-11.6, 2.0, 14.1], { fov: 48, ap: 5, roll: 0 });
K(27.4, [-10.9, 2.5, 21.2], [-11.4, 3.0, 14.1], { fov: 50, ap: 5 });
K(28.5, [-13.6, 1.8, 19.4], [-11.4, 2.4, 14.1], { fov: 48, ap: 6, roll: -2 });
// I: meeting — orbit, stone never moved, only the name changed (board ECU)
SHOT(28.5, 34.55, { type: 'flash' });
K(28.5, [-4.0, 7.6, 0.5], [-4, 1.5, -9], { fov: 54, ap: 2 });
K(29.6, [-7.6, 2.4, -2.6], [-4, 1.6, -8.5], { fov: 50, ap: 5, roll: 3 });
K(30.7, [-0.3, 1.7, -3.2], [-4, 1.8, -9], { fov: 48, ap: 6, roll: -2 });
K(31.3, [-1.8, 1.6, -4.6], [-4, 1.8, -9.4], { fov: 46, ap: 6, roll: 0 });
K(32.7, [-3.7, 1.7, -6.5], [-4, 1.7, -9.5], { fov: 44, ap: 8 });
K(33.15, [-4.0, 1.75, -7.95], [-4, 1.75, -9.33], { fov: 40, ap: 10 });
K(34.55, [-4.35, 1.8, -7.5], [-4, 1.75, -9.33], { fov: 42, ap: 9 });
// J: storm — stone slides off, sinks into darkness
SHOT(34.55, 38.55, { type: 'whip', axis: 'pitch', dir: 1 });
K(34.55, [STORM.x + 8, 3.0, STORM.z + 8], [STORM.x, 1.6, STORM.z], { fov: 56, ap: 2, roll: -6 });
K(35.4, [STORM.x + 4.6, 2.0, STORM.z + 4.8], [STORM.x, 1.9, STORM.z], { fov: 50, ap: 4, roll: 5 });
K(35.95, [STORM.x + 1.8, 0.4, STORM.z + 0.8], [STORM.x, -1.5, STORM.z - 3.2], { fov: 54, ap: 3, roll: -3 });
K(36.6, [STORM.x + 0.8, -3.0, STORM.z - 1.0], [STORM.x, -6.5, STORM.z - 3.4], { fov: 52, ap: 4, roll: 0 });
K(38.55, [STORM.x + 0.5, -8.4, STORM.z - 1.8], [STORM.x, -13, STORM.z - 3.4], { fov: 50, ap: 4 });
// K + L: everyone still calls it money; the family counting; fly out + dive to the stone
SHOT(38.55, 46.0, null);
K(38.55, [9.6, 1.05, 40.3], [5.0, 1.8, 35.6], { fov: 50, ap: 4 });
K(40.5, [-5.2, 1.0, 39.8], [-7.2, 1.8, 35.8], { fov: 48, ap: 5, roll: 0 });
K(41.6, [-7.8, 1.4, 39.6], [-9.0, 1.8, 36.6], { fov: 46, ap: 6 });
K(42.5, [-8.75, 2.05, 38.7], [-9.25, 2.05, 36.6], { fov: 40, ap: 10 });
K(43.3, [-8.0, 2.6, 40.4], [-6.5, 0.8, 70], { fov: 52, ap: 2, roll: -3 });
K(44.0, [-7.0, 1.7, 52.0], [-5, -1.5, 80], { fov: 56, ap: 2, roll: 0 });
K(44.8, [-5.6, -2.6, 64.0], [-4.2, -12, 79], { fov: 54, ap: 3 });
K(45.6, [-3.6, -10.2, 72.8], [-4, -13, 80], { fov: 50, ap: 6 });
K(46.0, [-3.4, -10.6, 73.6], [-4, -13.1, 80], { fov: 48, ap: 7 });

function monotone(xs, ys) {
  const n = xs.length, d = [], m = new Array(n).fill(0);
  for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]));
  for (let i = 1; i < n - 1; i++) { if (d[i - 1] * d[i] <= 0) m[i] = 0; else { const w1 = 2 * (xs[i + 1] - xs[i]) + (xs[i] - xs[i - 1]), w2 = (xs[i + 1] - xs[i]) + 2 * (xs[i] - xs[i - 1]); m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]); } }
  if (n > 1) { m[0] = d[0] * 0.5; m[n - 1] = d[n - 2] * 0.5; }
  return (x) => { if (x <= xs[0]) return ys[0]; if (x >= xs[n - 1]) return ys[n - 1]; let i = 0; while (x > xs[i + 1]) i++; const h = xs[i + 1] - xs[i], s = (x - xs[i]) / h; const h00 = 2 * s ** 3 - 3 * s ** 2 + 1, h10 = s ** 3 - 2 * s ** 2 + s, h01 = -2 * s ** 3 + 3 * s ** 2, h11 = s ** 3 - s ** 2; return h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]; };
}
const CH_KEYS = ['x', 'y', 'z', 'yawR', 'pitchR', 'roll', 'fov', 'ap', 'focus'];
for (const sh of SHOTS) { let prevYaw = null, last = { roll: 0 }; for (const k of sh.keys) { const d = k.look.clone().sub(k.p); k.focus = d.length(); d.normalize(); let yaw = Math.atan2(d.x, d.z); if (prevYaw !== null) { while (yaw - prevYaw > Math.PI) yaw -= TAU; while (yaw - prevYaw < -Math.PI) yaw += TAU; } k.yawR = yaw; prevYaw = yaw; k.pitchR = Math.asin(clamp(d.y, -1, 1)); for (const c of ['fov', 'ap', 'roll']) { if (k[c] === undefined) k[c] = last[c]; last[c] = k[c]; } }
  sh.chan = {}; for (const c of CH_KEYS) sh.chan[c] = monotone(sh.keys.map(k => k.t), sh.keys.map(k => c === 'x' ? k.p.x : c === 'y' ? k.p.y : c === 'z' ? k.p.z : k[c])); }
const WHIP_T = 0.2, WHIP_A = 1.25;
function shotAt(t) { for (let i = SHOTS.length - 1; i >= 0; i--) if (t >= SHOTS[i].t0) return i; return 0; }
function camAt(t) {
  const i = shotAt(t), sh = SHOTS[i]; const c = {}; for (const k of CH_KEYS) c[k] = sh.chan[k](clamp(t, sh.t0, sh.t1));
  let yawO = 0, pitO = 0, flash = 0, rollO = 0;
  const end = sh.tr, prev = i > 0 ? SHOTS[i - 1].tr : null;
  const apply = (tr, k) => { if (!tr) return; if (tr.type === 'flash') { flash = Math.max(flash, 1 - Math.abs(k)); return; } const off = tr.dir * WHIP_A * (k < 0 ? Math.pow(1 + k, 3) : -Math.pow(1 - k, 3)); if (tr.axis === 'yaw') yawO += off; else pitO += off * 0.7; rollO += off * 0.12; };
  if (end && t > sh.t1 - WHIP_T) apply(end, -((sh.t1 - t) / WHIP_T)); // k in (-1,0]: wind-up into the seam
  if (prev && t < sh.t0 + WHIP_T) apply(prev, (t - sh.t0) / WHIP_T);  // k in [0,1): settle after the seam
  const shk = 0.6 + 0.4 * Math.abs(pnoise(t, 5, 3, 9));
  const p = V(c.x + pnoise(t, 11) * 0.014 * shk, c.y + pnoise(t, 12) * 0.014 * shk, c.z + pnoise(t, 13) * 0.012 * shk);
  const yaw = c.yawR + yawO + pnoise(t, 14, 15, 50) * 0.004, pitch = clamp(c.pitchR + pitO + pnoise(t, 15, 15, 50) * 0.003, -1.5, 1.5);
  const dir = V(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
  return { p, dir, roll: (c.roll || 0) * Math.PI / 180 + rollO, fov: c.fov, ap: c.ap, focus: c.focus, flash, shot: i };
}
function applyCam(cs) { camera.position.copy(cs.p); camera.up.set(0, 1, 0); camera.lookAt(cs.p.clone().add(cs.dir)); camera.rotateZ(cs.roll); camera.fov = cs.fov; camera.updateProjectionMatrix(); camera.updateMatrixWorld(); }

// ------------------------------------------------------------------ environment per shot (day / storm / underwater)
const ENV = {
  day: { sky: ['#2f7fe6', '#bfe6ff'], fog: ['#a9dcff', 0.0045], sun: 2.1, hemi: 0.75, amp: 0.35, deep: '#0a4f9a', shallow: '#1fd6d0', exp: 0.72, tint: [1, 0.97, 0.92] },
  storm: { sky: ['#1a2238', '#3a4660'], fog: ['#2a3550', 0.02], sun: 0.5, hemi: 0.6, amp: 1.5, deep: '#0a2238', shallow: '#1a4a5a', exp: 1.15, tint: [0.75, 0.82, 1.0] },
};
const UW = { day: ['#0f6f8a', 0.055], storm: ['#06202c', 0.09] };
const tmpC = new THREE.Color();
function setEnv(t, cs) {
  const E = cs.shot === 8 ? ENV.storm : ENV.day; const st = E === ENV.storm;
  const wy = waveH(cs.p.x, cs.p.z, A(t), E.amp); const under = cs.p.y < wy - 0.05;
  skyMat.uniforms.uTop.value.set(E.sky[0]); skyMat.uniforms.uHor.value.set(E.sky[1]); skyMat.uniforms.uUnder.value = under ? 1 : 0;
  if (under) { const u = st ? UW.storm : UW.day; scene.fog.color.set(u[0]); scene.fog.density = u[1]; } else { scene.fog.color.set(E.fog[0]); scene.fog.density = E.fog[1]; }
  sun.intensity = E.sun * (under ? 0.6 : 1); hemi.intensity = E.hemi; if (under) hemi.color.set('#7fe8ff'); else hemi.color.set('#bfe4ff');
  oceanMat.uniforms.uAmp.value = E.amp; oceanMat.uniforms.uDeep.value.set(E.deep); oceanMat.uniforms.uShallow.value.set(E.shallow); oceanMat.uniforms.uSky.value.set(E.sky[1]); oceanMat.uniforms.uUnder.value = under ? 1 : 0; oceanMat.uniforms.fogD.value = scene.fog.density; oceanMat.uniforms.uSunC.value.setRGB(...(st ? [0.3, 0.35, 0.45] : [1, 0.96, 0.84]));
  causticM.opacity = causticM2.opacity = st ? 0.1 : 1;
  for (const C of Object.values(chars)) { C.mat.uniforms.fogD.value = scene.fog.density; C.mat.uniforms.uTint.value.setRGB(...(under ? [0.6, 0.85, 0.95] : E.tint)); C.mat.uniforms.uRimC.value.set(st ? '#9fb8ff' : '#fff0b0'); }
  let lightning = 0; if (st) for (const L of [34.62, 36.25, 37.6]) { const d = t - L; if (d > 0 && d < 0.35) lightning = Math.max(lightning, Math.exp(-d * 14) * (1 + 0.5 * Math.sin(d * 90))); }
  boltM.opacity = lightning > 0.15 && !under ? 1 : 0; bolt.visible = boltM.opacity > 0;
  return { under, storm: st, lightning, exp: E.exp };
}


// ------------------------------------------------------------------ particles: spray, chips, bubbles, rain, plankton
const MAXP = 5000;
const pGeo = new THREE.BufferGeometry(); const pPos = new Float32Array(MAXP * 3), pCol = new Float32Array(MAXP * 4), pSize = new Float32Array(MAXP);
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3)); pGeo.setAttribute('color', new THREE.BufferAttribute(pCol, 4)); pGeo.setAttribute('size', new THREE.BufferAttribute(pSize, 1));
const pMat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uScale: { value: H * 0.5 } },
  vertexShader: 'attribute vec4 color; attribute float size; uniform float uScale; varying vec4 vC; varying float vSoft; void main(){ vec4 mv = modelViewMatrix*vec4(position,1.); float d = -mv.z; gl_PointSize = clamp(size*uScale/d, 1., 160.); vSoft = clamp(1.2/d,0.,1.); vC = color; vC.a *= clamp(d*2.-0.2,0.,1.) / (1.+ max(0., 0.6/d - 0.2)); gl_Position = projectionMatrix*mv; }',
  fragmentShader: 'varying vec4 vC; varying float vSoft; void main(){ vec2 p = gl_PointCoord*2.-1.; float r = dot(p,p); if(r>1.) discard; float a = mix(1.-r, smoothstep(1.,0.6,r)*0.7, vSoft); gl_FragColor = vec4(vC.rgb*vC.a*a,1.); }' });
const points = new THREE.Points(pGeo, pMat); points.frustumCulled = false; points.renderOrder = 11; scene.add(points);
const rainGeo = new THREE.BufferGeometry(); const NR = 1800; const rainPos = new Float32Array(NR * 6); rainGeo.setAttribute('position', new THREE.BufferAttribute(rainPos, 3));
const rain = new THREE.LineSegments(rainGeo, new THREE.LineBasicMaterial({ color: new THREE.Color(0.55, 0.62, 0.8), transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false })); rain.frustumCulled = false; scene.add(rain);
const RR = rng(4242); const rainSeed = Array.from({ length: NR }, () => [RR() * 2 - 1, RR(), RR() * 2 - 1]);

// ------------------------------------------------------------------ world update for time t
const tmpM = new THREE.Matrix4(), tmpQ = new THREE.Quaternion(), tmpS = new THREE.Vector3(), tmpE = new THREE.Euler();
const SLATE_IMG = T.slate.image;
function floatObj(o, x, z, t, amp, heading, rollK = 1) { const a = A(t); const y = waveH(x, z, a, amp); const dx = waveH(x + 1.5, z, a, amp) - waveH(x - 1.5, z, a, amp), dz = waveH(x, z + 1.5, a, amp) - waveH(x, z - 1.5, a, amp); o.position.set(x, y * 0.85 + 0.05, z); o.rotation.set(0, 0, 0); o.rotation.order = 'YXZ'; o.rotation.y = heading; const c = Math.cos(heading), s = Math.sin(heading); const along = (dx * c - dz * s) / 3, across = (dx * s + dz * c) / 3; o.rotation.z = Math.atan(along) * 0.8; o.rotation.x = Math.atan(across) * 0.8 * rollK; }
function updateWorld(t, cs) {
  const a = A(t);
  const env = setEnv(t, cs);
  oceanMat.uniforms.uT.value = a; ocean.position.set(Math.round(cs.p.x / 4) * 4, 0, Math.round(cs.p.z / 4) * 4);
  sky.position.copy(cs.p); clouds.position.set(cs.p.x, 0, cs.p.z);
  sun.target.position.copy(cs.p).addScaledVector(cs.dir, 14); sun.target.position.y = 0; sun.position.copy(sun.target.position).addScaledVector(SUN, -90); sun.target.updateMatrixWorld();
  for (const m of shaftMats) m.uniforms.uT.value = a * 2;
  T.caustic.offset.set(a * 0.011, a * 0.007); causticM2.map.offset.set(-a * 0.009, a * 0.012);
  for (const f of fronds) f.f.rotation.z = f.base + Math.sin(a * 1.3 + f.ph) * 0.05;
  for (const k of kelps) k.m.rotation.z = Math.sin(a * 0.9 + k.ph) * 0.12;
  fishes.forEach((f, i) => { const ang = a * f.sp + f.ph; f.m.position.set(f.c.x + Math.cos(ang) * f.r, f.y + Math.sin(a * 1.4 + i) * 0.3, f.c.z + Math.sin(ang) * f.r); f.m.rotation.y = -ang + (f.sp > 0 ? 0 : Math.PI) + Math.PI / 2 * Math.sign(f.sp); f.m.visible = true; });
  // canoes
  floatObj(canoeV, cxV(t), -140, t, 0.35, 0);
  const rz = rzT(t); floatObj(canoeT, PAL.x, rz + 9.5, t, 0.35, -Math.PI / 2); floatObj(raft, PAL.x, rz, t, 0.35, 0); raft.position.y -= 0.05;
  { const p0 = V(PAL.x, 0.6, rz + 1.6), p1 = V(PAL.x, 0.55, rz + 9.5 - 3.0); rope.position.copy(p0).add(p1).multiplyScalar(0.5); rope.scale.set(1, p0.distanceTo(p1), 1); rope.quaternion.setFromUnitVectors(V(0, 1, 0), p1.clone().sub(p0).normalize()); }
  floatObj(canoeS, STORM.x, STORM.z, t, 1.5, 0.3, 2.2); canoeS.rotation.x += Math.sin(a * 2.3) * 0.12;
  { const k = sstep(35.55, 35.95, t); const sinkA = Math.max(0, a - A(35.95)); stormStone.position.set(0, 2.2 - k * 2.6 - sinkA * 3.4, -k * 3.0); stormStone.rotation.set(k * 0.6 + sinkA * 0.25, 0, k * 0.4); stormStone.visible = t < 38.4; }
  // bus gag
  bus.visible = t >= BUS_T0 && t < 28.6; if (bus.visible) { const hx = -11.4, hz = 14.1, gy = groundAt(hx, hz); const top = gy + 2.32 * heroSquash(t); const k = clamp((t - BUS_T0) / (BUS_T1 - BUS_T0), 0, 1); bus.position.set(hx + 0.2, lerp(top + 14, top + 0.32, k * k), hz); bus.rotation.set(0, 0.12, (1 - k) * 0.25 + (t > BUS_T1 ? Math.sin((t - BUS_T1) * 18) * 0.04 * Math.exp(-(t - BUS_T1) * 4) : 0)); }
  // name board flips at 33.1
  nameBoardM.map = t < 33.1 ? boardA : boardB; { const s = pop(a, [33.1], 0.25); nameBoard.scale.set(s, s, 1); }
  // characters
  const states = charStates(t);
  const camRight = V(1, 0, 0).applyQuaternion(camera.quaternion);
  const sunScreen = V().copy(SUN).negate().applyQuaternion(camera.quaternion.clone().invert());
  for (const [n, C] of Object.entries(chars)) {
    const st = states[n]; if (!st) { C.hide(); continue; }
    C.mesh.visible = true; C.sh.visible = !st.noShadow;
    drawChar(C, st);
    let px = st.x, py = st.y, pz = st.z;
    if (st.parent === 'storm') { const v = V(st.x - STORM.x, st.y, st.z - STORM.z).applyEuler(canoeS.rotation).add(canoeS.position); px = v.x; py = v.y; pz = v.z; }
    C.mesh.position.set(px, py, pz); const sc = st.scale || 1; C.mesh.scale.setScalar(sc);
    const to = camera.position.clone().sub(C.mesh.position); const yaw = Math.atan2(to.x, to.z); const pitch = Math.atan2(to.y - 1.4, Math.hypot(to.x, to.z));
    C.mesh.rotation.set(0, 0, 0); C.mesh.rotation.order = 'YXZ'; C.mesh.rotation.y = yaw; C.mesh.rotation.x = -clamp(pitch, -1.2, 1.2) * 0.35;
    C.mat.uniforms.uOp.value = st.op ?? 1;
    const rd = new THREE.Vector2(sunScreen.x, sunScreen.y); if (rd.lengthSq() < 1e-6) rd.set(1, 0); rd.normalize(); if (st.flip) rd.x *= -1; C.mat.uniforms.uRim.value.copy(rd);
    const s = (st.squash || 1); C.sh.position.set(px, groundAt(px, pz) > py - 0.3 ? py + 0.02 : py + 0.02, pz); C.sh.scale.set(1.5 * sc / Math.sqrt(s), 1, 0.65 * sc); C.sh.material.opacity = 0.5 * (st.op ?? 1); if (st.y !== undefined && Math.abs(st.y - groundAt(px, pz)) > 0.3 && !st.parent) C.sh.visible = false; if (st.parent) C.sh.visible = false;
  }
  // particles
  let n = 0;
  const put = (x, y, z, r, g, b, al, s) => { if (n >= MAXP) return; pPos[n * 3] = x; pPos[n * 3 + 1] = y; pPos[n * 3 + 2] = z; pCol[n * 4] = r; pCol[n * 4 + 1] = g; pCol[n * 4 + 2] = b; pCol[n * 4 + 3] = al; pSize[n] = s; n++; };
  const R = rng(1234);
  if (env.under) { for (let i = 0; i < 600; i++) { const x = cs.p.x + (R() - .5) * 24, z = cs.p.z + (R() - .5) * 24, y0 = R(); const y = SEABED + ((y0 * 14 + a * (0.15 + R() * 0.2)) % 14); put(x + Math.sin(a + i) * 0.3, y, z, 0.7, 0.95, 1.0, 0.25 + R() * 0.3, 0.015 + R() * 0.02); }
    for (let i = 0; i < 90; i++) { const bx = (cs.shot === 8 ? STORM.x : SEA_STONE.x) + (R() - .5) * 8, bz = (cs.shot === 8 ? STORM.z - 3 : SEA_STONE.z) + (R() - .5) * 8; const ph = R(); const y = SEABED + ((ph * 14 + a * (1.2 + R())) % 14); put(bx + Math.sin(a * 3 + i) * 0.2, y, bz, 0.85, 1.0, 1.0, 0.6, 0.04 + R() * 0.05); } }
  // sea spray around moving canoes + camera rush in shot A
  const spray = (cx, cz, cnt, spread, inten) => { for (let i = 0; i < cnt; i++) { const ph = (R() + a * (0.8 + R())) % 1; const x = cx + (R() - .5) * spread, z = cz + (R() - .5) * spread; put(x, ph * 1.4 + waveH(x, z, a, 0.35), z, 1, 1, 1, (1 - ph) * inten, 0.02 + R() * 0.04); } };
  if (cs.shot === 3) { spray(cxV(t) + 2.6, -140, 260, 2.5, 0.7); spray(cxV(t) - 2.8, -140.4, 160, 3, 0.5); }
  if (cs.shot === 4 && t > 14.4) { spray(PAL.x, rz + 12.4, 200, 2.5, 0.6); spray(PAL.x, rz + 1.8, 160, 2.5, 0.5); }
  if (cs.shot === 0 && t < 2.0) spray(cs.p.x, cs.p.z - 3, 260, 6, 0.5);
  if (cs.shot === 8 && !env.under) { spray(STORM.x + 2.6, STORM.z, 300, 5, 0.8); if (t > 35.8 && t < 36.6) { const age = t - 35.8; for (let i = 0; i < 400; i++) { const th = R() * TAU, sp = 1 + R() * 3; put(STORM.x + Math.cos(th) * sp * age, 0.3 + (sp * 2 * age - 6 * age * age) * R(), STORM.z - 3 + Math.sin(th) * sp * age, 1, 1, 1, (1 - age / 0.8) * 0.9, 0.03 + R() * 0.04); } } }
  // stone chips on hammer hits
  if (t > 12.9 && t < 15.0) for (const h of HITS) for (const off of [0, 0.17]) { const age = a - A(h + off); if (age < 0 || age > 0.9) continue; const cx = PAL.x + (off ? -2.0 : 2.05), cz = PAL.z - 8.1; for (let i = 0; i < 70; i++) { const vx = (R() - .5) * 3, vy = 1 + R() * 3, vz = 0.5 + R() * 1.5; put(cx + vx * age, 1.9 + vy * age - 4.9 * age * age, cz + vz * age, 1, 0.95, 0.85, (1 - age / 0.9), 0.025 + R() * 0.03); } }
  // dust when the thief / pusher hit the ground, bus lands, name flips (sparkle)
  for (const [T0, x, z] of [[21.05, 14.0, 9.6], [23.95, 17.0, 8.6], [BUS_T1, -11.2, 14.2]]) { const age = t - T0; if (age < 0 || age > 1.2) continue; for (let i = 0; i < 160; i++) { const th = R() * TAU, sp = 0.6 + R() * 2.2; put(x + Math.cos(th) * sp * age, groundAt(x, z) + 0.1 + R() * age * 0.8, z + Math.sin(th) * sp * age, 0.95, 0.85, 0.6, (1 - age / 1.2) * 0.55, 0.05 + R() * 0.06); } }
  { const age = a - A(33.1); if (age > 0 && age < 1.5) for (let i = 0; i < 120; i++) { const th = R() * TAU, r = 0.6 + age * (0.8 + R()); put(-4 + Math.cos(th) * r * 1.2, 1.75 + Math.sin(th) * r * 0.7, -9.2, 1, 0.85, 0.3, (1 - age / 1.5), 0.02 + R() * 0.02); } }
  for (let i = n; i < MAXP; i++) pCol[i * 4 + 3] = 0, pPos[i * 3 + 1] = -999;
  pGeo.attributes.position.needsUpdate = true; pGeo.attributes.color.needsUpdate = true; pGeo.attributes.size.needsUpdate = true; pGeo.setDrawRange(0, Math.max(1, n));
  // rain
  rain.visible = env.storm && !env.under; if (rain.visible) { for (let i = 0; i < NR; i++) { const [rx, ry, rz2] = rainSeed[i]; const y = ((ry * 20 - a * 18) % 20 + 20) % 20 - 2; const x = cs.p.x + rx * 14 + cs.dir.x * 8, z = cs.p.z + rz2 * 14 + cs.dir.z * 8; rainPos.set([x, y + cs.p.y - 6, z, x - 0.12, y + cs.p.y - 6 + 0.9, z - 0.05], i * 6); } rainGeo.attributes.position.needsUpdate = true; }
  return env;
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
const brightMat = new THREE.ShaderMaterial({ vertexShader: VS_Q, uniforms: { tIn: { value: accRT.texture }, uTex: { value: new THREE.Vector2(1 / W, 1 / H) } }, fragmentShader: `uniform sampler2D tIn; uniform vec2 uTex; varying vec2 vUv; void main(){ vec3 s = vec3(0.); for(int j=-1;j<=1;j++) for(int i=-1;i<=1;i++) s += texture2D(tIn, vUv + vec2(float(i),float(j))*uTex*1.5).rgb; s/=9.; float l = dot(s, vec3(0.3,0.59,0.11)); gl_FragColor = vec4(s*smoothstep(1.6,3.2,l), 1.); }` });
const blurMat = new THREE.ShaderMaterial({ vertexShader: VS_Q, uniforms: { tIn: { value: null }, uDir: { value: new THREE.Vector2() } }, fragmentShader: `uniform sampler2D tIn; uniform vec2 uDir; varying vec2 vUv; void main(){ vec3 s = vec3(0.); float ws = 0.; for(int i=-8;i<=8;i++){ float w = exp(-float(i*i)/24.); s += texture2D(tIn, vUv + uDir*float(i)).rgb*w; ws += w; } gl_FragColor = vec4(s/ws,1.); }` });
const capCanvas = document.createElement('canvas'); capCanvas.width = W; capCanvas.height = H; const capG = capCanvas.getContext('2d');
const capTex = new THREE.CanvasTexture(capCanvas); capTex.colorSpace = THREE.NoColorSpace; capTex.flipY = true;
const finalMat = new THREE.ShaderMaterial({ vertexShader: VS_Q, uniforms: { tIn: { value: accRT.texture }, tBloom: { value: bloomA.texture }, tCap: { value: capTex }, uT: { value: 0 }, uExp: { value: 1 }, uRes: { value: new THREE.Vector2(W, H) }, uFlash: { value: 0 }, uUnder: { value: 0 } },
  fragmentShader: `uniform sampler2D tIn, tBloom, tCap; uniform float uT, uExp, uFlash, uUnder; uniform vec2 uRes; varying vec2 vUv;
  vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.,1.); }
  float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)))*43758.5453); }
  void main(){ vec2 d = (vUv-0.5);
    vec3 c = vec3(texture2D(tIn, vUv - d*0.0025).r, texture2D(tIn, vUv).g, texture2D(tIn, vUv + d*0.0025).b);
    c += texture2D(tBloom, vUv).rgb*0.45;
    c *= uExp*1.25; c = aces(c);
    float l = dot(c, vec3(0.299,0.587,0.114)); c = mix(vec3(l), c, 1.32); c = mix(c, smoothstep(0.,1.,c), 0.35);
    c = mix(c, c*vec3(0.86,0.95,1.18), (1.-smoothstep(0.,0.45,l))*0.45); c = mix(c, c*vec3(1.08,1.0,0.86), smoothstep(0.5,1.,l)*0.35);
    float v = smoothstep(0.95, 0.25, length(d*vec2(1.0,0.82))); c *= mix(0.62, 1.0, v);
    c = mix(c, c*vec3(0.75,1.02,1.08), uUnder*0.5);
    c = pow(c, vec3(1./2.2)); c = mix(c, vec3(1.0,0.98,0.94), clamp(uFlash,0.,1.));
    c += (h(vUv*uRes + fract(uT)*91.7) - 0.5)*0.028;
    vec4 cap = texture2D(tCap, vUv); c = mix(c, cap.rgb, cap.a);
    gl_FragColor = vec4(c, 1.); }` });

// captions: 1–3 word pop-in chunks
const GOLDW = /^(yap|giant|stone|stones|richest|sea|metal|four|400|palau|limestone|canoes|tons|coconut|bus|name|storm|money|nobody|real|find)/i;
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
    const cs = camAt(ts); applyCam(cs); const env = updateWorld(ts, cs); if (i === 0) { drawCaption(t); finalMat.uniforms.uFlash.value = cs.flash * 0.9 + env.lightning * 0.35; finalMat.uniforms.uExp.value = env.exp * (1 + env.lightning * 1.2); finalMat.uniforms.uUnder.value = env.under ? 1 : 0; }
    renderer.setRenderTarget(sceneRT); renderer.setClearColor(scene.fog.color, 1); renderer.clear(); renderer.render(scene, camera);
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
window.renderFrame = (f) => { const t = frameTime(f); const frozen = f / FPS !== t; const n = renderAt(t, frozen); renderer.readRenderTargetPixels(outRT, 0, 0, W, H, pix); return { n, data: b64(pix) }; };
window.renderTime = (t) => { renderAt(t, false); renderer.readRenderTargetPixels(outRT, 0, 0, W, H, pix); return b64(pix); };
window.camTrack = () => { const out = []; for (let f = 0; f <= DUR * FPS; f++) { const t = frameTime(f); const c = camAt(t); out.push([t, c.p.x, c.p.y, c.p.z, Math.atan2(c.dir.x, c.dir.z), Math.asin(c.dir.y), c.fov, c.shot, c.p.y < waveH(c.p.x, c.p.z, A(t), c.shot === 8 ? 1.5 : 0.35) ? 1 : 0]); } return out; };
window.READY = true;
window.__dbg = { dofMat, sceneRT, accRT, outRT, points, sky, clouds, ocean, shaftMats, causticM, causticM2, finalMat, scene, rain, bloomA, renderer };
