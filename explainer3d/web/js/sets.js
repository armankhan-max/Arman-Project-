// Sets: each set = a scene + the actors/props shots animate. Built lazily, cached per worker.
import * as THREE from 'three';
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import * as C from './core.js';
import { toon, glow, basic, addOutline, shadows, mesh, G, roundBox, tube, taperTube, V, rng, clamp, smooth, lerp, canvasTex, radialSprite, skyDome, lights } from './core.js';
import { Character, drawFace } from './character.js';
import * as O from './organs.js';
import * as E from './envs.js';

export let FONT = null;
export async function initAssets() {
  const json = await (await fetch('/node_modules/three/examples/fonts/helvetiker_bold.typeface.json')).json();
  FONT = new FontLoader().parse(json);
}
export function text3d(str, size = 1, o = {}) {
  const geo = new TextGeometry(str, { font: FONT, size, depth: o.depth ?? size * .35, curveSegments: 8, bevelEnabled: true, bevelThickness: size * .04, bevelSize: size * .03, bevelSegments: 3 });
  geo.computeBoundingBox(); const bb = geo.boundingBox;
  geo.translate(-(bb.max.x + bb.min.x) / 2, o.alignBottom ? -bb.min.y : -(bb.max.y + bb.min.y) / 2, -(o.depth ?? size * .35) / 2);
  const m = new THREE.Mesh(geo, [toon(o.front ?? 0xffffff, { rim: .2, emissive: o.emissive ?? 0x000000, emissiveIntensity: o.ei ?? 1 }), toon(o.side ?? 0xff7a3d, { rim: .3 })]);
  if (o.outline !== false) addOutline(m, o.outlineW ?? size * .03);
  m.castShadow = true;
  return m;
}
// Letters as individual meshes for per-letter animation
export function text3dLetters(str, size = 1, o = {}) {
  const g = new THREE.Group(); const letters = [];
  const full = new TextGeometry(str, { font: FONT, size, depth: .01, curveSegments: 2, bevelEnabled: false }); full.computeBoundingBox();
  const totalW = full.boundingBox.max.x - full.boundingBox.min.x; full.dispose();
  let x = -totalW / 2;
  for (const ch of str) {
    if (ch === ' ') { x += size * .35; continue; }
    const geo = new TextGeometry(ch, { font: FONT, size, depth: o.depth ?? size * .4, curveSegments: 8, bevelEnabled: true, bevelThickness: size * .05, bevelSize: size * .035, bevelSegments: 3 });
    geo.computeBoundingBox(); const bb = geo.boundingBox; const w = bb.max.x - bb.min.x;
    geo.translate(-bb.min.x - w / 2, 0, -(o.depth ?? size * .4) / 2);
    const m = new THREE.Mesh(geo, [toon(o.front ?? 0xffffff, { rim: .25, emissive: o.emissive ?? 0, emissiveIntensity: o.ei ?? 1 }), toon(o.side ?? 0xff7a3d, { rim: .3 })]);
    m.position.x = x + w / 2; m.userData.baseX = m.position.x; x += w + size * (o.spacing ?? .08);
    if (o.outline !== false) addOutline(m, o.outlineW ?? size * .025);
    m.castShadow = true; g.add(m); letters.push(m);
  }
  g.userData.letters = letters; return g;
}

// ------------------------------------------------------------------ shared camera
export const camera = new THREE.PerspectiveCamera(40, C.W / C.H, .05, 700);

// ------------------------------------------------------------------ helpers
export function faceDecal(size, state, res = 256) {
  const c = document.createElement('canvas'); c.width = c.height = res; const g = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false }));
  m.userData.noOutline = true; m.renderOrder = 5; let key = '';
  m.userData.set = (s) => { const k = JSON.stringify(s); if (k === key) return; key = k; drawFace(g, s, res); tex.needsUpdate = true; };
  m.userData.set(state); return m;
}
export function bokehField(n, spread, color = '#ffb0b0', size = .35, seed = 1, opacity = .6) {
  const R = rng(seed); const geo = new THREE.BufferGeometry(); const p = [];
  for (let i = 0; i < n; i++) p.push((R() - .5) * spread[0], (R() - .5) * spread[1], (R() - .5) * spread[2]);
  geo.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
  const mat = new THREE.PointsMaterial({ map: radialSprite(color, .25), size, transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending, fog: false });
  const pts = new THREE.Points(geo, mat); pts.frustumCulled = false; return pts;
}
export function heartShapeGeo(s = .2) {
  const sh = new THREE.Shape(); const x = 0, y = 0;
  sh.moveTo(x, y + .25 * s); sh.bezierCurveTo(x, y + .35 * s, x - .1 * s, y + .5 * s, x - .3 * s, y + .5 * s);
  sh.bezierCurveTo(x - .6 * s, y + .5 * s, x - .6 * s, y + .15 * s, x - .6 * s, y + .15 * s);
  sh.bezierCurveTo(x - .6 * s, y - .05 * s, x - .4 * s, y - .3 * s, x, y - .5 * s);
  sh.bezierCurveTo(x + .4 * s, y - .3 * s, x + .6 * s, y - .05 * s, x + .6 * s, y + .15 * s);
  sh.bezierCurveTo(x + .6 * s, y + .15 * s, x + .6 * s, y + .5 * s, x + .3 * s, y + .5 * s);
  sh.bezierCurveTo(x + .1 * s, y + .5 * s, x, y + .35 * s, x, y + .25 * s);
  const g = new THREE.ExtrudeGeometry(sh, { depth: .15 * s, bevelEnabled: true, bevelSize: .05 * s, bevelThickness: .05 * s, bevelSegments: 3 });
  g.center(); return g;
}
export function puff(n = 7, col = 0xffffff, seed = 3) {
  const g = new THREE.Group(); const R = rng(seed); const m = toon(col, { rim: .3, unique: true, transparent: true });
  for (let i = 0; i < n; i++) { const s = mesh(new THREE.IcosahedronGeometry(.3 + R() * .2, 1), m, 0, 0, 0, g); s.userData.dir = V(R() - .5, R() * .6, R() - .5).normalize(); }
  g.userData.mat = m;
  g.userData.at = (k) => { // k 0..1
    g.visible = k > 0 && k < 1; m.opacity = 1 - smooth(k);
    g.children.forEach((c) => { c.position.copy(c.userData.dir).multiplyScalar(C.easeOut(k) * 1.2); c.scale.setScalar(.4 + C.easeOut(k) * .9); });
  };
  return g;
}

