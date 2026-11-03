// 3D sets: sunny town street + park, cosy living room, night "organ city", bedroom, dining corner,
// and the inside-the-body tunnels (vein, gut).
import * as THREE from 'three';
import { toon, glow, basic, addOutline, shadows, mesh, G, roundBox, tube, skyDome, lights, V, rng, canvasTex, clamp, smooth, radialSprite } from './core.js';

// ------------------------------------------------------------------ small props
export function tree(s = 1, seed = 1, col = 0x6dbb4f) {
  const g = new THREE.Group(); const R = rng(seed);
  mesh(G.cyl(.12, .18, 1.6, 10), toon(0x8a5a3c), 0, .8, 0, g);
  const mL = toon(col, { rim: .35, rimColor: 0xeaffc8 }), mL2 = toon(new THREE.Color(col).multiplyScalar(.85).getHex(), { rim: .3 });
  for (let i = 0; i < 4; i++) { const b = mesh(new THREE.IcosahedronGeometry(.75 + R() * .3, 2), i % 2 ? mL2 : mL, (R() - .5) * .9, 2.1 + R() * .7, (R() - .5) * .9, g); b.scale.setScalar(1 + R() * .2); }
  g.scale.setScalar(s); return g;
}
export function bush(s = 1, seed = 2) {
  const g = new THREE.Group(); const R = rng(seed); const m = toon(0x5cae47, { rim: .3 });
  for (let i = 0; i < 3; i++) mesh(new THREE.IcosahedronGeometry(.45 + R() * .2, 1), m, (i - 1) * .45, .35, (R() - .5) * .3, g);
  g.scale.setScalar(s); return g;
}
export function lamp(h = 3.4) {
  const g = new THREE.Group(); const m = toon(0x3a3f55);
  mesh(G.cyl(.06, .08, h, 10), m, 0, h / 2, 0, g);
  mesh(G.cyl(.05, .05, .7, 8), m, .3, h, 0, g).rotation.z = Math.PI / 2;
  const head = mesh(G.cyl(.08, .22, .2, 14), m, .6, h - .08, 0, g);
  const bulb = mesh(G.sphere(.1, 12, 8), glow(0xffe2a8, 2), .6, h - .2, 0, g); bulb.userData.noOutline = true;
  g.userData.bulb = bulb; return g;
}
export function house(w, h, d, col, roofCol, seed = 1) {
  const g = new THREE.Group(); const R = rng(seed);
  mesh(roundBox(w, h, d, .06), toon(col, { rim: .2 }), 0, h / 2, 0, g);
  const roof = new THREE.Mesh(new THREE.CylinderGeometry(.01, w * .78, 1.6, 4, 1), toon(roofCol, { rim: .2 }));
  roof.position.set(0, h + .78, 0); roof.rotation.y = Math.PI / 4; roof.scale.set(1, 1, d / w); g.add(roof);
  const mWin = toon(0xbfe3ff, { emissive: 0x334455, emissiveIntensity: .3 }), mFr = toon(0xffffff);
  const rows = Math.max(1, Math.floor(h / 1.6));
  for (let r = 0; r < rows; r++) for (const x of [-w * .27, w * .27]) {
    mesh(G.box(.62, .72, .05), mFr, x, 1 + r * 1.5, d / 2 + .01, g);
    mesh(G.box(.5, .6, .06), mWin, x, 1 + r * 1.5, d / 2 + .02, g);
  }
  mesh(G.box(.62, 1.15, .06), toon(0x7a4f37), 0, .58, d / 2 + .02, g);
  return g;
}
export function cloud(seed = 1, s = 1) {
  const g = new THREE.Group(); const R = rng(seed); const m = toon(0xffffff, { rim: .2, emissive: 0x9aa7c0, emissiveIntensity: .35 });
  for (let i = 0; i < 5; i++) mesh(new THREE.IcosahedronGeometry(1 + R() * .8, 2), m, (i - 2) * 1.3, R() * .6, (R() - .5), g).scale.set(1, .75, 1);
  g.scale.setScalar(s); return g;
}

