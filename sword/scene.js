import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const W = 720, H = 1280;
const TM = await (await fetch('timing.json')).json();
const T = TM.T;

// ---------- math helpers ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const rng = (t, a, b) => clamp((t - a) / (b - a));
const sm = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const eout = x => 1 - Math.pow(1 - clamp(x), 3);
const ein = x => Math.pow(clamp(x), 3);
const lerp = (a, b, t) => a + (b - a) * t;
const hash = n => { n = Math.sin(n * 127.1 + 311.7) * 43758.5453; return n - Math.floor(n); };
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const mix3 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];

// ---------- renderer ----------
const renderer = new THREE.WebGLRenderer({antialias: true, preserveDrawingBuffer: true});
renderer.setSize(W, H); renderer.setPixelRatio(1);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 0.85;
document.getElementById('wrap').prepend(renderer.domElement);

const scene = new THREE.Scene();
const pm = new THREE.PMREMGenerator(renderer);
scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.35;
scene.fog = new THREE.Fog(0xcfe6ff, 70, 420);
const camera = new THREE.PerspectiveCamera(50, W / H, 0.1, 900);

const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, {type: THREE.HalfFloatType, samples: 4}));
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.22, 0.5, 1.7);
composer.addPass(bloom);
composer.addPass(new OutputPass());

// ---------- sky ----------
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: {top: {value: new THREE.Color(0x3d86e6)}, hor: {value: new THREE.Color(0xd3e9ff)}},
  vertexShader: 'varying vec3 p;void main(){p=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
  fragmentShader: 'varying vec3 p;uniform vec3 top;uniform vec3 hor;void main(){float h=clamp(normalize(p).y*1.6,0.,1.);gl_FragColor=vec4(mix(hor,top,pow(h,.7)),1.);}'
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(600, 24, 16), skyMat); scene.add(sky);

// ---------- lights ----------
const hemi = new THREE.HemisphereLight(0xbfdcff, 0x5b7a3a, 0.9); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff0d6, 2.1);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, {left: -14, right: 14, top: 14, bottom: -14, near: 1, far: 90});
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03; sun.shadow.radius = 3;
scene.add(sun, sun.target);
const fill = new THREE.DirectionalLight(0x9ec4ff, 0.5); fill.position.set(12, 6, -20); scene.add(fill);

// ---------- textures ----------
function ctex(w, h, fn, rx = 1, ry = 1) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  fn(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
const grassTex = ctex(256, 256, (g, w, h) => {
  g.fillStyle = '#5da637'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 1400; i++) { g.fillStyle = `hsla(${88 + hash(i) * 30},55%,${30 + hash(i + 9) * 22}%,.35)`; g.fillRect(hash(i + 3) * w, hash(i + 5) * h, 2 + hash(i + 7) * 6, 2 + hash(i + 11) * 6); }
}, 120, 120);
const asphaltTex = ctex(256, 256, (g, w, h) => {
  g.fillStyle = '#3b3e46'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 1800; i++) { const l = 30 + hash(i) * 30; g.fillStyle = `hsla(220,6%,${l}%,.35)`; g.fillRect(hash(i + 3) * w, hash(i + 5) * h, 2, 2); }
}, 200, 2);
const barkTex = ctex(128, 256, (g, w, h) => {
  g.fillStyle = '#7a5535'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 90; i++) { g.fillStyle = `hsla(25,35%,${15 + hash(i) * 30}%,.55)`; g.fillRect(hash(i + 1) * w, 0, 2 + hash(i + 2) * 5, h); }
}, 2, 3);
const dotTex = ctex(64, 64, (g, w, h) => {
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.35, 'rgba(255,255,255,.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
});
const puffTex = ctex(128, 128, (g, w, h) => {
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,255,255,.95)'); gr.addColorStop(.55, 'rgba(255,255,255,.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
});

// ---------- world ----------
const mk = (geo, mat, shadow = true) => { const m = new THREE.Mesh(geo, mat); m.castShadow = shadow; m.receiveShadow = true; return m; };
const ground = mk(new THREE.PlaneGeometry(1200, 1200), new THREE.MeshStandardMaterial({map: grassTex, roughness: 1}), false);
ground.rotation.x = -Math.PI / 2; ground.position.y = -0.01; scene.add(ground);
const road = mk(new THREE.PlaneGeometry(1200, 8), new THREE.MeshStandardMaterial({map: asphaltTex, roughness: .9}), false);
road.rotation.x = -Math.PI / 2; road.position.y = 0.005; scene.add(road);
const whiteMat = new THREE.MeshStandardMaterial({color: 0xf4f4f0, roughness: .7});
for (const z of [-4.15, 4.15]) { const c = mk(new THREE.BoxGeometry(1200, 0.16, 0.25), whiteMat, false); c.position.set(0, 0.08, z); scene.add(c); }
const dashG = new THREE.BoxGeometry(2.6, 0.012, 0.16);
const dashes = new THREE.InstancedMesh(dashG, new THREE.MeshStandardMaterial({color: 0xf0f0e0, roughness: .8}), 220);
{ const m = new THREE.Matrix4(); for (let i = 0; i < 220; i++) { m.makeTranslation(-300 + i * 5.5, 0.012, 0.6); dashes.setMatrixAt(i, m); } }
dashes.receiveShadow = true; scene.add(dashes);

// stylized trees
const leafCols = [0x4fa53a, 0x62b645, 0x3f9438, 0x7cc552];
function makeLeafyTree(scale, seed, hasShadow = true) {
  const g = new THREE.Group();
  const trunk = mk(new THREE.CylinderGeometry(0.25, 0.4, 3.2, 10), new THREE.MeshStandardMaterial({map: barkTex, roughness: 1}), hasShadow); trunk.position.y = 1.6; g.add(trunk);
  for (let i = 0; i < 5; i++) {
    const r = 1.1 + hash(seed + i) * 0.7; const b = mk(new THREE.IcosahedronGeometry(r, 1), new THREE.MeshStandardMaterial({color: leafCols[(i + seed) % 4], roughness: .85, flatShading: false}), hasShadow);
    b.position.set((hash(seed + i * 3) - .5) * 2, 3.8 + hash(seed + i * 5) * 1.5, (hash(seed + i * 7) - .5) * 2); g.add(b);
  }
  g.scale.setScalar(scale); return g;
}
const farTrees = [];
for (let i = 0; i < 46; i++) {
  const x = -160 + hash(i * 3.1) * 320, z = -14 - hash(i * 1.7) * 90 - (i % 5) * 6;
  const t = makeLeafyTree(0.9 + hash(i) * 0.8, i, false); t.position.set(x, 0, z); scene.add(t); farTrees.push(t);
}
for (let i = 0; i < 16; i++) {
  const t = makeLeafyTree(1 + hash(i + 50) * 0.6, i + 50, false); t.position.set(-140 + hash(i * 5.3) * 280, 0, 12 + hash(i * 2.2) * 40); scene.add(t);
}
const hillMat = new THREE.MeshStandardMaterial({color: 0x6aa86a, roughness: 1});
for (let i = 0; i < 6; i++) {
  const h = mk(new THREE.SphereGeometry(1, 20, 12), hillMat, false); h.scale.set(60 + hash(i) * 40, 14 + hash(i + 3) * 18, 30); h.position.set(-220 + i * 90, -2, -260); scene.add(h);
}
// clouds
for (let i = 0; i < 9; i++) {
  const c = new THREE.Sprite(new THREE.SpriteMaterial({map: puffTex, color: 0xffffff, opacity: .8, depthWrite: false, fog: false}));
  c.scale.set(70 + hash(i) * 50, 18, 1); c.position.set(-250 + i * 70, 90 + hash(i + 2) * 40, -300); scene.add(c);
}

