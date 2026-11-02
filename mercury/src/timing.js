// Word-level timing from the voiceover transcript. Every cut, pop and SFX is keyed to a spoken word.
const path = require('path');
const segs = require(path.join(__dirname, '..', 'transcript.json'));
const words = [];
for (const s of segs) for (const w of s.words) words.push({ w: w.w.trim(), s: w.s, e: w.e });
const FIX = { 130: 'and', 931: 'MESSENGER', 1103: 'MESSENGER' };
words.forEach((w, i) => { if (i in FIX) w.w = FIX[i]; w.n = (w.w || '').toLowerCase().replace(/[^a-z0-9']/g, ''); });
const END = 441.5;

// at('melt lead', after) -> start time of that phrase (first match after `after`)
function at(phrase, after = 0, which = 's') {
  const p = phrase.toLowerCase().split(/\s+/).map(x => x.replace(/[^a-z0-9']/g, ''));
  for (let i = 0; i < words.length; i++) {
    if (words[i].s < after) continue;
    let ok = true; for (let k = 0; k < p.length; k++) if (!words[i + k] || words[i + k].n !== p[k]) { ok = false; break; }
    if (ok) return which === 's' ? words[i].s : words[i + p.length - 1].e;
  }
  throw new Error('phrase not found: ' + phrase + ' after ' + after);
}
const end = (phrase, after = 0) => at(phrase, after, 'e');

const chunks = [];
{
  let cur = [];
  const flush = () => { if (cur.length) chunks.push({ s: cur[0].s, e: cur[cur.length - 1].e, words: cur }); cur = []; };
  words.forEach(w => {
    const prev = cur[cur.length - 1];
    if (prev && (w.s - prev.e > .45 || cur.length >= 6)) flush();
    cur.push(w);
    if (/[.?!]$/.test(w.w) && cur.length >= 2) flush();
  });
  flush();
  for (let i = 0; i < chunks.length; i++) { const nx = chunks[i + 1]; chunks[i].hold = nx ? Math.min(nx.s, chunks[i].e + .6) : chunks[i].e + .8; }
}
module.exports = { words, at, end, chunks, END };
