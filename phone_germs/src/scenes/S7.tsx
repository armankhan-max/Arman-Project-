import React from 'react';
import {Stage, Cam} from '../lib/stage';
import {SceneProps, drift} from './common';
import {L} from '../timeline';
import {prog, lerp, easeInOutSine, easeInCubic, kf, clamp, shake, easeOutCubic, popIn} from '../lib/ease';
import {Hero, Expr, INK} from '../components/Hero';
import {Germ, GERM_COLS} from '../components/Germ';
import {Wall} from '../components/Room';

/** POV from inside the phone screen: Hero's giant face approaches until it smacks the glass. */
export const S7: React.FC<SceneProps> = ({f, dur, tin, tout}) => {
  const tPress = L('S7', 'press'), tScreen = L('S7', 'same screen'), tRight = L('S7', 'right against'), tFace = L('S7', 'face', 33.4);
  // face approach: hero scale grows (exponential feel), impact at "face"
  const appr = (f: number) => kf(f, [[0, 0], [tRight, 0.45, easeInOutSine], [tFace, 1, easeInCubic]]);
  const a = appr(f);
  const s = lerp(1.6, 9.6, a);
  const impact = f >= tFace;
  const squashT = f - tFace;
  const flat = impact ? kf(squashT, [[0, 1], [3, 1], [12, 0, easeOutCubic]]) : 0;
  const cam = (f: number): Cam => {
    const z = lerp(1, 1.12, prog(f, 0, tRight, easeInOutSine)) * (1 + 0.08 * prog(f, tRight, tFace, easeInCubic));
    const [dx, dy] = drift(f, 6);
    const [sx, sy] = shake(f, tFace, 14, 6, 3);
    return {x: 540 + dx, y: 960 + dy, z, r: Math.sin(f / 30) * 1.5, shx: sx, shy: sy};
  };
  // Hero head centered: head center local y = -500  => world y = Y - 500*s
  const headY = lerp(860, 900, a);
  const Y = headY + 500 * s;
  const expr: Expr = impact ? (squashT >= 6 ? 'disgusted' : 'shocked') : f >= tScreen ? 'focused' : 'neutral';
  const germs = [
    [250, 1330, 44], [520, 1480, 50], [800, 1300, 42], [380, 640, 34], [740, 720, 36], [930, 1050, 30], [150, 980, 32],
  ];
  return (
    <Stage f={f} dur={dur} tin={tin} tout={tout} cam={cam}
      bg={<g><Wall cx={540} cy={800} /><rect x={-2000} y={-2000} width={5000} height={5000} fill="#0B1A33" opacity={0.12} /></g>}
      subj={
        <g>
          <g transform={`translate(540 ${headY}) scale(${1 + 0.12 * flat} ${1 - 0.1 * flat}) translate(-540 ${-headY})`}>
            <Hero x={540} y={Y} s={s} f={f} seed={8} expr={expr} exprAt={impact ? (squashT >= 6 ? tFace + 6 : tFace) : f >= tScreen ? tScreen : undefined}
              look={[0, 0.3]} tint={impact ? clamp((squashT - 6) / 6) : 0} armR={[150, 0]} armL={[-150, 0]} shadow={false} />
          </g>
          {impact && <rect x={-500} y={-500} width={2100} height={2900} fill="#9BE59B" opacity={0.12 * clamp((squashT - 6) / 6)} />}
        </g>
      }
      fg={null}
      screen={
        <g>
          {/* germs ON the glass (screen space) */}
          {germs.map(([x, y, r], i) => {
            const sc = popIn(f, 4 + i * 3, 10);
            const sq = impact ? kf(squashT, [[0, 1], [2, 0.25], [10, 0.25], [16, 1.1], [20, 1]]) : 1;
            const ex = impact && squashT >= 12 ? 'laugh' : 'scared';
            return <Germ key={i} x={x} y={y + (1 - sq) * r} r={r} f={f} seed={70 + i} col={GERM_COLS[i % 4]} expr={ex} look={[0, -1]} scale={sc} sx={1 / Math.max(0.5, sq) * (sq < 1 ? 1.2 : 1)} sy={sq} />;
          })}
          {/* phone bezel + glass */}
          <path d="M -50 -50 H 1130 V 1970 H -50 Z M 40 120 Q 40 40 120 40 H 960 Q 1040 40 1040 120 V 1800 Q 1040 1880 960 1880 H 120 Q 40 1880 40 1800 Z" fill="#2B2F36" fillRule="evenodd" />
          <path d="M 40 120 Q 40 40 120 40 H 960 Q 1040 40 1040 120 V 1800 Q 1040 1880 960 1880 H 120 Q 40 1880 40 1800 Z" fill="none" stroke={INK} strokeWidth={8} />
          <rect x={420} y={58} width={240} height={42} rx={21} fill="#0E0F12" />
          <path d="M 40 300 L 300 40 L 420 40 L 40 420 Z" fill="#fff" opacity={0.07} />
          <path d="M 1040 1300 L 600 1880 L 700 1880 L 1040 1440 Z" fill="#fff" opacity={0.05} />
          {impact && <ellipse cx={540} cy={960} rx={430 * clamp(squashT / 6)} ry={520 * clamp(squashT / 6)} fill="#fff" opacity={0.12 * (1 - clamp((squashT - 10) / 12))} />}
        </g>
      }
    />
  );
};
