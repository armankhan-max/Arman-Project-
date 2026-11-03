// Stylized-but-anatomically-readable organs and micro-world props.
import * as THREE from 'three';
import { toon, glow, addOutline, mesh, G, roundBox, tube, taperTube, V, clamp, smooth, rng, lerp } from './core.js';

export const COL = {
  heart: 0xd9333f, heartDark: 0xa8222f, artery: 0xe2474f, vein: 0x3f6fd8, brain: 0xf3a7b6, lung: 0xf28f9f,
  liver: 0x8f2f33, pancreas: 0xf1c27e, stomach: 0xec8f9c, gut: 0xf2a2a6, colon: 0xd98a86, bone: 0xf1e7d0,
  cartilage: 0xbfe6f2, fat: 0xf6cf55, blood: 0xd81f2c, muscle: 0xd4434e,
};

function deform(geo, fn) {
  const p = geo.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); fn(v); p.setXYZ(i, v.x, v.y, v.z); }
  p.needsUpdate = true; geo.computeVertexNormals(); return geo;
}
const n3 = (x, y, z) => Math.sin(x * 1.7 + Math.sin(y * 2.3 + z)) * Math.sin(y * 1.9 + Math.sin(z * 2.1 + x)) * Math.sin(z * 2.2 + Math.sin(x * 1.6 + y));

// ------------------------------------------------------------------ HEART
export function makeHeart(o = {}) {
  const g = new THREE.Group();
  const body = new THREE.Group(); g.add(body); g.userData.body = body;
  const mHeart = toon(COL.heart, { rim: .45, rimColor: 0xffb0b0 });
  const geo = deform(new THREE.SphereGeometry(1, 64, 48), (v) => {
    // ventricles: taper toward an apex down-left
    let y = v.y;
    if (y < 0) { const k = 1 - .62 * Math.pow(-y, 1.4); v.x *= k; v.z *= k; v.x -= .32 * Math.pow(-y, 1.6); }
    else { v.x *= 1.06; v.z *= .95; }
    v.y *= 1.18; v.z *= .86;
    // interventricular groove (front)
    const gx = v.x + .1 + v.y * .35;
    if (v.z > 0) v.multiplyScalar(1 - .045 * Math.exp(-gx * gx * 60));
    v.x += .015 * n3(v.x * 4, v.y * 4, v.z * 4);
  });
  const main = mesh(geo, mHeart, 0, 0, 0, body); main.rotation.z = .35;
  // atria
  const mAtr = toon(0xc92a39, { rim: .4, rimColor: 0xffb0b0 });
  const ra = mesh(G.sphere(.48, 32, 24), mAtr, .62, .72, .15, body); ra.scale.set(1, .85, .9);
  const la = mesh(G.sphere(.42, 32, 24), mAtr, -.45, .82, -.25, body); la.scale.set(1.1, .8, .9);
  // auricle (ear-like flap) front left
  const aur = mesh(G.sphere(.25, 20, 16), mAtr, -.62, .62, .45, body); aur.scale.set(1.2, .6, .7); aur.rotation.z = .5;
  // aorta arch
  const mArt = toon(COL.artery, { rim: .45, rimColor: 0xffc0c0 });
  mesh(taperTube([[.05, .7, 0], [.08, 1.5, .05], [-.1, 2.05, -.05], [-.55, 2.15, -.3], [-.85, 1.8, -.55], [-.9, .9, -.75]], (t) => .27 - .05 * t, 64, 18), mArt, 0, 0, 0, body);
  // aortic branches
  for (const [x, z, h] of [[-.05, -.08, .55], [-.35, -.22, .5], [-.6, -.38, .45]]) mesh(taperTube([[x, 2.0, z], [x + .05, 2.0 + h * .6, z], [x + .08, 2.0 + h, z + .03]], (t) => .09 - .02 * t, 12, 10), mArt, 0, 0, 0, body);
  // pulmonary trunk (blue = deoxygenated)
  const mVein = toon(COL.vein, { rim: .45, rimColor: 0xbfd4ff });
  mesh(taperTube([[-.15, .6, .55], [-.25, 1.25, .55], [-.5, 1.7, .25], [-1.05, 1.75, .05]], (t) => .24 - .04 * t, 48, 16), mVein, 0, 0, 0, body);
  mesh(taperTube([[-.4, 1.65, .4], [.2, 1.85, .3], [.85, 1.75, .1]], (t) => .17, 32, 14), mVein, 0, 0, 0, body);
  // superior / inferior vena cava
  mesh(taperTube([[.72, .9, .05], [.75, 1.6, -.05], [.72, 2.4, -.1]], () => .2, 24, 16), mVein, 0, 0, 0, body);
  mesh(taperTube([[.68, .4, -.1], [.7, -.2, -.25], [.66, -.8, -.3]], () => .19, 24, 16), mVein, 0, 0, 0, body);
  // coronary vessels on surface
  const mCor = toon(0xf0525a, { rim: .2 });
  const cor = [[-.1, .55, .85], [-.25, .1, .92], [-.4, -.4, .78], [-.6, -.85, .45]];
  mesh(tube(cor, .035, 32, 8), mCor, 0, 0, 0, body).rotation.z = .2;
  mesh(tube([[.35, .45, .82], [.55, 0, .7], [.55, -.45, .5]], .03, 24, 8), toon(0x5b86e8), 0, 0, 0, body);
  // fat line along groove (yellow) for realism
  mesh(tube([[.2, .55, .78], [-.05, .2, .9], [-.3, -.35, .8]], .05, 24, 8), toon(0xf5d27a, { rim: .2 }), 0, 0, 0, body);
  if (o.outline !== false) addOutline(g, o.outlineW ?? .02);
  g.userData.beat = (t, bpm = 60, amp = 1) => {
    const ph = (t * bpm / 60) % 1;
    const lub = Math.exp(-Math.pow((ph - .05) / .05, 2)), dub = Math.exp(-Math.pow((ph - .28) / .05, 2)) * .6;
    const s = 1 + (lub * .09 + dub * .05) * amp;
    body.scale.set(s, 1 + (lub * .06 + dub * .03) * amp, s);
    return lub + dub;
  };
  return g;
}

