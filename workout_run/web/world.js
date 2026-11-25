// 3D worlds for the three levels: sunny city, underground tunnel, lava city.
// Everything is procedural (canvas textures + merged/instanced geometry), seeded, deterministic.
import * as THREE from 'three';
import { mergeGeometries } from './lib/BufferGeometryUtils.js';

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const col = (h) => new THREE.Color(h);
const LAMBERT = new URLSearchParams(location.search).get('lam') === '1';
function STD(p) {
  if (!LAMBERT) return new THREE.MeshStandardMaterial(p);
  const q = { ...p }; delete q.roughness; delete q.metalness;
  return new THREE.MeshLambertMaterial(q);
}

function canvasTex(w, h, draw, repeat = true) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d');
  draw(g, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; }
  t.anisotropy = 8;
  t.generateMipmaps = true;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  return t;
}

// ------------------------------------------------------------------ textures
function facadeTex(style) {
  // one floor x one window bay; border pixels are plain wall (white = tinted by vertex colour)
  return canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
    // subtle wall noise
    const r = rng(5);
    for (let i = 0; i < 900; i++) {
      g.fillStyle = `rgba(0,0,0,${r() * 0.035})`;
      g.fillRect(r() * w, r() * h, 2 + r() * 6, 2 + r() * 4);
    }
    // floor line
    g.fillStyle = 'rgba(0,0,0,0.10)'; g.fillRect(0, h - 14, w, 6);
    const wx = 62, wy = 52, ww = 132, wh = 150;
    // frame + sill
    g.fillStyle = '#f4f1ea'; g.fillRect(wx - 12, wy - 12, ww + 24, wh + 24);
    g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(wx - 16, wy + wh + 10, ww + 32, 10);
    // glass
    const gr = g.createLinearGradient(wx, wy, wx + ww, wy + wh);
    if (style === 'night') { gr.addColorStop(0, '#3c2f63'); gr.addColorStop(1, '#1c1638'); }
    else { gr.addColorStop(0, '#9fd3f5'); gr.addColorStop(0.55, '#4f86b8'); gr.addColorStop(1, '#2d4f78'); }
    g.fillStyle = gr; g.fillRect(wx, wy, ww, wh);
    // reflection streak
    g.fillStyle = 'rgba(255,255,255,0.28)';
    g.beginPath(); g.moveTo(wx + 20, wy + wh); g.lineTo(wx + 70, wy); g.lineTo(wx + 98, wy); g.lineTo(wx + 48, wy + wh); g.fill();
    // mullions
    g.fillStyle = '#f4f1ea'; g.fillRect(wx + ww / 2 - 5, wy, 10, wh); g.fillRect(wx, wy + 60, ww, 9);
  });
}

function windowGlowTex() {
  // emissive map for evening windows: some bays lit warm
  return canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = '#000'; g.fillRect(0, 0, w, h);
    const gr = g.createRadialGradient(128, 127, 10, 128, 127, 110);
    gr.addColorStop(0, '#ffd79a'); gr.addColorStop(1, '#a8561d');
    g.fillStyle = gr; g.fillRect(62, 52, 132, 150);
    g.fillStyle = '#000'; g.fillRect(62 + 66 - 5, 52, 10, 150); g.fillRect(62, 112, 132, 9);
  });
}

function ballastTex(base, rail) {
  return canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    const r = rng(9);
    for (let i = 0; i < 2600; i++) {
      const l = r();
      g.fillStyle = l < 0.5 ? 'rgba(0,0,0,0.13)' : 'rgba(255,255,255,0.10)';
      const s = 2 + r() * 5;
      g.beginPath(); g.ellipse(r() * w, r() * h, s, s * 0.7, r() * 3, 0, 7); g.fill();
    }
  });
}

function stripeTex(c1, c2, n = 5) {
  return canvasTex(512, 128, (g, w, h) => {
    g.fillStyle = c1; g.fillRect(0, 0, w, h);
    g.fillStyle = c2;
    const sw = w / n;
    for (let i = -2; i < n + 2; i++) {
      g.beginPath();
      g.moveTo(i * sw, h); g.lineTo(i * sw + sw / 2, h); g.lineTo(i * sw + sw / 2 + h * 0.8, 0); g.lineTo(i * sw + h * 0.8, 0);
      g.fill();
    }
    g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 8; g.strokeRect(4, 4, w - 8, h - 8);
  }, false);
}

function warnSignTex() {
  return canvasTex(256, 256, (g, w, h) => {
    g.clearRect(0, 0, w, h);
    g.fillStyle = '#ffd21f'; g.strokeStyle = '#111'; g.lineWidth = 16; g.lineJoin = 'round';
    g.beginPath(); g.moveTo(128, 22); g.lineTo(236, 222); g.lineTo(20, 222); g.closePath(); g.fill(); g.stroke();
    // downward chevrons = "get low"
    g.strokeStyle = '#111'; g.lineWidth = 18; g.lineCap = 'round';
    for (const y of [104, 150]) { g.beginPath(); g.moveTo(92, y); g.lineTo(128, y + 30); g.lineTo(164, y); g.stroke(); }
  }, false);
}

function coinFaceTex() {
  return canvasTex(256, 256, (g, w, h) => {
    const gr = g.createRadialGradient(100, 90, 10, 128, 128, 140);
    gr.addColorStop(0, '#fff6b0'); gr.addColorStop(0.5, '#ffc928'); gr.addColorStop(1, '#d68a00');
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.strokeStyle = '#b86e00'; g.lineWidth = 14; g.beginPath(); g.arc(128, 128, 100, 0, 7); g.stroke();
    // star
    g.fillStyle = '#ffe76a'; g.strokeStyle = '#c07400'; g.lineWidth = 8;
    g.beginPath();
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? 30 : 70;
      g.lineTo(128 + Math.cos(a) * rr, 132 + Math.sin(a) * rr);
    }
    g.closePath(); g.fill(); g.stroke();
  }, false);
}

const TRAIN_SCHEMES = [
  { body: '#f2f2ee', stripe: '#e2312d', stripe2: '#ffc21a', roof: '#9aa3ad' },
  { body: '#2f7fd8', stripe: '#ffffff', stripe2: '#ffd23a', roof: '#86909c' },
  { body: '#ffcf2e', stripe: '#1f2a44', stripe2: '#e2312d', roof: '#7d8792' },
  { body: '#2bb673', stripe: '#ffffff', stripe2: '#145c3a', roof: '#8a949f' },
];

function trainSideTex(sc) {
  return canvasTex(1024, 256, (g, w, h) => {
    g.fillStyle = sc.body; g.fillRect(0, 0, w, h);
    g.fillStyle = sc.stripe; g.fillRect(0, h * 0.70, w, h * 0.10);
    g.fillStyle = sc.stripe2; g.fillRect(0, h * 0.80, w, h * 0.04);
    // windows
    for (let i = 0; i < 6; i++) {
      const x = 40 + i * 166;
      if (i === 2) continue;
      const gr = g.createLinearGradient(0, 40, 0, 140);
      gr.addColorStop(0, '#2c3e57'); gr.addColorStop(1, '#14202f');
      g.fillStyle = '#1b2432'; g.fillRect(x - 6, 34, 128, 112);
      g.fillStyle = gr; g.fillRect(x, 40, 116, 100);
      g.fillStyle = 'rgba(255,255,255,0.22)'; g.fillRect(x + 10, 46, 20, 88);
    }
    // doors
    for (const x of [372, 900]) {
      g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(x - 3, 26, 92, h - 40);
      g.fillStyle = sc.body; g.fillRect(x, 30, 86, h - 48);
      g.fillStyle = '#1b2432'; g.fillRect(x + 10, 44, 28, 96); g.fillRect(x + 48, 44, 28, 96);
    }
    g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, h - 10, w, 10); g.fillRect(0, 0, w, 6);
  }, false);
}

function trainFrontTex(sc) {
  return canvasTex(256, 320, (g, w, h) => {
    g.fillStyle = sc.body; g.fillRect(0, 0, w, h);
    g.fillStyle = sc.stripe; g.fillRect(0, h * 0.70, w, h * 0.1);
    g.fillStyle = sc.stripe2; g.fillRect(0, h * 0.8, w, h * 0.04);
    // windscreen
    g.fillStyle = '#121a26';
    g.beginPath(); g.roundRect(22, 34, w - 44, 120, 18); g.fill();
    g.fillStyle = 'rgba(160,210,255,0.35)';
    g.beginPath(); g.moveTo(40, 150); g.lineTo(90, 40); g.lineTo(120, 40); g.lineTo(70, 150); g.fill();
    // headlights
    for (const x of [52, w - 52]) {
      const gr = g.createRadialGradient(x, 196, 2, x, 196, 26);
      gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.5, '#fff3b0'); gr.addColorStop(1, 'rgba(255,220,120,0)');
      g.fillStyle = gr; g.fillRect(x - 30, 166, 60, 60);
    }
    g.fillStyle = '#222'; g.fillRect(96, 172, 64, 40);
    g.fillStyle = 'rgba(0,0,0,0.3)'; g.fillRect(0, h - 12, w, 12);
  }, false);
}