// ---------- hero tree ----------
const TX = 0, TZ = -5, CUT_Y = 1.1;
const treeG = new THREE.Group(); treeG.position.set(TX, 0, TZ); scene.add(treeG);
const trunkMat = new THREE.MeshStandardMaterial({map: barkTex, roughness: 1, emissive: 0x000000});
const leafMats = leafCols.map(c => new THREE.MeshStandardMaterial({color: c, roughness: .85, emissive: 0x000000}));
const stump = mk(new THREE.CylinderGeometry(0.52, 0.64, CUT_Y, 16), trunkMat); stump.position.y = CUT_Y / 2; treeG.add(stump);
const cutCap = mk(new THREE.CircleGeometry(0.52, 16), new THREE.MeshStandardMaterial({color: 0xe0b878, roughness: .8})); cutCap.rotation.x = -Math.PI / 2; cutCap.position.y = CUT_Y + 0.002; cutCap.visible = false; treeG.add(cutCap);
const upperPivot = new THREE.Group(); upperPivot.position.set(0.52, CUT_Y, 0); treeG.add(upperPivot);
const upper = new THREE.Group(); upper.position.x = -0.52; upperPivot.add(upper);
const upTrunk = mk(new THREE.CylinderGeometry(0.34, 0.52, 3.0, 16), trunkMat); upTrunk.position.y = 1.5; upper.add(upTrunk);
for (let i = 0; i < 4; i++) {
  const br = mk(new THREE.CylinderGeometry(0.07, 0.14, 1.6, 8), trunkMat); const a = i * 1.7 + 0.5;
  br.position.set(Math.cos(a) * 0.6, 2.6 + i * 0.2, Math.sin(a) * 0.6); br.rotation.set(Math.sin(a) * 0.9, 0, -Math.cos(a) * 0.9); upper.add(br);
}
for (let i = 0; i < 7; i++) {
  const r = 1.2 + hash(i + 70) * 0.9; const b = mk(new THREE.IcosahedronGeometry(r, 2), leafMats[i % 4]);
  b.position.set((hash(i * 3 + 70) - .5) * 3, 4.0 + hash(i * 5 + 70) * 1.5, (hash(i * 7 + 70) - .5) * 3); upper.add(b);
}
const kerf = new THREE.Mesh(new THREE.BoxGeometry(1, 0.05, 1.1), new THREE.MeshBasicMaterial({color: 0xffb060})); kerf.visible = false; scene.add(kerf);

// ---------- stickman ----------
const JOINTS = ['head', 'neck', 'hip', 'lel', 'lha', 'rel', 'rha', 'lkn', 'lft', 'rkn', 'rft'];
const LIMBS = [['hip', 'neck'], ['neck', 'lel'], ['lel', 'lha'], ['neck', 'rel'], ['rel', 'rha'], ['hip', 'lkn'], ['lkn', 'lft'], ['hip', 'rkn'], ['rkn', 'rft']];
class Stick {
  constructor(R = 0.045, headR = 0.19) {
    this.g = new THREE.Group();
    this.mat = new THREE.MeshStandardMaterial({color: 0xffffff, roughness: .45, emissive: 0x2a2a2a});
    this.ol = new THREE.MeshBasicMaterial({color: 0x050505, side: THREE.BackSide});
    const cg = new THREE.CylinderGeometry(R, R, 1, 12), co = new THREE.CylinderGeometry(R + .017, R + .017, 1, 12);
    this.limbs = LIMBS.map(() => { const g = new THREE.Group(); const m = new THREE.Mesh(cg, this.mat); m.castShadow = true; g.add(m, new THREE.Mesh(co, this.ol)); this.g.add(g); return g; });
    const sg = new THREE.SphereGeometry(1, 20, 14); this.jt = {};
    for (const k of JOINTS) {
      const g = new THREE.Group(); const r = k === 'head' ? headR : (k.endsWith('ha') || k.endsWith('ft')) ? R * 1.5 : R * 1.12;
      const m = new THREE.Mesh(sg, this.mat); m.scale.setScalar(r); m.castShadow = true;
      const o = new THREE.Mesh(sg, this.ol); o.scale.setScalar(r + 0.02); g.add(m, o); this.g.add(g); this.jt[k] = g;
    }
  }
  pose(P) {
    for (const k of JOINTS) this.jt[k].position.set(...P[k]);
    LIMBS.forEach(([a, b], i) => {
      const A = V(...P[a]), B = V(...P[b]), d = B.clone().sub(A), L = d.length(), g = this.limbs[i];
      g.position.copy(A).addScaledVector(d, .5); g.scale.set(1, L, 1);
      g.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize());
    });
  }
  glow(col, k) { this.mat.emissive.set(col).multiplyScalar(k); if (k === 0) this.mat.emissive.set(0x2a2a2a); }
}

// ---------- car ----------
const CZ = -1.8;
const car = new THREE.Group(); scene.add(car);
const bodyMat = new THREE.MeshStandardMaterial({color: 0xf08a24, metalness: .12, roughness: .55});
const darkMat = new THREE.MeshStandardMaterial({color: 0x23262d, roughness: .8});
const glassMat = new THREE.MeshStandardMaterial({color: 0xaed3ff, transparent: true, opacity: .16, roughness: .05, depthWrite: false});
const add = (geo, mat, x, y, z, parent = car) => { const m = mk(geo, mat); m.position.set(x, y, z); parent.add(m); return m; };
add(new THREE.BoxGeometry(4.3, 0.55, 1.8), bodyMat, 0, 0.62, 0);
add(new THREE.BoxGeometry(1.3, 0.3, 1.74), bodyMat, 1.5, 1.02, 0);
add(new THREE.BoxGeometry(0.95, 0.28, 1.74), bodyMat, -1.65, 1.0, 0);
add(new THREE.BoxGeometry(2.2, 0.08, 1.7), bodyMat, -0.25, 1.68, 0);
for (const [x, z] of [[-1.25, .82], [-1.25, -.82], [0.85, .82], [0.85, -.82]]) add(new THREE.BoxGeometry(0.09, 0.7, 0.09), bodyMat, x, 1.33, z);
add(new THREE.BoxGeometry(2.3, 0.04, 1.6), darkMat, -0.15, 0.4, 0);
add(new THREE.BoxGeometry(0.3, 0.5, 1.4), darkMat, -0.65, 0.95, 0);   // seat back
add(new THREE.BoxGeometry(0.6, 0.12, 1.2), darkMat, -0.35, 0.72, 0);
add(new THREE.BoxGeometry(0.09, 0.35, 0.5), darkMat, 0.55, 1.05, 0).rotation.z = -0.6; // wheel
const sideGlass = add(new THREE.PlaneGeometry(2.0, 0.66), glassMat, -0.2, 1.3, 0.83); // near (camera) side
const wind = add(new THREE.PlaneGeometry(1.6, 0.66), glassMat, 0.9, 1.3, 0); wind.rotation.y = Math.PI / 2; wind.rotation.z = 0;
for (const z of [-.7, .7]) { const l = add(new THREE.SphereGeometry(0.12, 12, 8), new THREE.MeshStandardMaterial({color: 0xfff6c8, emissive: 0xfff0a0, emissiveIntensity: .6}), 2.15, 0.78, z); l.castShadow = false; }
add(new THREE.BoxGeometry(0.1, 0.12, 1.5), new THREE.MeshStandardMaterial({color: 0x15171c}), 2.17, 0.5, 0);
const tyreMat = new THREE.MeshStandardMaterial({color: 0x15161a, roughness: .9});
const rimMat = new THREE.MeshStandardMaterial({color: 0xc9ced6, metalness: .8, roughness: .3, emissive: 0x000000});
const wheels = [];
for (const [x, z] of [[1.4, .85], [1.4, -.85], [-1.4, .85], [-1.4, -.85]]) {
  const wg = new THREE.Group(); wg.position.set(x, 0.38, z); car.add(wg);
  const spin = new THREE.Group(); wg.add(spin);
  const tyre = mk(new THREE.CylinderGeometry(0.38, 0.38, 0.28, 24), tyreMat); tyre.rotation.x = Math.PI / 2; spin.add(tyre);
  const rim = mk(new THREE.CylinderGeometry(0.24, 0.24, 0.3, 16), rimMat); rim.rotation.x = Math.PI / 2; spin.add(rim);
  for (let s = 0; s < 5; s++) { const sp = mk(new THREE.BoxGeometry(0.4, 0.05, 0.31), darkMat); sp.rotation.z = s * Math.PI / 5; spin.add(sp); }
  wheels.push(spin);
}
const driver = new Stick(); car.add(driver.g);
const passenger = null;