// ------------------------------------------------------------------ BRAIN
export function makeBrain(o = {}) {
  const g = new THREE.Group();
  const mBrain = toon(o.color ?? COL.brain, { rim: .5, rimColor: 0xffd6e0, soft: true, unique: !!o.unique, emissive: o.emissive ?? 0 });
  const geo = deform(new THREE.SphereGeometry(1, 128, 96), (v) => {
    const n = v.clone().normalize();
    v.set(n.x * .86, n.y * .74, n.z * 1.12);
    if (v.y < -.2) v.y = -.2 + (v.y + .2) * .7;
    // gyri / sulci ridged noise
    const f = n3(n.x * 6.5, n.y * 6.5, n.z * 6.5) + .5 * n3(n.x * 13 + 3, n.y * 13, n.z * 13);
    const r = 1 + .045 * (1 - Math.abs(f)) - .02;
    v.multiplyScalar(r);
    // longitudinal fissure
    if (v.y > -.25) { const d = Math.abs(n.x); if (d < .09) v.multiplyScalar(1 - .16 * Math.pow(1 - d / .09, 2) * smooth((v.y + .25) / .4)); }
    // lateral (sylvian) fissure hint
    const sy = v.y + .05 + v.z * .25; if (Math.abs(n.x) > .55 && v.z > -.3) v.multiplyScalar(1 - .05 * Math.exp(-sy * sy * 120));
  });
  const cortex = mesh(geo, mBrain, 0, 0, 0, g); g.userData.cortex = cortex; g.userData.mat = mBrain;
  // cerebellum
  const mCb = toon(0xe58ea2, { rim: .4, soft: true });
  const cb = deform(new THREE.SphereGeometry(1, 64, 48), (v) => { v.set(v.x * .55, v.y * .3, v.z * .38); v.multiplyScalar(1 + .04 * Math.sin(v.y * 90)); });
  mesh(cb, mCb, 0, -.42, -.72, g);
  // brainstem
  mesh(taperTube([[0, -.3, -.35], [0, -.7, -.45], [0, -1.15, -.5]], (t) => .2 - .06 * t, 20, 16), toon(0xe08aa0, { rim: .3 }), 0, 0, 0, g);
  if (o.outline !== false) addOutline(g, o.outlineW ?? .015);
  return g;
}

