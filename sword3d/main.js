// "The Indestructible Sword" — 2D characters in a toon-shaded 3D world.
// Every frame is a pure function of time t: window.renderFrame(t) draws it.
import * as THREE from 'three';
import { OutlineEffect } from '/jsm/effects/OutlineEffect.js';
import { RoundedBoxGeometry } from '/jsm/geometries/RoundedBoxGeometry.js';

const W = 1080, H = 1920;
const glc = document.getElementById('gl');
const ov = document.getElementById('ov');
const o = ov.getContext('2d');

const renderer = new THREE.WebGLRenderer({ canvas: glc, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false);
renderer.setPixelRatio(1);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const effect = new OutlineEffect(renderer, { defaultThickness: 0.0042, defaultColor: [0.07, 0.06, 0.11] });

// ------------------------------------------------------------------ helpers
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const inv = (a, b, x) => clamp((x - a) / (b - a));
const sm = k => k * k * (3 - 2 * k);
const eo = k => 1 - Math.pow(1 - k, 3);
const ei = k => k * k * k;
const eio = k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
const back = k => { const c = 1.9; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const V = (x, y, z) => new THREE.Vector3(x, y, z);

const gm = new THREE.DataTexture(new Uint8Array([120, 120, 120, 255, 200, 200, 200, 255, 255, 255, 255, 255]), 3, 1);
gm.minFilter = gm.magFilter = THREE.NearestFilter; gm.needsUpdate = true;
const toon = (c, x = {}) => new THREE.MeshToonMaterial({ color: c, gradientMap: gm, ...x });
const noOut = m => { m.userData.outlineParameters = { visible: false }; return m; };
function mesh(geo, mat, x = 0, y = 0, z = 0, parent) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true;
  if (parent) parent.add(m); return m;
}
function glowTex(stops) {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  stops.forEach(([p, col]) => gr.addColorStop(p, col)); g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const TEX_GLOW = glowTex([[0, 'rgba(255,255,255,1)'], [0.25, 'rgba(255,255,255,0.6)'], [1, 'rgba(255,255,255,0)']]);
function glowSprite(color, scale, parent) {
  const m = noOut(new THREE.SpriteMaterial({ map: TEX_GLOW, color, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
  const s = new THREE.Sprite(m); s.scale.setScalar(scale); (parent || scene).add(s); return s;
}

// ------------------------------------------------------------------ scene
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(50, W / H, 0.05, 3000);
const FOG = new THREE.Fog(0xcfeaff, 70, 330);
scene.fog = FOG;

const hemi = new THREE.HemisphereLight(0xeaf6ff, 0x6b8a4a, 1.7); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff3dc, 2.6);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -25, right: 25, top: 25, bottom: -25, near: 1, far: 120 });
sun.shadow.bias = -0.0008;
scene.add(sun, sun.target);

// sky dome
const skyU = {
  top: { value: new THREE.Color(0x2f86e0) }, bot: { value: new THREE.Color(0xd6f0ff) },
  stars: { value: 0 }, tint: { value: new THREE.Color(0, 0, 0) },
};
const sky = new THREE.Mesh(new THREE.SphereGeometry(1500, 32, 16), noOut(new THREE.ShaderMaterial({
  uniforms: skyU, side: THREE.BackSide, depthWrite: false, fog: false,
  vertexShader: `varying vec3 vP; void main(){ vP=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform vec3 top,bot,tint; uniform float stars; varying vec3 vP;
    float h3(vec3 p){ return fract(sin(dot(p,vec3(12.9898,78.233,37.719)))*43758.5453); }
    void main(){ vec3 d=normalize(vP); float k=smoothstep(-0.02,0.55,d.y);
      vec3 c=mix(bot,top,k)+tint;
      vec3 g=floor(d*260.); float s=step(0.9965,h3(g)); c+=vec3(s)*stars*(0.6+0.4*h3(g+3.));
      gl_FragColor=vec4(c,1.); }`,
})));
sky.renderOrder = -10; scene.add(sky);

// ------------------------------------------------------------------ road world
const road = new THREE.Group(); scene.add(road);
const ground = mesh(new THREE.PlaneGeometry(2400, 2400), toon(0x7fcf5c), 0, 0, 0, road); ground.rotation.x = -Math.PI / 2; ground.castShadow = false;
const RZ = 2.6, RW = 7.4;
const asphalt = mesh(new THREE.PlaneGeometry(2400, RW), toon(0x555b6e), 0, 0.012, RZ, road); asphalt.rotation.x = -Math.PI / 2; asphalt.castShadow = false;
const lineMat = toon(0xffffff), dashMat = toon(0xffd34a);
[RZ - RW / 2 + 0.18, RZ + RW / 2 - 0.18].forEach(z => { const l = mesh(new THREE.PlaneGeometry(2400, 0.16), lineMat, 0, 0.02, z, road); l.rotation.x = -Math.PI / 2; l.castShadow = false; });
for (let x = -400; x < 400; x += 7) { const d = mesh(new THREE.PlaneGeometry(3.2, 0.2), dashMat, x, 0.02, RZ, road); d.rotation.x = -Math.PI / 2; d.castShadow = false; }
const curb = mesh(new THREE.BoxGeometry(2400, 0.14, 0.45), toon(0xd9dce4), 0, 0.07, RZ - RW / 2 - 0.22, road); curb.castShadow = false;
const curb2 = mesh(new THREE.BoxGeometry(2400, 0.14, 0.45), toon(0xd9dce4), 0, 0.07, RZ + RW / 2 + 0.22, road); curb2.castShadow = false;

const TRUNK = toon(0x9a6337), LEAF = [toon(0x58b947), toon(0x46a83e), toon(0x6fcf55)];
function makeTree(r, seed) {
  const R = rng(seed), g = new THREE.Group();
  const h = 2.6 + R() * 1.6;
  mesh(new THREE.CylinderGeometry(0.16, 0.26, h, 8), TRUNK, 0, h / 2, 0, g);
  const n = 3 + Math.floor(R() * 2);
  for (let i = 0; i < n; i++) {
    const s = 1.0 + R() * 0.7;
    const b = mesh(new THREE.IcosahedronGeometry(s, 1), LEAF[Math.floor(R() * 3)], (R() - 0.5) * 1.3, h + 0.3 + R() * 1.0, (R() - 0.5) * 1.3, g);
    b.scale.y = 0.85;
  }
  g.scale.setScalar(r); return g;
}
const TX = 0, TZ = -3.9; // hero tree position
const bgTrees = [];
{
  const R = rng(7);
  for (let i = 0; i < 70; i++) {
    const side = i % 2 ? 1 : -1;
    const x = -260 + R() * 520;
    const z = side < 0 ? -(7 + R() * 45) : RZ + RW / 2 + 5 + R() * 45;
    if (Math.abs(x - TX) < 9 && side < 0 && z > -14) continue;
    const t = makeTree(0.8 + R() * 0.8, 100 + i); t.position.set(x, 0, z); road.add(t); bgTrees.push(t);
  }
  for (let i = 0; i < 40; i++) { // bushes
    const x = -260 + R() * 520, z = R() < 0.5 ? -(2.4 + R() * 3) : RZ + RW / 2 + 1.5 + R() * 4;
    if (Math.abs(x - TX) < 5 && z < 0) continue;
    const b = mesh(new THREE.IcosahedronGeometry(0.6 + R() * 0.5, 1), LEAF[i % 3], x, 0.35, z, road); b.scale.y = 0.7; bgTrees.push(b);
  }
  for (let x = -300; x < 300; x += 22) { // lamp posts far side
    const g = new THREE.Group(); g.position.set(x, 0, RZ + RW / 2 + 1.1);
    mesh(new THREE.CylinderGeometry(0.08, 0.1, 5, 8), toon(0x7a8294), 0, 2.5, 0, g);
    mesh(new RoundedBoxGeometry(0.9, 0.18, 0.35, 2, 0.06), toon(0x7a8294), 0, 5, -0.35, g);
    mesh(new THREE.BoxGeometry(0.5, 0.06, 0.22), toon(0xfff4c2, { emissive: 0x665a20 }), 0, 4.9, -0.45, g);
    road.add(g); bgTrees.push(g);
  }
  // distant hills
  const HM = [toon(0x6cbf5a), toon(0x5aae55), toon(0x7ccf6a)];
  for (let i = 0; i < 16; i++) {
    const hz = (i % 2 ? 1 : -1) * (170 + R() * 80);
    const hll = mesh(new THREE.SphereGeometry(40 + R() * 40, 24, 12), HM[i % 3], -400 + i * 55 + R() * 20, -15, hz, road); hll.scale.y = 0.45; hll.castShadow = false;
  }
  // clouds
  const CM = toon(0xffffff, { emissive: 0x9aa6b8 });
  for (let i = 0; i < 26; i++) {
    const g = new THREE.Group(); g.position.set(-400 + R() * 800, 45 + R() * 35, (R() < 0.5 ? -1 : 1) * (60 + R() * 200));
    for (let k = 0; k < 4; k++) { const c = mesh(new THREE.SphereGeometry(5 + R() * 4, 16, 10), CM, k * 6 - 9, R() * 3, R() * 4, g); c.castShadow = false; c.scale.y = 0.7; }
    road.add(g);
  }
}

// hero tree (two halves so it can split)
const hero = new THREE.Group(); hero.position.set(TX, 0, TZ); road.add(hero);
const heroGlowMats = [];
function heroHalf(sign) {
  const g = new THREE.Group(); hero.add(g);
  const trunkM = toon(0xa56a3a); heroGlowMats.push(trunkM);
  const th = sign < 0 ? Math.PI / 2 : -Math.PI / 2; // z<=0 half / z>=0 half
  mesh(new THREE.CylinderGeometry(0.5, 0.62, 4.6, 20, 1, false, th, Math.PI), trunkM, 0, 2.3, 0, g);
  const cut = mesh(new THREE.PlaneGeometry(1.1, 4.6), toon(0xf1cf98, { side: THREE.DoubleSide }), 0, 2.3, 0, g);
  // branches
  const br = mesh(new THREE.CylinderGeometry(0.12, 0.2, 2.2, 8), trunkM, 0.6, 4.6, sign * 0.3, g); br.rotation.z = -0.7;
  const br2 = mesh(new THREE.CylinderGeometry(0.12, 0.2, 2.0, 8), trunkM, -0.6, 4.5, sign * 0.3, g); br2.rotation.z = 0.7;
  const R = rng(sign < 0 ? 5 : 9);
  for (let i = 0; i < 6; i++) {
    const m = toon([0x4fb443, 0x63c74e, 0x3fa13a][i % 3]); heroGlowMats.push(m);
    const b = mesh(new THREE.IcosahedronGeometry(1.3 + R() * 0.7, 1), m, (R() - 0.5) * 3.6, 5.6 + R() * 1.6, sign * (0.5 + R() * 1.2), g);
    b.scale.y = 0.85;
  }
  return g;
}
const halfA = heroHalf(-1), halfB = heroHalf(1);
const heroAura = glowSprite(0x33ff77, 14, hero); heroAura.position.y = 4; heroAura.visible = false;

// cracks on ground
const cracks = new THREE.Group(); road.add(cracks);
{
  const R = rng(31);
  for (let i = 0; i < 16; i++) {
    const a = (i / 16) * Math.PI * 2 + R() * 0.3, L = 2 + R() * 4;
    const c = mesh(new THREE.BoxGeometry(L, 0.04, 0.12 + R() * 0.1), toon(0x222018), 0, 0.03, 0, cracks);
    c.geometry.translate(L / 2, 0, 0); c.rotation.y = a; c.castShadow = false;
  }
  cracks.position.set(TX - 0.6, 0, TZ + 0.2);
}

// ------------------------------------------------------------------ car
const car = new THREE.Group(); scene.add(car);
const carPivot = new THREE.Group(); carPivot.position.x = 1.4; car.add(carPivot);
const body = new THREE.Group(); body.position.x = -1.4; carPivot.add(body);
const RED = toon(0xe8463c), DARK = toon(0x2a2b36), CHROME = toon(0xdfe4ea), GLASS = toon(0x9fd4ff, { transparent: true, opacity: 0.55 });
const carTint = RED;
mesh(new RoundedBoxGeometry(4.5, 0.95, 2.0, 4, 0.3), RED, 0, 0.86, 0, body);
mesh(new RoundedBoxGeometry(2.4, 0.16, 1.92, 3, 0.07), RED, -0.3, 2.06, 0, body);
for (const [px, tilt] of [[0.86, -0.35], [-0.32, 0], [-1.45, 0.3]]) for (const pz of [-0.9, 0.9]) {
  const p = mesh(new THREE.BoxGeometry(0.13, 0.78, 0.12), RED, px, 1.68, pz, body); p.rotation.z = tilt;
}
mesh(new THREE.BoxGeometry(0.06, 0.66, 1.7), GLASS, 0.98, 1.68, 0, body).rotation.z = -0.35; // windshield
mesh(new THREE.BoxGeometry(0.06, 0.66, 1.7), GLASS, -1.55, 1.68, 0, body).rotation.z = 0.3;
mesh(new THREE.BoxGeometry(2.1, 0.66, 0.05), GLASS, -0.3, 1.68, 0.92, body); // far side glass
mesh(new THREE.BoxGeometry(0.95, 0.66, 0.05), GLASS, -0.92, 1.68, -0.92, body); // near rear glass (front window open)
mesh(new RoundedBoxGeometry(0.5, 0.9, 1.6, 2, 0.12), DARK, -0.9, 1.35, 0, body); // seats
mesh(new RoundedBoxGeometry(4.62, 0.22, 2.06, 2, 0.1), CHROME, 0, 0.45, 0, body); // bumper band
mesh(new THREE.BoxGeometry(4.0, 0.08, 2.03), toon(0xffffff), 0, 1.0, 0, body); // stripe
const headL = toon(0xfff6b0, { emissive: 0x887722 });
mesh(new RoundedBoxGeometry(0.1, 0.22, 0.4, 2, 0.05), headL, 2.25, 0.95, -0.65, body); mesh(new RoundedBoxGeometry(0.1, 0.22, 0.4, 2, 0.05), headL, 2.25, 0.95, 0.65, body);
const tailL = toon(0xff3355, { emissive: 0x661020 });
mesh(new RoundedBoxGeometry(0.1, 0.2, 0.36, 2, 0.05), tailL, -2.25, 1.0, -0.65, body); mesh(new RoundedBoxGeometry(0.1, 0.2, 0.36, 2, 0.05), tailL, -2.25, 1.0, 0.65, body);
const wheels = [], hubMats = [];
for (const wx of [1.42, -1.42]) for (const wz of [-0.92, 0.92]) {
  const wg = new THREE.Group(); wg.position.set(wx, 0.46, wz); body.add(wg);
  const spin = new THREE.Group(); wg.add(spin);
  const tire = mesh(new THREE.CylinderGeometry(0.46, 0.46, 0.36, 24), DARK, 0, 0, 0, spin); tire.rotation.x = Math.PI / 2;
  const hm = toon(0xd8dde6); hubMats.push(hm);
  const hub = mesh(new THREE.CylinderGeometry(0.26, 0.26, 0.38, 16), hm, 0, 0, 0, spin); hub.rotation.x = Math.PI / 2;
  for (let k = 0; k < 3; k++) { const s = mesh(new THREE.BoxGeometry(0.5, 0.07, 0.4), DARK, 0, 0, 0, spin); s.rotation.z = k * Math.PI / 3; }
  const gl = glowSprite(0xb04dff, 2.2, wg); gl.position.z = wz * 0.4; gl.visible = false;
  wheels.push({ wg, spin, gl });
}
const CAR_Z = 1.0;
const ANCHOR_LOCAL = V(0.45, 1.55, -1.15); // grip point in car-body space

// ------------------------------------------------------------------ swords
const BLADE = toon(0xe9f0f8, { emissive: 0x000000 }), GOLD = toon(0xf4c34a), GRIP = toon(0x5b3a2a), GEM = toon(0x39e67a, { emissive: 0x0a5a22 });
function bladeGeo(pts) {
  const s = new THREE.Shape(); s.moveTo(pts[0][0], pts[0][1]); pts.slice(1).forEach(p => s.lineTo(p[0], p[1]));
  const g = new THREE.ExtrudeGeometry(s, { depth: 0.05, bevelEnabled: true, bevelThickness: 0.015, bevelSize: 0.015, bevelSegments: 1 });
  g.rotateY(Math.PI / 2); g.translate(-0.025, 0, -0.42); return g;
}
const FULL = [[0, -0.1], [3.45, -0.1], [3.85, 0], [3.45, 0.1], [0, 0.1]];
const STUB = [[0, -0.1], [1.5, -0.1], [1.38, -0.03], [1.56, 0.02], [1.42, 0.1], [0, 0.1]];
const SHARD = [[1.5, -0.1], [3.45, -0.1], [3.85, 0], [3.45, 0.1], [1.42, 0.1], [1.56, 0.02], [1.38, -0.03]];
function makeSword(pts, hilt = true, mat = BLADE) {
  const g = new THREE.Group();
  if (pts) mesh(bladeGeo(pts), mat, 0, 0, 0, g);
  if (hilt) {
    mesh(new RoundedBoxGeometry(0.14, 0.64, 0.13, 2, 0.05), GOLD, 0, 0, -0.36, g);
    const h = mesh(new THREE.CylinderGeometry(0.055, 0.06, 0.6, 10), GRIP, 0, 0, -0.03, g); h.rotation.x = Math.PI / 2;
    mesh(new THREE.SphereGeometry(0.095, 12, 8), GOLD, 0, 0, 0.3, g);
    mesh(new THREE.SphereGeometry(0.06, 10, 8), GEM, 0, 0, -0.36, g).scale.x = 1.6;
  }
  return g;
}
const swordCar = makeSword(FULL); swordCar.position.copy(ANCHOR_LOCAL); body.add(swordCar);
const swordGlow = glowSprite(0x7ff0ff, 1.2, swordCar); swordGlow.visible = false;
const hiltFree = makeSword(STUB); scene.add(hiltFree);
const shard = new THREE.Group(); const shardM = makeSword(SHARD, false); shardM.position.z = 2.25; shard.add(shardM); scene.add(shard);

// ------------------------------------------------------------------ 2D character (canvas texture on a billboard)
const CW = 1024, CH = 2048, PW = 1.1, PH = 2.2;
const ccan = document.createElement('canvas'); ccan.width = CW; ccan.height = CH;
const cc = ccan.getContext('2d');
const tmp = document.createElement('canvas'); tmp.width = CW; tmp.height = CH; const tc = tmp.getContext('2d');
const ctex = new THREE.CanvasTexture(ccan); ctex.colorSpace = THREE.SRGBColorSpace; ctex.anisotropy = 4;
const charMat = noOut(new THREE.MeshBasicMaterial({ map: ctex, transparent: true, alphaTest: 0.03, side: THREE.DoubleSide, fog: false }));
const charPlane = new THREE.Mesh(new THREE.PlaneGeometry(PW, PH), charMat); scene.add(charPlane);
const INK = '#1b1a26';

function limb(g, pts, w = 15, col = INK) {
  g.strokeStyle = col; g.lineWidth = w; g.lineCap = 'round'; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(pts[0], pts[1]);
  if (pts.length === 6) g.quadraticCurveTo(pts[2], pts[3], pts[4], pts[5]); else g.lineTo(pts[2], pts[3]);
  g.stroke();
}
function handD(g, x, y, open, glow) {
  if (glow) { g.save(); g.shadowColor = glow; g.shadowBlur = 50; g.fillStyle = glow; g.beginPath(); g.arc(x, y, 34, 0, 7); g.fill(); g.restore(); }
  g.fillStyle = '#fff'; g.strokeStyle = INK; g.lineWidth = 7;
  g.beginPath(); g.arc(x, y, 24, 0, 7); g.fill(); g.stroke();
  if (open) { for (let k = -1; k <= 1; k++) { g.beginPath(); g.moveTo(x + k * 12, y - 18); g.lineTo(x + k * 16, y - 42); g.lineWidth = 9; g.stroke(); } }
  else { g.lineWidth = 4; g.beginPath(); g.moveTo(x - 10, y - 6); g.lineTo(x + 12, y - 6); g.moveTo(x - 10, y + 4); g.lineTo(x + 12, y + 4); g.stroke(); }
}
function face(g, s, t) {
  const cx = 256, cy = 270;
  const e = s.expr || 'happy';
  const bl = (Math.floor(t * 10) % 38 === 0) ? 1 : 0;
  const lx = (s.look || [0, 0])[0] * 14, ly = (s.look || [0, 0])[1] * 10;
  g.fillStyle = INK; g.strokeStyle = INK; g.lineCap = 'round';
  const brow = (ang, y = 215) => { g.lineWidth = 10; for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(cx + sd * 78, y - sd * ang * -1 + (sd > 0 ? 0 : 0)); g.lineTo(cx + sd * 30, y + ang); g.stroke(); } };
  if (e === 'shock' || e === 'scared' || e === 'wow') {
    for (const sd of [-1, 1]) { g.fillStyle = '#fff'; g.lineWidth = 7; g.beginPath(); g.ellipse(cx + sd * 52, cy, 36, 44, 0, 0, 7); g.fill(); g.stroke(); g.fillStyle = INK; g.beginPath(); g.arc(cx + sd * 52 + lx, cy + 4 + ly, e === 'wow' ? 17 : 11, 0, 7); g.fill(); if (e === 'wow') { g.fillStyle = '#fff'; g.beginPath(); g.arc(cx + sd * 52 + lx + 6, cy - 2 + ly, 6, 0, 7); g.fill(); } }
    g.lineWidth = 10; for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(cx + sd * 25, 205); g.quadraticCurveTo(cx + sd * 52, 182, cx + sd * 82, 200); g.stroke(); }
    g.fillStyle = INK;
    if (e === 'scared') { g.lineWidth = 8; g.beginPath(); g.moveTo(cx - 40, 360); for (let k = 0; k <= 8; k++) g.lineTo(cx - 40 + k * 10, 360 + (k % 2 ? -8 : 8)); g.stroke(); }
    else { const m = s.mouth ?? 1; g.beginPath(); g.ellipse(cx, 360, 20 + 8 * m, 18 + 22 * m, 0, 0, 7); g.fill(); g.fillStyle = '#ff6b7a'; g.beginPath(); g.ellipse(cx, 372 + 10 * m, 12 + 4 * m, 7 + 6 * m, 0, 0, 7); g.fill(); }
  } else if (e === 'strain') {
    g.lineWidth = 9;
    for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(cx + sd * 76, 262); g.lineTo(cx + sd * 40, 280); g.lineTo(cx + sd * 76, 298); g.stroke(); }
    brow(16, 222);
    g.fillStyle = '#fff'; g.lineWidth = 7; g.beginPath(); g.roundRect(cx - 55, 335, 110, 46, 14); g.fill(); g.stroke();
    g.lineWidth = 4; g.beginPath(); g.moveTo(cx - 55, 358); g.lineTo(cx + 55, 358); for (let k = -2; k <= 2; k++) { g.moveTo(cx + k * 20, 335); g.lineTo(cx + k * 20, 381); } g.stroke();
  } else {
    // dot eyes family: happy, grin, determined, smug
    const lid = e === 'smug' ? 0.45 : e === 'determined' ? 0.25 : 0;
    for (const sd of [-1, 1]) {
      const ex = cx + sd * 50 + lx, ey = cy + 6 + ly;
      if (bl) { g.lineWidth = 8; g.beginPath(); g.moveTo(ex - 16, ey); g.lineTo(ex + 16, ey); g.stroke(); continue; }
      g.beginPath(); g.ellipse(ex, ey, 15, 21, 0, 0, 7); g.fill();
      g.fillStyle = '#fff'; g.beginPath(); g.arc(ex + 5, ey - 7, 5, 0, 7); g.fill(); g.fillStyle = INK;
      if (lid > 0) { g.fillStyle = '#fff'; g.fillRect(ex - 20, ey - 26, 40, 46 * lid); g.fillStyle = INK; g.lineWidth = 7; g.beginPath(); g.moveTo(ex - 20, ey - 26 + 46 * lid); g.lineTo(ex + 20, ey - 26 + 46 * lid); g.stroke(); }
    }
    if (e === 'determined') brow(14, 222);
    else if (e === 'smug') { g.lineWidth = 10; g.beginPath(); g.moveTo(cx - 80, 222); g.lineTo(cx - 28, 226); g.moveTo(cx + 28, 214); g.quadraticCurveTo(cx + 55, 196, cx + 82, 208); g.stroke(); }
    else { g.lineWidth = 10; for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(cx + sd * 28, 222); g.quadraticCurveTo(cx + sd * 52, 208, cx + sd * 78, 218); g.stroke(); } }
    g.lineWidth = 9;
    if (e === 'grin' || e === 'happy') {
      g.fillStyle = INK; g.beginPath(); g.moveTo(cx - 58, 335); g.quadraticCurveTo(cx, 345, cx + 58, 335); g.quadraticCurveTo(cx + 40, 400, cx, 402); g.quadraticCurveTo(cx - 40, 400, cx - 58, 335); g.fill();
      g.fillStyle = '#fff'; g.beginPath(); g.moveTo(cx - 50, 340); g.quadraticCurveTo(cx, 350, cx + 50, 340); g.lineTo(cx + 46, 356); g.quadraticCurveTo(cx, 362, cx - 46, 356); g.fill();
      g.fillStyle = '#ff6b7a'; g.beginPath(); g.ellipse(cx, 388, 22, 10, 0, 0, 7); g.fill();
    } else if (e === 'smug') { g.beginPath(); g.moveTo(cx - 40, 360); g.quadraticCurveTo(cx + 10, 372, cx + 52, 340); g.stroke(); }
    else { g.beginPath(); g.moveTo(cx - 36, 362); g.lineTo(cx + 36, 358); g.stroke(); }
  }
  // blush
  g.fillStyle = 'rgba(255,120,140,0.35)';
  for (const sd of [-1, 1]) { g.beginPath(); g.ellipse(cx + sd * 98, 330, 26, 14, 0, 0, 7); g.fill(); }
  if (s.sweat) {
    const k = (t * 1.5) % 1;
    g.fillStyle = '#7fd3ff'; g.strokeStyle = INK; g.lineWidth = 5;
    const sx = cx + 128, sy = 200 + k * 40;
    g.beginPath(); g.moveTo(sx, sy - 30); g.quadraticCurveTo(sx + 20, sy, sx, sy + 12); g.quadraticCurveTo(sx - 20, sy, sx, sy - 30); g.fill(); g.stroke();
  }
}
function drawChar(s, t) {
  const g = tc; g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, CW, CH); g.setTransform(2, 0, 0, 2, 0, 0);
  const cx = 256;
  g.save();
  if (s.clipY) { g.beginPath(); g.rect(0, 0, 512, s.clipY); g.clip(); }
  // legs
  if (s.legs !== false) {
    const sw = s.walk ? Math.sin(t * 12) * 30 : 0;
    limb(g, [cx - 24, 700, cx - 34 - sw, 850, cx - 30 - sw, 990], 15); limb(g, [cx + 24, 700, cx + 34 + sw, 850, cx + 30 + sw, 990], 15);
    g.fillStyle = INK; g.beginPath(); g.ellipse(cx - 44 - sw, 996, 30, 14, 0, 0, 7); g.fill(); g.beginPath(); g.ellipse(cx + 44 + sw, 996, 30, 14, 0, 0, 7); g.fill();
  }
  // torso (hoodie)
  g.fillStyle = '#ff7a2b'; g.strokeStyle = INK; g.lineWidth = 9;
  g.beginPath(); g.roundRect(cx - 72, 420, 144, 300, [40, 40, 26, 26]); g.fill(); g.stroke();
  g.fillStyle = '#2c4f9e'; g.beginPath(); g.roundRect(cx - 72, 680, 144, 46, [0, 0, 22, 22]); g.fill(); g.stroke();
  g.strokeStyle = '#d65a14'; g.lineWidth = 6; g.beginPath(); g.moveTo(cx - 40, 600); g.lineTo(cx + 40, 600); g.stroke();
  g.fillStyle = '#ffd23f'; g.strokeStyle = INK; g.lineWidth = 5; g.beginPath(); g.arc(cx, 520, 20, 0, 7); g.fill(); g.stroke(); // badge
  g.restore();
  // arms
  const arms = s.arms || { L: [cx - 100, 560, cx - 92, 660], R: [cx + 100, 560, cx + 92, 660] };
  for (const k of ['L', 'R']) {
    const a = arms[k]; if (!a) continue; const sx = cx + (k === 'L' ? -64 : 64);
    limb(g, [sx, 462, a[0], a[1], a[2], a[3]], 15);
    handD(g, a[2], a[3], k === 'R' ? s.openR : s.openL, k === 'R' ? s.glowR : null);
  }
  // head
  g.save(); g.translate(cx, 300); g.rotate(s.tilt || 0); g.translate(-cx, -300);
  g.fillStyle = '#fff'; g.strokeStyle = INK; g.lineWidth = 10;
  g.beginPath(); g.arc(cx, 270, 150, 0, 7); g.fill(); g.stroke();
  // hair: spiky tuft
  g.fillStyle = INK; g.beginPath(); g.moveTo(cx - 128, 205);
  const sp = [[-120, 120], [-95, 150], [-70, 75], [-40, 128], [-10, 60], [20, 125], [55, 70], [75, 135], [112, 105], [128, 200]];
  g.quadraticCurveTo(cx - 140, 130, cx - 92, 152);
  for (const [dx, dy] of sp) g.lineTo(cx + dx, dy + (dy < 100 ? -10 : 0));
  g.quadraticCurveTo(cx + 40, 140, cx - 128, 205); g.fill();
  face(g, s, t);
  g.restore();
  // final with optional aura
  const f = cc; f.setTransform(1, 0, 0, 1, 0, 0); f.clearRect(0, 0, CW, CH);
  if (s.aura) { f.save(); f.shadowColor = s.aura; f.shadowBlur = 70; f.drawImage(tmp, 0, 0); f.drawImage(tmp, 0, 0); f.restore(); }
  f.drawImage(tmp, 0, 0);
  ctex.needsUpdate = true;
}
// place billboard so canvas point (px,py in 512x1024 space) lands on world point P
const _r = V(0, 0, 0), _u = V(0, 0, 0), _f = V(0, 0, 0);
function placeChar(P, px, py, toward = 0.18) {
  cam.updateMatrixWorld();
  _r.setFromMatrixColumn(cam.matrixWorld, 0); _u.setFromMatrixColumn(cam.matrixWorld, 1);
  _f.copy(cam.position).sub(P).normalize();
  const ox = (px / 512 - 0.5) * PW, oy = (0.5 - py / 1024) * PH;
  charPlane.quaternion.copy(cam.quaternion);
  charPlane.position.copy(P).addScaledVector(_f, toward).addScaledVector(_r, -ox).addScaledVector(_u, -oy);
  // keep screen-projection of hand exactly on P: move along view ray compensation is small; fine.
}

