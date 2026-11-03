// The edit: every shot with absolute times (seconds in the voiceover), set, animation and camera.
import * as THREE from 'three';
import * as C from './core.js';
import { CamPath, V, clamp, smooth, smoother, lerp, range, pulse, easeOut, easeIn, easeInOut, expoOut, expoInOut, backOut, elasticOut, noise1, post, camAt } from './core.js';
import { camera, getSet, puff } from './sets.js';
import * as O from './organs.js';
import { walkPhase } from './character.js';

export const DURATION = 251.0;
export const shots = [];
const sh = (a, b, set, fn, o = {}) => shots.push({ a, b, set, fn, ...o });
const P = (t, p, l, fov = 40, roll = 0) => ({ t, p, l, fov, roll });
const cp = (keys, o) => new CamPath(keys, o);

// ------------------------------------------------------------------ shared per-set updaters
function townBase(S, t, o = {}) {
  const s = S.sam;
  S.elder.root.visible = !!o.elder; S.bench.visible = !!o.elder || !!o.bench;
  S.titleG.visible = !!o.title; S.bulb.visible = false; S.storm.visible = false; S.dust.visible = false;
  s.xray(o.xray ?? 0); s.root.visible = o.sam !== false;
  for (const m of s.legMuscles) m.material.emissiveIntensity = .3;
  ['heart', 'lungs', 'brain', 'gut', 'liver', 'stomach'].forEach((n) => s.glowOrgan(n, 0));
  // sky / time of day: 0 = noon, .5 = sunset, 1 = night
  const tod = o.tod ?? 0;
  const day = new THREE.Color(0x3d8fe8), dusk = new THREE.Color(0xff8a5c), night = new THREE.Color(0x101438);
  const midDay = new THREE.Color(0xbfe2ff), midDusk = new THREE.Color(0xffc48a), midNight = new THREE.Color(0x2a2a5a);
  const k1 = smooth(tod * 2), k2 = smooth(tod * 2 - 1);
  S.sky.material.uniforms.top.value.copy(day).lerp(dusk, k1).lerp(night, k2);
  S.sky.material.uniforms.mid.value.copy(midDay).lerp(midDusk, k1).lerp(midNight, k2);
  S.scene.fog.color.copy(S.sky.material.uniforms.mid.value);
  S.sun.intensity = lerp(2.6, 1.6, k1) * (1 - k2 * .85);
  S.sun.color.setHex(0xfff0dd).lerp(new THREE.Color(0xff9a5a), k1);
  S.scene.children.forEach((c) => { if (c.isHemisphereLight) c.intensity = 1.2 * (1 - k2 * .6); });
  const sunAng = o.sunAng ?? 0;
  S.sky.material.uniforms.sun.value.set(Math.sin(sunAng) * .8 + .3, lerp(.6, .05, k1), -1).normalize();
}
function followSun(S, pos) { S.sun.position.copy(pos).add(V(14, 22, 10)); S.sun.target.position.copy(pos); }
// Sam walking along the left sidewalk toward -z (away) or +z (toward camera)
function walk(char, dist, o = {}) {
  const dir = o.dir ?? -1; const x = o.x ?? -4.2, z0 = o.z0 ?? 0, y = o.y ?? .16;
  let z = z0 + dir * dist; z = ((z + 200) % 230 + 230) % 230 - 200;
  char.root.position.set(x, y, z); char.root.rotation.y = dir < 0 ? Math.PI : 0;
  return V(x, y, z);
}
function samFace(s, t, f = {}) { s.setFace({ eyes: 'open', mouth: 'smallSmile', blink: s.blinkAt(t, 1), ...f }); }

function vesselBase(S, t, o = {}) {
  const sp = o.speed ?? 3, d = o.dist ?? t * sp, L = S.curve.getLength();
  const wide = o.wide ?? 1; S.tun.material.uniforms.wide.value = wide; S.tun.material.uniforms.time.value = t;
  const c = new THREE.Vector3(), tg = new THREE.Vector3(), n = new THREE.Vector3(), b = new THREE.Vector3(), up = V(0, 1, 0);
  for (let i = 0; i < S.N; i++) {
    const cl = S.cells[i];
    let u = (cl.u + d * cl.sp / L) % 1; if (u < 0) u += 1;
    if (u > .98) { S.rbc.setMatrixAt(i, new THREE.Matrix4().makeScale(0, 0, 0)); continue; }
    S.curve.getPointAt(u, c); S.curve.getTangentAt(u, tg); n.crossVectors(tg, up).normalize(); b.crossVectors(n, tg).normalize();
    const r = cl.r * wide;
    O.setInst(S.rbc, i, c.x + n.x * Math.cos(cl.a) * r + b.x * Math.sin(cl.a) * r, c.y + n.y * Math.cos(cl.a) * r + b.y * Math.sin(cl.a) * r, c.z + n.z * Math.cos(cl.a) * r + b.z * Math.sin(cl.a) * r, cl.rx + t * cl.spin, cl.ry + t * .5, 0, 1);
  }
  S.rbc.instanceMatrix.needsUpdate = true;
  const sugarOn = o.sugar ?? 0;
  S.sugar.visible = sugarOn > 0;
  if (sugarOn > 0) {
    for (let i = 0; i < S.NS; i++) {
      const cl = S.sug[i]; let u = (cl.u + d * .9 / L) % 1;
      S.curve.getPointAt(u, c); S.curve.getTangentAt(u, tg); n.crossVectors(tg, up).normalize(); b.crossVectors(n, tg).normalize();
      const k = i / S.NS < sugarOn ? 1 : 0; const r = cl.r * wide;
      O.setInst(S.sugar, i, c.x + n.x * Math.cos(cl.a) * r + b.x * Math.sin(cl.a) * r, c.y + n.y * Math.cos(cl.a) * r + b.y * Math.sin(cl.a) * r, c.z + n.z * Math.cos(cl.a) * r + b.z * Math.sin(cl.a) * r, cl.rx + t, cl.ry + t * .7, 0, k * (o.sugarScale ?? 1));
    }
    S.sugar.instanceMatrix.needsUpdate = true;
  }
  for (const v of S.valves) { const open = o.valve ?? 1; v.flaps.forEach((f, j) => { f.rotation.x = (j ? -1 : 1) * lerp(0, 1.25, open); }); v.g.visible = o.valves !== false; }
  S.immune.forEach((m) => m.visible = false); S.keys.forEach((k) => k.visible = false);
  S.hemi.color.setHex(o.hemiCol ?? 0xffd0d0); S.hemi.intensity = o.light ?? 1.4;
  return d;
}
// camera riding inside the vessel at distance dc along the curve
function vesselCam(S, dc, t, o = {}) {
  const L = S.curve.getLength(); const u = clamp(dc / L, 0, .97), u2 = clamp((dc + (o.lookAhead ?? 6)) / L, 0, .99);
  const p = S.curve.getPointAt(u), l = S.curve.getPointAt(u2);
  const tg = S.curve.getTangentAt(u), n = new THREE.Vector3().crossVectors(tg, V(0, 1, 0)).normalize(), b = new THREE.Vector3().crossVectors(n, tg);
  const off = o.off ?? [0, 0]; p.addScaledVector(n, off[0]).addScaledVector(b, off[1]);
  l.addScaledVector(n, off[0] * .4).addScaledVector(b, off[1] * .4);
  p.x += noise1(t * .8) * .08; p.y += noise1(t * .7 + 4) * .08;
  camera.position.copy(p); camera.up.set(0, 1, 0); camera.lookAt(l); camera.rotateZ((o.roll ?? 0) + noise1(t * .3) * .05);
  camera.fov = o.fov ?? 62; camera.updateProjectionMatrix();
  post.focus.value = o.focus ?? 5; post.aperture.value = o.aperture ?? .006;
}

function heartBase(S, t, o = {}) {
  const beat = S.heart.userData.beat(o.bt ?? t, o.bpm ?? 60, o.amp ?? 1);
  S.heart.scale.setScalar(o.scale ?? 1);
  S.ring.visible = false; S.rbc.visible = false;
  S.key.intensity = o.key ?? 2.2; S.back.intensity = (o.back ?? 30) * (1 + beat * .6);
  S.hemi.intensity = o.hemi ?? .9;
  S.bokeh.position.y = Math.sin(t * .2) * .3; S.bokeh.rotation.y = t * .02;
  return beat;
}
function rbcBurst(S, tb, k = 1) {
  // tb: time since burst; particles shoot from aorta top
  S.rbc.visible = tb >= 0 && tb < 2.5;
  if (!S.rbc.visible) return;
  const R = C.rng(5);
  for (let i = 0; i < 220; i++) {
    const d = V(R() - .5, 1.2 + R(), R() - .5).normalize(); const sp = (2 + R() * 4) * k;
    const tt = tb * (1 - .15 * tb);
    const p = V(-.3, 2.1, -.2).addScaledVector(d, sp * tt * .8); p.y -= 1.2 * tt * tt;
    const s = clamp(tb * 6) * (1 - smooth((tb - 1.6) / .9));
    O.setInst(S.rbc, i, p.x, p.y, p.z, R() * 6 + tb * 3, R() * 6 + tb * 2, 0, s);
  }
  S.rbc.instanceMatrix.needsUpdate = true;
}

function brainBase(S, t, o = {}) {
  const st = o.streams ?? 0;
  S.cortexMat.emissive.setHex(0xff4f80); S.cortexMat.emissiveIntensity = o.glow ?? 0;
  S.cortexMat.transparent = (o.cortexOp ?? 1) < 1; S.cortexMat.opacity = o.cortexOp ?? 1; S.cortexMat.depthWrite = (o.cortexOp ?? 1) > .9;
  S.hip.visible = (o.hip ?? 0) > 0; S.hip.children.forEach((m) => m.material.color.setRGB(1.6, 1.2, .35).multiplyScalar(.4 + (o.hip ?? 0)));
  S.brain.rotation.y = o.rotY ?? t * .05;
  S.blood.visible = S.oxy.visible = st > 0;
  if (st > 0) {
    const c = new THREE.Vector3();
    for (let i = 0; i < Math.max(S.NB, S.NO); i++) {
      const b = S.bp[i]; const u = (b.u + t * .22 * b.sp) % 1; S.streams[b.s].getPointAt(u, c); c.add(b.o);
      const vis = (i / S.NB) < st ? 1 : 0; const fade = smooth(u * 8) * (1 - smooth((u - .85) / .15));
      if (i < S.NB) O.setInst(S.blood, i, c.x * 1.6, c.y * 1.6, c.z * 1.6, t + i, t * .7, 0, vis * fade * 1.6);
      if (i < S.NO) O.setInst(S.oxy, i, c.x * 1.6 + .2, c.y * 1.6, c.z * 1.6 - .1, 0, 0, 0, vis * fade * 1.6);
    }
    S.blood.instanceMatrix.needsUpdate = true; S.oxy.instanceMatrix.needsUpdate = true;
  }
  const fog = o.fog ?? 0;
  S.fogs.forEach((f, i) => { f.visible = fog > 0.01; f.material.opacity = .5 * fog; f.position.copy(f.userData.home).multiplyScalar(1.6 * (1 + (1 - fog) * 1.5)); f.material.rotation = t * .1 + i; });
  const sk = o.sparks ?? 0; S.sparks.visible = sk > 0;
  if (sk > 0) { for (let i = 0; i < S.NS; i++) { const s = S.sp[i]; const ph = (s.ph + t * s.sp * .5) % 1; const r = 1.6 * (1.1 + ph * 1.2); O.setInst(S.sparks, i, s.n.x * r * .9, s.n.y * r * .75, s.n.z * r * 1.1, 0, 0, 0, (i / S.NS < sk ? 1 : 0) * Math.sin(ph * Math.PI) * 1.5); } S.sparks.instanceMatrix.needsUpdate = true; }
  S.shield.material.opacity = (o.shield ?? 0) * .5; S.shield.scale.setScalar(1.6 * (1 + .03 * Math.sin(t * 3))); S.shield.rotation.y = t * .3;
  S.key.intensity = o.key ?? 2.0;
}

