// Easing + keyframe helpers. Everything is a pure function of the frame number.
export type Ease = (t: number) => number;
export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const linear: Ease = (t) => t;
export const easeOutCubic: Ease = (t) => 1 - Math.pow(1 - t, 3);
export const easeInCubic: Ease = (t) => t * t * t;
export const easeInOutCubic: Ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const easeInOutSine: Ease = (t) => -(Math.cos(Math.PI * t) - 1) / 2;
export const easeOutExpo: Ease = (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t));
export const easeInExpo: Ease = (t) => (t <= 0 ? 0 : Math.pow(2, 10 * t - 10));
export const easeOutQuad: Ease = (t) => 1 - (1 - t) * (1 - t);
export const easeInQuad: Ease = (t) => t * t;
// easeOutBack with ~6% overshoot
export const easeOutBack: Ease = (t) => {
  const c1 = 0.9, c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
};
export const easeOutBackBig: Ease = (t) => {
  const c1 = 1.9, c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
};
// SNAP_ZOOM: easeOutExpo with a 2% overshoot that settles.
export const snapEase: Ease = (t) => {
  const e = easeOutExpo(t);
  return e + 0.02 * Math.sin(Math.PI * clamp(t * 1.4)) ;
};

/** progress of frame f inside [a, b] with easing */
export const prog = (f: number, a: number, b: number, e: Ease = linear) => e(clamp((f - a) / Math.max(1e-6, b - a)));

/** piecewise keyframes: [[frame, value, easeIntoThisKey?], ...] */
export type Key = [number, number, Ease?];
export function kf(f: number, keys: Key[]): number {
  if (f <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [f1, v1, e] = keys[i];
    const [f0, v0] = keys[i - 1];
    if (f <= f1) return lerp(v0, v1, (e ?? easeInOutCubic)(clamp((f - f0) / Math.max(1e-6, f1 - f0))));
  }
  return keys[keys.length - 1][1];
}

/** deterministic pseudo random in [0,1) */
export function rnd(seed: number) {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

/** critically-damped follow (spring stiffness/damping) of a target signal, evaluated deterministically */
export function damped(f: number, target: (fr: number) => number, stiffness = 120, damping = 20, mass = 1, fps = 60) {
  const start = Math.max(0, Math.floor(f) - 240);
  let x = target(start), v = 0;
  const dt = 1 / fps;
  for (let i = start; i < f; i++) {
    const tgt = target(i + 1);
    const a = (stiffness * (tgt - x) - damping * v) / mass;
    v += a * dt; x += v * dt;
  }
  return x;
}

/** pop-in scale: 0 -> overshoot -> 1 */
export const popIn = (f: number, at: number, dur = 10) => (f < at ? 0 : easeOutBackBig(clamp((f - at) / dur)));
/** decaying shake */
export function shake(f: number, at: number, amp = 14, dur = 6, seed = 1) {
  if (f < at || f > at + dur) return [0, 0];
  const k = 1 - (f - at) / dur;
  return [Math.sin((f - at) * 2.7 + seed) * amp * k, Math.cos((f - at) * 3.3 + seed * 2) * amp * k];
}
/** darken a #rrggbb color by pct (0.18 = 18%) */
export function shade(hex: string, pct = 0.18) {
  const n = parseInt(hex.slice(1), 16);
  const r = Math.round(((n >> 16) & 255) * (1 - pct));
  const g = Math.round(((n >> 8) & 255) * (1 - pct));
  const b = Math.round((n & 255) * (1 - pct));
  return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}