// driver poses (car-local)
function driverPose(jx = 0, jy = 0, jz = 0, look = 0) {
  const hx = 0.2;
  return {
    hip: [hx, .8, -.45], neck: [hx + .05, 1.25, -.45], head: [hx + .1 + look * .05, 1.5, -.45],
    lel: [hx + .35, 1.05, -.95], lha: [0.62 + jx, 1.1 + jy, -1.2 + jz],
    rel: [hx + .5, 1.05, -.2], rha: [0.62, 1.1, -.35],
    lkn: [hx + .65, .85, -.55], lft: [hx + .8, .42, -.55], rkn: [hx + .65, .85, -.35], rft: [hx + .8, .42, -.35]
  };
}

// ---------- sword ----------
const swordG = new THREE.Group(); scene.add(swordG);
const bladeMat = new THREE.MeshStandardMaterial({color: 0xd7dde6, metalness: 1, roughness: .18, emissive: 0x000000});
const goldMat = new THREE.MeshStandardMaterial({color: 0xd9a63a, metalness: .9, roughness: .3});
const swordA = new THREE.Group(), swordB = new THREE.Group();
swordG.add(swordA, swordB);
const bladeA = mk(new THREE.BoxGeometry(0.2, 0.05, 1.5), bladeMat); bladeA.position.z = -0.75; swordA.add(bladeA);
add(new THREE.BoxGeometry(0.6, 0.09, 0.09), goldMat, 0, 0, 0.02, swordA);
add(new THREE.CylinderGeometry(0.05, 0.05, 0.36, 10), new THREE.MeshStandardMaterial({color: 0x3a2418, roughness: .8}), 0, 0, 0.22, swordA).rotation.x = Math.PI / 2;
add(new THREE.SphereGeometry(0.09, 12, 8), goldMat, 0, 0, 0.42, swordA);
const bladeB = mk(new THREE.BoxGeometry(0.2, 0.05, 1.35), bladeMat); bladeB.position.z = -0.675; swordB.add(bladeB);
const tip = mk(new THREE.ConeGeometry(0.1414, 0.25, 4), bladeMat); tip.rotation.x = -Math.PI / 2; tip.rotation.y = Math.PI / 4; tip.scale.set(1, 1, 0.22); tip.position.z = -1.475; swordB.add(tip);
swordB.position.z = -1.5;
function setSwordGlow(col, k) { bladeMat.emissive.set(col).multiplyScalar(k); }

// ---------- observer stickman ----------
const observer = new Stick(); scene.add(observer.g); observer.g.visible = false;
function standPose(arms = 0, lean = 0, ph = 0) {
  const sw = Math.sin(ph) * 0.03;
  return {
    hip: [0, 0.95, 0], neck: [lean * .3, 1.62, 0], head: [lean * .45, 1.9, 0],
    lel: [-.28, lerp(1.3, 1.85, arms), 0.05], lha: [-.4, lerp(1.0, 2.35, arms), .12],
    rel: [.28, lerp(1.3, 1.85, arms), 0.05], rha: [.4, lerp(1.0, 2.35, arms), .12],
    lkn: [-.12, .5, sw], lft: [-.16, 0.05, 0], rkn: [.12, .5, -sw], rft: [.16, 0.05, 0]
  };
}

// ---------- FX pools ----------
const MAXS = 700;
const sparkGeo = new THREE.BufferGeometry();
const sparkPos = new Float32Array(MAXS * 3), sparkCol = new Float32Array(MAXS * 3);
sparkGeo.setAttribute('position', new THREE.BufferAttribute(sparkPos, 3)); sparkGeo.setAttribute('color', new THREE.BufferAttribute(sparkCol, 3));
const sparkPts = new THREE.Points(sparkGeo, new THREE.PointsMaterial({size: .16, map: dotTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, vertexColors: true, fog: false}));
sparkPts.frustumCulled = false; scene.add(sparkPts);
let nS = 0;
function spark(o, u, n, speed, life, seed, dir = null, spread = 1, col = [1, .7, .25], g = 9.8) {
  for (let i = 0; i < n && nS < MAXS; i++) {
    const a = hash(seed + i * 1.3) * 6.283, b = (hash(seed + i * 2.7) - .5) * 2, r = Math.sqrt(1 - b * b);
    let d = V(Math.cos(a) * r, b, Math.sin(a) * r);
    if (dir) d = dir.clone().normalize().multiplyScalar(1 - spread).add(d.multiplyScalar(spread));
    const sp = speed * (0.35 + hash(seed + i * 4.1) * 0.9), age = u - hash(seed + i * 5.9) * 0.08;
    if (age < 0 || age > life) continue;
    const p = o.clone().addScaledVector(d, sp * age); p.y -= 0.5 * g * age * age;
    const f = 1 - age / life, k = nS * 3;
    sparkPos[k] = p.x; sparkPos[k + 1] = Math.max(0.02, p.y); sparkPos[k + 2] = p.z;
    sparkCol[k] = col[0] * f; sparkCol[k + 1] = col[1] * f; sparkCol[k + 2] = col[2] * f; nS++;
  }
}
const puffs = []; for (let i = 0; i < 140; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({map: puffTex, transparent: true, depthWrite: false})); s.visible = false; scene.add(s); puffs.push(s); }
let nP = 0;
function puff(o, u, life, s0, s1, col, seed, rise = 0.6, drift = null, op = 0.8) {
  if (nP >= puffs.length || u < 0 || u > life) return;
  const k = u / life, s = puffs[nP++];
  s.visible = true; s.position.copy(o); s.position.y += rise * u; if (drift) s.position.addScaledVector(drift, u);
  s.scale.setScalar(lerp(s0, s1, eout(k))); s.material.color.set(col); s.material.opacity = op * (s1 < 4 ? .5 : 1) * (1 - k) * Math.min(1, u * 8);
  s.material.rotation = hash(seed) * 6;
}
const rings = []; for (let i = 0; i < 12; i++) { const m = new THREE.Mesh(new THREE.RingGeometry(.93, 1, 64), new THREE.MeshBasicMaterial({transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, fog: false})); m.visible = false; scene.add(m); rings.push(m); }
let nR = 0;
function ring(o, axis, r, col, op) {
  if (nR >= rings.length || op <= 0) return; const m = rings[nR++]; m.visible = true; m.position.copy(o); m.scale.setScalar(Math.max(r, .001));
  m.rotation.set(0, 0, 0); if (axis === 'y') m.rotation.x = -Math.PI / 2; else if (axis === 'x') m.rotation.y = Math.PI / 2;
  m.material.color.set(col); m.material.opacity = op;
}
const glows = []; for (let i = 0; i < 8; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({map: dotTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false})); s.visible = false; scene.add(s); glows.push(s); }
let nG = 0;
function glow(o, size, col, op) { if (nG >= glows.length || op <= 0) return; const s = glows[nG++]; s.visible = true; s.position.copy(o); s.scale.setScalar(size * .6); s.material.color.set(col); s.material.opacity = op * .6; }
const arrows = []; for (let i = 0; i < 8; i++) {
  const g = new THREE.Group(); const mt = new THREE.MeshStandardMaterial({color: 0xe21b1b, emissive: 0x7a0000, roughness: .5});
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(.08, .08, 1, 12), mt); sh.position.y = .5; const hd = new THREE.Mesh(new THREE.ConeGeometry(.2, .45, 14), mt); hd.position.y = 1.25; sh.userData.s = 1;
  g.add(sh, hd); g.visible = false; scene.add(g); arrows.push({g, sh, hd});
}
let nA = 0;
function arrow(o, dir, len, k = 1) { // origin, direction, length, grow 0..1
  if (nA >= arrows.length || k <= 0) return; const a = arrows[nA++]; const L = len * k; a.g.visible = true; a.g.position.copy(o);
  a.g.quaternion.setFromUnitVectors(V(0, 1, 0), dir.clone().normalize()); a.sh.scale.set(1, Math.max(L - .5, .01), 1); a.sh.position.y = Math.max(L - .5, .01) / 2; a.hd.position.y = Math.max(L - .5, 0) + .25;
}
const spiralGeo = new THREE.BufferGeometry(); const SP = 600;
const spPos = new Float32Array(SP * 3), spCol = new Float32Array(SP * 3);
spiralGeo.setAttribute('position', new THREE.BufferAttribute(spPos, 3)); spiralGeo.setAttribute('color', new THREE.BufferAttribute(spCol, 3));
const spiralPts = new THREE.Points(spiralGeo, new THREE.PointsMaterial({size: .22, map: dotTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, vertexColors: true, fog: false}));
spiralPts.frustumCulled = false; spiralPts.visible = false; scene.add(spiralPts);