// ------------------------------------------------------------------ TOWN (street + park), path runs along -Z
export function buildTown(o = {}) {
  const scene = new THREE.Scene();
  const sky = skyDome(o.top ?? 0x3d8fe8, o.mid ?? 0xbfe2ff, o.bot ?? 0xd7ecff); sky.material.uniforms.sunAmt.value = 1; scene.add(sky);
  scene.fog = new THREE.Fog(o.fog ?? 0xcfe6ff, 45, 210);
  const L = lights(scene, { sunPos: [14, 22, 10], sun: 2.6, hemi: 1.2, shadowSize: 22 });
  const ground = mesh(new THREE.PlaneGeometry(900, 900), toon(0x8fd16a, { rim: 0 }), 0, 0, 0, scene); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true;
  // road along z
  const road = mesh(new THREE.PlaneGeometry(6, 400), toon(0x5d6274, { rim: 0 }), 0, .01, -100, scene); road.rotation.x = -Math.PI / 2; road.receiveShadow = true;
  const mDash = toon(0xf5f1e3);
  for (let z = 60; z > -260; z -= 4) { const d = mesh(new THREE.PlaneGeometry(.18, 1.8), mDash, 0, .02, z, scene); d.rotation.x = -Math.PI / 2; d.receiveShadow = true; }
  // sidewalks (where characters walk): x = ±4.2
  for (const sx of [-1, 1]) {
    const sw = mesh(G.box(2.4, .16, 400), toon(0xe9e3d7, { rim: 0 }), sx * 4.2, .08, -100, scene); sw.receiveShadow = true;
    mesh(G.box(.14, .2, 400), toon(0xc9c2b5, { rim: 0 }), sx * 3.0, .1, -100, scene).receiveShadow = true;
  }
  const R = rng(5);
  const pal = [0xffb4a2, 0xfdd77a, 0xa8d8ea, 0xc3aed6, 0xf6c6ea, 0xb6e2a1, 0xffcf9f, 0x9fd3c7];
  const roofs = [0xd9534f, 0x6c5b7b, 0x355c7d, 0xc06c84, 0x3f7f73];
  for (let z = 50, i = 0; z > -240; z -= 7.5, i++) for (const sx of [-1, 1]) {
    const w = 4.5 + R() * 1.5, h = 3 + R() * 3, d = 4 + R() * 1.5;
    const hs = house(w, h, d, pal[(i * 3 + (sx > 0 ? 1 : 0)) % pal.length], roofs[(i + (sx > 0 ? 2 : 0)) % roofs.length], i);
    hs.position.set(sx * (9.5 + R() * .8), 0, z); hs.rotation.y = sx > 0 ? -Math.PI / 2 : Math.PI / 2; scene.add(hs);
    if (i % 2 === 0) { const tr = tree(.9 + R() * .4, i * 7 + (sx > 0 ? 1 : 0)); tr.position.set(sx * 6.3, 0, z - 3.7); scene.add(tr); }
    if (i % 3 === 1) { const lp = lamp(); lp.position.set(sx * 5.6, 0, z - 2); lp.rotation.y = sx > 0 ? Math.PI : 0; scene.add(lp); }
    if (i % 2 === 1) { const b = bush(.9, i); b.position.set(sx * 6.4, 0, z - 1); scene.add(b); }
  }
  // distant hills + clouds
  const mHill = toon(0x7cc35f, { rim: .15 });
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; const h = mesh(G.sphere(30 + R() * 18, 24, 12), mHill, Math.cos(a) * 250, -14, Math.sin(a) * 250 - 90, scene); h.scale.set(1.8, .7, 1); }
  for (let i = 0; i < 14; i++) { const c = cloud(i + 3, 2 + R() * 2); c.position.set((R() - .5) * 200, 35 + R() * 25, -40 - R() * 200); scene.add(c); }
  addOutline(scene, .03);
  shadows(scene, true, true); sky.castShadow = sky.receiveShadow = false;
  scene.userData = { sun: L.sun, sky };
  return scene;
}