function concreteTex(c1, seam) {
  return canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = c1; g.fillRect(0, 0, w, h);
    const r = rng(21);
    for (let i = 0; i < 1600; i++) {
      g.fillStyle = `rgba(${r() < 0.5 ? '0,0,0' : '255,255,255'},${r() * 0.05})`;
      g.fillRect(r() * w, r() * h, 3 + r() * 30, 2 + r() * 10);
    }
    g.strokeStyle = seam; g.lineWidth = 6;
    g.strokeRect(3, 3, w - 6, h - 6);
    g.beginPath(); g.moveTo(w / 2, 0); g.lineTo(w / 2, h); g.stroke();
  });
}

function muralTex(seed) {
  // abstract colourful street-art shapes (no letters)
  return canvasTex(1024, 384, (g, w, h) => {
    const r = rng(seed);
    const pal = ['#ff3d7f', '#ffcf2e', '#2ad1ff', '#7b5cff', '#2bd67b', '#ff8a1f', '#ffffff'];
    g.fillStyle = '#2b2f3a'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 9; i++) {
      g.fillStyle = pal[Math.floor(r() * pal.length)];
      g.beginPath();
      const cx = r() * w, cy = h * 0.2 + r() * h * 0.6, rad = 60 + r() * 120;
      for (let k = 0; k < 9; k++) {
        const a = k / 9 * Math.PI * 2, rr = rad * (0.6 + r() * 0.5);
        g.lineTo(cx + Math.cos(a) * rr * 1.4, cy + Math.sin(a) * rr * 0.7);
      }
      g.closePath(); g.fill();
      g.strokeStyle = '#111'; g.lineWidth = 10; g.stroke();
    }
    for (let i = 0; i < 14; i++) {
      g.strokeStyle = pal[Math.floor(r() * pal.length)]; g.lineWidth = 14; g.lineCap = 'round';
      g.beginPath();
      let x = r() * w, y = r() * h;
      g.moveTo(x, y);
      for (let k = 0; k < 4; k++) { x += (r() - 0.5) * 200; y += (r() - 0.5) * 120; g.lineTo(x, y); }
      g.stroke();
    }
    for (let i = 0; i < 40; i++) {
      g.fillStyle = pal[Math.floor(r() * pal.length)];
      g.beginPath(); g.arc(r() * w, r() * h, 4 + r() * 10, 0, 7); g.fill();
    }
    g.strokeStyle = '#11151c'; g.lineWidth = 18; g.strokeRect(9, 9, w - 18, h - 18);
  }, false);
}

function lavaTex() {
  return canvasTex(512, 512, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, w, h);
    gr.addColorStop(0, '#ff6a00'); gr.addColorStop(0.5, '#ffb000'); gr.addColorStop(1, '#ff4a00');
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
    const r = rng(33);
    // hot spots
    for (let i = 0; i < 60; i++) {
      const x = r() * w, y = r() * h, rad = 20 + r() * 60;
      const rg = g.createRadialGradient(x, y, 0, x, y, rad);
      rg.addColorStop(0, 'rgba(255,245,170,0.9)'); rg.addColorStop(1, 'rgba(255,200,0,0)');
      for (const ox of [-w, 0, w]) for (const oy of [-h, 0, h]) { g.save(); g.translate(ox, oy); g.fillStyle = rg; g.fillRect(x - rad, y - rad, rad * 2, rad * 2); g.restore(); }
    }
    // dark crust plates
    for (let i = 0; i < 46; i++) {
      const cx = r() * w, cy = r() * h, rad = 18 + r() * 42;
      const pts = [];
      for (let k = 0; k < 8; k++) { const a = k / 8 * Math.PI * 2; const rr = rad * (0.6 + r() * 0.5); pts.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
      for (const ox of [-w, 0, w]) for (const oy of [-h, 0, h]) {
        g.fillStyle = 'rgba(70,14,8,0.92)';
        g.beginPath(); pts.forEach((p) => g.lineTo(cx + ox + p[0], cy + oy + p[1])); g.closePath(); g.fill();
        g.strokeStyle = 'rgba(255,120,20,0.8)'; g.lineWidth = 3; g.stroke();
      }
    }
  });
}

function checkerTex() {
  return canvasTex(512, 128, (g, w, h) => {
    const n = 16, m = 4, cw = w / n, ch = h / m;
    for (let i = 0; i < n; i++) for (let j = 0; j < m; j++) {
      g.fillStyle = (i + j) % 2 ? '#111' : '#fff'; g.fillRect(i * cw, j * ch, cw, ch);
    }
  }, false);
}