// explosion objects
const fireG = new THREE.Group(); scene.add(fireG); fireG.visible = false;
const fireMats = [0xb83a14, 0xe0601a, 0xff9a2a, 0xffd24a].map(c => new THREE.MeshBasicMaterial({color: c, transparent: true, opacity: .95, fog: false}));
const fireBalls = []; for (let i = 0; i < 4; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 18), fireMats[i]); fireG.add(m); fireBalls.push(m); }
const stemMat = new THREE.MeshBasicMaterial({color: 0x9b6b45, transparent: true, opacity: .95, fog: false});
const stem = new THREE.Mesh(new THREE.CylinderGeometry(1, 1.6, 1, 20, 1, true), stemMat); fireG.add(stem);
const capBalls = []; for (let i = 0; i < 9; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), new THREE.MeshBasicMaterial({color: i % 3 ? 0xc99a68 : 0xf0b060, transparent: true, opacity: .96, fog: false})); fireG.add(m); capBalls.push(m); }
const shockDome = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 24, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshBasicMaterial({color: 0xfff2d0, transparent: true, opacity: .25, side: THREE.DoubleSide, depthWrite: false, fog: false, blending: THREE.AdditiveBlending}));
shockDome.visible = false; scene.add(shockDome);
// vortex / orb
const vortexG = new THREE.Group(); scene.add(vortexG); vortexG.visible = false;
const vRings = []; for (let i = 0; i < 6; i++) { const m = new THREE.Mesh(new THREE.TorusGeometry(1, .035, 8, 80), new THREE.MeshBasicMaterial({color: i % 2 ? 0xb06bff : 0x7fb2ff, transparent: true, opacity: .9, blending: THREE.AdditiveBlending, depthWrite: false, fog: false})); vortexG.add(m); vRings.push(m); }
const orb = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 28), new THREE.MeshBasicMaterial({color: 0x20e070, fog: false})); orb.visible = false; scene.add(orb);
const orbCore = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), new THREE.MeshBasicMaterial({color: 0xc8ffe0, fog: false})); orbCore.visible = false; scene.add(orbCore);
const rays = []; for (let i = 0; i < 28; i++) { const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({color: 0x30ff90, transparent: true, opacity: .55, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false})); m.visible = false; scene.add(m); rays.push(m); }
// skid marks
const skids = [-.85, .85].map(z => { const m = new THREE.Mesh(new THREE.PlaneGeometry(1, .26), new THREE.MeshBasicMaterial({color: 0x0a0a0c, transparent: true, opacity: .65, depthWrite: false})); m.rotation.x = -Math.PI / 2; m.visible = false; scene.add(m); return m; });
// foreground leaves for depth
const leafPts = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({size: .09, map: dotTex, color: 0xffffff, transparent: true, depthWrite: false, opacity: .7, fog: false}));
{ const n = 90, p = new Float32Array(n * 3); for (let i = 0; i < n; i++) { p[i * 3] = (hash(i) - .5) * 14; p[i * 3 + 1] = hash(i + 7) * 6; p[i * 3 + 2] = (hash(i + 13) - .5) * 14; } leafPts.geometry.setAttribute('position', new THREE.BufferAttribute(p, 3)); leafPts.frustumCulled = false; scene.add(leafPts); }

// ---------- motion tables (car x) ----------
const DT = 1 / 120, NT = Math.ceil(42 / DT);
function table(vfun, anchorT, anchorX) {
  const a = new Float32Array(NT + 1); for (let i = 1; i <= NT; i++) a[i] = a[i - 1] + vfun((i - .5) * DT) * DT;
  const off = anchorX - a[Math.round(anchorT / DT)]; return t => { const f = clamp(t / DT, 0, NT - 1), i = Math.floor(f); return a[i] + (a[i + 1] - a[i]) * (f - i) + off; };
}
const XHIT = -1.12; // car x where sword touches trunk
const v1 = t => t < 4.6 ? 11 : t < 5.3 ? lerp(11, 3.2, sm(rng(t, 4.6, 5.3))) : t < 6.4 ? 3.2 : lerp(3.2, 11, sm(rng(t, 6.4, 7.2)));
const X1 = table(v1, T.contact1, XHIT);
const v2 = t => {
  if (t < 12.4) return 9; if (t < 13.4) return lerp(9, 2.6, sm(rng(t, 12.4, 13.4))); if (t < T.impact2) return 2.6;
  if (t < 18.3) return 2.6 * (1 - eout(rng(t, T.impact2, 16.2)));
  if (t < T.lunge) return 0.04; return 1.75 * sm(rng(t, T.lunge, T.lunge + .6));
};
const X2 = table(v2, T.impact2, XHIT);
let tcut = 22.4; for (let t = 21; t < 24; t += .01) if (X2(t) + 0.6 >= 0.5) { tcut = t; break; }
window.__tcut = tcut;

// ---------- ballistics for flying pieces ----------
function ballistic(p0, v0, t, bounce = .38, floor = .05) {
  const p = p0.clone(), v = v0.clone(); const dt = 1 / 240; let n = Math.floor(t / dt);
  for (let i = 0; i < n; i++) { v.y -= 9.8 * dt; p.addScaledVector(v, dt); if (p.y < floor) { p.y = floor; v.y = -v.y * bounce; v.x *= .8; v.z *= .8; if (Math.abs(v.y) < .3) v.y = 0; } }
  return p;
}

// ---------- camera helpers ----------
let camPos = V(0, 2, 8), camLook = V(0, 1, 0), camFov = 50, shake = 0, roll = 0;
function cam(p, l, fov = 50) { camPos.set(...p); camLook.set(...l); camFov = fov; }
function shakeOff(t, a) { return [Math.sin(t * 47.3) * a + Math.sin(t * 91.1) * a * .5, Math.sin(t * 53.7 + 1) * a + Math.sin(t * 77.7) * a * .5, Math.sin(t * 61.1 + 2) * a * .5]; }
const orbitAround = (c, R, phi, y) => [c[0] + Math.sin(phi) * R, y, c[2] + Math.cos(phi) * R];

// ---------- scene state ----------
let Xc = 0, carPitch = 0, handPos = V(0, 1.1, -2.95);
function placeCar(x, extraSpin = 0, bob = 0) {
  car.position.set(x, bob, CZ); car.rotation.set(0, 0, carPitch);
  wheels.forEach(w => { w.rotation.z = -(x / 0.38) - extraSpin; });
  Xc = x; handPos.set(x + 0.62, 1.1 + bob, CZ - 1.2);
}
function resetFX() {
  nS = nP = nR = nG = nA = 0; puffs.forEach(p => p.visible = false); rings.forEach(r => r.visible = false); glows.forEach(g => g.visible = false); arrows.forEach(a => a.g.visible = false);
  fireG.visible = false; shockDome.visible = false; vortexG.visible = false; orb.visible = false; orbCore.visible = false; rays.forEach(r => r.visible = false); spiralPts.visible = false;
  skids.forEach(s => s.visible = false); kerf.visible = false; cutCap.visible = false; observer.g.visible = false;
  swordG.visible = true; swordA.visible = swordB.visible = true;
  upperPivot.position.set(0.52, CUT_Y, 0); upperPivot.rotation.set(0, 0, 0); upper.position.set(-0.52, 0, 0);
  treeG.visible = true; trunkMat.emissive.set(0x000000); leafMats.forEach(m => m.emissive.set(0x000000));
  setSwordGlow(0x000000, 0); driver.glow(0, 0); rimMat.emissive.set(0x000000); carPitch = 0; skyMat.uniforms.top.value.set(0x3d86e6); skyMat.uniforms.hor.value.set(0xd3e9ff);
  scene.fog.color.set(0xcfe6ff); scene.fog.near = 70; scene.fog.far = 420; hemi.intensity = .9; sun.intensity = 2.1; bloom.strength = .22; roll = 0; shake = 0;
  farTrees.forEach((t, i) => { t.rotation.set(0, 0, 0); t.position.y = 0; });
  swordG.position.set(0, 0, 0); swordA.position.set(0, 0, 0); swordA.rotation.set(0, 0, 0); swordB.position.set(0, 0, -1.5); swordB.rotation.set(0, 0, 0);
}
function attachSword(h) { swordG.position.copy(h); swordA.position.set(0, 0, 0); swordA.rotation.set(0, 0, 0); swordB.position.set(0, 0, -1.5); swordB.rotation.set(0, 0, 0); }

