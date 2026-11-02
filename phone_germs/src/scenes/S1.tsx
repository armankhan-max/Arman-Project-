import React from 'react';
import {Stage, Cam} from '../lib/stage';
import {SceneProps, drift} from './common';
import {L} from '../timeline';
import {prog, lerp, easeInOutCubic, snapEase, linear, clamp, popIn} from '../lib/ease';
import {Hero, HeroProps, heroHand} from '../components/Hero';
import {Toilet} from '../components/Toilet';
import {Phone} from '../components/Phone';
import {Germ, GERM} from '../components/Germ';
import {Wall, Floor} from '../components/Room';
import {Skull, DangerGlow} from '../components/Fx';
import {ToiletPaper} from '../components/Props';

// shared with S8 so the last frame matches the first (loop)
export const HOLD_ARM: [number, number] = [80, 90];
export const PHONE_OFF: [number, number] = [0, -100];
export const PHONE_W = 100;
export const S1_HERO: HeroProps = {x: 540, y: 1482, s: 1.2, f: 0, sit: 227, armR: HOLD_ARM, armL: [18, -40], expr: 'smug', look: [0.55, 0.15], seed: 1};

export const LoopGerm: React.FC<{f: number; scale?: number}> = ({f, scale = 1}) => (
  <Germ x={0} y={14} r={30} col={GERM.green} f={f} seed={7} expr="happy" wave scale={scale} />
);

export const S1: React.FC<SceneProps> = ({f, dur, tin, tout}) => {
  const tSnap = L('S1', 'toilet seat');
  const hw = heroHand(S1_HERO, 'R');
  const phoneWorld: [number, number] = [hw[0] + PHONE_OFF[0] * 1.2, hw[1] + PHONE_OFF[1] * 1.2];
  const cam = (f: number): Cam => {
    const pb = prog(f, 0, 72, easeInOutCubic);
    let x = lerp(phoneWorld[0], 560, pb), y = lerp(phoneWorld[1], 1010, pb), z = lerp(3, 1, pb);
    const sn = prog(f, tSnap, tSnap + 10, snapEase);
    x = lerp(x, 560, sn); y = lerp(y, 1190, sn); z = z * (1 + 0.35 * sn);
    z *= 1 + 0.07 * prog(f, tSnap + 10, dur, linear) + 0.05 * prog(f, dur - 14, dur, (t) => t * t);
    const [dx, dy] = drift(f);
    return {x: x + dx * pb, y: y + dy * pb, z, r: Math.sin(f / 70) * 0.6};
  };
  const danger = prog(f, tSnap, tSnap + 8);
  const hero: HeroProps = {
    ...S1_HERO, f,
    holdR: <Phone x={PHONE_OFF[0]} y={PHONE_OFF[1]} w={PHONE_W} f={f} id="s1" scroll={f * 1.2}>
      <LoopGerm f={f} />
    </Phone>,
    expr: f >= tSnap + 2 ? 'smug' : 'smug', thumbR: false,
  };
  const tp = prog(f, 26, 96, linear);
  return (
    <Stage f={f} dur={dur} tin={tin} tout={tout} cam={cam}
      bg={<Wall cx={560} cy={900} mirror={null} />}
      mid={<g><ToiletPaper x={1000} y={1080} s={0.7} /><rect x={890} y={1060} width={30} height={40} fill="#B8C4CF" /></g>}
      subj={
        <g>
          <Floor y={1500} />
          <DangerGlow x={540} y={1240} rx={420} ry={260} amt={danger} f={f} />
          <Toilet x={540} y={1500} s={0.72} lid={0} seatGlow={danger} glow={danger > 0 ? 'red' : null} glowAmt={danger * (0.7 + 0.3 * Math.sin(f * 0.25))} />
          <Hero {...hero} />
          <Skull x={790} y={1120} s={0.85} t={f - tSnap - 3} />
        </g>
      }
      fg={tp > 0 && tp < 1 ? <g transform={`rotate(${lerp(-20, 25, tp)} ${lerp(1250, -250, tp)} 1500)`}><ToiletPaper x={lerp(1250, -250, tp)} y={1500 + Math.sin(tp * Math.PI) * -120} s={1.6} /></g> : null}
    />
  );
};
