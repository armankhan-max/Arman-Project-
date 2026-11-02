import React from 'react';
import {INK} from './Hero';
import {shade} from '../lib/ease';

type P = {x: number; y: number; s?: number; rot?: number; glow?: boolean; glowAmt?: number};
const G: React.FC<P & {children: React.ReactNode}> = ({x, y, s = 1, rot = 0, glow, glowAmt = 1, children}) => (
  <g transform={`translate(${x} ${y}) rotate(${rot}) scale(${s})`}>
    {glow && <g filter="url(#glowG)" opacity={glowAmt}>{children}</g>}
    {children}
  </g>
);

export const SprayBottle: React.FC<P & {squeeze?: number}> = ({squeeze = 0, ...p}) => (
  <G {...p}>
    {/* origin = nozzle tip */}
    <g transform="translate(70 30)">
      <path d="M -40 40 L 40 40 L 52 300 Q 52 320 32 320 L -32 320 Q -52 320 -52 300 Z" fill="#7FD3F7" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
      <path d="M 18 44 L 40 40 L 52 300 Q 52 320 32 320 L 22 320 Z" fill={shade('#7FD3F7')} />
      <rect x={-44} y={130} width={92} height={110} rx={10} fill="#fff" stroke={INK} strokeWidth={4} />
      <text x={2} y={172} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={17} fill="#E23B2E">NOT THE</text>
      <text x={2} y={194} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={17} fill="#E23B2E">HERO</text>
      <text x={2} y={222} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={12} fill="#4FA3E0">DISINFECT</text>
      <rect x={-30} y={0} width={60} height={44} rx={8} fill="#F7F7F5" stroke={INK} strokeWidth={4} />
      <path d="M -30 8 L -70 -30 L -70 -14 L -30 14 Z" fill="#F7F7F5" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
      <g transform={`rotate(${-squeeze * 18} 10 40)`}>
        <path d="M 6 40 Q -6 80 10 110" stroke={INK} strokeWidth={14} fill="none" strokeLinecap="round" />
        <path d="M 6 40 Q -6 80 10 110" stroke="#E23B2E" strokeWidth={6} fill="none" strokeLinecap="round" />
      </g>
    </g>
  </G>
);

export const DoorHandle: React.FC<P & {press?: number}> = ({press = 0, ...p}) => (
  <G {...p}>
    <rect x={-60} y={-110} width={120} height={220} rx={18} fill="#C7CED6" stroke={INK} strokeWidth={4} />
    <rect x={-60} y={-110} width={120} height={60} rx={18} fill="#DCE2E8" opacity={0.8} />
    <circle cx={0} cy={0} r={26} fill="#AEB7C1" stroke={INK} strokeWidth={4} />
    <g transform={`rotate(${press * 20} 0 0)`}>
      <rect x={-12} y={-16} width={190} height={32} rx={16} fill="#D9DEE4" stroke={INK} strokeWidth={4} />
      <rect x={-6} y={-12} width={170} height={8} rx={4} fill="#fff" opacity={0.7} />
    </g>
    <rect x={-14} y={50} width={28} height={36} rx={8} fill="#2F3540" />
  </G>
);

export const DollarBill: React.FC<P> = (p) => (
  <G {...p}>
    <rect x={-150} y={-66} width={300} height={132} rx={8} fill="#8FD18B" stroke={INK} strokeWidth={4} />
    <rect x={-134} y={-52} width={268} height={104} rx={6} fill="none" stroke="#3E8A4A" strokeWidth={4} />
    <ellipse cx={0} cy={0} rx={38} ry={42} fill="#B7E3B2" stroke="#3E8A4A" strokeWidth={4} />
    <text x={0} y={14} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={40} fill="#3E8A4A">$</text>
    <text x={-110} y={-18} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={30} fill="#3E8A4A">1</text>
    <text x={110} y={42} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={30} fill="#3E8A4A">1</text>
  </G>
);

export const SnackBag: React.FC<P> = (p) => (
  <G {...p}>
    <path d="M -95 -150 L 95 -150 L 88 -128 Q 104 0 88 128 L 95 150 L -95 150 L -88 128 Q -104 0 -88 -128 Z" fill="#FF8A1F" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
    <path d="M 40 -150 L 95 -150 L 88 -128 Q 104 0 88 128 L 95 150 L 50 150 Q 66 0 40 -150 Z" fill={shade('#FF8A1F')} />
    <path d="M -95 -150 L 95 -150 L 88 -128 Q 104 0 88 128 L 95 150 L -95 150 L -88 128 Q -104 0 -88 -128 Z" fill="none" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
    <path d="M -90 -134 L 90 -134 M -90 134 L 90 134" stroke={INK} strokeWidth={3} strokeDasharray="10 8" />
    <ellipse cx={0} cy={-20} rx={66} ry={44} fill="#FFD84A" stroke={INK} strokeWidth={4} />
    <text x={0} y={-8} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={36} fill="#E23B2E">CHIPS</text>
    {[[-40, 70], [10, 84], [50, 64]].map(([cx, cy], i) => <ellipse key={i} cx={cx} cy={cy} rx={26} ry={16} fill="#FFE08A" stroke={INK} strokeWidth={3} transform={`rotate(${i * 30 - 20} ${cx} ${cy})`} />)}
  </G>
);