export function spriteTex() {
  return canvasTex(64, 64, (g) => {
    const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.3, 'rgba(255,255,255,0.8)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  }, false);
}

// ------------------------------------------------------------------ geometry helpers
function box(w, h, d, x, y, z, color, uvMod = null) {
  const g = new THREE.BoxGeometry(w, h, d);
  if (uvMod) {
    // scale uvs per face so the texture repeats at a fixed physical size; top/bottom -> plain wall
    const uv = g.attributes.uv;
    const dims = [[d, h], [d, h], [0, 0], [0, 0], [w, h], [w, h]];
    for (let f = 0; f < 6; f++) for (let k = 0; k < 4; k++) {
      const i = f * 4 + k;
      const [du, dv] = dims[f];
      uv.setXY(i, du ? uv.getX(i) * du / uvMod[0] : 0.01, dv ? uv.getY(i) * dv / uvMod[1] : 0.01);
    }
  }
  g.translate(x, y, z);
  paint(g, color);
  return g;
}

function paint(g, color) {
  const c = col(color);
  const n = g.attributes.position.count;
  const arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { arr[i * 3] = c.r; arr[i * 3 + 1] = c.g; arr[i * 3 + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(arr, 3));
  if (!g.attributes.uv) g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(n * 2), 2));
  return g;
}

function shade(hex, k) {
  const c = col(hex);
  c.multiplyScalar(k);
  return '#' + c.getHexString();
}

// chunked merge so frustum culling still works
class Chunker {
  constructor(size = 90) { this.size = size; this.bins = new Map(); }
  add(key, geo, z) {
    const b = Math.floor(-z / this.size);
    const k = key + '|' + b;
    if (!this.bins.has(k)) this.bins.set(k, { key, list: [] });
    const g = geo.index ? geo.toNonIndexed() : geo;
    this.bins.get(k).list.push(g);
  }
  build(group, mats) {
    for (const { key, list } of this.bins.values()) {
      const m = mergeGeometries(list, false);
      m.computeBoundingSphere();
      const mesh = new THREE.Mesh(m, mats[key]);
      group.add(mesh);
    }
  }
}

function instanced(geo, mat, mats4) {
  const m = new THREE.InstancedMesh(geo, mat, mats4.length);
  mats4.forEach((M, i) => m.setMatrixAt(i, M));
  m.instanceMatrix.needsUpdate = true;
  m.computeBoundingSphere();
  return m;
}
const M4 = (x, y, z, ry = 0, sx = 1, sy = 1, sz = 1, rx = 0, rz = 0) => {
  const m = new THREE.Matrix4();
  m.compose(new THREE.Vector3(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), new THREE.Vector3(sx, sy, sz));
  return m;
};

// ------------------------------------------------------------------ sky
function skyMesh(top, mid, bottom, sunDir, sunCol, clouds, stars) {
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, depthTest: true, fog: false,
    uniforms: {
      top: { value: col(top) }, mid: { value: col(mid) }, bottom: { value: col(bottom) },
      sunDir: { value: new THREE.Vector3(...sunDir).normalize() }, sunCol: { value: col(sunCol) },
      clouds: { value: clouds }, stars: { value: stars }, time: { value: 0 },
    },
    vertexShader: `varying vec3 vDir; void main(){ vDir = normalize(position); vec4 p = modelViewMatrix*vec4(position,1.0); gl_Position = projectionMatrix*p; gl_Position.z = gl_Position.w; }`,
    fragmentShader: `
      uniform vec3 top, mid, bottom, sunDir, sunCol; uniform float clouds, stars, time; varying vec3 vDir;
      float h(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
      float n(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
        return mix(mix(h(i),h(i+vec2(1,0)),f.x), mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x), f.y); }
      float fbm(vec2 p){ float a=0.5, s=0.0; for(int i=0;i<5;i++){ s+=a*n(p); p*=2.03; a*=0.5; } return s; }
      void main(){
        vec3 d = normalize(vDir);
        float y = d.y;
        vec3 c = y > 0.0 ? mix(mid, top, pow(clamp(y*1.6,0.0,1.0), 0.7)) : mix(mid, bottom, clamp(-y*6.0,0.0,1.0));
        float sd = max(dot(d, sunDir), 0.0);
        c += sunCol * (pow(sd, 900.0) * 3.0 + pow(sd, 12.0) * 0.35 + pow(sd, 3.0) * 0.12);
        if (clouds > 0.0 && y > 0.0) {
          vec2 uv = d.xz / (y + 0.12) * 1.4 + vec2(time*0.01, 0.0);
          float cl = smoothstep(0.52, 0.78, fbm(uv));
          c = mix(c, vec3(1.0, 0.99, 0.97) * (0.9 + 0.1*y), cl * clouds * smoothstep(0.0, 0.25, y));
        }
        if (stars > 0.0 && y > 0.05) {
          vec2 g = d.xz / (y + 0.3) * 120.0;
          float s = step(0.996, h(floor(g))) * smoothstep(0.1, 0.6, y);
          c += vec3(s) * stars;
        }
        gl_FragColor = vec4(c, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const m = new THREE.Mesh(new THREE.SphereGeometry(500, 48, 24), mat);
  m.renderOrder = 10; // drawn after opaque geometry so only uncovered sky pixels are shaded
  m.frustumCulled = false;
  return m;
}

// ------------------------------------------------------------------ world builder
export const THEMES = [
  { // 0 city morning
    fog: '#cfe6f7', fogNear: 60, fogFar: 300,
    sky: ['#3d9df0', '#d6efff', '#b9d4e8', [-0.35, 0.32, -1], '#fff1c9', 0.85, 0],
    hemi: ['#dff0ff', '#9b8670', 1.35], sun: ['#fff0d6', 2.4, [-6, 9, 4]],
    ground: '#b9a99a', ballast: '#9c8577', bed: '#c45a4a', sleeper: '#6b4b39', rail: '#d7dde3',
    walk: '#d9d4cc', palette: ['#c8553d', '#e9d8b5', '#5aa3a0', '#e0b04a', '#e88a6a', '#9cc3e0', '#b7c97a', '#d07a9b'],
    windows: 'day', trees: 'round', lamps: true,
  },
  { // 1 underground tunnel
    fog: '#7d8ea6', fogNear: 30, fogFar: 230,
    sky: ['#2a3140', '#3b4456', '#222833', [0, 1, 0], '#000000', 0, 0],
    hemi: ['#eef4ff', '#4b5260', 1.7], sun: ['#ffffff', 1.0, [2, 8, 6]],
    ground: '#5d6472', ballast: '#6f7584', bed: '#5a6070', sleeper: '#4a4a52', rail: '#e5ebf2',
    walk: '#b9bec7', tunnel: true,
  },
  { // 2 sky rail above the city
    fog: '#cde8fb', fogNear: 80, fogFar: 420,
    sky: ['#2f8ff0', '#dff2ff', '#cfe6f5', [0.4, 0.45, -1], '#fff4d6', 1.0, 0],
    hemi: ['#e8f5ff', '#8fa3b5', 1.4], sun: ['#fff2dc', 2.3, [7, 10, 5]],
    ground: '#9aa7b3', ballast: '#8d8f96', bed: '#7f8792', sleeper: '#59524e', rail: '#e2e8ee',
    walk: '#c9ced6', palette: ['#f4d7b0', '#e8a87c', '#9fc7e8', '#f2e6c9', '#c8d9a5', '#e6b8c9', '#b8c6d9', '#ffd98a'],
    windows: 'day',
  },
  { // 3 jungle temple
    fog: '#a9c4a0', fogNear: 40, fogFar: 260,
    sky: ['#4f9fb8', '#e9f0d0', '#7f9c78', [-0.3, 0.35, -1], '#fff0b8', 0.6, 0],
    hemi: ['#f4ffe6', '#46603c', 1.45], sun: ['#ffe6b0', 2.2, [-5, 9, 3]],
    stone: '#b9a98a', stoneDark: '#7d6f58', moss: '#5f8f45',
  },
  { // 4 lava city at dusk
    fog: '#b2589a', fogNear: 50, fogFar: 280,
    sky: ['#3a1a7a', '#ff7aa8', '#ff9a52', [0.25, 0.12, -1], '#ffcf7a', 0.35, 0.5],
    hemi: ['#ffb8e0', '#ff5a1f', 1.25], sun: ['#ffd2a6', 1.9, [5, 6, -4]],
    ground: '#3a1a1a', ballast: '#3b2a2e', bed: '#2e2226', sleeper: '#1e1416', rail: '#f2d6c4',
    walk: '#6b4a52', palette: ['#f6b4c8', '#ffd3a1', '#c9a7f0', '#ff9e8a', '#ffe9b0', '#9fd8e8', '#f7c8e0'],
    windows: 'night', trees: 'palm', lamps: true, lava: true,
  },
];

const TRAIN_MATS = {};
function trainMats() {
  if (TRAIN_MATS.side) return TRAIN_MATS;
  TRAIN_MATS.side = TRAIN_SCHEMES.map((sc) => STD({ map: trainSideTex(sc), roughness: 0.45, metalness: 0.15 }));
  TRAIN_MATS.front = TRAIN_SCHEMES.map((sc) => STD({ map: trainFrontTex(sc), roughness: 0.4, metalness: 0.15 }));
  TRAIN_MATS.roof = TRAIN_SCHEMES.map((sc) => STD({ color: col(sc.roof), roughness: 0.6, metalness: 0.3 }));
  return TRAIN_MATS;
}

function sawTex() {
  return canvasTex(256, 256, (g, w, h) => {
    g.clearRect(0, 0, w, h);
    g.translate(128, 128);
    g.fillStyle = '#d9dde3';
    g.beginPath();
    for (let i = 0; i < 48; i++) {
      const a = i / 48 * Math.PI * 2, rr = i % 2 ? 104 : 126;
      g.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
    }
    g.closePath(); g.fill();
    const gr = g.createRadialGradient(-20, -20, 4, 0, 0, 104);
    gr.addColorStop(0, '#ffffff'); gr.addColorStop(1, '#8b939e');
    g.fillStyle = gr; g.beginPath(); g.arc(0, 0, 100, 0, 7); g.fill();
    g.fillStyle = '#e2312d'; g.beginPath(); g.arc(0, 0, 26, 0, 7); g.fill();
    g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 6;
    for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; g.beginPath(); g.arc(Math.cos(a) * 62, Math.sin(a) * 62, 14, 0, 7); g.stroke(); }
  }, false);
}

function flameTex() {
  return canvasTex(128, 256, (g, w, h) => {
    const gr = g.createRadialGradient(64, 190, 4, 64, 160, 120);
    gr.addColorStop(0, 'rgba(255,255,220,1)'); gr.addColorStop(0.25, 'rgba(255,210,60,0.95)');
    gr.addColorStop(0.6, 'rgba(255,90,20,0.7)'); gr.addColorStop(1, 'rgba(255,40,0,0)');
    g.fillStyle = gr;
    g.beginPath(); g.moveTo(64, 0); g.bezierCurveTo(130, 120, 120, 250, 64, 250); g.bezierCurveTo(8, 250, -2, 120, 64, 0); g.fill();
  }, false);
}

function carvedTex() {
  return canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = '#b9a98a'; g.fillRect(0, 0, w, h);
    const r = rng(77);
    for (let i = 0; i < 700; i++) { g.fillStyle = `rgba(${r() < 0.5 ? '0,0,0' : '255,255,255'},${r() * 0.08})`; g.fillRect(r() * w, r() * h, 2 + r() * 14, 2 + r() * 8); }
    g.strokeStyle = 'rgba(60,45,30,0.55)'; g.lineWidth = 5;
    g.strokeRect(6, 6, w - 12, h - 12);
    // glyph-free geometric carving: concentric diamonds and spirals
    g.beginPath(); g.moveTo(128, 30); g.lineTo(226, 128); g.lineTo(128, 226); g.lineTo(30, 128); g.closePath(); g.stroke();
    g.beginPath(); g.moveTo(128, 70); g.lineTo(186, 128); g.lineTo(128, 186); g.lineTo(70, 128); g.closePath(); g.stroke();
    g.beginPath(); for (let a = 0; a < 12; a += 0.2) g.lineTo(128 + Math.cos(a) * a * 3.2, 128 + Math.sin(a) * a * 3.2); g.stroke();
    // moss
    for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(80,130,50,${0.25 + r() * 0.3})`; g.beginPath(); g.arc(r() * w, h - r() * 60, 4 + r() * 14, 0, 7); g.fill(); }
  });
}

