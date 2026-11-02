// Every scene / camera move / caption / SFX is anchored to a WORD from words.json.
import words from './words.json';
export const FPS = 60;
export type Word = {word: string; start: number; end: number};
export const WORDS = words as Word[];
const norm = (s: string) => s.toLowerCase().replace(/[^a-z']/g, '');
export const VO_DURATION = 39.816;
export const TOTAL_FRAMES = Math.round((VO_DURATION + 0.5) * FPS);
export const fr = (s: number) => Math.round(s * FPS);

/** index of first word of `phrase` occurring at/after `afterSec` */
export function idx(phrase: string, afterSec = 0): number {
  const p = phrase.split(/\s+/).map(norm);
  for (let i = 0; i < WORDS.length; i++) {
    if (WORDS[i].start < afterSec - 1e-6) continue;
    if (p.every((w, k) => WORDS[i + k] && norm(WORDS[i + k].word) === w)) return i;
  }
  throw new Error('anchor not found: ' + phrase);
}
/** global frame of the start of a phrase */
export const W = (phrase: string, afterSec = 0) => fr(WORDS[idx(phrase, afterSec)].start);
/** global frame of the end of a phrase */
export const WE = (phrase: string, afterSec = 0) => {
  const p = phrase.split(/\s+/).length;
  return fr(WORDS[idx(phrase, afterSec) + p - 1].end);
};

// ---- scene boundaries (global frames), each anchored on its scene-plan phrase
const s2 = W("you'd think the toilet");
const s3 = W('but toilet seats get scrubbed');
const s4 = W('so every door handle');
const s5 = W('and your phone stays warm');
const s6 = W('then you carry it into the bathroom');
const s7 = W('and then you press that same screen');
const s8 = W('so the dirtiest thing');
export const SCENES = [
  {id: 'S1', from: 0, to: s2},
  {id: 'S2', from: s2, to: s3},
  {id: 'S3', from: s3, to: s4},
  {id: 'S4', from: s4, to: s5},
  {id: 'S5', from: s5, to: s6},
  {id: 'S6', from: s6, to: s7},
  {id: 'S7', from: s7, to: s8},
  {id: 'S8', from: s8, to: TOTAL_FRAMES},
] as const;
export type SceneId = (typeof SCENES)[number]['id'];
export const sceneStart = (id: SceneId) => SCENES.find((s) => s.id === id)!.from;
/** local (scene-relative) frame of a phrase */
export const L = (id: SceneId, phrase: string, afterSec?: number) => W(phrase, afterSec ?? sceneStart(id) / FPS - 0.05) - sceneStart(id);