function metaBase(S, t, o = {}) {
  S.mF.emissiveIntensity = o.muscleGlow ?? 0;
  // capillary flow
  for (let i = 0; i < S.NR; i++) { const r = S.rc[i]; const x = ((r.x + t * 2.2 + 8) % 16) - 8; O.setInst(S.rbc, i, x, 4.2 + Math.cos(r.a) * r.r, -2 + Math.sin(r.a) * r.r, r.rx + t, Math.PI / 2, 0, 1); }
  S.rbc.instanceMatrix.needsUpdate = true;
  const pull = o.pull ?? 0; // 0 = sugar in capillary, 1 = fully absorbed into doors
  for (let i = 0; i < S.NS; i++) {
    const g = S.sg[i]; const door = S.doors[g.door];
    const xCap = ((g.x + t * 2.2 + 7) % 14) - 7;
    const local = clamp(pull * 1.6 - (i / S.NS) * .6);
    const target = V(door.position.x, door.position.y - .2, door.position.z - 2).add(V(0, -.2, 0));
    const p0 = V(xCap, 4.2 + Math.cos(g.a) * g.r, -2 + Math.sin(g.a) * g.r);
    const k = easeInOut(local);
    const p = p0.clone().lerp(target, k); p.y += Math.sin(k * Math.PI) * .8;
    const s = (1 - smooth((local - .85) / .15)) * (o.sugar ?? 1);
    O.setInst(S.sugar, i, p.x, p.y, p.z, t + i, t * .6 + i, 0, s);
  }
  S.sugar.instanceMatrix.needsUpdate = true;
  S.doors.forEach((d, i) => { const op = o.doors ?? 0; d.userData.lid.position.x = op * .3; d.children[0].material.emissive?.setHex?.(0x2080c0); });
  S.keys.forEach((k) => k.visible = false);
  S.pancreas.visible = !!o.pancreas; S.liver.visible = !!o.liver; S.muscle.visible = o.muscle !== false; S.cap.visible = o.muscle !== false;
  S.rbc.visible = S.sugar.visible = o.muscle !== false || !!o.liverSugar;
}

function townCamFollow(S, path, lt, base) { const r = path.apply(camera, lt, base); post.focus.value = r.dist; return r; }

function stageBase(S, o = {}) {
  ['graph', 'gauge', 'clock', 'counter', 'gym'].forEach((k) => S[k].visible = !!o[k]);
  S.kcal.visible = !!o.kcal; S.minTxt.visible = !!o.minTxt; S.flames.visible = !!o.flames; S.blocks.visible = !!o.blocks; S.sam.root.visible = !!o.sam;
}
function graphLine(S, morph, draw = 1, col = 0xff4d5a) {
  const pts = []; const n = 120;
  for (let i = 0; i <= n * draw; i++) {
    const x = i / n; const spike = 3.3 * Math.exp(-Math.pow((x - .32) / .09, 2)) + .5;
    const flat = 1.25 * Math.exp(-Math.pow((x - .45) / .3, 2)) + .5;
    pts.push(V(-4 + x * 8.2, lerp(spike, flat, morph), 0));
  }
  if (pts.length < 2) pts.push(pts[0].clone().add(V(.01, 0, 0)));
  const g = S.graph.userData;
  g.ribbon.geometry.dispose(); g.ribbon.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), Math.max(4, pts.length * 2), .07, 8, false);
  g.ribbon.material.color.setHex(col).multiplyScalar(1.15);
  // area under curve
  const pos = []; for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1]; pos.push(a.x, .05, 0, b.x, .05, 0, b.x, b.y, 0, a.x, .05, 0, b.x, b.y, 0, a.x, a.y, 0); }
  g.area.geometry.dispose(); g.area.geometry = new THREE.BufferGeometry(); g.area.geometry.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.area.material.color.setHex(col);
  g.dot.position.copy(pts[pts.length - 1]);
}

function lungsBase(S, t, o = {}) {
  S.lungs.visible = !o.xray; S.lungsX.visible = !!o.xray;
  const br = Math.sin(t * Math.PI * 2 / (o.period ?? 4)) * .5 + .5;
  (o.xray ? S.lungsX : S.lungs).userData.breathe(br * (o.depth ?? .5));
  S.air.visible = !!o.air; S.tipGlow.visible = !!o.xray;
}

// ================================================================== SHOTS