// ------------------------------------------------------------------ LUNGS (+ bronchial tree)
export function makeLungs(o = {}) {
  const g = new THREE.Group();
  const mLung = toon(COL.lung, { rim: .5, rimColor: 0xffd0d8, transparent: !!o.transparent, opacity: o.opacity ?? 1, depthWrite: !o.transparent, unique: !!o.transparent, soft: true });
  g.userData.mat = mLung;
  const lobes = [];
  for (const sx of [-1, 1]) {
    const geo = deform(new THREE.SphereGeometry(1, 64, 48), (v) => {
      const y = v.y;
      const top = y > 0 ? 1 - .55 * Math.pow(y, 1.5) : 1;
      v.x *= .62 * top; v.z *= .7 * top; v.y *= 1.25;
      if (v.x * -sx > .12) v.x = -sx * (.12 + (v.x * -sx - .12) * .3); // flatten medial side
      if (y < -.7) v.y = -1.25 * .7 + (y + .7) * .5 * 1.25; // flatter base (diaphragm)
      if (sx < 0 && y < 0 && v.x > -.05 && v.z > 0) v.x -= .12 * smooth(-y * 2); // cardiac notch (left lung)
      v.x += .015 * n3(v.x * 5, v.y * 5, v.z * 5);
    });
    const lobe = new THREE.Group(); lobe.position.set(sx * .78, 0, 0); g.add(lobe);
    const m = mesh(geo, mLung, 0, 0, 0, lobe); m.renderOrder = 3;
    if (o.transparent) m.userData.noOutline = true;
    lobes.push(lobe);
  }
  g.userData.lobes = lobes;
  // trachea with rings
  const mTr = toon(0xf3d6d6, { rim: .3 });
  const tr = new THREE.Group(); g.add(tr);
  mesh(G.cyl(.16, .16, 1.4, 20), mTr, 0, 1.75, 0, tr);
  for (let i = 0; i < 9; i++) mesh(G.torus(.165, .028, 8, 24), toon(0xfbe8e8), 0, 1.15 + i * .14, 0, tr).rotation.x = Math.PI / 2;
  // bronchial tree
  const mBr = toon(o.brColor ?? 0xf6e2e2, { rim: .3 });
  const branches = []; const R = rng(7);
  const grow = (p, dir, len, r, depth, side) => {
    const e = p.clone().add(dir.clone().multiplyScalar(len));
    const geo = taperTube([p, p.clone().lerp(e, .5), e], (t) => r * (1 - .3 * t), 8, 8);
    const m = mesh(geo, mBr, 0, 0, 0, g); m.userData.depth = depth; m.userData.end = e; m.userData.noOutline = depth > 2; branches.push(m);
    if (depth >= (o.depth ?? 5)) return;
    for (const s of [-1, 1]) {
      const nd = dir.clone().applyAxisAngle(V(0, 0, 1), s * (.45 + R() * .25)).applyAxisAngle(V(0, 1, 0), (R() - .5) * 1.2);
      if (nd.y > .3) nd.y = .3;
      nd.normalize();
      grow(e, nd, len * (.72 + R() * .1), r * .68, depth + 1, side);
    }
  };
  for (const sx of [-1, 1]) grow(V(0, 1.05, 0), V(sx * .8, -.6, 0).normalize(), .55, .11, 1, sx);
  g.userData.branches = branches;
  if (o.outline !== false) addOutline(g, o.outlineW ?? .015);
  g.userData.breathe = (amt) => { for (const l of lobes) l.scale.set(1 + .08 * amt, 1 + .1 * amt, 1 + .08 * amt); };
  return g;
}