function hazardTex() { return stripeTex('#ffd21f', '#1b1b1b', 6); }

// shared: ballast beds, sleepers and rails for the three lanes
function buildTracks(world, ch, th, LX, S0, S1, mats, yBase = 0) {
  const LEN = S1 - S0, ZC = -(S0 + S1) / 2;
  const gTex = ballastTex(th.ballast);
  gTex.repeat.set(1, LEN / 4);
  const bedMat = STD({ map: gTex, color: col(th.bed), roughness: 0.95 });
  for (const lx of LX) {
    const bed = new THREE.Mesh(new THREE.BoxGeometry(2.7, 0.16, LEN), bedMat);
    bed.position.set(lx, yBase + 0.02, ZC);
    world.add(bed);
  }
  const sl = [];
  for (const lx of LX) for (let s = S0; s < S1; s += 0.72) sl.push(M4(lx, yBase + 0.13, -s));
  world.add(instanced(paint(new THREE.BoxGeometry(2.25, 0.1, 0.32), th.sleeper), mats.flat, sl));
  for (const lx of LX) for (const o of [-0.72, 0.72]) {
    ch.add('shiny', box(0.09, 0.15, LEN, lx + o, yBase + 0.25, ZC, th.rail), ZC);
    ch.add('flat', box(0.2, 0.04, LEN, lx + o, yBase + 0.19, ZC, '#5b5552'), ZC);
  }
}

function buildingRow(ch, th, r, sd, xNear, S0, S1, opt = {}) {
  let s = S0;
  const base = opt.base || 0;
  while (s < S1) {
    const w = (opt.wMin || 7) + r() * (opt.wVar || 9), d = (opt.dMin || 8) + r() * (opt.dVar || 8);
    const floors = (opt.fMin || 2) + Math.floor(r() * (opt.fVar || 8));
    const hgt = floors * 3.4 + 1.2;
    const x = sd * (xNear + d / 2 + r() * 1.2);
    const z = -(s + w / 2);
    const c = th.palette[Math.floor(r() * th.palette.length)];
    ch.add('facade', box(d, hgt, w - 0.3, x, base + hgt / 2, z, c, [3.4, 3.4]), z);
    if (!opt.simple) {
      ch.add('flat', box(d + 0.3, 3.0, w - 0.1, x, base + 1.5, z, shade(c, 0.62)), z);
      const aw = ['#e2312d', '#2f7fd8', '#2bb673', '#ffcf2e', '#ff7aa8'][Math.floor(r() * 5)];
      const ag = paint(new THREE.BoxGeometry(1.1, 0.12, w * 0.8), aw);
      ag.rotateZ(sd * 0.32);
      ag.translate(x - sd * (d / 2 + 0.5), base + 3.15, z);
      ch.add('flat', ag, z);
    }
    ch.add('flat', box(d + 0.7, 0.45, w + 0.2, x, base + hgt + 0.2, z, shade(c, 0.78)), z);
    ch.add('flat', box(d * 0.6, 0.9 + r() * 1.5, w * 0.5, x + sd * 1.0, base + hgt + 0.9, z, shade(c, 0.55)), z);
    if (r() < 0.3) ch.add('flat', box(1.6, 2.2, 1.6, x, base + hgt + 1.6, z - w * 0.2, '#8b6a52'), z);
    s += w + (opt.gap ? r() * opt.gap : 0);
  }
}

function facadeMaterial(th) {
  const m = STD({ map: facadeTex(th.windows), vertexColors: true, roughness: 0.8 });
  if (th.windows === 'night') { m.emissiveMap = windowGlowTex(); m.emissive = col('#ffffff'); m.emissiveIntensity = 0.9; }
  return m;
}

function makeTrain(o, x, yBase, mats, flat, anims) {
  const T = trainMats();
  const g = new THREE.Group();
  const sc = o.scheme % 4;
  const n = o.cars;
  const carLen = (o.len || n * CARLEN) / n;
  const bodyL = carLen - 0.6;
  for (let k = 0; k < n; k++) {
    const zc = -(k * carLen + carLen / 2);
    const car = new THREE.Mesh(new THREE.BoxGeometry(2.45, 3.0, bodyL), [T.side[sc], T.side[sc], T.roof[sc], T.roof[sc], T.front[sc], T.front[sc]]);
    car.position.set(0, 1.95, zc);
    g.add(car);
    const u = new THREE.Mesh(paint(new THREE.BoxGeometry(2.1, 0.55, bodyL - 0.8), '#26282d'), flat); u.position.set(0, 0.55, zc); g.add(u);
    const rf = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.28, bodyL - 0.6), T.roof[sc]); rf.position.set(0, 3.55, zc); g.add(rf);
    if (k > 0) { const c = new THREE.Mesh(paint(new THREE.BoxGeometry(1.6, 2.4, 0.8), '#30333a'), flat); c.position.set(0, 1.9, -(k * carLen - 0.1)); g.add(c); }
  }
  if (o.tall) g.scale.y = ROOF_TALL / ROOF;
  g.position.set(x, yBase, -o.s);
  g.userData = o;
  if (o.speed > 0) {
    // headlight glow on oncoming trains
    const lg = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 1.6), new THREE.MeshBasicMaterial({ map: SPR(), color: col('#fff4c0'), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
    lg.position.set(0, 1.35, 0.25);
    g.add(lg);
  }
  return g;
}
const CARLEN = 14.6, ROOF = 3.69, ROOF_TALL = 5.25;
let _spr = null;
const SPR = () => (_spr ||= spriteTex());

// dangerous lane barriers ------------------------------------------------------------
function laneObstacles(world, level, LX, yBase, flat, glow, anims) {
  const lowTex = stripeTex('#ffffff', '#e2312d'), highTex = hazardTex();
  const lowMat = STD({ map: lowTex, roughness: 0.5 });
  const highMat = STD({ map: highTex, roughness: 0.5 });
  const post = paint(new THREE.BoxGeometry(0.14, 1.1, 0.14), '#3a3d44');
  const tallPost = paint(new THREE.BoxGeometry(0.16, 2.9, 0.16), '#3a3d44');
  const spikeGeo = paint(new THREE.ConeGeometry(0.09, 0.42, 6), '#cfd5dc');
  const sawMat = new THREE.MeshStandardMaterial({ map: sawTex(), transparent: true, alphaTest: 0.4, side: THREE.DoubleSide, metalness: 0.6, roughness: 0.3 });
  const signMat = new THREE.MeshBasicMaterial({ map: warnSignTex(), transparent: true, alphaTest: 0.3 });
  const elecMat = new THREE.MeshBasicMaterial({ color: col('#7ff6ff'), toneMapped: false });
  const redMat = new THREE.MeshBasicMaterial({ color: col('#ff2a2a'), toneMapped: false });
  const ambMat = new THREE.MeshBasicMaterial({ color: col('#ffb21f'), toneMapped: false });
  for (const o of level.obstacles) {
    if (o.type === 'train' || o.type === 'bridge') continue;
    const x = LX[o.lane], z = -o.s;
    const g = new THREE.Group();
    g.position.set(x, yBase, z);
    if (o.type.startsWith('low')) {
      for (const sd of [-1, 1]) { const p = new THREE.Mesh(post, flat); p.position.set(sd * 1.12, 0.55, 0); g.add(p); }
      if (o.type === 'low_elec') {
        for (const yy of [0.45, 0.75, 1.05]) {
          const wire = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.05, 0.05), elecMat); wire.position.set(0, yy, 0); g.add(wire);
          anims.push({ obj: wire, kind: 'elec', seed: yy * 10 + o.s });
        }
        const sp = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 1.6), new THREE.MeshBasicMaterial({ map: SPR(), color: col('#55e8ff'), transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
        sp.position.set(0, 0.75, 0.1); g.add(sp);
        anims.push({ obj: sp, kind: 'elecglow', seed: o.s });
        for (const sd of [-1, 1]) { const b = new THREE.Mesh(paint(new THREE.BoxGeometry(0.34, 0.34, 0.34), '#2a2d33'), flat); b.position.set(sd * 1.12, 1.15, 0); g.add(b); }
      } else {
        const bd = new THREE.Mesh(new THREE.BoxGeometry(2.3, 0.5, 0.12), lowMat); bd.position.set(0, 0.78, 0); g.add(bd);
        if (o.type === 'low_spike') {
          for (let i = 0; i < 9; i++) { const sp = new THREE.Mesh(spikeGeo, flat); sp.position.set(-1.0 + i * 0.25, 1.24, 0); g.add(sp); }
        }
        for (const sd of [-1, 1]) {
          const l = new THREE.Mesh(new THREE.SphereGeometry(0.11, 10, 8), o.type === 'low_spike' ? redMat : ambMat);
          l.position.set(sd * 1.12, 1.2, 0); g.add(l);
          anims.push({ obj: l, kind: 'blink', seed: sd + o.s });
        }
      }
    } else {
      for (const sd of [-1, 1]) { const p = new THREE.Mesh(tallPost, flat); p.position.set(sd * 1.3, 1.45, 0); g.add(p); }
      if (o.type === 'high_saw') {
        const beam = new THREE.Mesh(paint(new THREE.BoxGeometry(2.8, 0.32, 0.32), '#2a2d33'), flat); beam.position.set(0, 2.72, 0); g.add(beam);
        const saw = new THREE.Mesh(new THREE.CircleGeometry(0.95, 40), sawMat);
        saw.position.set(0, 2.08, 0.12); g.add(saw);
        anims.push({ obj: saw, kind: 'saw', seed: o.s });
        const arm = new THREE.Mesh(paint(new THREE.BoxGeometry(0.14, 0.7, 0.14), '#2a2d33'), flat); arm.position.set(0, 2.45, 0.05); g.add(arm);
        for (const sd of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.12, 10, 8), redMat); l.position.set(sd * 1.3, 2.95, 0); g.add(l); anims.push({ obj: l, kind: 'blink', seed: sd * 3 + o.s }); }
      } else {
        const bd = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.72, 0.14), highMat); bd.position.set(0, 1.82, 0); g.add(bd);
        const sg = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.0), signMat); sg.position.set(0, 2.68, 0.06); g.add(sg);
        for (const sd of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.11, 10, 8), ambMat); l.position.set(sd * 1.3, 2.95, 0); g.add(l); anims.push({ obj: l, kind: 'blink', seed: sd * 5 + o.s }); }
      }
    }
    world.add(g);
  }
}