// ------------------------------------------------------------------ X-RAY CHARACTER
export class XrayCharacter extends Character {
  constructor(o = {}) {
    super(Object.assign({ outline: .018 }, o));
    // unique transparent materials
    const map = new Map(); this.xmats = []; this.olmats = [];
    this.root.traverse((m) => {
      if (!m.isMesh || m === this.face) return;
      if (m.userData.isOutline) {
        if (!map.has(m.material.uuid)) { const nm = m.material.clone(); nm.transparent = true; nm.uniforms = { w: m.material.uniforms.w, col: m.material.uniforms.col }; nm.userData.op = 1; map.set(m.material.uuid, nm); this.olmats.push(nm); nm.fragmentShader = 'uniform vec3 col; uniform float op; void main(){ gl_FragColor=vec4(col,op); }'; nm.uniforms.op = { value: 1 }; }
        m.material = map.get(m.material.uuid); return;
      }
      if (!map.has(m.material.uuid)) { const nm = toon(m.material.color.getHex(), { unique: true, rim: .3, transparent: true }); map.set(m.material.uuid, nm); this.xmats.push(nm); }
      m.material = map.get(m.material.uuid);
    });
    // inner organs (no outline, gently emissive)
    this.inner = new THREE.Group(); this.body.add(this.inner);
    const em = (g, col, k = .35) => { g.traverse((m) => { if (m.isMesh && m.material?.isMeshToonMaterial) { const nm = toon(m.material.color.getHex(), { unique: true, rim: .6, rimColor: 0xffffff, emissive: col, emissiveIntensity: k }); m.material = nm; } }); return g; };
    this.organs = {};
    const lungs = em(O.makeLungs({ outline: false, depth: 3 }), 0x401018); lungs.scale.setScalar(.17); lungs.position.set(0, 1.25, -.05); this.inner.add(lungs); this.organs.lungs = lungs;
    const heart = em(O.makeHeart({ outline: false }), 0x500808, .5); heart.scale.setScalar(.088); heart.position.set(.02, 1.24, .17); this.inner.add(heart); this.organs.heart = heart;
    const liver = em(O.makeLiver({ outline: false }), 0x300808); liver.scale.setScalar(.12); liver.position.set(-.1, 1.06, .06); liver.rotation.y = Math.PI; this.inner.add(liver); this.organs.liver = liver;
    const stom = em(O.makeStomach({ outline: false }), 0x401018); stom.scale.setScalar(.1); stom.position.set(.1, 1.05, .1); stom.rotation.y = Math.PI; this.inner.add(stom); this.organs.stomach = stom;
    const gut = em(O.makeIntestines({ outline: false }), 0x401018); gut.scale.setScalar(.15); gut.position.set(0, .99, .06); this.inner.add(gut); this.organs.gut = gut;
    const brain = em(O.makeBrain({ outline: false }), 0x501828, .4); brain.scale.setScalar(.33); brain.position.set(0, .07, -.02); this.head.add(brain); this.organs.brain = brain;
    // leg bones + muscles
    this.legMuscles = [];
    const mBone = toon(O.COL.bone, { unique: true, emissive: 0x403020, emissiveIntensity: .4, rim: .6 });
    for (let i = 0; i < 2; i++) {
      const th = mesh(G.sphere(1, 20, 14), toon(O.COL.muscle, { unique: true, rim: .5, emissive: 0x500000, emissiveIntensity: .3 }), 0, -.22, .0, this.hip[i]); th.scale.set(.085, .2, .09);
      const ca = mesh(G.sphere(1, 20, 14), toon(O.COL.muscle, { unique: true, rim: .5, emissive: 0x500000, emissiveIntensity: .3 }), 0, -.16, -.03, this.knee[i]); ca.scale.set(.075, .15, .08);
      mesh(G.cyl(.022, .022, .44, 8), mBone, 0, -.23, 0, this.hip[i]); mesh(G.cyl(.02, .02, .42, 8), mBone, 0, -.22, 0, this.knee[i]);
      const kn = mesh(G.sphere(.04, 12, 10), mBone, 0, 0, 0, this.knee[i]);
      this.legMuscles.push(th, ca);
      th.userData.inner = ca.userData.inner = true;
    }
    this.innerParts = [this.inner, brain, ...this.legMuscles];
    this.xray(0);
  }
  xray(a, tint = 0x7fe3ff) {
    this.xa = a;
    for (const m of this.xmats) { m.opacity = 1 - a * .72; m.depthWrite = a < .4; m.userData.rim.value = .3 + a * 1.4; m.userData.rimColor.value.set(a > 0 ? tint : 0xffffff); }
    for (const m of this.olmats) m.uniforms.op.value = 1 - a * .75;
    this.face.material.opacity = 1 - a * .7;
    const vis = a > .01;
    this.inner.visible = vis; this.organs.brain.visible = vis; for (const m of this.legMuscles) m.visible = vis;
    this.root.traverse((m) => { if (m.isMesh && m.parent && !m.userData.isOutline) { } });
  }
  glowOrgan(name, k) { const g = this.organs[name]; if (!g) return; g.traverse((m) => { if (m.isMesh && m.material?.emissiveIntensity !== undefined && m.material.userData?.rim) { m.material.emissiveIntensity = .35 + k * 1.6; } }); }
}

// ------------------------------------------------------------------ SET BUILDERS
const builders = {};
export const SETS = new Map();
export function getSet(name) {
  if (!SETS.has(name)) { const s = builders[name](); s.name = name; SETS.set(name, s); }
  return SETS.get(name);
}
export function dropSetsExcept(keep) {
  for (const [k, s] of SETS) if (!keep.includes(k)) { C.disposeScene(s.scene); SETS.delete(k); }
}

// TOWN: sam (x-ray capable), friend, elder, title letters, bulb, storm cloud
builders.town = () => {
  const scene = E.buildTown();
  const sam = new XrayCharacter({ hoodie: 0x4fa6ea }); scene.add(sam.root); sam.root.position.set(-4.2, .16, 0);
  const elder = new Character({ hoodie: 0x9a7fd1, hair: 'bun', hairColor: 0xd9d9de, glasses: true }); scene.add(elder.root); elder.root.position.set(-6, .16, -30); elder.root.visible = false;
  // bench
  const bench = new THREE.Group(); scene.add(bench); bench.position.set(-6.3, 0, -30); bench.rotation.y = Math.PI / 2;
  mesh(roundBox(2.4, .12, .7, .04), toon(0xb87a4b), 0, .75, 0, bench); mesh(roundBox(2.4, .5, .1, .04), toon(0xb87a4b), 0, 1.15, -.35, bench);
  for (const x of [-1, 1]) mesh(G.box(.1, .75, .6), toon(0x3a3f55), x, .375, 0, bench);
  addOutline(bench, .02); shadows(bench);
  bench.visible = false;
  const title = text3dLetters('5,000', 3.2, { front: 0xffffff, side: 0xff6b3d, depth: 1.4 });
  const steps = text3dLetters('STEPS', 1.5, { front: 0xffd23f, side: 0xe0503a, depth: .6 });
  const titleG = new THREE.Group(); titleG.add(title, steps); steps.position.set(0, -1.15, .5); scene.add(titleG); titleG.position.set(0, 0, -14);
  shadows(titleG, true, false);
  // light bulb
  const bulb = new THREE.Group(); const glass = mesh(G.sphere(.32, 24, 18), glow(0xffe680, 2.2), 0, .1, 0, bulb); mesh(G.cyl(.14, .16, .25, 14), toon(0x9aa0b0), 0, -.28, 0, bulb);
  for (let i = 0; i < 3; i++) mesh(G.torus(.15, .025, 6, 16), toon(0x7a8090), 0, -.2 - i * .07, 0, bulb).rotation.x = Math.PI / 2;
  const rays = new THREE.Group(); bulb.add(rays); for (let i = 0; i < 10; i++) { const r = mesh(G.box(.05, .25, .05), glow(0xfff1a0, 2.5), 0, 0, 0, rays); const a = i / 10 * Math.PI * 2; r.position.set(Math.cos(a) * .6, Math.sin(a) * .6 + .1, 0); r.rotation.z = a - Math.PI / 2; }
  addOutline(bulb, .015); bulb.userData.rays = rays; scene.add(bulb); bulb.visible = false;
  // storm cloud
  const storm = new THREE.Group(); const sm = toon(0x6b6f80, { unique: true, transparent: true, rim: .2 });
  for (let i = 0; i < 5; i++) mesh(new THREE.IcosahedronGeometry(.35 + (i % 2) * .12, 2), sm, (i - 2) * .32, (i % 2) * .12, (i % 3 - 1) * .1, storm);
  const rain = []; for (let i = 0; i < 10; i++) { const d = mesh(G.cyl(.012, .012, .18, 4), basic(0x8fc8ff, { transparent: true }), (i / 9 - .5) * 1.2, -.4, (i % 3 - 1) * .12, storm); rain.push(d); }
  addOutline(storm, .015); storm.userData = { mat: sm, rain }; scene.add(storm); storm.visible = false;
  const dust = puff(8, 0xe8dccb, 5); scene.add(dust);
  return { scene, sam, elder, bench, titleG, title, steps, bulb, storm, dust, sun: scene.userData.sun, sky: scene.userData.sky };
};

