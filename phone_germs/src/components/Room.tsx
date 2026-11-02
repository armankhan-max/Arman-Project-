import React from 'react';
import {INK} from './Hero';

/** BG layer: light-blue radial wall, lighter behind the subject, soft blue tiles. */
export const Wall: React.FC<{cx?: number; cy?: number; tiles?: boolean; door?: number | null; mirror?: [number, number] | null; tint?: string}> = ({cx = 540, cy = 900, tiles = true, door = null, mirror = null, tint}) => {
  const id = `wg${Math.round(cx)}_${Math.round(cy)}`;
  const lines = [];
  if (tiles) {
    for (let x = -2400; x <= 3600; x += 120) lines.push(<line key={'v' + x} x1={x} y1={-2000} x2={x} y2={1500} stroke="#B7D2EA" strokeWidth={3} />);
    for (let y = -2000; y <= 1500; y += 120) lines.push(<line key={'h' + y} x1={-2400} y1={y} x2={3600} y2={y} stroke="#B7D2EA" strokeWidth={3} />);
  }
  return (
    <g>
      <defs>
        <radialGradient id={id} gradientUnits="userSpaceOnUse" cx={cx} cy={cy} r={1300}>
          <stop offset="0" stopColor="#EEF6FC" /><stop offset="1" stopColor="#CDE3F4" />
        </radialGradient>
      </defs>
      <rect x={-2400} y={-2000} width={6000} height={5000} fill={`url(#${id})`} />
      {tiles && <g opacity={0.8}>{lines}</g>}
      {tint && <rect x={-2400} y={-2000} width={6000} height={5000} fill={tint} />}
      {door !== null && (
        <g transform={`translate(${door} 1500)`}>
          <rect x={-170} y={-760} width={340} height={760} rx={8} fill="#E9D7C2" stroke={INK} strokeWidth={4} />
          <rect x={-130} y={-710} width={260} height={300} rx={6} fill="none" stroke="#CDB79E" strokeWidth={6} />
          <rect x={-130} y={-370} width={260} height={320} rx={6} fill="none" stroke="#CDB79E" strokeWidth={6} />
        </g>
      )}
      {mirror && (
        <g transform={`translate(${mirror[0]} ${mirror[1]})`}>
          <rect x={-190} y={-240} width={380} height={480} rx={190} fill="#DDEFFB" stroke={INK} strokeWidth={4} />
          <path d="M -90 -150 L -20 -200 M -110 -80 L 30 -190" stroke="#fff" strokeWidth={14} strokeLinecap="round" opacity={0.8} />
        </g>
      )}
    </g>
  );
};

/** SUBJECT-layer floor band */
export const Floor: React.FC<{y: number}> = ({y}) => (
  <g>
    <rect x={-3000} y={y} width={7000} height={3000} fill="#E4EEF7" />
    <rect x={-3000} y={y} width={7000} height={10} fill="#C9D9E8" />
    {Array.from({length: 40}).map((_, i) => (
      <line key={i} x1={-3000 + i * 180} y1={y + 10} x2={-3000 + i * 180 - 140} y2={y + 600} stroke="#D3E1EE" strokeWidth={4} />
    ))}
  </g>
);
