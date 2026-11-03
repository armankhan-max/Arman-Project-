// Core engine: renderer, post-processing (bloom, depth of field, motion/zoom blur, grade, grain),
// toon materials with rim light + outlines, camera rigs and easing helpers.
import * as THREE from 'three';

export const W = 1600, H = 900;

// ------------------------------------------------------------------ math / easing
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
export const smoother = (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
export const easeOut = (t) => 1 - Math.pow(1 - clamp(t), 3);
export const easeIn = (t) => Math.pow(clamp(t), 3);
export const easeInOut = (t) => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const expoOut = (t) => { t = clamp(t); return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); };
export const expoInOut = (t) => { t = clamp(t); if (t === 0 || t === 1) return t; return t < .5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2; };
export const backOut = (t, s = 1.70158) => { t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1; };
export const elasticOut = (t) => { t = clamp(t); if (t === 0 || t === 1) return t; return Math.pow(2, -10 * t) * Math.sin((t * 10 - .75) * (2 * Math.PI / 3)) + 1; };
export const range = (t, a, b) => clamp((t - a) / (b - a));
export const pulse = (t, a, b, f = .15) => smooth(range(t, a, a + f)) * (1 - smooth(range(t, b - f, b)));
export function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
export function noise1(x) { const i = Math.floor(x), f = x - i; const u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; }
export function rng(seed) { let s = seed >>> 0 || 1; return () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return ((s >>> 0) % 100000) / 100000; }; }
export const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);

// ------------------------------------------------------------------ renderer
export const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
document.body.appendChild(renderer.domElement);

const depthTex = new THREE.DepthTexture(W, H);
depthTex.type = THREE.UnsignedIntType;
const rtMain = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4, depthTexture: depthTex, depthBuffer: true });
const mk = (w, h) => new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, depthBuffer: false });
const rtB1 = mk(W / 4, H / 4), rtB2 = mk(W / 4, H / 4), rtB3 = mk(W / 8, H / 8), rtB4 = mk(W / 8, H / 8);

const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const quadGeo = new THREE.PlaneGeometry(2, 2);
function pass(frag, uniforms) {
  const m = new THREE.ShaderMaterial({
    uniforms, depthTest: false, depthWrite: false,
    vertexShader: 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }',
    fragmentShader: frag,
  });
  const s = new THREE.Scene(); s.add(new THREE.Mesh(quadGeo, m));
  return { m, s, u: m.uniforms };
}
const brightPass = pass(`uniform sampler2D tex; uniform float thr; varying vec2 vUv;
void main(){ vec2 px=1./vec2(${W}.,${H}.); vec3 c=vec3(0.);
 c+=texture2D(tex,vUv+px*vec2(-1.,-1.)).rgb; c+=texture2D(tex,vUv+px*vec2(1.,-1.)).rgb;
 c+=texture2D(tex,vUv+px*vec2(-1.,1.)).rgb; c+=texture2D(tex,vUv+px*vec2(1.,1.)).rgb; c*=.25;
 float l=max(c.r,max(c.g,c.b)); gl_FragColor=vec4(c*smoothstep(thr,thr+.35,l),1.); }`, { tex: { value: null }, thr: { value: .8 } });
const blurPass = pass(`uniform sampler2D tex; uniform vec2 dir; varying vec2 vUv;
void main(){ vec3 c=texture2D(tex,vUv).rgb*.227;
 c+=texture2D(tex,vUv+dir*1.384).rgb*.316; c+=texture2D(tex,vUv-dir*1.384).rgb*.316;
 c+=texture2D(tex,vUv+dir*3.230).rgb*.070; c+=texture2D(tex,vUv-dir*3.230).rgb*.070;
 gl_FragColor=vec4(c,1.); }`, { tex: { value: null }, dir: { value: new THREE.Vector2() } });

