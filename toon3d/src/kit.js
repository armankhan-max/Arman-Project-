// Shared toolkit for "2D character in 3D world" shorts: toon materials, ink outlines,
// glow sprites, text cards, instanced props and the flat character cards.
import * as THREE from '/node_modules/three/build/three.module.js';
import { drawChar, handPos } from './char.js';
export { THREE };

const q = new URLSearchParams(location.search);
export const SC = parseFloat(q.get('scale') || '1');
export const W = Math.round(1080 * SC), H = Math.round(1920 * SC), FPS = 30;

export const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const seg = (t, a, b) => cl((t - a) / (b - a));
export const lerp = (a, b, k) => a + (b - a) * k;
export const EASE = {
  lin: k => k,
  io: k => k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2,
  out: k => 1 - Math.pow(1 - k, 4),
  in: k => k * k * k,
  back: k => { const c = 2.2; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
};
export const pop = (t, t0, d = 0.28) => t < t0 ? 0 : EASE.back(seg(t, t0, t0 + d));
export const bump = (t, t0, d = 0.25) => (t < t0 || t > t0 + d) ? 0 : Math.sin((t - t0) / d * Math.PI);
export function rng(seed) { let s = seed; return () => (s = (s * 16807) % 2147483647) / 2147483647; }

export const gl = document.getElementById('gl'); gl.width = W; gl.height = H;
export const out = document.getElementById('out'); out.width = W; out.height = H;
export const o2 = out.getContext('2d');
export const renderer = new THREE.WebGLRenderer({ canvas: gl, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.localClippingEnabled = true;
export const scene = new THREE.Scene();
export const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 400);

export function ctex(w, h, fn) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); fn(x, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.userData = { c, x }; return t;
}
const grad = new THREE.DataTexture(new Uint8Array([120, 120, 120, 255, 190, 190, 190, 255, 255, 255, 255, 255]), 3, 1);
grad.minFilter = grad.magFilter = THREE.NearestFilter; grad.needsUpdate = true;
export const toon = (color, o = {}) => new THREE.MeshToonMaterial({ color, gradientMap: grad, ...o });
export const INK = 0x16111f;
export const OUTM = new THREE.MeshBasicMaterial({ color: INK, side: THREE.BackSide });
export function ol(geo, mat, o = 0.03, shadow = true) {
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
export const box = (w, h, d, mat, o, sh) => ol(new THREE.BoxGeometry(w, h, d), mat, o, sh);
export const cyl = (r1, r2, h, mat, o = 0.02, n = 12) => ol(new THREE.CylinderGeometry(r1, r2, h, n), mat, o);
export function put(m, x, y, z, parent = scene) { m.position.set(x, y, z); parent.add(m); return m; }
const glowTex = ctex(128, 128, (c) => {
  const g = c.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.25, 'rgba(255,255,255,.55)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  c.fillStyle = g; c.fillRect(0, 0, 128, 128);
});
export function glow(color, size, x, y, z, parent = scene) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false }));
  s.scale.set(size, size, 1); return put(s, x, y, z, parent);
}
// flat card with painted artwork (signs, posters, labels). ppu = pixels per world unit.
export function card(w, h, fn, { ppu = 256, lit = false, alpha = false } = {}) {
  const tex = ctex(Math.round(w * ppu), Math.round(h * ppu), (c, cw, ch) => { c.scale(ppu, ppu); fn(c, w, h); });
  const mat = lit ? toon(0xffffff, { map: tex, transparent: alpha }) : new THREE.MeshBasicMaterial({ map: tex, transparent: alpha, fog: false });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat); m.userData = { tex, w, h, ppu, fn };
  m.redraw = (fn2) => { const x = tex.userData.x; x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, tex.userData.c.width, tex.userData.c.height); x.scale(ppu, ppu); fn2(x, w, h); tex.needsUpdate = true; };
  return m;
}
// text helper for cards (units are world units because of the ppu scale)
export function txt(c, s, x, y, size, color = '#16111f', { weight = 900, align = 'center', stroke = null, sw = 0.03, italic = false } = {}) {
  c.font = `${italic ? 'italic ' : ''}${weight} ${size}px Inter`; c.textAlign = align; c.textBaseline = 'middle'; c.lineJoin = 'round';
  if (stroke) { c.strokeStyle = stroke; c.lineWidth = sw; c.strokeText(s, x, y); }
  c.fillStyle = color; c.fillText(s, x, y);
}

export function makeChar(res = 512, tint = 0xffffff) {
  const cv = document.createElement('canvas'); cv.width = res; cv.height = res * 1.5;
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const geo = new THREE.PlaneGeometry(1.2, 1.8); geo.translate(0, 0.9 - 0.04, 0);
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: 0.08, side: THREE.DoubleSide, color: tint });
  const m = new THREE.Mesh(geo, mat); m.castShadow = true;
  m.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: tex, alphaTest: 0.5 });
  const ch = { mesh: m, cv, ctx: cv.getContext('2d'), tex, P: {}, billboard: true, key: '' };
  ch.draw = (P) => { const k = JSON.stringify(P); if (k === ch.key) return; ch.key = k; ch.P = P; drawChar(ch.ctx, cv.width, cv.height, P); tex.needsUpdate = true; };
  ch.handWorld = (side) => { const [px, py] = handPos(ch.P, side); m.updateMatrixWorld(); return m.localToWorld(new THREE.Vector3((px - 256) / 512 * 1.2, (768 - py) / 768 * 1.8 - 0.04, 0.01)); };
  ch.face = (cam) => { m.rotation.y = Math.atan2(cam.position.x - m.position.x, cam.position.z - m.position.z); };
  return ch;
}

