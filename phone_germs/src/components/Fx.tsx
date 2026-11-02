import React from 'react';
import {clamp, easeOutBack, easeOutBackBig, easeOutCubic, rnd} from '../lib/ease';
import {INK} from './Hero';

export const Skull: React.FC<{x: number; y: number; s?: number; t: number}> = ({x, y, s = 1, t}) => {
  const k = t <= 0 ? 0 : easeOutBackBig(clamp(t / 10));
  if (k <= 0) return null;
  return (
    <g transform={`translate(${x} ${y}) scale(${s * k}) rotate(${Math.sin(t * 0.15) * 6})`}>
      <circle r={70} fill="#E23B2E" stroke={INK} strokeWidth={5} />
      <path d="M -34 6 C -40 -40 40 -40 34 6 L 26 14 L 26 30 L -26 30 L -26 14 Z" fill="#fff" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
      <circle cx={-14} cy={-4} r={9} fill={INK} /><circle cx={14} cy={-4} r={9} fill={INK} />
      <path d="M -12 30 L -12 20 M 0 30 L 0 20 M 12 30 L 12 20" stroke={INK} strokeWidth={4} />
    </g>
  );
};

/** wavy stink lines rising */
export const Stink: React.FC<{x: number; y: number; f: number; s?: number; col?: string; op?: number}> = ({x, y, f, s = 1, col = '#7CC36B', op = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${s})`} opacity={op}>
    {[-60, 0, 60].map((dx, i) => {
      const ph = ((f * 0.9 + i * 25) % 75) / 75;
      return (
        <path key={i} d={`M ${dx} 0 q 18 -25 0 -50 q -18 -25 0 -50 q 18 -25 0 -50`} stroke={col} strokeWidth={10} fill="none" strokeLinecap="round"
          transform={`translate(${Math.sin(f * 0.08 + i) * 8} ${-ph * 90})`} opacity={Math.sin(ph * Math.PI)} />
      );
    })}
  </g>
);

/** CLEAN_SPARKLE: 12 four-point stars bursting over 0.5s (30 frames) */
export const Sparkle: React.FC<{x: number; y: number; t: number; s?: number; n?: number; seed?: number; rad?: number}> = ({x, y, t, s = 1, n = 12, seed = 3, rad = 180}) => {
  if (t < 0 || t > 40) return null;
  const k = clamp(t / 30);
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      {Array.from({length: n}).map((_, i) => {
        const a = (i / n) * Math.PI * 2 + rnd(seed + i) * 0.5;
        const d = rad * (0.4 + 0.6 * rnd(seed * 3 + i)) * easeOutCubic(k);
        const sz = (14 + 16 * rnd(seed + i * 7)) * Math.sin(Math.PI * clamp(t / (30 + 10 * rnd(i))));
        if (sz <= 0) return null;
        return (
          <path key={i} transform={`translate(${Math.cos(a) * d} ${Math.sin(a) * d}) rotate(${t * 4 + i * 20}) scale(${sz / 20})`}
            d="M 0 -20 Q 3 -3 20 0 Q 3 3 0 20 Q -3 3 -20 0 Q -3 -3 0 -20 Z" fill="#fff" stroke={INK} strokeWidth={2.5} />
        );
      })}
    </g>
  );
};

/** thick red arrow with white outline, slides in with easeOutBack; points toward +x of its local frame */
export const Arrow: React.FC<{x: number; y: number; rot?: number; t: number; s?: number}> = ({x, y, rot = 0, t, s = 1}) => {
  if (t < 0) return null;
  const k = easeOutBack(clamp(t / 14));
  const bob = Math.sin(t * 0.2) * 10;
  const d = 'M -170 -26 L 0 -26 L 0 -62 L 90 0 L 0 62 L 0 26 L -170 26 Z';
  return (
    <g transform={`translate(${x} ${y}) rotate(${rot}) translate(${-(1 - k) * 260 + bob} 0) scale(${s})`} opacity={clamp(t / 4)}>
      <path d={d} fill="none" stroke={INK} strokeWidth={26} strokeLinejoin="round" />
      <path d={d} fill="#E23B2E" stroke="#fff" strokeWidth={12} strokeLinejoin="round" />
    </g>
  );
};

export const Sweat: React.FC<{x: number; y: number; t: number; s?: number}> = ({x, y, t, s = 1}) => {
  const ph = (t % 40) / 40;
  return (
    <g transform={`translate(${x} ${y + ph * 40}) scale(${s})`} opacity={Math.sin(ph * Math.PI)}>
      <path d="M 0 -22 Q 16 0 0 12 Q -16 0 0 -22 Z" fill="#7EC8E3" stroke={INK} strokeWidth={4} />
    </g>
  );
};

export const Exclaim: React.FC<{x: number; y: number; t: number; s?: number}> = ({x, y, t, s = 1}) => {
  if (t < 0) return null;
  const k = easeOutBackBig(clamp(t / 8));
  return (
    <g transform={`translate(${x} ${y}) scale(${s * k}) rotate(${Math.sin(t * 0.4) * 6})`}>
      <path d="M -12 -70 L 12 -70 L 7 0 L -7 0 Z" fill="#FFD84A" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
      <circle cx={0} cy={22} r={11} fill="#FFD84A" stroke={INK} strokeWidth={5} />
    </g>
  );
};

/** small pop burst ring (for germs popping) */
export const PopBurst: React.FC<{x: number; y: number; t: number; col?: string; s?: number}> = ({x, y, t, col = '#39E35B', s = 1}) => {
  if (t < 0 || t > 14) return null;
  const k = easeOutCubic(t / 14);
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`} opacity={1 - k}>
      <circle r={20 + 50 * k} fill="none" stroke={col} strokeWidth={8 * (1 - k) + 1} />
      {Array.from({length: 8}).map((_, i) => {
        const a = (i / 8) * Math.PI * 2;
        return <line key={i} x1={Math.cos(a) * (30 + 40 * k)} y1={Math.sin(a) * (30 + 40 * k)} x2={Math.cos(a) * (44 + 60 * k)} y2={Math.sin(a) * (44 + 60 * k)} stroke={INK} strokeWidth={5} strokeLinecap="round" />;
      })}
    </g>
  );
};