// ------------------------------------------------------------------ LIVING ROOM (idle)
export function buildLivingRoom() {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x2a2340);
  const L = lights(scene, { sunPos: [-6, 7, 6], sun: 1.5, sunColor: 0xffd6aa, hemi: 1.05, sky: 0xd8d4ff, ground: 0x6a5a60, shadowSize: 9 });
  const floorTex = canvasTex(512, 512, (g) => { for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? '#b07a52' : '#a46f49'; g.fillRect(0, i * 64, 512, 64); g.fillStyle = 'rgba(0,0,0,.18)'; g.fillRect(0, i * 64, 512, 3); for (let k = 0; k < 3; k++) g.fillRect(((i * 197 + k * 170) % 512), i * 64, 3, 64); } });
  floorTex.wrapS = floorTex.wrapT = THREE.RepeatWrapping; floorTex.repeat.set(3, 3);
  const fl = mesh(new THREE.PlaneGeometry(14, 14), toon(0xffffff, { map: floorTex, rim: 0 }), 0, 0, 0, scene); fl.rotation.x = -Math.PI / 2;
  const mWall = toon(0x8e7fb8, { rim: 0 }), mWall2 = toon(0x7a6ca6, { rim: 0 });
  mesh(G.box(14, 6, .2), mWall, 0, 3, -4, scene);
  mesh(G.box(.2, 6, 14), mWall2, -6, 3, 0, scene);
  mesh(G.box(14, .4, .25), toon(0xe9e1ff), 0, .2, -3.85, scene);
  // window with warm evening light
  mesh(G.box(2.6, 2.2, .1), toon(0xffffff), 2.8, 3.1, -3.88, scene);
  const win = mesh(G.box(2.3, 1.9, .12), glow(0xffc27a, 1.6), 2.8, 3.1, -3.87, scene); win.userData.noOutline = true;
  mesh(G.box(.08, 1.9, .14), toon(0xffffff), 2.8, 3.1, -3.85, scene); mesh(G.box(2.3, .08, .14), toon(0xffffff), 2.8, 3.1, -3.85, scene);
  // couch
  const mC = toon(0xe0675a, { rim: .25 }), mC2 = toon(0xc9554a, { rim: .2 });
  const couch = new THREE.Group(); scene.add(couch); couch.position.set(-1, 0, -2.6);
  mesh(roundBox(4.2, .55, 1.5, .15), mC2, 0, .45, 0, couch);
  for (const x of [-1, 1]) mesh(roundBox(1.9, .35, 1.3, .14), mC, x * 1, .85, .08, couch);
  mesh(roundBox(4.2, 1.1, .4, .16), mC, 0, 1.15, -.6, couch);
  for (const x of [-1, 1]) mesh(roundBox(.42, .9, 1.5, .15), mC2, x * 2.15, .8, 0, couch);
  mesh(roundBox(.8, .6, .25, .1), toon(0xf6d36b), -1.4, 1.2, -.25, couch).rotation.z = .3;
  // TV + stand
  mesh(roundBox(2.2, .7, .6, .06), toon(0x5a4a3f), 1.2, .35, 2.6, scene);
  const tv = mesh(roundBox(2.4, 1.4, .12, .05), toon(0x1c1c24), 1.2, 1.5, 2.65, scene); tv.rotation.y = Math.PI;
  const scr = mesh(new THREE.PlaneGeometry(2.2, 1.2), glow(0x7fb8ff, 1.1), 1.2, 1.5, 2.58, scene); scr.rotation.y = Math.PI; scr.userData.noOutline = true;
  // rug, plant, floor lamp
  const rug = mesh(G.cyl(2.2, 2.2, .03, 40), toon(0x57c4b5, { rim: 0 }), -.6, .015, -.2, scene); rug.scale.set(1.3, 1, .8);
  const pot = mesh(G.cyl(.3, .22, .55, 16), toon(0xf2efe9), -5, .28, -3.2, scene);
  for (let i = 0; i < 6; i++) { const lf = mesh(G.sphere(.25, 10, 8), toon(0x4caf50), -5 + Math.cos(i) * .25, .9 + (i % 3) * .2, -3.2 + Math.sin(i) * .25, scene); lf.scale.set(.6, 1.5, .4); lf.rotation.z = Math.cos(i) * .6; }
  mesh(G.cyl(.04, .04, 2.6, 8), toon(0x333333), -3.7, 1.3, -3.2, scene);
  const shade = mesh(G.cyl(.3, .5, .55, 18, 1, true), toon(0xfff1d6, { emissive: 0xffc070, emissiveIntensity: .8, side: THREE.DoubleSide }), -3.7, 2.7, -3.2, scene);
  const pl = new THREE.PointLight(0xffb36b, 6, 9, 1.5); pl.position.set(-3.7, 2.4, -3.0); scene.add(pl);
  // picture frames
  for (const [x, c] of [[-2.2, 0x6fc3df], [-.6, 0xf28fad]]) { mesh(G.box(1, .8, .06), toon(0xffffff), x, 3.4, -3.88, scene); mesh(G.box(.8, .6, .07), toon(c), x, 3.4, -3.87, scene); }
  addOutline(scene, .02); shadows(scene, true, true);
  scene.userData = { sun: L.sun, screen: scr };
  return scene;
}

