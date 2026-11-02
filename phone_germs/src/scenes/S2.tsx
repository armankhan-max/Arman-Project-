import React from 'react';
import {Stage, Cam} from '../lib/stage';
import {SceneProps, drift} from './common';
import {L} from '../timeline';
import {prog, lerp, easeInOutSine, snapEase, easeInOutCubic, kf, clamp} from '../lib/ease';
import {Hero, HeroProps, Expr} from '../components/Hero';
import {Toilet} from '../components/Toilet';
import {Wall, Floor} from '../components/Room';
import {Skull, DangerGlow, Stink, Sweat, Exclaim} from '../components/Fx';
import {Plant} from '../components/Props';

export const S2: React.FC<SceneProps> = ({f, dur, tin, tout}) => {
  const tDirt = L('S2', 'dirtiest'), tTouch = L('S2', 'touch all day'), tLit = L('S2', "it's literally"), tWaste = L('S2', 'waste');
  const cam = (f: number): Cam => {
    const push = prog(f, 0, tDirt, easeInOutSine);
    let z = lerp(1.0, 1.12, push), x = lerp(470, 500, push), y = 1130;
    const sn = prog(f, tDirt, tDirt + 10, snapEase);
    z *= 1 + 0.35 * sn; x = lerp(x, 480, sn); y = lerp(y, 1110, sn);
    // dolly toward the poking hand
    const dl = prog(f, tDirt + 12, tLit, easeInOutCubic);
    x = lerp(x, 450, dl); z *= lerp(1, 0.96, dl);
    // ORBIT_FAKE
    const ob = prog(f, tLit, dur, easeInOutSine);
    const orb = f >= tLit ? lerp(-6, 6, ob) : 0;
    z = lerp(z, 1.25, prog(f, tLit, tLit + 30, easeInOutCubic));
    x = lerp(x, 520, prog(f, tLit, tLit + 40, easeInOutCubic));
    const [dx, dy] = drift(f);
    return {x: x + dx, y: y + dy, z, r: orb, orb};
  };
  const exprAt = f >= tWaste ? tWaste : f >= tTouch + 14 ? tTouch + 14 : f >= tTouch ? tTouch : f >= tDirt ? tDirt : 0;
  const expr: Expr = f >= tWaste ? 'scared' : f >= tTouch + 14 ? 'disgusted' : f >= tTouch ? 'shocked' : f >= tDirt ? 'disgusted' : 'neutral';
  const poke = kf(f, [[tTouch - 14, 0], [tTouch - 10, -0.15], [tTouch, 1, easeInOutCubic], [tTouch + 6, 1], [tTouch + 16, 0]]);
  const lean = kf(f, [[0, -4], [tDirt, -4], [tDirt + 8, -14], [tTouch - 4, -6], [tTouch + 4, -2], [tTouch + 14, -18], [dur, -16]]);
  const hero: HeroProps = {
    x: 250, y: 1560, s: 1.05, f, seed: 2, lean, expr, exprAt,
    look: [0.8, 0.2], tint: f >= tDirt ? clamp((f - tDirt) / 6) * (expr === 'shocked' ? 0.5 : 1) : 0,
    armR: [lerp(30, 88, poke), lerp(-10, 2, poke)],
    armL: f >= tTouch + 10 ? [-150, 30] : [-20, 10],
  };
  const rattle = f >= tWaste ? Math.abs(Math.sin((f - tWaste) * 0.9)) * Math.max(0, 1 - (f - tWaste) / 22) : 0;
  return (
    <Stage f={f} dur={dur} tin={tin} tout={tout} cam={cam}
      bg={<Wall cx={560} cy={1000} />}
      mid={<Plant x={980} y={1560} s={0.8} />}
      subj={
        <g>
          <Floor y={1560} />
          <DangerGlow x={600} y={1200} rx={430} ry={380} amt={0.6 + 0.4 * Math.sin(f * 0.12)} f={f} />
          <Toilet x={620} y={1560} s={0.85} lid={0} rattle={rattle} glow="red" glowAmt={0.55 + 0.25 * Math.sin(f * 0.2)} />
          <Stink x={620} y={1250} f={f} s={1.1} />
          <Stink x={540} y={1100} f={f + 30} s={0.8} />
          <Skull x={820} y={880} s={0.95} t={f - 6} />
          <Hero {...hero} />
          {f >= tWaste && <Exclaim x={280} y={860} t={f - tWaste} s={1.1} />}
          {f >= tDirt && f < tWaste && <Sweat x={120} y={980} t={f - tDirt} />}
        </g>
      }
    />
  );
};
