import React from 'react';
import {Stage, Cam} from '../lib/stage';
import {SceneProps, drift} from './common';
import {L} from '../timeline';
import {prog, lerp, easeInOutSine, snapEase, easeInOutCubic, easeOutCubic, kf, clamp, damped, rnd} from '../lib/ease';
import {Hero, HeroProps, heroHand, walkLegs, armTo, Expr, INK} from '../components/Hero';
import {Toilet} from '../components/Toilet';
import {Phone} from '../components/Phone';
import {Wall, Floor} from '../components/Room';
import {Exclaim, Sweat} from '../components/Fx';
import {Towel, Plant} from '../components/Props';

const FLOOR = 1650, TX = 640, TS = 0.85, HS = 1.15;
const PHONE_W = 110;

export const S6: React.FC<SceneProps> = ({f, dur, tin, tout}) => {
  const tCarry = L('S6', 'carry'), tBath = L('S6', 'bathroom'), tWhere = L('S6', 'where tiny'), tDrop = L('S6', 'tiny droplets'), tFlushW = L('S6', 'flushing');
  const tFloat = L('S6', 'float'), tLand = L('S6', 'land on it');
  const tPlace = tBath + 14; // phone set on the tank
  const heroX = (f: number) => kf(f, [[0, -380], [tBath + 4, 330, easeOutCubic], [dur, 336]]);
  const hx = heroX(f);
  const moving = f < tBath;
  const walk = walkLegs(hx / 40, moving ? 1 : 0);
  const tankTop = FLOOR - 664 * TS;
  const phoneRest: [number, number] = [TX + 20, tankTop - PHONE_W * 1.02 - 2];
  const lever: [number, number] = [TX - 128 * TS, FLOOR - 600 * TS];
  const base: HeroProps = {x: hx, y: FLOOR - walk.bob, s: HS, f, seed: 6, bodyTurn: moving ? 1 : 0.35, legL: walk.legL, legR: walk.legR};
  // arm choreography
  const carryHand: [number, number] = [hx + 150, FLOOR - 330];
  const reach = kf(f, [[tBath - 6, 0], [tPlace, 1, easeInOutCubic], [tPlace + 10, 1], [tPlace + 24, 0]]);
  const press = kf(f, [[tWhere - 14, 0], [tWhere - 2, 1, easeInOutCubic], [tWhere + 8, 1], [tWhere + 22, 0]]);
  let tgt: [number, number] = [lerp(carryHand[0], phoneRest[0] - 4, reach), lerp(carryHand[1], phoneRest[1] + 100, reach)];
  if (f > tPlace + 10) tgt = [lerp(hx + 70, lever[0] + 8, press), lerp(FLOOR - 330, lever[1] - 6, press)];
  const armR = armTo(base, 'R', tgt, 1);
  const expr: Expr = f >= tDrop + 16 ? 'shocked' : f > tPlace + 10 ? 'focused' : 'neutral';
  const hero: HeroProps = {...base, armR, armL: [-14 + walk.legL[0] * 0.4, -10], expr, exprAt: f >= tDrop + 16 ? tDrop + 16 : undefined, look: f >= tDrop + 16 ? [0.6, -0.8] : [1, 0], lean: f >= tDrop + 16 ? -8 : 0};
  const hand = heroHand(hero, 'R');
  const phoneHeld = f < tPlace;
  const phonePos: [number, number] = phoneHeld ? [hand[0], hand[1] - 62 * HS] : phoneRest;
  const flush = kf(f, [[tWhere - 4, 0], [tWhere, 1], [tWhere + 14, 1], [tWhere + 24, 0]]);
  // droplet cloud: 60 dots rising in slow motion, drifting, then landing on the phone
  const drops = Array.from({length: 60}).map((_, i) => {
    const t0 = tDrop - 6 + rnd(i) * 26;
    const p = clamp((f - t0) / (tLand - t0 + 10));
    if (f < t0) return null;
    const ox = TX + (rnd(i * 3) - 0.5) * 200, oy = FLOOR - 330 * TS;
    const rise = 260 + rnd(i * 5) * 420;
    let x = ox + (rnd(i * 7) - 0.5) * 520 * easeOutCubic(p) + Math.sin(f * 0.05 + i) * 22;
    let y = oy - rise * easeOutCubic(Math.min(1, p * 1.25)) + Math.cos(f * 0.04 + i * 2) * 14;
    const land = prog(f, tLand - 4 + rnd(i * 11) * 14, tLand + 18 + rnd(i * 11) * 14, easeInOutCubic);
    const sx = phoneRest[0] + (rnd(i * 13) - 0.5) * PHONE_W * 0.8, sy = phoneRest[1] + (rnd(i * 17) - 0.5) * PHONE_W * 1.7;
    x = lerp(x, sx, land); y = lerp(y, sy, land);
    const cols = ['#5FD3C4', '#7EC8E3', '#39E35B', '#9BE59B'];
    const r = (5 + rnd(i * 19) * 9) * (1 - 0.4 * land);
    return <circle key={i} cx={x} cy={y} r={r} fill={cols[i % 4]} stroke={INK} strokeWidth={2.5} opacity={clamp((f - t0) / 6)} />;
  });
  const cam = (f: number): Cam => {
    let x = damped(f, (k) => heroX(k) + 200, 120, 20), y = 1150, z = 1.2;
    const pp = prog(f, tBath, tWhere, easeInOutCubic);
    x = lerp(x, TX - 60, pp); z = lerp(z, 1.35, pp); y = lerp(y, 1120, pp);
    // follow the cloud up (slow-mo feel)
    const up = prog(f, tDrop, tFloat, easeInOutSine);
    y = lerp(y, 860, up); z = lerp(z, 1.15, up); x = lerp(x, TX, up);
    // ORBIT_FAKE around the cloud
    const ob = prog(f, tFloat, tLand, easeInOutSine);
    const orb = f >= tFloat ? lerp(-6, 6, ob) * (1 - prog(f, tLand, tLand + 12)) : 0;
    // land: SNAP_ZOOM on the phone
    const sn = prog(f, tLand, tLand + 10, snapEase);
    x = lerp(x, phoneRest[0], sn); y = lerp(y, phoneRest[1] + 10, sn); z = lerp(z, 2.2, sn);
    z *= 1 + 0.1 * prog(f, tLand + 10, dur, (t) => t * t);
    const [dx, dy] = drift(f);
    return {x: x + dx, y: y + dy, z, r: orb, orb};
  };
  const dirty = prog(f, tLand + 8, tLand + 24);
  return (
    <Stage f={f} dur={dur} tin={tin} tout={tout} cam={cam}
      bg={<Wall cx={TX} cy={900} door={-260} />}
      mid={<g><Towel x={1100} y={900} s={1.4} col="#4FA3E0" /><Plant x={1180} y={FLOOR} s={0.9} /></g>}
      subj={
        <g>
          <Floor y={FLOOR} />
          <Toilet x={TX} y={FLOOR} s={TS} lid={1} flush={flush} />
          {!phoneHeld && <Phone x={phonePos[0]} y={phonePos[1]} w={PHONE_W} f={f} id="s6" glow={dirty > 0 ? 'green' : null} glowAmt={dirty * (0.6 + 0.4 * Math.sin(f * 0.3))} />}
          <Hero {...hero} holdR={phoneHeld ? <Phone x={0} y={-62} w={PHONE_W / HS} f={f} id="s6h" /> : undefined} />
          {f >= tDrop + 16 && <Exclaim x={hx + 40} y={FLOOR - 760} t={f - tDrop - 16} />}
          {f >= tFloat && <Sweat x={hx - 90} y={FLOOR - 640} t={f - tFloat} />}
          {drops}
        </g>
      }
    />
  );
};
