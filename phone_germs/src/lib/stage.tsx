import React from 'react';
import {clamp, easeInExpo, easeOutExpo} from './ease';

export type Cam = {x: number; y: number; z: number; r: number; orb?: number; shx?: number; shy?: number};
export const CX = 540, CY = 960, SW = 1080, SH = 1920;
export const PAR = {bg: 0.3, mid: 0.6, subj: 1.0, fg: 1.6} as const;

export type Trans = 'whip' | 'cut' | 'match' | 'action';
const WHIP = 8;

/** apply whip-pan offsets at scene edges */
export function withTransitions(cam: Cam, f: number, dur: number, tin: Trans, tout: Trans): Cam {
  let x = cam.x;
  if (tin === 'whip' && f < WHIP) x += (-1.5 * SW * (1 - easeOutExpo((f + 1) / (WHIP + 1)))) / cam.z;
  if (tout === 'whip' && f >= dur - WHIP) x += (1.5 * SW * easeInExpo((f - (dur - WHIP) + 1) / WHIP)) / cam.z;
  return {...cam, x};
}

export function layerTransform(c: Cam, p: number) {
  const z = Math.max(0.15, 1 + (c.z - 1) * p);
  const ox = (c.orb ?? 0) * (p - 1) * -22; // ORBIT_FAKE: bg slides opposite the rotation
  const tx = CX + (c.x - CX) * p;
  const ty = CY + (c.y - CY) * p;
  return `translate(${CX + ox + (c.shx ?? 0) * p} ${CY + (c.shy ?? 0) * p}) rotate(${c.r * Math.min(p, 1.2)}) scale(${z}) translate(${-tx} ${-ty})`;
}

export const Defs: React.FC = () => (
  <defs>
    <filter id="blurBG" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="3" /></filter>
    <filter id="blurFG" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6" /></filter>
    <filter id="soft12" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="12" /></filter>
    <filter id="glowG" x="-50%" y="-50%" width="200%" height="200%">
      <feMorphology in="SourceAlpha" operator="dilate" radius="6" result="d" />
      <feGaussianBlur in="d" stdDeviation="12" result="b" />
      <feFlood floodColor="#39E35B" />
      <feComposite in2="b" operator="in" result="g" />
      <feMerge><feMergeNode in="g" /><feMergeNode in="g" /></feMerge>
    </filter>
    <filter id="glowR" x="-50%" y="-50%" width="200%" height="200%">
      <feMorphology in="SourceAlpha" operator="dilate" radius="6" result="d" />
      <feGaussianBlur in="d" stdDeviation="14" result="b" />
      <feFlood floodColor="#E23B2E" />
      <feComposite in2="b" operator="in" result="g" />
      <feMerge><feMergeNode in="g" /><feMergeNode in="g" /></feMerge>
    </filter>
    <filter id="glowW" x="-50%" y="-50%" width="200%" height="200%">
      <feMorphology in="SourceAlpha" operator="dilate" radius="4" result="d" />
      <feGaussianBlur in="d" stdDeviation="10" result="b" />
      <feFlood floodColor="#FFFFFF" />
      <feComposite in2="b" operator="in" />
    </filter>
    <radialGradient id="warm" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stopColor="#FFB347" stopOpacity="0.95" />
      <stop offset="0.55" stopColor="#FFB347" stopOpacity="0.45" />
      <stop offset="1" stopColor="#FFB347" stopOpacity="0" />
    </radialGradient>
    <radialGradient id="dangerGrad" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stopColor="#E23B2E" stopOpacity="0.55" />
      <stop offset="1" stopColor="#E23B2E" stopOpacity="0" />
    </radialGradient>
    <radialGradient id="vignette" cx="0.5" cy="0.5" r="0.75">
      <stop offset="0.55" stopColor="#0B1A33" stopOpacity="0" />
      <stop offset="1" stopColor="#0B1A33" stopOpacity="0.38" />
    </radialGradient>
    <radialGradient id="shadowGrad" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stopColor="#000" stopOpacity="0.22" />
      <stop offset="0.6" stopColor="#000" stopOpacity="0.16" />
      <stop offset="1" stopColor="#000" stopOpacity="0" />
    </radialGradient>
  </defs>
);

type StageProps = {
  f: number; dur: number; cam: (f: number) => Cam; tin: Trans; tout: Trans;
  bg?: React.ReactNode; mid?: React.ReactNode; subj?: React.ReactNode; fg?: React.ReactNode; screen?: React.ReactNode;
  bgBlur?: boolean;
};

/** One shot = 4 parallax layers driven by a virtual camera, plus a screen-space overlay. */
export const Stage: React.FC<StageProps> = ({f, dur, cam, tin, tout, bg, mid, subj, fg, screen, bgBlur = true}) => {
  const c = withTransitions(cam(f), f, dur, tin, tout);
  const p = withTransitions(cam(f - 1), f - 1, dur, tin, tout);
  // automatic motion blur from camera velocity (screen px / frame)
  const vx = Math.abs((c.x - p.x) * c.z), vy = Math.abs((c.y - p.y) * c.z);
  const vz = Math.abs(c.z - p.z) * 900;
  let bx = clamp(vx * 0.22, 0, 40), by = clamp(vy * 0.22 + vz * 0.05, 0, 14);
  if ((tin === 'whip' && f < 8) || (tout === 'whip' && f >= dur - 8)) bx = Math.max(bx, 40 * clamp(vx / 120));
  const id = `mb`;
  const useBlur = bx > 1.2 || by > 1.2;
  return (
    <g>
      {useBlur && (
        <defs>
          <filter id={id} x="-5%" y="-5%" width="110%" height="110%">
            <feGaussianBlur stdDeviation={`${bx.toFixed(1)} ${by.toFixed(1)}`} edgeMode="duplicate" />
          </filter>
        </defs>
      )}
      <g filter={useBlur ? `url(#${id})` : undefined}>
        <g transform={layerTransform(c, PAR.bg)} filter={bgBlur ? 'url(#blurBG)' : undefined}>{bg}</g>
        <g transform={layerTransform(c, PAR.mid)}>{mid}</g>
        <g transform={layerTransform(c, PAR.subj)}>{subj}</g>
        <g transform={layerTransform(c, PAR.fg)} filter="url(#blurFG)">{fg}</g>
      </g>
      {screen}
    </g>
  );
};