// 0.0 – 5.9  TITLE: letters slam down in slow motion, Sam walks toward camera, x-ray reveal
sh(0, 5.85, 'town', (S, lt, t) => {
  townBase(S, t, { title: true, xray: smooth(range(lt, 2.75, 3.4)) });
  // time remap: slow-mo until 1.5s then ramps to real time
  const at = lt < 1.4 ? lt * .32 : lt < 2.2 ? 1.4 * .32 + (lt - 1.4) * .32 + .68 * (lt - 1.4) * (lt - 1.4) / 1.6 : 1.4 * .32 + .8 * .32 + .68 * .8 * .8 / 1.6 + (lt - 2.2);
  const s = S.sam; const dist = at * 1.25;
  const pos = walk(s, dist, { x: .9, z0: -9.5, dir: 1 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, at); samFace(s, at, { mouth: lt > 3 ? 'smile' : 'smallSmile', look: [0, .1] });
  // title letters slam
  const L = S.title.userData.letters, SL = S.steps.userData.letters;
  S.title.position.set(0, 1.75, 0); S.steps.position.set(0, 0, 1.6);
  const lands = [0.0, 0.12, 0.24, 0.36, 0.48];
  L.forEach((m, i) => { const tl = (at - lands[i] * .32 + .25) / .25; const k = easeIn(clamp(tl)); m.position.y = (1 - k) * 14; m.rotation.x = (1 - k) * -.6; m.scale.setScalar(1 + .12 * Math.exp(-Math.max(0, tl - 1) * 9) * (tl > 1 ? Math.sin((tl - 1) * 20) : 0)); });
  SL.forEach((m, i) => { const k = backOut(range(lt, .8 + i * .07, 1.25 + i * .07)); m.position.y = (1 - k) * -2.2; m.scale.setScalar(Math.max(.001, k)); });
  // dust at feet on landings
  const shakeT = lands.map((l) => lt - l).filter((x) => x >= 0 && x < .5);
  const shake = shakeT.length ? Math.exp(-shakeT[shakeT.length - 1] * 8) * .08 : 0;
  // organs light up in sequence on "every organ inside you"
  s.glowOrgan('heart', pulse(lt, 3.3, 5.9, .2)); s.glowOrgan('lungs', pulse(lt, 3.7, 5.9, .2)); s.glowOrgan('brain', pulse(lt, 4.1, 5.9, .2)); s.glowOrgan('gut', pulse(lt, 4.5, 5.9, .2)); s.glowOrgan('liver', pulse(lt, 4.5, 5.9, .2));
  s.organs.heart.userData.beat(t, 70, 1);
  const path = cp([P(0, [2.2, .35, 4.5], [0, 2.6, -9], 74), P(1.9, [2.0, .55, 3.9], [.3, 2.4, -7], 70), P(3.0, [1.6, 1.4, 1.2 + pos.z * 0], [.9, 1.5, pos.z], 48), P(5.85, [-.6, 1.75, pos.z + 3.4], [.9, 1.55, pos.z], 38)], { shake: .03 });
  const r = path.apply(camera, lt);
  camera.position.y += (Math.random() * 0) + noise1(t * 40) * shake; camera.position.x += noise1(t * 37 + 3) * shake;
  post.focus.value = lt < 2.4 ? 9 : r.dist; post.aperture.value = lt < 2.4 ? .004 : .008;
  post.fade.value = 1 - smooth(range(lt, 0, .35));
}, { tout: 'whip' });

// 5.9 – 10.3  BULLET TIME orbit around frozen x-ray Sam
sh(5.85, 10.25, 'town', (S, lt, t) => {
  townBase(S, t, { xray: 1 });
  const s = S.sam; const pos = walk(s, 0, { x: .9, z0: -2.8, dir: 1 }); followSun(S, pos);
  s.pose({ walk: 1.1, walkAmt: 1 }, 0); samFace(s, 0, { mouth: 'smile', look: [0, .1] });
  const hq = pulse(lt, .3, 2.9, .3);
  s.glowOrgan('heart', pulse(lt, .2, 1.4, .2) + pulse(lt, 2.6, 3.6, .25) * 1.4); s.glowOrgan('lungs', pulse(lt, .6, 1.8, .2)); s.glowOrgan('gut', pulse(lt, 1.0, 2.2, .2)); s.glowOrgan('liver', pulse(lt, 1.0, 2.2, .2)); s.glowOrgan('brain', pulse(lt, 1.4, 2.6, .2) + pulse(lt, 3.3, 4.4, .2) * .6);
  s.organs.heart.userData.beat(t * .15, 70, 1);
  const a0 = -.5, a1 = Math.PI * 1.15; const a = lerp(a0, a1, easeInOut(lt / 4.4));
  const R = 3.3 - .6 * smooth(lt / 4.4);
  camera.position.set(pos.x + Math.sin(a) * R, 1.55 + .5 * Math.sin(lt * .8), pos.z + Math.cos(a) * R);
  camera.lookAt(pos.x, 1.45, pos.z); camera.fov = 38; camera.updateProjectionMatrix();
  post.focus.value = R; post.aperture.value = .012;
  // dust frozen in air
  S.dust.visible = true; S.dust.position.set(pos.x - .1, .12, pos.z - .35); S.dust.scale.setScalar(.35); S.dust.userData.at(.3);
  post.sat.value = 1.0; post.tint.value.set(.95, 1.0, 1.08);
}, { tin: 'whip', tout: 'dip' });

// 10.3 – 12.5  LIVING ROOM, idle on the couch
sh(10.25, 12.5, 'living', (S, lt, t) => {
  const s = S.sam; s.root.position.set(-1, .18, -2.35); s.root.rotation.y = 0;
  s.pose({ sit: 1, slump: 1, breathe: .6 }, t); s.setFace({ eyes: 'sleepy', mouth: lt > 1.2 ? 'yawn' : 'flat', blink: 0 });
  S.screen.material.color.setRGB(.5, .75, 1.1).multiplyScalar(.9 + .3 * Math.sin(t * 13) * Math.sin(t * 5));
  S.doorLight.visible = false; S.doorPivot.rotation.y = 0;
  const path = cp([P(0, [1.6, 1.3, 2.4], [-1, 1.5, -2.2], 40), P(2.25, [.7, 1.55, .6], [-1, 1.75, -2.2], 34)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .012;
  post.sat.value = .82; post.tint.value.set(1.05, .95, 1.0); post.exposure.value = .92;
  post.fade.value = 1 - smooth(range(lt, 0, .25));
});

// 12.5 – 14.0  lazy heart
sh(12.5, 14.0, 'heart', (S, lt, t) => {
  heartBase(S, t, { bpm: 42, amp: .6, key: 1.0, back: 10, hemi: .5 });
  const path = cp([P(0, [2.2, .8, 6.4], [0, .9, 0], 34), P(1.5, [1.7, .7, 5.6], [0, .9, 0], 34)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
  post.sat.value = .55; post.exposure.value = .8; post.tint.value.set(.95, .95, 1.05);
}, { tin: 'cut' });

// 14.0 – 15.3  slow blood
sh(14.0, 15.3, 'vessel', (S, lt, t) => {
  const d = vesselBase(S, t, { dist: 20 + lt * .5, light: .8 });
  vesselCam(S, 14 + lt * .4, t, { fov: 55, off: [.4, -.3] });
  post.sat.value = .55; post.exposure.value = .85;
});

// 15.3 – 17.3  muscles half asleep
sh(15.3, 17.3, 'legpump', (S, lt, t) => {
  S.musL.userData.squeeze(.05 + .05 * Math.sin(t * 1.2)); S.musR.userData.squeeze(.05 + .05 * Math.sin(t * 1.2 + 1));
  S.arrow.visible = false; S.back.intensity = 8;
  for (let i = 0; i < S.N; i++) { const c = S.cells[i]; O.setInst(S.rbc, i, Math.cos(c.a) * c.r, c.y + t * .05, Math.sin(c.a) * c.r, c.rx, c.ry, 0, 1); } S.rbc.instanceMatrix.needsUpdate = true;
  const path = cp([P(0, [-3.2, 2.2, 3.0], [-1.4, .3, 0], 38), P(2, [-2.3, 1.2, 3.4], [-1.2, .1, 0], 38)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
  post.sat.value = .55; post.exposure.value = .75;
});

// 17.3 – 21.0  dim organ city, drone descends
sh(17.3, 21.0, 'city', (S, lt, t) => {
  S.scene.userData.wake(0); S.wave.visible = false;
  S.faces.forEach((f, i) => f.userData.set({ eyes: (i + Math.floor(t * .7)) % 4 === 0 ? 'closed' : 'sleepy', mouth: 'flat' }));
  S.wrap.forEach((w, i) => { w.rotation.y = Math.PI / 2 - (i / 6 * Math.PI * 2 + Math.PI / 2) + Math.PI / 2 + 0; w.lookAt(0, 2.9, 0); w.rotateY(Math.PI); w.position.y = 2.9 + Math.sin(t * .8 + i) * .05; });
  S.heart.userData.beat(t, 40, .5);
  const path = cp([P(0, [30, 34, 34], [0, 0, 0], 40), P(3.7, [11, 7.5, 14], [0, 2.6, 0], 40)], { shake: .05, ease: easeInOut });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .006;
  post.bloom.value = .6; C.setBloomThreshold(.8);
}, { tin: 'dip' });

// 21.0 – 22.4  Sam stands up
sh(21.0, 22.45, 'living', (S, lt, t) => {
  const s = S.sam; const k = easeInOut(range(lt, .25, .9));
  s.root.position.set(-1, .18 - .02 * k, lerp(-2.35, -1.8, k)); s.root.rotation.y = 0;
  s.pose({ sit: 1 - k, slump: 1 - k, lean: .35 * Math.sin(k * Math.PI) }, t); s.setFace({ eyes: k > .5 ? 'open' : 'half', brow: k > .5 ? 'raised' : 'none', mouth: k > .5 ? 'smallSmile' : 'flat', blink: s.blinkAt(t) });
  S.screen.material.color.setRGB(.5, .75, 1.1);
  S.doorLight.visible = false; S.doorPivot.rotation.y = 0;
  const path = cp([P(0, [2.6, .6, 2.6], [-1, 1.4, -2.2], 46), P(1.45, [2.3, .9, 2.0], [-1, 2.1, -1.8], 46)], { shake: .03 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
  post.exposure.value = .95;
}, { tin: 'cut' });

// 22.4 – 23.4  first step, super slow motion, floor shockwave
sh(22.45, 23.4, 'living', (S, lt, t) => {
  const s = S.sam; s.root.position.set(-1, .16, -1.4); s.root.rotation.y = 0;
  const ph = lerp(-.4, .05, easeOut(lt / .95));
  s.pose({ walk: ph * 2.2 + .2, walkAmt: 1 }, t); samFace(s, t);
  S.doorLight.visible = false;
  if (!S.ringFx) { S.ringFx = new THREE.Mesh(new THREE.RingGeometry(.9, 1, 64), C.glow(0x8fe6ff, 2.5, { transparent: true, additive: true, side: THREE.DoubleSide })); S.ringFx.rotation.x = -Math.PI / 2; S.ringFx.position.y = .03; S.scene.add(S.ringFx); }
  const kk = range(lt, .55, .95); S.ringFx.visible = kk > 0; S.ringFx.scale.setScalar(.2 + kk * 3.5); S.ringFx.material.opacity = 1 - kk; S.ringFx.position.set(-.9, .03, -1.2);
  const path = cp([P(0, [.2, .22, .6], [-1, .3, -1.4], 52), P(.95, [.05, .2, .35], [-1, .25, -1.4], 50)], { shake: .01 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .02;
  post.exposure.value = 1.0;
}, { tin: 'cut', tout: 'flash' });

// 23.4 – 25.5  CITY WAKES UP
sh(23.4, 25.5, 'city', (S, lt, t) => {
  const w = expoOut(range(lt, 0, 1.9)) * 85; S.scene.userData.wake(w);
  S.wave.visible = true; S.wave.scale.setScalar(Math.max(.1, w)); S.wave.material.opacity = 1 - range(lt, 0, 1.9);
  S.faces.forEach((f, i) => { const on = w > 7; f.userData.set(on ? { eyes: lt > 1.3 ? 'happy' : 'wide', mouth: lt > 1.3 ? 'grin' : 'o', brow: 'raised' } : { eyes: 'sleepy', mouth: 'flat' }); });
  S.wrap.forEach((w2, i) => { w2.lookAt(0, 2.9, 0); w2.rotateY(Math.PI); w2.position.y = 2.9 + Math.sin(t * 3 + i) * .08 + .4 * backOut(range(lt, .15 + i * .05, .6 + i * .05)) - .0; });
  S.heart.userData.beat(t, 80, 1.2);
  const path = cp([P(0, [5, 2.2, 9], [0, 3, 0], 50), P(.9, [8, 6, 13], [0, 2.5, 0], 52), P(2.1, [18, 20, 24], [0, 0, -2], 52)], { shake: .06, ease: easeInOut });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .006;
  post.bloom.value = .75; C.setBloomThreshold(.75);
}, { tin: 'flash', tout: 'whip' });

// 25.5 – 28.0  legs go first: low side tracking on sidewalk
sh(25.5, 28.0, 'town', (S, lt, t) => {
  townBase(S, t, {}); const s = S.sam; const dist = (t - 25.5) * 1.45 + 2;
  const pos = walk(s, dist, { z0: 0 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); samFace(s, t, { mouth: 'smile' });
  const path = cp([P(0, [1.6, .35, 1.2], [0, .55, -.2], 50), P(2.5, [1.3, .45, -.4], [0, .6, -.8], 46)], { shake: .02 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .012;
}, { tin: 'whip' });

// 28.0 – 32.0  x-ray legs: calves + thighs squeeze & release
sh(28.0, 32.1, 'town', (S, lt, t) => {
  townBase(S, t, { xray: smooth(range(lt, 0, .5)) }); const s = S.sam; const dist = (t - 25.5) * 1.35 + 2;
  const pos = walk(s, dist, { z0: 0 }); followSun(S, pos);
  const ph = walkPhase(dist); s.pose({ walk: ph, walkAmt: 1 }, t); samFace(s, t);
  const sq = (x) => pulse(t, x, x + .75, .12);
  const em = .4 + 1.8 * Math.max(sq(28.9), sq(30.4)) + .5 * (.5 + .5 * Math.sin(ph * 2));
  s.legMuscles.forEach((m, i) => { const leg = Math.floor(i / 2); const stance = .5 + .5 * Math.sin(ph + (leg ? Math.PI : 0)); m.material.emissiveIntensity = em * (.4 + .6 * stance); m.scale.x = (i % 2 ? .075 : .085) * (1 + .25 * stance * em / 2); m.scale.z = m.scale.x * 1.05; });
  const path = cp([P(0, [1.7, .7, .8], [0, .75, 0], 44), P(4.1, [1.35, .85, -.8], [0, .8, -.2], 40)], { shake: .02 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .012;
}, { tin: 'cut', tout: 'zoom' });

// 32.0 – 36.0  dive into the vein: flying up with the blood, valves open
sh(32.1, 36.0, 'vessel', (S, lt, t) => {
  const dc = 4 + lt * 7 + lt * lt * .6;
  const d = vesselBase(S, t, { dist: dc * 1.0 + 6, valve: 1, light: 1.5 });
  S.valves.forEach((v) => { const L = S.curve.getLength(); const dd = v.u * L - dc; const open = smooth(1 - dd / 12); v.flaps.forEach((f, j) => f.rotation.x = (j ? -1 : 1) * lerp(.15, 1.3, open)); });
  vesselCam(S, dc, t, { fov: 66, roll: lt * .08 });
  post.zoomBlur.value = .04 * (1 - smooth(lt / .6));
}, { tin: 'zoom' });

// 36.0 – 39.5  fighting gravity (cut-away vein, slow)
sh(36.0, 39.5, 'legpump', (S, lt, t) => {
  S.musL.userData.squeeze(.1); S.musR.userData.squeeze(.1);
  S.arrow.visible = lt > .6; S.arrow.scale.setScalar(backOut(range(lt, .6, 1.1)) || .001); S.arrow.position.y = 1 - (lt * .3) % .6;
  S.back.intensity = 25;
  for (let i = 0; i < S.N; i++) { const c = S.cells[i]; const y = c.y + Math.sin(t * 1.6 + c.rx) * .25 - .1 * lt; O.setInst(S.rbc, i, Math.cos(c.a) * c.r, y, Math.sin(c.a) * c.r, c.rx + t * .3, c.ry, 0, 1); }
  S.rbc.instanceMatrix.needsUpdate = true;
  S.valves.forEach((v) => v.fl.forEach((f, j) => f.rotation.z = (j ? -1 : 1) * .2 * Math.sin(t * 2)));
  const path = cp([P(0, [0, -4.5, 6], [0, 0, 0], 40), P(3.5, [1.2, -2.5, 5.2], [0, .5, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
}, { tin: 'whip' });

// 39.5 – 44.3  second pump: muscles squeeze vein, blood shoots upward
sh(39.5, 44.3, 'legpump', (S, lt, t) => {
  const hits = [40.75, 41.7, 42.75, 43.55];
  let sq = 0; for (const h of hits) sq = Math.max(sq, Math.exp(-Math.pow((t - h - .12) / .18, 2)));
  S.musL.userData.squeeze(.1 + sq * .9); S.musR.userData.squeeze(.1 + sq * .9);
  S.vein.scale.set(1 - sq * .45, 1, 1 - sq * .45);
  S.arrow.visible = false; S.back.intensity = 25 + sq * 40;
  let push = 0; for (const h of hits) push += smooth((t - h) / .5) * 2.4;
  for (let i = 0; i < S.N; i++) { const c = S.cells[i]; let y = ((c.y + push + 7) % 14) - 7; O.setInst(S.rbc, i, Math.cos(c.a) * c.r * (1 - sq * .4), y, Math.sin(c.a) * c.r * (1 - sq * .4), c.rx + t, c.ry, 0, 1); }
  S.rbc.instanceMatrix.needsUpdate = true;
  S.valves.forEach((v) => v.fl.forEach((f, j) => f.rotation.z = (j ? -1 : 1) * (.2 + sq * 1.2)));
  const path = cp([P(0, [4.5, 1, 5], [0, 0, 0], 44), P(2.3, [-2, 2.5, 5.6], [0, .8, 0], 44), P(4.8, [-4.5, -1, 3.5], [0, .5, 0], 46)], { shake: .03 });
  const r = path.apply(camera, lt); camera.position.x += noise1(t * 30) * sq * .05;
  post.focus.value = r.dist; post.aperture.value = .008;
}, { tin: 'cut' });

// 44.3 – 47.0  "calves = second heart": tiny heart beating on the x-ray calf
sh(44.3, 47.0, 'town', (S, lt, t) => {
  townBase(S, t, { xray: 1 }); const s = S.sam; const dist = (t - 44.3) * 1.1 + 30;
  const pos = walk(s, dist, { z0: 0 }); followSun(S, pos); const ph = walkPhase(dist);
  s.pose({ walk: ph, walkAmt: 1 }, t); samFace(s, t);
  if (!S.calfHeart) { S.calfHeart = O.makeHeart({ outline: false }); S.calfHeart.traverse((m) => { if (m.isMesh) m.material = C.toon(m.material.color.getHex(), { unique: true, emissive: 0x801020, emissiveIntensity: .9, rim: .8 }); }); s.knee[1].add(S.calfHeart); S.calfHeart.position.set(0, -.17, -.12); }
  const hk = backOut(range(t, 45.9, 46.4)); S.calfHeart.visible = hk > 0; S.calfHeart.scale.setScalar(Math.max(.001, .055 * hk)); S.calfHeart.userData.beat(t, 90, 1.5);
  s.legMuscles.forEach((m, i) => m.material.emissiveIntensity = .6 + (i === 3 ? 1.5 * hk : 0) + .4 * Math.sin(t * 9));
  const path = cp([P(0, [-1.2, .55, .2], [0, .5, 0], 34), P(2.7, [-1.0, .45, -.9], [0, .45, -.1], 30)], { shake: .02 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .014;
}, { tin: 'cut' });

// 47.0 – 49.5  whip tilt from calf up to the real heart, which notices
sh(47.0, 49.5, 'town', (S, lt, t) => {
  townBase(S, t, { xray: 1 }); const s = S.sam; const dist = (t - 44.3) * 1.1 + 30;
  const pos = walk(s, dist, { z0: 0 }); followSun(S, pos); s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); samFace(s, t, { look: [0, -.2] });
  s.glowOrgan('heart', smooth(range(t, 47.8, 48.3)) * (1.2 + .4 * Math.sin(t * 8)));
  s.organs.heart.userData.beat(t, 60 + 30 * smooth(range(t, 48, 49.5)), 1.6);
  if (S.calfHeart) S.calfHeart.visible = false;
  const path = cp([P(0, [-1.4, .5, -.4], [0, .45, 0], 32), P(.75, [-1.5, 1.35, -.6], [0, 1.25, 0], 30), P(2.5, [-1.15, 1.35, -.9], [0, 1.27, 0], 26)], { shake: .02, ease: expoInOut });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .014;
});

// 49.5 – 54.3  heart speeds up — gentle, steady
sh(49.5, 54.3, 'heart', (S, lt, t) => {
  const bpm = lerp(62, 98, smooth(range(t, 50.2, 51.2)));
  // integrate beat phase for smooth tempo change
  const bt = t * 62 / 60 + (bpm > 62 ? (bpm - 62) / 60 * (t - 50.7) : 0);
  heartBase(S, t, { bt: bt * 60 / bpm, bpm, amp: 1.2, key: 2.4, back: 35 });
  const path = cp([P(0, [3.6, 1.6, 5.2], [0, .9, 0], 36), P(4.8, [-2.8, 1.0, 5.6], [0, 1.0, 0], 34)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .012;
  post.tint.value.set(1.05, 1.0, .96);
}, { tin: 'cut' });

// 54.3 – 58.2  vessels relax and widen, flow becomes easy
sh(54.3, 58.2, 'vessel', (S, lt, t) => {
  const wide = 1 + .45 * smooth(range(t, 55.1, 56.2));
  const sp = lerp(2, 7, smooth(range(t, 56.6, 57.6)));
  const dist = 40 + lt * 2 + Math.max(0, t - 56.6) * 5 * smooth(range(t, 56.6, 57.6));
  vesselBase(S, t, { dist, wide, light: 1.4 + (wide - 1) });
  vesselCam(S, 30 + lt * 1.6, t, { fov: 60 + (wide - 1) * 10, off: [0, 0] });
}, { tin: 'whip' });

// 58.2 – 61.0  pressure drops (gauge)
sh(58.2, 61.0, 'stage', (S, lt, t) => {
  stageBase(S, { gauge: true });
  const v = lerp(.86, .2, easeInOut(range(t, 59.4, 60.6)));
  S.gauge.userData.needle.rotation.z = Math.PI / 2 - v * Math.PI + Math.sin(t * 20) * .01 * (1 - range(t, 59.4, 60.6));
  S.gauge.position.set(0, 2.6, 0); S.gauge.rotation.set(0, 0, 0);
  const path = cp([P(0, [1.6, 2.2, 7.5], [0, 2.4, 0], 38), P(2.8, [.5, 2.6, 6.2], [0, 2.4, 0], 38)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
}, { tin: 'cut' });

// 61.0 – 62.4  every day: timelapse walk (sun races across the sky)
sh(61.0, 62.45, 'town', (S, lt, t) => {
  const tod = (lt / 1.45 * 1.6) % 1.0; const night = Math.sin(lt / 1.45 * Math.PI * 1.6) ;
  townBase(S, t, { tod: Math.abs(Math.sin(lt * 2.2)) * .9, sunAng: lt * 4 });
  const s = S.sam; const dist = lt * 6; const pos = walk(s, dist, { z0: -20 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist) * .25, walkAmt: 1 }, t); samFace(s, t, { mouth: 'smile' });
  S.sun.position.copy(pos).add(V(Math.cos(lt * 4) * 20, 18, Math.sin(lt * 4) * 20));
  const path = cp([P(0, [5, 6, 6], [0, 1, -2], 50), P(1.45, [5.5, 6.5, -2], [0, 1, -6], 50)], { shake: .01 });
  const r = path.apply(camera, lt, V(-4.2, 0, -20)); post.focus.value = 9; post.aperture.value = .003;
}, { tin: 'whip' });

// 62.4 – 64.4  heart grows stronger
sh(62.45, 64.45, 'heart', (S, lt, t) => {
  const g = smooth(range(t, 63.05, 63.8));
  heartBase(S, t, { bpm: 72, amp: 1.2, scale: 1 + .16 * g, key: 2.4 + g, back: 30 + 30 * g });
  S.heart.traverse((m) => { if (m.isMesh && m.material.isMeshToonMaterial) m.material.emissiveIntensity = 1; });
  S.ring.visible = true; const rk = range(t, 63.4, 64.4); S.ring.scale.setScalar(.6 + rk * 1.4); S.ring.material.opacity = Math.sin(rk * Math.PI); S.ring.position.set(0, .8, 0);
  S.ring.lookAt(camera.position);
  const path = cp([P(0, [0, -.6, 6.6], [0, 1.0, 0], 36), P(2, [0, -.9, 5.6], [0, 1.2, 0], 38)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .012;
  post.bloom.value = .45 + g * .3;
}, { tin: 'flash' });

// 64.4 – 70.6  stronger heart: bigger output per beat, fewer beats (slow-mo first beat)
sh(64.45, 70.6, 'heart', (S, lt, t) => {
  // slow-motion first beat 64.6-66.6, then calm slowing beats
  let bt, bpm;
  if (t < 67.0) { bt = .9 + range(t, 64.6, 66.9) * .45; bpm = 60; }
  else { bpm = lerp(70, 54, range(t, 67, 70.6)); bt = (t - 67) * bpm / 60 / (bpm / 60) + .2; }
  heartBase(S, t, { bt, bpm, amp: 1.6, scale: 1.12, key: 2.6, back: 40 });
  const beats = [65.0, 68.3, 69.45];
  const tb = Math.max(...beats.map((b) => (t >= b ? b : -99)));
  const slow = t < 67 ? .35 : 1;
  rbcBurst(S, (t - tb) * slow, t < 67 ? 1.4 : 1);
  const path = cp([P(0, [2.4, -.6, 4.6], [-.3, 1.7, 0], 44), P(2.5, [3.2, .4, 5.4], [-.3, 1.7, 0], 42), P(6.15, [5, 1.4, 8.6], [0, 1.2, 0], 36)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .012;
}, { tin: 'cut' });

// 70.6 – 75.5  crane up from chest to head (x-ray walk)
sh(70.6, 75.5, 'town', (S, lt, t) => {
  townBase(S, t, { xray: 1 }); const s = S.sam; const dist = (t - 70.6) * 1.2 + 50;
  const pos = walk(s, dist, { z0: 0, dir: 1 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); samFace(s, t, { look: [0, .2] });
  s.glowOrgan('heart', .9 + .3 * Math.sin(t * 7)); s.organs.heart.userData.beat(t, 75, 1.2);
  s.glowOrgan('brain', smooth(range(t, 74.4, 75.5)) * 1.3);
  const path = cp([P(0, [.9, 1.3, 1.9], [0, 1.28, 0], 36), P(3.1, [.9, 1.45, 1.9], [0, 1.4, 0], 36), P(4.9, [.6, 2.6, 1.6], [0, 2.25, 0], 34)], { shake: .02 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .012;
}, { tin: 'cut' });

// 75.5 – 77.1  "far more surprising": dolly-zoom push into the head
sh(75.5, 77.1, 'town', (S, lt, t) => {
  townBase(S, t, { xray: 1 }); const s = S.sam; const dist = (t - 70.6) * 1.2 + 50;
  const pos = walk(s, dist, { z0: 0, dir: 1 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); samFace(s, t, { eyes: 'wide', mouth: 'o', look: [0, .2] });
  s.glowOrgan('brain', 1.3 + range(lt, 0, 1.6) * 1.5);
  const k = easeIn(range(lt, 0, 1.6));
  const fov = lerp(30, 75, k); const d0 = 2.2; const dd = d0 * Math.tan(THREE.MathUtils.degToRad(30) / 2) / Math.tan(THREE.MathUtils.degToRad(fov) / 2);
  camera.position.set(pos.x + .2, pos.y + 2.2, pos.z + Math.max(.35, dd)); camera.lookAt(pos.x, pos.y + 2.2, pos.z); camera.fov = fov; camera.updateProjectionMatrix();
  post.focus.value = dd; post.aperture.value = .01; post.zoomBlur.value = k * .08;
}, { tout: 'flash' });

// 77.1 – 82.0  brain: blood + oxygen travel upward
sh(77.1, 82.0, 'brain', (S, lt, t) => {
  brainBase(S, t, { streams: smooth(range(t, 78.3, 80.0)), glow: .05 });
  const path = cp([P(0, [0, -2.5, 7.5], [0, .3, 0], 42), P(4.9, [4.5, -3.2, 5.5], [0, 0, 0], 46)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
  post.bloom.value = .55; C.setBloomThreshold(.9);
}, { tin: 'flash' });

// 82.0 – 87.9  energy-hungry brain finally gets its fuel
sh(82.0, 87.9, 'brain', (S, lt, t) => {
  const g = smooth(range(t, 85.3, 87.3));
  brainBase(S, t, { streams: 1, glow: .05 + g * .5, sparks: g, key: 2 + g });
  const path = cp([P(0, [-5.5, 1.5, 4.5], [0, .2, 0], 40), P(5.9, [-2.6, .9, 4.4], [0, .2, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
  post.bloom.value = .5 + g * .35; C.setBloomThreshold(.9);
}, { tin: 'cut' });

// 87.9 – 89.6  the fog lifts (slow motion)
sh(87.9, 89.6, 'brain', (S, lt, t) => {
  const f = 1 - easeInOut(range(t, 88.1, 89.5));
  brainBase(S, t * .3, { fog: f, glow: .35 + (1 - f) * .3, rotY: 1.2 });
  const path = cp([P(0, [0, .8, 7.5], [0, .3, 0], 38), P(1.7, [0, .6, 6.4], [0, .3, 0], 38)], { shake: .015 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
  post.sat.value = lerp(.6, 1.15, 1 - f); post.bloom.value = .5;
}, { tin: 'cut' });

// 89.6 – 93.7  chemicals that lift mood & lower stress
sh(89.6, 93.7, 'neurons', (S, lt, t) => {
  const rel = smooth(range(t, 90.3, 91.2));
  for (let i = 0; i < S.NC; i++) { const c = S.cc[i]; const ph = (c.ph + (t - 90.3) * c.sp * .25); const k = ph % 1; const on = (t > 90.3 && ph >= 0) ? 1 : 0; const p = c.src.clone().addScaledVector(c.d, k * 6); O.setInst(S.chem, i, p.x, p.y + Math.sin(k * 6 + i) * .3, p.z, 0, 0, 0, on * rel * Math.sin(k * Math.PI) * 1.8); }
  S.chem.instanceMatrix.needsUpdate = true;
  S.ns.forEach((n, i) => n.rotation.y += 0);
  const path = cp([P(0, [0, 0, 8], [0, 0, -4], 50), P(4.1, [1.5, .6, -2], [0, 0, -12], 54)], { shake: .03 });
  const r = path.apply(camera, lt); post.focus.value = 5; post.aperture.value = .012;
  post.bloom.value = .7; C.setBloomThreshold(.7);
}, { tin: 'whip' });

// 93.7 – 96.7  a short walk clears a heavy mind (storm cloud dissolves)
sh(93.7, 96.7, 'town', (S, lt, t) => {
  townBase(S, t, {}); const s = S.sam; const dist = (t - 93.7) * 1.2 + 70;
  const pos = walk(s, dist, { z0: 0, dir: 1 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: 1, headNod: lt < 1.6 ? .15 : 0 }, t);
  const clear = smooth(range(t, 95.2, 96.0));
  s.setFace(clear < .5 ? { eyes: 'half', brow: 'worried', mouth: 'frown', blink: s.blinkAt(t) } : { eyes: 'happy', mouth: 'grin', blush: .6 });
  S.storm.visible = clear < 1; S.storm.position.set(pos.x, pos.y + 3.55 + clear * .6, pos.z); S.storm.userData.mat.opacity = 1 - clear; S.storm.scale.setScalar(1 + clear * .6);
  S.storm.userData.rain.forEach((d, i) => { d.position.y = -.4 - ((t * 3 + i * .37) % 1) * 1.2; d.visible = clear < .3; });
  const path = cp([P(0, [.5, 2.1, 3.2], [0, 2.5, 0], 38), P(3, [.3, 2.0, 2.9], [0, 2.6, 0], 38)], { shake: .02 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .014;
  post.sat.value = lerp(.7, 1.12, clear); post.exposure.value = lerp(.85, 1.05, clear);
}, { tin: 'cut' });

// 96.7 – 100.0  best ideas while walking: light bulb pops
sh(96.7, 100.05, 'town', (S, lt, t) => {
  townBase(S, t, {}); const s = S.sam; const dist = (t - 96.7) * 1.2 + 76;
  const pos = walk(s, dist, { z0: 0, dir: -1, x: -4.0 }); followSun(S, pos);
  const stop = smooth(range(t, 98.1, 98.5));
  s.pose({ walk: walkPhase(dist), walkAmt: 1 - stop * .0, headNod: -.1 * stop }, t);
  const pop = backOut(range(t, 98.35, 98.75));
  s.setFace(pop > .1 ? { eyes: 'wide', brow: 'raised', mouth: 'grin', look: [0, .4] } : { eyes: 'open', mouth: 'smallSmile', blink: s.blinkAt(t) });
  S.bulb.visible = pop > 0; S.bulb.position.set(pos.x, pos.y + 3.45 + .05 * Math.sin(t * 4), pos.z); S.bulb.scale.setScalar(Math.max(.001, pop));
  S.bulb.userData.rays.rotation.z = t * .5; S.bulb.userData.rays.scale.setScalar(1 + .1 * Math.sin(t * 10));
  S.bulb.lookAt(camera.position.x, S.bulb.position.y, camera.position.z);
  const path = cp([P(0, [1.4, .5, -2.6], [0, 2.4, 0], 46), P(3.35, [1.0, .6, -2.2], [0, 2.7, 0], 46)], { shake: .02 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .012;
  post.flash.value = .35 * Math.exp(-Math.max(0, t - 98.4) * 6) * (t > 98.4 ? 1 : 0);
}, { tin: 'cut' });

// 100.0 – 105.3  protecting memory: hippocampus glows, shield
sh(100.05, 105.3, 'brain', (S, lt, t) => {
  const op = lerp(1, .28, smooth(range(t, 100.4, 101.6)));
  brainBase(S, t, { glow: .2, cortexOp: op, hip: smooth(range(t, 101.0, 102.0)) + .6 * pulse(t, 104.0, 105.3, .2), shield: smooth(range(t, 102.6, 103.6)), rotY: .4 + lt * .08 });
  const path = cp([P(0, [5.5, 1.2, 4.5], [0, -.3, 0], 38), P(5.25, [3.2, .4, 5.6], [0, -.4, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
  post.bloom.value = .55; C.setBloomThreshold(.9);
}, { tin: 'dip' });

// 105.3 – 108.3  tilt down: brain isn't the only organ
sh(105.3, 108.3, 'town', (S, lt, t) => {
  townBase(S, t, { xray: 1 }); const s = S.sam; const dist = (t - 105.3) * 1.2 + 84;
  const pos = walk(s, dist, { z0: 0, dir: 1 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); samFace(s, t);
  s.glowOrgan('brain', 1 - smooth(range(t, 106.6, 107.3))); s.glowOrgan('gut', smooth(range(t, 107.0, 107.6)) * 1.2); s.glowOrgan('liver', smooth(range(t, 107.0, 107.6)) * 1.2); s.glowOrgan('stomach', smooth(range(t, 107.0, 107.6)));
  const path = cp([P(0, [.8, 2.3, 1.9], [0, 2.2, 0], 34), P(1.4, [.8, 2.3, 1.9], [0, 2.2, 0], 34), P(2.2, [.9, 1.15, 1.8], [0, 1.0, 0], 34), P(3, [.8, 1.1, 1.6], [0, 1.02, 0], 32)], { shake: .02, ease: expoInOut });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .012;
}, { tin: 'dip' });

// 108.3 – 112.0  blood sugar: sugar cubes drifting in the bloodstream
sh(108.3, 112.0, 'vessel', (S, lt, t) => {
  vesselBase(S, t, { dist: 60 + lt * 1.6, sugar: 1, light: 1.2, hemiCol: 0xffe0f0, valves: false });
  vesselCam(S, 52 + lt * 1.2, t, { fov: 56, off: [.6, .2] });
  post.tint.value.set(1.0, .98, 1.05);
}, { tin: 'zoom' });

// 112.0 – 117.8  muscles need fuel: sugar from the capillary
sh(112.0, 117.8, 'metabolic', (S, lt, t) => {
  metaBase(S, t, { pull: range(t, 116.3, 120.5) * .25, muscleGlow: .15 + .1 * Math.sin(t * 3), doors: smooth(range(t, 116.0, 116.8)) });
  const path = cp([P(0, [-6, 1, 6], [-2, 1.4, -2], 40), P(5.8, [2.5, 2.4, 6.5], [0, 2, -2], 42)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
}, { tin: 'cut' });

// 117.8 – 121.0  pulling it in (slow-mo on "beautiful part")
sh(117.8, 121.0, 'metabolic', (S, lt, t) => {
  const slowT = t < 119.6 ? t : 119.6 + (t - 119.6) * .3;
  metaBase(S, slowT, { pull: .25 + range(slowT, 117.8, 120.2) * .75, muscleGlow: .3 + range(t, 118, 120) * .6, doors: 1 });
  const path = cp([P(0, [1.8, 3.2, 2.2], [-1, 2, -2], 44), P(1.8, [.6, 2.9, 1.0], [-1.6, 1.9, -2], 40), P(3.2, [.3, 2.8, .6], [-1.7, 1.9, -2], 38)], { shake: .015 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .014;
}, { tin: 'cut' });

// 121.0 – 123.9  with much less insulin (only a couple of keys needed)
sh(121.0, 123.9, 'metabolic', (S, lt, t) => {
  metaBase(S, t, { pull: .6 + range(t, 121, 124) * .4, muscleGlow: .5, doors: 1 });
  S.keys.forEach((k, i) => {
    const appear = backOut(range(t, 121.4 + i * .03, 121.8 + i * .03));
    const gone = i >= 2 ? smooth(range(t, 122.2 + i * .04, 122.6 + i * .04)) : 0;
    k.visible = appear > 0 && gone < 1; k.scale.setScalar(Math.max(.001, appear * (1 - gone)) * 1.4);
    const a = i / 10 * Math.PI * 2 + t * .3; k.position.set(Math.cos(a) * 3.2, 3 + Math.sin(a * 2) * .6, Math.sin(a) * 1.5 - 1);
    k.rotation.set(t * .5 + i, t + i, 0);
  });
  const path = cp([P(0, [0, 3.2, 8.5], [0, 2.4, -1], 42), P(2.9, [0, 3.4, 7.2], [0, 2.4, -1], 42)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
}, { tin: 'cut' });

// 123.9 – 126.2  pancreas relaxes
sh(123.9, 126.2, 'metabolic', (S, lt, t) => {
  metaBase(S, t, { muscle: false, pancreas: true });
  const relief = smooth(range(t, 124.6, 125.1));
  S.pancreas.position.set(0, 2.2, 0); S.pancreas.rotation.set(.2, -.15 + Math.sin(t) * .05, 0);
  S.pancreas.scale.set(1.3 * (1 + .03 * Math.sin(t * 2)), 1.3, 1.3);
  S.pFace.userData.set(relief > .5 ? { eyes: 'happy', mouth: 'smile', blush: .7 } : { eyes: 'open', brow: 'worried', mouth: 'wobble', sweat: 1 });
  const path = cp([P(0, [-1.5, 2.6, 5.0], [-.6, 2.3, 0], 36), P(2.3, [-1.1, 2.5, 4.0], [-.5, 2.3, 0], 36)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .014;
}, { tin: 'whip' });

// 126.2 – 131.0  pancreas makes (fewer) insulin keys; liver relaxes, stores & releases sugar
sh(126.2, 131.0, 'metabolic', (S, lt, t) => {
  metaBase(S, t, { muscle: false, pancreas: true, liver: true, liverSugar: true });
  S.pancreas.position.set(-3.2, 2.0, 0); S.pancreas.rotation.set(.2, .1, 0); S.pFace.userData.set({ eyes: 'happy', mouth: 'smile', blush: .5 });
  S.liver.position.set(2.6, 2.3, -.5); S.liver.rotation.set(.1, -.3 + Math.sin(t) * .04, 0);
  const lr = smooth(range(t, 128.4, 128.9));
  S.lFace.userData.set(lr > .5 ? { eyes: 'happy', mouth: 'smile', blush: .6 } : { eyes: 'open', brow: 'worried', mouth: 'frown', blink: 0 });
  S.keys.forEach((k, i) => { const kt = range(t, 126.6 + i * .25, 128.4 + i * .25); k.visible = i < 3 && kt > 0 && kt < 1; k.position.set(-3.2 + kt * 2.6, 2.2 + Math.sin(kt * Math.PI) * 1.6, .8); k.scale.setScalar(1.2 * Math.sin(kt * Math.PI) + .01); k.rotation.set(t, t * 1.3, 0); });
  // sugar cubes in & out of the liver
  for (let i = 0; i < S.NS; i++) { const ph = ((t - 129.0) * .5 + i / S.NS) % 1; const on = t > 129.0 ? 1 : 0; const inward = i % 2 === 0; const k = inward ? ph : 1 - ph; const a = i * 2.4; const p = V(2.6 + Math.cos(a) * (3.2 * (1 - k) + .4), 2.3 + Math.sin(a) * (2 * (1 - k) + .2), -.5 + .8); O.setInst(S.sugar, i, p.x, p.y, p.z, t + i, t, 0, on * Math.sin(ph * Math.PI) * 1.2); }
  S.sugar.instanceMatrix.needsUpdate = true; S.sugar.visible = true; S.rbc.visible = false;
  const path = cp([P(0, [-3.4, 2.4, 4.6], [-3.0, 2.1, 0], 38), P(2.0, [-2.6, 2.5, 5.0], [-2.2, 2.1, 0], 38), P(3.0, [1.8, 2.6, 5.2], [2.4, 2.3, -.5], 38), P(4.8, [2.4, 2.8, 4.6], [2.6, 2.3, -.5], 38)], { shake: .02, ease: easeInOut });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .012;
}, { tin: 'cut' });

// 131.0 – 132.7  after a meal → stand up and walk
sh(131.0, 132.75, 'dining', (S, lt, t) => {
  const s = S.sam; const up = easeInOut(range(lt, .5, 1.1));
  s.root.position.set(1.2 + up * .9, .12, -.3 - up * .2); s.root.rotation.y = lerp(0, -1.2, up);
  s.pose({ sit: 1 - up, walk: lt * 5, walkAmt: smooth(range(lt, 1.0, 1.4)) }, t);
  s.setFace({ eyes: up > .5 ? 'open' : 'happy', mouth: 'smile', blink: s.blinkAt(t) });
  S.pasta.scale.set(1, .35 * (1 - smooth(range(lt, 0, .4)) * .8), 1);
  const path = cp([P(0, [4.6, 1.8, 4.4], [1.4, 1.2, -.3], 38), P(1.75, [4.2, 1.6, 3.6], [2.0, 1.4, -.4], 38)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
}, { tin: 'dip' });

// 132.7 – 136.4  sugar spike flattens (graph)
sh(132.75, 136.4, 'stage', (S, lt, t) => {
  stageBase(S, { graph: true });
  const draw = easeOut(range(t, 132.8, 133.6));
  const morph = easeInOut(range(t, 134.3, 135.2));
  const col = new THREE.Color(0xff4d5a).lerp(new THREE.Color(0x4fd17a), morph).getHex();
  graphLine(S, morph, draw, col);
  S.graph.position.set(0, 0, 0); S.graph.rotation.y = 0;
  const path = cp([P(0, [-1.5, 2.2, 8.5], [.2, 2, 0], 40), P(3.65, [1.2, 2.5, 7.8], [.2, 1.8, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .006;
  post.bloom.value = .5;
}, { tin: 'whip' });

// 136.4 – 138.0  daily (timelapse)
sh(136.4, 138.0, 'town', (S, lt, t) => {
  townBase(S, t, { tod: Math.abs(Math.sin(lt * 2.4)) * .85, sunAng: lt * 4 });
  const s = S.sam; const dist = lt * 7; const pos = walk(s, dist, { z0: -40, dir: 1 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist) * .25, walkAmt: 1 }, t); samFace(s, t, { mouth: 'smile' });
  S.sun.position.copy(pos).add(V(Math.cos(lt * 4) * 20, 18, Math.sin(lt * 4) * 20));
  const path = cp([P(0, [0.5, 6, -32], [-4.2, 1, -38], 44), P(1.6, [0.8, 6.5, -26], [-4.2, 1, -32], 44)], { shake: .01 });
  path.apply(camera, lt); post.aperture.value = .002;
}, { tin: 'cut' });

// 138.0 – 140.9  better at handling sugar — not worse
sh(138.0, 140.9, 'metabolic', (S, lt, t) => {
  const cyc = ((t - 138) * .55) % 1;
  metaBase(S, t, { pull: .2 + cyc * .9, muscleGlow: .5 + .3 * Math.sin(t * 4), doors: 1 });
  const path = cp([P(0, [5.5, 3.0, 5.5], [0, 1.6, -2], 40), P(2.9, [3.5, 2.6, 4.2], [-.5, 1.8, -2], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
}, { tin: 'whip' });

// 140.9 – 143.9  follow the walk deeper into the gut (push into belly)
sh(140.9, 143.9, 'town', (S, lt, t) => {
  townBase(S, t, { xray: smooth(range(lt, 0, .5)) }); const s = S.sam; const dist = (t - 140.9) * 1.2 + 100;
  const pos = walk(s, dist, { z0: 0, dir: 1 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); samFace(s, t);
  s.glowOrgan('gut', smooth(range(t, 142.2, 143.2)) * 1.5); s.glowOrgan('stomach', smooth(range(t, 142.2, 143.2)));
  const path = cp([P(0, [1.2, 1.6, 4.5], [0, 1.2, 0], 36), P(1.8, [.5, 1.2, 2.4], [0, 1.0, 0], 34), P(3.0, [.1, 1.0, .9], [0, 1.0, 0], 46)], { shake: .02, ease: easeIn });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .012; post.zoomBlur.value = .06 * easeIn(range(lt, 2.2, 3));
}, { tin: 'cut', tout: 'zoom' });

// 143.9 – 147.5  each step shakes and massages the intestines
sh(143.9, 147.5, 'gut', (S, lt, t) => {
  const stepPh = (t * 1.9) % 1; const bump = Math.exp(-stepPh * 7);
  S.gut.position.set(0, -bump * .08, 0); S.gut.scale.set(2.2 * (1 + bump * .04), 2.2 * (1 - bump * .05), 2.2 * (1 + bump * .04));
  S.gut.rotation.set(Math.sin(t * 6) * .02 * bump, Math.sin(t * .3) * .2, 0); S.face.visible = false; S.hearts.forEach((h) => h.visible = false);
  S.gut.userData.si.rotation.z = Math.sin(t * 11.9) * .015 * bump;
  S.back.intensity = 30 + bump * 30;
  const path = cp([P(0, [3.5, 1.5, 6.5], [0, 0, 0], 40), P(3.6, [-2.5, .9, 6.8], [0, 0, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); camera.position.y += bump * .03; post.focus.value = r.dist; post.aperture.value = .01;
}, { tin: 'zoom' });

// 147.5 – 154.6  inside the gut: food moves along, bloating eases
sh(147.5, 154.6, 'gut', (S, lt, t) => {
  S.tun.material.uniforms.time.value = t; S.face.visible = false; S.hearts.forEach((h) => h.visible = false);
  const L = S.curve.getLength(); const c = new THREE.Vector3(), tg = new THREE.Vector3(), n = new THREE.Vector3(), b = new THREE.Vector3();
  S.food.forEach((f, i) => { const d = f.userData; const u = (d.u + (t - 147.5) * .028) % 1; S.curve.getPointAt(u, c); S.curve.getTangentAt(u, tg); n.crossVectors(tg, V(0, 1, 0)).normalize(); b.crossVectors(n, tg); f.position.copy(c).addScaledVector(n, Math.cos(d.a) * d.r).addScaledVector(b, Math.sin(d.a) * d.r - .6); f.rotation.set(t * .5 + i, t * .3, 0); });
  const deflate = smooth(range(t, 152.3, 153.8));
  S.gas.forEach((g, i) => { const d = g.userData; const u = (d.u + (t - 147.5) * .02) % 1; S.curve.getPointAt(u, c); S.curve.getTangentAt(u, tg); n.crossVectors(tg, V(0, 1, 0)).normalize(); b.crossVectors(n, tg); g.position.copy(c).addScaledVector(n, Math.cos(d.a) * d.r).addScaledVector(b, Math.sin(d.a) * d.r); const pop = clamp(deflate * 1.3 - (i % 5) * .08); g.scale.setScalar(Math.max(.001, (1 + .08 * Math.sin(t * 3 + i)) * (1 - pop))); g.visible = pop < 1; });
  const dc = 4 + (t - 147.5) * .9;
  const u = clamp(dc / L), u2 = clamp((dc + 5) / L);
  const p = S.curve.getPointAt(u), l = S.curve.getPointAt(u2); p.y += .4 + noise1(t * .7) * .1; p.x += noise1(t * .6 + 3) * .1;
  camera.position.copy(p); camera.lookAt(l); camera.rotateZ(noise1(t * .3) * .06); camera.fov = 64; camera.updateProjectionMatrix();
  post.focus.value = 4; post.aperture.value = .008;
  post.exposure.value = lerp(.95, 1.1, smooth(range(t, 150.6, 151.5)));
}, { tin: 'cut' });

// 154.6 – 157.7  your gut loves movement (happy gut, hearts)
sh(154.6, 157.7, 'gut', (S, lt, t) => {
  S.gut.position.set(0, 0, 0); S.gut.scale.setScalar(2.2); S.gut.rotation.set(0, Math.sin(t * .4) * .12, 0);
  S.face.visible = true; S.face.userData.set({ eyes: 'happy', mouth: 'grin', blush: 1 });
  S.hearts.forEach((h, i) => { const ph = ((t - 154.8) * .45 + i / 16) % 1; const on = t > 154.9 ? 1 : 0; h.visible = on > 0; h.position.set(Math.sin(i * 2.3) * 2.2, 1.2 + ph * 3.2, 1 + Math.cos(i * 1.7) * .8); h.scale.setScalar(on * Math.sin(ph * Math.PI) * 1.1 + .001); h.rotation.set(0, Math.sin(t * 2 + i) * .5, Math.sin(t * 3 + i) * .2); });
  const path = cp([P(0, [0, .6, 7.5], [0, .5, 0], 40), P(3.1, [0, .9, 6.4], [0, .7, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
  post.bloom.value = .5;
}, { tin: 'whip' });

// 157.7 – 160.4  joints: x-ray knee, slow-mo step
sh(157.7, 160.4, 'town', (S, lt, t) => {
  townBase(S, t, { xray: 1 }); const s = S.sam; const at = 157.7 + lt * .35; const dist = (at - 157.7) * 1.2 + 120;
  const pos = walk(s, dist, { z0: 0 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, at); samFace(s, at);
  s.legMuscles.forEach((m) => m.material.emissiveIntensity = .2);
  const path = cp([P(0, [1.3, .55, .5], [0, .5, 0], 34), P(2.7, [1.15, .5, -.35], [0, .5, -.15], 30)], { shake: .015 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .016;
  post.tint.value.set(.95, 1.0, 1.08);
}, { tin: 'cut' });

// 160.4 – 163.5  worried elder on a bench holding the knee
sh(160.4, 163.5, 'town', (S, lt, t) => {
  townBase(S, t, { elder: true, sam: false }); const e = S.elder;
  e.root.position.set(-6.25, .2, -30); e.root.rotation.y = Math.PI / 2;
  e.pose({ sit: 1, armL: -.9, elbowL: -1.1, armR: -.7, elbowR: -1.3, headNod: .25, headTilt: .1 }, t);
  e.setFace({ eyes: 'open', brow: 'worried', mouth: 'wobble', blink: e.blinkAt(t, 2), look: [.3, -.4] });
  followSun(S, V(-6, 0, -30));
  const path = cp([P(0, [-2.0, 1.4, -27.6], [-6.1, 1.4, -30], 38), P(3.1, [-3.0, 1.5, -28.6], [-6.1, 1.5, -30], 36)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .016;
}, { tin: 'cut' });

// 163.5 – 168.4  knee: no blood supply of its own
sh(163.5, 168.4, 'knee', (S, lt, t) => {
  S.knee.userData.femur.position.y = 0; S.knee.userData.cartTop.scale.y = 1; S.knee.userData.cartMat.emissive.setHex(0x2080a0); S.knee.userData.cartMat.emissiveIntensity = .2;
  S.vess.children.forEach((m) => { if (m.material?.emissive) { m.material.emissive.setHex(0x801010); m.material.emissiveIntensity = pulse(t, 164.8, 166.0, .2) * 1.2; } });
  for (let i = 0; i < S.NF; i++) { const f = S.fp[i]; const r = 1.55 + .3 * Math.sin(t + i); O.setInst(S.fluid, i, Math.cos(f.a + t * .1) * r, f.y + Math.sin(t * .8 + i) * .2, Math.sin(f.a + t * .1) * r * .8, 0, 0, 0, smooth(range(t, 166, 167))); }
  S.fluid.instanceMatrix.needsUpdate = true; S.waste.visible = false;
  const path = cp([P(0, [4.5, 1.6, 6.5], [0, 0, 0], 38), P(4.9, [-3.5, .8, 7.0], [0, 0, 0], 38)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
}, { tin: 'dip' });

// 168.4 – 174.3  every step squeezes the cartilage like a sponge (fluid in, waste out)
sh(168.4, 174.3, 'knee', (S, lt, t) => {
  // first squeeze slow-motion, then rhythmic
  let c; if (t < 170.8) c = Math.sin(range(t, 168.8, 170.8) * Math.PI); else c = Math.pow(Math.max(0, Math.sin((t - 170.8) * Math.PI * 1.1)), 2);
  S.knee.userData.femur.position.y = -c * .18; S.knee.userData.patella;
  S.knee.userData.cartTop.scale.set(1 + c * .08, 1 - c * .45, 1 + c * .08); S.knee.userData.cartTop.position.y = -c * .1;
  S.knee.userData.cartBot.scale.set(1 + c * .06, 1 - c * .4, .78 * (1 + c * .06));
  S.knee.userData.cartMat.emissive.setHex(0x2090b0); S.knee.userData.cartMat.emissiveIntensity = .25 + (1 - c) * .25;
  S.vess.children.forEach((m) => { if (m.material?.emissive) m.material.emissiveIntensity = 0; });
  // fluid flows in when released, waste squeezed out when compressed
  const R = C.rng(3);
  for (let i = 0; i < S.NF; i++) { const f = S.fp[i]; const k = (f.ph + t * .35 * f.sp) % 1; const r = lerp(1.7, .35, easeInOut(k) * (1 - c * .6)); O.setInst(S.fluid, i, Math.cos(f.a) * r, f.y + .05, Math.sin(f.a) * r * .8, 0, 0, 0, (t > 171.4 ? 1 : .3) * Math.sin(k * Math.PI)); }
  S.fluid.instanceMatrix.needsUpdate = true;
  S.waste.visible = t > 172.8;
  for (let i = 0; i < S.NW; i++) { const f = S.fp[i]; const k = (f.ph + t * .4) % 1; const r = lerp(.3, 2.0, k); O.setInst(S.waste, i, Math.cos(f.a + 1) * r, f.y, Math.sin(f.a + 1) * r * .8, 0, 0, 0, Math.sin(k * Math.PI) * smooth(range(t, 172.8, 173.5))); }
  S.waste.instanceMatrix.needsUpdate = true;
  const path = cp([P(0, [3.2, .6, 4.2], [0, 0, 0], 40), P(2.5, [2.2, .3, 3.4], [0, 0, 0], 38), P(5.9, [-2.6, .8, 4.0], [0, 0, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
}, { tin: 'cut' });

// 174.3 – 177.6  it feeds them: cartilage glowing healthy
sh(174.3, 177.6, 'knee', (S, lt, t) => {
  const c = Math.pow(Math.max(0, Math.sin((t - 174.3) * Math.PI * 1.1)), 2) * .6;
  S.knee.userData.femur.position.y = -c * .18; S.knee.userData.cartTop.scale.set(1, 1 - c * .4, 1); S.knee.userData.cartTop.position.y = -c * .1; S.knee.userData.cartBot.scale.set(1, 1 - c * .35, .78);
  const g = smooth(range(t, 176.5, 177.2));
  S.knee.userData.cartMat.emissive.setHex(0x30c0ff); S.knee.userData.cartMat.emissiveIntensity = .3 + g * 1.2;
  for (let i = 0; i < S.NF; i++) { const f = S.fp[i]; const k = (f.ph + t * .35 * f.sp) % 1; const r = lerp(1.7, .35, easeInOut(k)); O.setInst(S.fluid, i, Math.cos(f.a) * r, f.y + .05, Math.sin(f.a) * r * .8, 0, 0, 0, Math.sin(k * Math.PI)); }
  S.fluid.instanceMatrix.needsUpdate = true; S.waste.visible = false;
  S.knee.rotation.y = 0;
  const path = cp([P(0, [0, 3.5, 5.5], [0, 0, 0], 40), P(3.3, [1.2, 1.2, 5.2], [0, 0, 0], 38)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
  post.bloom.value = .45 + g * .3;
}, { tin: 'whip' });

// 177.6 – 180.2  the stiffer you feel, the more they need it: elder walking happily
sh(177.6, 180.2, 'town', (S, lt, t) => {
  townBase(S, t, { elder: true, bench: true, sam: false }); const e = S.elder; const dist = lt * .95;
  const loosen = smooth(range(lt, 0, 2));
  const pos = walk(e, dist, { z0: -31.5, dir: 1, x: -4.4 }); followSun(S, pos);
  e.pose({ walk: walkPhase(dist, .5), walkAmt: lerp(.45, .9, loosen), lean: .1 * (1 - loosen) }, t);
  e.setFace({ eyes: loosen > .5 ? 'happy' : 'open', mouth: loosen > .5 ? 'grin' : 'flat', blink: e.blinkAt(t, 2) });
  const path = cp([P(0, [-2.2, 1.0, -27.5], [-4.4, 1.5, -31], 36), P(2.6, [-2.0, 1.1, -26.4], [-4.4, 1.5, -29.6], 36)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .014;
}, { tin: 'cut' });

// 180.2 – 182.5  bones feel each step: impact shock travels up the x-ray leg (slow-mo)
sh(180.2, 182.5, 'town', (S, lt, t) => {
  townBase(S, t, { xray: 1 }); const s = S.sam; const at = lt * .3; const dist = at * 1.2 + 140;
  const pos = walk(s, dist, { z0: 0 }); followSun(S, pos);
  const ph = walkPhase(dist); s.pose({ walk: ph, walkAmt: 1 }, at); samFace(s, at);
  if (!S.shock) { S.shock = new THREE.Mesh(new THREE.RingGeometry(.9, 1, 64), C.glow(0xffe0a0, 3, { transparent: true, additive: true, side: THREE.DoubleSide })); S.shock.rotation.x = -Math.PI / 2; S.scene.add(S.shock); }
  const k = range(lt, .9, 1.9); S.shock.visible = k > 0 && k < 1; S.shock.scale.setScalar(.1 + k * 1.2); S.shock.material.opacity = 1 - k; S.shock.position.set(pos.x - .13, pos.y + .03, pos.z - .2);
  s.legMuscles.forEach((m) => m.material.emissiveIntensity = .2);
  const path = cp([P(0, [.9, .12, -1.2], [0, .25, 0], 50), P(2.3, [.7, .15, -.9], [0, .3, 0], 46)], { shake: .01 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .02;
}, { tin: 'cut' });

// 182.5 – 186.2  bone stays dense & strong (trabecular lattice thickens with each impact)
sh(182.5, 186.2, 'knee', (S, lt, t) => {
  const dens = smooth(range(t, 183.3, 185.4));
  const hits = [182.7, 183.6, 184.5, 185.4]; let pk = 0; for (const h of hits) pk = Math.max(pk, Math.exp(-Math.max(0, t - h) * 5) * (t >= h ? 1 : 0));
  for (let i = 0; i < S.NT; i++) { const b = S.tb[i]; const vis = b.th < .45 + dens * .55 ? 1 : 0; O.setInst(S.trab, i, b.x, b.y, b.z, b.rx, 0, b.rz, vis * (1 + dens * 1.2), b.len, vis * (1 + dens * 1.2)); }
  S.trab.instanceMatrix.needsUpdate = true; S.trab.material.emissiveIntensity = pk * .8;
  S.pulse.position.y = -3 + (t % .9) / .9 * 6; S.pulse.material.opacity = pk;
  const path = cp([P(0, [60 + 5.5, 2.5, 6.5], [60, 0, 0], 40), P(3.7, [60 + 3.5, 1.5, 6.0], [60, 0, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
}, { tin: 'flash' });

// 186.2 – 192.9  something starts to burn: stored fat
sh(186.2, 192.9, 'fat', (S, lt, t) => {
  const burn = smooth(range(t, 187.9, 189.5));
  S.warm.intensity = burn * 40 * (1 + .1 * Math.sin(t * 9));
  S.cells.forEach((c) => { c.userData.core.material.emissiveIntensity = .3 + burn * .4; c.scale.setScalar(c.userData.base * (1 + .015 * Math.sin(t * 1.5 + c.userData.ph * 6))); });
  S.energy.visible = false;
  const path = cp([P(0, [-6, 1.5, 7.5], [0, 0, 0], 38), P(6.7, [3.5, 2.8, 7.2], [0, 0, 0], 38)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
  post.tint.value.set(1.05, 1.0, .95);
}, { tin: 'dip' });

// 192.9 – 199.4  using stored energy, slowly: cells shrink, energy rises
sh(192.9, 199.4, 'fat', (S, lt, t) => {
  const use = smooth(range(t, 195.2, 199.4));
  S.warm.intensity = 40 * (1 + .1 * Math.sin(t * 9));
  S.cells.forEach((c) => { c.userData.core.material.emissiveIntensity = .7; c.scale.setScalar(c.userData.base * (1 - use * .28 * (.6 + c.userData.ph * .4))); });
  S.energy.visible = true; const e0 = smooth(range(t, 195.0, 196.0));
  for (let i = 0; i < S.NE; i++) { const ep = S.ep[i]; const ph = (ep.ph + t * .3 * ep.sp) % 1; const c = S.cells[ep.c].position; O.setInst(S.energy, i, c.x + ep.d.x * ph * 3, c.y + ep.d.y * ph * 4, c.z + ep.d.z * ph * 3 + .6, 0, 0, 0, e0 * Math.sin(ph * Math.PI) * 1.4); }
  S.energy.instanceMatrix.needsUpdate = true;
  const path = cp([P(0, [0, -3.5, 6.5], [0, .5, 0], 42), P(6.5, [0, -1.0, 5.2], [0, .6, 0], 42)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01;
  post.bloom.value = .55;
}, { tin: 'cut' });

// 199.4 – 204.0  ~200 calories
sh(199.4, 204.0, 'stage', (S, lt, t) => {
  stageBase(S, { counter: true, kcal: true, flames: true });
  const v = Math.round(200 * easeOut(range(t, 199.9, 201.7)));
  const ds = String(v).padStart(3, '0'); const shown = v >= 100 ? 3 : v >= 10 ? 2 : 1;
  S.dm.forEach((m, i) => { m.geometry = S.digits[+ds[i]]; m.visible = i >= 3 - shown; m.position.set((i - 1) * 1.75, .3, 0); m.scale.setScalar(1 + (v === 200 ? .08 * Math.exp(-(t - 201.7) * 6) : 0)); });
  S.counter.position.set(-.8, 1.2, 0);
  S.kcal.position.set(2.6, 1.55, 0); S.kcal.scale.setScalar(Math.max(.001, backOut(range(t, 201.6, 202.1))));
  for (let i = 0; i < S.NF; i++) { const ph = (i / S.NF + t * .6) % 1; const a = i * 2.39; const r = 3.6 + Math.sin(i) * .5; O.setInst(S.flames, i, Math.cos(a) * r - .5, ph * 4.5, Math.sin(a) * r * .5 - 1.5, 0, 0, 0, Math.sin(ph * Math.PI) * (1.2 - ph)); }
  S.flames.instanceMatrix.needsUpdate = true;
  const path = cp([P(0, [-2.5, 1.0, 8.5], [0, 2.2, 0], 40), P(4.6, [1.5, 2.6, 8.0], [0, 2.2, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .006;
  post.bloom.value = .6;
}, { tin: 'whip' });

// 204.0 – 209.7  it adds up day after day, week after week (tower grows, camera cranes)
sh(204.0, 209.7, 'stage', (S, lt, t) => {
  stageBase(S, { blocks: true });
  const n = Math.floor(lerp(1, S.NB, range(t, 205.0, 209.4)));
  for (let i = 0; i < S.NB; i++) { const land = clamp((n - i) * .5); const y = .16 + i * .32 + (1 - easeOut(land)) * 2.5; O.setInst(S.blocks, i, 0, y, 0, 0, i * .12, 0, i < n ? 1 : 0); }
  S.blocks.instanceMatrix.needsUpdate = true; S.blocks.count = S.NB;
  const top = .16 + n * .32;
  const path = cp([P(0, [5, 1.0, 7], [0, 1.0, 0], 40), P(5.7, [6, 1 + 22.4 * .8, 9], [0, 22.4 * .75, 0], 44)], { shake: .02, ease: easeIn });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .006;
}, { tin: 'cut' });

// 209.7 – 213.3  lungs join in, deeper breaths
sh(209.7, 213.3, 'lungs', (S, lt, t) => {
  lungsBase(S, t, { depth: lerp(.35, 1, smooth(range(t, 211.3, 212.6))), period: 3.4 });
  const path = cp([P(0, [2.2, .4, 5.0], [0, .3, 0], 40), P(3.6, [-1.6, .7, 4.8], [0, .3, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
}, { tin: 'dip' });

// 213.3 – 217.1  air reaches the parts that usually stay unused
sh(213.3, 217.1, 'lungs', (S, lt, t) => {
  lungsBase(S, t, { xray: true, air: true, depth: 1, period: 3.4 });
  // air particles travel down the bronchial tree to tips
  const tips = S.tips;
  for (let i = 0; i < S.NA; i++) { const tip = tips[i % tips.length].userData.end; const ph = ((i * .618) % 1 + (t - 213.3) * .4) % 1; const p0 = V(0, 2.4, 0), p1 = V(0, 1.05, 0); const p = ph < .3 ? p0.clone().lerp(p1, ph / .3) : p1.clone().lerp(tip, (ph - .3) / .7); O.setInst(S.air, i, p.x, p.y, p.z, 0, 0, 0, Math.sin(ph * Math.PI) * 1.3); }
  S.air.instanceMatrix.needsUpdate = true;
  const fill = range(t, 214.0, 216.3);
  tips.forEach((b, i) => { const e = b.userData.end; const order = 1 - (e.y + 1.4) / 2.6; const on = smooth((fill - order * .8) / .2); O.setInst(S.tipGlow, i, e.x, e.y, e.z, 0, 0, 0, on * 1.4); });
  S.tipGlow.instanceMatrix.needsUpdate = true; S.tipGlow.material.color.setRGB(.6, 2.4, 2.8);
  const path = cp([P(0, [0, .3, 6.8], [0, .3, 0], 42), P(3.8, [1.6, -.6, 6.0], [0, -.2, 0], 42)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .006;
  post.bloom.value = .6;
}, { tin: 'cut' });

// 217.1 – 219.3  immune system boost: white cells patrol fast
sh(217.1, 219.3, 'vessel', (S, lt, t) => {
  const dist = 90 + lt * 9;
  vesselBase(S, t, { dist: dist * .8, light: 1.5, valves: false });
  const L = S.curve.getLength();
  S.immune.forEach((m, i) => { m.visible = true; const u = clamp((dist + 5 + i * 3.5) / L); const p = S.curve.getPointAt(u); m.position.copy(p).add(V(Math.sin(i * 2) * 1.1, Math.cos(i * 3) * .9, 0)); m.rotation.set(t + i, t * .7, 0); m.scale.setScalar(1 + .1 * Math.sin(t * 6 + i)); });
  vesselCam(S, dist, t, { fov: 64, lookAhead: 8, roll: -lt * .2 });
}, { tin: 'whip' });

// 219.3 – 221.3  sleep gets deeper
sh(219.3, 221.3, 'bedroom', (S, lt, t) => {
  const s = S.sam; s.root.position.set(0, 1.12, -.25); s.root.rotation.set(-Math.PI / 2, 0, 0);
  s.pose({ breathe: 3 }, t); s.setFace({ eyes: 'closed', mouth: 'smallSmile', blush: .4 });
  const path = cp([P(0, [1.3, 3.0, .2], [0, 1.25, -2.3], 38), P(2, [1.0, 2.7, -.4], [0, 1.25, -2.4], 36)], { shake: .015 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .012;
  post.tint.value.set(.9, .95, 1.1);
}, { tin: 'dip' });

// 221.3 – 223.4  so what is 5000 steps really? (aerial sunset)
sh(221.3, 223.4, 'town', (S, lt, t) => {
  townBase(S, t, { tod: .45, sunAng: .3 }); const s = S.sam; const dist = (t - 221.3) * 1.2 + 160;
  const pos = walk(s, dist, { z0: 0 }); followSun(S, pos); s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); samFace(s, t);
  const path = cp([P(0, [3, 4, 4], [0, 1, -1], 44), P(2.1, [8, 14, 12], [0, 0, -4], 44)], { shake: .02, ease: easeOut });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .004;
}, { tin: 'dip' });

// 223.4 – 226.6  about 40–50 minutes (clock)
sh(223.4, 226.6, 'stage', (S, lt, t) => {
  stageBase(S, { clock: true, minTxt: true });
  const m = 50 * easeInOut(range(t, 223.6, 224.9));
  S.clock.userData.hand.rotation.z = -m / 60 * Math.PI * 2;
  const sec = S.clock.userData.sector; const len = Math.max(.001, (Math.min(m, 50) - 40) / 60 * Math.PI * 2);
  sec.geometry.dispose(); sec.geometry = new THREE.RingGeometry(.05, 2.05, 48, 1, Math.PI / 2 - 40 / 60 * Math.PI * 2 - len, len); sec.visible = m > 40;
  S.minTxt.position.set(0, .55, 1.5); S.minTxt.scale.setScalar(Math.max(.001, backOut(range(t, 224.3, 224.8))));
  const path = cp([P(0, [0, 3.4, 9.5], [0, 2.4, 0], 40), P(3.2, [.8, 2.8, 8.4], [0, 2.3, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .006;
}, { tin: 'whip' });

// 226.6 – 228.0  not a hard workout (relaxed stroll)
sh(226.6, 228.0, 'town', (S, lt, t) => {
  townBase(S, t, { tod: .15 }); const s = S.sam; const dist = (t - 226.6) * 1.1 + 170;
  const pos = walk(s, dist, { z0: 0, dir: 1 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: .85, armL: .0, armR: .0 }, t); s.setFace({ eyes: 'happy', mouth: 'smile', blink: 0 });
  const path = cp([P(0, [1.5, 1.6, 3.2], [0, 1.6, 0], 40), P(1.4, [1.2, 1.7, 2.6], [0, 1.7, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .012;
}, { tin: 'cut' });

// 228.0 – 231.8  no gym, no special clothes, no equipment — poof
sh(228.0, 231.8, 'stage', (S, lt, t) => {
  stageBase(S, { gym: true, sam: true });
  const pt = [228.55, 228.75, 230.85, 229.75];
  S.gym.userData.items.forEach((it, i) => { const k = range(t, pt[i], pt[i] + .25); it.visible = k < 1; it.scale.setScalar(Math.max(.001, 1 + .25 * Math.sin(k * Math.PI) - smooth(k))); });
  S.gym.userData.puffs.forEach((p, i) => p.userData.at(range(t, pt[i] + .1, pt[i] + .8)));
  const s = S.sam; const dist = Math.max(0, t - 230.6) * 1.3; s.root.position.set(-6 + dist, 0, 2.5); s.root.rotation.y = Math.PI / 2; s.root.visible = t > 230.6;
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); s.setFace({ eyes: 'open', mouth: 'smile', blink: s.blinkAt(t) });
  const path = cp([P(0, [.5, 2.6, 9.5], [.5, 1.0, 0], 40), P(3.8, [-.5, 2.2, 8.8], [-.5, 1.0, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .006;
}, { tin: 'cut' });

// 231.8 – 233.5  over weeks and months (fast timelapse)
sh(231.8, 233.5, 'town', (S, lt, t) => {
  townBase(S, t, { tod: Math.abs(Math.sin(lt * 3.2)) * .9, sunAng: lt * 6 });
  const s = S.sam; const dist = lt * 9; const pos = walk(s, dist, { z0: -60 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist) * .2, walkAmt: 1 }, t); samFace(s, t);
  S.sun.position.copy(pos).add(V(Math.cos(lt * 6) * 20, 18, Math.sin(lt * 6) * 20));
  const path = cp([P(0, [2, 18, -50], [-4.2, 0, -64], 50), P(1.7, [2, 18, -62], [-4.2, 0, -76], 50)], { shake: .01 });
  path.apply(camera, lt); post.aperture.value = .002;
}, { tin: 'whip' });

// 233.5 – 235.0  heart stronger
sh(233.5, 235.0, 'heart', (S, lt, t) => {
  heartBase(S, t, { bpm: 66, amp: 1.5, scale: 1.12, key: 3, back: 50 });
  S.ring.visible = true; const rk = (lt * .9) % 1; S.ring.scale.setScalar(.7 + rk * 1.3); S.ring.material.opacity = Math.sin(rk * Math.PI); S.ring.position.set(0, .8, 0); S.ring.lookAt(camera.position);
  const path = cp([P(0, [-3, .4, 5.2], [0, .9, 0], 38), P(1.5, [-1.6, .6, 5.6], [0, .9, 0], 38)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .012;
}, { tin: 'cut' });
// 235.0 – 236.5  brain clearer
sh(235.0, 236.5, 'brain', (S, lt, t) => {
  brainBase(S, t, { glow: .55, sparks: 1, streams: .6, key: 2.8 });
  const path = cp([P(0, [4.5, 1.6, 5.0], [0, .2, 0], 40), P(1.5, [3.2, 1.2, 5.6], [0, .2, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .01; post.bloom.value = .75; C.setBloomThreshold(.9);
}, { tin: 'cut' });
// 236.5 – 238.4  blood sugar steadier
sh(236.5, 238.4, 'stage', (S, lt, t) => {
  stageBase(S, { graph: true }); graphLine(S, 1, .3 + .7 * easeOut(range(t, 236.5, 237.8)), 0x4fd17a);
  const path = cp([P(0, [3, 2.6, 7.5], [.5, 1.6, 0], 40), P(1.9, [1, 2.0, 7.0], [.5, 1.5, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .006;
}, { tin: 'cut' });
// 238.4 – 239.9  joints stronger
sh(238.4, 239.9, 'knee', (S, lt, t) => {
  S.knee.userData.femur.position.y = 0; S.knee.userData.cartTop.scale.set(1, 1, 1); S.knee.userData.cartTop.position.y = 0; S.knee.userData.cartBot.scale.set(1, 1, .78);
  S.knee.userData.cartMat.emissive.setHex(0x30c0ff); S.knee.userData.cartMat.emissiveIntensity = 1 + .4 * Math.sin(t * 6);
  S.fluid.visible = true; for (let i = 0; i < S.NF; i++) { const f = S.fp[i]; const k = (f.ph + t * .35 * f.sp) % 1; const r = lerp(1.7, .35, easeInOut(k)); O.setInst(S.fluid, i, Math.cos(f.a) * r, f.y + .05, Math.sin(f.a) * r * .8, 0, 0, 0, Math.sin(k * Math.PI)); } S.fluid.instanceMatrix.needsUpdate = true; S.waste.visible = false;
  const path = cp([P(0, [-3.5, 1.4, 4.8], [0, 0, 0], 40), P(1.5, [-2.4, .6, 5.2], [0, 0, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008; post.bloom.value = .7;
}, { tin: 'cut' });

// 239.9 – 242.1  whole body a little younger: all organs glow, x-ray fades to bright sunlight
sh(239.9, 242.1, 'town', (S, lt, t) => {
  const xr = 1 - smooth(range(t, 241.2, 242.0));
  townBase(S, t, { xray: xr, tod: .1 }); const s = S.sam; const dist = (t - 239.9) * 1.2 + 190;
  const pos = walk(s, dist, { z0: 0, dir: 1 }); followSun(S, pos);
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); s.setFace({ eyes: 'happy', mouth: 'grin', blush: .7 });
  ['heart', 'lungs', 'brain', 'gut', 'liver', 'stomach'].forEach((n, i) => s.glowOrgan(n, smooth(range(t, 240.0 + i * .1, 240.4 + i * .1)) * 1.6));
  s.legMuscles.forEach((m) => m.material.emissiveIntensity = 1.4);
  s.organs.heart.userData.beat(t, 70, 1.3);
  const path = cp([P(0, [1.2, 1.3, 4.6], [0, 1.4, 0], 40), P(2.2, [-.8, 1.0, 3.9], [0, 1.5, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt, pos); post.focus.value = r.dist; post.aperture.value = .01;
  post.flash.value = .5 * pulse(t, 241.2, 242.1, .3); post.bloom.value = .45;
}, { tin: 'cut', tout: 'dip' });

// 242.1 – 245.2  your organs are already waiting
sh(242.1, 245.2, 'city', (S, lt, t) => {
  S.scene.userData.wake(12); S.wave.visible = false;
  S.faces.forEach((f, i) => f.userData.set({ eyes: 'open', mouth: 'smallSmile', look: [0, .1], blink: (t * 1.3 + i * .37) % 3 < .12 ? 1 : 0 }));
  S.wrap.forEach((w, i) => { w.lookAt(0, 2.9, 0); w.rotateY(Math.PI); w.position.y = 2.9 + Math.sin(t * 1.2 + i) * .06; });
  S.heart.userData.beat(t, 58, .8);
  const path = cp([P(0, [9, 4.5, 9], [0, 2.6, 0], 40), P(3.1, [3, 4.0, 12.2], [0, 2.7, 0], 40)], { shake: .02 });
  const r = path.apply(camera, lt); post.focus.value = r.dist; post.aperture.value = .008;
  post.bloom.value = .6; C.setBloomThreshold(.8);
}, { tin: 'dip' });

// 245.2 – 248.3  will you take the first step? door opens, foot lifts, freeze
sh(245.2, 248.3, 'living', (S, lt, t) => {
  const s = S.sam; s.root.position.set(4.0, .02, -2.0); s.root.rotation.y = Math.PI;
  const open = easeInOut(range(t, 245.4, 246.4));
  S.doorPivot.rotation.y = -open * 1.6; S.doorLight.visible = open > .02; S.doorLight.material.color.setRGB(2.2, 2.0, 1.6).multiplyScalar(open);
  S.sunBeam.intensity = open * 10;
  const lift = easeOut(range(t, 247.0, 247.7));
  s.pose({ legR: -.55 * lift, kneeR: .9 * lift, armL: -.3 * lift, armR: .3 * lift }, t); s.setFace({ eyes: 'open', mouth: 'smile', blink: 0 });
  const path = cp([P(0, [6.6, .4, 1.4], [4.6, 1.3, -3.9], 48), P(3.1, [6.2, .45, .5], [4.6, 1.25, -3.9], 44)], { shake: .015 });
  const r = path.apply(camera, lt); post.focus.value = 3; post.aperture.value = .012;
  post.bloom.value = .4 + open * .4; C.setBloomThreshold(.9);
}, { tin: 'dip', tout: 'flash' });

// 248.3 – 251.0  end title
sh(248.3, 251.0, 'town', (S, lt, t) => {
  townBase(S, t, { title: true, tod: .05 }); const s = S.sam; const dist = (t - 248.3) * 1.25;
  const pos = walk(s, dist, { x: .9, z0: -8, dir: -1 }); followSun(S, V(0, 0, -12));
  s.pose({ walk: walkPhase(dist), walkAmt: 1 }, t); samFace(s, t);
  S.title.position.set(0, 1.75, 0); S.steps.position.set(0, 0, 1.6);
  S.title.userData.letters.forEach((m, i) => { m.position.y = 0; m.rotation.x = 0; m.scale.setScalar(1); });
  S.steps.userData.letters.forEach((m, i) => { m.position.y = 0; m.scale.setScalar(1); });
  const path = cp([P(0, [2.5, 1.2, 1.5], [0, 2.6, -14], 50), P(2.7, [1.5, 2.6, -1.5], [0, 3.2, -14], 46)], { shake: .02 });
  path.apply(camera, lt); post.focus.value = 12; post.aperture.value = .004;
  post.fade.value = smooth(range(lt, 1.9, 2.7));
}, { tin: 'flash' });

export function shotAt(t) { for (let i = 0; i < shots.length; i++) if (t < shots[i].b) return i; return shots.length - 1; }