builders.living = () => {
  const scene = E.buildLivingRoom();
  const sam = new Character({ hoodie: 0x4fa6ea }); scene.add(sam.root);
  // front door on right wall
  const door = new THREE.Group(); door.position.set(5, 0, -3.88); scene.add(door);
  mesh(G.box(1.6, 3, .1), toon(0xffffff), 0, 1.5, 0, door);
  const pivot = new THREE.Group(); pivot.position.set(-.7, 0, .06); door.add(pivot);
  const leaf = mesh(roundBox(1.4, 2.8, .12, .03), toon(0x3f7fbf), .7, 1.42, 0, pivot); mesh(G.sphere(.06, 10, 8), toon(0xffd34d), 1.25, 1.4, .1, pivot);
  const light = mesh(G.box(1.4, 2.8, .05), glow(0xfff2c8, 3), 0, 1.42, -.03, door); light.userData.noOutline = true;
  addOutline(door, .02); shadows(door);
  const sunBeam = new THREE.SpotLight(0xffe7b0, 0, 18, .7, .6, 1); sunBeam.position.set(5, 2, -5); sunBeam.target.position.set(4, 0, 0); scene.add(sunBeam, sunBeam.target);
  return { scene, sam, door, doorPivot: pivot, doorLight: light, sunBeam, screen: scene.userData.screen };
};
builders.dining = () => {
  const scene = E.buildDining();
  const sam = new Character({ hoodie: 0x4fa6ea }); scene.add(sam.root);
  return { scene, sam, table: scene.userData.table, pasta: scene.userData.pasta };
};
builders.bedroom = () => {
  const scene = E.buildBedroom();
  const sam = new Character({ hoodie: 0x4fa6ea }); scene.add(sam.root);
  return { scene, sam, bed: scene.userData.bed, blanket: scene.userData.blanket };
};

builders.city = () => {
  const heart = O.makeHeart(); heart.scale.setScalar(.75); heart.userData.lightColor = 0xff5060;
  const brain = O.makeBrain(); brain.scale.setScalar(1.1); brain.userData.lightColor = 0xff90c0;
  const lungs = O.makeLungs(); lungs.scale.setScalar(.75); lungs.position.y = -.2; lungs.userData.lightColor = 0xff8090;
  const gut = O.makeIntestines(); gut.scale.setScalar(1.1); gut.userData.lightColor = 0xffa080;
  const knee = O.makeKnee(); knee.scale.setScalar(.45); knee.userData.lightColor = 0x90e0ff;
  const liver = O.makeLiver(); liver.scale.setScalar(.95); liver.userData.lightColor = 0xff7060;
  const organs = [heart, brain, lungs, gut, knee, liver];
  const wrap = organs.map((o) => { const g = new THREE.Group(); g.add(o); g.userData.lightColor = o.userData.lightColor; return g; });
  const scene = E.buildOrganCity(wrap);
  // faces on organs (sleepy -> awake)
  const faces = wrap.map((w, i) => { const f = faceDecal(1.3, { eyes: 'sleepy', mouth: 'flat' }); f.position.set(0, .1, 1.35); w.add(f); return f; });
  const wave = new THREE.Mesh(new THREE.RingGeometry(.9, 1, 96), glow(0x8fe6ff, 2.5, { transparent: true, additive: true, side: THREE.DoubleSide }));
  wave.rotation.x = -Math.PI / 2; wave.position.y = .3; wave.userData.noOutline = true; scene.add(wave);
  return { scene, organs, wrap, faces, wave, heart, brain, lungs, gut, knee, liver };
};

// Chest cavity with hero heart
builders.heart = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x1a0408);
  scene.fog = new THREE.Fog(0x1a0408, 8, 30);
  const hemi = new THREE.HemisphereLight(0xffb0a0, 0x300810, .9); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xfff0e0, 2.2); key.position.set(4, 6, 6); scene.add(key);
  const back = new THREE.PointLight(0xff3050, 30, 20, 1.5); back.position.set(-3, 2, -4); scene.add(back);
  const heart = O.makeHeart({ outlineW: .025 }); scene.add(heart);
  const ribs = O.makeLungs({ outline: false }); ribs.scale.setScalar(2.3); ribs.position.set(0, .6, -3.2); scene.add(ribs);
  ribs.traverse((m) => { if (m.isMesh) m.material = toon(0xb85c6c, { rim: .5, rimColor: 0xff9aa8, unique: true }); });
  const bokeh = bokehField(160, [26, 16, 22], '#ff8a8a', .5, 3, .5); scene.add(bokeh);
  // blood burst particles (instanced RBCs)
  const rbc = O.instanced(O.rbcGeometry(.14), toon(O.COL.blood, { rim: .5, rimColor: 0xff9090 }), 220); scene.add(rbc);
  // glow ring for "stronger"
  const ring = new THREE.Mesh(new THREE.RingGeometry(2.2, 2.35, 96), glow(0xffd36b, 2, { transparent: true, additive: true, side: THREE.DoubleSide })); ring.userData.noOutline = true; scene.add(ring);
  // pressure gauge + vessel (for the pressure beat)
  return { scene, heart, ribs, bokeh, rbc, ring, key, back, hemi };
};

