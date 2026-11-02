import React from 'react';
import {Stage, Cam} from '../lib/stage';
import {SceneProps, drift} from './common';
import {L} from '../timeline';
import {prog, lerp, easeInOutSine, snapEase, easeInOutCubic, easeOutCubic, kf, clamp, damped, popIn, easeOutBack} from '../lib/ease';
import {Hero, HeroProps, heroHand, walkLegs, armTo, INK} from '../components/Hero';
import {Phone} from '../components/Phone';
import {Germ, GERM_COLS} from '../components/Germ';
import {Wall, Floor} from '../components/Room';
import {DoorHandle, DollarBill, SnackBag, Plant, Lamp} from '../components/Props';

export const S4_PHONE_W = 110;
const FLOOR = 1700, HS = 1.4;
const X1 = 1000, X2 = 1800, X3 = 2600; // touch points (hand x)
const HAND_Y = 1205;

/** germ leaping on a parabola from a -> b, with stretch (smear) in flight and squash on landing */
function leap(f: number, t0: number, a: [number, number], b: [number, number], dur = 12) {
  const p = clamp((f - t0) / dur);
  const x = lerp(a[0], b[0], p), y = lerp(a[1], b[1], p) - Math.sin(Math.PI * p) * 110;
  const vy = (b[1] - a[1]) - Math.cos(Math.PI * p) * 110 * Math.PI;
  const vx = b[0] - a[0];
  const inAir = p > 0 && p < 1;
  const rot = inAir ? (Math.atan2(vy, vx) * 180) / Math.PI + 90 : 0;
  const land = f - (t0 + dur);
  const sq = land >= 0 && land < 6 ? 0.75 + 0.25 * (land / 6) : 1;
  return {x, y, rot, sx: inAir ? 0.8 : 1 / sq, sy: inAir ? 1.3 : sq, p};
}