function coinMeshFor(n) {
  const faceMat = STD({ map: coinFaceTex(), metalness: 0.35, roughness: 0.3, emissive: col('#ffb000'), emissiveIntensity: 0.3 });
  const edgeMat = STD({ color: col('#e8a300'), metalness: 0.6, roughness: 0.3, emissive: col('#8a5a00'), emissiveIntensity: 0.3 });
  const cg = new THREE.CylinderGeometry(0.36, 0.36, 0.09, 28);
  cg.rotateX(Math.PI / 2);
  const m = new THREE.InstancedMesh(cg, [edgeMat, faceMat, faceMat], Math.max(1, n));
  m.frustumCulled = false;
  return m;
}

export function buildWorld(index, level, timeline) {
  const th = THEMES[level.world];
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(col(th.fog), th.fogNear, th.fogFar);
  scene.background = col(th.fog);
  const r = rng(100 + index * 17);
  const LX = timeline.lane_x;
  const sky = skyMesh(...th.sky);
  scene.add(sky);
  scene.add(new THREE.HemisphereLight(col(th.hemi[0]), col(th.hemi[1]), th.hemi[2]));
  const sun = new THREE.DirectionalLight(col(th.sun[0]), th.sun[1]);
  sun.position.set(...th.sun[2]);
  scene.add(sun);
  const world = new THREE.Group();
  scene.add(world);
  const flat = STD({ vertexColors: true, roughness: 0.85, metalness: 0.0 });
  const shiny = STD({ vertexColors: true, roughness: 0.35, metalness: 0.6 });
  const glow = new THREE.MeshBasicMaterial({ vertexColors: true, toneMapped: false });
  const mats = { flat, shiny, glow };
  const anims = [];
  const out = { scene, sky, trains: [], anims, index, theme: th, kind: level.kind };
  if (level.kind === 'temple') buildTemple(world, level, th, r, mats, anims, out);
  else if (level.kind === 'skyrail') buildSkyrail(world, level, th, r, mats, anims, out, LX);
  else buildLanes(world, level, th, r, mats, anims, out, LX, scene);
  out.coinMesh = coinMeshFor(level.coins.length);
  world.add(out.coinMesh);
  return out;
}

