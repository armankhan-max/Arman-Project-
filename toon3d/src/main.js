import * as THREE from '/node_modules/three/build/three.module.js';
import { drawChar, handPos } from './char.js';

const q = new URLSearchParams(location.search);
const SC = parseFloat(q.get('scale') || '1');
const W = Math.round(1080 * SC), H = Math.round(1920 * SC);
export const DUR = 20.5, FPS = 30;

// ---------- helpers ----------
const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const seg = (t, a, b) => cl((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const EASE = {
  lin: k => k,
  io: k => k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2,
  out: k => 1 - Math.pow(1 - k, 4),
  back: k => { const c = 2.2; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
};
const pop = (t, t0, d = 0.28) => t < t0 ? 0 : EASE.back(seg(t, t0, t0 + d));

const gl = document.getElementById('gl'); gl.width = W; gl.height = H;
const out = document.getElementById('out'); out.width = W; out.height = H;
const o2 = out.getContext('2d');
const renderer = new THREE.WebGLRenderer({ canvas: gl, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.localClippingEnabled = true;
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x232a6e, 22, 75);
const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 300);

function ctex(w, h, fn) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; fn(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
const grad = new THREE.DataTexture(new Uint8Array([70, 70, 70, 255, 150, 150, 150, 255, 255, 255, 255, 255]), 3, 1);
grad.minFilter = grad.magFilter = THREE.NearestFilter; grad.needsUpdate = true;
const toon = (color, o = {}) => new THREE.MeshToonMaterial({ color, gradientMap: grad, ...o });
const OUTM = new THREE.MeshBasicMaterial({ color: 0x100c1c, side: THREE.BackSide });
function ol(geo, mat, o = 0.03, shadow = true) { // toon mesh + inverted-hull ink outline
  const m = new THREE.Mesh(geo, mat); m.castShadow = shadow; m.receiveShadow = true;
  if (o > 0) {
    geo.computeBoundingBox(); const s = new THREE.Vector3(), c = new THREE.Vector3();
    geo.boundingBox.getSize(s); geo.boundingBox.getCenter(c);
    const h = new THREE.Mesh(geo, OUTM);
    h.scale.set((s.x + 2 * o) / Math.max(s.x, 1e-4), (s.y + 2 * o) / Math.max(s.y, 1e-4), (s.z + 2 * o) / Math.max(s.z, 1e-4));
    h.position.set(c.x * (1 - h.scale.x), c.y * (1 - h.scale.y), c.z * (1 - h.scale.z));
    m.add(h);
  }
  return m;
}
const box = (w, h, d, mat, o) => ol(new THREE.BoxGeometry(w, h, d), mat, o);
function put(m, x, y, z, parent = scene) { m.position.set(x, y, z); parent.add(m); return m; }
const glowTex = ctex(128, 128, (c) => {
  const g = c.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.25, 'rgba(255,255,255,.55)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  c.fillStyle = g; c.fillRect(0, 0, 128, 128);
});
function glow(color, size, x, y, z, parent = scene) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false }));
  s.scale.set(size, size, 1); return put(s, x, y, z, parent);
}

// ---------- characters as flat cards ----------
function makeChar(res = 512, tint = 0xffffff) {
  const cv = document.createElement('canvas'); cv.width = res; cv.height = res * 1.5;
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const geo = new THREE.PlaneGeometry(1.2, 1.8); geo.translate(0, 0.9 - 0.04, 0);
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: 0.08, side: THREE.DoubleSide, color: tint });
  const m = new THREE.Mesh(geo, mat); m.castShadow = true;
  m.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: tex, alphaTest: 0.5 });
  const ch = { mesh: m, cv, ctx: cv.getContext('2d'), tex, P: {}, billboard: true };
  ch.draw = (P) => { ch.P = P; drawChar(ch.ctx, cv.width, cv.height, P); tex.needsUpdate = true; };
  ch.handWorld = (side) => { const [px, py] = handPos(ch.P, side); m.updateMatrixWorld(); return m.localToWorld(new THREE.Vector3((px - 256) / 512 * 1.2, (768 - py) / 768 * 1.8 - 0.04, 0.01)); };
  return ch;
}

// ---------- world ----------
// sky
scene.add(new THREE.Mesh(new THREE.SphereGeometry(200, 32, 16), new THREE.MeshBasicMaterial({
  side: THREE.BackSide, fog: false, map: ctex(1024, 512, (c, w, h) => {
    const g = c.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#0a0b33'); g.addColorStop(0.42, '#1b2378'); g.addColorStop(0.5, '#4a3aa0'); g.addColorStop(0.56, '#262a6e'); g.addColorStop(1, '#101238');
    c.fillStyle = g; c.fillRect(0, 0, w, h);
    let s = 7; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
  })
})));
{ // crisp stars
  let s = 11; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647; const p = [];
  for (let i = 0; i < 340; i++) { const a = rnd() * Math.PI * 2, e = 0.08 + rnd() * 1.3; p.push(Math.cos(a) * Math.cos(e) * 180, Math.sin(e) * 180, Math.sin(a) * Math.cos(e) * 180); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ size: 4.5 * SC, sizeAttenuation: false, color: 0xfff6cf, fog: false })));
}
const moon = put(new THREE.Mesh(new THREE.CircleGeometry(4.2, 40), new THREE.MeshBasicMaterial({ color: 0xfff6d8, fog: false })), 30, 30, -80);
glow(0x8fa4ff, 34, 30, 30, -79);