export const Plant: React.FC<P> = (p) => (
  <G {...p}>
    {[-60, -25, 10, 45, -80, 70].map((a, i) => (
      <path key={i} d={`M 0 -120 Q ${a * 1.2} ${-260 - (i % 3) * 40} ${a * 2.4} ${-330 - (i % 2) * 60} Q ${a * 0.6} ${-230} 0 -120 Z`} fill={i % 2 ? '#3FA45B' : '#57C26F'} stroke={INK} strokeWidth={4} strokeLinejoin="round" />
    ))}
    <path d="M -90 -130 L 90 -130 L 70 0 L -70 0 Z" fill="#E07A4B" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
    <rect x={-100} y={-150} width={200} height={34} rx={10} fill="#F08C5C" stroke={INK} strokeWidth={4} />
  </G>
);

export const Lamp: React.FC<P & {on?: boolean}> = ({on = true, ...p}) => (
  <G {...p}>
    <rect x={-70} y={-12} width={140} height={20} rx={10} fill="#2F3540" stroke={INK} strokeWidth={4} />
    <rect x={-8} y={-560} width={16} height={556} fill="#3A404A" stroke={INK} strokeWidth={4} />
    {on && <ellipse cx={0} cy={-520} rx={180} ry={120} fill="url(#warm)" opacity={0.6} />}
    <path d="M -100 -520 L 100 -520 L 60 -660 L -60 -660 Z" fill="#FFE3A3" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
  </G>
);

export const ToiletPaper: React.FC<P> = (p) => (
  <G {...p}>
    <rect x={-110} y={-80} width={220} height={160} rx={30} fill="#F7F7F5" stroke={INK} strokeWidth={4} />
    <ellipse cx={110} cy={0} rx={30} ry={80} fill="#E6E6E2" stroke={INK} strokeWidth={4} />
    <ellipse cx={110} cy={0} rx={12} ry={30} fill="#B9A58C" stroke={INK} strokeWidth={4} />
    <path d="M -110 60 Q -120 160 -100 240 L -40 240 Q -50 160 -40 78" fill="#F7F7F5" stroke={INK} strokeWidth={4} />
  </G>
);

export const Wipes: React.FC<P> = (p) => (
  <G {...p}>
    <rect x={-130} y={-80} width={260} height={160} rx={36} fill="#7FE3C4" stroke={INK} strokeWidth={4} />
    <rect x={40} y={-80} width={90} height={160} rx={36} fill={shade('#7FE3C4')} />
    <rect x={-130} y={-80} width={260} height={160} rx={36} fill="none" stroke={INK} strokeWidth={4} />
    <rect x={-70} y={-62} width={140} height={34} rx={17} fill="#fff" stroke={INK} strokeWidth={4} />
    <text x={0} y={22} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={26} fill="#fff" stroke={INK} strokeWidth={5} paintOrder="stroke">NOT THE HERO</text>
    <text x={0} y={54} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={18} fill="#1E6B55">WIPES</text>
  </G>
);

export const Sink: React.FC<P> = (p) => (
  <G {...p}>
    {/* origin = counter top center */}
    <rect x={-420} y={0} width={840} height={60} rx={10} fill="#F2F5F8" stroke={INK} strokeWidth={4} />
    <rect x={-400} y={60} width={800} height={420} fill="#9CB7CF" stroke={INK} strokeWidth={4} />
    <rect x={-380} y={90} width={370} height={360} rx={10} fill="#ADC6DB" stroke={INK} strokeWidth={4} />
    <rect x={10} y={90} width={370} height={360} rx={10} fill="#ADC6DB" stroke={INK} strokeWidth={4} />
    <circle cx={-40} cy={270} r={10} fill="#E4EEF7" stroke={INK} strokeWidth={4} />
    <circle cx={40} cy={270} r={10} fill="#E4EEF7" stroke={INK} strokeWidth={4} />
    <path d="M 120 6 Q 230 40 340 6" fill="#DCE6EF" stroke={INK} strokeWidth={4} />
    <path d="M 220 0 L 220 -110 Q 220 -140 190 -140 L 160 -140" fill="none" stroke={INK} strokeWidth={20} strokeLinecap="round" />
    <path d="M 220 0 L 220 -110 Q 220 -140 190 -140 L 160 -140" fill="none" stroke="#C7CED6" strokeWidth={10} strokeLinecap="round" />
  </G>
);

export const Umbrella: React.FC<P> = (p) => (
  <G {...p}>
    <path d="M 0 0 L 0 -150" stroke={INK} strokeWidth={6} />
    <path d="M -90 -140 Q 0 -230 90 -140 Q 60 -155 45 -140 Q 22 -158 0 -140 Q -22 -158 -45 -140 Q -60 -155 -90 -140 Z" fill="#E23B2E" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
    <path d="M -45 -140 Q -30 -200 0 -205 Q -14 -170 0 -140 M 45 -140 Q 30 -200 0 -205" fill="#fff" stroke={INK} strokeWidth={3} />
  </G>
);

export const Towel: React.FC<P & {col?: string}> = ({col = '#FF4FA3', ...p}) => (
  <G {...p}>
    <rect x={-70} y={-16} width={140} height={32} rx={6} fill={col} stroke={INK} strokeWidth={3} />
    <path d="M -50 -16 L -50 16 M 0 -16 L 0 16 M 50 -16 L 50 16" stroke="#fff" strokeWidth={6} />
  </G>
);