export const S4: React.FC<SceneProps> = ({f, dur, tin, tout}) => {
  const tDoor = L('S4', 'door'), tHandle = L('S4', 'handle'), tDollar = L('S4', 'dollar'), tBill = L('S4', 'bill'), tSnack = L('S4', 'snack');
  const tTouch = L('S4', 'touch', 17.9), tEnds = L('S4', 'ends up'), tRight = L('S4', 'right on'), tScreen = L('S4', 'screen', 19);
  const touches = [tHandle, tBill, tTouch];
  const handX = (f: number) => kf(f, [[0, 330], [tHandle - 4, X1 - 8, easeInOutSine], [tHandle + 2, X1], [tHandle + 16, X1 + 4], [tBill - 4, X2 - 8, easeInOutSine], [tBill + 2, X2], [tBill + 16, X2 + 4], [tTouch - 4, X3 - 8, easeInOutSine], [tTouch + 2, X3], [dur, X3 + 10]]);
  // side-view reach pose
  const turn = 1 - prog(f, tEnds - 6, tEnds + 8, easeInOutCubic);
  const reachArm: [number, number] = [82, 6];
  const base: HeroProps = {x: 0, y: FLOOR, s: HS, f, bodyTurn: 1, armR: reachArm};
  const off = heroHand(base, 'R')[0];
  const heroX = (f: number) => handX(Math.min(f, tEnds)) - off;
  const hx = heroX(f);
  const moving = Math.abs(heroX(f + 1) - heroX(f - 1)) > 0.8;
  const walk = walkLegs(hx / 42, moving ? 1 : 0.15);
  // poke at each touch
  const poke = Math.max(...touches.map((t) => kf(f, [[t - 6, 0], [t - 3, -0.2], [t, 1, easeOutCubic], [t + 5, 1], [t + 12, 0]])));
  // front-facing phone pose after "ends up"
  const phonePos: [number, number] = [hx - 10, 1290];
  let armR: [number, number] = [82 + poke * 6, 6 - poke * 6];
  let armL: [number, number] = [-10 + walk.legL[0] * 0.5, -20];
  const tapT = (t: number) => kf(f, [[t - 8, 0], [t - 2, 1, easeOutCubic], [t + 4, 1], [t + 12, 0]]);
  if (f >= tEnds - 6) {
    const front: HeroProps = {x: hx, y: FLOOR, s: HS, f, bodyTurn: 0};
    armL = armTo(front, 'L', [phonePos[0] - 40, phonePos[1] + 140], -1);
    const tap = Math.max(tapT(tRight), tapT(tScreen));
    const rest: [number, number] = [hx + 60, 1120];
    const tgt: [number, number] = [lerp(rest[0], phonePos[0] + 8, tap), lerp(rest[1], phonePos[1] + 10, tap)];
    const ar = armTo(front, 'R', tgt, 1);
    armR = turn > 0 ? [lerp(ar[0], armR[0], turn), lerp(ar[1], armR[1], turn)] : ar;
  }
  const hero: HeroProps = {
    x: hx, y: FLOOR - walk.bob * (moving ? 1 : 0), s: HS, f, seed: 4, bodyTurn: turn, look: [turn > 0.5 ? 1 : -0.35, turn > 0.5 ? 0 : 0.5],
    legL: walk.legL, legR: walk.legR, armR, armL,
    expr: f >= tEnds ? 'neutral' : 'focused', exprAt: f >= tEnds ? tEnds : undefined,
  };
  const hand = heroHand(hero, 'R');
  // camera: DOLLY_TRACK on the hand (spring 120/20), then SNAP_ZOOM on the phone
  const cam = (f: number): Cam => {
    const cx = damped(f, (k) => handX(Math.min(k, tEnds)) - 40, 120, 20);
    let x = cx, y = 1100, z = 1.55;
    touches.forEach((t) => { z *= 1 + 0.12 * kf(f, [[t - 2, 0], [t + 4, 1, easeOutCubic], [t + 24, 0]]); });
    const toPhone = prog(f, tEnds - 4, tEnds + 20, easeInOutCubic);
    x = lerp(x, phonePos[0], toPhone); y = lerp(y, phonePos[1] + 60, toPhone);
    const sn = prog(f, tRight, tRight + 10, snapEase);
    z = lerp(z, 2.3, sn); y = lerp(y, phonePos[1] + 20, sn);
    const sn2 = prog(f, tScreen, tScreen + 10, snapEase);
    z = lerp(z, 3.1, sn2); y = lerp(y, phonePos[1], sn2);
    const [dx, dy] = drift(f, 6);
    return {x: x + dx, y: y + dy, z, r: lerp(-1.5, 1.5, prog(f, 0, dur, easeInOutSine))};
  };
  // objects pop in on their words
  const glowAmt = (t: number) => (f >= t ? 0.6 + 0.4 * Math.sin((f - t) * 0.25) : 0);
  // germs on the fingertip (hand-relative offsets)
  const fingerSpots: [number, number][] = [[30, -18], [16, 20], [-4, -30], [40, 10], [8, 34], [-14, 4]];
  const sources: [number, number][] = [[X1 + 60, HAND_Y - 10], [X1 + 40, HAND_Y + 30], [X2 + 40, 1200], [X2 + 90, 1215], [X3 + 20, 1120], [X3 - 30, 1180]];
  const jumpT = [tHandle + 4, tHandle + 10, tBill + 4, tBill + 10, tTouch + 4, tTouch + 10];
  const scr: [number, number][] = [[-30, -60], [30, -10], [-20, 50], [34, 80], [-34, 110], [10, -110]];
  const toScreenT = [tRight + 2, tRight + 6, tRight + 10, tScreen + 2, tScreen + 6, tScreen + 10];
  const phoneScale = HS; // phone drawn in world units
  const germs = jumpT.map((jt, i) => {
    if (f < jt) return null;
    const fp: [number, number] = [hand[0] + fingerSpots[i][0], hand[1] + fingerSpots[i][1]];
    const sp: [number, number] = [phonePos[0] + scr[i][0] * phoneScale * 0.6, phonePos[1] + scr[i][1] * phoneScale * 0.6];
    const onScreen = f >= toScreenT[i];
    const l = onScreen ? leap(f, toScreenT[i], fp, sp, 12) : leap(f, jt, sources[i], fp, 12);
    return <Germ key={i} x={l.x} y={l.y} r={17} col={GERM_COLS[i % 4]} f={f} seed={20 + i} expr={onScreen && l.p >= 1 ? 'happy' : 'happy'} rot={l.rot} sx={l.sx} sy={l.sy} />;
  });
  const showPhone = f >= tEnds - 30;
  const phoneIn = easeOutBack(prog(f, tEnds - 30, tEnds - 10));
  return (
    <Stage f={f} dur={dur} tin={tin} tout={tout} cam={cam}
      bg={<Wall cx={damped(f, (k) => handX(Math.min(k, tEnds)), 120, 20)} cy={1000} door={null} tiles={false} />}
      mid={<g>{[200, 900, 1600, 2300, 3000].map((x, i) => <rect key={i} x={x} y={600} width={260} height={180} rx={14} fill={['#FFD84A', '#9B4DFF', '#4FA3E0', '#FF8A1F', '#39E35B'][i]} opacity={0.35} />)}</g>}
      subj={
        <g>
          <Floor y={FLOOR} />
          {/* door + handle */}
          <g transform={`translate(${X1 + 210} ${FLOOR}) scale(1 ${popIn(f, tDoor - 6, 12)})`}>
            <rect x={-150} y={-900} width={300} height={900} rx={8} fill="#E9D7C2" stroke={INK} strokeWidth={4} />
            <rect x={-110} y={-840} width={220} height={320} rx={6} fill="none" stroke="#CDB79E" strokeWidth={6} />
          </g>
          {f >= tDoor - 6 && <DoorHandle x={X1 + 150} y={HAND_Y} s={0.7 * popIn(f, tDoor - 2, 10)} rot={180} press={kf(f, [[tHandle, 0], [tHandle + 4, 1], [tHandle + 14, 0]])} glow={f >= tHandle} glowAmt={glowAmt(tHandle)} />}
          {/* table for the bill and the snack */}
          {[X2 + 80, X3 + 60].map((tx, i) => (
            <g key={i} transform={`translate(${tx} ${FLOOR}) scale(1 ${popIn(f, (i ? tSnack : tDollar) - 8, 10)})`}>
              <rect x={-170} y={-430} width={340} height={30} rx={8} fill="#C98B5B" stroke={INK} strokeWidth={4} />
              <rect x={-140} y={-400} width={22} height={400} fill="#A86F45" stroke={INK} strokeWidth={4} />
              <rect x={118} y={-400} width={22} height={400} fill="#A86F45" stroke={INK} strokeWidth={4} />
            </g>
          ))}
          {f >= tDollar && <DollarBill x={X2 + 110} y={1222} s={0.62 * popIn(f, tDollar, 10)} rot={-8} glow={f >= tBill} glowAmt={glowAmt(tBill)} />}
          {f >= tSnack && <SnackBag x={X3 + 70} y={1145} s={0.8 * popIn(f, tSnack, 10)} rot={6} glow={f >= tTouch} glowAmt={glowAmt(tTouch)} />}
          {/* sitting germs on the objects before they jump */}
          {[0, 1, 2, 3, 4, 5].map((i) => (f < jumpT[i] && f >= [tDoor, tDoor, tDollar, tDollar, tSnack, tSnack][i] + 6 ? <Germ key={i} x={sources[i][0]} y={sources[i][1]} r={17} col={GERM_COLS[i % 4]} f={f} seed={20 + i} expr="smug" scale={popIn(f, [tDoor, tDoor, tDollar, tDollar, tSnack, tSnack][i] + 6 + (i % 2) * 3, 8)} sy={f > jumpT[i] - 4 ? 0.7 : 1} /> : null))}
          <Hero {...hero} />
          {showPhone && turn < 1 && (
            <g transform={`translate(${phonePos[0]} ${phonePos[1]}) scale(${phoneIn}) translate(${-phonePos[0]} ${-phonePos[1]})`}>
              <Phone x={phonePos[0]} y={phonePos[1]} w={S4_PHONE_W * HS} f={f} id="s4" />
              <circle cx={heroHand(hero, 'L')[0]} cy={heroHand(hero, 'L')[1]} r={19 * HS} fill="#F7F7F5" stroke={INK} strokeWidth={6 * HS} />
            </g>
          )}
          {f >= tEnds - 6 && <g><circle cx={hand[0]} cy={hand[1]} r={19 * HS} fill="#F7F7F5" stroke={INK} strokeWidth={6 * HS} /></g>}
          {germs}
        </g>
      }
      fg={
        <g>
          <Plant x={X1 + 520} y={FLOOR + 380} s={1.5} />
          <Lamp x={X2 + 560} y={FLOOR + 420} s={1.4} />
          <Plant x={X3 + 560} y={FLOOR + 380} s={1.3} />
        </g>
      }
    />
  );
};