// ------------------------------------------------------------------ props: hammer, glove, rings, energy, shockwave, mushroom, void
const hammer = new THREE.Group(); scene.add(hammer);
mesh(new RoundedBoxGeometry(1.4, 0.8, 0.8, 3, 0.12), toon(0x8d96a8), 0, 0, 0, hammer);
mesh(new THREE.CylinderGeometry(0.1, 0.1, 2.6, 10), toon(0xa0683a), 0, -1.6, 0, hammer);

const glove = new THREE.Group(); scene.add(glove);
mesh(new THREE.SphereGeometry(0.55, 20, 14), toon(0xe02a2a), 0, 0, 0, glove).scale.set(1.15, 1, 1);
mesh(new THREE.SphereGeometry(0.22, 12, 10), toon(0xe02a2a), 0.25, 0.25, 0.42, glove);
mesh(new THREE.CylinderGeometry(0.32, 0.36, 0.5, 16), toon(0xffffff), -0.6, 0, 0, glove).rotation.z = Math.PI / 2;
const spring = mesh(new THREE.CylinderGeometry(0.12, 0.12, 4, 8), toon(0x9aa2b2), -2.8, 0, 0, glove); spring.rotation.z = Math.PI / 2;

const rings = [];
for (let i = 0; i < 3; i++) {
  const m = noOut(new THREE.MeshBasicMaterial({ color: 0x3dff86, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  const r = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.025, 8, 48), m); scene.add(r); rings.push(r);
}
const handGlow = glowSprite(0x3dff86, 1.4);

const orb = glowSprite(0xfff1b8, 1); const orb2 = glowSprite(0xffffff, 1); const orbCore = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), noOut(new THREE.MeshBasicMaterial({ color: 0xffffff, fog: false })));
scene.add(orbCore);