scene.add(new THREE.HemisphereLight(0x98a6ff, 0x2a2a70, 2.1));
const moonL = new THREE.DirectionalLight(0xb9c6ff, 2.3); moonL.position.set(9, 14, 7); moonL.castShadow = true;
moonL.shadow.mapSize.set(2048, 2048); Object.assign(moonL.shadow.camera, { left: -16, right: 24, top: 18, bottom: -18, near: 1, far: 60 });
moonL.shadow.bias = -0.0015; moonL.shadow.radius = 3; scene.add(moonL); scene.add(moonL.target);

// ground (grass with painted tufts)
const grassTex = ctex(512, 512, (c) => {
  c.fillStyle = '#2f8a55'; c.fillRect(0, 0, 512, 512);
  let s = 3; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < 260; i++) { c.fillStyle = rnd() > 0.5 ? '#3b9d62' : '#27774a'; const x = rnd() * 512, y = rnd() * 512; c.beginPath(); c.ellipse(x, y, 4 + rnd() * 9, 2 + rnd() * 3, 0, 0, 7); c.fill(); }
});
grassTex.wrapS = grassTex.wrapT = THREE.RepeatWrapping; grassTex.repeat.set(26, 26);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(160, 160), toon(0xffffff, { map: grassTex }));
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
// road + far street
const road = put(new THREE.Mesh(new THREE.PlaneGeometry(160, 5), toon(0x3a3d6b)), 0, 0.01, -7.6); road.rotation.x = -Math.PI / 2; road.receiveShadow = true;
for (let i = -8; i < 12; i++) { const d = put(new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.16), new THREE.MeshBasicMaterial({ color: 0xcfd3ff })), i * 3.2, 0.02, -7.6); d.rotation.x = -Math.PI / 2; }

// grave
const dirt = toon(0x7a4a2e), stone = toon(0x9aa0c8), wood = toon(0x9a6a3c), woodD = toon(0x6e4526);
const mound = put(ol(new THREE.CapsuleGeometry(0.62, 1.5, 4, 14), dirt, 0.03), 0, 0, 0); mound.rotation.x = Math.PI / 2; mound.scale.set(1, 1, 0.3);
for (const [x, z, r] of [[-0.75, 0.6, 0.11], [0.8, 0.9, 0.08], [0.72, -0.2, 0.1], [-0.82, -0.5, 0.07], [0.3, 1.25, 0.09]]) put(ol(new THREE.DodecahedronGeometry(r), dirt, 0.02), x, r * 0.5, z);
const hsTex = ctex(256, 320, (c) => {
  c.fillStyle = '#2a2550'; c.textAlign = 'center';
  c.font = '900 58px Inter'; c.fillText('R.I.P.', 128, 120); c.font = '800 34px Inter'; c.fillText('BOB', 128, 172);
  c.font = 'italic 700 19px Inter'; c.fillText('"I\'ll pay you back', 128, 214); c.fillText('tomorrow"', 128, 238);
  c.strokeStyle = '#7f85b5'; c.lineWidth = 5; c.beginPath(); c.moveTo(40, 268); c.lineTo(120, 262); c.lineTo(150, 290); c.stroke();
});
function headstone(x, z, ry = 0, sc = 1, tex = null) {
  const g = new THREE.Group();
  const sh = new THREE.Shape(); sh.moveTo(-0.42, 0); sh.lineTo(-0.42, 0.75); sh.absarc(0, 0.75, 0.42, Math.PI, 0, true); sh.lineTo(0.42, 0);
  const geo = new THREE.ExtrudeGeometry(sh, { depth: 0.2, bevelEnabled: false }); geo.translate(0, 0, -0.1);
  g.add(ol(geo, stone, 0.03));
  if (tex) { const f = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 1.0), new THREE.MeshBasicMaterial({ map: tex, color: 0xffffff, transparent: true })); f.position.set(0, 0.6, 0.105); g.add(f); }
  g.add(put(box(1.05, 0.14, 0.4, stone, 0.03), 0, 0.07, 0, g));
  g.position.set(x, 0, z); g.rotation.set(0, ry, 0); g.scale.setScalar(sc); scene.add(g); return g;
}
headstone(0, -1.45, 0, 1.15, hsTex);
for (const [x, z, r, s] of [[-2.6, -1.9, 0.2, 0.95], [-4.4, 0.4, -0.15, 1.05], [-2.4, 1.8, 0.3, 0.85], [-5.2, -3.2, 0.1, 1], [1.9, -3.4, -0.2, 0.9], [-0.9, -4.3, 0.12, 1], [-6.5, 2.4, 0.4, 0.9]]) { const h = headstone(x, z, r, s); h.rotation.z = (x * 7 % 1) * 0.12; }