const GREEN = 0x28ff6a, PURPLE = 0xb05cff;

// ---------- the scenes ----------
function sceneA(t) { // 0..3.8 approach
  const x = X1(t); placeCar(x); attachSword(handPos); driver.pose(driverPose(0, Math.sin(t * 6) * .01, 0));
  const u = t / 3.8, e = sm(u);
  const rel = [x + lerp(-2.5, 1.5, e), lerp(1.0, 1.7, e), CZ + lerp(5.2, 7.4, e)], look = [x + lerp(1.2, .3, e), 1.15, lerp(-2.6, -3.8, e)];
  const w = sm(rng(t, 2.3, 3.8)), wp = [-6.2, 1.9, 4.6], wl = [-0.5, 1.6, -4.8];
  cam(mix3(rel, wp, w), mix3(look, wl, w), lerp(54, 46, e));
  for (let i = 0; i < 7; i++) puff(V(x - 2.4 - i * 1.3, .15, CZ), (t * 1.5 + i * .5) % 2.2, 2.2, .5, 1.6, 0xcbbd9a, i * 5, .2, V(-1.2, 0, 0), .22);
}
function sceneB(t) { // 3.8..7.0 snap + rip
  const x = X1(t); placeCar(x); const u = t - T.contact1;
  attachSword(handPos); driver.pose(driverPose(0, 0, 0));
  const imp = V(0, CUT_Y, -4.45), ss = .45;
  // camera push-in then follow
  const e = sm(rng(t, 3.8, 5.6));
  let cp = mix3([-6.2, 1.9, 4.6], [-4.2, 2.7, 2.6], e), cl = [-0.6, 1.25, -4.3];
  if (t > 5.2) { const f = sm(rng(t, 5.2, 6.8)); cl = mix3(cl, [handPos.x - 2, 2.3, -1.5], f * .55); }
  cam(cp, cl, lerp(46, 40, e));
  if (u > 0) {
    const sU = (u) * ss;
    // sword snaps at T.snap: piece B bounces off tree, piece A rips away
    swordA.visible = true; swordB.visible = true;
    const us = Math.max(0, t - T.snap) * ss;
    const pB = ballistic(V(handPos.x, 1.1, -4.45), V(3.2, 3.2, -1.4), us, .35); swordB.position.set(pB.x - swordG.position.x, pB.y - swordG.position.y, pB.z - swordG.position.z);
    if (t >= T.snap) { swordB.rotation.set(us * 5.5, us * 3.1, us * 2.2); }
    const ur = Math.max(0, t - T.rip) * ss;
    if (t >= T.rip) {
      const pA = ballistic(handPos.clone().add(V(0, 0, 0)), V(-5.5, 5.5, 6.5), ur, .42);
      const base = X1(T.rip) + 0.62; const p0 = V(base + 0, 1.1, -2.95); const pp = ballistic(p0, V(-5.5 + 8, 5.5, 6.5), ur, .42);
      swordA.position.set(pp.x - swordG.position.x, pp.y - swordG.position.y, pp.z - swordG.position.z); swordA.rotation.set(ur * 5, ur * 7, ur * 3);
      const k = t - T.rip; const sp = Math.exp(-k * 5) * Math.cos(k * 28);
      driver.pose(driverPose(-.5 * sp - .25 * Math.min(1, k * 8) * Math.exp(-k * 1.2), .25 * sp, .18 * Math.sin(k * 25) * Math.exp(-k * 4)));
    }
    spark(imp, t - T.contact1, 70, 7, .9, 11, V(1, .3, 0), .6, [1, .75, .3]);
    spark(imp, t - T.snap, 60, 9, 1.1, 41, V(0, .2, 1), .8, [1, .85, .5]);
    const pk = rng(t, T.contact1, T.contact1 + .12) * (1 - rng(t, T.contact1 + .2, T.contact1 + .7));
    glow(imp, 1.7 * pk, 0xffd9a0, .9 * pk);
    for (let i = 0; i < 6; i++) puff(V(0, .3, -4.3), t - T.contact1 - i * .05, 1.8, .3, 2.2, 0xa38a5c, i + 3, .5, V(-.5, .2, .6), .45);
    if (t > T.rip && t < T.rip + 1) shake = .05 * (1 - (t - T.rip));
  } else {
    for (let i = 0; i < 0; i++);
  }
}
function carRunSetup(t, x) { placeCar(x); attachSword(handPos); }
function sceneC(t) { // 7.0..9.1 sword turns green
  const x = X2(t); placeCar(x); attachSword(handPos); driver.pose(driverPose());
  const u = rng(t, 7.0, 9.1), mid = [handPos.x, 1.1, -4.4];
  const g = sm(rng(t, 7.9, 8.4)) * (1 - 0.15 * sm(rng(t, 8.5, 9.1))); setSwordGlow(GREEN, g * 1.4);
  const flash = Math.exp(-Math.max(0, t - T.unb) * 4.5) * (t > T.unb - .25 ? 1 : 0) * sm(rng(t, T.unb - .25, T.unb));
  glow(V(handPos.x, 1.1, -4.0), 3.6 * flash + 1.4 * g, GREEN, .8 * (g * .5 + flash));
  cam(orbitAround([mid[0], 1.1, -4.0], lerp(8.4, 9.4, u), lerp(-.55, .5, sm(u)), lerp(1.7, 2.7, sm(u))), [mid[0], 1.1, -4.0], 42);
  const sparks = g > .3 ? 1 : 0; if (sparks) spark(V(handPos.x, 1.1, -5.0), (t - 8.2) % .7, 14, 2.4, .7, 7 + Math.floor((t - 8.2) / .7) * 3, null, 1, [.3, 1, .5], 4);
}
function sceneD(t) { // 9.1..12.5 grip + body
  const x = X2(t); placeCar(x); attachSword(handPos); driver.pose(driverPose(0, 0, 0)); setSwordGlow(GREEN, 1.0);
  const gripk = sm(rng(t, T.grip - .3, T.grip + .3)) * (1 - .35 * sm(rng(t, T.body - .2, T.body + .5)));
  const bodyk = sm(rng(t, T.body - .1, T.body + .5)); driver.glow(GREEN, Math.max(bodyk * .9, 0));
  if (gripk > 0 && bodyk < .5) glow(handPos.clone().add(V(0, 0, .0)), 1.0 + .3 * Math.sin(t * 10), GREEN, .9 * gripk);
  if (t > T.body) { ring(V(x + .35, 1.2, CZ - .45), 'z', 1.1 + .4 * ((t - T.body) % .6), GREEN, .8 * (1 - ((t - T.body) % .6) / .6)); }
  const e = sm(rng(t, 9.1, 10.9)), f = sm(rng(t, 10.9, 12.5));
  const ph = V(handPos.x, 1.1, handPos.z);
  const p1 = [ph.x - .9 + e * .4, 1.5, CZ + 2.5 - e * .25], l1 = [ph.x - .1, 1.15, ph.z + .35];
  const p2 = [x + lerp(.8, 3.4, f), lerp(1.55, 2.0, f), CZ + lerp(3.3, 5.8, f)], l2 = [x + .3, 1.2, CZ - .5];
  const sw = sm(rng(t, 10.6, 11.4)); cam(mix3(p1, p2, sw), mix3(l1, l2, sw), lerp(38, 50, sw));
}
function sceneE(t) { // 12.5..15.4 force transfer (slow-mo approach)
  const x = X2(t); placeCar(x); attachSword(handPos); driver.pose(driverPose()); setSwordGlow(GREEN, 1.0); driver.glow(GREEN, .55);
  const e = sm(rng(t, 12.5, 15.2)), f = sm(rng(t, 14.6, 15.4));
  cam(mix3(mix3([-6, 1.6, .6], [-2.6, 1.25, -2.1], e), [-.9, 1.2, -3.6], f * .5), mix3([x + 1.2, 1.1, -4.0], [-0.1, 1.1, -4.7], e), lerp(48, 40, e));
  // force line pulses: ripples travel from the trunk back along the sword to the hand
  if (t > T.ripple0) for (let i = 0; i < 5; i++) {
    const ph = ((t - T.ripple0) * .9 + i * .2) % 1; const z = lerp(-5.0, -2.95, ph);
    ring(V(handPos.x, 1.1, z), 'z', .22 + .12 * Math.sin(ph * 6.28), PURPLE, .9 * Math.sin(ph * 3.14));
  }
  const k = sm(rng(t, T.ripple0, T.ripple0 + .8)); rimMat.emissive.set(PURPLE).multiplyScalar(k * (.6 + .4 * Math.sin(t * 12))); bodyMat.emissive?.set(0x000000);
  if (k > 0) glow(V(handPos.x - .6, .9, CZ), 4.2 * k, PURPLE, .35 * k);
  arrow(V(handPos.x - .2, 1.75, -4.1), V(0, 0, 1), 1.6, k * .8);
  if (t > T.impact2 - .15) spark(V(handPos.x, 1.1, -4.5), t - (T.impact2 - .1), 30, 5, .6, 21, null, 1, [.7, 1, .8], 6);
}
function sceneF(t) { // 15.4..18.1 impact + screech to halt
  const x = X2(t); const u = t - T.impact2;
  carPitch = -0.075 * Math.exp(-u * 2.2) * Math.sin(clamp(u, 0, 5) * 5) * 1 * (u > 0 ? 1 : 0);
  const bob = 0; placeCar(x, 0, bob); attachSword(handPos); driver.pose(driverPose(0, 0, 0)); setSwordGlow(GREEN, .9); driver.glow(GREEN, .4);
  const rim = sm(rng(t, T.impact2, T.impact2 + .15)) * (1 - sm(rng(t, 17.0, 18.0))); rimMat.emissive.set(PURPLE).multiplyScalar(rim * 1.3);
  for (const w of [[1.4, .85], [-1.4, .85]]) glow(V(x + w[0], .4, CZ + w[1] + .1), 1.5 * rim, PURPLE, .8 * rim);
  const imp = V(handPos.x, 1.1, -4.45);
  ring(imp, 'z', .2 + u * 3.5, PURPLE, .9 * Math.max(0, 1 - u * 1.6) * (u > 0 ? 1 : 0));
  spark(imp, u, 40, 6, .7, 61, null, 1, [.8, 1, 1], 5);
  // skid marks + smoke while braking
  const brake = u > 0 && u < 1.4; const run = X2(Math.min(t, 16.8)) - X2(T.impact2);
  skids.forEach((s, i) => { if (u > 0) { s.visible = true; const len = Math.max(.01, run); s.scale.x = len; s.position.set(X2(T.impact2) - 0.4 + len / 2 - 1.4 + 1.4, .016, CZ + (i ? .85 : -.85)); } });
  if (u > 0 && u < 1.5) for (let i = 0; i < 12; i++) puff(V(x + 1.4 - hash(i) * 1.2, .2, CZ + .9), u - i * .07, 1.8, .4, 1.6, 0xe6e6e6, i + 11, .5, V(-1, 0, .6), .75);
  if (u > 0 && u < 1.5) for (let i = 0; i < 10; i++) puff(V(x - 1.4 - hash(i) * 1.2, .2, CZ + .9), u - i * .07, 1.8, .4, 1.6, 0xe6e6e6, i + 21, .5, V(-1, 0, .6), .75);
  // camera: low wheel angle, then crane up
  const lo = [x + 3.2, .55, CZ + 2.4], loL = [x + 1.4, .5, CZ + .9];
  const a = sm(rng(t, 15.4, 15.9)), b = sm(rng(t, 16.6, 18.0));
  const prev = mix3([-2.2, 1.25, -2.1], lo, a); const wide = [x - 3.2, 2.4, 7.4], wideL = [x + 1.0, 1.1, -1.8];
  const base = mix3(prev, wide, b); const bl = mix3(mix3([-0.1, 1.1, -4.7], loL, a), wideL, b);
  cam(base, bl, lerp(40, 48, b)); if (u > 0 && u < .8) shake = .06 * (1 - u / .8);
}
function sceneG(t) { // 18.1..21.9 car forced to keep moving
  const x = X2(t); const u = t - T.push; const pressing = t < T.lunge;
  placeCar(x, pressing ? (t - T.push) * 22 : 0, Math.sin(t * 40) * .008 * (pressing ? 1 : 0)); attachSword(handPos); driver.pose(driverPose(0, 0, 0)); setSwordGlow(GREEN, .9); driver.glow(GREEN, .4);
  const ak = sm(rng(t, T.push, T.push + .5)); arrow(V(x - 3.2 + ak * .6, .85, CZ + 0.95), V(1, 0, 0), 2.2, ak * (t > T.lunge + .5 ? 0 : 1));
  arrow(V(x - 3.2 + ak * .6, .85, CZ - 0.95), V(1, 0, 0), 2.2, ak * (t > T.lunge + .5 ? 0 : 1));
  if (t > T.push) for (let i = 0; i < 9; i++) { puff(V(x - 1.4, .2, CZ + .9 + (i % 2 ? -1.8 : 0)), ((t - T.push) * 1.2 + i * .13) % 1.7, 1.7, .4, 1.5, 0xdadada, i + 31, .6, V(-2, 0, 0), .7); }
  rimMat.emissive.set(PURPLE).multiplyScalar(.5);
  const e = sm(rng(t, 18.1, 21.4)), f = sm(rng(t, 21.4, 21.9));
  cam(mix3(mix3([x - 4.5, .55, CZ + 1.7], [-3.8, 1.5, -.9], e), [x - 2.5, 2.1, -1.5], f * .6), mix3([x - 1.4, .45, CZ + .9], [x + .6, 1.15, -4.6], sm(rng(t, 18.9, 21.0))), 48);
  if (t > T.lunge) { const k = t - T.lunge; shake = .03 * Math.min(1, k * 2); if (t > T.lunge + .2) spark(V(handPos.x, 1.1, -4.5), (t - T.lunge - .2), 40, 6, .8, 71, V(0, .5, 1), .7, [1, .8, .3]); }
}
function sceneH(t) { // 21.9..24.0 tree cut in half
  const x = X2(t); placeCar(x); attachSword(handPos); driver.pose(driverPose(0, 0, 0)); setSwordGlow(GREEN, .9); driver.glow(GREEN, .35);
  const cutLen = clamp(handPos.x + .55, 0, 1.2); kerf.visible = t < tcut + 1.5;
  kerf.scale.set(Math.max(cutLen, .001), 1, 1); kerf.position.set(-.55 + cutLen / 2, CUT_Y, TZ);
  spark(V(handPos.x, 1.1, -5.0), (t * 7) % .5, 26, 3.5, .5, Math.floor(t * 14), null, 1, [1, .7, .3], 6);
  const f = t - tcut; // fall
  if (f >= 0) {
    cutCap.visible = true; kerf.visible = false;
    const slide = .28 * eout(f * 1.8); const ang = (-1) * (Math.PI / 2 - .12) * (Math.pow(clamp(f / 1.05), 2));
    const bounceK = f > 1.05 ? .07 * Math.exp(-(f - 1.05) * 5) * Math.cos((f - 1.05) * 22) : 0;
    upperPivot.rotation.z = ang + bounceK; upperPivot.position.x = .52 + slide; upperPivot.position.y = CUT_Y + (f > 1.05 ? Math.max(0, bounceK * 2.2) : 0);
    if (f > 1.0) { const ff = f - 1.0; for (let i = 0; i < 14; i++) puff(V(2.6 + hash(i) * 1.4, .2, TZ + (hash(i + 5) - .5) * 2.4), ff - i * .03, 2.2, .8, 3.2, 0xbfa77a, i + 41, .5, V(.6, 0, 0), .7); spark(V(3.2, .3, TZ), ff, 24, 4.5, .9, 91, V(0, 1, 0), .6, [.8, .9, .4], 7); if (ff < .5) shake = .12 * (1 - ff / .5); }
  }
  const e = sm(rng(t, 21.9, 23.5));
  const baseP = mix3([-3.2, 1.45, -2.0], [2.4, 2.0, 1.4], e), look = mix3([-.2, 1.1, -4.9], [1.2, 1.4, -5.0], sm(rng(t, 22.0, 23.2)));
  cam(baseP, look, lerp(42, 50, e));
}
function sceneI(t) { // 24..26.3 indestructible tree
  placeCar(XHIT, (t - 24) * 24, Math.sin(t * 42) * .01); attachSword(handPos); driver.pose(driverPose()); setSwordGlow(0xff3030, 1.1); driver.glow(GREEN, .35);
  const band = sm(rng(t, T.greenBand - .25, T.greenBand + .6)); const gk = band;
  trunkMat.emissive.set(GREEN).multiplyScalar(.45 * gk); leafMats.forEach(m => m.emissive.set(GREEN).multiplyScalar(.12 * gk));
  glow(V(0, 1.3 + band * 3.3, TZ + .65), 2.2 * Math.sin(band * 3.14) + .01, GREEN, .8 * Math.sin(band * 3.14));
  const pk = sm(rng(t, 24, 25.5)); arrow(V(XHIT - 3.0, .85, CZ + .95), V(1, 0, 0), 2.0, pk); arrow(V(XHIT - 3.0, .85, CZ - .95), V(1, 0, 0), 2.0, pk);
  for (let i = 0; i < 12; i++) puff(V(XHIT - 1.4, .2, CZ + .9 + (i % 2 ? -1.8 : 0)), ((t - 24) * 1.2 + i * .14) % 1.7, 1.7, .4, 1.5, 0xdadada, i + 51, .6, V(-2, 0, 0), .7);
  const u = rng(t, 24, 26.3);
  cam(orbitAround([0, 1.8, TZ], lerp(8.5, 6.2, sm(u)), lerp(-.95, .75, sm(u)), lerp(1.1, 3.0, sm(u))), [0, lerp(1.2, 2.6, sm(u)), TZ], 46);
  ring(V(0, 1.1, TZ + .6), 'z', .6 + .3 * Math.sin(t * 8), 0xff4040, .5 * pk);
}
function sceneJ(t) { // 26.3..31.4 energy building
  const u = rng(t, T.build0, T.boom), build = Math.pow(u, 1.5);
  placeCar(XHIT, (t - 24) * 26, Math.sin(t * (40 + u * 80)) * (.01 + .03 * u)); attachSword(handPos); driver.pose(driverPose(0, Math.sin(t * 55) * .015 * u, 0)); setSwordGlow(0xff7040, .6 + 1.2 * build); driver.glow(GREEN, .35);
  trunkMat.emissive.set(GREEN).multiplyScalar(.45); leafMats.forEach(m => m.emissive.set(GREEN).multiplyScalar(.12));
  const c = V(0, 1.1, TZ + .55);
  for (let i = 0; i < 5; i++) { const ph = ((t * (1.2 + u * 2.6)) + i * .2) % 1; ring(c, 'z', lerp(2.4, .1, ph) * (1 - .2 * u), PURPLE, .8 * Math.sin(ph * 3.14)); }
  glow(c, .8 + 3.2 * build, 0xffe6c0, .35 + .5 * build);
  for (let i = 0; i < 6; i++) { const a = i / 6 * 6.28 + t * .4, d = lerp(3.2, 1.5, build) + .15 * Math.sin(t * 9 + i); arrow(V(Math.cos(a) * d, 1.1 + Math.sin(a) * d * .8, TZ + .55), V(-Math.cos(a), -Math.sin(a) * .8, 0), 1.1, sm(rng(t, 26.8 + i * .1, 27.6 + i * .1))); }
  spark(V(0, 1.1, TZ + .55), (t * 3) % .5, 36, 4 + 5 * u, .5, Math.floor(t * 6) * 13, null, 1, [1, .8, .4], 0);
  for (let i = 0; i < 12; i++) puff(V(XHIT - 1.4, .2, CZ + .9 + (i % 2 ? -1.8 : 0)), ((t - 24) * 1.4 + i * .13) % 1.5, 1.5, .4, 1.6, 0xdadada, i + 61, .6, V(-2, 0, 0), .7);
  shake = .01 + .08 * u * u;
  const e = sm(u);
  const p = orbitAround([0, 1.1, TZ], lerp(8.5, 5.2, e), lerp(-.9, .85, sm(u)), lerp(1.6, 1.15, e)); cam(p, [0, 1.15, TZ + .3], lerp(46, 36, e));
  observer.g.visible = true; observer.g.position.set(7.5, 0, -7.5); observer.g.rotation.y = -.8; observer.pose(standPose(sm(rng(t, 28.6, 29.8)), 0, t * 2));
}
function sceneK(t) { // 31.4..34.1 explosion
  const u = t - T.boom; placeCar(XHIT, (t - 24) * 26, 0); attachSword(handPos); driver.pose(driverPose());
  const c = V(0, 1.1, TZ + .3);
  const fb = eout(u / 1.6);
  const flash = Math.exp(-u * 5.5) * (u > 0 ? 1 : 0);
  // fireball, expanding and rising into a mushroom cloud (colors kept below clipping)
  fireG.visible = u > 0;
  const R = lerp(.1, 9, eout(u / 2.2)); fireG.position.set(0, 0, TZ);
  fireBalls.forEach((b, i) => { b.scale.setScalar(R * (1 - i * .16) * (u > 0 ? 1 : 0)); b.position.y = R * .45 + rng(u, 0, 3) * 6 * (1 - i * .2); b.material.opacity = (1 - rng(u, 1.2, 2.6)) * .95; });
  const rise = rng(u, .4, 2.8) * 22; stem.position.y = rise * .5; stem.scale.set(3.2 * eout(u / 1.2), Math.max(rise, .01), 3.2 * eout(u / 1.2)); stem.material.opacity = Math.min(1, rng(u, .3, .9)) * .95;
  capBalls.forEach((b, i) => { const a = i / 9 * 6.28; const cr = 5.8 * eout(rng(u, .5, 2.8)); b.position.set(Math.cos(a) * cr, rise + 2 + Math.sin(i * 2.1) * 1.2, Math.sin(a) * cr); b.scale.setScalar(Math.max(.01, 3.4 * eout(rng(u, .6, 2.6)))); });
  shockDome.visible = u > 0 && u < 2.4; shockDome.position.set(0, 0, TZ); shockDome.scale.setScalar(Math.max(.01, eout(u / 2.4) * 120)); shockDome.material.opacity = .22 * (1 - rng(u, .3, 2.4));
  ring(V(0, .15, TZ), 'y', Math.max(.01, eout(u / 2.6) * 110), 0xffe2b0, .9 * (1 - rng(u, .2, 2.6)));
  if (u > 0) for (let i = 0; i < 40; i++) { const a = i / 40 * 6.28 + hash(i) * .3, rr = eout(u / 2.8) * (30 + hash(i + 5) * 40); puff(V(Math.cos(a) * rr, .6, TZ + Math.sin(a) * rr), u * .8, 3.2, 4, 12, 0xb58a55, i + 81, 1.4, null, .5 * (1 - rng(u, 1.8, 3.2))); }
  if (u > 0) spark(V(0, 1, TZ), u, 120, 22, 1.8, 133, null, 1, [1, .8, .4], 4);
  const fall = (tr, dist) => clamp((u - dist / 70) * 1.8, 0, 1);
  farTrees.forEach((tr, i) => { const d = Math.hypot(tr.position.x, tr.position.z - TZ), f = clamp((u - d / 60) * 1.4, 0, 1); const dir = Math.atan2(tr.position.z - TZ, tr.position.x - TX); tr.rotation.set(0, 0, 0); tr.rotation.z = -Math.cos(dir) * f * 1.35; tr.rotation.x = Math.sin(dir) * f * 1.35; tr.position.y = f * .2; });
  observer.g.visible = true; const ob = ballistic(V(7.5, 0, -7.5), V(14, 10, -6), clamp(u - .25, 0, 4), .3); const of = u > .25;
  observer.g.position.set(of ? ob.x : 7.5, of ? ob.y : 0, of ? ob.z : -7.5); observer.g.rotation.set(of ? u * 3 : 0, -.8, of ? u * 5 : 0); observer.pose(standPose(1, 0, t));
  if (u > 0 && u < 2) { treeG.visible = u < .06; }
  upperPivot.rotation.z = 0; // tree burned away after boom
  // camera: at flash we are close, then pull way out and up to reveal the mushroom cloud
  const e = sm(rng(t, T.boom - .05, 33.6));
  const pre = orbitAround([0, 1.1, TZ], 22, .55, 4.5);
  cam(mix3(pre, [4, 13, 52], e), mix3([0, 1.5, TZ + .3], [0, 10, TZ], e), lerp(42, 56, e));
  shake = .12 * Math.exp(-u * 1.6) * (u > 0 ? 1 : 0); bloom.strength = .22 + .2 * flash;
  sun.intensity = 2.1 * (1 - .3 * rng(u, 0, 2)); skyMat.uniforms.hor.value.lerp(new THREE.Color(0xe7caa0), rng(u, .5, 2.5) * .8); scene.fog.color.set(0xd9bf94).lerp(new THREE.Color(0xcfe6ff), 1 - rng(u, .3, 2));
  if (flash > .02) glow(c, 5 * flash + 1, 0xfff0c8, .75 * flash);
  scene.fog.near = 40; scene.fog.far = 280;
}
function sceneL(t) { // 34.1..39.5 reality breaks
  const u = t - T.vortex; placeCar(XHIT, 0); treeG.visible = false; swordG.visible = false; car.visible = false;
  skyMat.uniforms.top.value.set(0x120a2e); skyMat.uniforms.hor.value.set(0x3a1d6b); scene.fog.color.set(0x2a1650); scene.fog.near = 30; scene.fog.far = 200; hemi.intensity = .5; sun.intensity = .7;
  farTrees.forEach(t0 => t0.rotation.set(0, 0, 0));
  const c = V(0, 3, TZ + 4); vortexG.visible = true; vortexG.position.copy(c);
  const grow = eout(rng(t, T.vortex, T.vortex + 1.6));
  vRings.forEach((r, i) => { r.scale.setScalar((.8 + i * .9) * grow); r.rotation.z = t * (i % 2 ? 1.4 : -1.1) * .6; r.rotation.x = Math.sin(t * .8 + i) * .5; r.rotation.y = Math.cos(t * .7 + i) * .5; });
  spiralPts.visible = true; spiralPts.position.copy(c);
  for (let i = 0; i < SP; i++) { const arm = i % 4, k = Math.floor(i / 4) / (SP / 4), ang = arm * 1.57 + k * 9 - t * 1.8, r = (.3 + k * 6) * grow; spPos[i * 3] = Math.cos(ang) * r; spPos[i * 3 + 1] = Math.sin(ang) * r; spPos[i * 3 + 2] = (hash(i) - .5) * .4; const a = (1 - k) * .9; spCol[i * 3] = .6 * a; spCol[i * 3 + 1] = .4 * a; spCol[i * 3 + 2] = 1 * a; }
  spiralGeo.attributes.position.needsUpdate = true; spiralGeo.attributes.color.needsUpdate = true;
  const ob = rng(t, T.orb, T.orb + 1.2), dv = sm(rng(t, T.dive0, 37.7));
  orb.visible = ob > 0; orb.position.copy(c); orb.scale.setScalar(Math.max(.01, .9 * eout(ob) + dv * 14)); orbCore.visible = ob > 0; orbCore.position.copy(c); orbCore.scale.setScalar(Math.max(.01, .22 * eout(ob) + dv * 6));
  glow(c, 4 * eout(ob) + 8 * dv, 0x34ff9a, .5 * eout(ob));
  rays.forEach((r, i) => { r.visible = ob > 0; const a = i / 28 * 6.28 + t * .3, L = (2.5 + hash(i) * 3) * eout(ob) * (1 + dv * 6); r.position.set(c.x + Math.cos(a) * L / 2 * 1, c.y + Math.sin(a) * L / 2, c.z); r.rotation.z = a; r.scale.set(L, .05 + .05 * hash(i + 3), 1); });
  const e = sm(rng(t, T.vortex, T.orb + .6)), d = sm(rng(t, T.dive0, 37.8));
  cam(mix3(mix3([-5, 4.5, TZ + 16], [-1.5, 3.2, TZ + 9], e), [0, 3, TZ + 4.6], d), [c.x, c.y, c.z], lerp(52, 34, e) + d * 24);
  shake = .015 + .03 * d; bloom.strength = .45 + .2 * d;
  observer.g.visible = false;
}

