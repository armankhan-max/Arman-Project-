import {buildCues} from './src/cues';
import {SCENES, TOTAL_FRAMES, FPS} from './src/timeline';
import {writeFileSync} from 'fs';
writeFileSync('assets/cues.json', JSON.stringify({fps: FPS, total: TOTAL_FRAMES, scenes: SCENES, cues: buildCues()}, null, 1));
console.log('cues', buildCues().length);
