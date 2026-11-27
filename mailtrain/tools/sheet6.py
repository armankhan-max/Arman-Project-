import glob, os, sys
from PIL import Image, ImageDraw
out=sys.argv[1]; files=sorted(sum([glob.glob(p) for p in sys.argv[2:]],[]))
cols=int(os.environ.get("COLS",6)); tw,th=int(os.environ.get("TW",300)),int(os.environ.get("TH",210)); rows=(len(files)+cols-1)//cols
S=Image.new("RGB",(cols*tw,max(1,rows)*(th+14)),"white"); d=ImageDraw.Draw(S)
for i,f in enumerate(files):
    im=Image.open(f); im.draft("L",(tw*2,th*2)); im=im.convert("RGB"); im.thumbnail((tw,th))
    x,y=(i%cols)*tw,(i//cols)*(th+14); S.paste(im,(x+(tw-im.width)//2,y)); d.text((x+3,y+th+1),os.path.basename(f)[:40],fill="black")
S.save(out,quality=78); print(out,len(files))