// ------------------------------------------------------------------ LIVER / PANCREAS / STOMACH / INTESTINES
export function makeLiver(o = {}) {
  const g = new THREE.Group();
  const geo = deform(new THREE.SphereGeometry(1, 64, 40), (v) => {
    const x = v.x;
    v.x *= 1.5; v.z *= .8;
    const k = x < 0 ? lerp(1, .35, smooth(-x)) : 1; v.y *= .7 * k; v.z *= lerp(1, .7, smooth(-x));
    if (v.y < 0) v.y *= .55; // flatter underside
    v.y += .25 * x;          // slope
    v.x += .01 * n3(v.x * 4, v.y * 4, v.z * 4);
  });
  mesh(geo, toon(COL.liver, { rim: .45, rimColor: 0xff9a9a, unique: !!o.unique }), 0, 0, 0, g);
  // falciform ligament line + gallbladder
  mesh(G.sphere(.22, 20, 14), toon(0x6fa84a, { rim: .3 }), .35, -.45, .5, g).scale.set(.7, 1.2, .7);
  if (o.outline !== false) addOutline(g, .02);
  return g;
}
export function makePancreas(o = {}) {
  const g = new THREE.Group();
  const geo = taperTube([[-1.2, 0, 0], [-.6, .1, .1], [0, .05, .15], [.6, .15, .05], [1.1, .35, -.05]], (t) => .26 * (1 - .65 * t) + .02 * Math.sin(t * 50), 80, 20);
  deform(geo, (v) => { v.addScaledVector(v.clone().normalize(), .012 * n3(v.x * 18, v.y * 18, v.z * 18)); });
  mesh(geo, toon(COL.pancreas, { rim: .45, rimColor: 0xfff0c0, unique: !!o.unique }), 0, 0, 0, g);
  if (o.outline !== false) addOutline(g, .02);
  return g;
}
export function makeStomach(o = {}) {
  const g = new THREE.Group();
  mesh(taperTube([[-.15, 1.0, 0], [-.2, .6, 0], [-.45, .1, .05], [-.25, -.45, .1], [.3, -.55, .1], [.7, -.2, .05], [.85, .15, 0]], (t) => .12 + .4 * Math.sin(Math.PI * Math.min(1, t * 1.25)) * (t < .85 ? 1 : .6), 80, 22), toon(COL.stomach, { rim: .45, rimColor: 0xffd0d8 }), 0, 0, 0, g);
  if (o.outline !== false) addOutline(g, .02);
  return g;
}
export function makeIntestines(o = {}) {
  const g = new THREE.Group();
  // large intestine frame (with haustra)
  const lp = [[-.95, -.95, 0], [-1.0, -.2, 0], [-.95, .55, .05], [-.4, .7, .15], [.4, .7, .15], [.95, .55, .05], [1.0, -.2, 0], [.85, -.85, 0], [.4, -1.05, .05], [.15, -1.25, 0]];
  mesh(taperTube(lp, (t) => .19 + .03 * Math.sin(t * 110), 200, 18), toon(COL.colon, { rim: .4, rimColor: 0xffd6d6 }), 0, 0, 0, g);
  // small intestine coil
  const pts = []; const R = rng(11);
  for (let i = 0; i < 60; i++) { const a = i * .9; const rr = .55 * (.4 + .6 * ((i * 37) % 60) / 60); pts.push(V(Math.cos(a) * rr * 1.1, .35 - i * .018 + Math.sin(a * .5) * .15, Math.sin(a) * .25 + .15 + (R() - .5) * .1)); }
  const si = mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 600, .085, 12, false), toon(COL.gut, { rim: .45, rimColor: 0xffe0e0, unique: !!o.unique }), 0, 0, 0, g);
  g.userData.si = si;
  if (o.outline !== false) addOutline(g, .012);
  return g;
}

