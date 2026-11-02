import React from 'react';
import {shade} from '../lib/ease';
import {INK} from './Hero';

export const GERM = {green: '#39E35B', purple: '#9B4DFF', orange: '#FF8A1F', pink: '#FF4FA3'};
export const GERM_COLS = [GERM.green, GERM.purple, GERM.orange, GERM.pink];
export type GermExpr = 'neutral' | 'happy' | 'laugh' | 'scared' | 'smug' | 'shocked' | 'squint';

export type GermProps = {
  x: number; y: number; r?: number; col?: string; f: number; seed?: number;
  expr?: GermExpr; sx?: number; sy?: number; rot?: number; op?: number;
  look?: [number, number]; shades?: boolean; wave?: boolean; scale?: number; armUp?: boolean;
};

/** Round blobby germ with wiggly cilia (7 Hz), eyes, brows and a mouth. Origin = body center. */
export const Germ: React.FC<GermProps> = ({x, y, r = 40, col = GERM.green, f, seed = 1, expr = 'neutral', sx = 1, sy = 1, rot = 0, op = 1, look = [0, 0], shades, wave, scale = 1, armUp}) => {
  if (scale <= 0.001 || op <= 0.001) return null;
  const t = f / 60;
  const N = 15;
  const wob = (a: number) => r * (1 + 0.055 * Math.sin(3 * a + t * 5 + seed) + 0.03 * Math.sin(5 * a - t * 7 + seed * 2));
  const pts: string[] = [];
  for (let i = 0; i <= 36; i++) {
    const a = (i / 36) * Math.PI * 2;
    pts.push(`${(Math.cos(a) * wob(a)).toFixed(1)} ${(Math.sin(a) * wob(a)).toFixed(1)}`);
  }
  const body = 'M' + pts.join(' L') + ' Z';
  const cil = [];
  for (let i = 0; i < N; i++) {
    const a = (i / N) * Math.PI * 2 + seed;
    const w = Math.sin(t * Math.PI * 2 * 7 + i * 1.7 + seed) * 0.35;
    const r0 = wob(a) * 0.96, len = r * 0.32;
    const x0 = Math.cos(a) * r0, y0 = Math.sin(a) * r0;
    const xm = Math.cos(a + w * 0.5) * (r0 + len * 0.55), ym = Math.sin(a + w * 0.5) * (r0 + len * 0.55);
    const x1 = Math.cos(a + w) * (r0 + len), y1 = Math.sin(a + w) * (r0 + len);
    cil.push(`M ${x0.toFixed(1)} ${y0.toFixed(1)} Q ${xm.toFixed(1)} ${ym.toFixed(1)} ${x1.toFixed(1)} ${y1.toFixed(1)}`);
  }
  const cd = cil.join(' ');
  const dark = shade(col, 0.18);
  const eyeR = r * 0.27, ex = r * 0.34, ey = -r * 0.14;
  const lk = [look[0] * eyeR * 0.4, look[1] * eyeR * 0.4];
  const big = expr === 'scared' || expr === 'shocked' ? 1.25 : 1;
  const blink = (f + seed * 23) % 150 < 5 ? 0.15 : 1;
  const sw = Math.max(3, r * 0.09);
  const eyes = expr === 'happy' || expr === 'laugh' || expr === 'squint'
    ? [-1, 1].map((s) => <path key={s} d={`M ${s * ex - eyeR * 0.8} ${ey + 2} q ${eyeR * 0.8} ${-eyeR * 1.1} ${eyeR * 1.6} 0`} stroke={INK} strokeWidth={sw * 1.1} fill="none" strokeLinecap="round" />)
    : [-1, 1].map((s) => (
      <g key={s}>
        <ellipse cx={s * ex} cy={ey} rx={eyeR * big} ry={eyeR * big * blink} fill="#fff" stroke={INK} strokeWidth={sw * 0.8} />
        <circle cx={s * ex + lk[0]} cy={ey + lk[1] * blink} r={eyeR * 0.48 * (expr === 'scared' ? 0.75 : 1)} fill={INK} />
      </g>
    ));
  const ba = expr === 'scared' ? -24 : expr === 'smug' || expr === 'neutral' ? 14 : expr === 'shocked' ? -10 : expr === 'laugh' || expr === 'happy' ? -8 : 10;
  const brows = [-1, 1].map((s) => {
    const a = (ba * Math.PI) / 180 * -s;
    const bx = s * ex, by = ey - eyeR * big - r * 0.13 - (expr === 'smug' && s === -1 ? r * 0.08 : 0), L = r * 0.18;
    return <path key={s} d={`M ${bx - L * Math.cos(a)} ${by - L * Math.sin(a)} L ${bx + L * Math.cos(a)} ${by + L * Math.sin(a)}`} stroke={INK} strokeWidth={sw * 1.2} strokeLinecap="round" />;
  });
  const my = r * 0.36;
  let mouth: React.ReactNode;
  if (expr === 'laugh') {
    const open = 0.5 + 0.5 * Math.abs(Math.sin(t * Math.PI * 8));
    mouth = <path d={`M ${-r * 0.3} ${my - 4} Q 0 ${my - 4 + r * 0.45 * open} ${r * 0.3} ${my - 4} Z`} fill="#5A0F1E" stroke={INK} strokeWidth={sw} strokeLinejoin="round" />;
  } else if (expr === 'happy') {
    mouth = <path d={`M ${-r * 0.28} ${my - 4} Q 0 ${my + r * 0.3} ${r * 0.28} ${my - 4} Z`} fill="#5A0F1E" stroke={INK} strokeWidth={sw} strokeLinejoin="round" />;
  } else if (expr === 'scared') {
    mouth = <path d={`M ${-r * 0.24} ${my} q ${r * 0.08} ${-r * 0.1} ${r * 0.16} 0 q ${r * 0.08} ${r * 0.1} ${r * 0.16} 0 q ${r * 0.08} ${-r * 0.1} ${r * 0.16} 0`} stroke={INK} strokeWidth={sw} fill="none" strokeLinecap="round" />;
  } else if (expr === 'shocked') {
    mouth = <ellipse cx={0} cy={my} rx={r * 0.12} ry={r * 0.17} fill="#5A0F1E" stroke={INK} strokeWidth={sw * 0.8} />;
  } else if (expr === 'smug') {
    mouth = <path d={`M ${-r * 0.22} ${my} Q ${r * 0.05} ${my + r * 0.12} ${r * 0.26} ${my - r * 0.1}`} stroke={INK} strokeWidth={sw} fill="none" strokeLinecap="round" />;
  } else {
    mouth = <path d={`M ${-r * 0.2} ${my} Q 0 ${my + r * 0.14} ${r * 0.2} ${my}`} stroke={INK} strokeWidth={sw} fill="none" strokeLinecap="round" />;
  }
  const shakeX = expr === 'scared' ? Math.sin(f * 2.3 + seed) * 3 : 0;
  const waveA = Math.sin(t * Math.PI * 2 * 3) * 28;
  const clipId = `gc${seed}_${Math.round(x)}_${Math.round(y)}`;
  return (
    <g transform={`translate(${x + shakeX} ${y}) rotate(${rot}) scale(${sx * scale} ${sy * scale})`} opacity={op}>
      <path d={cd} stroke={INK} strokeWidth={sw * 2.2} fill="none" strokeLinecap="round" />
      <path d={cd} stroke={dark} strokeWidth={sw * 1.0} fill="none" strokeLinecap="round" />
      {(wave || armUp) && (
        <g transform={`translate(${r * 0.85} ${-r * 0.1}) rotate(${armUp ? -30 : -40 + waveA})`}>
          <path d={`M 0 0 Q ${r * 0.35} ${-r * 0.3} ${r * 0.45} ${-r * 0.75}`} stroke={INK} strokeWidth={sw * 3.2} fill="none" strokeLinecap="round" />
          <path d={`M 0 0 Q ${r * 0.35} ${-r * 0.3} ${r * 0.45} ${-r * 0.75}`} stroke={col} strokeWidth={sw * 1.6} fill="none" strokeLinecap="round" />
          <circle cx={r * 0.45} cy={-r * 0.8} r={r * 0.14} fill={col} stroke={INK} strokeWidth={sw * 0.8} />
        </g>
      )}
      <defs><clipPath id={clipId}><path d={body} /></clipPath></defs>
      <path d={body} fill={dark} />
      <g clipPath={`url(#${clipId})`}>
        <circle cx={-r * 0.12} cy={-r * 0.12} r={r * 0.95} fill={col} />
        <ellipse cx={-r * 0.38} cy={-r * 0.5} rx={r * 0.18} ry={r * 0.1} fill="#fff" opacity={0.55} transform={`rotate(-30 ${-r * 0.38} ${-r * 0.5})`} />
        {[0, 1, 2].map((k) => <circle key={k} cx={r * (0.45 - k * 0.32)} cy={r * (0.55 + (k % 2) * 0.12)} r={r * 0.07} fill={dark} />)}
      </g>
      <path d={body} fill="none" stroke={INK} strokeWidth={sw} strokeLinejoin="round" />
      {eyes}
      {shades && (
        <g>
          <path d={`M ${-ex - eyeR * 1.3} ${ey - eyeR * 0.7} L ${ex + eyeR * 1.3} ${ey - eyeR * 0.7}`} stroke={INK} strokeWidth={sw} />
          {[-1, 1].map((s) => (
            <path key={s} d={`M ${s * ex - eyeR * 1.25} ${ey - eyeR * 0.75} h ${eyeR * 2.5} q 0 ${eyeR * 1.7} ${-eyeR * 1.25} ${eyeR * 1.7} q ${-eyeR * 1.25} 0 ${-eyeR * 1.25} ${-eyeR * 1.7} Z`} fill="#16161C" stroke={INK} strokeWidth={sw * 0.8} />
          ))}
          <path d={`M ${-ex - eyeR * 0.7} ${ey - eyeR * 0.35} l ${eyeR * 0.5} ${eyeR * 0.5}`} stroke="#fff" strokeWidth={sw * 0.8} strokeLinecap="round" opacity={0.8} />
        </g>
      )}
      {!shades && brows}
      {mouth}
    </g>
  );
};
