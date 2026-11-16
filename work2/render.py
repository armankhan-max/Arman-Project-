import subprocess, os, math
from concurrent.futures import ThreadPoolExecutor
exec(open('tl.py').read())
U='/root/.claude/uploads/95b30f93-c970-520b-a345-3c13f7b431e6/'
S='/home/user/Arman-Project-/work/stock/'
END=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0','vo_final.wav']))
os.makedirs('seg',exist_ok=True)
FPS=30; jobs=[]
st=[round(M(t)*FPS) for t,_ in TL]; st[0]=0; st.append(round(END*FPS))
for k,(t,src) in enumerate(TL):
    n=st[k+1]-st[k]; out=f'seg/{k:03d}.mp4'
    enc=['-frames:v',str(n),'-r','30','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',out]
    if src.startswith('s:'):
        _,sid,ss=src.split(':')
        vf="fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,eq=saturation=0.92"
        cmd=['ffmpeg','-v','error','-y','-stream_loop','-1','-ss',ss,'-i',S+sid+'.mp4','-vf',vf]+enc
    else:
        m=k%4; z0,z1=((1.0,1.14) if m in(0,2) else (1.14,1.0))
        Z=f"{z0}+({z1-z0})*on/{n}"
        fx=[0.5,0.5,0.35,0.65][m]; fy=[0.45,0.5,0.45,0.5][m]
        x=f"(iw-iw/zoom)*{fx}+8*sin(on/37)"; y=f"(ih-ih/zoom)*{fy}+6*sin(on/53+1)"
        vf=f"scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,zoompan=z='{Z}':x='{x}':y='{y}':d={n}:s=1920x1080:fps=30"
        cmd=['ffmpeg','-v','error','-y','-loop','1','-framerate','30','-i',U+src+'-image.jpg','-vf',vf]+enc
    jobs.append(cmd)
def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print('ERR',c[-1],r.stderr[-300:])
with ThreadPoolExecutor(4) as ex: list(ex.map(run,jobs))
open('seg/list.txt','w').write(''.join(f"file '{k:03d}.mp4'\n" for k in range(len(TL))))
print('ok',len(TL),END)