// instanced prop with a matching instanced ink outline
export function instanced(geo, mats, n, o = 0.012) {
  const mesh = new THREE.InstancedMesh(geo, mats, n); mesh.castShadow = true; mesh.receiveShadow = true; mesh.frustumCulled = false;
  const og = geo.clone(); og.computeBoundingBox(); const s = new THREE.Vector3(); og.boundingBox.getSize(s);
  og.scale((s.x + 2 * o) / s.x, (s.y + 2 * o) / s.y, (s.z + 2 * o) / s.z); og.clearGroups();
  const outl = new THREE.InstancedMesh(og, OUTM, n); outl.frustumCulled = false;
  const d = new THREE.Object3D();
  const api = {
    mesh, outl, n,
    set(i, x, y, z, rx = 0, ry = 0, rz = 0, sc = 1) { d.position.set(x, y, z); d.rotation.set(rx, ry, rz); d.scale.setScalar(sc); d.updateMatrix(); mesh.setMatrixAt(i, d.matrix); outl.setMatrixAt(i, d.matrix); },
    done() { mesh.instanceMatrix.needsUpdate = true; outl.instanceMatrix.needsUpdate = true; },
    add(parent = scene) { parent.add(mesh); parent.add(outl); return api; },
  };
  return api;
}

// eased key-framed camera: keys = [time, pos, lookAt, fov, ease-into-key]
export function makeCam(keys) {
  function at(t) {
    let i = 0; while (i < keys.length - 2 && t > keys[i + 1][0]) i++;
    const a = keys[i], b = keys[i + 1], k = EASE[b[4]](seg(t, a[0], b[0]));
    const v = (p, r) => p.map((x, j) => lerp(x, r[j], k));
    const pos = v(a[1], b[1]), look = v(a[2], b[2]);
    pos[0] += Math.sin(t * 1.3) * 0.012; pos[1] += Math.sin(t * 1.7 + 1) * 0.01;
    return { pos, look, fov: lerp(a[3], b[3], k) };
  }
  function set(t, shake = 0) {
    const c = at(t); camera.position.set(...c.pos); camera.fov = c.fov; camera.updateProjectionMatrix(); camera.lookAt(...c.look);
    camera.rotation.z += Math.sin(t * 0.9) * 0.004 + shake * Math.sin(t * 95) * 0.012; camera.position.y += shake * Math.sin(t * 80) * 0.02;
    return c;
  }
  return { at, set };
}

// 1-2 word captions, heavy white type with ink stroke and a small pop
export function drawCaption(t, chunks) {
  const c = chunks.find(c => t >= c[0] && t < c[1]); if (!c) return;
  const k = 0.86 + 0.14 * EASE.out(seg(t, c[0], c[0] + 0.09));
  o2.save(); o2.translate(W / 2, H * 0.705); o2.scale(k, k);
  o2.font = `900 ${Math.round(76 * SC)}px Inter`; o2.textAlign = 'center'; o2.textBaseline = 'middle'; o2.lineJoin = 'round';
  o2.shadowColor = 'rgba(0,0,0,.5)'; o2.shadowBlur = 14 * SC; o2.shadowOffsetY = 5 * SC;
  o2.strokeStyle = '#0d0a14'; o2.lineWidth = 16 * SC; o2.strokeText(c[2], 0, 0);
  o2.shadowColor = 'transparent'; o2.fillStyle = '#fff'; o2.fillText(c[2], 0, 0); o2.restore();
}
export function vignette(strength = 0.32) {
  const g = o2.createRadialGradient(W / 2, H * 0.48, H * 0.3, W / 2, H * 0.5, H * 0.74);
  g.addColorStop(0, 'rgba(20,10,40,0)'); g.addColorStop(1, `rgba(20,10,40,${strength})`); o2.fillStyle = g; o2.fillRect(0, 0, W, H);
}
// render one frame with motion blur on fast camera moves
export function renderBlurred(t, cam, shakeFn = () => 0) {
  const a = cam.at(t), b = cam.at(Math.max(0, t - 1 / FPS));
  const speed = Math.hypot(a.pos[0] - b.pos[0], a.pos[1] - b.pos[1], a.pos[2] - b.pos[2]) + Math.hypot(a.look[0] - b.look[0], a.look[1] - b.look[1], a.look[2] - b.look[2]);
  const n = speed > 0.6 ? 10 : speed > 0.14 ? 5 : 1;
  for (let i = 0; i < n; i++) {
    cam.set(t - (n > 1 ? (i / n) * 0.6 / FPS : 0), shakeFn(t));
    renderer.shadowMap.autoUpdate = i === 0; if (i === 0) renderer.shadowMap.needsUpdate = true;
    renderer.render(scene, camera); o2.globalAlpha = 1 / (i + 1); o2.drawImage(gl, 0, 0);
  }
  o2.globalAlpha = 1; cam.set(t, shakeFn(t));
}
