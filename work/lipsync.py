import numpy as np, wave, subprocess, glob
from PIL import Image
fr=[np.array(Image.open(f).convert('RGB')) for f in sorted(glob.glob('av/f*.png'))]
N=len(fr)
o=np.array([ (f[185:240,260:370].mean(axis=2)<70).mean() for f in fr])
o=(o-o.min())/(o.max()-o.min()+1e-9)
print('openness range',np.percentile(o,[5,50,95]))
w=wave.open('vo16.wav');a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
sr=16000;fps=30;hop=sr//fps;T=len(a)//hop
env=np.array([np.sqrt((a[i*hop:(i+1)*hop]**2).mean()) for i in range(T)])
env=np.convolve(env,[0.25,0.5,0.25],'same')
lo,hi=np.percentile(env,[20,97]);tgt=np.clip((env-lo)/(hi-lo),0,1)
tgt[env<lo*1.2]=0
prev=0;play=0.0;d=1;out=[]
for t in range(T):
    play+=d
    if play>=N-1:d=-1
    if play<=0:d=1
    best=None
    for j in range(max(0,prev-4),min(N,prev+5)):
        c=abs(o[j]-tgt[t])+0.03*abs(j-play)/8
        if best is None or c<best[0]:best=(c,j)
    prev=best[1];out.append(prev)
p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','640x360','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','16','-pix_fmt','yuv420p','avatar_track.mp4'],stdin=subprocess.PIPE)
for j in out:p.stdin.write(fr[j].tobytes())
p.stdin.close();p.wait();print('done',T)
