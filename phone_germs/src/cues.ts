// SFX / music cue sheet, built from the SAME word anchors the scenes use.
import {L, SCENES, sceneStart, SceneId, TOTAL_FRAMES} from './timeline';

export type Cue = {f: number; sfx: string; gain?: number; pan?: number};
export function buildCues(): Cue[] {
  const c: Cue[] = [];
  const at = (id: SceneId, local: number, sfx: string, gain = 1, pan = 0) => c.push({f: sceneStart(id) + local, sfx, gain, pan});
  const dur = (id: SceneId) => { const s = SCENES.find((x) => x.id === id)!; return s.to - s.from; };
  // whip pans: whoosh centred on the cut
  ['S3', 'S4', 'S6', 'S8'].forEach((id) => c.push({f: sceneStart(id as SceneId) - 10, sfx: 'whoosh_whip', gain: 1}));
  // S1
  at('S1', 0, 'whoosh_reveal', 0.9); at('S1', 4, 'pop', 0.7, 0.2); at('S1', 40, 'whoosh_soft', 0.5, -0.4);
  const s1snap = L('S1', 'toilet seat'); at('S1', s1snap, 'snap_tick'); at('S1', s1snap, 'whoosh_soft', 0.6); at('S1', s1snap + 3, 'pop', 0.8, 0.4); at('S1', s1snap + 1, 'danger_sting', 0.6);
  // S2
  const tDirt = L('S2', 'dirtiest'), tTouch = L('S2', 'touch all day'), tWaste = L('S2', 'waste');
  at('S2', 6, 'pop', 0.6, 0.4); at('S2', tDirt, 'snap_tick'); at('S2', tDirt, 'pop', 0.6, -0.4); at('S2', tDirt + 4, 'stink', 0.6);
  at('S2', tTouch, 'tap', 0.8); at('S2', tTouch, 'pop', 0.6, -0.3); at('S2', tTouch + 14, 'pop', 0.5, -0.3);
  at('S2', tWaste, 'lid_rattle', 0.9); at('S2', tWaste, 'pop', 0.6, -0.4);
  // S3
  const tScrub = L('S3', 'scrubbed'), tDis = L('S3', 'disinfectant'), tEvery = L('S3', 'every day', 10.9), tPhone = L('S3', 'your phone almost'), tNever = L('S3', 'never');
  at('S3', 0, 'music_hit', 1);
  [8, tScrub - 4, tDis - 6, tDis + 22].forEach((t) => at('S3', t, 'spray_hiss', 0.8, -0.3));
  [tScrub - 16, tScrub + 14, tDis + 6, tDis + 30, tEvery - 18].forEach((t, i) => at('S3', t, 'pop', 0.8, -0.4 + i * 0.2));
  at('S3', tDis, 'snap_tick'); at('S3', tEvery, 'sparkle_chime', 0.9);
  at('S3', tPhone - 6, 'whoosh_soft', 0.6, 0.4); at('S3', tPhone + 2, 'clack', 0.6);
  at('S3', tNever, 'snap_tick'); at('S3', tNever + 2, 'laugh_boing', 0.9); at('S3', tNever + 26, 'laugh_boing', 0.6);
  // S4
  const tDoor = L('S4', 'door'), tHandle = L('S4', 'handle'), tDollar = L('S4', 'dollar'), tBill = L('S4', 'bill'), tSnack = L('S4', 'snack');
  const tTouch4 = L('S4', 'touch', 17.9), tEnds = L('S4', 'ends up'), tRight = L('S4', 'right on'), tScreen = L('S4', 'screen', 19);
  for (let t = 6; t < tEnds; t += 24) at('S4', t, 'step', 0.35, 0.1);
  [tDoor - 2, tDollar, tSnack].forEach((t) => at('S4', t, 'pop', 0.8, 0.3));
  [tDoor + 6, tDollar + 6, tSnack + 6].forEach((t) => at('S4', t, 'pop', 0.5, 0.4));
  [tHandle, tBill, tTouch4].forEach((t) => { at('S4', t, 'tap', 0.7); at('S4', t + 2, 'snap_tick', 0.6); });
  [tHandle + 4, tHandle + 10, tBill + 4, tBill + 10, tTouch4 + 4, tTouch4 + 10].forEach((t, i) => at('S4', t, 'boing', 0.6, (i % 2 ? 0.3 : -0.3)));
  at('S4', tEnds - 4, 'whoosh_soft', 0.5);
  at('S4', tRight, 'snap_tick'); at('S4', tScreen, 'snap_tick');
  at('S4', tRight - 2, 'tap', 0.9); at('S4', tScreen - 2, 'tap', 0.9);
  [tRight + 2, tRight + 6, tRight + 10, tScreen + 2, tScreen + 6, tScreen + 10].forEach((t, i) => at('S4', t, 'squeaky_jump', 0.5, i % 2 ? 0.25 : -0.25));
  // S5 (match cut + pull back reveal)
  const tStays = L('S5', 'stays warm'), tWarm = L('S5', 'warm'), tHelp = L('S5', 'help'), tGerms = L('S5', 'germs'), tSurv = L('S5', 'survive'), tLonger = L('S5', 'longer');
  at('S5', 0, 'whoosh_reveal', 0.7); at('S5', tStays, 'warm_swell', 0.8); at('S5', tWarm, 'pop', 0.6, 0.4);
  [tHelp, tGerms, tGerms + 8, tSurv, tSurv + 4, tSurv + 9, tLonger, tLonger + 3, tLonger + 7, tLonger + 10, tLonger + 14].forEach((t, i) => at('S5', t, 'pop', 0.65, ((i % 3) - 1) * 0.35));
  at('S5', tGerms, 'snap_tick');
  // S6
  const tBath = L('S6', 'bathroom'), tWhere = L('S6', 'where tiny'), tDrop = L('S6', 'tiny droplets'), tFloat = L('S6', 'float'), tLand = L('S6', 'land on it');
  for (let t = 4; t < tBath; t += 22) at('S6', t, 'step', 0.35, -0.1);
  at('S6', tBath + 14, 'clack', 0.7); at('S6', tWhere - 2, 'click', 0.8); at('S6', tWhere, 'flush', 1.0);
  at('S6', tDrop, 'bubbly_whoosh', 0.9); at('S6', tDrop + 16, 'pop', 0.5, -0.4);
  at('S6', tFloat, 'whoosh_soft', 0.5); at('S6', tLand, 'snap_tick'); at('S6', tLand + 4, 'patter', 0.8);
  // heartbeat_soft: from the droplets through the face smack (escalation), very low
  const hbStart = sceneStart('S6') + tDrop, hbEnd = sceneStart('S7') + L('S7', 'face', 33.4);
  for (let f = hbStart, k = 0; f < hbEnd; k++) { c.push({f, sfx: 'heartbeat_soft', gain: 0.55 + 0.35 * ((f - hbStart) / (hbEnd - hbStart))}); f += Math.round(60 * (0.95 - 0.35 * ((f - hbStart) / (hbEnd - hbStart)))); }
  // S7
  const tRight7 = L('S7', 'right against'), tFace = L('S7', 'face', 33.4);
  [4, 7, 10, 13, 16, 19, 22].forEach((t, i) => at('S7', t, 'pop', 0.4, ((i % 3) - 1) * 0.4));
  at('S7', tRight7 - 10, 'riser', 0.8); at('S7', tFace, 'squish', 1); at('S7', tFace, 'impact', 0.8);
  at('S7', tFace + 6, 'pop', 0.6); at('S7', tFace + 12, 'laugh_boing', 0.7);
  // S8
  const d8 = dur('S8');
  const tDirt8 = L('S8', 'dirtiest'), tOne = L('S8', 'one in your'), tAnd = L('S8', 'and a quick'), tWipe = L('S8', 'wipe'), tOnce = L('S8', 'once a day'), tRem = L('S8', 'removes'), tThem = L('S8', 'them'), tHand = L('S8', 'hand');
  at('S8', 0, 'music_hit', 1); at('S8', 4, 'sparkle_chime', 0.45); at('S8', tDirt8 - 6, 'whoosh_reveal', 0.7);
  at('S8', tOne, 'whoosh_soft', 0.5); at('S8', tOne + 4, 'pop', 0.7, 0.4); at('S8', tHand, 'pop', 0.6, -0.3);
  at('S8', tAnd, 'snap_tick'); at('S8', tAnd + 2, 'pop', 0.6, -0.3);
  at('S8', tWipe - 4, 'wipe_swish', 1); [0, 3, 6, 9, 12, 15].forEach((k, i) => at('S8', tWipe + k, 'boing', 0.4, 0.5 - i * 0.05));
  at('S8', tOnce - 4, 'sparkle_chime', 0.9); at('S8', tWipe + 12, 'ding', 0.9);
  at('S8', tRem, 'pop', 0.7, -0.3); at('S8', tThem - 8, 'whoosh_soft', 0.6); at('S8', tThem + 6, 'pop', 0.8);
  void TOTAL_FRAMES; void d8;
  return c.sort((a, b) => a.f - b.f);
}