// bell post
const BELL = new THREE.Vector3(0.45, 1.42, -1.2);
put(ol(new THREE.CylinderGeometry(0.055, 0.065, 1.85, 8), wood, 0.022), 1.0, 0.92, -1.2);
const arm = put(ol(new THREE.CylinderGeometry(0.04, 0.04, 0.85, 8), wood, 0.02), 0.68, 1.72, -1.2); arm.rotation.z = Math.PI / 2;
const bellPivot = new THREE.Group(); bellPivot.position.set(BELL.x, 1.7, BELL.z); scene.add(bellPivot);
const gold = toon(0xf2b632), goldD = toon(0xb9791c);
{
  const pts = [[0, 0], [0.05, 0], [0.08, -0.04], [0.11, -0.16], [0.16, -0.27], [0.21, -0.31], [0.21, -0.335], [0, -0.335]].reverse().map(p => new THREE.Vector2(p[0], p[1]));
  const b = ol(new THREE.LatheGeometry(pts, 24), gold, 0.02); b.position.y = -0.08; bellPivot.add(b);
  bellPivot.add(put(ol(new THREE.CylinderGeometry(0.012, 0.012, 0.1, 6), goldD, 0.01), 0, -0.04, 0, bellPivot));
}
const clapper = new THREE.Group(); clapper.position.y = -0.3; bellPivot.add(clapper);
clapper.add(put(ol(new THREE.SphereGeometry(0.05, 12, 8), goldD, 0.014), 0, -0.14, 0, clapper));
const bellGlint = glow(0xfff2b0, 0.9, BELL.x - 0.08, 1.48, BELL.z + 0.25);
// ring lines card
const ringCard = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.0), new THREE.MeshBasicMaterial({
  transparent: true, depthWrite: false, fog: false, map: ctex(384, 256, (c) => {
    c.strokeStyle = '#fff3b8'; c.lineWidth = 9; c.lineCap = 'round';
    for (const s of [-1, 1]) for (let i = 0; i < 3; i++) { c.beginPath(); c.arc(192, 128, 78 + i * 30, s > 0 ? -0.5 : Math.PI - 0.5, s > 0 ? 0.5 : Math.PI + 0.5); c.stroke(); }
  })
})); put(ringCard, BELL.x, 1.42, BELL.z + 0.05);
// string (rebuilt every frame)
const stringMat = new THREE.MeshBasicMaterial({ color: 0xf3e6c4 });
let stringMesh = new THREE.Mesh(new THREE.BufferGeometry(), stringMat); scene.add(stringMesh);
let stringOut = new THREE.Mesh(new THREE.BufferGeometry(), OUTM); scene.add(stringOut);
put(ol(new THREE.TorusGeometry(0.07, 0.03, 6, 14), dirt, 0.012), BELL.x, 0.01, BELL.z).rotation.x = Math.PI / 2;

{ const lg = new THREE.Group(); lg.position.set(-0.95, 0, -1.25); scene.add(lg);
  lg.add(put(box(0.2, 0.05, 0.2, toon(0x2a2a3a), 0.015), 0, 0.03, 0, lg)); lg.add(put(box(0.2, 0.05, 0.2, toon(0x2a2a3a), 0.015), 0, 0.37, 0, lg));
  lg.add(put(new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.3, 0.15), new THREE.MeshBasicMaterial({ color: 0xffd98a, fog: false })), 0, 0.2, 0, lg));
  const pl = new THREE.PointLight(0xffa64d, 9, 6, 1.5); pl.position.set(0, 0.45, 0.25); lg.add(pl); glow(0xffb45a, 1.6, -0.95, 0.22, -1.2); }
// shovel + gravedigger
const shovel = new THREE.Group(); shovel.position.set(-0.62, 1.0, 0.35); scene.add(shovel);
shovel.add(put(ol(new THREE.CylinderGeometry(0.03, 0.03, 1.3, 6), wood, 0.016), 0, -0.45, 0, shovel));
shovel.add(put(box(0.3, 0.36, 0.04, toon(0xb9bfdc), 0.02), 0, -1.2, 0, shovel));
const digger = makeChar(512, 0xb9c2ff); put(digger.mesh, -1.05, 0, 0.3);

// fence between graveyard and street
for (let i = 0; i < 22; i++) {
  const z = -6 + i * 0.52, h = 1.0 + ((i * 37) % 5) * 0.03;
  const p = put(box(0.08, h, 0.36, toon(0xe9ecff), 0.02), 3.4, h / 2, z); p.rotation.z = (((i * 53) % 7) - 3) * 0.012;
}
put(box(0.05, 0.1, 11.6, toon(0xcfd4f5), 0.015), 3.36, 0.7, -0.55); put(box(0.05, 0.1, 11.6, toon(0xcfd4f5), 0.015), 3.36, 0.3, -0.55);
// dead tree
{
  const t = new THREE.Group(); const bark = toon(0x3d2f52);
  t.add(put(ol(new THREE.CylinderGeometry(0.16, 0.3, 3.4, 8), bark, 0.03), 0, 1.7, 0, t));
  for (const [y, rz, ry, l] of [[2.6, 0.9, 0, 1.6], [3.0, -0.8, 1, 1.4], [2.2, -1.1, 2.4, 1.1], [3.3, 0.3, 3.5, 1.2]]) { const b = ol(new THREE.CylinderGeometry(0.05, 0.1, l, 6), bark, 0.02); b.position.set(Math.sin(rz) * -l / 2 * Math.cos(ry), y + Math.cos(rz) * l / 2, Math.sin(ry) * l / 3); b.rotation.set(0, ry, rz); t.add(b); }
  t.position.set(-3.6, 0, -3.4); scene.add(t);
}
// bushes + pumpkin
for (const [x, z, r] of [[2.6, 1.6, 0.5], [-1.9, -0.2, 0.35], [2.7, -2.2, 0.42], [4.3, 0.9, 0.45]]) put(ol(new THREE.IcosahedronGeometry(r, 1), toon(0x256b4f), 0.03), x, r * 0.7, z);
put(ol(new THREE.SphereGeometry(0.2, 10, 8), toon(0xf08a2c), 0.02), 2.2, 0.17, 0.9).scale.y = 0.8;