// ------------------------------------------------------------------ BONES / KNEE
export function makeBone(len = 2, r = .17, o = {}) {
  const g = new THREE.Group();
  const m = toon(COL.bone, { rim: .35 });
  mesh(G.cyl(r, r * 1.05, len, 24), m, 0, 0, 0, g);
  for (const s of [-1, 1]) {
    mesh(G.sphere(r * 1.6, 24, 16), m, -r * .8, s * len / 2, 0, g).scale.set(1, .8, 1);
    mesh(G.sphere(r * 1.6, 24, 16), m, r * .8, s * len / 2, 0, g).scale.set(1, .8, 1);
  }
  if (o.outline !== false) addOutline(g, .02);
  return g;
}
export function makeKnee(o = {}) {
  const g = new THREE.Group();
  const mB = toon(COL.bone, { rim: .4, rimColor: 0xfff5e0 });
  const femur = new THREE.Group(); g.add(femur);
  mesh(G.cyl(.32, .36, 3, 28), mB, 0, 2.0, 0, femur);
  for (const sx of [-1, 1]) mesh(G.sphere(.48, 32, 24), mB, sx * .38, .45, 0, femur).scale.set(.95, .85, 1.1);
  mesh(G.sphere(.6, 32, 24), mB, 0, .75, 0, femur).scale.set(1.3, .9, 1);
  const tibia = new THREE.Group(); g.add(tibia);
  mesh(G.cyl(.36, .3, 3, 28), mB, 0, -2.0, 0, tibia);
  const plat = mesh(G.cyl(.95, .55, .55, 36), mB, 0, -.45, 0, tibia); plat.scale.set(1, 1, .8);
  // fibula
  mesh(G.cyl(.12, .1, 2.8, 14), mB, .75, -2.2, -.2, tibia);
  // patella
  const pat = mesh(G.sphere(.35, 24, 16), mB, 0, .55, .78, g); pat.scale.set(1, 1.2, .5);
  // cartilage layers (blue-white)
  const mC = toon(COL.cartilage, { rim: .6, rimColor: 0xe8fbff, unique: true });
  const cartTop = new THREE.Group(); g.add(cartTop);
  for (const sx of [-1, 1]) { const c = mesh(G.sphere(.5, 32, 16, ), mC, sx * .38, .4, 0, cartTop); c.scale.set(.96, .5, 1.1); }
  const cartBot = mesh(G.cyl(.9, .9, .14, 36), mC, 0, -.14, 0, g); cartBot.scale.set(1, 1, .78);
  // menisci (C-shaped rings)
  const mMen = toon(0xe9f6fa, { rim: .5 });
  for (const sx of [-1, 1]) { const mm = mesh(new THREE.TorusGeometry(.36, .1, 10, 30, Math.PI * 1.6), mMen, sx * .42, -.03, 0, g); mm.rotation.x = Math.PI / 2; mm.rotation.z = sx > 0 ? -2.2 : .9; }
  // joint capsule (translucent)
  const cap = mesh(G.sphere(1.25, 40, 28), new THREE.MeshToonMaterial({ color: 0x9fd8ee, transparent: true, opacity: .16, depthWrite: false, side: THREE.DoubleSide }), 0, .05, 0, g);
  cap.scale.set(1.05, .75, .9); cap.userData.noOutline = true;
  g.userData = { femur, tibia, cartTop, cartBot, cartMat: mC, capsule: cap };
  if (o.outline !== false) addOutline(g, .025);
  return g;
}

// ------------------------------------------------------------------ cells & particles (instanced)
export function rbcGeometry(r = .3) {
  const pts = [];
  for (let i = 0; i <= 20; i++) { const t = i / 20; const x = t * r; const th = .12 * r + .32 * r * Math.pow(t, 1.2) * Math.sqrt(Math.max(0, 1 - Math.pow(t, 8))) * (1 + .3 * t); pts.push(new THREE.Vector2(x, th)); }
  for (let i = 20; i >= 0; i--) { const p = pts[i]; pts.push(new THREE.Vector2(p.x, -p.y)); }
  const g = new THREE.LatheGeometry(pts, 28); g.computeVertexNormals(); return g;
}
export function instanced(geo, mat, count) {
  const m = new THREE.InstancedMesh(geo, mat, count); m.instanceMatrix.setUsage(THREE.DynamicDrawUsage); m.frustumCulled = false; return m;
}
const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(), _s = new THREE.Vector3(), _p = new THREE.Vector3();
export function setInst(im, i, x, y, z, rx = 0, ry = 0, rz = 0, s = 1, sy, sz) {
  _p.set(x, y, z); _q.setFromEuler(_e.set(rx, ry, rz)); _s.set(s, sy ?? s, sz ?? s); _m.compose(_p, _q, _s); im.setMatrixAt(i, _m);
}

