// usage: node render.js <outDir> <startFrame> <endFrame> [step]   (renders frames of the 3D scene with headless Chromium)
const http=require('http'),fs=require('fs'),path=require('path');
const {chromium}=require('playwright');
const THREE=process.env.THREE_DIR||'/tmp/w/node_modules/three';
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json'};
function serve(port){return new Promise(r=>{const s=http.createServer((q,res)=>{let u=decodeURIComponent(q.url.split('?')[0]);let f=u.startsWith('/three/')?path.join(THREE,u.slice(7)):path.join(__dirname,u==='/'?'index.html':u);
 fs.readFile(f,(e,d)=>{if(e){res.writeHead(404);res.end();return}res.writeHead(200,{'content-type':mime[path.extname(f)]||'application/octet-stream'});res.end(d)})});s.listen(port,()=>r(s))})}
(async()=>{
 const [out,a,b,step]=[process.argv[2],+process.argv[3],+process.argv[4],+(process.argv[5]||1)];
 fs.mkdirSync(out,{recursive:true});
 const port=20000+Math.floor(Math.random()*20000);const srv=await serve(port);
 const br=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--no-sandbox']});
 const pg=await br.newPage({viewport:{width:720,height:1280}});
 pg.on('console',m=>{if(m.type()==='error')console.log('ERR',m.text())});pg.on('pageerror',e=>console.log('PAGEERR',e.message));
 await pg.goto(`http://localhost:${port}/`);await pg.waitForFunction('window.ready===true',null,{timeout:120000});
 const fps=30;const t0=Date.now();
 const list=process.env.FRAMES?process.env.FRAMES.split(',').map(Number):null;const seq=list||Array.from({length:Math.ceil((b-a)/step)},(_,i)=>a+i*step);
 for(const f of seq){await pg.evaluate(t=>window.setFrame(t),f/fps);
  await pg.screenshot({path:path.join(out,String(f).padStart(5,'0')+'.jpg'),type:'jpeg',quality:93});
  if((f-a)%30===0)console.log('frame',f,((Date.now()-t0)/1000).toFixed(0)+'s');}
 console.log('tcut',await pg.evaluate('window.__tcut'));
 await br.close();srv.close();
})();