// Blood vessel tunnel: RBCs, valves, sugar cubes, immune cells, insulin keys
builders.vessel = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x2a0508);
  const pts = []; for (let i = 0; i <= 40; i++) pts.push(V(Math.sin(i * .35) * 2.2, Math.cos(i * .27) * 1.4, -i * 4));
  const curve = new THREE.CatmullRomCurve3(pts);
  const tun = E.tunnel(curve, 2.2, { color: 0x9e1624, color2: 0xff5a64, fog: 0x2a0508, fogDist: 22, wave: .05 }); scene.add(tun);
  const hemi = new THREE.HemisphereLight(0xffd0d0, 0x501010, 1.4); scene.add(hemi);
  const dl = new THREE.DirectionalLight(0xffffff, 1.2); dl.position.set(0, 3, 4); scene.add(dl);
  const N = 420; const rbc = O.instanced(O.rbcGeometry(.32), toon(O.COL.blood, { rim: .55, rimColor: 0xff9a9a, unique: true }), N); scene.add(rbc);
  const R = rng(4); const cells = []; for (let i = 0; i < N; i++) cells.push({ u: R(), a: R() * Math.PI * 2, r: Math.sqrt(R()) * 1.75, sp: .8 + R() * .4, rx: R() * 6, ry: R() * 6, spin: (R() - .5) * 2 });
  const NS = 60; const sugar = O.instanced(roundBox(.24, .24, .24, .05, 2), toon(0xffffff, { emissive: 0xfff0c0, emissiveIntensity: .6, rim: .8, rimColor: 0xfff6d8, unique: true }), NS); scene.add(sugar);
  const sug = []; for (let i = 0; i < NS; i++) sug.push({ u: R(), a: R() * Math.PI * 2, r: Math.sqrt(R()) * 1.6, rx: R() * 6, ry: R() * 6 });
  // valves (two leaflets) placed along the vessel
  const valves = [];
  for (const u of [.18, .36, .54, .72]) {
    const p = curve.getPointAt(u), tg = curve.getTangentAt(u);
    const vg = new THREE.Group(); vg.position.copy(p); vg.lookAt(p.clone().add(tg)); scene.add(vg);
    const flaps = [];
    for (const s of [-1, 1]) {
      const piv = new THREE.Group(); piv.position.set(0, s * 2.15, 0); vg.add(piv);
      const f = mesh(new THREE.SphereGeometry(2.2, 32, 16, 0, Math.PI, 0, Math.PI / 2), toon(0xff7d86, { rim: .6, unique: true, transparent: true, opacity: .92, side: THREE.DoubleSide }), 0, 0, 0, piv);
      f.scale.set(1, .98, .9); f.rotation.set(s > 0 ? Math.PI : 0, 0, 0); f.rotation.x = s > 0 ? -Math.PI / 2 : Math.PI / 2; f.position.set(0, -s * .0, 0);
      flaps.push(piv);
    }
    valves.push({ g: vg, flaps, u });
  }
  // immune cells
  const immune = []; for (let i = 0; i < 6; i++) { const c = O.makeImmuneCell(.55); scene.add(c); immune.push(c); c.visible = false; }
  const keys = []; for (let i = 0; i < 14; i++) { const k = O.makeInsulinKey(); k.scale.setScalar(1.3); scene.add(k); keys.push(k); k.visible = false; }
  const bokeh = bokehField(120, [8, 8, 160], '#ffc0c0', .25, 9, .45); bokeh.position.z = -80; scene.add(bokeh);
  return { scene, curve, tun, rbc, cells, sugar, sug, valves, immune, keys, hemi, dl, N, NS, bokeh };
};

// Leg cross-section: muscle bundles squeezing a vein (outside view, translucent vein)
builders.legpump = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x200810);
  scene.fog = new THREE.Fog(0x200810, 10, 30);
  scene.add(new THREE.HemisphereLight(0xffd0c8, 0x401018, 1.2));
  const dl = new THREE.DirectionalLight(0xffffff, 1.6); dl.position.set(3, 5, 6); scene.add(dl);
  const back = new THREE.PointLight(0x60a0ff, 25, 20); back.position.set(0, 2, -4); scene.add(back);
  const vein = mesh(G.cyl(.55, .55, 14, 40, 1, true), new THREE.MeshToonMaterial({ color: 0x4d7be0, transparent: true, opacity: .35, side: THREE.DoubleSide, depthWrite: false }), 0, 0, 0, scene);
  vein.userData.noOutline = true;
  const veinIn = mesh(G.cyl(.5, .5, 14, 40, 1, true), glow(0x2a4fb0, .6, { transparent: true, opacity: .3, side: THREE.BackSide }), 0, 0, 0, scene); veinIn.userData.noOutline = true;
  const musL = O.makeMuscle({ n: 70, len: 4, seed: 5 }); musL.position.set(-1.45, 0, 0); scene.add(musL);
  const musR = O.makeMuscle({ n: 70, len: 4, seed: 6 }); musR.position.set(1.45, 0, 0); scene.add(musR);
  // muscle sheath
  const N = 90; const rbc = O.instanced(O.rbcGeometry(.15), toon(0x8a1b2c, { rim: .5, rimColor: 0xff9090 }), N); scene.add(rbc);
  const R = rng(8); const cells = []; for (let i = 0; i < N; i++) cells.push({ y: R() * 14 - 7, a: R() * 6.28, r: Math.sqrt(R()) * .38, rx: R() * 6, ry: R() * 6 });
  // valves inside vein
  const valves = [];
  for (const y of [-3, 1, 5]) { const vg = new THREE.Group(); vg.position.y = y; scene.add(vg); const fl = []; for (const s of [-1, 1]) { const piv = new THREE.Group(); piv.position.x = s * .5; vg.add(piv); const f = mesh(G.box(.5, .05, .6), toon(0x9fb8ff, { rim: .5 }), -s * .25, 0, 0, piv); fl.push(piv); } valves.push({ vg, fl }); }
  // gravity arrow (3D) pointing down
  const arrow = new THREE.Group(); scene.add(arrow);
  mesh(G.cyl(.12, .12, 2.2, 14), glow(0xffd0a0, 1.6), 0, 0, 0, arrow); mesh(new THREE.ConeGeometry(.35, .6, 18), glow(0xffd0a0, 1.6), 0, -1.4, 0, arrow).rotation.x = Math.PI;
  arrow.position.set(2.8, 0, 1); arrow.visible = false;
  const bokeh = bokehField(100, [20, 18, 14], '#ff9a9a', .4, 2, .45); scene.add(bokeh);
  return { scene, vein, musL, musR, rbc, cells, valves, arrow, N, back };
};

