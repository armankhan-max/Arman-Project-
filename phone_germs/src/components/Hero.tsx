import React from 'react';
import {clamp, easeOutBack, shade} from '../lib/ease';

export const INK = '#111111';
export const HOOD = '#4FA3E0';
export const HOOD_D = shade(HOOD);
export const SKIN = '#F7F7F5';
export const SKIN_D = shade(SKIN);
export const HAIR = '#3A2A20';

export type Expr = 'neutral' | 'smug' | 'shocked' | 'disgusted' | 'scared' | 'happy' | 'angry' | 'focused';
export type Limb = [number, number]; // [upper angle, lower angle relative] in deg; 0 = straight down, + = toward +x

export type HeroProps = {
  x: number; y: number; s?: number; f: number;
  flip?: boolean;          // face left
  lean?: number;           // torso lean (deg)
  armL?: Limb; armR?: Limb; legL?: Limb; legR?: Limb;
  expr?: Expr; exprAt?: number; // frame expression changed (for pop)
  look?: [number, number];  // face direction offset (-1..1)
  tint?: number;            // green disgust tint 0..1
  sit?: number;             // sitting: hip-to-floor distance (local units). 0 = standing
  squash?: number;          // vertical scale at feet (1 = none)
  holdR?: React.ReactNode;  // drawn in hand-local coords (origin = hand center)
  holdL?: React.ReactNode;
  thumbR?: boolean; thumbL?: boolean;
  headTurn?: number;        // extra head tilt (deg)
  hairLag?: number;         // hair bounce (local px)
  seed?: number;
  shadow?: boolean;
  bodyTurn?: number;        // 0 = front, 1 = side profile (narrows torso, shifts face)
};

const UA = 92, FA = 84, TH = 108, SHN = 102;
const HIP_Y = -212, SH_Y = -378, HEAD_Y = -500, HEAD_R = 90;

const rad = (d: number) => (d * Math.PI) / 180;
const seg = (x: number, y: number, ang: number, len: number): [number, number] => [x + Math.sin(rad(ang)) * len, y + Math.cos(rad(ang)) * len];

export function heroRig(p: HeroProps) {
  const sitting = !!p.sit && p.sit > 0;
  const armL = p.armL ?? [12, -8], armR = p.armR ?? [-12, 8];
  const legL = p.legL ?? [6, -4], legR = p.legR ?? [-6, 4];
  const turn = p.bodyTurn ?? 0;
  const shw = 54 * (1 - 0.45 * turn);
  const shL: [number, number] = [-shw, SH_Y + 8], shR: [number, number] = [shw, SH_Y + 8];
  const elL = seg(...shL, armL[0], UA), elR = seg(...shR, armR[0], UA);
  const haL = seg(...elL, armL[0] + armL[1], FA), haR = seg(...elR, armR[0] + armR[1], FA);
  const hipL: [number, number] = [-22, HIP_Y], hipR: [number, number] = [22, HIP_Y];
  let knL: [number, number], knR: [number, number], ftL: [number, number], ftR: [number, number];
  if (sitting) {
    const fore = 30;
    knL = [hipL[0] - 14, hipL[1] + fore]; knR = [hipR[0] + 14, hipR[1] + fore];
    ftL = [knL[0] - 6, HIP_Y + p.sit!]; ftR = [knR[0] + 6, HIP_Y + p.sit!];
  } else {
    knL = seg(...hipL, legL[0], TH); knR = seg(...hipR, legR[0], TH);
    ftL = seg(...knL, legL[0] + legL[1], SHN); ftR = seg(...knR, legR[0] + legR[1], SHN);
  }
  return {shL, shR, elL, elR, haL, haR, hipL, hipR, knL, knR, ftL, ftR};
}