// ------------------------------------------------------------------ lanes (city / tunnel / lava)
function buildLanes(world, level, th, r, mats, anims, out, LX, scene) {
  const { flat, glow } = mats;
  const S0 = -170, S1 = level.length + 300;
  const LEN = S1 - S0, ZC = -(S0 + S1) / 2;
  const ch = new Chunker(90);
  if (!th.lava) {
    const gt = ballastTex(th.ground); gt.repeat.set(10, LEN / 6);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(60, LEN), STD({ map: gt, roughness: 1 }));
    ground.rotation.x = -Math.PI / 2; ground.position.set(0, -0.05, ZC);
    world.add(ground);
  } else {
    const lt = lavaTex(); lt.repeat.set(5, LEN / 14);
    const lt2 = lavaTex(); lt2.repeat.set(3, LEN / 22);
    const lava = new THREE.Mesh(new THREE.PlaneGeometry(120, LEN), new THREE.MeshBasicMaterial({ map: lt, toneMapped: false }));
    lava.rotation.x = -Math.PI / 2; lava.position.set(0, -0.6, ZC);
    world.add(lava);
    const lava2 = new THREE.Mesh(new THREE.PlaneGeometry(120, LEN), new THREE.MeshBasicMaterial({ map: lt2, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
    lava2.rotation.x = -Math.PI / 2; lava2.position.set(0, -0.55, ZC);
    world.add(lava2);
    scene.userData.lava = [lt, lt2];
    for (const lx of LX) ch.add('flat', box(3.0, 0.75, LEN, lx, -0.36, ZC, '#2a1d22'), ZC);
  }
  buildTracks(world, ch, th, LX, S0, S1, mats);
  const sideX = 4.3;
  if (!th.tunnel) {
    mats.facade = facadeMaterial(th);
    for (const sd of [-1, 1]) {
      ch.add('flat', box(2.6, th.lava ? 0.9 : 0.35, LEN, sd * (sideX + 1.3), th.lava ? -0.2 : 0.17, ZC, th.walk), ZC);
      ch.add('flat', box(0.25, th.lava ? 0.95 : 0.42, LEN, sd * (sideX + 0.1), th.lava ? -0.15 : 0.2, ZC, shade(th.walk, 0.8)), ZC);
      buildingRow(ch, th, r, sd, sideX + 3.2, S0, S1, { fVar: th.lava ? 6 : 8 });
      buildingRow(ch, th, r, sd, 34, S0, S1, { simple: true, wMin: 12, wVar: 16, fMin: 5, fVar: 11, gap: 6 });
    }
    const poles = [], heads = [], trunks = [], crowns = [], fronds = [];
    for (const sd of [-1, 1]) {
      for (let s = S0 + 6; s < S1; s += 16) {
        const x = sd * (sideX + 1.9);
        poles.push(M4(x, 2.6, -s));
        heads.push(M4(x - sd * 0.55, 5.15, -s));
      }
      for (let s = S0 + 14; s < S1; s += 16 + r() * 8) {
        const x = sd * (sideX + 2.2), z = -s;
        if (th.trees === 'round') {
          trunks.push(M4(x, 1.3, z));
          const k = 0.9 + r() * 0.4;
          crowns.push(M4(x, 3.4 * k, z, r() * 6, 1.6 * k, 1.5 * k, 1.6 * k));
        } else {
          trunks.push(M4(x, 3.2, z, 0, 0.8, 2.5, 0.8, (r() - 0.5) * 0.25, sd * 0.12));
          for (let k = 0; k < 7; k++) {
            const a = k / 7 * Math.PI * 2 + r();
            fronds.push(M4(x + sd * 0.4 + Math.cos(a) * 1.25, 6.35, z + Math.sin(a) * 1.25, -a, 1, 1, 1, 0, 0.5));
          }
        }
      }
    }
    world.add(instanced(paint(new THREE.CylinderGeometry(0.08, 0.11, 5.2, 8), '#3a3f47'), flat, poles));
    world.add(instanced(paint(new THREE.BoxGeometry(1.2, 0.18, 0.4), th.lava ? '#ffe2a8' : '#f6f2e6'), glow, heads));
    world.add(instanced(paint(new THREE.CylinderGeometry(0.16, 0.24, 2.6, 7), '#6d4a33'), flat, trunks));
    if (crowns.length) world.add(instanced(paint(new THREE.IcosahedronGeometry(1, 1), '#4caa4f'), flat, crowns));
    if (fronds.length) {
      const fg = new THREE.BoxGeometry(2.6, 0.08, 0.6); fg.translate(1.1, 0, 0);
      world.add(instanced(paint(fg, '#2f9e5a'), flat, fronds));
    }
  } else {
    const R = 10.5;
    const cTex = concreteTex('#c9ced6', 'rgba(60,70,85,0.45)');
    cTex.repeat.set(8, LEN / 8);
    const shell = new THREE.Mesh(new THREE.CylinderGeometry(R, R, LEN, 40, 1, true, -Math.PI / 2, Math.PI),
      STD({ map: cTex, side: THREE.BackSide, roughness: 0.9 }));
    shell.rotation.x = -Math.PI / 2;
    shell.position.set(0, 0.0, ZC);
    world.add(shell);
    const ribs = [];
    for (let s = S0; s < S1; s += 9) ribs.push(M4(0, 0, -s));
    world.add(instanced(paint(new THREE.TorusGeometry(R - 0.15, 0.22, 6, 40, Math.PI), '#9aa4b2'), flat, ribs));
    const lights = [];
    for (let s = S0; s < S1; s += 4.5) for (const x of [-3.2, 3.2]) lights.push(M4(x, Math.sqrt(R * R - x * x) - 0.35, -s));
    world.add(instanced(paint(new THREE.BoxGeometry(0.35, 0.12, 3.2), '#f4fbff'), glow, lights));
    ch.add('flat', box(5.2, 1.15, LEN, -7.3, 0.57, ZC, '#a7adb7'), ZC);
    ch.add('flat', box(0.35, 0.06, LEN, -4.85, 1.16, ZC, '#ffd21f'), ZC);
    ch.add('flat', box(2.2, 0.6, LEN, 7.6, 0.3, ZC, '#8a919d'), ZC);
    const pil = [];
    for (let s = S0; s < S1; s += 13) pil.push(M4(-8.4, 4.6, -s));
    world.add(instanced(paint(new THREE.BoxGeometry(0.9, 7, 0.9), '#e3e6eb'), flat, pil));
    const muralTexs = [0, 1, 2, 3, 4, 5].map((k) => muralTex(1000 + k * 77));
    const muralMats = muralTexs.map((t) => STD({ map: t, roughness: 0.7 }));
    const mg = new THREE.PlaneGeometry(14, 5.2);
    for (let s = S0; s < S1; s += 26) {
      const mm = new THREE.Mesh(mg, muralMats[Math.floor(r() * muralMats.length)]);
      if (r() < 0.5) { mm.position.set(9.15, 3.4, -s - 6); mm.rotation.y = -Math.PI / 2 + 0.18; }
      else { mm.position.set(-9.6, 4.0, -s - 6); mm.rotation.y = Math.PI / 2 - 0.25; }
      world.add(mm);
    }
    for (const sd of [-1, 1]) for (const yy of [5.2, 5.6]) ch.add('flat', box(0.12, 0.12, LEN, sd * (Math.sqrt(R * R - yy * yy) - 0.25), yy, ZC, '#3b3f48'), ZC);
    const sp = [], sr = [], sg = [];
    for (let s = S0 + 20; s < S1; s += 60) for (const x of [-1.3, 1.3]) {
      sp.push(M4(x, 1.6, -s));
      (r() < 0.5 ? sr : sg).push(M4(x, 3.05, -s + 0.12));
    }
    world.add(instanced(paint(new THREE.BoxGeometry(0.18, 3.3, 0.18), '#2a2d33'), flat, sp));
    if (sr.length) world.add(instanced(paint(new THREE.SphereGeometry(0.16, 10, 8), '#ff3b30'), glow, sr));
    if (sg.length) world.add(instanced(paint(new THREE.SphereGeometry(0.16, 10, 8), '#36ff6e'), glow, sg));
  }
  // overhead gantries
  {
    const gp = [], gb = [];
    for (let s = S0 + 30; s < S1; s += th.tunnel ? 120 : 55) {
      for (const sd of [-1, 1]) gp.push(M4(sd * 4.25, 3.4, -s));
      gb.push(M4(0, 6.7, -s));
    }
    world.add(instanced(paint(new THREE.BoxGeometry(0.28, 6.8, 0.28), '#5f6672'), flat, gp));
    world.add(instanced(paint(new THREE.BoxGeometry(8.8, 0.3, 0.3), '#5f6672'), flat, gb));
  }
  ch.build(world, mats);
  laneObstacles(world, level, LX, 0, flat, glow, anims);
  for (const o of level.obstacles) if (o.type === 'train') { const g = makeTrain(o, LX[o.lane], 0, mats, flat, anims); world.add(g); out.trains.push(g); }
  if (level.index === 4) {
    const fin = new THREE.Group();
    const cm = STD({ map: checkerTex(), roughness: 0.5 });
    const beam = new THREE.Mesh(new THREE.BoxGeometry(11, 1.4, 0.5), cm); beam.position.set(0, 7.4, 0); fin.add(beam);
    for (const sd of [-1, 1]) {
      const p = new THREE.Mesh(paint(new THREE.BoxGeometry(0.7, 8, 0.7), '#ffffff'), flat); p.position.set(sd * 5.5, 4, 0); fin.add(p);
      const b = new THREE.Mesh(paint(new THREE.BoxGeometry(0.75, 0.6, 0.75), '#ffcf2e'), glow); b.position.set(sd * 5.5, 8.2, 0); fin.add(b);
    }
    const fl = [];
    const fcols = ['#ff3d7f', '#ffcf2e', '#2ad1ff', '#2bd67b', '#ffffff'];
    for (let i = 0; i < 18; i++) {
      const x = -5 + i * (10 / 17);
      const fg = paint(new THREE.ConeGeometry(0.22, 0.55, 3), fcols[i % 5]);
      fg.rotateX(Math.PI); fg.translate(x, 6.3 - 0.35 * Math.sin(Math.PI * i / 17), 0.3);
      fl.push(fg);
    }
    fin.add(new THREE.Mesh(mergeGeometries(fl), glow));
    const gr = new THREE.Mesh(new THREE.PlaneGeometry(9, 1.2), cm); gr.rotation.x = -Math.PI / 2; gr.position.set(0, 0.3, 0); fin.add(gr);
    world.add(fin);
    out.finish = fin;
  }
}

// ------------------------------------------------------------------ sky rail: train roofs above the city
function buildSkyrail(world, level, th, r, mats, anims, out, LX) {
  const { flat, glow } = mats;
  const S0 = -220, S1 = level.length + 360;
  const LEN = S1 - S0, ZC = -(S0 + S1) / 2;
  const ch = new Chunker(110);
  const DROP = -42;
  // viaduct deck + parapets
  ch.add('flat', box(9.6, 1.0, LEN, 0, -0.5, ZC, '#c3c8cf'), ZC);
  ch.add('flat', box(10.4, 0.5, LEN, 0, -1.2, ZC, '#a1a8b2'), ZC);
  for (const sd of [-1, 1]) {
    ch.add('flat', box(0.3, 0.7, LEN, sd * 4.85, 0.35, ZC, '#d9dde3'), ZC);
    ch.add('shiny', box(0.08, 0.08, LEN, sd * 4.85, 1.05, ZC, '#e2312d'), ZC);
  }
  buildTracks(world, ch, th, LX, S0, S1, mats);
  const pil = [], posts = [];
  for (let s = S0; s < S1; s += 32) pil.push(M4(0, DROP / 2 - 1.2, -s));
  for (let s = S0; s < S1; s += 3.2) for (const sd of [-1, 1]) posts.push(M4(sd * 4.85, 0.75, -s));
  world.add(instanced(paint(new THREE.BoxGeometry(4.2, -DROP, 3.2), '#b4bac3'), flat, pil));
  world.add(instanced(paint(new THREE.BoxGeometry(0.06, 0.6, 0.06), '#e2312d'), flat, posts));
  // the city far below
  mats.facade = facadeMaterial(th);
  const gt = ballastTex('#8fa58a'); gt.repeat.set(40, LEN / 10);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(600, LEN), STD({ map: gt, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2; ground.position.set(0, DROP, ZC);
  world.add(ground);
  for (const sd of [-1, 1]) {
    // streets along the viaduct, then blocks of buildings at varying distances
    ch.add('flat', box(14, 0.2, LEN, sd * 12, DROP + 0.1, ZC, '#6c737c'), ZC);
    for (const [xn, fMin, fVar] of [[20, 4, 9], [48, 6, 12], [82, 8, 14], [125, 10, 16]]) {
      buildingRow(ch, th, r, sd, xn, S0, S1, { base: DROP, simple: true, wMin: 10, wVar: 14, dMin: 14, dVar: 10, fMin, fVar, gap: 10 });
    }
  }
  ch.build(world, mats);
  // trains: the runner's roofs and parked neighbours
  for (const o of level.obstacles) {
    if (o.type !== 'train') continue;
    const g = makeTrain(o, LX[o.lane], 0, mats, flat, anims);
    world.add(g);
    out.trains.push(g);
  }
  // bridges to duck under (steel girder with hazard stripes)
  const hz = STD({ map: hazardTex(), roughness: 0.5 });
  const redMat = new THREE.MeshBasicMaterial({ color: col('#ff2a2a'), toneMapped: false });
  for (const o of level.obstacles) {
    if (o.type !== 'bridge') continue;
    const g = new THREE.Group();
    const beam = new THREE.Mesh(new THREE.BoxGeometry(10.4, 0.85, 1.3), hz); beam.position.set(0, ROOF + 1.6, 0); g.add(beam);
    const top = new THREE.Mesh(paint(new THREE.BoxGeometry(10.8, 0.5, 2.2), '#4a505b'), flat); top.position.set(0, ROOF + 2.3, 0); g.add(top);
    for (const sd of [-1, 1]) {
      const p = new THREE.Mesh(paint(new THREE.BoxGeometry(0.7, ROOF + 2.6, 0.7), '#4a505b'), flat); p.position.set(sd * 5.4, (ROOF + 2.6) / 2, 0); g.add(p);
    }
    for (let i = 0; i < 5; i++) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.13, 10, 8), redMat); l.position.set(-4 + i * 2, ROOF + 1.1, 0.7); g.add(l); anims.push({ obj: l, kind: 'blink', seed: i + o.s }); }
    g.position.set(0, 0, -o.s);
    world.add(g);
  }
  // birds / clouds drifting below for depth
  const cl = [];
  for (let i = 0; i < 140; i++) {
    const s = S0 + r() * LEN;
    cl.push(M4((r() < 0.5 ? -1 : 1) * (14 + r() * 90), DROP + 18 + r() * 14, -s, r() * 3, 6 + r() * 10, 1.5 + r() * 1.5, 4 + r() * 6));
  }
  const cm = new THREE.MeshLambertMaterial({ color: col('#ffffff'), transparent: true, opacity: 0.8, emissive: col('#ffffff'), emissiveIntensity: 0.3 });
  world.add(instanced(new THREE.IcosahedronGeometry(1, 1), cm, cl));
}

// ------------------------------------------------------------------ jungle temple causeway
function buildTemple(world, level, th, r, mats, anims, out) {
  const { flat, glow } = mats;
  const stoneTex = carvedTex();
  const deckTex = concreteTex('#b3a283', 'rgba(70,55,35,0.5)');
  const deckMat = STD({ map: deckTex, roughness: 0.95 });
  const stoneMat = STD({ map: stoneTex, roughness: 0.9 });
  const W = 4.4, TH = 1.4;
  const gaps = level.obstacles.filter((o) => o.type === 'gap');
  const yawM = (a) => a; // heading angle: rotate geometry about y by a
  const place = (geo, x, y, z, a) => { const m = new THREE.Mesh(geo, flat); m.position.set(x, y, z); m.rotation.y = a; return m; };
  const dirv = (a) => [-Math.sin(a), -Math.cos(a)];
  const ch = new Chunker(100);
  const pillars = [], torches = [], flamesPos = [], curbs = [], trunks = [], canopy = [], rocks = [];
  const pieces = level.pieces;
  const lines = pieces.filter((p) => p.type === 'line');
  const nearPath = (x, z, d) => lines.some((p) => {
    const [ux, uz] = dirv(p.a);
    const L = p.s1 - p.s0;
    const t = Math.max(0, Math.min(L, (x - p.x) * ux + (z - p.z) * uz));
    const qx = p.x + ux * t, qz = p.z + uz * t;
    return (x - qx) ** 2 + (z - qz) ** 2 < d * d;
  });
  for (const pc of pieces) {
    if (pc.type === 'line') {
      // split by gaps
      let cuts = [[pc.s0, pc.s1]];
      for (const g of gaps) {
        cuts = cuts.flatMap(([a, b]) => (g.s0 < b && a < g.s1 ? [[a, g.s0], [g.s1, b]].filter(([u, v]) => v - u > 0.2) : [[a, b]]));
      }
      const [dx, dz] = dirv(pc.a);
      for (const [a, b] of cuts) {
        const L = b - a, mid = (a + b) / 2 - pc.s0;
        const cx = pc.x + dx * mid, cz = pc.z + dz * mid;
        const g = new THREE.BoxGeometry(W, TH, L);
        // uv repeat along length
        const uv = g.attributes.uv;
        for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * (i >= 8 && i < 16 ? 1 : 1), uv.getY(i) * (i >= 8 && i < 16 ? L / 4 : 1));
        const m = new THREE.Mesh(g, deckMat);
        m.position.set(cx, -TH / 2, cz);
        m.rotation.y = pc.a;
        world.add(m);
        // supports under the deck
        for (let s = a + 6; s < b - 3; s += 22) {
          const q = s - pc.s0;
          pillars.push(M4(pc.x + dx * q, -22, pc.z + dz * q, pc.a, 2.6, 40, 2.6));
        }
      }
      // edge stones, columns and torches
      const lx = -dz, lz = dx; // left normal
      for (let s = pc.s0 + 2; s < pc.s1 - 2; s += 3.0) {
        if (gaps.some((g) => s > g.s0 - 1.5 && s < g.s1 + 1.5)) continue;
        const q = s - pc.s0;
        for (const sd of [-1, 1]) {
          if (r() < 0.25) continue;
          const x = pc.x + dx * q + lx * sd * (W / 2 - 0.25), z = pc.z + dz * q + lz * sd * (W / 2 - 0.25);
          curbs.push(M4(x, 0.18, z, pc.a + (r() - 0.5) * 0.2, 0.5, 0.36 + r() * 0.3, 1.2 + r() * 1.2));
        }
      }
      for (let s = pc.s0 + 8; s < pc.s1 - 4; s += 13) {
        if (gaps.some((g) => s > g.s0 - 3 && s < g.s1 + 3)) continue;
        const q = s - pc.s0;
        const sd = (Math.floor(s / 13) % 2) ? 1 : -1;
        const x = pc.x + dx * q + lx * sd * (W / 2 + 0.9), z = pc.z + dz * q + lz * sd * (W / 2 + 0.9);
        const hgt = 3 + r() * 5;
        pillars.push(M4(x, hgt / 2 - 1.4, z, pc.a, 1.1, hgt + 2.8, 1.1));
        if (r() < 0.6) {
          torches.push(M4(x - lx * sd * 0.7, 1.4, z - lz * sd * 0.7, 0, 1, 1, 1));
          flamesPos.push([x - lx * sd * 0.7, 2.55, z - lz * sd * 0.7]);
        }
      }
      // giant jungle trees and rock spires on both sides, rising from the abyss
      for (let s = pc.s0; s < pc.s1; s += 9 + r() * 10) {
        const q = s - pc.s0;
        for (const sd of [-1, 1]) {
          const off = 9 + r() * 40;
          const x = pc.x + dx * q + lx * sd * off, z = pc.z + dz * q + lz * sd * off;
          if (nearPath(x, z, 8)) continue;
          if (r() < 0.55) {
            const h = 30 + r() * 40;
            trunks.push(M4(x, -40 + h / 2, z, r() * 3, 1.3 + r(), h / 2, 1.3 + r()));
            canopy.push(M4(x, -40 + h + 2, z, r() * 3, 6 + r() * 5, 3 + r() * 2.5, 6 + r() * 5));
          } else {
            const h = 20 + r() * 45;
            rocks.push(M4(x, -45 + h / 2, z, r() * 3, 3 + r() * 4, h / 2, 3 + r() * 4));
          }
        }
      }
    } else {
      // corner platform at the outer corner point, and a carved wall straight ahead
      const qx = pc.cx - pc.px * pc.r + pc.dx * pc.r, qz = pc.cz - pc.pz * pc.r + pc.dz * pc.r;
      const pg = new THREE.BoxGeometry(6.4, TH, 6.4);
      const m = new THREE.Mesh(pg, deckMat); m.position.set(qx, -TH / 2, qz); m.rotation.y = pc.a0; world.add(m);
      pillars.push(M4(qx, -22, qz, pc.a0, 4, 40, 4));
      const wx = qx + pc.dx * 4.6, wz = qz + pc.dz * 4.6;
      const wall = new THREE.Mesh(new THREE.BoxGeometry(9, 9, 1.6), stoneMat);
      wall.position.set(wx, 3.0, wz); wall.rotation.y = pc.a0; world.add(wall);
      // arrow-shaped glowing chevrons carved into the wall pointing to the turn side
      const turnSide = pc.d; // -1 left, +1 right
      for (let i = 0; i < 3; i++) {
        const cg = new THREE.ConeGeometry(0.5, 1.0, 3);
        cg.rotateZ(turnSide < 0 ? Math.PI / 2 : -Math.PI / 2);
        const cm = new THREE.Mesh(cg, new THREE.MeshBasicMaterial({ color: col('#ffcf2e'), toneMapped: false }));
        const lxw = -pc.dz, lzw = pc.dx; // left of incoming dir
        const side = turnSide < 0 ? 1 : -1; // offset along "left" axis
        cm.position.set(wx - pc.dx * 0.9 + lxw * side * (i - 1) * 1.3, 3.2, wz - pc.dz * 0.9 + lzw * side * (i - 1) * 1.3);
        cm.rotation.y = pc.a0;
        world.add(cm);
        anims.push({ obj: cm, kind: 'chev', seed: i });
      }
      for (const k of [-1, 1]) {
        const lxw = -pc.dz, lzw = pc.dx;
        const x = wx - pc.dx * 1.2 + lxw * k * 4.2, z = wz - pc.dz * 1.2 + lzw * k * 4.2;
        torches.push(M4(x, 1.4, z));
        flamesPos.push([x, 2.55, z]);
      }
    }
  }
  world.add(instanced(paint(new THREE.BoxGeometry(1, 1, 1), th.stoneDark), flat, pillars));
  world.add(instanced(paint(new THREE.BoxGeometry(1, 1, 1), th.stone), flat, curbs));
  world.add(instanced(paint(new THREE.CylinderGeometry(0.08, 0.12, 2.4, 6), '#3b2a1c'), flat, torches));
  world.add(instanced(paint(new THREE.CylinderGeometry(1, 1.3, 2, 8), '#5a4632'), flat, trunks));
  world.add(instanced(paint(new THREE.IcosahedronGeometry(1, 1), '#3f7f3a'), flat, canopy));
  world.add(instanced(paint(new THREE.CylinderGeometry(0.7, 1, 2, 7), '#8d8a7a'), flat, rocks));
  // abyss floor + mist
  const mistT = canvasTex(256, 256, (g, w, h) => {
    const rr2 = rng(4);
    g.clearRect(0, 0, w, h);
    for (let i = 0; i < 40; i++) { const x = rr2() * w, y = rr2() * h, s = 30 + rr2() * 60; const gr = g.createRadialGradient(x, y, 0, x, y, s); gr.addColorStop(0, 'rgba(255,255,255,0.5)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(x - s, y - s, s * 2, s * 2); }
  });
  mistT.repeat.set(20, 20);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000), STD({ color: col('#2e4a2c'), roughness: 1 }));
  floor.rotation.x = -Math.PI / 2; floor.position.y = -45; world.add(floor);
  const mist = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000), new THREE.MeshBasicMaterial({ map: mistT, transparent: true, opacity: 0.55, depthWrite: false, color: col('#e8f2e0') }));
  mist.rotation.x = -Math.PI / 2; mist.position.y = -9; world.add(mist);
  out.scene.userData.mist = mistT;
  // flames (sprites) on torches
  const fT = flameTex();
  const fMat = new THREE.SpriteMaterial({ map: fT, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
  for (const [x, y, z] of flamesPos) {
    const s = new THREE.Sprite(fMat); s.position.set(x, y, z); s.scale.set(0.7, 1.2, 1); world.add(s);
    anims.push({ obj: s, kind: 'torch', seed: x * 3.1 + z });
  }
  // hazards
  const sawMat = new THREE.MeshStandardMaterial({ map: sawTex(), transparent: true, alphaTest: 0.4, side: THREE.DoubleSide, metalness: 0.6, roughness: 0.3 });
  const spikeGeo = paint(new THREE.ConeGeometry(0.13, 0.75, 6), '#c9ced6');
  for (const o of level.obstacles) {
    const g = new THREE.Group();
    g.position.set(o.x, 0, o.z);
    g.rotation.y = o.a;
    if (o.type === 'gap') {
      // crumbling edges
      for (const sd of [-1, 1]) for (let i = 0; i < 4; i++) {
        const b = new THREE.Mesh(paint(new THREE.BoxGeometry(0.6 + r() * 0.6, 0.5, 0.5), th.stoneDark), flat);
        b.position.set(-1.8 + i * 1.2, -0.9 - r() * 1.5, sd * ((o.s1 - o.s0) / 2 + 0.3) * -1);
        b.rotation.set(r(), r(), r());
        g.add(b);
      }
    } else if (o.type === 'fire') {
      const grate = new THREE.Mesh(paint(new THREE.BoxGeometry(W, 0.12, 1.4), '#2a2420'), flat); grate.position.y = 0.06; g.add(grate);
      for (let i = 0; i < 5; i++) {
        const s = new THREE.Sprite(fMat); s.position.set(-1.7 + i * 0.85, 0.7, 0); s.scale.set(1.0, 1.8, 1); g.add(s);
        anims.push({ obj: s, kind: 'fire', seed: i + o.x });
      }
      const gl = new THREE.Mesh(new THREE.PlaneGeometry(6, 3), new THREE.MeshBasicMaterial({ map: SPR(), color: col('#ff7a1f'), transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
      gl.position.set(0, 1.0, 0.3); g.add(gl);
    } else if (o.type === 'spikes') {
      const base = new THREE.Mesh(paint(new THREE.BoxGeometry(W, 0.25, 1.4), '#4a4038'), flat); base.position.y = 0.12; g.add(base);
      for (let i = 0; i < 9; i++) for (let j = 0; j < 3; j++) { const sp = new THREE.Mesh(spikeGeo, flat); sp.position.set(-1.9 + i * 0.47, 0.6, -0.45 + j * 0.45); g.add(sp); }
    } else if (o.type === 'log') {
      const lg = new THREE.Mesh(paint(new THREE.CylinderGeometry(0.42, 0.42, W + 1.2, 12), '#6b4a2e'), flat);
      lg.rotation.z = Math.PI / 2; lg.position.y = 0.42; g.add(lg);
      for (let i = 0; i < 8; i++) { const sp = new THREE.Mesh(spikeGeo, flat); const a = i * 0.9; sp.position.set(-2 + i * 0.55, 0.42 + Math.cos(a) * 0.5, Math.sin(a) * 0.5); sp.rotation.x = a; g.add(sp); }
    } else if (o.type === 'blade' || o.type === 'arch') {
      for (const sd of [-1, 1]) {
        const p = new THREE.Mesh(new THREE.BoxGeometry(1.0, 4.4, 1.0), stoneMat); p.position.set(sd * (W / 2 + 0.6), 2.2, 0); g.add(p);
      }
      const lint = new THREE.Mesh(new THREE.BoxGeometry(W + 2.4, 1.2, 1.1), stoneMat); lint.position.set(0, o.type === 'arch' ? 1.95 : 3.9, 0); g.add(lint);
      if (o.type === 'arch') {
        // glowing eyes on the lintel
        for (const sd of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.16, 10, 8), new THREE.MeshBasicMaterial({ color: col('#ff3b1f'), toneMapped: false })); e.position.set(sd * 0.7, 2.05, 0.58); g.add(e); anims.push({ obj: e, kind: 'blink', seed: sd + o.x }); }
      } else {
        const axle = new THREE.Mesh(paint(new THREE.BoxGeometry(W + 1.2, 0.22, 0.22), '#3a3a3a'), flat); axle.position.set(0, 2.25, 0); g.add(axle);
        for (const k of [-1.2, 1.2]) {
          const saw = new THREE.Mesh(new THREE.CircleGeometry(0.85, 40), sawMat);
          saw.position.set(k, 2.25, 0); saw.rotation.y = Math.PI / 2; g.add(saw);
          anims.push({ obj: saw, kind: 'sawx', seed: k });
        }
        const hang = new THREE.Mesh(paint(new THREE.BoxGeometry(0.16, 1.5, 0.16), '#3a3a3a'), flat); hang.position.set(0, 3.0, 0); g.add(hang);
      }
    } else if (o.type === 'corner') {
      continue;
    }
    world.add(g);
  }
}
