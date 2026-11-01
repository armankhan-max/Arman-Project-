// Word-level timing from the voiceover transcript. Every cut, pop and SFX is keyed to a spoken word.
const path = require('path');
const segs = require(path.join(__dirname, '..', 'transcript.json'));
const words = [];
for (const s of segs) for (const w of s.words) words.push({ w: w.w.trim(), s: w.s, e: w.e });
// transcription fixes (index -> text); null hides the word from captions
const FIX = { 37: 'Four', 261: 'Applause.', 444: 'whose.', 468: 'too.', 657: '5:30.', 823: 'Whose?', 824: 'Yours.', 941: null };
// merge split tokens like "6" + ".10" or "o" + "'clock."
for (let i = 1; i < words.length; i++) { const w = words[i]; if (/^[.'][0-9a-z]/i.test(w.w) && words[i - 1].w) { const p = words[i - 1]; p.w = (/^\d+$/.test(p.w) && w.w[0] === '.' && p.s < 1) ? p.w + ':' + w.w.slice(1) : p.w + w.w; p.e = w.e; w.w = null; } }
for (let i = 1; i < words.length - 1; i++) { if (/^\d+$/.test(words[i].w || '') && /^o'clock/.test(words[i + 1].w || '')) { const p = words[i - 1]; if (p.w && !/[.?!,]$/.test(p.w)) p.w += '.'; } }
words.forEach((w, i) => { if (i in FIX) w.w = FIX[i]; if (w.w === null) { w.n = ''; return; } w.n = (w.w || '').toLowerCase().replace(/[^a-z0-9']/g, ''); if (w.n === 'dev') w.w = w.w.replace('dev', 'Dev'); });
const END = 372.0;

// at('crow lands', 0) -> start time of that word sequence (first match after `after`)
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

// caption chunks: break on sentence ends, long pauses, or 6 words
const chunks = [];
{
  let cur = [];
  const flush = () => { if (cur.length) chunks.push({ s: cur[0].s, e: cur[cur.length - 1].e, words: cur }); cur = []; };
  words.forEach((w, i) => {
    if (w.w === null) return;
    const prev = cur[cur.length - 1];
    if (prev && (w.s - prev.e > .45 || cur.length >= 6)) flush();
    cur.push(w);
    if (/[.?!]$/.test(w.w) && cur.length >= 2) flush();
  });
  flush();
  for (let i = 0; i < chunks.length; i++) { const nx = chunks[i + 1]; chunks[i].hold = nx ? Math.min(nx.s, chunks[i].e + .6) : chunks[i].e + .8; }
}
module.exports = { words, at, end, chunks, END };
