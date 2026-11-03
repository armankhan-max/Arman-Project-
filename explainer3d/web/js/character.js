// 2D-faced toon character in a 3D world: big white head with a hand-drawn face texture,
// hoodie body, thin white legs, ball hands/feet. Procedural walk cycle and poses.
import * as THREE from 'three';
import { toon, addOutline, shadows, mesh, G, roundBox, clamp, smooth, lerp } from './core.js';

const WHITE = 0xf4f3f7;
const INK = '#1d1a26';

export function drawFace(g, s, S) {
  g.clearRect(0, 0, S, S);
  const k = S / 512;
  g.save(); g.scale(k, k);
  g.lineCap = 'round'; g.lineJoin = 'round';
  const cx = 256 + (s.look?.[0] ?? 0) * 26, cy = 250 - (s.look?.[1] ?? 0) * 18;
  const ex = 58, ey = cy;
  const blink = s.blink ?? 0;
  // blush
  if (s.blush) {
    g.fillStyle = `rgba(255,120,140,${0.35 * s.blush})`;
    for (const sx of [-1, 1]) { g.beginPath(); g.ellipse(256 + sx * 105, cy + 52, 34, 17, 0, 0, Math.PI * 2); g.fill(); }
  }
  // eyes
  for (const side of [-1, 1]) {
    const x = cx + side * ex, y = ey;
    g.fillStyle = INK; g.strokeStyle = INK;
    const mode = blink > .55 ? 'closed' : s.eyes || 'open';
    if (mode === 'open' || mode === 'wide' || mode === 'half' || mode === 'sleepy') {
      const wide = mode === 'wide' ? 1.25 : 1;
      const h = 30 * wide * (1 - blink * 1.5);
      g.beginPath(); g.ellipse(x, y, 19 * wide, Math.max(3, h), 0, 0, Math.PI * 2); g.fill();
      if (h > 10) { g.fillStyle = '#fff'; g.beginPath(); g.ellipse(x + 6, y - 10 * wide, 6.5, 7.5, 0, 0, Math.PI * 2); g.fill(); }
      if (mode === 'half' || mode === 'sleepy') { // heavy eyelid
        const lid = mode === 'sleepy' ? .62 : .42;
        g.fillStyle = '#f4f3f7'; g.fillRect(x - 30, y - 45, 60, 45 * 0.6 + 70 * lid - 20);
        g.strokeStyle = INK; g.lineWidth = 7; g.beginPath(); g.moveTo(x - 23, y - 40 + 70 * lid - 2); g.lineTo(x + 23, y - 40 + 70 * lid - 2); g.stroke();
      }
    } else if (mode === 'happy') {
      g.lineWidth = 9; g.beginPath(); g.arc(x, y + 10, 20, Math.PI * 1.1, Math.PI * 1.9); g.stroke();
    } else if (mode === 'closed') {
      g.lineWidth = 8; g.beginPath(); g.arc(x, y - 6, 20, Math.PI * .15, Math.PI * .85); g.stroke();
    } else if (mode === 'star') {
      g.fillStyle = '#ffd34d'; g.beginPath();
      for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? 11 : 26; g.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); }
      g.closePath(); g.fill(); g.lineWidth = 4; g.stroke();
    }
  }
  // brows
  g.strokeStyle = INK; g.lineWidth = 10;
  const b = s.brow || 'none';
  if (b !== 'none') {
    for (const side of [-1, 1]) {
      const x = cx + side * ex, y = ey - 48 - (b === 'raised' ? 12 : 0);
      g.beginPath();
      if (b === 'angry') { g.moveTo(x + side * 26, y - 12); g.lineTo(x - side * 20, y + 8); }
      else if (b === 'worried') { g.moveTo(x + side * 24, y + 8); g.lineTo(x - side * 20, y - 10); }
      else { g.moveTo(x - 22, y + 2); g.quadraticCurveTo(x, y - 8, x + 22, y + 2); }
      g.stroke();
    }
  }
  // mouth
  const mx = 256 + (s.look?.[0] ?? 0) * 18, my = cy + 78;
  const m = s.mouth || 'smile';
  g.lineWidth = 8; g.strokeStyle = INK; g.fillStyle = INK;
  g.beginPath();
  if (m === 'smile') { g.arc(mx, my - 20, 26, Math.PI * .2, Math.PI * .8); g.stroke(); }
  else if (m === 'smallSmile') { g.arc(mx, my - 12, 15, Math.PI * .2, Math.PI * .8); g.stroke(); }
  else if (m === 'frown') { g.arc(mx, my + 18, 20, Math.PI * 1.2, Math.PI * 1.8); g.stroke(); }
  else if (m === 'flat') { g.moveTo(mx - 16, my); g.lineTo(mx + 16, my); g.stroke(); }
  else if (m === 'o') { g.ellipse(mx, my, 13, 17, 0, 0, Math.PI * 2); g.fill(); }
  else if (m === 'yawn') { g.ellipse(mx, my + 4, 20, 28, 0, 0, Math.PI * 2); g.fill(); g.fillStyle = '#e8687a'; g.beginPath(); g.ellipse(mx, my + 18, 12, 9, 0, 0, Math.PI * 2); g.fill(); }
  else if (m === 'grin' || m === 'open') {
    g.moveTo(mx - 30, my - 8); g.quadraticCurveTo(mx, my - 2, mx + 30, my - 8); g.quadraticCurveTo(mx, my + 40, mx - 30, my - 8); g.fill();
    g.fillStyle = '#e8687a'; g.beginPath(); g.ellipse(mx, my + 14, 13, 7, 0, 0, Math.PI * 2); g.fill();
  } else if (m === 'wobble') { g.moveTo(mx - 22, my); for (let i = 0; i <= 8; i++) g.lineTo(mx - 22 + i * 5.5, my + (i % 2 ? -5 : 5)); g.stroke(); }
  else if (m === 'teeth') {
    g.fillStyle = '#fff'; g.beginPath(); g.roundRect(mx - 30, my - 12, 60, 24, 8); g.fill(); g.lineWidth = 6; g.stroke();
    g.beginPath(); g.moveTo(mx - 30, my); g.lineTo(mx + 30, my); for (let i = -2; i <= 2; i++) { g.moveTo(mx + i * 12, my - 12); g.lineTo(mx + i * 12, my + 12); } g.lineWidth = 3; g.stroke();
  }
  // sweat / zzz extras
  if (s.sweat) { g.fillStyle = '#7fc8ff'; g.beginPath(); g.moveTo(370, 150); g.quadraticCurveTo(392, 190, 370, 200); g.quadraticCurveTo(350, 190, 370, 150); g.fill(); }
  g.restore();
}

