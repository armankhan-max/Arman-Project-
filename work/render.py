import subprocess, os
from concurrent.futures import ThreadPoolExecutor
exec(open('timeline.py').read())
U='/root/.claude/uploads/95b30f93-c970-520b-a345-3c13f7b431e6/'
os.makedirs('seg',exist_ok=True)
FPS=30
jobs=[]
ends=[x[0] for x in TL[1:]]+[END]
ai=0
for k,((st,kind,src),en) in enumerate(zip(TL,ends)):
    n=round(en*FPS)-round(st*FPS); d=n/FPS
    out=f'seg/{k:03d}.mp4'
    enc=['-frames:v',str(n),'-r','30','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',out]
    if kind=='i':
        m=k%4
        Z=f"min(1+0.12*on/{n},1.12)" if m in(0,2) else f"max(1.12-0.12*on/{n},1.0)"
        if m==0: x,y="iw/2-(iw/zoom/2)","ih/2-(ih/zoom/2)"
        elif m==1: x,y="iw/2-(iw/zoom/2)","ih/2-(ih/zoom/2)"
        elif m==2: x,y="(iw-iw/zoom)*0.2","(ih-ih/zoom)*0.4"
        else: x,y="(iw-iw/zoom)*0.8","(ih-ih/zoom)*0.5"
        vf=f"scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,zoompan=z='{Z}':x='{x}':y='{y}':d={n}:s=1920x1080:fps=30,eq=contrast=1.04:saturation=1.05"
        cmd=['ffmpeg','-v','error','-y','-loop','1','-framerate','30','-i',U+src+'-image.jpg','-vf',vf]+enc
    elif kind=='s':
        sid,ss=src.split(':')
        vf="fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1"
        cmd=['ffmpeg','-v','error','-y','-stream_loop','-1','-ss',ss,'-i',f'stock/{sid}.mp4','-vf',vf]+enc
    else:
        punch = ai%2==1; ai+=1
        crop = "crop=544:306:48:10," if punch else ""
        vf=f"{crop}scale=1920:1080:flags=lanczos,unsharp=5:5:0.8,setsar=1"
        cmd=['ffmpeg','-v','error','-y','-ss',f'{round(st*FPS)/FPS:.4f}','-i','avatar_track.mp4','-vf',vf]+enc
    jobs.append(cmd)
def run(c):
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode: print('ERR',c[-1],r.stderr[-300:])
with ThreadPoolExecutor(4) as ex: list(ex.map(run,jobs))
with open('seg/list.txt','w') as f:
    for k in range(len(TL)): f.write(f"file '{k:03d}.mp4'\n")
print('ok')