// clock tower (2:00 AM)
{
  const g = new THREE.Group(); g.position.set(-8.6, 0, -17); scene.add(g);
  g.add(put(box(3.4, 8.5, 3.4, toon(0x6b6fae), 0.06), 0, 4.25, 0, g));
  const sp = ol(new THREE.ConeGeometry(2.7, 3.4, 4), toon(0x3b3f7e), 0.06); sp.rotation.y = Math.PI / 4; g.add(put(sp, 0, 10.2, 0, g));
  const ck = new THREE.Mesh(new THREE.CircleGeometry(1.3, 40), new THREE.MeshBasicMaterial({
    fog: false, map: ctex(256, 256, (c) => {
      c.fillStyle = '#fff3c9'; c.beginPath(); c.arc(128, 128, 124, 0, 7); c.fill(); c.strokeStyle = '#1b1636'; c.lineWidth = 12; c.stroke();
      c.fillStyle = '#1b1636'; for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; c.beginPath(); c.arc(128 + Math.sin(a) * 98, 128 - Math.cos(a) * 98, i % 3 ? 5 : 9, 0, 7); c.fill(); }
      c.lineCap = 'round'; c.lineWidth = 12; c.beginPath(); c.moveTo(128, 128); c.lineTo(128, 44); c.stroke();
      c.lineWidth = 15; c.beginPath(); c.moveTo(128, 128); c.lineTo(128 + Math.sin(Math.PI / 3) * 56, 128 - Math.cos(Math.PI / 3) * 56); c.stroke();
    })
  })); g.add(put(ck, 0, 6.3, 1.72, g)); glow(0xffe9a0, 7, -8.6, 6.3, -15);
}

// underground cutaway chamber
const soil = new THREE.MeshToonMaterial({ color: 0x6b3f2a, gradientMap: grad, side: THREE.BackSide });
const chamber = put(new THREE.Mesh(new THREE.BoxGeometry(3.8, 2.2, 4.6), soil), 0, -1.4, 0); chamber.receiveShadow = false;
for (const [x, y, z, r, c] of [[-1.3, -2.3, 1.2, 0.3, 0x8a8fb0], [1.4, -2.35, -1.4, 0.36, 0x7d82a6], [1.2, -2.4, 1.5, 0.22, 0x8a8fb0], [-1.5, -1.3, -1.9, 0.25, 0x7d82a6], [-1.75, -0.9, 0.4, 0.2, 0x8a8fb0]]) put(ol(new THREE.DodecahedronGeometry(r), toon(c), 0.025, false), x, y, z);
for (const [x, z, l] of [[-1.2, -0.6, 0.7], [1.3, 0.4, 0.9], [-0.9, 1.6, 0.5], [1.5, -1.7, 0.6]]) put(ol(new THREE.CylinderGeometry(0.025, 0.05, l, 6), toon(0x4a2c1c), 0.012, false), x, -0.08 - l / 2, z).rotation.z = x * 0.15;
const bone = new THREE.Group(); bone.add(ol(new THREE.CapsuleGeometry(0.035, 0.34, 3, 8), toon(0xf1ecdf), 0.014, false));
for (const y of [-0.2, 0.2]) for (const x of [-0.035, 0.035]) bone.add(put(ol(new THREE.SphereGeometry(0.05, 8, 6), toon(0xf1ecdf), 0.014, false), x, y, 0, bone));
put(bone, -1.25, -2.38, -0.1).rotation.set(Math.PI / 2, 0, 0.9);
const worm = put(ol(new THREE.TorusGeometry(0.13, 0.035, 6, 14, Math.PI), toon(0xf08fa8), 0.012, false), 1.15, -2.4, 0.2); worm.rotation.x = -Math.PI / 2;
// coffin
const coffin = new THREE.Group(); coffin.position.set(0, -2.3, 0); scene.add(coffin);
coffin.add(put(box(1.04, 0.08, 2.3, woodD, 0.025), 0, 0.04, 0, coffin));
for (const s of [-1, 1]) coffin.add(put(box(0.07, 0.5, 2.3, wood, 0.025), s * 0.52, 0.29, 0, coffin));
for (const s of [-1, 1]) coffin.add(put(box(1.11, 0.5, 0.07, wood, 0.025), 0, 0.29, s * 1.15, coffin));
const lining = put(new THREE.Mesh(new THREE.PlaneGeometry(0.97, 2.23), toon(0xb3364a)), 0, 0.09, 0, coffin); lining.rotation.x = -Math.PI / 2;
coffin.add(put(box(0.74, 0.03, 0.5, toon(0xe9e3f2), 0.02), 0, 0.105, -0.74, coffin));
const coffinL = new THREE.PointLight(0xffc27a, 5.5, 5.5, 1.6); coffinL.position.set(0, -1.1, 0.1); scene.add(coffinL);
const man = makeChar(1024, 0xffe7cf); man.billboard = false; man.mesh.rotation.x = -Math.PI / 2; man.mesh.castShadow = false; put(man.mesh, 0, -2.12, 0.5);

