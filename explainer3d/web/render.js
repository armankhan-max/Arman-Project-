// node render.js out.mp4 [jobs] [start] [end] -- renders frames in parallel workers, each piping JPEGs to ffmpeg
const {chromium}=require('playwright'); const {spawn}=require('child_process'); const fs=require('fs'); const path=require('path');
const FPS=30;
async function worker(id, f0, f1, out){
  const b=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  const p=await b.newPage({viewport:{width:1600,height:900}});
  p.on('pageerror',e=>console.log(`[w${id}] ERR`,e.message));
  await p.goto('http://127.0.0.1:8765/web/index.html'); await p.waitForFunction('window.ready',null,{timeout:180000});
  const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r',String(FPS),out],{stdio:['pipe','inherit','inherit']});
  const t0=Date.now();
  for(let f=f0;f<f1;f++){
    const d=await p.evaluate(`(window.frame(${(f/FPS).toFixed(5)}), window.grab(.94))`);
    const buf=Buffer.from(d.slice(d.indexOf(',')+1),'base64');
    if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));
    if((f-f0)%150===0) console.log(`[w${id}] frame ${f}/${f1} ${((Date.now()-t0)/Math.max(1,f-f0)).toFixed(0)}ms/f`);
  }
  ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await b.close();
}
(async()=>{
  const [out, jobsS='4', s0, s1]=process.argv.slice(2); const jobs=+jobsS;
  const dur=251.0; const F0=Math.round((+s0||0)*FPS), F1=Math.round((s1?+s1:dur)*FPS);
  const dir=out.replace(/\.mp4$/,'_parts'); fs.mkdirSync(dir,{recursive:true});
  const n=F1-F0, per=Math.ceil(n/jobs); const parts=[];
  await Promise.all([...Array(jobs)].map((_,i)=>{const a=F0+i*per,b=Math.min(F1,a+per); const o=path.join(dir,`p${i}.mp4`); parts.push(o); return a<b?worker(i,a,b,o):null;}));
  fs.writeFileSync(path.join(dir,'list.txt'),parts.filter(f=>fs.existsSync(f)).map(f=>`file '${path.resolve(f)}'`).join('\n'));
  await new Promise(r=>spawn('ffmpeg',['-y','-loglevel','error','-f','concat','-safe','0','-i',path.join(dir,'list.txt'),'-c','copy',out],{stdio:'inherit'}).on('close',r));
  console.log('done',out);
})();