const shockMat = noOut(new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: { a: { value: 1 } },
  vertexShader: `varying vec3 vN; varying vec3 vV; void main(){ vec4 mv=modelViewMatrix*vec4(position,1.); vN=normalize(normalMatrix*normal); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `uniform float a; varying vec3 vN; varying vec3 vV; void main(){ float f=pow(1.-abs(dot(vN,vV)),2.2); gl_FragColor=vec4(vec3(0.75,0.9,1.)*f*a*2.6+vec3(1.,.9,.7)*0.06*a,1.); }`,
}));
const shock = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2), shockMat); scene.add(shock);
const shockRing = new THREE.Mesh(new THREE.RingGeometry(0.9, 1, 96), noOut(new THREE.MeshBasicMaterial({ color: 0xfff0d0, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide })));
shockRing.rotation.x = -Math.PI / 2; scene.add(shockRing);
const dust = new THREE.Group(); scene.add(dust);
{ const R = rng(77); const DM = [toon(0xc9a27a, { transparent: true }), toon(0xb08b66, { transparent: true })]; for (let i = 0; i < 40; i++) { const d = mesh(new THREE.IcosahedronGeometry(1, 1), DM[i % 2], 0, 0, 0, dust); d.userData = { a: (i / 40) * Math.PI * 2 + R() * 0.1, s: 0.7 + R() * 0.8, h: R() }; d.castShadow = false; } }

const mush = new THREE.Group(); scene.add(mush);
const mushMats = [toon(0xff9a3c, { emissive: 0x7a2a00 }), toon(0xffc04d, { emissive: 0x804000 }), toon(0x8a7a70, { emissive: 0x2a1a10 }), toon(0x6f625c)];
{
  const R = rng(55);
  for (let i = 0; i < 14; i++) { const b = mesh(new THREE.IcosahedronGeometry(1, 1), mushMats[i % 2], 0, 0, 0, mush); b.userData = { k: 'stem', i, r: R() }; }
  for (let i = 0; i < 26; i++) { const b = mesh(new THREE.IcosahedronGeometry(1, 1), mushMats[i < 10 ? 1 : i < 18 ? 0 : 2], 0, 0, 0, mush); b.userData = { k: 'cap', i, a: R() * Math.PI * 2, r: R(), h: R() }; }
  for (let i = 0; i < 18; i++) { const b = mesh(new THREE.IcosahedronGeometry(1, 1), mushMats[3], 0, 0, 0, mush); b.userData = { k: 'base', i, a: (i / 18) * Math.PI * 2, r: R() }; }
}
const mushGlow = glowSprite(0xffb050, 60, mush);

const voidG = new THREE.Group(); scene.add(voidG);
const frags = [];
{
  const R = rng(91);
  for (let i = 0; i < 34; i++) {
    const g = new THREE.Group();
    const s = 0.6 + R() * 2.2;
    mesh(new THREE.BoxGeometry(s, s * 0.6, s * (0.7 + R() * 0.5)), toon(0x8a6a4a), 0, 0, 0, g);
    mesh(new THREE.BoxGeometry(s * 1.02, s * 0.15, s * (0.7 + R() * 0.5) * 1.02), toon(0x7fcf5c), 0, s * 0.32, 0, g);
    g.userData = { x: (R() - 0.5) * 50, y: -4 + R() * 6, z: -10 - R() * 40 + (R() < 0.3 ? 30 : 0), sp: 0.5 + R() * 1.5, rx: R() * 2, ry: R() * 2, ph: R() * 6 };
    voidG.add(g); frags.push(g);
  }
}
const voidOrb = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 24), noOut(new THREE.ShaderMaterial({
  uniforms: { t: { value: 0 } }, fog: false,
  vertexShader: `varying vec3 vN; varying vec3 vP; void main(){ vN=normalize(normalMatrix*normal); vP=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform float t; varying vec3 vN; varying vec3 vP;
    void main(){ float f=1.-abs(vN.z); float sw=sin(vP.x*9.+t*5.)*sin(vP.y*7.-t*4.)*sin(vP.z*8.+t*3.);
      vec3 c=mix(vec3(0.75,1.,0.85),vec3(0.1,1.,0.45),f); c=mix(c,vec3(0.7,0.25,1.),smoothstep(0.55,1.,f)*0.8); c+=sw*0.12;
      gl_FragColor=vec4(c,1.); }`,
})));
voidG.add(voidOrb);
const voidGlow = glowSprite(0x45ff8f, 20, voidG); const voidGlow2 = glowSprite(0xa040ff, 34, voidG);

// hero-sword studio (far above the world)
const studio = new THREE.Group(); studio.position.set(0, 600, 0); scene.add(studio);
const studioBg = new THREE.Mesh(new THREE.SphereGeometry(40, 32, 16), noOut(new THREE.ShaderMaterial({
  side: THREE.BackSide, fog: false, uniforms: { t: { value: 0 } },
  vertexShader: `varying vec3 vP; void main(){ vP=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform float t; varying vec3 vP; void main(){ vec3 d=normalize(vP); float r=length(d.xy); float a=atan(d.y,d.x);
    float rays=0.5+0.5*sin(a*14.+t*0.6); vec3 c=mix(vec3(0.22,0.62,1.0),vec3(0.05,0.12,0.42),smoothstep(0.,0.9,r));
    c+=rays*0.08*(1.-r); gl_FragColor=vec4(c,1.);} `,
})));
studio.add(studioBg);
const swordHero = new THREE.Group(); studio.add(swordHero); const _sh = makeSword(FULL); _sh.position.z = 1.9; const _shp = new THREE.Group(); _shp.rotation.x = Math.PI / 2; _shp.add(_sh); swordHero.add(_shp);
const heroShine = glowSprite(0xffffff, 1.5, studio);
const studioLight = new THREE.PointLight(0xffffff, 60, 30); studioLight.position.set(3, 4, 6); studio.add(studioLight);

// ------------------------------------------------------------------ particles (additive points)
const MAXP = 1600;
const pGeo = new THREE.BufferGeometry();
const pPos = new Float32Array(MAXP * 3), pCol = new Float32Array(MAXP * 3), pSize = new Float32Array(MAXP);
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
pGeo.setAttribute('color', new THREE.BufferAttribute(pCol, 3));
pGeo.setAttribute('size', new THREE.BufferAttribute(pSize, 1));
const points = new THREE.Points(pGeo, noOut(new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, vertexColors: true,
  vertexShader: `attribute float size; varying vec3 vC; void main(){ vC=color; vec4 mv=modelViewMatrix*vec4(position,1.); gl_PointSize=size*(1100./-mv.z); gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `varying vec3 vC; void main(){ float d=length(gl_PointCoord-.5); float a=smoothstep(.5,.0,d); gl_FragColor=vec4(vC*a*1.4,1.); }`,
})));
points.frustumCulled = false; scene.add(points);
let pN = 0;
function addP(p, col, size) { if (pN >= MAXP) return; pPos.set([p.x, p.y, p.z], pN * 3); pCol.set(col, pN * 3); pSize[pN] = size; pN++; }
// burst: deterministic sparks
function burst(t, t0, O, opt) {
  const age = t - t0; if (age < 0) return;
  const R = rng(opt.seed || 1);
  for (let i = 0; i < opt.n; i++) {
    const life = opt.life * (0.5 + R() * 0.5); const a = age; if (a > life) { R(); R(); R(); R(); continue; }
    const th = R() * Math.PI * 2, ph = (R() - 0.5) * Math.PI, sp = opt.speed * (0.3 + R() * 0.9);
    const d = opt.dir || V(0, 0, 0);
    const v = V(Math.cos(th) * Math.cos(ph) + d.x, Math.sin(ph) + d.y, Math.sin(th) * Math.cos(ph) + d.z).multiplyScalar(sp);
    const p = V(O.x + v.x * a, O.y + v.y * a - 0.5 * (opt.g ?? 9) * a * a, O.z + v.z * a);
    const k = 1 - a / life; const c = opt.col || [1, 0.8, 0.3];
    addP(p, [c[0] * k, c[1] * k, c[2] * k], (opt.size || 0.08) * (0.5 + k));
  }
}
// smoke puffs (toon spheres)
const SMOKE = []; const smokeMat = [];
for (let i = 0; i < 90; i++) { const m = toon(0xeeeeee, { transparent: true, opacity: 0.9 }); m.userData.outlineParameters = { visible: true }; smokeMat.push(m); const s = mesh(new THREE.IcosahedronGeometry(1, 1), m); s.castShadow = false; scene.add(s); SMOKE.push(s); }
let sN = 0;
function puffs(t, t0, t1, rate, originAt, opt) {
  const R = rng(opt.seed || 3);
  for (let ts = t0; ts < Math.min(t, t1); ts += 1 / rate) {
    const r1 = R(), r2 = R(), r3 = R(); const age = t - ts; const life = opt.life || 1.2; if (age > life || sN >= SMOKE.length) continue;
    const O = originAt(ts); const k = age / life; const v = opt.vel || V(0, 1, 0);
    const s = SMOKE[sN]; const m = smokeMat[sN]; sN++;
    s.visible = true; s.position.set(O.x + (v.x + (r1 - 0.5) * 1.5) * age, O.y + (v.y + r2 * 0.6) * age, O.z + (v.z + (r3 - 0.5) * 1.5) * age);
    s.scale.setScalar((opt.size || 0.5) * (0.4 + eo(k) * 1.6));
    m.color.set(opt.color || 0xeeeeee); m.opacity = 0.95 * (1 - k * k);
  }
}

