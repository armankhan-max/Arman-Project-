// Bundle once, render many stills: node stills.mjs out_dir f1 f2 ...
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'path';
const [outDir, ...frames] = process.argv.slice(2);
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const composition = await selectComposition({serveUrl, id: 'Main', browserExecutable});
for (const f of frames) {
  await renderStill({serveUrl, composition, frame: Number(f), output: `${outDir}/f${f}.jpg`, imageFormat: 'jpeg', browserExecutable, chromiumOptions: {gl: 'swangle'}});
}
console.log('done', frames.length);
