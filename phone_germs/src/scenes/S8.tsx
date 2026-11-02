import React from 'react';
import {Stage, Cam} from '../lib/stage';
import {SceneProps, drift} from './common';
import {L} from '../timeline';
import {prog, lerp, easeInOutSine, snapEase, easeInOutCubic, easeOutCubic, easeInCubic, kf, clamp, rnd, popIn} from '../lib/ease';
import {Hero, HeroProps, heroHand, Expr, INK} from '../components/Hero';
import {Toilet} from '../components/Toilet';
import {Phone} from '../components/Phone';
import {Germ, GERM_COLS} from '../components/Germ';
import {Wall, Floor} from '../components/Room';
import {Sparkle, Arrow} from '../components/Fx';
import {Wipes, Towel} from '../components/Props';
import {HOLD_ARM, PHONE_OFF, PHONE_W, LoopGerm} from './S1';

const FLOOR = 1650;

export const S8: React.FC<SceneProps> = ({f, dur, tin, tout}) => {
  const tDirt = L('S8', 'dirtiest'), tMight = L('S8', 'might'), tOne = L('S8', 'one in your'), tHand = L('S8', 'hand'), tAnd = L('S8', 'and a quick'), tWipe = L('S8', 'wipe'), tOnce = L('S8', 'once a day'), tRem = L('S8', 'removes'), tThem = L('S8', 'them');
  const HS = 1.2;
  const heroBase: HeroProps = {x: 380, y: FLOOR, s: HS, f, seed: 1, armR: HOLD_ARM};
  const hand = heroHand(heroBase, 'R');
  const phone: [number, number] = [hand[0] + PHONE_OFF[0] * HS, hand[1] + PHONE_OFF[1] * HS];
  const thumbs = f >= tRem;
  const expr: Expr = f >= tRem ? 'smug' : f >= tWipe + 10 ? 'happy' : f >= tHand ? 'shocked' : 'neutral';
  const exprAt = f >= tRem ? tRem : f >= tWipe + 10 ? tWipe + 10 : f >= tHand ? tHand : undefined;
  const wipeIn = prog(f, tAnd, tAnd + 14, easeOutCubic);
  const hero: HeroProps = {
    ...heroBase, expr, exprAt, look: f >= tRem ? [0.55, 0.15] : [0.7, -0.2],
    armL: thumbs ? kf(f, [[tRem, 0], [tRem + 8, 1]]) > 0.5 ? [-110, -60] : [-40, -40] : [lerp(18, -40, wipeIn), lerp(-40, -30, wipeIn)],
    thumbL: thumbs && f >= tRem + 6,
  };
  // germs on the phone screen (phone-local), flung off by the wipe with smear
  const wipeP = prog(f, tWipe - 4, tWipe + 14, easeInOutCubic);
  const wipeX = lerp(-140, 140, wipeP);
  const spots: [number, number, number][] = [[-26, -60, 17], [24, -20, 15], [-20, 30, 16], [28, 70, 14], [-30, 100, 13], [20, -110, 14]];
  const flying: React.ReactNode[] = [];
  const onScreen = spots.map(([x, y, r], i) => {
    const hitT = tWipe - 4 + ((x + 140) / 280) * 18;
    if (f >= hitT) {
      const t = f - hitT;
      if (t < 40) {
        const vx = 18 + rnd(i) * 10, vy = -12 - rnd(i * 3) * 10;
        const px = phone[0] + x * HS + vx * t * 3, py = phone[1] + y * HS + vy * t * 3 + 0.9 * t * t;
        flying.push(<Germ key={i} x={px} y={py} r={r * HS} f={f} seed={80 + i} col={GERM_COLS[i % 4]} expr="shocked" sx={t < 3 ? 1.9 : 1} sy={t < 3 ? 0.6 : 1} rot={t * 12} />);
      }
      return null;
    }
    return <Germ key={i} x={x} y={y} r={r} f={f} seed={80 + i} col={GERM_COLS[i % 4]} expr={f >= tHand ? 'laugh' : 'happy'} scale={1} />;
  });
  const clean = f >= tWipe + 10;
  const loopGerm = prog(f, tThem + 6, tThem + 16);
  const screen = clean ? (f >= dur - 10 ? 'feed' : 'lock') : 'feed';
  const glow = f >= tOne && !clean;
  const cam = (f: number): Cam => {
    // start on the clean toilet, PULL_BACK and pan down to the phone in Hero's hand
    let x = 780, y = 1180, z = 1.7;
    const pb = prog(f, tDirt - 6, tMight, easeInOutCubic);
    x = lerp(x, 600, pb); y = lerp(y, 1120, pb); z = lerp(z, 1.0, pb);
    const pan = prog(f, tMight, tOne, easeInOutCubic);
    x = lerp(x, phone[0] + 60, pan); y = lerp(y, phone[1] + 160, pan); z = lerp(z, 1.55, pan);
    const sn = prog(f, tAnd, tAnd + 10, snapEase);
    x = lerp(x, phone[0] - 40, sn); y = lerp(y, phone[1] + 80, sn); z = lerp(z, 2.3, sn);
    const back = prog(f, tRem - 4, tRem + 22, easeInOutCubic);
    x = lerp(x, 470, back); y = lerp(y, 1080, back); z = lerp(z, 1.35, back);
    // final push-in: end exactly on frame-0 framing (phone centered, zoom 3) for the loop
    const fin = prog(f, tThem - 8, dur - 1, easeInOutCubic);
    x = lerp(x, phone[0], fin); y = lerp(y, phone[1], fin); z = lerp(z, 3, fin);
    const [dx, dy] = drift(f);
    const dk = 1 - fin;
    return {x: x + dx * dk, y: y + dy * dk, z, r: Math.sin(f / 50) * 1 * dk};
  };
  return (
    <Stage f={f} dur={dur} tin={tin} tout={tout} cam={cam}
      bg={<Wall cx={600} cy={900} />}
      mid={<Towel x={1150} y={850} s={1.3} col="#FF4FA3" />}
      subj={
        <g>
          <Floor y={FLOOR} />
          <Toilet x={780} y={FLOOR} s={0.85} lid={0} />
          {[0, 1, 2].map((k) => <Sparkle key={k} x={780 + [-90, 80, 0][k]} y={[1150, 1250, 1350][k]} t={(f + k * 14) % 44} s={0.6} seed={k * 5 + 2} rad={120} />)}
          <Hero {...hero} holdR={
            <Phone x={PHONE_OFF[0]} y={PHONE_OFF[1]} w={PHONE_W} f={f} id="s8" screen={screen as 'feed' | 'lock'} scroll={screen === 'feed' && clean ? 0 : f * 1.2} glow={glow ? 'green' : clean && f < tRem + 20 ? 'white' : null} glowAmt={glow ? 0.6 + 0.4 * Math.sin(f * 0.3) : 1 - prog(f, tRem, tRem + 20)} shine={prog(f, tOnce, tOnce + 24)}>
              {onScreen}
              {loopGerm > 0 && <LoopGerm f={f} scale={popIn(f, tThem + 6, 10)} />}
            </Phone>
          } holdL={wipeIn > 0 && !thumbs ? <g transform={`scale(${wipeIn})`}><Wipes x={0} y={30} s={0.5} /></g> : undefined} />
          {/* the wipe sweeping across the screen */}
          {wipeP > 0 && wipeP < 1 && (
            <g transform={`translate(${phone[0] + wipeX * HS} ${phone[1]}) rotate(-12)`}>
              <rect x={-60} y={-150} width={120} height={300} rx={20} fill="#fff" stroke={INK} strokeWidth={5} />
              <path d="M -40 -120 L -40 120 M 0 -120 L 0 120 M 40 -120 L 40 120" stroke="#DCEFF7" strokeWidth={6} />
            </g>
          )}
          {flying}
          <Sparkle x={phone[0]} y={phone[1]} t={f - tOnce + 4} s={1.2} rad={200} />
          <Arrow x={phone[0] + 230} y={phone[1] - 10} rot={180} t={f >= tOne && f < tAnd + 6 ? f - tOne : -1} s={0.9} />
        </g>
      }
    />
  );
};