/** world position of a hand */
export function heroHand(p: HeroProps, side: 'L' | 'R'): [number, number] {
  const r = heroRig(p);
  const s = p.s ?? 1;
  let [hx, hy] = side === 'L' ? r.haL : r.haR;
  // apply lean around hip
  const lean = rad(p.lean ?? 0);
  const dx = hx, dy = hy - HIP_Y;
  hx = dx * Math.cos(lean) - dy * Math.sin(lean);
  hy = HIP_Y + dx * Math.sin(lean) + dy * Math.cos(lean);
  if (p.flip) hx = -hx;
  return [p.x + hx * s, p.y + hy * s * (p.squash ?? 1)];
}

const Tube: React.FC<{pts: [number, number][]; w: number; col: string}> = ({pts, w, col}) => {
  const d = 'M' + pts.map((q) => q.join(' ')).join(' L');
  return (
    <>
      <path d={d} stroke={INK} strokeWidth={w + 12} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} stroke={col} strokeWidth={w} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </>
  );
};

const Hand: React.FC<{at: [number, number]; thumb?: boolean; hold?: React.ReactNode; flip?: boolean}> = ({at, thumb, hold, flip}) => (
  <g transform={`translate(${at[0]} ${at[1]})`}>
    {hold && <g transform={flip ? 'scale(-1 1)' : undefined}>{hold}</g>}
    {thumb && (
      <g>
        <rect x={-7} y={-44} width={16} height={34} rx={8} fill={SKIN} stroke={INK} strokeWidth={6} />
      </g>
    )}
    <circle r={19} fill={SKIN} stroke={INK} strokeWidth={6} />
    <path d="M 4 -10 A 12 12 0 0 1 10 6" stroke={SKIN_D} strokeWidth={5} fill="none" strokeLinecap="round" />
  </g>
);

