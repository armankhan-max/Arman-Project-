import React from 'react';
import {Stage, Cam} from '../lib/stage';
import {SceneProps, drift} from './common';
import {L} from '../timeline';
import {prog, lerp, easeInOutSine, snapEase, easeInOutCubic, popIn, rnd} from '../lib/ease';
import {INK, HOOD, HOOD_D, SKIN} from '../components/Hero';
import {Phone} from '../components/Phone';
import {Germ, GERM_COLS} from '../components/Germ';
import {WarmGlow} from '../components/Fx';
import {Umbrella, Towel} from '../components/Props';
import {S4_PHONE_W} from './S4';

const PW = S4_PHONE_W * 1.4; // same on-screen size as the end of S4 (match cut)
const PX = 540, PY = 960;

export const S5: React.FC<SceneProps> = ({f, dur, tin, tout}) => {
  const tWarm = L('S5', 'warm'), tStays = L('S5', 'stays warm'), tPocket = L('S5', 'pocket'), tHelp = L('S5', 'help'), tGerms = L('S5', 'germs'), tSurv = L('S5', 'survive'), tLonger = L('S5', 'longer');
  const cam = (f: number): Cam => {
    const pb = prog(f, 0, 40, easeInOutCubic);
    let z = lerp(3.1, 1.25, pb);
    z *= 1 + 0.16 * prog(f, 40, tGerms, easeInOutSine);
    const sn = prog(f, tGerms, tGerms + 10, snapEase);
    z *= 1 + 0.35 * sn;
    z *= 1 + 0.08 * prog(f, tGerms + 10, dur, easeInOutSine);
    const [dx, dy] = drift(f);
    return {x: PX + dx * pb, y: lerp(PY, PY + 40, pb) - 40 * sn + dy * pb, z, r: lerp(0, -3, prog(f, tSurv, dur, easeInOutSine))};
  };
  const warm = prog(f, tStays, tStays + 30);
  // beach germs on the screen (phone-local coords, phone w=PW)
  const extra: {t: number; x: number; y: number; r: number}[] = [
    {t: tHelp, x: -40, y: 100, r: 18}, {t: tGerms, x: 44, y: -40, r: 16}, {t: tGerms + 8, x: -48, y: -120, r: 15},
    {t: tSurv, x: 40, y: 140, r: 17}, {t: tSurv + 9, x: -10, y: -170, r: 14}, {t: tLonger, x: 50, y: 60, r: 15}, {t: tLonger + 7, x: -52, y: 30, r: 13},
    {t: tLonger + 14, x: 10, y: 190, r: 14},
  ];
  const outside: {t: number; x: number; y: number; r: number}[] = [
    {t: tSurv + 4, x: PX - 160, y: PY + 190, r: 20}, {t: tLonger + 3, x: PX + 165, y: PY - 150, r: 18}, {t: tLonger + 10, x: PX + 150, y: PY + 170, r: 19},
  ];
  const heat = Array.from({length: 6}).map((_, i) => {
    const ph = ((f * 0.8 + i * 23) % 90) / 90;
    const x = PX - 160 + i * 64;
    return <path key={i} d={`M ${x} ${PY + 180 - ph * 420} q 14 -20 0 -40 q -14 -20 0 -40`} stroke="#FFB347" strokeWidth={7} fill="none" strokeLinecap="round" opacity={warm * Math.sin(ph * Math.PI) * 0.9} />;
  });
  const pocket = `M ${PX - 210} ${PY - 250} L ${PX + 210} ${PY - 250} L ${PX + 230} ${PY + 250} Q ${PX} ${PY + 290} ${PX - 230} ${PY + 250} Z`;
  const thermo = popIn(f, tWarm, 10);
  return (
    <Stage f={f} dur={dur} tin={tin} tout={tout} cam={cam}
      bg={<rect x={-2000} y={-2000} width={5000} height={5000} fill={HOOD_D} />}
      mid={
        <g>
          {/* hoodie front, big */}
          <rect x={-800} y={-300} width={2700} height={2000} fill={HOOD} />
          {Array.from({length: 30}).map((_, i) => <path key={i} d={`M ${-800 + i * 100} -300 l 60 2000`} stroke={HOOD_D} strokeWidth={3} opacity={0.25} />)}
          <path d={`M ${PX - 260} 0 Q ${PX} 220 ${PX + 260} 0`} fill={HOOD_D} stroke={INK} strokeWidth={6} />
          <path d={`M ${PX - 60} 120 q -10 160 -20 260`} stroke="#fff" strokeWidth={14} fill="none" strokeLinecap="round" />
          <path d={`M ${PX + 60} 120 q 10 160 20 260`} stroke="#fff" strokeWidth={14} fill="none" strokeLinecap="round" />
          <text x={PX} y={540} textAnchor="middle" fontFamily="Baloo2" fontWeight={800} fontSize={64} fill="#fff" letterSpacing={2}>NOT THE HERO</text>
          <rect x={-800} y={1560} width={2700} height={120} fill={HOOD_D} stroke={INK} strokeWidth={6} />
        </g>
      }
      subj={
        <g>
          {/* kangaroo pocket: outer stitched panel + cut-open cross-section */}
          <path d={`M ${PX - 330} ${PY - 330} L ${PX + 330} ${PY - 330} L ${PX + 380} ${PY + 380} L ${PX - 380} ${PY + 380} Z`} fill={HOOD_D} stroke={INK} strokeWidth={6} strokeLinejoin="round" />
          <path d={`M ${PX - 310} ${PY - 310} L ${PX + 310} ${PY - 310} L ${PX + 356} ${PY + 360} L ${PX - 356} ${PY + 360} Z`} fill="none" stroke="#fff" strokeWidth={4} strokeDasharray="16 12" opacity={0.6} />
          <path d={pocket} fill="#1F3F5B" stroke="#7FB8E6" strokeWidth={18} strokeLinejoin="round" />
          <path d={pocket} fill="none" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
          <WarmGlow x={PX} y={PY} r={420} amt={warm} f={f} />
          {heat}
          <Phone x={PX} y={PY} w={PW} f={f} id="s5" glow="green" glowAmt={prog(f, tGerms, tGerms + 10) * (0.6 + 0.3 * Math.sin(f * 0.3))}>
            <rect x={-PW} y={-PW * 2} width={PW * 2} height={PW * 4} fill="#FFB347" opacity={0.25 * warm} />
            <Towel x={-10} y={30} s={0.9} col="#FF4FA3" rot={-8} />
            <Germ x={-10} y={10} r={24} f={f} seed={31} col="#39E35B" expr="happy" shades rot={-80} sx={1.1} sy={0.85} />
            <Umbrella x={36} y={-50} s={0.45} rot={8} />
            <Germ x={30} y={-60} r={20} f={f} seed={32} col="#9B4DFF" expr="smug" shades />
            {extra.map((e, i) => (f >= e.t ? <Germ key={i} x={e.x} y={e.y} r={e.r} f={f} seed={40 + i} col={GERM_COLS[i % 4]} expr={i % 2 ? 'happy' : 'laugh'} scale={popIn(f, e.t, 9)} /> : null))}
          </Phone>
          {outside.map((e, i) => (f >= e.t ? <Germ key={i} x={e.x} y={e.y} r={e.r} f={f} seed={60 + i} col={GERM_COLS[(i + 2) % 4]} expr="happy" scale={popIn(f, e.t, 9)} /> : null))}
          {/* thermometer */}
          {thermo > 0 && (
            <g transform={`translate(${PX + 300} ${PY - 260}) scale(${thermo}) rotate(${Math.sin(f * 0.15) * 8})`}>
              <rect x={-22} y={-130} width={44} height={170} rx={22} fill="#fff" stroke={INK} strokeWidth={6} />
              <rect x={-9} y={lerp(20, -110, prog(f, tWarm, tWarm + 40))} width={18} height={lerp(20, 150, prog(f, tWarm, tWarm + 40))} rx={9} fill="#E23B2E" />
              <circle cx={0} cy={56} r={34} fill="#E23B2E" stroke={INK} strokeWidth={6} />
            </g>
          )}
        </g>
      }
    />
  );
};