const finalPass = pass(`
uniform sampler2D tColor, tDepth, tBloom1, tBloom2;
uniform float near, far, focus, aperture, maxBlur, bloom, vign, grain, time, fade, flash, sat, contrast, ca, zoomBlur, exposure;
uniform vec2 dirBlur; uniform vec3 tint, lift;
varying vec2 vUv;
float linD(float d){ float z=d*2.-1.; return 2.*near*far/(far+near-z*(far-near)); }
float rnd(vec2 p){ return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453); }
vec3 aces(vec3 x){ return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.); }
void main(){
  vec2 uv=vUv; vec2 asp=vec2(${H}./${W}.,1.);
  float d=linD(texture2D(tDepth,uv).r);
  float coc=clamp(abs(d-focus)/d*aperture,0.,maxBlur);
  vec3 col=vec3(0.); float wsum=0.;
  if(length(dirBlur)>0.0005 || zoomBlur>0.0005){
    vec2 zd=(uv-.5)*zoomBlur;
    for(int i=0;i<12;i++){ float f=float(i)/11.-.5; vec2 o=dirBlur*f - zd*(f+.5);
      col+=texture2D(tColor,uv+o).rgb; wsum+=1.; }
    col/=wsum;
  } else if(coc>0.0006){
    col=texture2D(tColor,uv).rgb; wsum=1.;
    for(int i=0;i<16;i++){ float fi=float(i)+.5; float r=sqrt(fi/16.); float a=fi*2.39996;
      vec2 o=vec2(cos(a),sin(a))*r*coc*asp; vec2 suv=uv+o;
      float sd=linD(texture2D(tDepth,suv).r); float scoc=clamp(abs(sd-focus)/sd*aperture,0.,maxBlur);
      float w=(sd<d)? smoothstep(0.,1.,scoc/max(coc,1e-4)*1.2) : 1.;
      col+=texture2D(tColor,suv).rgb*w; wsum+=w; }
    col/=wsum;
  } else col=texture2D(tColor,uv).rgb;
  if(ca>0.){ vec2 o=(uv-.5)*ca; col.r=mix(col.r,texture2D(tColor,uv+o).r,.7); col.b=mix(col.b,texture2D(tColor,uv-o).b,.7); }
  col+= (texture2D(tBloom1,uv).rgb*.9 + texture2D(tBloom2,uv).rgb*1.3)*bloom;
  col*=exposure*tint;
  col=aces(col*1.05);
  col=pow(col,vec3(1./2.2));
  col=col+lift*(1.-col);
  float l=dot(col,vec3(.299,.587,.114)); col=mix(vec3(l),col,sat);
  col=(col-.5)*contrast+.5;
  vec2 vc=uv-.5; col*=1.-vign*dot(vc*vec2(1.25,1.),vc*vec2(1.25,1.))*1.6;
  col+= (rnd(uv*vec2(913.1,577.7)+time)-.5)*grain;
  col=mix(col,vec3(1.),flash); col*=1.-fade;
  gl_FragColor=vec4(clamp(col,0.,1.),1.);
}`, {
  tColor: { value: rtMain.texture }, tDepth: { value: depthTex }, tBloom1: { value: rtB1.texture }, tBloom2: { value: rtB3.texture },
  near: { value: .1 }, far: { value: 500 }, focus: { value: 8 }, aperture: { value: 0 }, maxBlur: { value: .012 },
  bloom: { value: .5 }, vign: { value: .35 }, grain: { value: .035 }, time: { value: 0 }, fade: { value: 0 }, flash: { value: 0 },
  sat: { value: 1.08 }, contrast: { value: 1.04 }, ca: { value: .0015 }, zoomBlur: { value: 0 }, exposure: { value: 1 },
  dirBlur: { value: new THREE.Vector2() }, tint: { value: new THREE.Vector3(1, 1, 1) }, lift: { value: new THREE.Vector3(0, 0, 0) },
});
export const post = finalPass.u;
export const postDefaults = () => {
  post.aperture.value = 0; post.focus.value = 8; post.maxBlur.value = .012; post.bloom.value = .32; post.vign.value = .35;
  post.grain.value = .03; post.fade.value = 0; post.flash.value = 0; post.sat.value = 1.08; post.contrast.value = 1.04;
  post.ca.value = .0012; post.zoomBlur.value = 0; post.exposure.value = 1; post.dirBlur.value.set(0, 0);
  post.tint.value.set(1, 1, 1); post.lift.value.set(0, 0, 0); brightPass.u.thr.value = 1.05;
};
export const setBloomThreshold = (v) => { brightPass.u.thr.value = v; };

export function renderFrame(scene, camera, t) {
  post.near.value = camera.near; post.far.value = camera.far; post.time.value = t % 10;
  renderer.setRenderTarget(rtMain); renderer.render(scene, camera);
  brightPass.u.tex.value = rtMain.texture; renderer.setRenderTarget(rtB1); renderer.render(brightPass.s, quadCam);
  blurPass.u.tex.value = rtB1.texture; blurPass.u.dir.value.set(4 / W, 0); renderer.setRenderTarget(rtB2); renderer.render(blurPass.s, quadCam);
  blurPass.u.tex.value = rtB2.texture; blurPass.u.dir.value.set(0, 4 / H); renderer.setRenderTarget(rtB1); renderer.render(blurPass.s, quadCam);
  blurPass.u.tex.value = rtB1.texture; blurPass.u.dir.value.set(8 / W, 0); renderer.setRenderTarget(rtB3); renderer.render(blurPass.s, quadCam);
  blurPass.u.tex.value = rtB3.texture; blurPass.u.dir.value.set(0, 8 / H); renderer.setRenderTarget(rtB4); renderer.render(blurPass.s, quadCam);
  blurPass.u.tex.value = rtB4.texture; blurPass.u.dir.value.set(12 / W, 0); renderer.setRenderTarget(rtB3); renderer.render(blurPass.s, quadCam);
  renderer.setRenderTarget(null); renderer.render(finalPass.s, quadCam);
}

