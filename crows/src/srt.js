// Export YouTube subtitles (captions_en.srt) from the corrected word timings.
const fs = require('fs'), path = require('path');
const { chunks } = require('./timing');
const ts = s => { const ms = Math.round(s * 1000); const h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, se = Math.floor(ms / 1000) % 60; return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(se).padStart(2, '0')},${String(ms % 1000).padStart(3, '0')}`; };
const out = chunks.map((c, i) => `${i + 1}\n${ts(c.s)} --> ${ts(c.hold)}\n${c.words.map(w => w.w).join(' ')}\n`).join('\n');
fs.writeFileSync(path.join(__dirname, '..', 'captions_en.srt'), out); console.log('wrote captions_en.srt', chunks.length);
