import React from 'react';
import {INK} from './Hero';

const POR = '#F7F7F5', POR_D = '#CBCBC9', WATER = '#7EC8E3';
export type ToiletProps = {x: number; y: number; s?: number; lid?: number; rattle?: number; glow?: 'red' | 'green' | null; glowAmt?: number; seatGlow?: number; flush?: number; children?: React.ReactNode};

/** Front-view toilet. Origin = floor center. lid: 0 closed, 1 open. Seat top at y = -360*s. */
export const Toilet: React.FC<ToiletProps> = ({x, y, s = 1, lid = 0, rattle = 0, glow = null, glowAmt = 1, seatGlow = 0, flush = 0, children}) => {
  const bowl = 'M -168 -352 C -170 -250 -120 -190 -88 -150 L -100 -12 Q -100 0 -88 0 L 88 0 Q 100 0 100 -12 L 88 -150 C 120 -190 170 -250 168 -352 Z';
  const tank = <rect x={-150} y={-640} width={300} height={250} rx={26} />;
  const shape = (
    <g>
      {tank}
      <path d={bowl} />
      <ellipse cx={0} cy={-360} rx={176} ry={66} />
    </g>
  );
  const lidAng = lid; // 0..1
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      <ellipse cx={0} cy={4} rx={190} ry={24} fill="url(#shadowGrad)" />
      {glow && <g filter={glow === 'red' ? 'url(#glowR)' : 'url(#glowG)'} opacity={glowAmt}>{shape}</g>}
      {/* tank */}
      <rect x={-150} y={-640} width={300} height={250} rx={26} fill={POR} stroke={INK} strokeWidth={4} />
      <rect x={60} y={-640} width={90} height={250} rx={26} fill={POR_D} opacity={0.7} />
      <rect x={-150} y={-640} width={300} height={250} rx={26} fill="none" stroke={INK} strokeWidth={4} />
      <rect x={-166} y={-664} width={332} height={40} rx={16} fill={POR} stroke={INK} strokeWidth={4} />
      {/* flush lever */}
      <g transform={`rotate(${flush * 28} -120 -600)`}>
        <rect x={-150} y={-606} width={50} height={14} rx={7} fill="#B8C4CF" stroke={INK} strokeWidth={4} />
      </g>
      <circle cx={-120} cy={-600} r={9} fill="#B8C4CF" stroke={INK} strokeWidth={4} />
      {/* bowl */}
      <path d={bowl} fill={POR} stroke={INK} strokeWidth={4} strokeLinejoin="round" />
      <path d="M 60 -350 C 110 -260 90 -200 70 -150 L 82 -10 L 88 -10 L 88 -150 C 120 -190 168 -250 168 -352 Z" fill={POR_D} opacity={0.75} />
      <path d={bowl} fill="none" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
      {/* seat ring + water */}
      <ellipse cx={0} cy={-360} rx={176} ry={66} fill={POR} stroke={INK} strokeWidth={4} />
      <ellipse cx={0} cy={-356} rx={118} ry={38} fill={WATER} stroke={INK} strokeWidth={4} />
      <ellipse cx={-30} cy={-364} rx={40} ry={10} fill="#fff" opacity={0.5} />
      {seatGlow > 0 && <ellipse cx={0} cy={-360} rx={150} ry={54} fill="none" stroke="#E23B2E" strokeWidth={22} opacity={0.55 * seatGlow} filter="url(#soft12)" />}
      {children}
      {/* lid */}
      {lidAng < 0.5 ? (
        <g transform={`translate(0 ${-rattle * 10}) rotate(${rattle * 3} 0 -380)`}>
          <ellipse cx={0} cy={-378 - lidAng * 60} rx={180} ry={66 * (1 - lidAng * 1.6)} fill={POR} stroke={INK} strokeWidth={4} />
          <ellipse cx={-20} cy={-388 - lidAng * 60} rx={110} ry={30 * (1 - lidAng * 1.6)} fill="#fff" opacity={0.6} />
          <path d={`M -176 -372 Q 0 ${-300 - lidAng * 80} 176 -372`} fill="none" stroke={POR_D} strokeWidth={8} opacity={0.8} />
        </g>
      ) : (
        <g transform={`translate(0 ${-rattle * 6})`}>
          <path d={`M -150 -420 C -160 ${-420 - 260 * lidAng} 160 ${-420 - 260 * lidAng} 150 -420 Z`} fill={POR} stroke={INK} strokeWidth={4} />
          <path d={`M 70 -430 C 120 ${-420 - 200 * lidAng} 150 -500 150 -420 Z`} fill={POR_D} opacity={0.6} />
        </g>
      )}
    </g>
  );
};
