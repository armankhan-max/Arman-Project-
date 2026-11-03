// Frame driver: picks the shot, runs it, adds camera motion blur + transitions, renders.
import * as THREE from 'three';
import * as C from './core.js';
import { camera, getSet, dropSetsExcept, initAssets, SETS } from './sets.js';
import { shots, shotAt, DURATION } from './timeline.js';

const vpPrev = new THREE.Matrix4(), tmpV = new THREE.Vector3();
function runShot(s, t) {
  const S = getSet(s.set);
  C.postDefaults();
  s.fn(S, t - s.a, t);
  camera.updateMatrixWorld();
  return S;
}
function transition(i, t) {
  const s = shots[i]; let blurX = 0, zoom = 0, flash = 0, fade = 0;
  const edge = (bt, type, side) => { // side: -1 before boundary, +1 after
    const d = Math.abs(t - bt);
    if (type === 'whip') { const k = 1 - C.clamp(d / .13); blurX += k * k * .09 * (side < 0 ? 1 : 1); }
    if (type === 'zoom') { const k = 1 - C.clamp(d / .16); zoom += k * k * .16; }
    if (type === 'flash') { const k = side < 0 ? 1 - C.clamp(d / .1) : 1 - C.clamp(d / .35); flash += k * k; }
    if (type === 'dip') { const k = 1 - C.clamp(d / .2); fade += C.smooth(k); }
  };
  const prev = shots[i - 1], next = shots[i + 1];
  const tin = s.tin || prev?.tout; if (tin && i > 0) edge(s.a, tin, 1);
  const tout = s.tout || next?.tin; if (tout && next) edge(s.b, tout, -1);
  return { blurX, zoom, flash: Math.min(1, flash), fade: Math.min(1, fade) };
}
window.frame = (t) => {
  const i = shotAt(t), s = shots[i];
  // keep caches small: current + next set
  if (SETS.size > 3) dropSetsExcept([s.set, shots[i + 1]?.set, shots[i - 1]?.set].filter(Boolean));
  // previous camera (half a frame earlier) for motion blur
  runShot(s, t - 1 / 50);
  vpPrev.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
  const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  const focusPt = camera.position.clone().addScaledVector(fwd, Math.max(1, C.post.focus.value));
  const S = runShot(s, t);
  const p0 = focusPt.clone().applyMatrix4(vpPrev);
  const vp = new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
  const p1 = focusPt.clone().applyMatrix4(vp);
  let mx = (p1.x - p0.x) * .5 * 1.0, my = (p1.y - p0.y) * .5;
  const ml = Math.hypot(mx, my); if (ml > .05) { mx *= .05 / ml; my *= .05 / ml; }
  if (ml < .0012) { mx = 0; my = 0; }
  const tr = transition(i, t);
  const dx = C.post.dirBlur.value.x + mx + tr.blurX, dy = C.post.dirBlur.value.y + my;
  C.post.dirBlur.value.set(dx, dy);
  C.post.zoomBlur.value += tr.zoom;
  C.post.flash.value = Math.min(1, C.post.flash.value + tr.flash);
  C.post.fade.value = Math.min(1, C.post.fade.value + tr.fade);
  C.renderFrame(S.scene, camera, t);
};
window.grab = (q = .93) => C.renderer.domElement.toDataURL('image/jpeg', q);
window.DURATION = DURATION;
window.SHOTS = shots.map((s) => [s.a, s.b, s.set]);
await initAssets();
window.ready = true;