/** DANGER: red radial glow behind something */
export const DangerGlow: React.FC<{x: number; y: number; rx: number; ry: number; amt: number; f: number}> = ({x, y, rx, ry, amt, f}) => (
  amt <= 0 ? null : <ellipse cx={x} cy={y} rx={rx * (1 + 0.04 * Math.sin(f * 0.2))} ry={ry * (1 + 0.04 * Math.sin(f * 0.2))} fill="url(#dangerGrad)" opacity={amt} />
);
export const WarmGlow: React.FC<{x: number; y: number; r: number; amt: number; f: number}> = ({x, y, r, amt, f}) => (
  amt <= 0 ? null : <circle cx={x} cy={y} r={r * (1 + 0.05 * Math.sin(f * 0.12))} fill="url(#warm)" opacity={amt} />
);

/** speed lines (screen space) */
export const SpeedLines: React.FC<{amt: number; f: number; vertical?: boolean}> = ({amt, f, vertical}) => {
  if (amt <= 0.01) return null;
  return (
    <g opacity={amt}>
      {Array.from({length: 18}).map((_, i) => {
        const y = (rnd(i + Math.floor(f / 2) * 0.13) * 1920);
        const len = 200 + rnd(i * 3) * 400;
        const x = rnd(i * 7 + f) * 1080;
        return vertical
          ? <line key={i} x1={rnd(i) * 1080} y1={(x * 2) % 1920} x2={rnd(i) * 1080} y2={(x * 2) % 1920 + len} stroke="#fff" strokeWidth={4} opacity={0.5} />
          : <line key={i} x1={x - len} y1={y} x2={x} y2={y} stroke="#fff" strokeWidth={4} opacity={0.5} />;
      })}
    </g>
  );
};