// ------------------------------------------------------------------ ORGAN CITY (night, wakes up)
export function buildOrganCity(organs) {
  const scene = new THREE.Scene();
  const sky = skyDome(0x0b0a24, 0x2a1d4f, 0x150f30); scene.add(sky);
  scene.fog = new THREE.Fog(0x1b1438, 20, 110);
  const hemi = new THREE.HemisphereLight(0x5a5fb0, 0x201830, .5); scene.add(hemi);
  const moon = new THREE.DirectionalLight(0x9fb4ff, .8); moon.position.set(-10, 20, 10); moon.castShadow = true;
  Object.assign(moon.shadow.camera, { left: -30, right: 30, top: 30, bottom: -30, far: 100 }); moon.shadow.mapSize.set(2048, 2048); moon.shadow.bias = -.0005;
  scene.add(moon);
  const ground = mesh(new THREE.PlaneGeometry(300, 300), toon(0x2b2748, { rim: 0, unique: true }), 0, 0, 0, scene); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true;
  const roads = toon(0x1c1a30, { rim: 0 });
  for (let i = -5; i <= 5; i++) { const r1 = mesh(new THREE.PlaneGeometry(3, 200), roads, i * 12, .01, 0, scene); r1.rotation.x = -Math.PI / 2; r1.receiveShadow = true; const r2 = mesh(new THREE.PlaneGeometry(200, 3), roads, 0, .012, i * 12, scene); r2.rotation.x = -Math.PI / 2; r2.receiveShadow = true; }
  // window texture
  const winTex = canvasTex(128, 256, (g) => { g.fillStyle = '#000'; g.fillRect(0, 0, 128, 256); for (let y = 0; y < 8; y++) for (let x = 0; x < 4; x++) { g.fillStyle = (x * 7 + y * 3) % 5 ? '#ffd890' : '#7fd8ff'; g.fillRect(10 + x * 30, 12 + y * 31, 18, 20); } });
  const R = rng(9); const buildings = [];
  const bodyCols = [0x3c3570, 0x463a7a, 0x34406e, 0x51406f];
  for (let gx = -4; gx < 4; gx++) for (let gz = -4; gz < 4; gz++) {
    const cx = gx * 12 + 6, cz = gz * 12 + 6;
    if (Math.abs(cx) < 13 && Math.abs(cz) < 13) continue; // central plaza
    for (let k = 0; k < 4; k++) {
      const w = 2.5 + R() * 2, d = 2.5 + R() * 2, h = 3 + R() * 9 * (1 - Math.min(1, Math.hypot(cx, cz) / 80) * .5);
      const x = cx + (k % 2 ? 2.4 : -2.4), z = cz + (k > 1 ? 2.4 : -2.4);
      const b = new THREE.Group(); b.position.set(x, 0, z); scene.add(b);
      mesh(G.box(w, h, d), toon(bodyCols[k % 4], { rim: .15 }), 0, h / 2, 0, b);
      const t2 = winTex.clone(); t2.repeat.set(Math.max(1, Math.round(w / 1.2)) / 4, Math.round(h / 1.2) / 8); t2.wrapS = t2.wrapT = THREE.RepeatWrapping; t2.needsUpdate = true;
      const wm = new THREE.MeshBasicMaterial({ map: t2, color: new THREE.Color(0, 0, 0), blending: THREE.AdditiveBlending, transparent: true, depthWrite: false });
      for (const [rx, ry, px, pz, ww] of [[0, 0, 0, d / 2 + .02, w], [0, Math.PI, 0, -d / 2 - .02, w], [0, Math.PI / 2, w / 2 + .02, 0, d], [0, -Math.PI / 2, -w / 2 - .02, 0, d]]) {
        const p = mesh(new THREE.PlaneGeometry(ww * .9, h * .9), wm, px, h / 2, pz, b); p.rotation.y = ry; p.userData.noOutline = true;
      }
      buildings.push({ g: b, wm, dist: Math.hypot(x, z), h });
    }
  }
  // central plaza with organ landmarks on glowing pedestals
  const plaza = mesh(G.cyl(12, 12, .2, 64), toon(0x3a3360, { rim: 0, unique: true }), 0, .1, 0, scene); plaza.receiveShadow = true;
  const ring = mesh(G.torus(11.5, .12, 8, 96), glow(0x6bdcff, .2, { unique: true }), 0, .22, 0, scene); ring.rotation.x = Math.PI / 2; ring.userData.noOutline = true;
  const peds = [];
  organs.forEach((og, i) => {
    const a = i / organs.length * Math.PI * 2 + Math.PI / 2;
    const p = new THREE.Group(); p.position.set(Math.cos(a) * 6.5, 0, Math.sin(a) * 6.5); scene.add(p);
    mesh(G.cyl(1.5, 1.8, 1.2, 32), toon(0x4a4380, { rim: .2 }), 0, .6, 0, p);
    const top = mesh(G.cyl(1.55, 1.55, .08, 32), new THREE.MeshBasicMaterial({ color: 0x000000 }), 0, 1.22, 0, p); top.userData.noOutline = true;
    og.position.y = 2.9; p.add(og);
    const lightP = new THREE.PointLight(og.userData.lightColor ?? 0xff8080, 0, 10, 1.6); lightP.position.set(0, 3, 1.5); p.add(lightP);
    peds.push({ p, og, top, light: lightP });
  });
  addOutline(scene, .025); shadows(scene, true, true); sky.castShadow = false;
  // stars
  const sg = new THREE.BufferGeometry(); const sp = [];
  for (let i = 0; i < 600; i++) { const a = R() * Math.PI * 2, e = .15 + R() * 1.3; sp.push(Math.cos(a) * Math.cos(e) * 300, Math.sin(e) * 300, Math.sin(a) * Math.cos(e) * 300); }
  sg.setAttribute('position', new THREE.Float32BufferAttribute(sp, 3));
  const stars = new THREE.Points(sg, new THREE.PointsMaterial({ color: 0xffffff, size: 1.2, sizeAttenuation: false, fog: false })); scene.add(stars);
  scene.userData = { buildings, peds, ground, ring, hemi, moon, sky, plaza };
  scene.userData.wake = (w, origin = V(0, 0, 0), t = 0) => {
    // w: wave radius; lights turn on as the wave passes
    for (const b of buildings) { const on = smooth((w - b.dist) / 6); b.wm.color.setScalar(.05 + on * 1.6); }
    for (const p of peds) { const on = smooth((w - p.p.position.length()) / 4); p.top.material.color.setRGB(on * 1.2, on * 2.2, on * 2.6); p.light.intensity = on * 30; }
    ring.material.color.setRGB(.42, 1.7, 2.0).multiplyScalar(.1 + smooth((w - 11) / 5) * 1.2);
    const day = smooth((w - 30) / 50);
    hemi.intensity = .5 + day * .5;
  };
  scene.userData.wake(0);
  return scene;
}