// Brain in dark space with incoming blood/oxygen streams, fog, hippocampus, energy sparks
builders.brain = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0a0c22);
  scene.fog = new THREE.Fog(0x0a0c22, 8, 40);
  const hemi = new THREE.HemisphereLight(0xc8d8ff, 0x301020, .9); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xfff0f0, 2.0); key.position.set(4, 6, 5); scene.add(key);
  const rimL = new THREE.PointLight(0x6fa8ff, 40, 20); rimL.position.set(-4, 2, -3); scene.add(rimL);
  const brain = O.makeBrain({ unique: true, outlineW: .02 }); brain.scale.setScalar(1.6); scene.add(brain);
  // hippocampus (seahorse-shaped curl) inside, visible when cortex fades
  const hip = new THREE.Group(); scene.add(hip);
  for (const s of [-1, 1]) mesh(taperTube([[s * .5, -.35, .5], [s * .6, -.45, 0], [s * .55, -.3, -.5], [s * .4, 0, -.7], [s * .3, .25, -.55]], (t) => .16 * (1 - .6 * t), 40, 12), glow(0xffc85a, 1.6, { unique: true }), 0, 0, 0, hip);
  hip.visible = false;
  // blood + oxygen streams (instanced spheres/rbcs along curves rising into the brain)
  const streams = []; const R = rng(12);
  for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; streams.push(new THREE.CatmullRomCurve3([V(Math.cos(a) * 1.2, -8, Math.sin(a) * 1.2), V(Math.cos(a) * .9, -4, Math.sin(a) * .9), V(Math.cos(a) * .5, -2.2, Math.sin(a) * .5), V(Math.cos(a + .6) * 1.2, -.4, Math.sin(a + .6) * 1.5), V(Math.cos(a + 1.2) * 1.6, .9, Math.sin(a + 1.2) * 1.9)])); }
  const NB = 240; const blood = O.instanced(O.rbcGeometry(.09), toon(O.COL.blood, { rim: .6, rimColor: 0xffa0a0, emissive: 0x400000, emissiveIntensity: .6 }), NB); scene.add(blood);
  const NO = 240; const oxy = O.instanced(G.sphere(.05, 10, 8), glow(0x9fe8ff, 2.6), NO); scene.add(oxy);
  const bp = []; for (let i = 0; i < Math.max(NB, NO); i++) bp.push({ s: i % 6, u: R(), o: V((R() - .5) * .3, (R() - .5) * .3, (R() - .5) * .3), sp: .8 + R() * .4 });
  // fog cloud sprites around brain
  const fogTex = radialSprite('#9aa0b4', .2);
  const fogs = []; for (let i = 0; i < 40; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: fogTex, color: 0xb0b4c8, transparent: true, opacity: .55, depthWrite: false })); const a = R() * Math.PI * 2, e = (R() - .5) * 1.4, r = 1.8 + R() * 1.4; s.position.set(Math.cos(a) * Math.cos(e) * r, Math.sin(e) * r, Math.sin(a) * Math.cos(e) * r); s.scale.setScalar(2.5 + R() * 2); s.userData.home = s.position.clone(); scene.add(s); fogs.push(s); }
  // energy sparks
  const NS = 160; const sparks = O.instanced(G.sphere(.035, 8, 6), glow(0xfff0a0, 3.5), NS); scene.add(sparks);
  const sp = []; for (let i = 0; i < NS; i++) { const n = V(R() - .5, R() - .5, R() - .5).normalize(); sp.push({ n, ph: R(), sp: .5 + R() }); }
  const bokeh = bokehField(150, [30, 20, 30], '#8fb0ff', .45, 5, .4); scene.add(bokeh);
  // shield ring for memory protection
  const shield = new THREE.Mesh(new THREE.SphereGeometry(1.05, 40, 30), new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffd36b).multiplyScalar(1.5), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, wireframe: true }));
  scene.add(shield); shield.userData.noOutline = true;
  return { scene, brain, cortexMat: brain.userData.mat, hip, streams, blood, oxy, bp, NB, NO, fogs, sparks, sp, NS, key, rimL, shield, hemi };
};

// Neuron network with chemical release
builders.neurons = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x080a1e);
  scene.fog = new THREE.Fog(0x080a1e, 4, 22);
  const R = rng(21); const ns = [];
  for (let i = 0; i < 26; i++) { const n = O.makeNeuron(i + 2, [0x8fd3ff, 0xc39bff, 0x7fffd4][i % 3]); n.position.set((R() - .5) * 14, (R() - .5) * 8, -R() * 22 + 4); n.rotation.set(R() * 6, R() * 6, R() * 6); n.scale.setScalar(1.4 + R()); scene.add(n); ns.push(n); }
  const NC = 500; const chem = O.instanced(G.sphere(.05, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), NC); scene.add(chem);
  const cc = []; const pal = [new THREE.Color(0xffd84a).multiplyScalar(3), new THREE.Color(0xff6fb5).multiplyScalar(3), new THREE.Color(0x6fffc8).multiplyScalar(3)];
  for (let i = 0; i < NC; i++) { cc.push({ src: ns[i % 8].position.clone(), d: V(R() - .5, R() - .5, R() - .5).normalize(), sp: .6 + R() * 1.4, ph: R() }); chem.setColorAt(i, pal[i % 3]); }
  chem.instanceColor.needsUpdate = true;
  const bokeh = bokehField(200, [30, 20, 30], '#a0c0ff', .35, 8, .35); scene.add(bokeh);
  return { scene, ns, chem, cc, NC };
};

// Muscle + capillary + sugar transfer + GLUT doors + organs with faces (pancreas/liver)
builders.metabolic = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x1d0a1e);
  scene.fog = new THREE.Fog(0x1d0a1e, 10, 40);
  scene.add(new THREE.HemisphereLight(0xffe0e8, 0x301030, 1.1));
  const dl = new THREE.DirectionalLight(0xffffff, 1.8); dl.position.set(4, 6, 6); scene.add(dl);
  const fill = new THREE.PointLight(0xff70a0, 25, 25); fill.position.set(-5, 2, 2); scene.add(fill);
  // muscle cell: big rounded block with striations and doors
  const muscle = new THREE.Group(); scene.add(muscle); muscle.position.set(0, -.2, -2);
  const fibers = []; const mF = toon(O.COL.muscle, { rim: .5, rimColor: 0xffb0b0, unique: true, emissive: 0x501010, emissiveIntensity: 0 });
  for (let i = 0; i < 5; i++) for (let j = 0; j < 2; j++) { const f = mesh(G.capsule(.42, 7, 16), mF, 0, -i * .82 + 1.6, -j * .8, muscle); f.rotation.z = Math.PI / 2; fibers.push(f); }
  // striation rings
  for (let i = 0; i < 14; i++) mesh(G.torus(.43, .025, 6, 24), toon(0xb0303c), -3.4 + i * .52, 1.6, 0, muscle).rotation.y = Math.PI / 2;
  // doors (GLUT4 channels) on top fiber surface
  const doors = []; for (let i = 0; i < 6; i++) { const d = new THREE.Group(); d.position.set(-2.8 + i * 1.12, 2.02, .1); muscle.add(d); mesh(G.torus(.17, .05, 10, 24), toon(0x7ad3ff, { rim: .5 }), 0, 0, 0, d).rotation.x = Math.PI / 2; const lid = mesh(G.cyl(.15, .15, .04, 20), toon(0x4a9bd1), 0, .02, 0, d); d.userData.lid = lid; doors.push(d); }
  // capillary above
  const cap = mesh(G.cyl(.55, .55, 16, 32, 1, true), new THREE.MeshToonMaterial({ color: 0xe0404c, transparent: true, opacity: .32, side: THREE.DoubleSide, depthWrite: false }), 0, 4.2, -2, scene); cap.rotation.z = Math.PI / 2; cap.userData.noOutline = true;
  const NS = 40; const sugar = O.instanced(roundBox(.2, .2, .2, .04, 2), toon(0xffffff, { emissive: 0xfff0c0, emissiveIntensity: .7, rim: .8 }), NS); scene.add(sugar);
  const R = rng(3); const sg = []; for (let i = 0; i < NS; i++) sg.push({ x: (R() - .5) * 14, ph: R(), door: i % 6, a: R() * 6.28, r: Math.sqrt(R()) * .35 });
  const NR = 40; const rbc = O.instanced(O.rbcGeometry(.16), toon(O.COL.blood, { rim: .5 }), NR); scene.add(rbc);
  const rc = []; for (let i = 0; i < NR; i++) rc.push({ x: (R() - .5) * 16, a: R() * 6.28, r: Math.sqrt(R()) * .38, rx: R() * 6 });
  const keys = []; for (let i = 0; i < 10; i++) { const k = O.makeInsulinKey(); scene.add(k); keys.push(k); k.visible = false; }
  // organs with faces
  const pancreas = O.makePancreas({ unique: true }); pancreas.scale.setScalar(1.3); scene.add(pancreas); pancreas.visible = false;
  const pFace = faceDecal(.9, { eyes: 'open', brow: 'worried', mouth: 'wobble', sweat: 1 }); pFace.position.set(-.5, .05, .38); pancreas.add(pFace);
  const liver = O.makeLiver({ unique: true }); liver.scale.setScalar(1.3); scene.add(liver); liver.visible = false;
  const lFace = faceDecal(1.1, { eyes: 'open', brow: 'worried', mouth: 'frown' }); lFace.position.set(.2, .15, .82); liver.add(lFace);
  addOutline(muscle, .02);
  const bokeh = bokehField(120, [30, 18, 20], '#ffb0d0', .4, 6, .4); scene.add(bokeh);
  return { scene, muscle, fibers, mF, doors, cap, sugar, sg, NS, rbc, rc, NR, keys, pancreas, pFace, liver, lFace };
};

