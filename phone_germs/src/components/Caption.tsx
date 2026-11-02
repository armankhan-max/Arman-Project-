import React from 'react';
import {WORDS, fr} from '../timeline';
import {clamp, easeOutCubic} from '../lib/ease';

type Group = {words: {text: string; key: boolean}[]; start: number; end: number};
const norm = (s: string) => s.toLowerCase().replace(/[^a-z']/g, '');
const KEY1 = new Set(['dirtiest', 'germs', 'face', 'hand']);

export function buildGroups(): Group[] {
  const keyIdx = new Set<number>();
  WORDS.forEach((w, i) => {
    const n = norm(w.word);
    if (KEY1.has(n)) keyIdx.add(i);
    if (n === 'toilet' && WORDS[i + 1] && /^seats?$/.test(norm(WORDS[i + 1].word))) { keyIdx.add(i); keyIdx.add(i + 1); }
  });
  const groups: Group[] = [];
  let cur: number[] = [];
  const flush = () => { if (cur.length) groups.push({words: cur.map((i) => ({text: WORDS[i].word.replace(/[.,]$/, '').toUpperCase(), key: keyIdx.has(i)})), start: fr(WORDS[cur[0]].start), end: 0}); cur = []; };
  WORDS.forEach((w, i) => {
    const prev = WORDS[i - 1];
    const len = cur.reduce((a, k) => a + WORDS[k].word.length + 1, 0);
    const keepPair = prev && keyIdx.has(i - 1) && keyIdx.has(i) && norm(prev.word) === 'toilet';
    if (cur.length && !keepPair && (cur.length >= 3 || /[.,?!]$/.test(prev.word) || w.start - prev.end > 0.28 || len + w.word.length > 15)) flush();
    cur.push(i);
  });
  flush();
  groups.forEach((g, i) => {
    g.end = i + 1 < groups.length ? groups[i + 1].start : fr(WORDS[WORDS.length - 1].end + 0.45);
  });
  return groups;
}
const GROUPS = buildGroups();

export const Captions: React.FC<{g: number}> = ({g}) => {
  const grp = GROUPS.find((x) => g >= x.start && g < x.end);
  if (!grp) return null;
  const t = g - grp.start;
  const k = easeOutCubic(clamp(t / 5));
  const sc = 1.15 - 0.15 * k;
  return (
    <g transform={`translate(540 ${1920 * 0.72}) scale(${sc})`} opacity={clamp(t / 2 + 0.4)}>
      <text x={4} y={10} textAnchor="middle" dominantBaseline="middle" fontFamily="Baloo2" fontWeight={800} fontSize={86} fill="#000" opacity={0.35} stroke="#000" strokeWidth={20} strokeLinejoin="round" style={{filter: 'blur(6px)'}}>
        {grp.words.map((w) => w.text).join(' ')}
      </text>
      <text x={0} y={0} textAnchor="middle" dominantBaseline="middle" fontFamily="Baloo2" fontWeight={800} fontSize={86}
        stroke="#111" strokeWidth={20} strokeLinejoin="round" paintOrder="stroke" letterSpacing={1}>
        {grp.words.map((w, i) => (
          <tspan key={i} fill={w.key ? '#FFD84A' : '#FFFFFF'}>{(i ? ' ' : '') + w.text}</tspan>
        ))}
      </text>
    </g>
  );
};