// ---------- scene dispatcher ----------
function render(t) {
  resetFX(); car.visible = true; shake = 0;
  if (t < 3.8) sceneA(t); else if (t < 7.0) sceneB(t); else if (t < 9.1) sceneC(t); else if (t < 12.5) sceneD(t);
  else if (t < 15.4) sceneE(t); else if (t < 18.1) sceneF(t); else if (t < 21.9) sceneG(t); else if (t < 24.0) sceneH(t);
  else if (t < 26.3) sceneI(t); else if (t < T.boom) sceneJ(t); else if (t < T.vortex) sceneK(t); else sceneL(t);
  // aftermath: tree gone in L, car pieces remain irrelevant
  const so = shakeOff(t, shake); camera.position.set(camPos.x + so[0], camPos.y + so[1], camPos.z + so[2]); camera.lookAt(camLook.x, camLook.y, camLook.z);
  camera.fov = camFov; camera.updateProjectionMatrix();
  sky.position.copy(camera.position);
  sun.position.set(camLook.x - 10, 22, camLook.z + 16); sun.target.position.set(camLook.x, 0, camLook.z); sun.target.updateMatrixWorld();
  leafPts.position.set(camera.position.x, 0, camera.position.z); leafPts.position.y = 0; leafPts.rotation.y = t * .05;
  sparkGeo.setDrawRange(0, nS); sparkGeo.attributes.position.needsUpdate = true; sparkGeo.attributes.color.needsUpdate = true;
  document.getElementById('fade').style.opacity = String(clamp(rng(t, T.fadeOut, TM.dur - .05)) + clamp(1 - rng(t, 0, .25)));
  caption(t);
  composer.render();
}