// houses
const sidingTex = (col, line) => { const t = ctex(256, 256, (c) => { c.fillStyle = col; c.fillRect(0, 0, 256, 256); c.strokeStyle = line; c.lineWidth = 5; for (let y = 0; y < 256; y += 32) { c.beginPath(); c.moveTo(0, y); c.lineTo(256, y); c.stroke(); } }); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(2, 2.4); return t; };
const roomTex = ctex(256, 276, (c) => {
  c.fillStyle = '#ffd98a'; c.fillRect(0, 0, 256, 276); c.fillStyle = '#f6c56a'; for (let x = 0; x < 256; x += 32) c.fillRect(x, 0, 14, 276);
  c.fillStyle = '#7a4a2e'; c.fillRect(150, 40, 76, 62); c.fillStyle = '#9fd6ff'; c.fillRect(158, 48, 60, 46); c.fillStyle = '#58b368'; c.fillRect(158, 78, 60, 16);
  c.fillStyle = '#c8493f'; c.beginPath(); c.moveTo(22, 120); c.lineTo(78, 120); c.lineTo(66, 70); c.lineTo(34, 70); c.fill(); c.fillStyle = '#5a4030'; c.fillRect(46, 120, 8, 160);
});
const houses = [];
function house(x, z, col, line, roofCol, withPerson = true) {
  const g = new THREE.Group(); g.position.set(x, 0, z); scene.add(g);
  const w = 4.4, h = 3.0, d = 4.0;
  g.add(put(box(w, h, d, toon(0xffffff, { map: sidingTex(col, line) }), 0.05), 0, h / 2, 0, g));
  const sh = new THREE.Shape(); sh.moveTo(-w / 2 - 0.35, 0); sh.lineTo(w / 2 + 0.35, 0); sh.lineTo(0, 1.7); sh.closePath();
  const rg = new THREE.ExtrudeGeometry(sh, { depth: d + 0.7, bevelEnabled: false }); rg.translate(0, 0, -(d + 0.7) / 2);
  g.add(put(ol(rg, toon(roofCol), 0.05), 0, h, 0, g));
  g.add(put(box(0.5, 1.1, 0.5, toon(0x8a4a4a), 0.04), 1.2, h + 1.0, -0.8, g));
  // door + porch
  g.add(put(box(0.95, 1.9, 0.08, toon(0xc8493f), 0.03), 1.15, 1.1, d / 2 + 0.03, g));
  g.add(put(box(2.0, 0.15, 1.3, toon(0xd9dcf2), 0.03), 1.15, 0.075, d / 2 + 0.65, g));
  const lamp = glow(0xffc46a, 2.6, 0.45, 2.15, d / 2 + 0.25, g); lamp.material.opacity = 0;
  g.add(put(ol(new THREE.SphereGeometry(0.09, 8, 6), toon(0xfff0c0), 0.015), 0.45, 2.15, d / 2 + 0.12, g));
  // window
  const winMat = new THREE.MeshBasicMaterial({ color: 0x1a1d55, fog: false, map: roomTex });
  g.add(put(new THREE.Mesh(new THREE.PlaneGeometry(1.3, 1.4), winMat), -0.9, 1.6, d / 2 + 0.012, g));
  const fr = toon(0xf4f6ff);
  for (const s of [-1, 1]) g.add(put(box(0.1, 1.6, 0.12, fr, 0.02), -0.9 + s * 0.7, 1.6, d / 2 + 0.06, g));
  g.add(put(box(1.5, 0.1, 0.12, fr, 0.02), -0.9, 2.35, d / 2 + 0.06, g));
  g.add(put(box(1.7, 0.12, 0.22, fr, 0.02), -0.9, 0.86, d / 2 + 0.1, g));
  const wglow = glow(0xffb85a, 4.2, -0.9, 1.6, d / 2 + 0.3, g); wglow.material.opacity = 0;
  const hObj = { g, winMat, lamp, wglow, x, z, d, person: null, on: 99 };
  if (withPerson) { const p = makeChar(256, 0xd6d0ff); put(p.mesh, x + 1.15, 0.15, z + d / 2 + 0.75); p.mesh.scale.setScalar(0.001); hObj.person = p; }
  houses.push(hObj); return hObj;
}
const H0 = house(6.5, -2.5, '#7fb6e6', '#5b93c9', 0x3a3566, false);
house(12.2, -2.6, '#f0c35a', '#c99a35', 0x5a3550); house(17.8, -2.4, '#e58aa0', '#bf6480', 0x353a70);
house(1.0, -14.5, '#9ad68a', '#6eb060', 0x4a3560); house(7.0, -14.8, '#c9a0f0', '#9f78c8', 0x353a70); house(13.0, -14.4, '#7fd0d6', '#56a6ad', 0x5a3550); house(19.0, -14.6, '#f0a070', '#c97a4c', 0x3a3566);
const PEOPLE = [
  { skin: '#f1c9a5', skinSh: '#dba983', hair: '#7a4a22', top: '#e9b33a', topSh: '#c48f22', pants: '#3a2d4d' },
  { skin: '#8a5a3c', skinSh: '#724628', hair: '#15101a', top: '#d9577a', topSh: '#b53f60', pants: '#232c4d' },
  { skin: '#f1c9a5', skinSh: '#dba983', hair: '#c9c9d6', top: '#7c6fd0', topSh: '#5f52b0', pants: '#2a2a3a' },
  { skin: '#d9a070', skinSh: '#bf8456', hair: '#3a1f12', top: '#58b368', topSh: '#3f914e', pants: '#3a2d4d' },
  { skin: '#f1c9a5', skinSh: '#dba983', hair: '#e07a2c', top: '#4f8fe0', topSh: '#3a70ba', pants: '#232c4d' },
  { skin: '#8a5a3c', skinSh: '#724628', hair: '#15101a', top: '#f0a070', topSh: '#c97a4c', pants: '#2a2a3a' },
];
houses.slice(1).forEach((h, i) => { h.on = 16.9 + [0.0, 0.75, 0.35, 1.1, 0.55, 1.4][i]; h.col = PEOPLE[i]; });
// neighbor in the window of house 0 (clipped by the window opening)
const WIN = new THREE.Vector3(5.6, 1.6, -0.49);
const neighbor = makeChar(512, 0xffe9d2); neighbor.billboard = false; neighbor.mesh.castShadow = false;
neighbor.mesh.material.clippingPlanes = [new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.93), new THREE.Plane(new THREE.Vector3(1, 0, 0), -4.98), new THREE.Plane(new THREE.Vector3(-1, 0, 0), 6.22), new THREE.Plane(new THREE.Vector3(0, -1, 0), 2.31)];
put(neighbor.mesh, 5.6, 0.2, -0.47); neighbor.mesh.scale.setScalar(0.95);
const shutters = [-1, 1].map(s => {
  const p = new THREE.Group(); p.position.set(WIN.x + s * 0.66, WIN.y, WIN.z + 0.13); scene.add(p);
  const m = box(0.64, 1.42, 0.06, toon(0x2f6fb5), 0.025); m.position.x = -s * 0.32; p.add(m);
  for (let i = 0; i < 5; i++) { const sl = box(0.5, 0.05, 0.02, toon(0x245a96), 0); sl.position.set(-s * 0.32, -0.5 + i * 0.25, 0.04); p.add(sl); }
  return { p, s };
});

