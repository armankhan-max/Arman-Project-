// node stills.js outdir t1 t2 ...   -> renders jpgs (and logs errors)
const {chromium}=require('playwright'); const fs=require('fs');
(async()=>{const [out,...ts]=process.argv.slice(2); fs.mkdirSync(out,{recursive:true});
const b=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await b.newPage({viewport:{width:1280,height:720}});
p.on('console',m=>{if(m.type()==='error')console.log('c:',m.text().slice(0,400))}); p.on('pageerror',e=>console.log('ERR',e.message, e.stack?.slice(0,600)));
await p.goto('http://127.0.0.1:8765/web/index.html'); await p.waitForFunction('window.ready',null,{timeout:180000});
for(const t of ts){const t0=Date.now(); try{ await p.evaluate(`window.frame(${t})`); const d=await p.evaluate('window.grab(.9)');
 fs.writeFileSync(`${out}/f_${(+t).toFixed(2).padStart(7,'0')}.jpg`,Buffer.from(d.split(',')[1],'base64')); console.log(t,'ms',Date.now()-t0);}catch(e){console.log('fail',t,e.message.slice(0,500));}}
await b.close();})();