// ---------- captions (word-chunk timed to narration) ----------
const KEY = {unbreakable: '#35ff7a', indestructible: '#35ff7a', immovable: '#35ff7a', force: '#c284ff', screech: '#ffb347', nuclear: '#ff9a3c', shockwave: '#ff9a3c', explosion: '#ff7a2c', reality: '#c284ff', snap: '#ff5a5a', rip: '#ff5a5a', split: '#ffd24a'};
const chunks = [];
for (const [text, a, b] of TM.lines) {
  const ws = text.split(' '); const groups = []; let cur = [];
  for (const w of ws) { cur.push(w); const L = cur.join(' ').length; if (cur.length >= 3 || L > 17 || /[,.?]$/.test(w)) { groups.push(cur); cur = []; } }
  if (cur.length) groups.push(cur);
  const tot = groups.reduce((s, g) => s + g.join(' ').length + 2, 0); let p = a;
  for (const g of groups) { const d = (b - a) * (g.join(' ').length + 2) / tot; chunks.push({s: p, e: p + d, w: g}); p += d; }
}
const capEl = document.getElementById('cap');
function caption(t) {
  const c = chunks.find(c => t >= c.s && t < c.e + .02);
  if (!c) { capEl.innerHTML = ''; return; }
  capEl.innerHTML = c.w.map(w => { const k = w.toLowerCase().replace(/[^a-z]/g, ''); return `<span style="color:${KEY[k] || '#fff'}">${w}</span>`; }).join(' ');
  const pop = clamp((t - c.s) / .08); capEl.style.transform = `scale(${.92 + .08 * pop})`;
}
window.setFrame = render; window.ready = true; window.timing = TM;
render(0);
