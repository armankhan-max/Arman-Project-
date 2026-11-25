// Pictogram human figure: 2D forward kinematics + animated move/stretch poses.
// Angles in degrees. Limbs: 0 = hanging straight down, positive = swings toward +x.
// Torso lean: 0 = upright, positive = leans toward +x.

const D = Math.PI / 180;
const L = { torso: 1.18, upper: 0.62, fore: 0.6, thigh: 0.82, shin: 0.82, head: 0.34, neck: 0.46, width: 0.3 };

export function fk(p) {
  const lean = (p.lean || 0) * D;
  const P = [0, 0];
  const N = [P[0] + Math.sin(lean) * L.torso, P[1] + Math.cos(lean) * L.torso];
  const hl = lean + (p.headTilt || 0) * D;
  const Hd = [N[0] + Math.sin(hl) * L.neck, N[1] + Math.cos(hl) * L.neck];
  const limb = (o, a1, a2, l1, l2) => {
    const A = a1 * D, B = a2 * D;
    const j = [o[0] + Math.sin(A) * l1, o[1] - Math.cos(A) * l1];
    const e = [j[0] + Math.sin(B) * l2, j[1] - Math.cos(B) * l2];
    return [o, j, e];
  };
  // arm angles are relative to the torso so a leaning body carries its arms
  const ld = p.lean || 0;
  const armL = limb(N, (p.shL || 0) + ld, (p.shL || 0) + ld + (p.elL || 0), L.upper, L.fore);
  const armR = limb(N, (p.shR || 0) + ld, (p.shR || 0) + ld + (p.elR || 0), L.upper, L.fore);
  const legL = limb(P, p.hipL || 0, (p.hipL || 0) - (p.knL || 0), L.thigh, L.shin);
  const legR = limb(P, p.hipR || 0, (p.hipR || 0) - (p.knR || 0), L.thigh, L.shin);
  let pts = { P, N, Hd, armL, armR, legL, legR };
  // put the lowest point of the body on the ground (y = 0), then add any lift
  let minY = Infinity;
  for (const lg of [legL, legR, armL, armR]) for (const q of lg) minY = Math.min(minY, q[1]);
  minY = Math.min(minY, P[1]);
  const lift = p.lift || 0;
  const dy = -minY + lift;
  const sh = (q) => [q[0] + (p.dx || 0), q[1] + dy];
  const mapL = (lg) => lg.map(sh);
  return { P: sh(P), N: sh(N), Hd: sh(Hd), armL: mapL(armL), armR: mapL(armR), legL: mapL(legL), legR: mapL(legR) };
}

export function lerpPose(a, b, u) {
  const o = {};
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k of keys) o[k] = (a[k] || 0) * (1 - u) + (b[k] || 0) * u;
  return o;
}

const ss = (u) => { u = Math.min(1, Math.max(0, u)); return u * u * (3 - 2 * u); };

// ---------------------------------------------------------------- move poses
export function runPose(ph, knees = 0) {
  const s = Math.sin(ph), c = Math.cos(ph);
  const legA = (q) => {
    const sq = Math.sin(q), cq = Math.cos(q);
    const hip = 6 + 42 * sq + knees * 45 * Math.max(0, sq);
    const kn = 18 + 70 * Math.max(0, -cq) * (0.6 + 0.4 * Math.max(0, -sq)) + 35 * Math.max(0, sq) + knees * 50 * Math.max(0, sq);
    return [hip, kn];
  };
  const [hL, kL] = legA(ph);
  const [hR, kR] = legA(ph + Math.PI);
  return {
    lean: 12 + knees * -6, headTilt: -6,
    hipL: hL, knL: kL, hipR: hR, knR: kR,
    shL: -42 * s * (1 + knees * 0.3) - 4, elL: 95,
    shR: 42 * s * (1 + knees * 0.3) - 4, elR: 95,
    lift: 0.12 * Math.abs(Math.sin(ph)) + (knees ? 0.1 * Math.abs(c) : 0),
  };
}

export const POSE = {
  stand: { lean: 0, hipL: 4, knL: 4, hipR: -4, knR: 4, shL: 12, elL: 10, shR: -12, elR: 10 },
  crouchPrep: { lean: 22, hipL: 50, knL: 75, hipR: 45, knR: 75, shL: -35, elL: 30, shR: -45, elR: 30 },
  tuck: { lean: 8, hipL: 80, knL: 105, hipR: 70, knR: 100, shL: 165, elL: 15, shR: 150, elR: 20 },
  squat: { lean: 38, headTilt: -20, hipL: 92, knL: 128, hipR: 84, knR: 125, shL: 70, elL: 15, shR: 80, elR: 10 },
  // front view
  frontStand: { lean: 0, hipL: -8, knL: 0, hipR: 8, knR: 0, shL: -18, elL: 0, shR: 18, elR: 0 },
  frontWide: { lean: 0, hipL: -26, knL: -12, hipR: 26, knR: 12, shL: -55, elL: -20, shR: 55, elR: 20 },
};

// side step in a direction (dir = -1 left, +1 right), phase 0..1 loop
export function sideStepPose(u, dir) {
  const k = 0.5 - 0.5 * Math.cos(u * Math.PI * 2);
  const p = lerpPose(POSE.frontStand, POSE.frontWide, k);
  p.lean = dir * 10 * k;
  p.dx = dir * 0.35 * (k - 0.5);
  p.lift = 0.15 * Math.sin(u * Math.PI * 2) ** 2;
  return p;
}

