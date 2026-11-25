// usage: node snap.js outdir t1 t2 ...   (seconds) -> outdir/f_<t>.jpg
const {chromium}=require('playwright');(async()=>{
const b=await chromium.launch({headless:false,args:['--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist','--enable-gpu','--window-size=1920,1080']});
const p=await b.newPage({viewport:{width:1920,height:1080}});
p.on('console',m=>console.log('console:',m.text()));p.on('pageerror',e=>console.log('PAGEERROR',e.message));
await p.goto('http://localhost:8765/index.html');await p.waitForFunction('window.ready',null,{timeout:300000});
const out=process.argv[2];
for(const ts of process.argv.slice(3)){const f=Math.round(parseFloat(ts)*30);const t0=Date.now();
await p.evaluate(f=>window.renderFrame(f),f);await p.screenshot({path:`${out}/f_${ts}.jpg`,type:'jpeg',quality:90});console.log(ts,Date.now()-t0,'ms');}
await b.close();})();