// Infographic stage: graph, gauge, clock, counter, stacking blocks, gym items
builders.stage = () => {
  const scene = new THREE.Scene();
  const sky = skyDome(0x141633, 0x2b2f5e, 0x141633); scene.add(sky);
  scene.fog = new THREE.Fog(0x1a1c3d, 18, 60);
  scene.add(new THREE.HemisphereLight(0xc8d0ff, 0x302850, 1.0));
  const key = new THREE.DirectionalLight(0xffffff, 2.0); key.position.set(5, 10, 7); key.castShadow = true;
  Object.assign(key.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12 }); key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0005; scene.add(key);
  const floor = mesh(new THREE.CircleGeometry(40, 64), toon(0x2a2d58, { rim: 0 }), 0, 0, 0, scene); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true;
  const grid = new THREE.GridHelper(40, 40, 0x5a63c0, 0x3a3f80); grid.position.y = .01; grid.material.transparent = true; grid.material.opacity = .5; scene.add(grid);
  // --- graph: axes + ribbon
  const graph = new THREE.Group(); scene.add(graph); graph.position.set(0, 0, 0);
  mesh(G.box(.08, 4.2, .08), toon(0xdfe3ff), -4, 2.1, 0, graph); mesh(G.box(8.4, .08, .08), toon(0xdfe3ff), .2, .05, 0, graph);
  const ribbon = new THREE.Mesh(new THREE.BufferGeometry(), glow(0xff4d5a, 2.2)); ribbon.userData.noOutline = true; graph.add(ribbon);
  const area = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color: 0xff4d5a, transparent: true, opacity: .22, side: THREE.DoubleSide, depthWrite: false })); graph.add(area);
  const dot = mesh(G.sphere(.16, 16, 12), glow(0xffffff, 3), 0, 0, 0, graph);
  graph.userData = { ribbon, area, dot };
  graph.visible = false;
  // --- gauge
  const gauge = new THREE.Group(); scene.add(gauge); gauge.position.set(0, 2.5, 0);
  mesh(G.cyl(2.3, 2.3, .3, 64), toon(0x222642, { rim: .3 }), 0, 0, -.2, gauge).rotation.x = Math.PI / 2;
  const segs = [[0x4fd17a, 0, .33], [0xffd23f, .33, .66], [0xff5a4f, .66, 1]];
  for (const [c, a, b] of segs) { const r = mesh(new THREE.RingGeometry(1.5, 2.05, 48, 1, Math.PI - b * Math.PI, (b - a) * Math.PI), glow(c, 1.3, { side: THREE.DoubleSide }), 0, 0, .0, gauge); r.userData.noOutline = true; }
  const needle = new THREE.Group(); gauge.add(needle); mesh(G.box(.1, 1.9, .08), toon(0xffffff, { emissive: 0x666666 }), 0, .9, .12, needle); mesh(G.sphere(.22, 16, 12), toon(0xeeeeee), 0, 0, .12, needle);
  gauge.userData.needle = needle; gauge.visible = false;
  // --- clock
  const clock = new THREE.Group(); scene.add(clock); clock.position.set(0, 3, 0);
  mesh(G.cyl(2.6, 2.6, .35, 64), toon(0xf6f4ff, { rim: .3 }), 0, 0, 0, clock).rotation.x = Math.PI / 2;
  mesh(G.torus(2.6, .18, 12, 64), toon(0x4fa6ea, { rim: .4 }), 0, 0, 0, clock);
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; mesh(G.box(.1, i % 3 ? .3 : .5, .06), toon(0x2a2a3a), Math.sin(a) * 2.2, Math.cos(a) * 2.2, .2, clock).rotation.z = -a; }
  const sector = new THREE.Mesh(new THREE.RingGeometry(.05, 2.05, 64, 1, 0, .01), glow(0x4fd17a, 1.1, { transparent: true, opacity: .85, side: THREE.DoubleSide })); sector.position.z = .19; sector.userData.noOutline = true; clock.add(sector);
  const hand = new THREE.Group(); clock.add(hand); mesh(G.box(.12, 1.9, .06), toon(0x2a2a3a), 0, .85, .25, hand); mesh(G.sphere(.18, 12, 10), toon(0xff6b3d), 0, 0, .25, hand);
  clock.userData = { sector, hand }; clock.visible = false;
  // --- text bits
  const kcal = text3d('kcal', .9, { front: 0xffd23f, side: 0xe0503a }); scene.add(kcal); kcal.visible = false;
  const digits = []; for (let d = 0; d < 10; d++) digits.push(new TextGeometry(String(d), { font: FONT, size: 2.2, depth: .7, curveSegments: 6, bevelEnabled: true, bevelThickness: .08, bevelSize: .06, bevelSegments: 2 }));
  digits.forEach((g) => { g.computeBoundingBox(); const bb = g.boundingBox; g.translate(-(bb.max.x + bb.min.x) / 2, 0, -.35); g.userData.shared = true; });
  const counter = new THREE.Group(); scene.add(counter); const dm = [];
  for (let i = 0; i < 3; i++) { const m = new THREE.Mesh(digits[0], [toon(0xffffff, { rim: .2 }), toon(0xff6b3d)]); m.position.x = (i - 1) * 1.75; m.castShadow = true; counter.add(m); dm.push(m); }
  counter.visible = false;
  const minTxt = text3d('40-50 MIN', .8, { front: 0xffffff, side: 0x4fa6ea }); scene.add(minTxt); minTxt.visible = false;
  // flames for burning
  const NF = 80; const flames = O.instanced(new THREE.IcosahedronGeometry(.18, 1), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: .9, blending: THREE.AdditiveBlending, depthWrite: false }), NF); scene.add(flames);
  const fc = new THREE.Color(); for (let i = 0; i < NF; i++) { fc.setHSL(.02 + (i % 7) * .015, 1, .55).multiplyScalar(2.2); flames.setColorAt(i, fc); } flames.instanceColor.needsUpdate = true; flames.visible = false;
  // stacking blocks
  const NB = 70; const blocks = O.instanced(roundBox(1.2, .3, 1.2, .06, 2), toon(0xffffff, { rim: .4 }), NB); scene.add(blocks); blocks.castShadow = true;
  const bc = new THREE.Color(); for (let i = 0; i < NB; i++) { bc.setHSL((.55 + i * .013) % 1, .7, .62); blocks.setColorAt(i, bc); } blocks.instanceColor.needsUpdate = true; blocks.visible = false;
  // gym items
  const gym = new THREE.Group(); scene.add(gym); gym.visible = false;
  const dumb = new THREE.Group(); mesh(G.cyl(.08, .08, 1.4, 12), toon(0x9aa0b0), 0, 0, 0, dumb).rotation.z = Math.PI / 2; for (const s of [-1, 1]) for (const k of [0, 1]) mesh(G.cyl(.38 - k * .06, .38 - k * .06, .14, 24), toon(0x2b2f3a, { rim: .4 }), s * (.5 + k * .16), 0, 0, dumb).rotation.z = Math.PI / 2;
  const kb = new THREE.Group(); mesh(G.sphere(.45, 24, 18), toon(0x2b2f3a, { rim: .4 }), 0, 0, 0, kb); mesh(G.torus(.28, .06, 8, 20, Math.PI), toon(0x2b2f3a), 0, .4, 0, kb);
  const tread = new THREE.Group(); mesh(roundBox(1.4, .3, 3, .1), toon(0x333845, { rim: .3 }), 0, .15, 0, tread); mesh(G.box(1.2, .05, 2.6), toon(0x15171d), 0, .32, 0, tread); for (const s of [-1, 1]) mesh(G.cyl(.05, .05, 1.6, 8), toon(0x9aa0b0), s * .6, 1, -1.2, tread); mesh(roundBox(1.4, .5, .3, .06), toon(0x333845), 0, 1.8, -1.25, tread); const scr = mesh(G.box(.8, .3, .05), glow(0x4fe0ff, 1.5), 0, 1.85, -1.08, tread);
  const outfit = new THREE.Group(); mesh(G.torus(.25, .02, 6, 20, Math.PI), toon(0x9aa0b0), 0, 1.6, 0, outfit).rotation.z = 0; mesh(G.cyl(.015, .015, .3, 6), toon(0x9aa0b0), 0, 1.75, 0, outfit);
  mesh(roundBox(.8, .9, .25, .1), toon(0xff3d7f, { rim: .4 }), 0, 1.1, 0, outfit); mesh(roundBox(.85, .1, .27, .03), toon(0x37e0c8), 0, 1.3, 0, outfit);
  gym.add(dumb, kb, tread, outfit); dumb.position.set(-3, .4, 0); kb.position.set(-1, .45, .5); tread.position.set(1.6, 0, -.5); outfit.position.set(4, 0, 0);
  const puffs = [puff(8, 0xffffff, 1), puff(8, 0xffffff, 2), puff(8, 0xffffff, 3), puff(8, 0xffffff, 4)]; puffs.forEach((p, i) => { gym.add(p); p.position.copy([dumb, kb, tread, outfit][i].position).add(V(0, .6, 0)); });
  addOutline(gym, .02); shadows(gym);
  gym.userData = { items: [dumb, kb, tread, outfit], puffs };
  const sam = new Character({ hoodie: 0x4fa6ea }); scene.add(sam.root); sam.root.visible = false;
  addOutline(clock, .02); addOutline(gauge, .02);
  return { scene, graph, gauge, clock, kcal, digits, counter, dm, minTxt, flames, NF, blocks, NB, gym, sam, key, floor, grid };
};

