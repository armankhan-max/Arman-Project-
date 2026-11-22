import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H=1800,1013
def noise(h,w,sc,seed):
    r=np.random.default_rng(seed).random((max(2,h//sc),max(2,w//sc))).astype(np.float32)
    return np.asarray(Image.fromarray((r*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)).astype(np.float32)/255
def wood(h,w,seed,base=0.3):
    r=np.random.default_rng(seed)
    st=np.asarray(Image.fromarray((r.random((max(2,h//90),max(2,w//3)))*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)).astype(np.float32)/255
    fine=np.asarray(Image.fromarray((r.random((max(2,h//25),w))*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)).astype(np.float32)/255
    return np.clip(base+0.22*((st-.5)*.9+(fine-.5)*.35+noise(h,w,120,seed+3)*.25),0,1)
def toimg(a):
    if a.ndim==2: a=np.stack([a]*3,-1)
    return Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
def save(im,name): im.convert("RGB").save(f"dl/g_{name}.jpg",quality=95)
def light(im,cx,cy,r,amt=0.5):
    a=np.asarray(im).astype(np.float32)/255; yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]]
    g=np.exp(-(((xx-cx)**2+(yy-cy)**2)/(2*r*r)))
    return toimg(a*(0.45+amt*g[...,None]*1.2))
# ---- lard tin on cellar shelf
bg=wood(H,W,1,0.22); im=toimg(bg); d=ImageDraw.Draw(im)
d.rectangle((0,700,W,760),fill=(70,62,52)); d.rectangle((0,760,W,790),fill=(30,26,22))
x0,x1,y0,y1=640,1160,250,720
a=np.asarray(im).astype(np.float32)/255
xx=np.arange(W)[None,:].astype(np.float32); cyl=np.clip(1-((xx-(x0+x1)/2)/((x1-x0)/2))**2,0,1)**0.5
metal=(0.30+0.45*cyl+0.12*np.sin((xx-x0)/9)*0.15)*np.ones((H,1))
rust=noise(H,W,18,5)+0.5*noise(H,W,5,6)>1.05
tin=np.where(rust,0.22+0.08*noise(H,W,4,7),metal)
m=np.zeros((H,W),np.float32); m[y0:y1,x0:x1]=1
a=a*(1-m[...,None])+tin[...,None]*m[...,None]
im=toimg(a); d=ImageDraw.Draw(im)
for yy in (y0+18,y1-18): d.line((x0,yy,x1,yy),fill=(60,58,54),width=6)
d.ellipse((x0,y0-40,x1,y0+40),fill=(120,118,110),outline=(60,58,54),width=5)
d.arc((870,y0-140,930,y0-10),180,360,fill=(80,78,72),width=7)
lab=Image.new("RGBA",(360,170),(215,205,180,255)); dl=ImageDraw.Draw(lab)
f=ImageFont.truetype("../work/fonts/7fb78b.ttf",88); dl.text((180,62),"PURE LARD",font=f,fill=(40,34,28,255),anchor="mm")
dl.text((180,135),"50 LBS NET",font=ImageFont.truetype("../work/fonts/092e85.ttf",28),fill=(60,50,40,255),anchor="mm")
im.paste(lab,(720,420),lab)
d=ImageDraw.Draw(im)
for i in range(40): x=x0+i*13; d.line((x,y0+30,x+4,y0+42),fill=(200,190,170),width=3)  # wax drips
save(light(im,900,420,520),"tin")
# ---- chain link on blue flannel
fl=0.30+0.10*noise(H,W,3,9)+0.06*np.sin(np.arange(W)[None,:]/6)*np.cos(np.arange(H)[:,None]/6)
im=toimg(fl); d=ImageDraw.Draw(im)
cx,cy=900,520
for r,c,wd in ((0,(235,232,222),46),):
    d.rounded_rectangle((cx-330,cy-95,cx+330,cy+95),95,outline=(40,40,40),width=wd+12)
    d.rounded_rectangle((cx-330,cy-95,cx+330,cy+95),95,outline=c,width=wd)
d.rounded_rectangle((cx-322,cy-87,cx+322,cy+87),87,outline=(255,255,250),width=8)
im=im.filter(ImageFilter.GaussianBlur(1.2)); save(light(im,900,500,600,0.6),"link")
# ---- pencil sketch of long house
pg=np.clip(0.86+0.06*noise(H,W,60,11)+0.03*noise(H,W,2,12),0,1); im=toimg(pg); d=ImageDraw.Draw(im)
rng=np.random.default_rng(3)
def pl(pts,w=3):
    for i in range(len(pts)-1):
        for k in range(2):
            j=rng.normal(0,1.5,4); d.line((pts[i][0]+j[0],pts[i][1]+j[1],pts[i+1][0]+j[2],pts[i+1][1]+j[3]),fill=(60,60,64),width=w)
d.line((120,760,1680,740),fill=(110,110,115),width=2)  # hillside
pl([(330,750),(330,520),(1470,520),(1470,750)])
pl([(300,525),(900,250),(1500,525)])
pl([(380,520),(380,330),(440,330),(440,500)]); pl([(1360,500),(1360,330),(1420,330),(1420,520)])
pl([(830,750),(830,610),(970,610),(970,750)])
for s in range(5): pl([(780-s*25,750+s*14),(1020+s*25,750+s*14)],2)
pl([(1560,750),(1560,738)],2); d.ellipse((1556,728,1564,736),outline=(60,60,64),width=2)
for k in range(60):
    x=rng.uniform(340,1460); d.line((x,530,x-30,560),fill=(150,150,155),width=1)
f=ImageFont.truetype("../work/fonts/b8a6dc.ttf",90); d.text((900,880),"30",font=f,fill=(55,55,60),anchor="mm")
save(im,"sketch")
# ---- line in the ashes
ash=np.clip(0.42+0.18*noise(H,W,3,21)+0.12*noise(H,W,30,22)-0.15*noise(H,W,200,23),0,1)
emb=noise(H,W,6,24)>0.9; ash=np.where(emb,0.12,ash)
im=toimg(ash); d=ImageDraw.Draw(im)
for o,c in ((10,(40,38,36)),(0,(150,146,140))):
    d.line((300,540+o,1500,520+o),fill=c,width=30)
    for x,y in ((300,540),(1500,520)): d.line((x,y-70+o,x,y+70+o),fill=c,width=26)
im=im.filter(ImageFilter.GaussianBlur(2)); save(light(im,900,520,700,0.5),"ash")
# ---- tally sticks bundle
bg=wood(H,W,31,0.16); im=toimg(bg); d=ImageDraw.Draw(im)
for i in range(26):
    x=110+i*62+rng.normal(0,6); top=rng.uniform(-40,60); bot=H+40
    col=int(rng.uniform(140,190)); d.rectangle((x,top,x+40,bot),fill=(col,col-8,col-20))
    d.line((x,top,x,bot),fill=(60,55,50),width=3)
    y=top+40
    while y<bot:
        y+=rng.uniform(14,26); L=26 if rng.random()<0.8 else 40
        d.line((x+4,y,x+4+L,y+rng.normal(0,2)),fill=(50,44,38),width=4)
d.line((80,150,1720,170),fill=(120,110,90),width=14)
im=im.filter(ImageFilter.GaussianBlur(0.8)); save(light(im,900,450,700,0.55),"tally")
# ---- long table with bowls
def bowls(n,extra):
    tb=wood(W,H,41,0.30).T.copy()
    im=toimg(tb); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,150),fill=(20,18,16)); d.rectangle((0,880,W,H),fill=(20,18,16))
    xs=np.linspace(150,1650,n)
    for i,x in enumerate(xs):
        big = extra and i==n-1
        rx,ry=48,30
        y=520+(25 if i%2 else -25)
        d.ellipse((x-rx-6,y-ry+26,x+rx+6,y+ry+40),fill=(25,22,20))
        d.ellipse((x-rx,y-ry,x+rx,y+ry),fill=(190,185,172) if not big else (230,226,214),outline=(80,76,70),width=4)
        d.ellipse((x-rx+14,y-ry+8,x+rx-14,y+ry-6),fill=(130,126,118) if not big else (170,166,156))
    return light(im.filter(ImageFilter.GaussianBlur(1.0)),W-150 if extra else 900,520,500 if extra else 900,0.55)
save(bowls(11,False),"bowls11"); save(bowls(12,True),"bowls12")
print("ok")