// ------------------------------------------------------------------ toon materials
function gradTex(steps) {
  const d = new Uint8Array(steps.length * 4);
  steps.forEach((v, i) => { d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = v; d[i * 4 + 3] = 255; });
  const t = new THREE.DataTexture(d, steps.length, 1); t.minFilter = t.magFilter = THREE.NearestFilter; t.needsUpdate = true; return t;
}
export const GRAD3 = gradTex([110, 190, 255]);
export const GRAD2 = gradTex([150, 255]);
export const GRAD_SOFT = (() => { const a = []; for (let i = 0; i < 16; i++) a.push(Math.round(120 + 135 * smooth(i / 15))); const t = gradTex(a); t.minFilter = t.magFilter = THREE.LinearFilter; return t; })();

const matCache = new Map();
// Toon material with fresnel rim light. opts: rim (0..), rimColor, emissive, soft
export function toon(color, opts = {}) {
  const key = JSON.stringify([color, opts]);
  if (!opts.unique && matCache.has(key)) return matCache.get(key);
  const m = new THREE.MeshToonMaterial({
    color, gradientMap: opts.soft ? GRAD_SOFT : GRAD3,
    emissive: opts.emissive ?? 0x000000, emissiveIntensity: opts.emissiveIntensity ?? 1,
    transparent: !!opts.transparent, opacity: opts.opacity ?? 1, side: opts.side ?? THREE.FrontSide,
    map: opts.map ?? null, depthWrite: opts.depthWrite ?? true,
  });
  const rim = opts.rim ?? .35, rc = new THREE.Color(opts.rimColor ?? 0xffffff);
  m.userData.rim = { value: rim }; m.userData.rimColor = { value: rc };
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uRim = m.userData.rim; sh.uniforms.uRimColor = m.userData.rimColor;
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform float uRim; uniform vec3 uRimColor;')
      .replace('#include <opaque_fragment>', `float fr=1.-abs(dot(normalize(normal),normalize(vViewPosition)));
      outgoingLight+=uRimColor*smoothstep(.55,.95,fr)*uRim;
      #include <opaque_fragment>`);
  };
  m.customProgramCacheKey = () => 'toonrim';
  if (!opts.unique) matCache.set(key, m);
  return m;
}
export function basic(color, opts = {}) {
  return new THREE.MeshBasicMaterial({ color, transparent: !!opts.transparent, opacity: opts.opacity ?? 1, side: opts.side ?? THREE.FrontSide, map: opts.map ?? null, depthWrite: opts.depthWrite ?? true, blending: opts.additive ? THREE.AdditiveBlending : THREE.NormalBlending, fog: opts.fog ?? true });
}
export function glow(color, intensity = 3, opts = {}) {
  const c = new THREE.Color(color).multiplyScalar(intensity);
  return new THREE.MeshBasicMaterial({ color: c, transparent: !!opts.transparent || opts.opacity !== undefined, opacity: opts.opacity ?? 1, blending: opts.additive ? THREE.AdditiveBlending : THREE.NormalBlending, depthWrite: opts.depthWrite ?? !opts.additive, side: opts.side ?? THREE.FrontSide, fog: false });
}