// Gut: intestines outside (coiled) + inside tunnel with food
builders.gut = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x24080e);
  scene.fog = new THREE.Fog(0x24080e, 6, 26);
  scene.add(new THREE.HemisphereLight(0xffe0d8, 0x401018, 1.1));
  const dl = new THREE.DirectionalLight(0xffffff, 2); dl.position.set(3, 5, 6); scene.add(dl);
  const back = new THREE.PointLight(0xff9050, 30, 20); back.position.set(-3, 2, -4); scene.add(back);
  const gut = O.makeIntestines({ unique: true }); gut.scale.setScalar(2.2); scene.add(gut);
  const stom = O.makeStomach(); stom.scale.setScalar(1.4); stom.position.set(1.0, 3.3, -.6); stom.rotation.y = Math.PI; scene.add(stom);
  const face = faceDecal(1.4, { eyes: 'happy', mouth: 'smile', blush: 1 }); face.position.set(0, .1, 1.3); gut.add(face); face.scale.setScalar(1 / 2.2 * 1.6); face.visible = false;
  const NH = 16; const hearts = []; const hg = heartShapeGeo(.6); for (let i = 0; i < NH; i++) { const h = mesh(hg, toon(0xff6f9a, { rim: .5, emissive: 0x501020, emissiveIntensity: .6 }), 0, 0, 0, scene); hearts.push(h); h.visible = false; }
  const bokeh = bokehField(120, [24, 16, 20], '#ffb090', .45, 4, .45); scene.add(bokeh);
  // tunnel world placed far away
  const pts = []; for (let i = 0; i <= 40; i++) pts.push(V(200 + Math.sin(i * .5) * 3, Math.cos(i * .4) * 2, -i * 3));
  const curve = new THREE.CatmullRomCurve3(pts);
  const tun = E.tunnel(curve, 2.0, { color: 0xc9586a, color2: 0xffb0a8, fog: 0x3a0e14, fogDist: 14, wave: .18, waveSpeed: 1.2, villi: 1 }); scene.add(tun);
  const NF = 30; const food = []; const R = rng(14); const fcol = [0x9bd35a, 0xf2c14e, 0xe8894a, 0xd9e36b];
  for (let i = 0; i < NF; i++) { const f = mesh(new THREE.IcosahedronGeometry(.35 + R() * .3, 1), toon(fcol[i % 4], { rim: .5 }), 0, 0, 0, scene); f.userData = { u: R() * .9, a: R() * 6.28, r: R() * 1.0, s: R() }; food.push(f); }
  const NG = 18; const gas = []; for (let i = 0; i < NG; i++) { const b = mesh(G.sphere(.4 + R() * .4, 20, 14), new THREE.MeshToonMaterial({ color: 0xd8f0ff, transparent: true, opacity: .45 }), 0, 0, 0, scene); b.userData = { u: R() * .8, a: R() * 6.28, r: R() * 1.1 }; gas.push(b); }
  addOutline(scene, .015);
  return { scene, gut, stom, face, hearts, curve, tun, food, gas, back };
};