// jump loop: prep -> tuck in the air -> land
export function jumpPose(u) {
  if (u < 0.25) return lerpPose(POSE.stand, POSE.crouchPrep, ss(u / 0.25));
  if (u < 0.75) {
    const a = (u - 0.25) / 0.5;
    const p = lerpPose(POSE.crouchPrep, POSE.tuck, ss(a * 2.2));
    p.lift = 1.1 * Math.sin(Math.PI * a);
    return p;
  }
  return lerpPose(POSE.crouchPrep, POSE.stand, ss((u - 0.75) / 0.25));
}

export function duckPose(u) {
  const k = u < 0.2 ? ss(u / 0.2) : u < 0.7 ? 1 : 1 - ss((u - 0.7) / 0.3);
  return lerpPose(POSE.stand, POSE.squat, k);
}

// ---------------------------------------------------------------- stretches
// all are gently "breathing" holds; side flips between halves (mirror)
export function stretchPose(name, t) {
  const br = Math.sin(t * Math.PI * 2 / 3.75); // one breath per two bars
  if (name === 'side_reach') {
    const tilt = 20 + 6 * br;
    return {
      lean: -tilt, headTilt: -6,
      hipL: -20, knL: 0, hipR: 22, knR: 0,
      shL: -38, elL: 118,            // hand on hip
      shR: 196 + 6 * br, elR: 38,    // arm arching over the head
    };
  }
  if (name === 'lunge_twist') {
    return {
      lean: 18 + 3 * br, headTilt: -25,
      hipL: 88, knL: 92, hipR: -48, knR: 10,
      shL: 8 + 4 * br, elL: 0,       // hand down to the floor
      shR: 182 + 6 * br, elR: 0,     // arm reaching to the sky
    };
  }
  if (name === 'hamstring') {
    // side view forward fold, legs straight, hands reaching to the toes
    const k = 0.5 + 0.5 * br;
    return {
      lean: 98 + 10 * k, headTilt: 20,
      hipL: 6, knL: 0, hipR: -2, knR: 0,
      shL: -92 - 10 * k, elL: 0, shR: -86 - 10 * k, elR: 0,
    };
  }
  if (name === 'arm_circles') {
    // front view, both arms sweeping big circles (dynamic warm-up)
    const a = t * Math.PI * 2 / (60 / 128 * 2) ; // one circle per two beats
    const sw = 90 + 80 * Math.sin(a);
    return {
      lean: 0, hipL: -14, knL: 0, hipR: 14, knR: 0,
      shL: -sw, elL: -10 * Math.cos(a), shR: sw, elR: 10 * Math.cos(a),
      lift: 0,
    };
  }
  if (name === 'recover') {
    // standing tall, hands on hips, chest rising with the breath
    return {
      lean: -2 * br, headTilt: -6 * br,
      hipL: -10, knL: 2, hipR: 10, knR: 2,
      shL: -40, elL: 118, shR: 40, elR: -118,
    };
  }
  if (name === 'quad') {
    return {
      lean: 4, headTilt: 4,
      hipL: 2, knL: 0,
      hipR: -24 + 3 * br, knR: 158,  // heel to the glutes
      shR: -26, elR: -2,             // hand holds the ankle
      shL: 92 + 4 * br, elL: 6,      // arm forward for balance
    };
  }
  return POSE.stand;
}

// ---------------------------------------------------------------- drawing
export function drawFigure(ctx, pose, x, y, scale, color, opt = {}) {
  const f = fk(pose);
  const flip = opt.flip ? -1 : 1;
  const X = (q) => x + q[0] * scale * flip;
  const Y = (q) => y - q[1] * scale;
  const lw = L.width * scale;
  ctx.save();
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  if (opt.shadow !== false) {
    ctx.fillStyle = opt.shadowColor || 'rgba(0,0,0,0.22)';
    ctx.beginPath();
    const lift = pose.lift || 0;
    const sw = Math.max(0.35, 1 - lift * 0.4);
    ctx.ellipse(x + (pose.dx || 0) * scale * flip, y + lw * 0.25, scale * 0.95 * sw, scale * 0.13 * sw, 0, 0, Math.PI * 2);
    ctx.fill();
  }
  const seg = (pts, w, col) => {
    ctx.strokeStyle = col;
    ctx.lineWidth = w;
    ctx.beginPath();
    ctx.moveTo(X(pts[0]), Y(pts[0]));
    for (let i = 1; i < pts.length; i++) ctx.lineTo(X(pts[i]), Y(pts[i]));
    ctx.stroke();
  };
  const gap = opt.gap || null; // outline colour that separates overlapping limbs
  const far = opt.farColor || color;
  seg(f.armL, lw * 0.92, far);
  seg(f.legL, lw, far);
  seg([f.P, f.N], lw * 1.25, color);
  if (gap) { seg(f.legR, lw + scale * 0.12, gap); }
  seg(f.legR, lw, color);
  if (gap) { seg(f.armR, lw * 0.92 + scale * 0.12, gap); }
  seg(f.armR, lw * 0.92, color);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(X(f.Hd), Y(f.Hd), L.head * scale, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
  return f;
}