export const Face: React.FC<{expr: Expr; f: number; lookX: number; lookY: number; seed: number; tint: number}> = ({expr, f, lookX, lookY, seed, tint}) => {
  const fx = lookX * 26, fy = lookY * 14;
  const blinkPhase = (f + seed * 37) % 170;
  const blink = blinkPhase < 6 && expr !== 'happy' ? 0.12 : 1;
  const eyeS = expr === 'shocked' ? 1.4 : expr === 'scared' ? 1.25 : 1;
  const ex = 30, ey = HEAD_Y - 2 + fy;
  const brow = (side: -1 | 1) => {
    const bx = fx + side * ex, by = ey - 34 * (eyeS > 1 ? 1.25 : 1);
    let a = 0, dy = 0; // a>0 = inner end lower
    switch (expr) {
      case 'angry': case 'focused': a = 18; break;
      case 'disgusted': a = 14; dy = 4; break;
      case 'scared': a = -22; dy = -6; break;
      case 'shocked': a = -6; dy = -16; break;
      case 'smug': a = side === -1 ? -16 : 8; dy = side === -1 ? -12 : 2; break;
      case 'happy': a = -6; dy = -6; break;
      default: a = 0;
    }
    const ang = rad(a) * -side;
    const L = 20;
    return (
      <path d={`M ${bx - L * Math.cos(ang)} ${by + dy - L * Math.sin(ang)} L ${bx + L * Math.cos(ang)} ${by + dy + L * Math.sin(ang)}`}
        stroke={INK} strokeWidth={10} strokeLinecap="round" />
    );
  };
  const mx = fx, my = HEAD_Y + 40 + fy;
  let mouth: React.ReactNode;
  switch (expr) {
    case 'shocked': mouth = <ellipse cx={mx} cy={my + 4} rx={12} ry={17} fill={INK} />; break;
    case 'scared': mouth = <path d={`M ${mx - 18} ${my + 6} q 6 -8 12 0 q 6 8 12 0 q 6 -8 12 0`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />; break;
    case 'disgusted': mouth = (
      <g>
        <path d={`M ${mx - 10} ${my + 6} q 6 22 20 2`} fill="#FF6B8A" stroke={INK} strokeWidth={5} />
        <path d={`M ${mx - 24} ${my + 4} q 8 -10 16 0 q 8 10 16 0 q 8 -10 16 0`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />
      </g>); break;
    case 'smug': mouth = <path d={`M ${mx - 16} ${my + 4} Q ${mx + 4} ${my + 10} ${mx + 20} ${my - 6}`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />; break;
    case 'happy': mouth = <path d={`M ${mx - 22} ${my - 2} Q ${mx} ${my + 30} ${mx + 22} ${my - 2} Z`} fill={INK} stroke={INK} strokeWidth={5} strokeLinejoin="round" />; break;
    case 'angry': mouth = <path d={`M ${mx - 14} ${my + 8} Q ${mx} ${my - 4} ${mx + 14} ${my + 8}`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />; break;
    case 'focused': mouth = <path d={`M ${mx - 10} ${my + 4} L ${mx + 10} ${my + 4}`} stroke={INK} strokeWidth={6} strokeLinecap="round" />; break;
    default: mouth = <path d={`M ${mx - 12} ${my + 2} Q ${mx} ${my + 8} ${mx + 12} ${my + 2}`} stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />;
  }
  const eye = (side: -1 | 1) => {
    if (expr === 'happy') return <path key={side} d={`M ${fx + side * ex - 11} ${ey + 3} q 11 -14 22 0`} stroke={INK} strokeWidth={7} fill="none" strokeLinecap="round" />;
    return <ellipse key={side} cx={fx + side * ex} cy={ey} rx={9 * eyeS} ry={11 * eyeS * blink} fill={INK} />;
  };
  return (
    <g>
      {eye(-1)}{eye(1)}
      {brow(-1)}{brow(1)}
      {mouth}
      {tint > 0 && null}
    </g>
  );
};

export const Hero: React.FC<HeroProps> = (p) => {
  const s = p.s ?? 1;
  const f = p.f;
  const seed = p.seed ?? 1;
  const r = heroRig(p);
  const breathe = 1 + 0.01 * (1 + Math.sin((f / 120) * Math.PI * 2));
  const expr = p.expr ?? 'neutral';
  const popT = p.exprAt !== undefined ? clamp((f - p.exprAt) / 4) : 1;
  const facePop = p.exprAt !== undefined && f >= p.exprAt ? 1 + 0.1 * (1 - easeOutBack(popT)) * (popT < 1 ? 1 : 0) + (popT < 1 ? 0.1 * (1 - popT) : 0) : 1;
  const scaredShake = expr === 'scared' ? Math.sin(f * 2.1) * 3 : 0;
  const look = p.look ?? [0, 0];
  const turn = p.bodyTurn ?? 0;
  const lookX = clamp(look[0] + turn * 0.9, -1.2, 1.2);
  const tint = p.tint ?? 0;
  const hair = p.hairLag ?? Math.sin(f * 0.21 + seed) * 1.2;
  const stringSwing = Math.sin(f * 0.13 + seed) * 6 + (p.lean ?? 0) * 0.6;
  const tw = 1 - 0.38 * turn; // torso width factor
  const sq = p.squash ?? 1;
  const headId = `hc${seed}`;
  const torsoId = `tc${seed}`;
  const torso = `M ${-58 * tw} ${SH_Y + 2} Q ${-66 * tw} ${SH_Y - 10} ${-40 * tw} ${SH_Y - 16} L ${40 * tw} ${SH_Y - 16} Q ${66 * tw} ${SH_Y - 10} ${58 * tw} ${SH_Y + 2} L ${62 * tw} ${HIP_Y + 4} Q ${0} ${HIP_Y + 18} ${-62 * tw} ${HIP_Y + 4} Z`;
  const flipS = p.flip ? -1 : 1;
  return (
    <g transform={`translate(${p.x} ${p.y}) scale(${s * flipS} ${s * sq})`}>
      {p.shadow !== false && <ellipse cx={0} cy={4} rx={110} ry={20} fill="url(#shadowGrad)" />}
      <g transform={`rotate(${p.lean ?? 0} 0 ${HIP_Y})`}>
        {/* legs */}
        <Tube pts={[r.hipL, r.knL, r.ftL]} w={26} col={SKIN} />
        <Tube pts={[r.hipR, r.knR, r.ftR]} w={26} col={SKIN} />
        {[r.ftL, r.ftR].map((ft, i) => (
          <ellipse key={i} cx={ft[0] + (i ? 8 : -8) + turn * 10} cy={ft[1] - 4} rx={27} ry={18} fill={SKIN} stroke={INK} strokeWidth={6} />
        ))}
        {/* back arm (left) */}
        <Tube pts={[r.shL, r.elL]} w={30} col={HOOD} />
        <Tube pts={[r.elL, r.haL]} w={22} col={SKIN} />
        <Hand at={r.haL} thumb={p.thumbL} hold={p.holdL} flip={p.flip} />
        {/* torso / hoodie */}
        <g transform={`translate(0 ${HIP_Y}) scale(1 ${breathe}) translate(0 ${-HIP_Y})`}>
          <defs><clipPath id={torsoId}><path d={torso} /></clipPath></defs>
          <path d={torso} fill={HOOD} />
          <g clipPath={`url(#${torsoId})`}>
            <rect x={20 * tw} y={SH_Y - 30} width={80} height={220} fill={HOOD_D} />
            <rect x={-70} y={HIP_Y - 10} width={140} height={30} fill={HOOD_D} />
          </g>
          <path d={torso} fill="none" stroke={INK} strokeWidth={6} strokeLinejoin="round" />
          {/* hood collar */}
          <path d={`M ${-40 * tw} ${SH_Y - 14} Q 0 ${SH_Y + 26} ${40 * tw} ${SH_Y - 14}`} fill={HOOD_D} stroke={INK} strokeWidth={5} strokeLinejoin="round" />
          {/* drawstrings */}
          {[-12, 12].map((dx, i) => (
            <g key={i}>
              <path d={`M ${dx * tw} ${SH_Y + 2} q ${stringSwing * 0.4} 22 ${stringSwing * 0.7 + dx * 0.15} 44`} stroke="#FFFFFF" strokeWidth={5} fill="none" strokeLinecap="round" />
              <circle cx={dx * tw + stringSwing * 0.7 + dx * 0.15} cy={SH_Y + 48} r={3.5} fill="#FFFFFF" stroke={INK} strokeWidth={1.5} />
            </g>
          ))}
          {/* chest print */}
          {turn < 0.5 && (
            <text x={0} y={SH_Y + 76} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={13} fill="#FFFFFF" letterSpacing={0.5}>NOT THE HERO</text>
          )}
          {/* kangaroo pocket */}
          <path d={`M ${-38 * tw} ${HIP_Y - 22} L ${-30 * tw} ${HIP_Y - 66} L ${30 * tw} ${HIP_Y - 66} L ${38 * tw} ${HIP_Y - 22} Z`} fill={HOOD_D} stroke={INK} strokeWidth={4} strokeLinejoin="round" />
        </g>
        {/* neck */}
        <path d={`M 0 ${SH_Y - 10} L 0 ${HEAD_Y + HEAD_R - 6}`} stroke={INK} strokeWidth={20} strokeLinecap="round" />
        <path d={`M 0 ${SH_Y - 10} L 0 ${HEAD_Y + HEAD_R - 6}`} stroke={SKIN} strokeWidth={9} strokeLinecap="round" />
        {/* head */}
        <g transform={`translate(${scaredShake} 0) rotate(${p.headTurn ?? 0} 0 ${HEAD_Y + 60})`}>
          <g transform={`translate(0 ${HEAD_Y}) scale(${facePop}) translate(0 ${-HEAD_Y})`}>
            <defs><clipPath id={headId}><circle cx={0} cy={HEAD_Y} r={HEAD_R} /></clipPath></defs>
            <circle cx={0} cy={HEAD_Y} r={HEAD_R} fill={SKIN_D} />
            <g clipPath={`url(#${headId})`}>
              <circle cx={-14} cy={HEAD_Y - 10} r={HEAD_R - 4} fill={SKIN} />
              {tint > 0 && <circle cx={0} cy={HEAD_Y} r={HEAD_R} fill="#9BE59B" opacity={0.4 * tint} />}
              {/* hair cap */}
              <g transform={`translate(0 ${hair})`}>
                <path d={`M ${-HEAD_R - 4} ${HEAD_Y - 18} C ${-HEAD_R} ${HEAD_Y - 120} ${HEAD_R} ${HEAD_Y - 120} ${HEAD_R + 4} ${HEAD_Y - 18}
                  C ${70} ${HEAD_Y - 46} ${40} ${HEAD_Y - 50} ${8 + lookX * 20} ${HEAD_Y - 56}
                  L ${lookX * 20} ${HEAD_Y - 40} L ${-8 + lookX * 20} ${HEAD_Y - 56}
                  C ${-40} ${HEAD_Y - 50} ${-70} ${HEAD_Y - 46} ${-HEAD_R - 4} ${HEAD_Y - 18} Z`} fill={HAIR} />
                <path d={`M ${-50} ${HEAD_Y - 78} Q ${-20} ${HEAD_Y - 92} ${10} ${HEAD_Y - 84}`} stroke="#5A4434" strokeWidth={8} fill="none" strokeLinecap="round" />
              </g>
            </g>
            <circle cx={0} cy={HEAD_Y} r={HEAD_R} fill="none" stroke={INK} strokeWidth={6} />
            <g transform={`translate(0 ${HEAD_Y + 10}) scale(${p.exprAt !== undefined && f >= p.exprAt && f < p.exprAt + 4 ? 1.1 - 0.025 * (f - p.exprAt) : 1}) translate(0 ${-HEAD_Y - 10})`}>
              <Face expr={expr} f={f} lookX={lookX} lookY={look[1]} seed={seed} tint={tint} />
            </g>
          </g>
        </g>
        {/* front arm (right) */}
        <Tube pts={[r.shR, r.elR]} w={30} col={HOOD} />
        <Tube pts={[r.elR, r.haR]} w={22} col={SKIN} />
        <Hand at={r.haR} thumb={p.thumbR} hold={p.holdR} flip={p.flip} />
      </g>
    </g>
  );
};

/** two-link IK: returns a Limb that puts the hand at a WORLD target (assumes lean 0). bend: +1 / -1 elbow side */
export function armTo(p: HeroProps, side: 'L' | 'R', target: [number, number], bend = 1): Limb {
  const s = p.s ?? 1, sq = p.squash ?? 1;
  const lx = ((target[0] - p.x) / s) * (p.flip ? -1 : 1);
  const ly = (target[1] - p.y) / (s * sq);
  const turn = p.bodyTurn ?? 0;
  const shw = 54 * (1 - 0.45 * turn);
  const sh: [number, number] = [side === 'L' ? -shw : shw, SH_Y + 8];
  const dx = lx - sh[0], dy = ly - sh[1];
  const d = Math.min(UA + FA - 0.5, Math.max(Math.abs(UA - FA) + 1, Math.hypot(dx, dy)));
  const base = (Math.atan2(dx, dy) * 180) / Math.PI;
  const alpha = (Math.acos((UA * UA + d * d - FA * FA) / (2 * UA * d)) * 180) / Math.PI;
  const upper = base + bend * alpha;
  const el = seg(sh[0], sh[1], upper, UA);
  const fore = (Math.atan2(lx - el[0], ly - el[1]) * 180) / Math.PI;
  let rel = fore - upper;
  while (rel > 180) rel -= 360;
  while (rel < -180) rel += 360;
  return [upper, rel];
}
/** walk cycle legs from a phase (radians) */
export function walkLegs(phase: number, amt = 1): {legL: Limb; legR: Limb; bob: number} {
  const a = Math.sin(phase) * 28 * amt;
  const kneeL = Math.max(0, -Math.cos(phase)) * 30 * amt;
  const kneeR = Math.max(0, Math.cos(phase)) * 30 * amt;
  return {legL: [a, -kneeL], legR: [-a, -kneeR], bob: Math.abs(Math.sin(phase)) * 8 * amt};
}