// ---------- timeline ----------
// camera keys: [time, pos, lookAt, fov, ease-into-this-key]. One continuous move, no cuts.
const CAM = [
  [0.0, [0.98, 1.5, -0.2], [0.45, 1.4, -1.2], 32, 'lin'],
  [0.8, [0.95, 1.5, 0.0], [0.45, 1.4, -1.2], 32, 'lin'],
  [1.75, [1.1, 1.75, 5.6], [-0.4, 0.75, -0.4], 42, 'io'],
  [2.6, [1.0, 1.8, 5.3], [-0.4, 0.72, -0.4], 42, 'lin'],
  [3.3, [0.0, -0.42, 1.0], [0, -2.1, -0.3], 56, 'io'],
  [3.9, [0.0, -0.46, 0.95], [0, -2.1, -0.3], 56, 'lin'],
  [4.25, [0.0, -0.62, 0.0], [0, -2.15, -0.72], 48, 'out'],
  [5.6, [0.0, -0.7, -0.05], [0, -2.15, -0.72], 48, 'lin'],
  [6.5, [1.3, 1.25, 0.75], [0.45, 1.38, -1.2], 34, 'io'],
  [8.0, [1.2, 1.3, 0.6], [0.45, 1.38, -1.2], 34, 'lin'],
  [8.7, [0.22, -0.7, 0.3], [0.2, -2.1, -0.52], 46, 'io'],
  [10.0, [0.24, -0.85, 0.2], [0.22, -2.1, -0.52], 46, 'lin'],
  [10.7, [1.55, 0.9, 1.3], [0.15, 1.6, -1.7], 40, 'io'],
  [12.3, [1.5, 0.92, 1.2], [0.15, 1.6, -1.7], 40, 'lin'],
  [12.9, [5.1, 1.75, 4.9], [5.6, 1.62, -0.5], 30, 'io'],
  [14.5, [5.2, 1.75, 4.5], [5.6, 1.62, -0.5], 30, 'lin'],
  [15.0, [1.35, 1.32, 1.0], [0.45, 1.36, -1.2], 36, 'io'],
  [16.2, [1.22, 1.32, 0.8], [0.45, 1.36, -1.2], 36, 'lin'],
  [17.9, [12.5, 5.6, 17.5], [14.2, -0.4, -6.0], 50, 'io'],
  [20.5, [12.9, 6.0, 18.8], [14.2, -0.4, -6.0], 50, 'lin'],
];
function camAt(t) {
  let i = 0; while (i < CAM.length - 2 && t > CAM[i + 1][0]) i++;
  const a = CAM[i], b = CAM[i + 1], k = EASE[b[4]](seg(t, a[0], b[0]));
  const v = (p, r) => p.map((x, j) => lerp(x, r[j], k));
  const pos = v(a[1], b[1]), look = v(a[2], b[2]);
  pos[0] += Math.sin(t * 1.3) * 0.012; pos[1] += Math.sin(t * 1.7 + 1) * 0.01; // breathing camera
  return { pos, look, fov: lerp(a[3], b[3], k) };
}
function setCam(t) {
  const c = camAt(t); camera.position.set(...c.pos); camera.fov = c.fov; camera.updateProjectionMatrix(); camera.lookAt(...c.look);
  camera.rotation.z += Math.sin(t * 0.9) * 0.004;
}
// bell ring events (shared with audio.py)
export const RINGS = [10.1, 10.5, 10.9, 11.35, 12.0];
for (let x = 14.9; x < 16.6; x += 0.15) RINGS.push(+x.toFixed(2));
for (let x = 16.6; x < 20.4; x += 0.19) RINGS.push(+x.toFixed(2));
const PATS = [1.25, 1.65, 2.05];
function bellSwing(t) { let a = 0; for (const r of RINGS) if (t > r) { const d = t - r; a += 0.42 * Math.exp(-d * 5.5) * Math.sin(d * 24); } return cl(a, -0.75, 0.75); }
function ringEnergy(t) { let a = 0; for (const r of RINGS) if (t > r) a += Math.exp(-(t - r) * 7); return cl(a); }
function yank(t) { let a = 0; for (const r of RINGS) { const d = t - (r - 0.12); if (d > 0) a += Math.exp(-d * 14) * Math.sin(Math.min(d * 26, Math.PI)); } return cl(a, 0, 1.2); }