// Inverted-hull outline (world-space thickness).
const outlineMats = new Map();
export function outlineMat(width = .02, color = 0x1a1626) {
  const key = width + '_' + color;
  if (outlineMats.has(key)) return outlineMats.get(key);
  const m = new THREE.ShaderMaterial({
    uniforms: { w: { value: width }, col: { value: new THREE.Color(color) } },
    side: THREE.BackSide,
    vertexShader: `uniform float w;
      #include <common>
      #include <skinning_pars_vertex>
      void main(){ vec3 p=position+normal*w; vec4 mv=modelViewMatrix*vec4(p,1.); gl_Position=projectionMatrix*mv; }`,
    fragmentShader: 'uniform vec3 col; void main(){ gl_FragColor=vec4(col,1.); }',
  });
  outlineMats.set(key, m); return m;
}
// Adds outline child meshes for all meshes in obj (skip those with userData.noOutline)
export function addOutline(obj, width = .02, color = 0x1a1626) {
  const list = [];
  obj.traverse((o) => { if (o.isMesh && !o.userData.noOutline && !o.userData.isOutline) list.push(o); });
  for (const o of list) {
    // outline width relative to object world scale is approximated by local scale compensation
    const s = o.getWorldScale(new THREE.Vector3()); const k = 1 / Math.max(1e-3, (s.x + s.y + s.z) / 3);
    const ol = new THREE.Mesh(o.geometry, outlineMat(width * k, color));
    ol.userData.isOutline = true; ol.castShadow = false; ol.receiveShadow = false; ol.raycast = () => { };
    o.add(ol);
  }
  return obj;
}
export function shadows(obj, cast = true, receive = true) {
  obj.traverse((o) => { if (o.isMesh && !o.userData.isOutline) { o.castShadow = cast; o.receiveShadow = receive; } });
  return obj;
}

// ------------------------------------------------------------------ geometry helpers
export function mesh(geo, mat, x = 0, y = 0, z = 0, parent = null) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); if (parent) parent.add(m); return m;
}
export const G = {
  sphere: (r = 1, ws = 32, hs = 20) => new THREE.SphereGeometry(r, ws, hs),
  box: (x, y, z) => new THREE.BoxGeometry(x, y, z),
  cyl: (rt, rb, h, s = 24) => new THREE.CylinderGeometry(rt, rb, h, s),
  capsule: (r, l, s = 12) => new THREE.CapsuleGeometry(r, l, 6, s),
  torus: (r, t, rs = 12, ts = 40) => new THREE.TorusGeometry(r, t, rs, ts),
};
export function roundBox(w, h, d, r = .1, seg = 3) {
  // rounded box via smoothed box geometry
  const g = new THREE.BoxGeometry(w, h, d, seg * 2, seg * 2, seg * 2);
  const p = g.attributes.position, v = new THREE.Vector3();
  const hw = w / 2 - r, hh = h / 2 - r, hd = d / 2 - r;
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const c = new THREE.Vector3(clamp(v.x, -hw, hw), clamp(v.y, -hh, hh), clamp(v.z, -hd, hd));
    const n = v.clone().sub(c); if (n.lengthSq() > 0) n.normalize().multiplyScalar(r);
    p.setXYZ(i, c.x + n.x, c.y + n.y, c.z + n.z);
  }
  g.computeVertexNormals(); return g;
}
export function tube(points, r = .1, seg = 64, rs = 12, closed = false) {
  const c = new THREE.CatmullRomCurve3(points.map((p) => Array.isArray(p) ? V(...p) : p), closed);
  return new THREE.TubeGeometry(c, seg, r, rs, closed);
}
// tube with varying radius
export function taperTube(points, rfn, seg = 64, rs = 14) {
  const curve = new THREE.CatmullRomCurve3(points.map((p) => Array.isArray(p) ? V(...p) : p));
  const g = new THREE.TubeGeometry(curve, seg, 1, rs, false);
  const p = g.attributes.position, n = g.attributes.normal;
  for (let i = 0; i <= seg; i++) {
    const c = curve.getPointAt(i / seg); const r = rfn(i / seg);
    for (let j = 0; j <= rs; j++) {
      const k = i * (rs + 1) + j;
      p.setXYZ(k, c.x + n.getX(k) * r, c.y + n.getY(k) * r, c.z + n.getZ(k) * r);
    }
  }
  p.needsUpdate = true; g.computeVertexNormals(); return g;
}