builders.knee = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0b1626);
  scene.fog = new THREE.Fog(0x0b1626, 8, 30);
  scene.add(new THREE.HemisphereLight(0xd0e8ff, 0x202838, 1.0));
  const dl = new THREE.DirectionalLight(0xffffff, 2.2); dl.position.set(4, 5, 6); scene.add(dl);
  const rimL = new THREE.PointLight(0x5fd0ff, 40, 20); rimL.position.set(-4, 1, -3); scene.add(rimL);
  const knee = O.makeKnee(); scene.add(knee);
  // blood vessels around (stop short of cartilage)
  const vess = new THREE.Group(); scene.add(vess); const mA = toon(O.COL.artery, { rim: .5 });
  for (const s of [-1, 1]) { mesh(taperTube([[s * 1.6, 3, -.6], [s * 1.5, 1.4, -.5], [s * 1.35, .6, .2], [s * 1.0, .25, .9]], () => .07, 30, 8), mA, 0, 0, 0, vess); mesh(taperTube([[s * 1.5, -3, -.6], [s * 1.45, -1.4, -.4], [s * 1.3, -.6, .3], [s * .95, -.35, .95]], () => .07, 30, 8), toon(O.COL.vein, { rim: .5 }), 0, 0, 0, vess); }
  addOutline(vess, .015);
  // fluid particles
  const NF = 200; const fluid = O.instanced(G.sphere(.06, 8, 6), glow(0x7fe8ff, 2.4), NF); scene.add(fluid);
  const NW = 80; const waste = O.instanced(G.sphere(.07, 8, 6), toon(0x8a7a5a, { rim: .3 }), NW); scene.add(waste);
  const R = rng(17); const fp = []; for (let i = 0; i < 200; i++) fp.push({ a: R() * 6.28, r: .3 + R() * .7, y: (R() - .5) * .25, ph: R(), sp: .6 + R() * .6 });
  const bokeh = bokehField(120, [24, 18, 20], '#8fd0ff', .4, 11, .4); scene.add(bokeh);
  // bone cross-section (density) far away
  const bone = new THREE.Group(); bone.position.set(60, 0, 0); scene.add(bone);
  const shell = mesh(G.cyl(2, 2, 6, 48, 1, true), toon(O.COL.bone, { rim: .6, transparent: true, opacity: .22, depthWrite: false, unique: true, side: THREE.DoubleSide }), 0, 0, 0, bone); shell.userData.noOutline = true;
  const capTop = mesh(new THREE.RingGeometry(1.6, 2, 48), toon(0xfff6e0, { side: THREE.DoubleSide }), 0, 3, 0, bone); capTop.rotation.x = -Math.PI / 2; capTop.visible = false;
  const NT = 260; const trab = O.instanced(G.cyl(.05, .05, 1, 6), toon(0xf2cf8e, { rim: .5, emissive: 0x806020, emissiveIntensity: 0, unique: true }), NT); bone.add(trab);
  const tb = []; for (let i = 0; i < NT; i++) { const a = R() * 6.28, r = Math.sqrt(R()) * 1.55; tb.push({ x: Math.cos(a) * r, z: Math.sin(a) * r, y: (R() - .5) * 5.6, rx: R() * 3, rz: R() * 3, len: .4 + R() * .6, th: R() }); }
  const marrow = mesh(G.cyl(1.58, 1.58, .2, 40), toon(0xd9705a, { rim: .2 }), 0, -2.9, 0, bone);
  addOutline(bone, .02);
  const pulse = new THREE.Mesh(new THREE.TorusGeometry(2.05, .08, 10, 64), glow(0xffe0a0, 2.5, { transparent: true, additive: true })); pulse.rotation.x = Math.PI / 2; bone.add(pulse);
  return { scene, knee, vess, fluid, waste, fp, NF, NW, bone, trab, tb, NT, pulse, marrow, rimL };
};

builders.fat = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x221208);
  scene.fog = new THREE.Fog(0x221208, 8, 30);
  scene.add(new THREE.HemisphereLight(0xfff0d8, 0x402810, 1.1));
  const dl = new THREE.DirectionalLight(0xffffff, 2); dl.position.set(4, 6, 6); scene.add(dl);
  const warm = new THREE.PointLight(0xff7a20, 0, 25, 1.4); warm.position.set(0, 1, 4); scene.add(warm);
  const cells = []; const R = rng(31);
  for (let i = -4; i <= 4; i++) for (let j = -3; j <= 3; j++) for (let k = 0; k < 2; k++) {
    const c = O.makeFatCell(.6 + R() * .15); c.position.set(i * 1.25 + (j % 2) * .62, j * 1.1, -k * 1.3 - R() * .2); scene.add(c); c.userData.ph = R(); c.userData.base = c.scale.x; cells.push(c);
  }
  const NE = 260; const energy = O.instanced(G.sphere(.05, 8, 6), glow(0xffb84a, 3.5), NE); scene.add(energy);
  const ep = []; for (let i = 0; i < NE; i++) ep.push({ c: Math.floor(R() * cells.length), ph: R(), d: V(R() - .5, .6 + R(), R() - .5).normalize(), sp: .6 + R() });
  const bokeh = bokehField(120, [24, 18, 20], '#ffc070', .45, 13, .45); scene.add(bokeh);
  return { scene, cells, energy, ep, NE, warm };
};

builders.lungs = () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0c1424);
  scene.fog = new THREE.Fog(0x0c1424, 8, 30);
  scene.add(new THREE.HemisphereLight(0xd8e8ff, 0x302030, 1.0));
  const dl = new THREE.DirectionalLight(0xffffff, 2); dl.position.set(4, 6, 6); scene.add(dl);
  const rimL = new THREE.PointLight(0x7fd0ff, 40, 20); rimL.position.set(-3, 2, -4); scene.add(rimL);
  const lungs = O.makeLungs({ depth: 5 }); scene.add(lungs);
  const lungsX = O.makeLungs({ transparent: true, opacity: .28, depth: 6, brColor: 0xffe8ea }); scene.add(lungsX); lungsX.visible = false;
  const NA = 300; const air = O.instanced(G.sphere(.045, 8, 6), glow(0x8ff0ff, 3), NA); scene.add(air);
  const tips = lungsX.userData.branches.filter((b) => b.userData.depth >= 5);
  const tipGlow = O.instanced(G.sphere(.09, 10, 8), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }), tips.length); scene.add(tipGlow);
  tips.forEach((b, i) => O.setInst(tipGlow, i, b.userData.end.x, b.userData.end.y, b.userData.end.z, 0, 0, 0, 1));
  const bokeh = bokehField(120, [24, 18, 20], '#9fd0ff', .4, 15, .4); scene.add(bokeh);
  // immune guard ring etc not needed
  return { scene, lungs, lungsX, air, NA, tips, tipGlow };
};

export function warmAll() { }