const CAPS = [
  [0.0, 2.0, 'They buried a man alive with a bell tied'], [2.0, 2.7, 'to his finger.'], [2.75, 4.0, 'You see, people were so'],
  [4.0, 6.0, 'scared of waking up in a coffin that'], [6.0, 8.0, 'graves came with a little bell on top,'],
  [8.0, 9.9, "tied by a string to the body's finger."], [10.0, 12.0, 'Except when his bell starts ringing at'],
  [12.0, 13.1, '2:00 in the morning, the guy next door'], [13.1, 14.55, "decides it's probably the wind."], [14.55, 15.0, 'Then it'],
  [15.0, 15.9, 'rings faster.'], [16.1, 18.0, 'And now the whole street'], [18.0, 20.2, 'is out on their porches going,'],
];
const CHUNKS = [];
for (const [a, b, txt] of CAPS) {
  const w = txt.split(' '); const groups = [];
  for (let i = 0; i < w.length;) { const two = i + 1 < w.length && (w[i].length + w[i + 1].length) <= 11 && !/[.,?]$/.test(w[i]); groups.push(w.slice(i, i + (two ? 2 : 1)).join(' ')); i += two ? 2 : 1; }
  const tot = groups.reduce((s, g) => s + g.length + 2, 0); let t = a;
  for (const g of groups) { const d = (b - a) * (g.length + 2) / tot; CHUNKS.push([t, t + d, g]); t += d; }
}

// ---------- per-frame state ----------
const V = new THREE.Vector3();
function update(t) {
  // bell
  const sw = bellSwing(t); bellPivot.rotation.z = sw; clapper.rotation.z = -sw * 1.6;
  const re = ringEnergy(t); ringCard.material.opacity = re * 0.95; ringCard.scale.setScalar(0.75 + re * 0.35 + Math.sin(t * 40) * 0.03 * re);
  bellGlint.material.opacity = Math.max(0, Math.sin(seg(t, 0.05, 0.7) * Math.PI)) * 0.9 + re * 0.25; bellGlint.scale.setScalar(0.5 + Math.sin(seg(t, 0.05, 0.7) * Math.PI) * 0.6);

  // gravedigger pats the mound
  digger.mesh.visible = shovel.visible = t < 3.2;
  if (digger.mesh.visible) {
    let pat = 0; for (const p of PATS) pat += Math.exp(-Math.pow((t - p) / 0.07, 2));
    const lift = Math.max(0, Math.sin((t - 1.05) * Math.PI / 0.4 * 1)) * (t < 2.15 ? 1 : 0);
    const done = seg(t, 2.2, 2.45);
    shovel.rotation.z = lerp(0.75 - lift * 0.35 + pat * 0.12, 0.15, EASE.io(done)); shovel.position.y = 1.0 - pat * 0.05;
    digger.draw({
      colors: { skin: '#f1c9a5', skinSh: '#dba983', top: '#7a5a3a', topSh: '#5f4329', pants: '#2a2a3a', inner: '#d8d2c4' }, hat: 'cap', hair: 'none', noStrings: true,
      eye: done > 0.5 ? 'happy' : 'squint', mouth: done > 0.5 ? 'grin' : 'flat', brow: -8, look: [0.6, 0.5],
      armR: [48 - lift * 14 + pat * 6, -28], armL: [-20, -95 + lift * 10], bob: pat * 10, tilt: 5 - pat * 4,
    });
  }

  // man in the coffin
  const awake = t >= 3.9, yk = yank(t), raised = t > 6.4;
  const dart = Math.sin(t * 9) > 0 ? 1 : -1;
  const wig = (t > 8.9 && t < 9.9) ? Math.sin((t - 8.9) * 22) * 9 : 0;
  man.draw({
    tied: true, prop: 'lily',
    eye: awake ? 'wide' : 'closed', mouth: awake ? (t > 8 ? 'o' : 'grit') : 'smile', mouthOpen: 0.6 + yk * 0.5,
    brow: awake ? 16 : 0, browY: awake ? 4 : 0, sweat: awake, look: awake ? [t < 5.7 ? dart * 0.8 : 0.7, t < 5.7 ? 0 : -0.5] : [0, 0],
    armL: [30, -140], armR: raised ? [22 + yk * 10, 138 + wig - yk * 42] : [30, -140],
    headX: awake && t < 5.7 ? Math.sin(t * 34) * 2.5 : 0, tilt: awake ? Math.sin(t * 4) * 2 : 0,
  });
  coffinL.intensity = 5.5 + Math.sin(t * 13) * 0.35;
  worm.position.x = 1.15 + Math.sin(t * 2) * 0.12; worm.scale.x = 1 + Math.sin(t * 6) * 0.18;

  // string: bell -> hole -> finger
  const hand = man.handWorld(1); hand.y += 0.03;
  const bb = bellPivot.localToWorld(V.set(0, -0.42, 0)).clone();
  const jit = yk * 0.03 * Math.sin(t * 90);
  const pts = [bb, new THREE.Vector3(BELL.x + jit, 0.6, BELL.z), new THREE.Vector3(BELL.x, 0, BELL.z), new THREE.Vector3(BELL.x - 0.02 + jit, -0.9, BELL.z + 0.5), hand];
  const curve = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.2);
  stringMesh.geometry.dispose(); stringMesh.geometry = new THREE.TubeGeometry(curve, 48, 0.011, 6);
  stringOut.geometry.dispose(); stringOut.geometry = new THREE.TubeGeometry(curve, 48, 0.02, 6);

  // neighbor at his window
  const up = EASE.back(seg(t, 12.75, 13.05)), shut = EASE.io(seg(t, 14.12, 14.3));
  H0.winMat.color.setHex(t > 12.55 ? 0xffffff : 0x1a1d55); H0.wglow.material.opacity = t > 12.55 ? 0.5 * (1 - shut * 0.7) : 0;
  neighbor.mesh.position.y = lerp(-0.9, 0.4, up);
  const talk = t > 13.15 && t < 14.05, shrug = Math.sin(seg(t, 13.5, 14.0) * Math.PI);
  neighbor.draw({
    colors: { skin: '#f1c9a5', skinSh: '#dba983', top: '#e8e2f7', topSh: '#c9c0e6', inner: '#e8e2f7', pants: '#8a86c0', hair: '#7a4a22' }, stripes: '#9c8fe0', noStrings: true, hat: 'nightcap',
    eye: 'squint', look: [-0.8, 0.1], brow: shrug > 0.3 ? 6 : -6, mouth: talk ? 'talk' : 'flat', mouthOpen: 0.5 + 0.5 * Math.sin(t * 30),
    armL: [20 + shrug * 70, 20 + shrug * 95], armR: [20 + shrug * 70, 20 + shrug * 95], tilt: -6 + shrug * 10, headY: -shrug * 6,
  });
  for (const { p, s } of shutters) p.rotation.y = s * lerp(Math.PI * 0.93, 0, shut);

  // the street wakes up
  for (const h of houses.slice(1)) {
    const on = t > h.on; h.winMat.color.setHex(on ? 0xffffff : 0x1a1d55);
    const k = pop(t, h.on, 0.3); h.wglow.material.opacity = 0.55 * cl(k); h.lamp.material.opacity = 0.9 * cl(pop(t, h.on + 0.25, 0.2));
    const pk = pop(t, h.on + 0.45, 0.32); h.person.mesh.scale.setScalar(Math.max(0.001, 1.7 * pk));
    if (pk > 0 && pk < 1.2) {
      const ph = h.on * 7;
      h.person.draw({ colors: h.col, eye: 'wide', mouth: 'o', mouthOpen: 0.7, brow: 12, look: [-0.7, -0.2], armL: [150 + Math.sin(t * 9 + ph) * 12, 10], armR: [25, 20], hat: (ph | 0) % 2 ? 'nightcap' : null, noStrings: true, tilt: Math.sin(t * 5 + ph) * 4 });
    }
  }
  // billboards
  for (const c of [digger, ...houses.slice(1).map(h => h.person)]) c.mesh.rotation.y = Math.atan2(camera.position.x - c.mesh.position.x, camera.position.z - c.mesh.position.z);
  ringCard.quaternion.copy(camera.quaternion);
}