// ------------------------------------------------------------------ BEDROOM (night)
export function buildBedroom() {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x141a3a);
  const hemi = new THREE.HemisphereLight(0xa8b8ff, 0x2a2540, 1.1); scene.add(hemi);
  const moon = new THREE.DirectionalLight(0xa8c0ff, 1.4); moon.position.set(5, 6, -2); moon.castShadow = true;
  Object.assign(moon.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8 }); moon.shadow.mapSize.set(2048, 2048); scene.add(moon);
  const fl = mesh(new THREE.PlaneGeometry(14, 14), toon(0x3a3560, { rim: 0 }), 0, 0, 0, scene); fl.rotation.x = -Math.PI / 2;
  mesh(G.box(14, 6, .2), toon(0x2d3a6e, { rim: 0 }), 0, 3, -3.5, scene);
  mesh(G.box(.2, 6, 14), toon(0x27325f, { rim: 0 }), 4.5, 3, 0, scene);
  // window w/ moon
  mesh(G.box(2.2, 2.4, .1), toon(0xdfe6ff), 4.4, 3.3, -.5, scene).rotation.y = Math.PI / 2;
  const w = mesh(G.box(2, 2.2, .1), glow(0x5b78d6, 1.2), 4.38, 3.3, -.5, scene); w.rotation.y = Math.PI / 2; w.userData.noOutline = true;
  const moonM = mesh(G.sphere(.35, 20, 14), glow(0xfff6d8, 3), 4.3, 3.8, -.2, scene); moonM.userData.noOutline = true;
  // bed
  const bed = new THREE.Group(); scene.add(bed); bed.position.set(0, 0, -1.2);
  mesh(roundBox(2.6, .6, 4.2, .12), toon(0x7a5a8a), 0, .3, 0, bed);
  mesh(roundBox(2.4, .35, 4.0, .15), toon(0xf1eefc), 0, .75, 0, bed);
  mesh(roundBox(2.8, 1.8, .25, .1), toon(0x6a4a7a), 0, .9, -2.1, bed);
  const pillow = mesh(roundBox(1.4, .3, .7, .14), toon(0xffffff), 0, 1.05, -1.55, bed);
  const blanket = mesh(roundBox(2.5, .3, 2.7, .14), toon(0x5d8ce8, { rim: .3 }), 0, 1.0, .55, bed);
  // nightstand + lamp
  mesh(roundBox(.8, .9, .7, .06), toon(0x8a6a5a), 1.9, .45, -2.6, scene);
  addOutline(scene, .02); shadows(scene, true, true);
  scene.userData = { bed, blanket, pillow };
  return scene;
}