// ------------------------------------------------------------------ captions
let WORDS = [];
const CHUNKS = [];
function buildChunks() {
  let cur = [];
  WORDS.forEach((w, i) => {
    cur.push(i);
    const nxt = WORDS[i + 1];
    const gap = nxt ? nxt[0] - w[1] : 9;
    if (cur.length >= 3 || /[.,?!]$/.test(w[2]) || gap > 0.2 || !nxt) { CHUNKS.push(cur); cur = []; }
  });
}
function drawCaption(t) {
  let ci = -1;
  for (let i = 0; i < CHUNKS.length; i++) {
    const c = CHUNKS[i]; const s = WORDS[c[0]][0] - 0.05; const nx = CHUNKS[i + 1]; const e = nx ? Math.min(WORDS[nx[0]][0] - 0.05, WORDS[c[c.length - 1]][1] + 0.5) : WORDS[c[c.length - 1]][1] + 0.6;
    if (t >= s && t < e) { ci = i; break; }
  }
  if (ci < 0) return;
  const c = CHUNKS[ci];
  const txt = c.map(i => WORDS[i][2]);
  const pop = eo(inv(WORDS[c[0]][0] - 0.05, WORDS[c[0]][0] + 0.08, t));
  o.save();
  o.font = '800 92px Toon'; o.textBaseline = 'middle'; o.lineJoin = 'round';
  const sp = 34; const ws = txt.map(s => o.measureText(s).width); const tot = ws.reduce((a, b) => a + b, 0) + sp * (txt.length - 1);
  const y = 1340;
  let x = W / 2 - tot / 2;
  o.translate(W / 2, y); o.scale(0.85 + 0.15 * back(pop), 0.85 + 0.15 * back(pop)); o.translate(-W / 2, -y);
  txt.forEach((s, k) => {
    const wi = c[k]; const act = t >= WORDS[wi][0] - 0.03 && t < (WORDS[wi + 1] ? Math.max(WORDS[wi][1], WORDS[wi + 1][0] - 0.03) : 99);
    const sc = act ? 1.06 : 1;
    o.save(); o.translate(x + ws[k] / 2, y); o.scale(sc, sc);
    o.lineWidth = 22; o.strokeStyle = '#000'; o.strokeText(s, -ws[k] / 2, 4);
    o.fillStyle = act ? '#ffe03a' : '#ffffff'; o.fillText(s, -ws[k] / 2, 0);
    o.restore();
    x += ws[k] + sp;
  });
  o.restore();
}

