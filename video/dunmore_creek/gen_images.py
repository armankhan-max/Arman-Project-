import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H=1800,1013
F="../work/fonts/"; PLAY=F+"b8a6dc.ttf"; TYPE=F+"c33104.ttf"
rng=np.random.default_rng(5)
def noise(h,w,sc,seed):
    r=np.random.default_rng(seed).random((max(2,h//sc),max(2,w//sc))).astype(np.float32)
    return np.asarray(Image.fromarray((r*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)).astype(np.float32)/255
def wood(h,w,seed,base=0.45,light=False):
    r=np.random.default_rng(seed)
    a=r.random((max(2,h//90),max(2,w//3))).astype(np.float32)
    st=np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)).astype(np.float32)/255
    b=r.random((max(2,h//25),max(2,w//1))).astype(np.float32)
    fine=np.asarray(Image.fromarray((b*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)).astype(np.float32)/255
    g=(st-0.5)*0.9+(fine-0.5)*0.35+noise(h,w,120,seed+3)*0.25
    v=base+0.22*g+(0.14 if light else 0)
    return np.clip(v,0,1)
def floor():
    img=np.zeros((H,W),np.float32); pw=W//7
    for i in range(7):
        x0=i*pw; light=(i==4)
        img[:,x0:x0+pw]=wood(H,pw,10+i,0.30+0.06*rng.random(),light)
        img[:,x0:x0+3]=0.05
        for y in [int(H*0.12),int(H*0.86)]:
            for dx in [pw*0.3,pw*0.7]:
                cx=int(x0+dx); img[y-5:y+5,cx-5:cx+5]=0.08 if not light else 0.55
    img=img*(0.75+0.35*noise(H,W,300,99))
    img+=np.clip(noise(H,W,2,7)-0.93,0,1)*2  # dust
    return np.clip(img,0,1)
def save(a,name):
    if a.ndim==2: a=np.stack([a]*3,-1)
    Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).save(f"raw/{name}-image.jpg",quality=95)
fl=floor(); save(fl,"a0000001")
# ---- tin box
bg=fl*0.55
im=Image.fromarray((np.stack([bg]*3,-1)*255).astype(np.uint8)).convert("RGB"); d=ImageDraw.Draw(im)
# oilcloth
cloth=Image.new("L",(W,H),0); dc=ImageDraw.Draw(cloth)
dc.polygon([(330,170),(1480,140),(1530,860),(300,890)],fill=255)
cl=np.asarray(cloth.filter(ImageFilter.GaussianBlur(6))).astype(np.float32)/255
tx=0.22+0.12*noise(H,W,40,3)+0.05*noise(H,W,3,4)
a=np.asarray(im).astype(np.float32)/255
a=a*(1-cl[...,None])+tx[...,None]*cl[...,None]
# tin
x0,y0,x1,y1=470,250,1340,770
m=Image.new("L",(W,H),0); ImageDraw.Draw(m).rounded_rectangle((x0,y0,x1,y1),40,fill=255)
mm=np.asarray(m).astype(np.float32)/255
yy,xx=np.mgrid[0:H,0:W]
metal=0.55+0.25*np.sin((xx+yy*0.6)/180)+0.08*noise(H,W,2,8)
paint=(noise(H,W,25,9)+0.4*noise(H,W,6,10))>0.78
tin=np.where(paint,0.30+0.1*noise(H,W,5,11),metal*0.85)
rim=np.zeros((H,W),bool); rim[y0:y1,x0:x1]=True; rim[y0+28:y1-28,x0+28:x1-28]=False
tin=np.where(rim,metal*0.95,tin)
a=a*(1-mm[...,None])+tin[...,None]*mm[...,None]
im=Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)); d=ImageDraw.Draw(im)
# string
for s in [(905,y0-60,905,y1+60),(x0-80,520,x1+80,520)]: d.line(s,fill=(200,195,180),width=7)
d.ellipse((890,505,920,535),fill=(190,185,170))
# label
lab=Image.new("RGBA",(520,170),(232,222,196,255)); dl=ImageDraw.Draw(lab)
f=ImageFont.truetype(PLAY,34)
dl.text((24,30),"For Walter, when I am gone,",font=f,fill=(30,25,20,255))
dl.text((24,88),"if you are the sort who asks.",font=f,fill=(30,25,20,255))
lab=lab.rotate(-2.5,expand=True,resample=Image.BICUBIC)
im.paste(lab,(560,300),lab)
save(np.asarray(im).astype(np.float32)/255,"a0000002")
# ---- letter
pg=Image.new("RGB",(1300,1650),(230,222,200)); d=ImageDraw.Draw(pg)
for y in range(170,1650,62): d.line((0,y,1300,y),fill=(150,160,175),width=2)
d.line((140,0,140,1650),fill=(170,90,90),width=3)
for y in [550,1100]: d.line((0,y,1300,y),fill=(185,175,150),width=4)
f=ImageFont.truetype(PLAY,40)
lines=["Dunmore Creek, October the 4th, 1908.","Fair and dry. My health poor. Corn is in.","I am sixty-nine years old and do not","expect to see another spring. The sheriff","and the doctor are both dead. Martha is","deaf now and will not be troubled by this.","I am not a man who tells things, but I","find I cannot take this one with me.","I have thought many times of burning","this letter and have not been able to.","You are going to read that the doctor","saw a braid. It is true. But the doctor","did not see what was under it.","","                               A. R."]
y=118
for ln in lines:
    d.text((175,y),ln,font=f,fill=(70,70,75)); y+=62*1.6 if False else 62*1.0+38
pga=np.asarray(pg).astype(np.float32)/255
pga*= (0.85+0.2*noise(1650,1300,80,21))[...,None]
pg=Image.fromarray((np.clip(pga,0,1)*255).astype(np.uint8)).rotate(4,expand=True,resample=Image.BICUBIC,fillcolor=(0,0,0))
tb=np.stack([wood(H,W,40,0.22)]*3,-1)
tbi=Image.fromarray((tb*255).astype(np.uint8))
pm=Image.new("L",pg.size,0); ImageDraw.Draw(pm).rectangle((0,0)+pg.size,fill=255); pm=pm.rotate(0)
pg=pg.resize((int(pg.size[0]*0.62),int(pg.size[1]*0.62)))
mask=Image.fromarray((np.asarray(pg.convert("L"))>3).astype(np.uint8)*255)
sh=Image.new("RGB",tbi.size,(0,0,0)); 
tbi.paste(pg,(520,-60),mask)
save(np.asarray(tbi).astype(np.float32)/255,"a0000003")
# ---- Ruth oval tintype
bgv=0.10+0.06*noise(H,W,50,31)
im=Image.fromarray((np.stack([bgv]*3,-1)*255).astype(np.uint8)); d=ImageDraw.Draw(im)
cx,cy,rx,ry=900,506,300,390
for k,c in [(34,(150,140,120)),(26,(205,195,170)),(18,(120,112,95)),(10,(175,165,140))]:
    d.ellipse((cx-rx-k,cy-ry-k,cx+rx+k,cy+ry+k),fill=c)
# photo inside
ph=Image.new("L",(2*rx,2*ry),150); dp=ImageDraw.Draw(ph)
dp.rectangle((0,0,2*rx,2*ry),fill=165)
px=rx
dp.ellipse((px-78,170,px+78,370),fill=70)              # head
dp.polygon([(px-60,350),(px+60,350),(px+150,520),(px+175,780),(px-175,780),(px-150,520)],fill=60)  # dress
dp.rectangle((px-40,330,px+40,380),fill=75)
for i in range(9): dp.ellipse((px+52-i*3,300+i*30,px+86-i*3,336+i*30),fill=95)  # braid over shoulder
dp.rectangle((px-95,600,px+95,640),fill=88)  # folded hands
ph=ph.filter(ImageFilter.GaussianBlur(9))
pa=np.asarray(ph).astype(np.float32)/255
pa=pa*0.75+0.25*noise(2*ry,2*rx,3,33)*pa
yy2,xx2=np.mgrid[0:2*ry,0:2*rx]
silver=np.clip(((xx2/(2*rx)-0.5)**2+(yy2/(2*ry)-0.5)**2)*3.2,0,1)
pa=pa*(1-silver*0.6)+silver*0.55
pa=np.clip(0.18+pa*0.75,0,1)
php=Image.fromarray((pa*255).astype(np.uint8)).convert("RGB")
om=Image.new("L",(2*rx,2*ry),0); ImageDraw.Draw(om).ellipse((0,0,2*rx-1,2*ry-1),fill=255)
im.paste(php,(cx-rx,cy-ry),om)
save(np.asarray(im).astype(np.float32)/255,"a0000004")
print("ok")