// ------------------------------------------------------------------ DINING corner (after a meal)
export function buildDining() {
  const scene = buildLivingRoom();
  const table = new THREE.Group(); table.position.set(1.2, 0, .6); scene.add(table);
  mesh(roundBox(2.2, .12, 1.3, .05), toon(0xc58c5c), 0, 1.05, 0, table);
  for (const [x, z] of [[-.95, -.5], [.95, -.5], [-.95, .5], [.95, .5]]) mesh(G.cyl(.05, .05, 1.0, 8), toon(0x8a5a3c), x, .5, z, table);
  mesh(G.cyl(.38, .3, .05, 28), toon(0xffffff), 0, 1.14, 0, table);
  // pasta + bread
  const pasta = mesh(G.sphere(.28, 16, 10), toon(0xf6c453), 0, 1.18, 0, table); pasta.scale.set(1, .35, 1);
  mesh(G.sphere(.08, 10, 8), toon(0xd9433a), .08, 1.27, .05, table); mesh(G.sphere(.06, 10, 8), toon(0xd9433a), -.1, 1.26, -.04, table);
  const bread = mesh(G.capsule(.09, .3, 8), toon(0xd99a50), .6, 1.17, .2, table); bread.rotation.z = Math.PI / 2;
  addOutline(table, .015); shadows(table, true, true);
  scene.userData.table = table; scene.userData.pasta = pasta;
  return scene;
}