function overlay(t, camY) {
  // soil wipe when the camera passes through the ground
  const a = cl(1 - Math.abs(camY + 0.08) / 0.34);
  if (a > 0) { o2.fillStyle = `rgba(74,42,28,${a})`; o2.fillRect(0, 0, W, H); }
  // vignette
  const g = o2.createRadialGradient(W / 2, H * 0.48, H * 0.28, W / 2, H * 0.5, H * 0.72);
  g.addColorStop(0, 'rgba(8,6,30,0)'); g.addColorStop(1, 'rgba(8,6,30,0.5)'); o2.fillStyle = g; o2.fillRect(0, 0, W, H);
  // captions: 1-2 words, bold white, ink stroke, tiny pop
  const c = CHUNKS.find(c => t >= c[0] && t < c[1]);
  if (c) {
    const k = 0.86 + 0.14 * EASE.out(seg(t, c[0], c[0] + 0.09));
    o2.save(); o2.translate(W / 2, H * 0.705); o2.scale(k, k);
    o2.font = `900 ${Math.round(74 * SC)}px Inter`; o2.textAlign = 'center'; o2.textBaseline = 'middle'; o2.lineJoin = 'round';
    o2.shadowColor = 'rgba(0,0,0,.55)'; o2.shadowBlur = 14 * SC; o2.shadowOffsetY = 5 * SC;
    o2.strokeStyle = '#0d0a14'; o2.lineWidth = 15 * SC; o2.strokeText(c[2], 0, 0);
    o2.shadowColor = 'transparent'; o2.fillStyle = '#fff'; o2.fillText(c[2], 0, 0); o2.restore();
  }
}

window.DUR = DUR; window.FPS = FPS;
window.renderFrame = (t) => {
  setCam(t); update(t);
  const a = camAt(t), b = camAt(Math.max(0, t - 1 / FPS));
  const speed = Math.hypot(a.pos[0] - b.pos[0], a.pos[1] - b.pos[1], a.pos[2] - b.pos[2]) + Math.hypot(a.look[0] - b.look[0], a.look[1] - b.look[1], a.look[2] - b.look[2]);
  const n = speed > 0.5 ? 12 : speed > 0.12 ? 6 : 1; // motion blur on fast camera moves
  for (let i = 0; i < n; i++) {
    setCam(t - (n > 1 ? (i / n) * 0.65 / FPS : 0)); renderer.shadowMap.autoUpdate = i === 0; if (i === 0) renderer.shadowMap.needsUpdate = true; renderer.render(scene, camera);
    o2.globalAlpha = 1 / (i + 1); o2.drawImage(gl, 0, 0);
  }
  o2.globalAlpha = 1; setCam(t);
  overlay(t, a.pos[1]);
  return n;
};
window.READY = document.fonts.load('900 40px Inter').then(() => true);