// ------------------------------------------------------------------ overlay fx
const _p = V(0, 0, 0);
function proj(v) { _p.copy(v).project(cam); return [(_p.x * 0.5 + 0.5) * W, (-_p.y * 0.5 + 0.5) * H, _p.z]; }
function flash(a, col = '255,255,255') { if (a <= 0) return; o.fillStyle = `rgba(${col},${clamp(a)})`; o.fillRect(0, 0, W, H); }
function vignette(a = 0.35) {
  const g = o.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.62);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${a})`); o.fillStyle = g; o.fillRect(0, 0, W, H);
}
function speedLines(t, a, cx = W / 2, cy = H / 2, seed = 1) {
  if (a <= 0) return; const R = rng(seed + Math.floor(t * 20));
  o.save(); o.strokeStyle = `rgba(255,255,255,${0.55 * a})`; o.lineCap = 'round';
  for (let i = 0; i < 40; i++) { const an = R() * Math.PI * 2, r0 = 520 + R() * 500, L = 150 + R() * 400; o.lineWidth = 3 + R() * 7; o.beginPath(); o.moveTo(cx + Math.cos(an) * r0, cy + Math.sin(an) * r0); o.lineTo(cx + Math.cos(an) * (r0 + L), cy + Math.sin(an) * (r0 + L)); o.stroke(); }
  o.restore();
}
function vhs(t, a) {
  if (a <= 0) return; const R = rng(Math.floor(t * 30));
  o.save(); o.globalAlpha = a;
  for (let i = 0; i < 6; i++) { const y = R() * H, h = 10 + R() * 60, dx = (R() - 0.5) * 120; o.drawImage(glc, 0, y, W, h, dx, y, W, h); }
  o.fillStyle = 'rgba(255,255,255,0.08)'; for (let y = 0; y < H; y += 6) o.fillRect(0, y, W, 2);
  o.fillStyle = 'rgba(0,30,80,0.18)'; o.fillRect(0, 0, W, H);
  o.fillStyle = '#fff'; o.strokeStyle = '#000'; o.lineWidth = 8;
  for (const dx of [0, 70]) { o.beginPath(); o.moveTo(150 + dx, 230); o.lineTo(210 + dx, 190); o.lineTo(210 + dx, 270); o.closePath(); o.stroke(); o.fill(); }
  o.font = '800 64px Toon'; o.lineWidth = 12; o.strokeText('REWIND', 300, 252); o.fillText('REWIND', 300, 252);
  o.restore();
}
function glitch(t, a, seed = 0) {
  if (a <= 0) return; const R = rng(seed + Math.floor(t * 30) * 13);
  o.save();
  const n = Math.floor(4 + a * 14);
  for (let i = 0; i < n; i++) { const y = R() * H, h = 8 + R() * 140, dx = (R() - 0.5) * 260 * a; o.drawImage(glc, 0, y, W, h, dx, y, W, h); }
  o.globalCompositeOperation = 'screen'; o.globalAlpha = 0.45 * a;
  o.drawImage(glc, 14 * a, 0); o.fillStyle = 'rgba(255,0,200,0.15)'; o.fillRect(0, 0, W, H);
  o.restore();
}
function lightning(A, B, seed, col, w = 8, jag = 60) {
  const R = rng(seed); const pts = [A]; const n = 9;
  for (let i = 1; i < n; i++) { const k = i / n; pts.push([lerp(A[0], B[0], k) + (R() - 0.5) * jag, lerp(A[1], B[1], k) + (R() - 0.5) * jag]); }
  pts.push(B);
  o.save(); o.lineCap = 'round'; o.lineJoin = 'round'; o.shadowColor = col; o.shadowBlur = 30;
  for (const [lw, c] of [[w * 2.2, col], [w * 0.7, '#ffffff']]) { o.strokeStyle = c; o.lineWidth = lw; o.beginPath(); pts.forEach((p, i) => i ? o.lineTo(p[0], p[1]) : o.moveTo(p[0], p[1])); o.stroke(); }
  o.restore();
}
function arrowPath(pts, k, col = '#ff2d3d') {
  // pts: screen points; draw progressively by fraction k
  if (k <= 0) return; let L = 0; const seg = []; for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d; }
  let rem = L * k; const out = [pts[0]];
  for (let i = 1; i < pts.length && rem > 0; i++) { const d = seg[i - 1]; const f = Math.min(1, rem / d); out.push([lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)]); rem -= d; }
  const e = out[out.length - 1], p = out[out.length - 2] || pts[0]; const an = Math.atan2(e[1] - p[1], e[0] - p[0]);
  o.save(); o.lineCap = 'round'; o.lineJoin = 'round';
  for (const [lw, c] of [[46, '#000'], [30, col]]) {
    o.strokeStyle = c; o.lineWidth = lw; o.beginPath(); out.forEach((q, i) => i ? o.lineTo(q[0], q[1]) : o.moveTo(q[0], q[1])); o.stroke();
    o.fillStyle = c; o.beginPath(); const s = lw * 1.9;
    o.moveTo(e[0] + Math.cos(an) * s * 0.9, e[1] + Math.sin(an) * s * 0.9); o.lineTo(e[0] + Math.cos(an + 2.4) * s, e[1] + Math.sin(an + 2.4) * s); o.lineTo(e[0] + Math.cos(an - 2.4) * s, e[1] + Math.sin(an - 2.4) * s); o.closePath(); o.fill();
  }
  o.restore();
}
function reticle(x, y, r, t, a) {
  if (a <= 0) return; o.save(); o.globalAlpha = a; o.translate(x, y); o.rotate(t * 1.5);
  for (const [lw, c] of [[18, '#000'], [9, '#ff2d3d']]) {
    o.strokeStyle = c; o.lineWidth = lw; o.beginPath(); o.arc(0, 0, r, 0, 7); o.stroke(); o.beginPath(); o.arc(0, 0, r * 0.45, 0, 7); o.stroke();
    for (let k = 0; k < 4; k++) { o.beginPath(); o.moveTo(0, r * 0.65); o.lineTo(0, r * 1.3); o.stroke(); o.rotate(Math.PI / 2); }
  }
  o.restore();
}
function cracksOv(t, a, seed, cx, cy, col = '#e9fff1') {
  if (a <= 0) return; const R = rng(seed);
  o.save(); o.lineCap = 'round'; o.lineJoin = 'round'; o.shadowColor = '#45ff8f'; o.shadowBlur = 25;
  for (let i = 0; i < 12; i++) {
    let x = cx, y = cy; const an0 = (i / 12) * Math.PI * 2 + R(); const L = (300 + R() * 900) * a;
    o.strokeStyle = col; o.lineWidth = 9 * (1 - i / 30); o.beginPath(); o.moveTo(x, y);
    let d = 0; let an = an0; while (d < L) { const st = 40 + R() * 70; an += (R() - 0.5) * 0.9; x += Math.cos(an) * st; y += Math.sin(an) * st; d += st; o.lineTo(x, y); }
    o.stroke();
  }
  o.restore();
}

// ------------------------------------------------------------------ camera
function setCam(p, l, fov = 50, roll = 0, shake = 0, t = 0) {
  const s = shake;
  cam.position.set(p.x + s * (Math.sin(t * 61) + Math.sin(t * 37)) * 0.5, p.y + s * (Math.sin(t * 53 + 1) + Math.sin(t * 29)) * 0.5, p.z + s * Math.sin(t * 47 + 2) * 0.5);
  cam.up.set(Math.sin(roll), Math.cos(roll), 0);
  cam.lookAt(l.x, l.y, l.z);
  if (roll) cam.rotateZ(roll);
  cam.fov = fov; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
}

// ------------------------------------------------------------------ timeline
const HITX = TX - 0.6 - ANCHOR_LOCAL.x - 0.03; // car.x where blade meets trunk
const T = {
  s2: 2.45, s3: 3.85, snap: 5.19, rip: 5.73, s4: 6.95, s4b: 7.35, s5: 9.08, s6: 10.95, s7: 13.1, force: 13.97,
  s8: 16.0, hit8: 16.95, s8b: 17.75, s9: 18.75, s9b: 20.4, s10: 21.92, split: 22.61, s11: 23.65, s11b: 24.0, s12: 25.9,
  bend: 27.2, stop: 27.85, energy: 28.75, s13: 30.85, unleash: 31.27, nuke: 33.72, s14: 35.15, reality: 36.55, contain: 38.2, end: 39.35,
};

function carState(x, opts = {}) {
  car.position.set(x, opts.y || 0, CAR_Z);
  car.rotation.set(opts.rx || 0, opts.ry || 0, opts.rz || 0);
  carPivot.rotation.z = -(opts.pitch || 0);
  const spin = opts.spin ?? (x / 0.46);
  wheels.forEach(w => { w.spin.rotation.z = -spin; w.gl.visible = !!opts.glow; if (opts.glow) w.gl.scale.setScalar(1.6 + 0.6 * Math.sin(opts.t * 40 + w.wg.position.x)); });
  hubMats.forEach(m => { m.emissive.set(opts.glow ? 0x8a2be2 : 0x000000); m.color.set(opts.glow ? 0xe0b3ff : 0xd8dde6); });
  car.updateMatrixWorld(true);
}
const anchorW = () => swordCar.getWorldPosition(V(0, 0, 0));
const CONTACT = V(TX - 0.6, 1.55, -3.75);

function charInCar(t, st) {
  // character leaning out of the window, right hand on the grip
  const P = st.handPos || anchorW();
  const s = Object.assign({ expr: 'happy', legs: false, clipY: 505, arms: { L: [150, 470, 175, 500], R: [380, 470, 440, 400] } }, st);
  if (st.lurch) { P.x += st.lurch; }
  drawChar(s, t);
  const hp = s.arms.R ? [s.arms.R[2], s.arms.R[3]] : [440, 400];
  placeChar(P, hp[0], hp[1], st.toward ?? 0.2);
  charPlane.visible = true;
}

function resetFrame() {
  pN = 0; sN = 0; SMOKE.forEach(s => (s.visible = false));
  road.visible = true; sky.visible = true; scene.fog = FOG;
  skyU.top.value.set(0x2f86e0); skyU.bot.value.set(0xd6f0ff); skyU.stars.value = 0; skyU.tint.value.set(0, 0, 0);
  FOG.color.set(0xcfeaff); FOG.near = 70; FOG.far = 330;
  hemi.intensity = 1.7; sun.intensity = 2.6; sun.color.set(0xfff3dc); hemi.color.set(0xeaf6ff);
  car.visible = true; swordCar.visible = true; swordGlow.visible = false; BLADE.emissive.set(0); BLADE.color.set(0xe9f0f8);
  hiltFree.visible = false; shard.visible = false; charPlane.visible = false; hammer.visible = false; glove.visible = false;
  rings.forEach(r => (r.visible = false)); handGlow.visible = false; orb.visible = false; orb2.visible = false; orbCore.visible = false;
  shock.visible = false; shockRing.visible = false; dust.visible = false; mush.visible = false; voidG.visible = false; studio.visible = false;
  cracks.visible = false; heroAura.visible = false;
  halfA.position.set(0, 0, 0); halfB.position.set(0, 0, 0); halfA.rotation.set(0, 0, 0); halfB.rotation.set(0, 0, 0); hero.position.set(TX, 0, TZ);
  heroGlowMats.forEach(m => m.emissive.set(0));
  bgTrees.forEach(b => b.rotation.set(0, 0, 0));
  RED.emissive.set(0);
}
function sunFollow(x, z = 0) { sun.position.set(x + 12, 30, z - 14); sun.target.position.set(x, 0, z); sun.target.updateMatrixWorld(); }

// overlay jobs gathered during scene setup
let OV = [];

function shot(t) {
  OV = [];
  let shake = 0;
  // ---------- S1: car with sword driving
  if (t < T.s2) {
    const lt = t;
    const x = HITX + 14 * (t - T.snap); carState(x, { t });
    const k = eo(inv(0, 2.4, lt));
    const fov = lerp(64, 48, eo(inv(0, 0.6, lt)));
    const m = eio(inv(0.85, 1.9, lt));
    setCam(V(x + lerp(4.4, 3.6, m), lerp(1.35, 3.1, m), CAR_Z - lerp(5.8, 6.4, m)), V(x + lerp(0.9, 0.4, m), lerp(1.55, 1.3, m), lerp(0.2, -1.2, m)), fov, 0.04, 0.02, t);
    charInCar(t, { expr: lt < 1.1 ? 'happy' : 'grin', look: [-0.6, 0.2] });
    sunFollow(x);
    OV.push(() => speedLines(t, 0.6));
  }
  // ---------- S2: aiming for a tree (over-shoulder)
  else if (t < T.s3) {
    const lt = t - T.s2; const x = HITX + 14 * (t - T.snap); carState(x, { t });
    setCam(V(x - 3.2, 2.35, CAR_Z - 1.9), V(TX, 2.4, TZ + 0.3), lerp(38, 30, lt / 1.4), 0, 0.015, t);
    charInCar(t, { expr: 'determined', look: [1, 0], toward: 0.3 });
    sunFollow(x + 8);
    const tp = proj(V(TX, 2.2, TZ));
    OV.push(() => reticle(tp[0], tp[1], lerp(150, 95, eo(inv(0, 0.5, lt))), t, eo(inv(0.05, 0.35, lt))));
    OV.push(() => speedLines(t, 0.4));
  }
  // ---------- S3: snap and rip
  else if (t < T.s4) {
    const lt = t - T.s3;
    if (t < T.snap) {
      const k = inv(T.s3, T.snap, t);
      const x = HITX - 16 * Math.pow(1 - k, 1.5); carState(x, { t, spin: x / 0.46 });
      setCam(V(TX + 3.8, 1.25, TZ + 1.4), V(TX - 3.5, 1.5, -0.6), lerp(46, 40, k), 0, 0.01, t);
      charInCar(t, { expr: 'determined', look: [1, 0] });
      sunFollow(TX);
    } else {
      const x = HITX + 14 * (t - T.snap); carState(x, { t });
      const after = t - T.snap;
      swordCar.visible = false;
      // hilt: rides the car until rip, then flies off
      const A = anchorW();
      hiltFree.visible = true;
      if (t < T.rip) { hiltFree.position.copy(A); hiltFree.rotation.set(0, 0, Math.sin(after * 60) * 0.06); }
      else { const a = t - T.rip; const A0 = V(HITX + 14 * (T.rip - T.snap) + ANCHOR_LOCAL.x, 1.55, ANCHOR_LOCAL.z + CAR_Z); hiltFree.position.set(A0.x + 3 * a, A0.y + 6 * a - 6 * a * a, A0.z - 2.5 * a); hiltFree.rotation.set(a * 9, a * 4, a * 13); }
      // shard flies up from the tree
      shard.visible = true; const sa = after; shard.position.set(CONTACT.x - 1.5 * sa, CONTACT.y + 7 * sa - 7 * sa * sa, CONTACT.z - 1.0 * sa + 0.35); shard.rotation.set(sa * 3, sa * 14, sa * 2);
      burst(t, T.snap, CONTACT, { n: 140, speed: 7, life: 0.7, seed: 4, size: 0.09, col: [1, 0.85, 0.4] });
      if (t < T.rip + 0.05) {
        setCam(V(TX + 3.8, 1.25, TZ + 1.4), V(TX - 2.5 + after * 2, 1.7, -1.2), lerp(36, 44, eo(inv(0, 0.5, after))), 0.05 * Math.sin(after * 30) * (1 - inv(0, 0.4, after)), 0.18 * (1 - inv(0, 0.35, after)), t);
        charInCar(t, { expr: 'shock', mouth: 0.6, handPos: A, arms: { L: [150, 470, 175, 500], R: [380, 470, 440, 400] } });
      } else {
        const a = t - T.rip;
        setCam(V(x + 2.2, 2.0, CAR_Z - 4.4), V(x + 0.1, 1.75, -0.2), 40, 0, 0.12 * (1 - inv(0, 0.3, a)), t);
        const P = A.clone();
        charInCar(t, { expr: 'shock', mouth: 1, handPos: P, openR: true, arms: { L: [130, 430, 120, 330], R: [380, 470, 440, 400] }, look: [-1, -0.2], sweat: true });
        OV.push(() => speedLines(t, 0.35));
      }
      sunFollow(x);
      shake = 0;
      OV.push(() => flash(1 - inv(T.snap, T.snap + 0.12, t)));
    }
  }
  // ---------- S4: rewind, then the unbreakable sword on a pedestal of light
  else if (t < T.s5) {
    if (t < T.s4b) {
      const k = inv(T.s4, T.s4b, t); const tr = lerp(6.9, 4.4, eio(k));
      shot(tr); // replay backwards
      const prev = OV; OV = [...prev.filter(Boolean), () => vhs(t, 1)];
      return;
    }
    const lt = t - T.s4b; road.visible = false; car.visible = false; sky.visible = false; scene.fog = null; studio.visible = true;
    studioBg.material.uniforms.t.value = t;
    swordHero.rotation.set(0.1, lt * 1.1 + 0.4, -0.35 + Math.sin(lt * 1.3) * 0.05);
    const hitT = 8.12;
    let sh = 0;
    if (t < hitT + 0.6) {
      hammer.visible = true; const hk = inv(hitT - 0.38, hitT, t); const rec = inv(hitT, hitT + 0.5, t);
      const m = t < hitT ? 1 - ei(hk) : eo(rec);
      hammer.position.set(0.85 + 2.2 * m, 600.3 + 1.6 * m, 0.3);
      hammer.rotation.set(0, 0, 0.4 + 0.9 * m);
      sh = 0.12 * (1 - inv(hitT, hitT + 0.35, t)) * (t > hitT ? 1 : 0);
    }
    burst(t, hitT, V(0.12, 600.3, 0.3), { n: 120, speed: 6, life: 0.6, seed: 9, size: 0.06, col: [1, 0.95, 0.6], g: 4 });
    const glowK = inv(hitT, hitT + 0.3, t);
    BLADE.emissive.setRGB(0.25 * glowK, 0.55 * glowK, 0.75 * glowK);
    heroShine.position.set(0.05, lerp(-1.9, 1.9, inv(hitT + 0.1, hitT + 0.8, t)), 0.4); heroShine.scale.setScalar(t > hitT ? 1.4 : 0.001);
    setCam(V(0.3, 600.4, lerp(6.6, 5.6, inv(T.s4b, T.s5, t))), V(0, 600.1, 0), 42, 0, sh, t);
    OV.push(() => flash(0.7 * (1 - inv(hitT, hitT + 0.15, t)) * (t >= hitT ? 1 : 0)));
    // sparkles
    OV.push(() => { if (t > hitT) { const R = rng(5); for (let i = 0; i < 26; i++) { const ph = R() * 6, x = 120 + R() * 840, y = 500 + R() * 800; const a = Math.max(0, Math.sin(t * 5 + ph)); star(x, y, 18 + 26 * a, a); } } });
  }
  // ---------- S5: indestructible grip
  else if (t < T.s6) {
    const lt = t - T.s5; const x = -80 + 13 * lt; carState(x, { t });
    swordGlow.visible = false; BLADE.emissive.setRGB(0.1, 0.25, 0.32);
    const A = anchorW();
    const gk = inv(9.6, 10.0, t); const sq = t > 10.4 ? Math.max(0, 1 - (t - 10.4) * 3) : 0;
    setCam(V(A.x + lerp(2.6, 2.0, eo(inv(T.s5, T.s6, t))), A.y + 0.35, A.z - lerp(3.0, 2.4, eo(inv(T.s5, T.s6, t)))), V(A.x - 0.25, A.y + 0.15, A.z + 0.3), 42, -0.05, 0.01 + 0.05 * sq, t);
    charInCar(t, { expr: t < 10.35 ? 'determined' : 'grin', glowR: gk > 0 ? `rgba(61,255,134,${gk})` : null, look: [-0.4, 0.4] });
    if (gk > 0) {
      handGlow.visible = true; handGlow.position.copy(A).add(V(0, 0, -0.1)); handGlow.scale.setScalar(1.2 + 0.4 * gk + 0.4 * sq + 0.1 * Math.sin(t * 20));
      rings.forEach((r, i) => { r.visible = true; r.position.copy(A); r.rotation.set(t * (1.5 + i) + i, t * (2 + i * 0.7), i); r.scale.setScalar(gk * (1 + i * 0.25) * (1 + 0.3 * sq)); r.material.opacity = 0.8 * gk; });
      burst(t, 9.65, A, { n: 50, speed: 1.4, life: 1.0, seed: 12, size: 0.03, col: [0.3, 1, 0.55], g: -1 });
    }
    sunFollow(x);
    OV.push(() => speedLines(t, 0.25));
  }
  // ---------- S6: immovable body (glove test)
  else if (t < T.s7) {
    const lt = t - T.s6; const X0 = -40;
    carState(X0 + 4, { t, spin: 0 }); swordCar.visible = true;
    const feet = V(X0, 0, -1.6);
    setCam(V(X0 + lerp(0.4, 0.1, lt / 2), 1.4, -1.6 - lerp(4.6, 4.0, eo(lt / 2))), V(X0 - 0.5, 1.2, -1.6), 46, 0, 0, t);
    const hitT = 12.4; const ak = inv(11.2, 11.9, t);
    const glk = inv(hitT - 0.28, hitT, t); const rec = inv(hitT, hitT + 0.6, t);
    glove.visible = true;
    let gx = t < hitT ? lerp(-5.5, -0.75, ei(glk)) : lerp(-0.75, -4.5, eo(rec));
    glove.position.set(X0 + gx, 1.75, -1.6); glove.rotation.set(0, 0, 0);
    const squash = t >= hitT ? Math.max(0, 1 - (t - hitT) * 5) : 0; glove.scale.set(1 - 0.35 * squash, 1 + 0.25 * squash, 1 + 0.25 * squash);
    const st = { expr: t < 11.9 ? 'determined' : 'smug', legs: true, aura: ak > 0 ? `rgba(80,170,255,${0.9 * ak})` : null, arms: { L: [180, 600, 210, 700], R: [332, 600, 302, 700] }, look: [-0.8, 0] };
    drawChar(st, t); placeChar(feet, 256, 1000, 0.0); charPlane.visible = true;
    burst(t, hitT, V(X0 - 0.3, 1.8, -1.6), { n: 70, speed: 5, life: 0.5, seed: 21, size: 0.06, col: [1, 1, 0.7] });
    shake = t > hitT ? 0.08 * (1 - inv(hitT, hitT + 0.3, t)) : 0;
    setCam(cam.position.clone(), V(X0 - 0.5, 1.2, -1.6), 46, 0, shake, t);
    placeChar(feet, 256, 1000, 0.0);
    sunFollow(X0);
    OV.push(() => { if (t > hitT && t < hitT + 0.35) impactStar(proj(V(X0 - 0.35, 1.8, -1.6)), 1 - inv(hitT, hitT + 0.35, t)); });
  }
  // ---------- S7: hit → force transfers to the car
  else if (t < T.s8) {
    const lt = t - T.s7;
    const x = t < T.force ? HITX - 3.2 * (T.force - t) : HITX; carState(x, { t, spin: (t < T.force ? x : HITX) / 0.46 });
    BLADE.emissive.setRGB(0.1, 0.25, 0.32);
    const sh = t > T.force ? 0.1 * (1 - inv(T.force, T.force + 0.5, t)) : 0;
    setCam(V(TX - lerp(8.5, 7.5, eo(lt / 2.9)), 4.6, TZ - 5.5), V(TX - 1.6, 1.2, -1.6), 46, 0, sh, t);
    charInCar(t, { expr: t < T.force ? 'determined' : 'strain', look: [1, 0] });
    burst(t, T.force, CONTACT, { n: 90, speed: 6, life: 0.6, seed: 31, size: 0.08 });
    sunFollow(TX);
    const A = anchorW();
    const pts = [proj(CONTACT), proj(A), proj(V(x - 0.4, 1.0, CAR_Z)), proj(V(x - 3.2, 1.0, CAR_Z))];
    const ak = inv(14.5, 15.8, t);
    if (t > 15.3) RED.emissive.setRGB(0.35 * Math.abs(Math.sin(t * 12)), 0, 0);
    OV.push(() => arrowPath(pts.map(p => [p[0], p[1]]), eio(ak)));
    OV.push(() => { if (t > T.force && t < T.force + 0.3) impactStar(proj(CONTACT), 1 - inv(T.force, T.force + 0.3, t)); });
  }
  // ---------- S8: screech to a halt
  else if (t < T.s9) {
    if (t < T.s8b) {
      const x = t < T.hit8 ? HITX - 15 * (T.hit8 - t) : HITX;
      const a = t - T.hit8;
      const pitch = a > 0 ? 0.42 * Math.exp(-a * 3.2) * Math.abs(Math.sin(a * 5.2 + 0.25)) : 0;
      carState(x, { t, pitch, spin: (t < T.hit8 ? x : HITX + Math.max(0, a) * 6) / 0.46 });
      BLADE.emissive.setRGB(0.1, 0.25, 0.32);
      setCam(V(TX - 13, 3.2, TZ - 4.5), V(TX - 3.5, 1.2, 0.3), 44, 0, a > 0 ? 0.14 * Math.exp(-a * 3) : 0, t);
      charInCar(t, { expr: a > 0 ? 'shock' : 'determined', mouth: 0.8, lurch: 0 });
      if (a > 0) {
        puffs(t, T.hit8, T.hit8 + 0.7, 40, () => V(HITX - 1.42 + 1.4, 0.3, CAR_Z - 0.95), { seed: 41, life: 0.9, size: 0.45, vel: V(-1.5, 1.2, -0.8) });
        puffs(t, T.hit8, T.hit8 + 0.7, 30, () => V(HITX - 1.42 + 1.4, 0.3, CAR_Z + 0.95), { seed: 42, life: 0.9, size: 0.45, vel: V(-1.5, 1.2, 0.8) });
        burst(t, T.hit8, CONTACT, { n: 110, speed: 7, life: 0.6, seed: 43, size: 0.09 });
      }
      sunFollow(TX);
    } else {
      const lt = t - T.s8b; carState(HITX, { t, spin: HITX / 0.46 });
      BLADE.emissive.setRGB(0.1, 0.25, 0.32);
      setCam(V(CONTACT.x - 1.6, CONTACT.y + 0.6, CONTACT.z + 1.5), V(CONTACT.x, CONTACT.y, CONTACT.z), lerp(42, 34, eo(lt / 1)), 0, 0.03, t);
      const hT = 18.02;
      burst(t, hT, CONTACT, { n: 120, speed: 5, life: 0.6, seed: 44, size: 0.05 });
      OV.push(() => { if (t > hT && t < hT + 0.35) impactStar(proj(CONTACT), 1 - inv(hT, hT + 0.35, t)); });
      OV.push(() => flash(0.5 * (1 - inv(hT, hT + 0.12, t)) * (t > hT ? 1 : 0)));
      sunFollow(TX);
    }
  }
  // ---------- S9: car can't stop — wheels burn
  else if (t < T.s10) {
    const spin = (t - T.s9) * 70; const jit = Math.sin(t * 90) * 0.015;
    carState(HITX + jit, { t, spin, glow: t > 19.3, pitch: 0.02 + Math.sin(t * 50) * 0.01 });
    BLADE.emissive.setRGB(0.1, 0.25, 0.32);
    const rw = V(HITX - 1.42 + 1.4 - 1.4, 0.46, CAR_Z - 0.92); // rear near wheel
    if (t < T.s9b) {
      setCam(V(rw.x + 1.7, 0.6, rw.z - 2.2), V(rw.x - 0.2, 0.5, rw.z), lerp(46, 38, inv(T.s9, T.s9b, t)), 0, 0.04, t);
    } else {
      setCam(V(HITX + 7.5, 2.0, CAR_Z - 7.5), V(HITX + 0.3, 1.0, -0.8), 46, 0, 0.05, t);
      charInCar(t, { expr: 'strain', sweat: true });
      const c = proj(V(HITX + 0.5, 1.2, CAR_Z)); const f = proj(V(HITX + 4.5, 1.2, CAR_Z));
      OV.push(() => arrowPath([[c[0], c[1]], [f[0], f[1]]], eo(inv(T.s9b + 0.6, T.s9b + 1.2, t)), '#ffcc00'));
    }
    for (const [i, w] of wheels.entries()) if (w.wg.position.x < 0) {
      const wp = w.wg.getWorldPosition(V(0, 0, 0)); wp.y = 0.1;
      puffs(t, T.s9 - 0.6, T.s10, 22, () => V(wp.x - 0.7, wp.y, wp.z + 0.3), { seed: 50 + i, life: 1.1, size: 0.35, vel: V(-3, 1.4, 0), color: 0xdcd3e6 });
      burst(t, 19.3, wp, { n: 70, speed: 4, life: 0.5, seed: 60 + i, size: 0.05, col: [0.8, 0.4, 1], dir: V(-1, 0.6, 0) });
      burst(t, 20.1, wp, { n: 70, speed: 4, life: 0.5, seed: 70 + i, size: 0.05, col: [0.8, 0.4, 1], dir: V(-1, 0.6, 0) });
      burst(t, 20.9, wp, { n: 70, speed: 4, life: 0.5, seed: 80 + i, size: 0.05, col: [0.8, 0.4, 1], dir: V(-1, 0.6, 0) });
    }
    sunFollow(HITX);
  }
  // ---------- S10: the tree splits
  else if (t < T.s11) {
    const k = inv(T.split, T.split + 0.6, t);
    const x = HITX + eo(inv(T.split, T.split + 1.0, t)) * 2.5; carState(x, { t, spin: (t - T.s9) * 70, glow: true });
    BLADE.emissive.setRGB(0.1, 0.25, 0.32);
    splitTree(k);
    setCam(V(TX - 6.5, 2.2, TZ - 11), V(TX - 0.6, 2.8, TZ + 0.5), 50, 0, k > 0 && k < 1 ? 0.1 : 0.02, t);
    charInCar(t, { expr: t > T.split + 0.2 ? 'wow' : 'strain' });
    burst(t, T.split, V(TX, 1.6, TZ), { n: 120, speed: 6, life: 0.9, seed: 91, size: 0.1, col: [1, 0.75, 0.4] });
    puffs(t, T.split, T.split + 0.4, 50, () => V(TX, 0.6, TZ), { seed: 92, life: 1.2, size: 0.7, vel: V(0, 1.5, 0), color: 0xd9c2a0 });
    sunFollow(TX);
  }
  // ---------- S11: rewind — the tree is indestructible too
  else if (t < T.s12) {
    if (t < T.s11b) { const k = inv(T.s11, T.s11b, t); shot(lerp(23.6, 22.5, k)); OV.push(() => vhs(t, 1)); return; }
    const lt = t - T.s11b;
    carState(HITX, { t, spin: t * 70, glow: true });
    BLADE.emissive.setRGB(0.1, 0.25, 0.32);
    const gk = inv(24.5, 24.9, t);
    heroGlowMats.forEach(m => m.emissive.setRGB(0.05 * gk, (0.35 + 0.15 * Math.sin(t * 9)) * gk, 0.12 * gk));
    heroAura.visible = gk > 0; heroAura.scale.setScalar(16 * gk); heroAura.material.opacity = 0.6 * gk;
    const an = lerp(-0.9, -0.2, eo(lt / 1.9));
    setCam(V(TX + Math.sin(an) * 12, 1.2, TZ - Math.cos(an) * 12), V(TX - 0.8, 3.4, TZ + 0.5), 52, 0, 0.02, t);
    charInCar(t, { expr: 'strain', sweat: true });
    for (let i = 0; i < 4; i++) burst(t, 24.6 + i * 0.3, V(TX, 3 + i * 0.6, TZ), { n: 40, speed: 2.4, life: 0.8, seed: 100 + i, size: 0.08, col: [0.3, 1, 0.5], g: -1 });
    sunFollow(TX);
    OV.push(() => { if (gk > 0 && t < 25.4) shieldSweep(t, inv(24.6, 25.3, t)); });
  }
  // ---------- S12: no way to break, bend or stop — energy builds
  else if (t < T.s13) {
    carState(HITX + Math.sin(t * 90) * 0.02, { t, spin: t * 70, glow: true });
    BLADE.emissive.setRGB(0.2, 0.45, 0.6);
    heroGlowMats.forEach(m => m.emissive.setRGB(0.03, 0.2, 0.08));
    const ek = inv(T.energy, T.s13, t);
    const vib = Math.sin(t * 80) * 0.008;
    swordCar.position.copy(ANCHOR_LOCAL).add(V(0, vib, 0));
    if (t < T.bend) {
      const lt = t - T.s12;
      setCam(V(CONTACT.x - 2.0, CONTACT.y + 0.9, CONTACT.z + 1.9), V(CONTACT.x, CONTACT.y, CONTACT.z), lerp(40, 30, eo(lt / 1.3)), 0, 0.03, t);
    } else if (t < T.stop) {
      const A = anchorW();
      setCam(V(A.x - 3.2, 3.0, (A.z + CONTACT.z) / 2 - 1.0), V(A.x, 1.5, (A.z + CONTACT.z) / 2), 46, 0, 0.02, t);
      charInCar(t, { expr: 'strain', sweat: true });
    } else if (t < T.energy) {
      const rw = V(HITX - 1.42, 0.46, CAR_Z - 0.92);
      setCam(V(rw.x + 1.6, 0.7, rw.z - 1.9), V(rw.x - 0.2, 0.45, rw.z), 40, 0, 0.05, t);
      const wp = V(rw.x, 0.1, rw.z);
      puffs(t, T.stop - 0.8, T.energy, 25, () => wp, { seed: 120, life: 1.0, size: 0.5, vel: V(-3, 1.4, 0), color: 0xdcd3e6 });
      burst(t, T.stop, wp, { n: 80, speed: 4, life: 0.5, seed: 121, size: 0.05, col: [0.8, 0.4, 1], dir: V(-1, 0.6, 0) });
    } else {
      const d = lerp(2.5, 13, eio(ek));
      setCam(V(CONTACT.x - d * 0.75, CONTACT.y + d * 0.35, CONTACT.z - d * 0.7), V(CONTACT.x, CONTACT.y + 0.4, CONTACT.z), 46, 0, 0.03 + 0.25 * ek, t);
      cracks.visible = true; cracks.scale.setScalar(0.1 + 1.2 * eo(ek));
      skyU.tint.value.setRGB(0.25 * ek, 0.02 * ek, -0.2 * ek); FOG.color.setRGB(0.81 + 0.15 * ek, 0.9 - 0.2 * ek, 1 - 0.5 * ek);
      hemi.color.setRGB(1, 0.92 - 0.2 * ek, 0.86 - 0.4 * ek);
      charInCar(t, { expr: 'scared', sweat: true });
    }
    // energy orb at the contact point
    const ok = inv(T.s12, T.s13, t);
    const pul = 1 + 0.15 * Math.sin(t * 30);
    orb.visible = orb2.visible = orbCore.visible = true;
    orb.position.copy(CONTACT); orb2.position.copy(CONTACT); orbCore.position.copy(CONTACT);
    orb.scale.setScalar((0.6 + 6 * ei(ok) + 2.5 * ek) * pul); orb2.scale.setScalar((0.3 + 2.5 * ei(ok)) * pul); orbCore.scale.setScalar(0.05 + 0.5 * ei(ok) + 0.6 * ek);
    for (let i = 0; i < 6; i++) burst(t, T.s12 + i * 0.8, CONTACT, { n: 50, speed: 5 + i, life: 0.5, seed: 130 + i, size: 0.05 });
    if (t > T.energy) {
      const C = proj(CONTACT); const R = rng(Math.floor(t * 15));
      OV.push(() => { const n = 2 + Math.floor(ek * 6); for (let i = 0; i < n; i++) { const an = R() * 6.28, L = 200 + R() * 500 * (0.4 + ek); lightning([C[0], C[1]], [C[0] + Math.cos(an) * L, C[1] + Math.sin(an) * L], Math.floor(t * 15) * 7 + i, '#ffcf4a', 5 + 4 * ek); } });
    }
    sunFollow(TX);
    OV.push(() => flash(ei(inv(30.3, T.s13, t)) * 0.9));
  }
  // ---------- S13: shockwave → nuclear
  else if (t < T.s14) {
    carState(HITX, { t, spin: t * 70, glow: true });
    if (t < T.unleash) {
      // engulfed by light
      setCam(V(CONTACT.x - 4, CONTACT.y + 2, CONTACT.z - 4), CONTACT, lerp(46, 20, inv(T.s13, T.unleash, t)), 0, 0.3, t);
      orb.visible = orb2.visible = true; orb.position.copy(CONTACT); orb2.position.copy(CONTACT); orb.scale.setScalar(12 + 30 * inv(T.s13, T.unleash, t)); orb2.scale.setScalar(5 + 10 * inv(T.s13, T.unleash, t));
      OV.push(() => flash(0.85 + 0.15 * inv(T.s13, T.unleash, t)));
    } else if (t < T.nuke) {
      const k = inv(T.unleash, T.nuke, t); const Rr = 4 + 150 * eo(k);
      const C0 = V(TX - 0.6, 0, TZ + 0.2);
      shock.visible = true; shock.position.copy(C0); shock.scale.setScalar(Rr); shockMat.uniforms.a.value = 1 - 0.6 * k;
      shockRing.visible = true; shockRing.position.set(C0.x, 0.2, C0.z); shockRing.scale.setScalar(Rr * 1.02); shockRing.material.opacity = 1 - k;
      dust.visible = true; dust.position.copy(C0);
      dust.children.forEach(d => { const u = d.userData; const rr = Rr * (0.92 + 0.1 * u.h); d.position.set(Math.cos(u.a) * rr, 1 + u.h * 3, Math.sin(u.a) * rr); d.scale.setScalar(u.s * (3 + Rr * 0.07)); d.material.opacity = 0.9 * (1 - k * 0.7); });
      bgTrees.forEach(b => { const dx = b.position.x - C0.x, dz = b.position.z - C0.z; const dd = Math.hypot(dx, dz); if (dd < Rr) { const ang = Math.min(1.35, (Rr - dd) * 0.2); const ax = V(dz / dd, 0, -dx / dd); b.setRotationFromAxisAngle(ax, ang); } });
      // tree survives (indestructible), car gets blown back a bit
      carState(HITX - 2 * eo(inv(T.unleash, T.unleash + 0.5, t)), { t, rz: 0.15 * eo(k), glow: true });
      heroGlowMats.forEach(m => m.emissive.setRGB(0.05, 0.3, 0.1));
      skyU.top.value.setRGB(0.95, 0.55, 0.25); skyU.bot.value.setRGB(1, 0.85, 0.6); FOG.color.setRGB(1, 0.8, 0.55); FOG.near = 120; FOG.far = 700;
      hemi.color.setRGB(1, 0.85, 0.65); sun.color.setRGB(1, 0.8, 0.6);
      setCam(V(C0.x - 45 - 30 * k, 22 + 18 * k, C0.z - 40 - 25 * k), V(C0.x, 0, C0.z), 52, 0, 0.6 * (1 - k) + 0.1, t);
      OV.push(() => flash(1 - inv(T.unleash, T.unleash + 0.4, t)));
      orb.visible = true; orb.position.copy(CONTACT); orb.scale.setScalar(30 * (1 - k) + 8);
    } else {
      const k = inv(T.nuke, T.s14, t);
      const C0 = V(TX - 0.6, 0, TZ + 0.2);
      bgTrees.forEach(b => { const dx = b.position.x - C0.x, dz = b.position.z - C0.z; const dd = Math.hypot(dx, dz); const ang = Math.min(1.35, Math.max(0, (154 - dd) * 0.2)); if (ang > 0) b.setRotationFromAxisAngle(V(dz / dd, 0, -dx / dd), ang); });
      car.visible = false; charPlane.visible = false;
      mush.visible = true; mush.position.copy(C0);
      const rise = eo(inv(T.nuke - 0.1, T.s14 + 0.3, t)); const top = 15 + 85 * rise;
      mush.children.forEach(b => {
        const u = b.userData; if (!u.k) return;
        if (u.k === 'stem') { b.position.set(Math.sin(u.i * 2.1) * 2, (u.i / 14) * top, Math.cos(u.i * 1.7) * 2); b.scale.setScalar(5 + 3 * u.r + 3 * rise); }
        if (u.k === 'cap') { const rr = (10 + 22 * rise) * (0.3 + 0.7 * u.r); b.position.set(Math.cos(u.a) * rr, top + (u.h - 0.4) * 14 * (0.5 + rise), Math.sin(u.a) * rr); b.scale.setScalar(9 + 9 * rise * (0.6 + u.r)); }
        if (u.k === 'base') { const rr = 12 + 50 * rise; b.position.set(Math.cos(u.a) * rr, 3, Math.sin(u.a) * rr); b.scale.setScalar(6 + 8 * u.r + 6 * rise); }
      });
      mushGlow.position.set(0, top * 0.8, 0); mushGlow.scale.setScalar(80 + 60 * rise);
      skyU.top.value.setRGB(0.7, 0.3, 0.2); skyU.bot.value.setRGB(1, 0.7, 0.4); FOG.color.setRGB(1, 0.72, 0.45); FOG.near = 200; FOG.far = 1400;
      hemi.color.setRGB(1, 0.8, 0.6); sun.color.setRGB(1, 0.75, 0.5);
      setCam(V(C0.x - 230 + 30 * k, 6, C0.z - 170 + 20 * k), V(C0.x, 45 + 10 * k, C0.z), 52, 0, 0.6 * (1 - inv(T.nuke, T.nuke + 0.8, t)) + 0.1, t);
      OV.push(() => flash(0.9 * (1 - inv(34.28, 34.6, t)) * (t > 34.28 ? 1 : 0), '255,240,200'));
      OV.push(() => flash(0.8 * (1 - inv(T.nuke, T.nuke + 0.2, t)), '255,240,200'));
    }
    sunFollow(TX);
  }
  // ---------- S14: reality breaks
  else {
    road.visible = false; voidG.visible = true; scene.fog = null;
    skyU.top.value.setRGB(0.08, 0.0, 0.16); skyU.bot.value.setRGB(0.35, 0.05, 0.45); skyU.stars.value = 1;
    hemi.color.setRGB(0.7, 0.5, 1); hemi.intensity = 1.4; sun.color.setRGB(0.6, 1, 0.75); sun.intensity = 2.2;
    const lt = t - T.s14;
    const C0 = V(0, 3, -30);
    voidG.position.set(0, 0, 0); voidOrb.position.copy(C0); voidOrb.material.uniforms.t.value = t;
    const grow = t < T.contain ? 3 + 1.2 * lt + 0.5 * Math.sin(t * 6) : 3 + 1.2 * (T.contain - T.s14) + 40 * ei(inv(T.contain, T.end, t));
    voidOrb.scale.setScalar(grow);
    voidGlow.position.copy(C0); voidGlow.scale.setScalar(grow * 4.5); voidGlow2.position.copy(C0); voidGlow2.scale.setScalar(grow * 8);
    frags.forEach(f => { const u = f.userData; const pull = ei(inv(T.contain, T.end, t)); f.position.set(lerp(u.x, C0.x, pull), lerp(u.y + lt * u.sp, C0.y, pull), lerp(u.z, C0.z, pull)); f.rotation.set(u.rx * t, u.ry * t, 0); f.scale.setScalar(1 - pull * 0.9); });
    // the car and our hero float in the void
    const pull = ei(inv(T.contain, T.end, t));
    const cp = V(lerp(-6, C0.x, pull), lerp(0.5 + lt * 0.6, C0.y, pull), lerp(-8, C0.z, pull));
    car.position.copy(cp); car.position.z += 0; car.rotation.set(lt * 0.25, -0.6 + lt * 0.1, lt * 0.2);
    carPivot.rotation.z = 0; wheels.forEach(w => (w.spin.rotation.z = -t * 20)); car.updateMatrixWorld(true);
    hubMats.forEach(m => m.emissive.set(0x8a2be2));
    const camP = V(lerp(-3, -2, lt / 4), lerp(3, 4, lt / 4), lerp(8, 4, eio(inv(T.s14, T.contain, t))));
    setCam(camP, V(C0.x * 0.5 - 2, C0.y + 1, C0.z * 0.6), lerp(50, 44, lt / 4), Math.sin(t * 0.8) * 0.06, 0.04 + 0.2 * pull + (t > T.reality && t < T.reality + 0.4 ? 0.2 : 0), t);
    const A = anchorW();
    drawChar({ expr: 'scared', sweat: true, legs: true, arms: { L: [150, 520, 120, 420], R: [380, 470, 440, 400] }, look: [0.5, -0.3], tilt: Math.sin(t * 1.5) * 0.15 }, t);
    placeChar(A, 440, 400, 0.2); charPlane.visible = true;
    const C = proj(C0);
    OV.push(() => { const R = rng(Math.floor(t * 12)); const n = 5; for (let i = 0; i < n; i++) { const an = R() * 6.28, L = 300 + R() * 600; lightning([C[0], C[1]], [C[0] + Math.cos(an) * L, C[1] + Math.sin(an) * L], Math.floor(t * 12) * 11 + i, i % 2 ? '#b44dff' : '#46ff8f', 6); } });
    OV.push(() => cracksOv(t, eo(inv(T.reality, T.reality + 0.6, t)), 777, C[0], C[1]));
    OV.push(() => glitch(t, Math.max(1 - inv(T.s14, T.s14 + 0.35, t), t > T.reality && t < T.reality + 0.25 ? 1 : 0, t > 37.06 && t < 37.2 ? 0.8 : 0, pull)));
    OV.push(() => flash(ei(inv(T.contain + 0.4, T.end, t)), '220,255,230'));
    OV.push(() => { if (t >= T.end) { o.fillStyle = '#000'; o.fillRect(0, 0, W, H); const k = 1 - inv(T.end, T.end + 0.8, t); const g = o.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, 300); g.addColorStop(0, `rgba(80,255,150,${0.5 * k})`); g.addColorStop(1, 'rgba(0,0,0,0)'); o.fillStyle = g; o.fillRect(0, 0, W, H); } });
  }
}

function splitTree(k) {
  const a = eo(k);
  halfA.position.z = -0.9 * a; halfA.rotation.x = -0.5 * a;
  halfB.position.z = 0.9 * a; halfB.rotation.x = 0.5 * a;
}
function star(x, y, r, a) { o.save(); o.globalAlpha = a; o.fillStyle = '#fff'; o.shadowColor = '#bff'; o.shadowBlur = 20; o.beginPath(); for (let i = 0; i < 8; i++) { const rr = i % 2 ? r * 0.25 : r; const an = i * Math.PI / 4; o.lineTo(x + Math.cos(an) * rr, y + Math.sin(an) * rr); } o.closePath(); o.fill(); o.restore(); }
function impactStar(p, a) {
  if (a <= 0) return; const [x, y] = p; const r = 160 * (1.3 - a * 0.3);
  o.save(); o.globalAlpha = a; o.translate(x, y);
  for (const [s, c] of [[1, '#000'], [0.85, '#fff36b'], [0.55, '#fff']]) { o.fillStyle = c; o.beginPath(); for (let i = 0; i < 20; i++) { const rr = (i % 2 ? r * 0.45 : r) * s; const an = i * Math.PI / 10; o.lineTo(Math.cos(an) * rr, Math.sin(an) * rr); } o.closePath(); o.fill(); }
  o.restore();
}
function shieldSweep(t, k) {
  o.save(); o.globalCompositeOperation = 'lighter';
  const x = lerp(-300, W + 300, k); const g = o.createLinearGradient(x - 200, 0, x + 200, 0);
  g.addColorStop(0, 'rgba(60,255,140,0)'); g.addColorStop(0.5, 'rgba(120,255,170,0.35)'); g.addColorStop(1, 'rgba(60,255,140,0)');
  o.fillStyle = g; o.translate(W / 2, H / 2); o.rotate(-0.35); o.translate(-W / 2, -H / 2); o.fillRect(-400, -400, W + 800, H + 800); o.restore();
}

window.renderFrame = (t) => {
  resetFrame();
  shot(t);
  pGeo.setDrawRange(0, pN); pGeo.attributes.position.needsUpdate = true; pGeo.attributes.color.needsUpdate = true; pGeo.attributes.size.needsUpdate = true;
  sky.position.copy(cam.position);
  effect.render(scene, cam);
  o.clearRect(0, 0, W, H);
  OV.forEach(f => f && f());
  vignette(0.32);
  drawCaption(t);
};

(async () => {
  WORDS = await (await fetch('/words.json')).json(); buildChunks();
  const f = new FontFace('Toon', 'url(/font.woff2)', { weight: '800' }); await f.load(); document.fonts.add(f);
  window.ready = true;
})();