// ------------------------------------------------------------------ inner-body tunnels
// Generic organic tunnel along a curve, inner wall shader with peristaltic/pulse waves and a glow
export function tunnel(curve, radius, o = {}) {
  const geo = new THREE.TubeGeometry(curve, o.seg ?? 400, radius, o.rs ?? 40, false);
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: { time: { value: 0 }, col: { value: new THREE.Color(o.color ?? 0xb3202e) }, col2: { value: new THREE.Color(o.color2 ?? 0xff6a70) }, wave: { value: o.wave ?? .06 }, waveSpeed: { value: o.waveSpeed ?? 1 }, wide: { value: 1 }, glowAmt: { value: o.glow ?? 1 }, fogCol: { value: new THREE.Color(o.fog ?? 0x2a0508) }, fogDist: { value: o.fogDist ?? 18 }, villi: { value: o.villi ?? 0 }, squeeze: { value: 0 }, squeezeAt: { value: 0 } },
    vertexShader: `uniform float time, wave, waveSpeed, wide, villi, squeeze, squeezeAt; varying vec2 vUv; varying vec3 vN; varying float vD; varying vec3 vVP;
      void main(){ vUv=uv; vec3 p=position;
        float w=sin(uv.x*120.-time*waveSpeed*6.)*wave + sin(uv.y*6.283*6.+uv.x*40.)*wave*.25;
        float sq = squeeze*exp(-pow((uv.x-squeezeAt)*30.,2.));
        vec3 n=normalize(normal);
        p += n*(w - sq) ; p += n*(wide-1.)*1.0;
        float vl = villi*pow(max(0.,sin(uv.x*900.)*sin(uv.y*6.283*28.)),3.);
        p += n*vl*.25;
        vN=normalMatrix*n; vec4 mv=modelViewMatrix*vec4(p,1.); vVP=mv.xyz; vD=-mv.z; gl_Position=projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 col,col2,fogCol; uniform float time,glowAmt,fogDist; varying vec2 vUv; varying vec3 vN; varying float vD; varying vec3 vVP;
      void main(){ vec3 n=normalize(vN); float fr=1.-abs(dot(n,normalize(-vVP)));
        float stripes=.5+.5*sin(vUv.y*6.283*10.+sin(vUv.x*80.)*1.5);
        float band=smoothstep(.3,.9,stripes);
        vec3 c=mix(col,col2,band*.35+fr*.6);
        c+=col2*pow(fr,3.)*.8*glowAmt;
        float f=1.-exp(-vD/fogDist); c=mix(c,fogCol,f);
        gl_FragColor=vec4(c,1.); }`,
  });
  const m = new THREE.Mesh(geo, mat); m.userData.noOutline = true; m.frustumCulled = false;
  return m;
}