// ------------------------------------------------------------------ sky + environment
export function skyDome(top, mid, bottom, r = 600) {
  const m = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { top: { value: new THREE.Color(top) }, mid: { value: new THREE.Color(mid) }, bot: { value: new THREE.Color(bottom) }, sun: { value: V(0.3, .25, -1).normalize() }, sunCol: { value: new THREE.Color(0xfff1d0) }, sunAmt: { value: 0 } },
    vertexShader: 'varying vec3 vP; void main(){ vP=normalize(position); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: `uniform vec3 top,mid,bot,sunCol,sun; uniform float sunAmt; varying vec3 vP;
     void main(){ float h=vP.y; vec3 c= h>0.? mix(mid,top,pow(clamp(h,0.,1.),.6)) : mix(mid,bot,clamp(-h*4.,0.,1.));
     float s=max(dot(vP,normalize(sun)),0.); c+=sunCol*(pow(s,600.)*4.+pow(s,8.)*.35)*sunAmt; gl_FragColor=vec4(c,1.); }`,
  });
  const s = new THREE.Mesh(new THREE.SphereGeometry(r, 32, 16), m); s.userData.noOutline = true; s.frustumCulled = false; s.renderOrder = -10;
  return s;
}
export function lights(scene, o = {}) {
  const hemi = new THREE.HemisphereLight(o.sky ?? 0xbfd6ff, o.ground ?? 0x8a7a70, o.hemi ?? 1.1); scene.add(hemi);
  const sun = new THREE.DirectionalLight(o.sunColor ?? 0xfff0dd, o.sun ?? 2.4);
  sun.position.set(...(o.sunPos ?? [12, 20, 8])); sun.castShadow = o.shadow ?? true;
  const sz = o.shadowSize ?? 18; Object.assign(sun.shadow.camera, { left: -sz, right: sz, top: sz, bottom: -sz, near: .5, far: 120 });
  sun.shadow.mapSize.set(o.shadowRes ?? 2048, o.shadowRes ?? 2048); sun.shadow.bias = -0.0004; sun.shadow.normalBias = .02; sun.shadow.radius = 3;
  scene.add(sun); scene.add(sun.target);
  return { hemi, sun };
}

// ------------------------------------------------------------------ camera rig
// keys: [{t, p:[x,y,z], l:[x,y,z], fov, roll}] interpolated with Catmull-Rom on positions and eased time
export class CamPath {
  constructor(keys, opts = {}) {
    this.keys = keys; this.ease = opts.ease ?? smoother; this.shake = opts.shake ?? .02; this.seed = opts.seed ?? 1;
    this.spline = keys.length > 2;
    if (this.spline) {
      this.pc = new THREE.CatmullRomCurve3(keys.map((k) => V(...k.p)), false, 'centripetal');
      this.lc = new THREE.CatmullRomCurve3(keys.map((k) => V(...k.l)), false, 'centripetal');
    }
  }
  apply(cam, t, off = null) {
    const k = this.keys, n = k.length;
    let u; // global param 0..1 along keys
    if (t <= k[0].t) u = 0; else if (t >= k[n - 1].t) u = 1;
    else { let i = 0; while (t > k[i + 1].t) i++; const f = this.ease((t - k[i].t) / (k[i + 1].t - k[i].t)); u = (i + f) / (n - 1); }
    let p, l;
    if (this.spline) { p = this.pc.getPoint(u); l = this.lc.getPoint(u); }
    else { p = V(...k[0].p).lerp(V(...k[n - 1].p), u); l = V(...k[0].l).lerp(V(...k[n - 1].l), u); }
    const seg = u * (n - 1), i0 = Math.min(n - 2, Math.floor(seg)), f = seg - i0;
    const fov = lerp(k[i0].fov ?? 40, k[i0 + 1]?.fov ?? k[i0].fov ?? 40, f);
    const roll = lerp(k[i0].roll ?? 0, k[i0 + 1]?.roll ?? k[i0].roll ?? 0, f);
    if (off) { p.add(off); l.add(off); }
    const s = this.shake, sd = this.seed * 10;
    p.x += noise1(t * .7 + sd) * s; p.y += noise1(t * .6 + sd + 3) * s; l.x += noise1(t * .5 + sd + 7) * s * .6; l.y += noise1(t * .55 + sd + 11) * s * .6;
    cam.position.copy(p); cam.up.set(0, 1, 0); cam.lookAt(l);
    cam.rotateZ(roll + noise1(t * .4 + sd + 5) * s * .15);
    if (cam.fov !== fov) { cam.fov = fov; cam.updateProjectionMatrix(); }
    return { p, l, dist: p.distanceTo(l) };
  }
}
export function camAt(cam, p, l, fov = 40, roll = 0) {
  cam.position.set(...p); cam.up.set(0, 1, 0); cam.lookAt(V(...l)); cam.rotateZ(roll);
  if (cam.fov !== fov) { cam.fov = fov; cam.updateProjectionMatrix(); }
}

// ------------------------------------------------------------------ canvas textures
export function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
export function radialSprite(color = '#ffffff', soft = .5) {
  return canvasTex(128, 128, (g) => {
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    gr.addColorStop(0, color); gr.addColorStop(soft, color + '88'); gr.addColorStop(1, color + '00');
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  });
}

export function disposeScene(scene) {
  scene.traverse((o) => {
    if (o.geometry && !o.userData.isOutline && !o.geometry.userData.shared) o.geometry.dispose();
    if (o.material) {
      const ms = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of ms) { if (m.userData?.keep) continue; if (m.map && !m.map.userData?.shared) m.map.dispose(); }
    }
  });
}