export function makeSugarCube(s = .14) {
  return mesh(roundBox(s, s, s, s * .18, 2), toon(0xffffff, { emissive: 0xfff3c8, emissiveIntensity: .45, rim: .6 }));
}
export function makeInsulinKey(o = {}) {
  const g = new THREE.Group(); const m = toon(0xffc53d, { rim: .6, emissive: 0x7a4a00, emissiveIntensity: .4 });
  const ring = mesh(G.torus(.12, .045, 10, 24), m, 0, .22, 0, g);
  mesh(G.cyl(.035, .035, .4, 10), m, 0, -.08, 0, g);
  mesh(G.box(.12, .05, .05), m, .06, -.2, 0, g); mesh(G.box(.09, .05, .05), m, .045, -.1, 0, g);
  if (o.outline !== false) addOutline(g, .012);
  return g;
}
export function makeNeuron(seed = 1, color = 0x8fd3ff) {
  const g = new THREE.Group(); const R = rng(seed);
  const mG = glow(color, .9);
  mesh(G.sphere(.12, 16, 12), glow(color, 1.8), 0, 0, 0, g);
  const branch = (p, d, len, r, depth) => {
    const e = p.clone().add(d.clone().multiplyScalar(len));
    const mid = p.clone().lerp(e, .5).add(V((R() - .5) * len * .3, (R() - .5) * len * .3, (R() - .5) * len * .3));
    mesh(taperTube([p, mid, e], (t) => r * (1 - .6 * t), 8, 6), mG, 0, 0, 0, g).userData.noOutline = true;
    if (depth > 0) for (let i = 0; i < 2; i++) branch(e, d.clone().add(V(R() - .5, R() - .5, R() - .5)).normalize(), len * .65, r * .6, depth - 1);
  };
  for (let i = 0; i < 6; i++) branch(V(), V(R() - .5, R() - .5, R() - .5).normalize(), .5 + R() * .3, .035, 2);
  // axon
  branch(V(), V(1, -.2, 0).normalize(), 1.6, .03, 1);
  return g;
}
export function makeFatCell(r = .5, o = {}) {
  const g = new THREE.Group();
  const core = mesh(G.sphere(r, 32, 24), toon(COL.fat, { rim: .6, rimColor: 0xfff6c8, emissive: 0x3a2a00, emissiveIntensity: .3 }), 0, 0, 0, g);
  const nuc = mesh(G.sphere(r * .18, 12, 10), toon(0xb58a2a), r * .55, r * .55, r * .45, g);
  g.userData.core = core;
  if (o.outline !== false) addOutline(g, .015);
  return g;
}
export function makeImmuneCell(r = .4) {
  const g = new THREE.Group();
  const geo = deform(new THREE.SphereGeometry(r, 40, 30), (v) => { v.multiplyScalar(1 + .12 * n3(v.x * 9 / r * .3, v.y * 9 / r * .3, v.z * 9 / r * .3)); });
  mesh(geo, toon(0xf3f6ff, { rim: .7, rimColor: 0xc9e3ff }), 0, 0, 0, g);
  mesh(G.sphere(r * .45, 16, 12), toon(0x9b7fe0), 0, 0, r * .4, g).scale.set(1.2, .8, .6);
  addOutline(g, .012);
  return g;
}

// Muscle bundle: fibers as instanced capsules
export function makeMuscle(o = {}) {
  const g = new THREE.Group();
  const n = o.n ?? 60, len = o.len ?? 3, R = rng(o.seed ?? 3);
  const geo = new THREE.CapsuleGeometry(.07, len, 4, 10);
  const mat = toon(COL.muscle, { rim: .4, rimColor: 0xffb4b4, unique: true, emissive: 0x400000, emissiveIntensity: 0 });
  const im = instanced(geo, mat, n);
  const fib = [];
  for (let i = 0; i < n; i++) { const a = R() * Math.PI * 2, r = Math.sqrt(R()) * .5; fib.push([Math.cos(a) * r, Math.sin(a) * r, (R() - .5) * .15]); }
  g.add(im); g.userData = { im, fib, mat, len };
  g.userData.squeeze = (s) => {
    // s: 0 relaxed..1 contracted -> shorter & thicker bulge
    for (let i = 0; i < n; i++) { const [x, z, oy] = fib[i]; const k = 1 + .45 * s * (1 - (x * x + z * z) / .3); setInst(im, i, x * k, oy, z * k, 0, 0, 0, 1 + .4 * s, 1 - .22 * s, 1 + .4 * s); }
    im.instanceMatrix.needsUpdate = true; mat.emissiveIntensity = s * .9;
  };
  g.userData.squeeze(0);
  return g;
}
