import os,sys,glob,numpy as np
from PIL import Image,ImageFilter
from concurrent.futures import ProcessPoolExecutor
U="/root/.claude/uploads/30c4e146-8864-5bf9-8426-9f627abc5b68/"
skip={"a3e33817","44976479","18f8d608","933982f7","15a89c88","f9e93369","4829d8bf","9d5ea671","1acf3b9e","5fb3404c","8aef6b96","9681a104"}
files=[f for f in glob.glob(U+"*-image.jpg") if os.path.basename(f)[:8] not in skip]
W,H=1600,900
def proc(f):
    k=os.path.basename(f)[:8]; rng=np.random.default_rng(int(k,16)%2**32)
    im=Image.open(f).convert("RGB"); w,h=im.size
    c=0.035; im=im.crop((int(w*c),int(h*c),int(w*(1-c)),int(h*(1-c))))
    # fit 16:9
    w,h=im.size; t=16/9
    if w/h>t: nw=int(h*t); im=im.crop(((w-nw)//2,0,(w-nw)//2+nw,h))
    else: nh=int(w/t); im=im.crop((0,(h-nh)//2,w,(h-nh)//2+nh))
    # kill AI detail: downsample hard then upsample soft
    im=im.resize((620,349),Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6)).resize((W,H),Image.BICUBIC)
    a=np.asarray(im).astype(np.float32)/255
    L=a[...,0]*.30+a[...,1]*.59+a[...,2]*.11
    # tone: flatten contrast, lift blacks, roll off highlights
    L=np.clip(L,0,1); L=L**0.92
    L=0.5+(L-0.5)*0.82
    L=0.07+L*0.83
    # big soft halation of highlights
    hl=Image.fromarray((np.clip(L-0.6,0,1)*255/0.4).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))
    L=L+np.asarray(hl).astype(np.float32)/255*0.10
    # uneven exposure / print fading
    yy,xx=np.mgrid[0:H,0:W]/np.array([H,W])[:,None,None]
    gx,gy=rng.uniform(0.2,0.8),rng.uniform(0.2,0.8)
    fade=0.06*np.exp(-(((xx-gx)**2)/0.15+((yy-gy)**2)/0.15))
    L=L+fade
    vig=1-0.38*(((xx-.5)**2*1.1+(yy-.5)**2*1.6)*2.4)
    L=L*np.clip(vig,0.45,1)
    # baked static grain (clumpy)
    g=rng.normal(0,1,(H//2,W//2)).astype(np.float32)
    g=np.asarray(Image.fromarray(((g*40)+128).clip(0,255).astype(np.uint8)).resize((W,H),Image.BICUBIC)).astype(np.float32)/255-0.5
    L=L+g*0.10
    # dust specks & hairline scratches
    for _ in range(rng.integers(25,60)):
        x,y=rng.integers(0,W),rng.integers(0,H); r=rng.integers(1,3); v=rng.choice([-0.35,0.3])
        L[max(0,y-r):y+r,max(0,x-r):x+r]+=v
    for _ in range(rng.integers(0,3)):
        x=rng.integers(0,W); L[:,x:x+1]+=rng.uniform(-0.08,0.1)
    L=np.clip(L,0,1)
    # tint: cool-neutral silver to warm sepia
    s=rng.choice([0.0,0.25,0.5,0.8],p=[.3,.3,.25,.15])
    r=L*(1+0.10*s); gch=L*(1+0.03*s); b=L*(1-0.12*s)
    out=np.stack([r,gch,b],-1).clip(0,1)
    Image.fromarray((out*255).astype(np.uint8)).save(f"img/{k}.jpg",quality=90)
    return k
with ProcessPoolExecutor(3) as ex: print(len(list(ex.map(proc,files))))
