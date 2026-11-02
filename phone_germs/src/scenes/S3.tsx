import React from 'react';
import {Stage, Cam} from '../lib/stage';
import {SceneProps, drift} from './common';
import {L} from '../timeline';
import {prog, lerp, easeInOutSine, snapEase, easeInOutCubic, easeInCubic, easeOutCubic, kf, clamp, rnd, popIn} from '../lib/ease';
import {INK, HOOD, SKIN} from '../components/Hero';
import {Toilet} from '../components/Toilet';
import {Phone} from '../components/Phone';
import {Germ, GERM_COLS} from '../components/Germ';
import {Wall, Floor} from '../components/Room';
import {Sparkle, PopBurst, Stink} from '../components/Fx';
import {SprayBottle, Sink, Towel, Plant} from '../components/Props';

const SEAT_GERMS: [number, number][] = [[-138, -318], [-72, -298], [0, -292], [72, -298], [138, -318]];

export const S3: React.FC<SceneProps> = ({f, dur, tin, tout}) => {
  const tScrub = L('S3', 'scrubbed'), tDis = L('S3', 'disinfectant'), tEvery = L('S3', 'every day', 10.9), tPhone = L('S3', 'your phone almost'), tNever = L('S3', 'never');
  const CUT = tPhone; // CUT_ON_ACTION to the phone on the sink
  const pops = [tScrub - 16, tScrub + 14, tDis + 6, tDis + 30, tEvery - 18];
  if (f < CUT) {
    const cam = (f: number): Cam => {
      let x = lerp(470, 560, prog(f, 0, tDis, easeInOutSine)), y = 1180, z = lerp(1.25, 1.35, prog(f, 0, tDis, easeInOutSine));
      const sn = prog(f, tDis, tDis + 10, snapEase);
      z *= 1 + 0.35 * sn; x = lerp(x, 640, sn); y = lerp(y, 1290, sn);
      const pb = prog(f, tEvery, tEvery + 26, easeInOutCubic);
      z = lerp(z, 1.3, pb); y = lerp(y, 1220, pb);
      // accelerate right into the cut (cut on action)
      x += 900 * prog(f, CUT - 22, CUT, easeInCubic);
      const [dx, dy] = drift(f);
      return {x: x + dx, y: y + dy, z, r: Math.sin(f / 40) * 1.2};
    };
    const sprays = [8, tScrub - 4, tDis - 6, tDis + 22];
    const squeeze = Math.max(...sprays.map((s) => kf(f, [[s - 4, 0], [s, 1], [s + 10, 1], [s + 16, 0]])));
    const mist = sprays.map((s, k) => {
      const t = f - s;
      if (t < 0 || t > 40) return null;
      return Array.from({length: 22}).map((_, i) => {
        const p = clamp((t - rnd(i + k * 50) * 8) / 26);
        if (p <= 0 || p >= 1) return null;
        const ang = -0.05 + (rnd(i * 3 + k) - 0.5) * 0.7;
        const d = 60 + p * (300 + rnd(i * 7) * 160);
        return <circle key={k * 100 + i} cx={330 + Math.cos(ang) * d} cy={1105 + Math.sin(ang) * d + p * p * 120} r={6 + p * 18 * rnd(i + 9)} fill="#CFEFFF" stroke="#7EC8E3" strokeWidth={2} opacity={(1 - p) * 0.85} />;
      });
    });
    const seatClean = prog(f, tEvery - 4, tEvery + 10);
    const toiletKids = (
      <g>
        {SEAT_GERMS.map(([gx, gy], i) => {
          const tp = pops[i];
          const shrink = 1 - prog(f, tp - 10, tp, easeInCubic) * 0.6;
          if (f >= tp) return <PopBurst key={i} x={gx} y={gy - 24} t={f - tp} col={GERM_COLS[i % 4]} s={0.9} />;
          return <Germ key={i} x={gx} y={gy - 30} r={36} col={GERM_COLS[i % 4]} f={f} seed={i + 3} expr="scared" look={[-1, -0.4]} scale={shrink * popIn(f, -4 + i * 2, 8)} />;
        })}
        {seatClean > 0 && <ellipse cx={0} cy={-360} rx={176} ry={66} fill="none" stroke="#fff" strokeWidth={10} opacity={0.8 * (1 - prog(f, tEvery + 20, tEvery + 50))} />}
      </g>
    );
    return (
      <Stage f={f} dur={dur} tin={tin} tout="action" cam={cam}
        bg={<Wall cx={600} cy={1000} />}
        mid={<Plant x={1050} y={1700} s={0.8} />}
        subj={
          <g>
            <Floor y={1700} />
            <Toilet x={640} y={1700} s={1.1} lid={1}>{toiletKids}</Toilet>
            {f < tEvery && <Stink x={640} y={1260} f={f} s={0.8} op={1 - prog(f, tScrub, tDis + 20)} />}
            {/* arm + spray bottle entering from the left */}
            <g transform={`translate(${lerp(-200, 0, prog(f, 0, 14, easeOutCubic)) + Math.sin(f * 0.1) * 6} ${Math.sin(f * 0.08) * 6})`}>
              <path d="M -300 1260 L 170 1190" stroke={INK} strokeWidth={46} strokeLinecap="round" />
              <path d="M -300 1260 L 170 1190" stroke={HOOD} strokeWidth={34} strokeLinecap="round" />
              <SprayBottle x={190} y={1060} s={1.0} squeeze={squeeze} />
              <circle cx={215} cy={1180} r={30} fill={SKIN} stroke={INK} strokeWidth={6} />
            </g>
            {mist}
            <Sparkle x={640} y={1300} t={f - tEvery} s={1.3} rad={260} />
            <Sparkle x={560} y={1250} t={f - tEvery - 8} s={0.9} seed={9} />
          </g>
        }
      />
    );
  }
  // ---- 3b: phone lying on the sink, a germ lounging with sunglasses
  const g = f - CUT, d = dur - CUT, tn = tNever - CUT;
  const cam = (g: number): Cam => {
    let x = lerp(250, 540, prog(g, 0, 30, easeOutCubic)), y = 1150, z = lerp(1.45, 1.55, prog(g, 0, tn));
    const sn = prog(g, tn, tn + 10, snapEase);
    z *= 1 + 0.6 * sn; x = lerp(x, 560, sn); y = lerp(y, 1120, sn);
    z *= 1 + 0.06 * prog(g, tn + 10, d);
    const [dx, dy] = drift(g);
    return {x: x + dx, y: y + dy, z, r: lerp(-2, 2, prog(g, 0, d, easeInOutSine))};
  };
  const laugh = g >= tn;
  return (
    <Stage f={g} dur={d} tin="action" tout={tout} cam={cam}
      bg={<Wall cx={540} cy={900} mirror={[540, 860]} />}
      mid={<Towel x={1000} y={980} s={1.3} col="#9B4DFF" />}
      subj={
        <g>
          <Sink x={540} y={1240} s={1} />
          {/* phone lying flat on the counter */}
          <g transform="translate(540 1232) scale(1 0.34)">
            <ellipse cx={0} cy={30} rx={210} ry={60} fill="#000" opacity={0.15} />
            <Phone x={0} y={0} w={190} rot={90} f={g} id="s3b" glow={laugh ? 'green' : null} glowAmt={0.6 + 0.3 * Math.sin(g * 0.3)} />
          </g>
          <Towel x={490} y={1205} s={0.9} col="#FF4FA3" />
          <Germ x={560} y={1165} r={44} f={g} seed={11} col="#39E35B" expr={laugh ? 'laugh' : 'smug'} shades rot={laugh ? Math.sin(g * 0.5) * 6 : -14} sx={1.1} sy={laugh ? 0.92 + 0.08 * Math.abs(Math.sin(g * 0.5)) : 0.9} armUp={!laugh} />
          {laugh && [0, 1, 2].map((i) => <text key={i} x={630 + i * 34} y={1080 - i * 30 - ((g * 2) % 30)} fontFamily="Baloo2" fontWeight={800} fontSize={34 - i * 4} fill="#fff" stroke={INK} strokeWidth={6} paintOrder="stroke" opacity={1 - ((g * 2) % 30) / 30}>HA</text>)}
        </g>
      }
    />
  );
};