export class Character {
  constructor(o = {}) {
    this.o = Object.assign({ hoodie: 0x58a9e6, hair: null, hairColor: 0x5a3a22, pants: null, scale: 1, faceRes: 512, cap: null, outline: .018, glasses: false }, o);
    const hood = this.o.hoodie;
    this.root = new THREE.Group();
    this.body = new THREE.Group(); this.root.add(this.body);
    const mW = toon(WHITE, { rim: .25 }), mH = toon(hood, { rim: .3 });
    const mH2 = toon(new THREE.Color(hood).multiplyScalar(.78).getHex(), { rim: .2 });
    this.mats = { mW, mH, mH2 };
    // legs
    this.hip = [];
    this.knee = [];
    for (const sx of [-1, 1]) {
      const hip = new THREE.Group(); hip.position.set(sx * .13, .95, 0); this.body.add(hip);
      const legMat = this.o.pants ? toon(this.o.pants, { rim: .2 }) : mW;
      mesh(G.cyl(.058, .052, .5, 14), legMat, 0, -.24, 0, hip);
      const knee = new THREE.Group(); knee.position.set(0, -.47, 0); hip.add(knee);
      mesh(G.cyl(.052, .048, .45, 14), mW, 0, -.22, 0, knee);
      const foot = mesh(G.sphere(.11, 20, 14), mW, 0, -.46, .05, knee); foot.scale.set(1, .72, 1.45);
      this.hip.push(hip); this.knee.push(knee);
    }
    // torso (hoodie) via lathe
    const prof = [[0, .86], [.27, .87], [.33, .93], [.355, 1.05], [.36, 1.22], [.345, 1.38], [.3, 1.48], [.2, 1.55], [.08, 1.58], [0, 1.585]].map(([r, y]) => new THREE.Vector2(r, y));
    const torso = mesh(new THREE.LatheGeometry(prof, 36), mH, 0, 0, 0, this.body); torso.scale.set(1, 1, .78);
    this.torso = torso;
    const hem = mesh(G.torus(.315, .045, 10, 36), mH2, 0, .9, 0, this.body); hem.rotation.x = Math.PI / 2; hem.scale.set(1, .78, 1);
    // pocket
    const pocket = mesh(roundBox(.34, .14, .06, .03), mH2, 0, 1.06, .245, this.body); pocket.rotation.x = -.12;
    // hood collar + back hood
    const collar = mesh(G.torus(.13, .065, 12, 30), mH2, 0, 1.56, -.02, this.body); collar.rotation.x = Math.PI / 2 - .25;
    const hoodBack = mesh(G.sphere(.2, 20, 14), mH, 0, 1.55, -.2, this.body); hoodBack.scale.set(1.2, .8, .7);
    for (const sx of [-1, 1]) { const st = mesh(G.cyl(.012, .012, .2, 6), mW, sx * .065, 1.39, .262, this.body); st.rotation.x = -.18; mesh(G.sphere(.022, 8, 6), mW, sx * .065, 1.285, .278, this.body); }
    // arms
    this.sh = []; this.el = []; this.hand = [];
    for (const sx of [-1, 1]) {
      const sh = new THREE.Group(); sh.position.set(sx * .37, 1.42, 0); this.body.add(sh);
      mesh(G.sphere(.105, 16, 12), mH, 0, 0, 0, sh);
      mesh(G.capsule(.088, .24, 14), mH, 0, -.17, 0, sh);
      const el = new THREE.Group(); el.position.set(0, -.34, 0); sh.add(el);
      mesh(G.capsule(.082, .22, 14), mH, 0, -.14, 0, el);
      const cuff = mesh(G.cyl(.075, .075, .05, 14), mH2, 0, -.3, 0, el);
      const hand = mesh(G.sphere(.105, 18, 14), mW, 0, -.38, 0, el);
      this.sh.push(sh); this.el.push(el); this.hand.push(hand);
    }
    // neck + head
    this.neck = new THREE.Group(); this.neck.position.set(0, 1.55, 0); this.body.add(this.neck);
    mesh(G.cyl(.05, .055, .2, 12), mW, 0, .07, 0, this.neck);
    this.head = new THREE.Group(); this.head.position.set(0, .62, 0); this.neck.add(this.head);
    const R = .56; this.R = R;
    mesh(G.sphere(R, 48, 32), mW, 0, 0, 0, this.head);
    // face cap with canvas texture
    this.faceCanvas = document.createElement('canvas'); this.faceCanvas.width = this.faceCanvas.height = this.o.faceRes;
    this.faceCtx = this.faceCanvas.getContext('2d');
    this.faceTex = new THREE.CanvasTexture(this.faceCanvas); this.faceTex.colorSpace = THREE.SRGBColorSpace; this.faceTex.anisotropy = 8;
    const span = 1.9;
    const faceGeo = new THREE.SphereGeometry(R * 1.004, 48, 40, Math.PI / 2 - span / 2, span, Math.PI / 2 - span / 2, span);
    const face = mesh(faceGeo, new THREE.MeshBasicMaterial({ map: this.faceTex, transparent: true, depthWrite: false }), 0, 0, 0, this.head);
    face.userData.noOutline = true; face.renderOrder = 2; this.face = face;
    if (this.o.hair) this.addHair(this.o.hair);
    if (this.o.cap) this.addCap(this.o.cap);
    if (this.o.glasses) this.addGlasses();
    addOutline(this.root, this.o.outline);
    shadows(this.root, true, false);
    face.castShadow = false;
    this.root.scale.setScalar(this.o.scale);
    this.faceKey = '';
    this.setFace({});
    this.extras = new THREE.Group(); this.head.add(this.extras);
  }
  addHair(type) {
    const mHair = toon(this.o.hairColor, { rim: .3 });
    const R = this.R;
    if (type === 'bowl') {
      const g = new THREE.SphereGeometry(R * 1.05, 40, 20, 0, Math.PI * 2, 0, 1.25);
      const h = mesh(g, mHair, 0, .015, -.02, this.head); h.rotation.x = -.12;
      // parting line
    } else if (type === 'messy') {
      const g = new THREE.SphereGeometry(R * 1.05, 40, 20, 0, Math.PI * 2, 0, 1.15);
      const h = mesh(g, mHair, 0, .02, -.03, this.head); h.rotation.x = -.18;
      for (let i = 0; i < 7; i++) { const a = i / 7 * Math.PI * 1.6 - .8; const sp = mesh(new THREE.ConeGeometry(.09, .22, 8), mHair, Math.sin(a) * .3, R * .92, Math.cos(a) * .25 - .05, this.head); sp.rotation.set(Math.cos(a) * .7 - .3, 0, -Math.sin(a) * .7); }
    } else if (type === 'bun') {
      const g = new THREE.SphereGeometry(R * 1.04, 40, 20, 0, Math.PI * 2, 0, 1.35);
      const h = mesh(g, mHair, 0, .01, -.03, this.head); h.rotation.x = -.15;
      mesh(G.sphere(.2, 16, 12), mHair, 0, R * .95, -.25, this.head);
    }
  }
  addCap(color) {
    const m = toon(color, { rim: .3 });
    const g = new THREE.SphereGeometry(this.R * 1.06, 40, 16, 0, Math.PI * 2, 0, 1.05);
    mesh(g, m, 0, .02, 0, this.head).rotation.x = -.15;
    const brim = mesh(G.cyl(.32, .32, .03, 28), m, 0, .3, .38, this.head); brim.scale.set(1, 1, .7); brim.rotation.x = .25;
  }
  addGlasses() {
    const m = toon(0x222222);
    for (const sx of [-1, 1]) { const r = mesh(G.torus(.11, .016, 8, 24), m, sx * .16, .03, this.R * .93, this.head); r.rotation.y = sx * .25; }
    mesh(G.cyl(.012, .012, .1, 6), m, 0, .04, this.R * .98, this.head).rotation.z = Math.PI / 2;
  }
  setFace(s) {
    const key = JSON.stringify(s);
    if (key === this.faceKey) return;
    this.faceKey = key;
    drawFace(this.faceCtx, s, this.o.faceRes);
    this.faceTex.needsUpdate = true;
  }
  // Pose: all angles in radians. p: {walk, walkAmt, run, armsUp, wave, sit, lean, headTilt, headTurn, headNod, bob, armL, armR, elbowL, elbowR, legL, legR, kneeL, kneeR, crouch, breathe}
  pose(p = {}, t = 0) {
    const amt = p.walkAmt ?? 0, ph = p.walk ?? 0;
    const run = p.run ?? 0;
    const sw = (.42 + .25 * run) * amt;
    // legs
    for (let i = 0; i < 2; i++) {
      const f = ph + (i ? Math.PI : 0);
      let hx = -Math.sin(f) * sw;
      let kx = amt * (.15 + .9 * (.5 + run * .3)) * Math.max(0, Math.cos(f)) * Math.max(0, Math.sin(f + .9) + .2);
      this.hip[i].rotation.set(hx, 0, (i ? -1 : 1) * -.02);
      this.knee[i].rotation.set(kx, 0, 0);
    }
    // arms
    const armSw = (.4 + .3 * run) * amt;
    for (let i = 0; i < 2; i++) {
      const sx = i ? 1 : -1;
      const f = ph + (i ? Math.PI : 0);
      this.sh[i].rotation.set(Math.sin(f) * armSw, 0, sx * .14);
      this.el[i].rotation.set(-.25 - .4 * run * amt - (amt * .15), 0, 0);
    }
    // body bob + lean
    const bob = amt * (.035 + .04 * run) * Math.cos(2 * ph);
    const breathe = Math.sin(t * 2.2) * .008 * (p.breathe ?? 1);
    this.body.position.set(0, bob + breathe, 0);
    this.body.rotation.set((p.lean ?? 0) + amt * (.05 + .12 * run), Math.sin(ph) * .06 * amt, 0);
    this.neck.rotation.set(-(p.lean ?? 0) * .5 + (p.headNod ?? 0) - amt * .05, p.headTurn ?? 0, p.headTilt ?? 0);
    // overrides
    const ov = (arr, idx, key, axis) => { if (p[key] !== undefined) arr[idx].rotation[axis] = p[key]; };
    ov(this.sh, 0, 'armL', 'x'); ov(this.sh, 1, 'armR', 'x');
    ov(this.sh, 0, 'armLz', 'z'); ov(this.sh, 1, 'armRz', 'z');
    ov(this.el, 0, 'elbowL', 'x'); ov(this.el, 1, 'elbowR', 'x');
    ov(this.hip, 0, 'legL', 'x'); ov(this.hip, 1, 'legR', 'x');
    ov(this.knee, 0, 'kneeL', 'x'); ov(this.knee, 1, 'kneeR', 'x');
    if (p.armsUp) { const a = p.armsUp; this.sh[0].rotation.z = lerp(-.14, -2.6, a); this.sh[1].rotation.z = lerp(.14, 2.6, a); this.sh[0].rotation.x *= 1 - a; this.sh[1].rotation.x *= 1 - a; this.el[0].rotation.x = this.el[1].rotation.x = -.2 * a; }
    if (p.wave) { this.sh[1].rotation.set(0, 0, 2.5); this.el[1].rotation.set(0, 0, Math.sin(t * 9) * .5 + .3); }
    if (p.sit) {
      const s = p.sit;
      for (let i = 0; i < 2; i++) { this.hip[i].rotation.x = lerp(this.hip[i].rotation.x, -1.5, s); this.knee[i].rotation.x = lerp(this.knee[i].rotation.x, 1.5, s); }
      this.body.position.y -= .02 * s;
    }
    if (p.slump) { this.body.rotation.x += .18 * p.slump; this.neck.rotation.x += .25 * p.slump; for (const s of this.sh) s.rotation.z *= 1 - .5 * p.slump; }
    if (p.crouch) { const c = p.crouch; this.body.position.y -= .25 * c; for (let i = 0; i < 2; i++) { this.hip[i].rotation.x -= .7 * c; this.knee[i].rotation.x += 1.3 * c; } }
  }
  // Standard idle blink schedule
  blinkAt(t, seed = 0) {
    const period = 3.1 + (seed % 3) * .7; const ph = (t + seed * 1.3) % period;
    return ph < .14 ? Math.sin(ph / .14 * Math.PI) : 0;
  }
}

// Footstep phase helper: distance travelled -> walk phase (stride ~0.62 per step)
export const walkPhase = (dist, stride = .62) => dist / stride * Math.PI;
