import json, numpy as np, subprocess, wave
U='/root/.claude/uploads/95b30f93-c970-520b-a345-3c13f7b431e6/78f5b23e-merged_natural.mp3'
SR=44100
subprocess.run(['ffmpeg','-v','error','-y','-i',U,'-ac','1','-ar',str(SR),'orig.wav'],check=True)
w=wave.open('orig.wav');a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
segs=json.load(open('transcript.json'))
rms=np.sqrt(np.mean(a[np.abs(a)>0.02]**2))
rng=np.random.default_rng(7)
def breath(dur):
    n=int(dur*SR); x=rng.standard_normal(n+4000)
    # pinkish + band shaping via FFT
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR)
    shape=np.exp(-((np.log(f+1)-np.log(1100))**2)/(2*0.55**2)); X*=shape/np.sqrt(f+30)
    y=np.fft.irfft(X)[2000:2000+n]; y/=np.abs(y).max()+1e-9
    t=np.linspace(0,1,n); env=np.sin(np.pi*np.clip(t*1.15,0,1))**1.6
    return y*env*rms*0.16
inserts=[]  # (old_time, added_seconds)
out=[];last=0;k=0
for s,nx in zip(segs,segs[1:]):
    txt=s['text'].strip(); gap=nx['start']-s['end']
    cut=(s['end']+nx['start'])/2 if gap>0 else s['end']
    if txt[-1:] in '.?!':
        k+=1; withb = (k%2==1) or gap<0.3
        pause = 0.22 if gap<0.6 else 0.10
        ins=np.zeros(int(pause*SR),np.float32)
        if withb:
            b=breath(0.38); ins=np.concatenate([ins,b,np.zeros(int(0.06*SR),np.float32)])
    elif txt[-1:] in ',;' and gap<0.35:
        ins=np.zeros(int(0.10*SR),np.float32)
    else: continue
    ci=int(cut*SR); out.append(a[last:ci]); out.append(ins); last=ci
    inserts.append((cut,len(ins)/SR))
out.append(a[last:]); y=np.concatenate(out)
w2=wave.open('paused.wav','wb');w2.setnchannels(1);w2.setsampwidth(2);w2.setframerate(SR)
w2.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes());w2.close()
json.dump(inserts,open('inserts.json','w'))
print('inserted',sum(d for _,d in inserts),len(inserts))
