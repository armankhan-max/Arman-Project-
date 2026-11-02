import React from 'react';
import {clamp} from '../lib/ease';
import {INK} from './Hero';

export type Screen = 'feed' | 'lock' | 'off';
export type PhoneProps = {
  x: number; y: number; w?: number; rot?: number; f: number; screen?: Screen;
  scroll?: number; shine?: number; glow?: 'green' | 'red' | 'white' | null; glowAmt?: number; id?: string;
  children?: React.ReactNode; // drawn on top of the screen, in phone-local coords (origin = center)
  skewY?: number; sy?: number;
};
const FEED = ['#FF6B6B', '#4FC3F7', '#FFD54F', '#9B4DFF', '#66BB6A', '#FF8A65', '#BA68C8', '#4DD0E1'];

/** Dark graphite phone (portrait). Origin = center. Height = 2.05 * width. */
export const Phone: React.FC<PhoneProps> = ({x, y, w = 120, rot = 0, f, screen = 'feed', scroll, shine = 0, glow = null, glowAmt = 1, id = 'p', children, skewY = 0, sy = 1}) => {
  const h = w * 2.05, rr = w * 0.16;
  const sw = w * 0.86, sh = h * 0.9, sr = w * 0.11;
  const cid = `ps_${id}`;
  const sc = scroll ?? f * 1.6;
  const card = sh * 0.36;
  const k0 = Math.floor(sc / card);
  const cards = [];
  for (let k = k0 - 1; k < k0 + 4; k++) {
    const yy = -sh / 2 + k * card - sc + sh * 0.08;
    const col = FEED[((k % FEED.length) + FEED.length) % FEED.length];
    cards.push(
      <g key={k}>
        <rect x={-sw * 0.42} y={yy} width={sw * 0.84} height={card * 0.62} rx={sw * 0.05} fill={col} />
        <circle cx={-sw * 0.3} cy={yy + card * 0.73} r={sw * 0.05} fill="#C9D3DE" />
        <rect x={-sw * 0.22} y={yy + card * 0.7} width={sw * 0.5} height={sw * 0.04} rx={sw * 0.02} fill="#C9D3DE" />
        <rect x={-sw * 0.22} y={yy + card * 0.79} width={sw * 0.32} height={sw * 0.035} rx={sw * 0.02} fill="#DCE3EA" />
      </g>,
    );
  }
  const glowCol = glow === 'green' ? 'url(#glowG)' : glow === 'red' ? 'url(#glowR)' : glow === 'white' ? 'url(#glowW)' : undefined;
  const body = <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={rr} />;
  return (
    <g transform={`translate(${x} ${y}) rotate(${rot}) skewY(${skewY}) scale(1 ${sy})`}>
      {glowCol && <g filter={glowCol} opacity={clamp(glowAmt)}>{React.cloneElement(body, {fill: '#000'})}</g>}
      {React.cloneElement(body, {fill: '#2B2F36', stroke: INK, strokeWidth: 4})}
      <rect x={-w / 2 + 3} y={-h / 2 + 3} width={w - 6} height={h - 6} rx={rr - 2} fill="none" stroke="#565C66" strokeWidth={2} />
      <defs><clipPath id={cid}><rect x={-sw / 2} y={-sh / 2} width={sw} height={sh} rx={sr} /></clipPath></defs>
      <g clipPath={`url(#${cid})`}>
        {screen === 'feed' && (
          <g>
            <rect x={-sw / 2} y={-sh / 2} width={sw} height={sh} fill="#F4F7FB" />
            {cards}
            <rect x={-sw / 2} y={-sh / 2} width={sw} height={sh * 0.07} fill="#FFFFFF" />
            <rect x={-sw * 0.3} y={-sh / 2 + sh * 0.025} width={sw * 0.6} height={sh * 0.022} rx={sh * 0.01} fill="#E2E8EF" />
          </g>
        )}
        {screen === 'lock' && (
          <g>
            <defs>
              <linearGradient id={`lg_${id}`} x1="0" y1="0" x2="0.6" y2="1">
                <stop offset="0" stopColor="#6A5CFF" /><stop offset="0.55" stopColor="#4FA3E0" /><stop offset="1" stopColor="#7FE3C4" />
              </linearGradient>
            </defs>
            <rect x={-sw / 2} y={-sh / 2} width={sw} height={sh} fill={`url(#lg_${id})`} />
            <text x={0} y={-sh * 0.24} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={sw * 0.32} fill="#fff">9:41</text>
            <text x={0} y={-sh * 0.15} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={sw * 0.07} fill="#fff" opacity={0.85}>Monday</text>
            <rect x={-sw * 0.4} y={sh * 0.02} width={sw * 0.8} height={sw * 0.34} rx={sw * 0.08} fill="#111" opacity={0.25} />
            <text x={0} y={sh * 0.02 + sw * 0.22} textAnchor="middle" fontFamily="Baloo2, sans-serif" fontWeight={800} fontSize={sw * 0.115} fill="#fff" letterSpacing={1}>NOT THE HERO</text>
            <rect x={-sw * 0.2} y={sh * 0.44} width={sw * 0.4} height={sw * 0.03} rx={sw * 0.015} fill="#fff" opacity={0.8} />
          </g>
        )}
        {screen === 'off' && <rect x={-sw / 2} y={-sh / 2} width={sw} height={sh} fill="#1B1E24" />}
        {children}
        {/* glass reflection + shine sweep */}
        <path d={`M ${-sw / 2} ${-sh / 2} L ${sw * 0.1} ${-sh / 2} L ${-sw / 2} ${-sh * 0.1} Z`} fill="#fff" opacity={0.08} />
        {shine > 0 && shine < 1 && (
          <rect x={-sw} y={-sh / 2 - sh * 0.4 + shine * sh * 1.6} width={sw * 2} height={sh * 0.16} fill="#fff" opacity={0.55} transform={`rotate(-25 0 ${-sh / 2 - sh * 0.4 + shine * sh * 1.6})`} />
        )}
      </g>
      <rect x={-w * 0.12} y={-sh / 2 + sh * 0.012} width={w * 0.24} height={w * 0.06} rx={w * 0.03} fill="#0E0F12" />
    </g>
  );
};
