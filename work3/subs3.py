import json,re
exec(open('tl.py').read())
def ts(t):
    t=max(0,t);h=int(t//3600);m=int(t%3600//60);s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
H="""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,DejaVu Sans,56,&H0033CCFF,&H00FFFFFF,&H00101010,&H99000000,1,0,0,0,100,100,0,0,1,4,3,2,120,120,48,1
Style: Num,DejaVu Serif,240,&H0033CCFF,&H000000FF,&H00101010,&H90000000,1,0,0,0,100,100,0,0,1,10,6,5,0,0,0,1
Style: Title,DejaVu Sans,78,&H00FFFFFF,&H000000FF,&H00203A1F,&HC0000000,1,0,0,0,100,100,1,0,3,20,0,5,0,0,0,1
Style: Box,DejaVu Sans,60,&H00FFFFFF,&H000000FF,&H00141414,&H80000000,1,0,0,0,100,100,0,0,3,16,0,8,80,80,70,1
Style: Gold,DejaVu Sans,60,&H00101010,&H000000FF,&H0033CCFF,&H80000000,1,0,0,0,100,100,0,0,3,16,0,8,80,80,70,1
Style: Big,DejaVu Serif,150,&H00FFFFFF,&H000000FF,&H00101010,&H90000000,1,0,0,0,100,100,2,0,1,9,5,5,0,0,0,1
Style: Badge,DejaVu Sans,44,&H00FFFFFF,&H000000FF,&H00443322,&H00000000,1,0,0,0,100,100,1,0,3,14,0,9,0,50,45,1
Style: Quote,DejaVu Serif,76,&H00FFFFFF,&H000000FF,&H00101010,&H90000000,1,1,0,0,100,100,0,0,1,6,4,5,0,0,0,1
Style: Red,DejaVu Sans,66,&H00FFFFFF,&H000000FF,&H000000CC,&H00000000,1,0,0,0,100,100,1,0,3,20,0,5,0,0,0,1
Style: Lower,DejaVu Sans,46,&H00FFFFFF,&H000000FF,&H00443322,&H00000000,1,0,0,0,100,100,0,0,3,14,0,1,90,0,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
E=[]
def ev(a,b,style,txt,layer=1,raw=False):
    if not raw: a,b=M(a),M(b)
    E.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{txt}")
POP=r"{\fscx30\fscy30\t(0,220,\fscx112\fscy112)\t(220,380,\fscx100\fscy100)\fad(0,250)}"
SLIDE=r"{\fad(200,250)\fscx100\t(0,250,\fscx100)}"
def box(a,b,t,s='Box'): ev(a,b,s,POP+t,2)
def card(t,tag,title,dur=4.0,small="#"):
    ev(t,t+dur,'Num',r"{\an5\pos(960,390)\fscx20\fscy20\t(0,260,\fscx118\fscy118)\t(260,420,\fscx100\fscy100)\fad(0,300)}"+tag,3)
    ev(t+0.35,t+dur,'Title',r"{\an5\pos(960,640)\fad(250,300)\move(960,710,960,640,0,320)}"+title,3)
def count(a,b,v0,v1,fmt,y=460,dur=1.0):
    st=20
    for i in range(st):
        t0=a+dur*i/st; t1=a+dur*(i+1)/st if i<st-1 else b
        v=v0+(v1-v0)*(i+1)/st
        ev(t0,t1,'Big',r"{\an5\pos(960,%d)}"%y+fmt.format(int(round(v))),3)
def badge(a,b,t): ev(a,b,'Badge',r"{\fad(300,300)}"+t,2)
def quote(a,b,t): ev(a,b,'Quote',r"{\an5\pos(960,470)\fad(400,400)\blur1}"+t,3)
def lower(a,b,t): ev(a,b,'Lower',r"{\fad(300,300)\move(40,910,90,910,0,300)}"+t,2)

# ---- karaoke captions ----
segs=json.load(open('transcript.json'))
for s in segs:
    ws=[w for w in s['words'] if w[2].strip()]
    chunk=[]
    def flush():
        if not chunk: return
        a=M(chunk[0][0]); b=M(chunk[-1][1])+0.15
        parts=[]
        for i,(w0,w1,wd) in enumerate(chunk):
            nxt=M(chunk[i+1][0]) if i+1<len(chunk) else M(w1)
            cs=max(1,int(round((nxt-M(w0))*100)))
            parts.append(r"{\kf%d}"%cs+wd.strip().replace('{','').replace('}',''))
        lead=max(0,int(round((M(chunk[0][0])-a)*100)))
        ev(a,b,'Cap',r"{\fad(80,80)}"+" ".join(parts),1,raw=True)
        chunk.clear()
    for w in ws:
        chunk.append(w)
        if len(chunk)>=6 or w[2].strip()[-1:] in '.,?!': flush()
    flush()

# ---- hook ----
box(0.3,1.9,"The first cold week of December...")
box(2.9,7.3,"The same grey sweatshirt")
box(7.5,12.4,"The same tired cardigan")
box(16.5,20.5,"\"A man who has given up\"")
box(20.7,24.0,"It's NOT you. It was never your fault.",'Gold')
quote(24.3,30.9,"COSY  +  SHARP\\N{\\fs50\\i0}can live in the same outfit")
count(31.5,35.2,0,12,"{} OUTFITS",dur=1.0)
lower(33.0,35.6,"Still wearing them at {\\c&H33CCFF&}72")
box(36.0,43.0,"Built the way a TAILOR builds them",'Gold')
lower(43.4,47.6,"#1: the outfit Evelyn chose {\\c&H33CCFF&}40 years ago")
lower(48.0,52.3,"MALCOLM ASHBY {\\c&H33CCFF&}• 50 years fitting clothes • London")
count(52.6,57.0,1950,1970,"{}",dur=1.2)
ev(53.6,57.0,'Title',r"{\an5\pos(960,650)\fad(250,250)}Age 16 • a wool mill town",3)
lower(58.0,62.9,"Evelyn {\\c&H33CCFF&}• kept the books")
ev(70.3,80.3,'Badge',r"{\fad(300,300)}GUIDE LINK IN THE DESCRIPTION",3)
box(71.0,75.8,"The Over-60 Fit & Style Guide",'Gold')
box(85.2,92.4,"A sweater rule most men get BACKWARDS")
# ---- 3 rules ----
ev(93.1,98.8,'Big',r"{\an5\pos(960,470)\fscx40\fscy40\t(0,250,\fscx105\fscy105)\t(250,380,\fscx100\fscy100)\fad(0,300)}3 RULES",3)
card(99.3,"1","FIT FIRST, FASHION SECOND",3.6)
box(104.9,107.4,"Hangs off you = a blanket with sleeves")
box(107.6,111.5,"Seam at shoulder edge • Cuff at wrist bone",'Gold')
card(111.9,"2","SOFT CLOTH YOU'LL WEAR",3.6)
box(116.0,121.3,"Merino • Lambswool — no itch",'Gold')
card(121.7,"3","THIN LAYERS BEFORE THICK",3.6)
box(126.0,128.5,"Shirt → Knit → Jacket",'Gold')
box(128.7,132.3,"Thin layers trap warm air")
for i,(c,t) in enumerate([("&H5A2A12&","NAVY"),("&H4A4A4A&","CHARCOAL"),("&H2A4A7A&","BROWN"),("&HB9D4E6&","CREAM")]):
    ev(133.0+i*0.8,138.6,'Badge',r"{\an7\pos(%d,780)\3c%s\fad(200,0)\fscx40\fscy40\t(0,200,\fscx100\fscy100)}%s"%(150+i*430,c,t),3)
# ---- outfits ----
OUT=[(139.0,"12","GREY FLANNEL + NAVY LAMBSWOOL"),(172.1,"11","BROWN CORDS + CREAM CABLE KNIT"),(201.9,"10","TWEED + GREEN KNITTED TIE"),
(233.2,"9","NAVY BLAZER + CHARCOAL ROLL NECK"),(260.0,"8","THE SHAWL-COLLAR CARDIGAN"),(301.3,"7","DARK JEANS + NAVY BLAZER"),
(329.2,"6","CHARCOAL + GREY MERINO"),(362.5,"5","WAXED JACKET FOR A COLD WALK"),(400.8,"4","THE KNITTED WAISTCOAT"),
(478.7,"3","SCARF • GLOVES • FLAT CAP"),(513.6,"2","CHARCOAL WORSTED + FINE NAVY KNIT"),(561.0,"1","EVELYN'S NAVY SWEATER")]
for k,(t,n,title) in enumerate(OUT):
    card(t,"#"+n,title,4.2)
    end=OUT[k+1][0]-0.3 if k+1<len(OUT) else 628.0
    badge(t+4.3,end,"OUTFIT #%s"%n)
box(147.0,150.0,"White collar showing")
box(150.3,154.5,"Flannel = brushed wool, soft as a blanket")
box(154.7,159.5,"…the collar stops it looking like pyjamas",'Gold')
box(159.7,163.0,"Natural waist • gentle break")
quote(169.2,171.6,"Nobody asked if I was unwell.")
quote(178.5,183.8,"\"A friendly\\Nlighthouse keeper\"")
box(184.8,189.6,"Corduroy: warm & smart for Sunday lunch")
box(189.8,193.8,"Cable knit = texture, no pattern needed",'Gold')
box(194.5,199.6,"Outlasted 3 washing machines")
box(211.8,217.3,"Tweed hides every crease",'Gold')
box(217.8,223.4,"3 weddings & a christening")
quote(224.0,232.9,"\"The shoulders never lie.\"")
box(243.9,248.1,"Roll neck fills the gap a tie would leave",'Gold')
lower(248.5,253.1,"Evelyn: {\\c&H33CCFF&}\"my quiet outfit\"")
box(253.6,259.5,"Bunches at the collar? Too thick — choose FINE knit")
box(265.2,270.2,"Over a shirt and tie")
box(270.4,277.3,"Shawl collar = a woollen smoking jacket",'Gold')
box(277.5,286.0,"Buttons pull? Go UP a size")
ev(292.3,297.5,'Red',r"{\an5\pos(780,560)\fscx30\fscy30\t(0,250,\fscx110\fscy110)\t(250,400,\fscx100\fscy100)\fad(0,300)}LIKE",4)
ev(292.9,297.5,'Red',r"{\an5\pos(1150,560)\fscx30\fscy30\t(0,250,\fscx110\fscy110)\t(250,400,\fscx100\fscy100)\fad(0,300)}SUBSCRIBE",4)
box(307.5,313.0,"White shirt • Navy blazer • Brown boots")
box(313.2,316.5,"Plain & dark — no rips, no fading",'Gold')
box(334.0,339.9,"Charcoal trousers • Grey merino crew")
box(339.9,346.4,"Polished brown lace-ups",'Gold')
box(346.6,349.2,"Quiet colours never argue")
count(349.8,353.0,0,20,"{} YEARS",dur=0.8)
box(367.8,373.7,"Waxed jacket • Thick grey jumper")
quote(377.0,382.0,"Pavements are the real\\Ndanger after 60")
box(382.2,385.1,"Deep-tread rubber soles",'Gold')
box(390.8,395.4,"Sheds rain • Cuts the wind")
lower(400.8,406.3,"Mr. Pettigrew's {\\c&H33CCFF&}everyday outfit")
box(411.5,416.9,"Knitted waistcoat • Cream shirt • Navy tie")
box(416.9,421.4,"Warm chest — arms free",'Gold')
box(427.1,434.0,"Leave the BOTTOM button undone")
quote(436.0,441.0,"\"Measure it again, lad.\"")
box(445.5,451.2,"Measure twice. Buy once.",'Gold')
quote(451.8,456.6,"The sweater rule\\N{\\c&H33CCFF&}men get backwards")
box(456.9,462.2,"Tight FINE knit beats chunky LOOSE knit",'Gold')
box(462.4,468.0,"Wind walks through an open knit")
box(473.3,478.5,"Hold it to a window — see daylight? Put it back")
box(478.9,485.0,"Costs the least • does the most")
box(492.2,497.3,"Scarf closes the gap at the collar",'Gold')
box(497.5,503.3,"Scarf UNDER the coat collar")
lower(503.3,513.4,"Feeling the cold more? {\\c&H33CCFF&}Mention it at your check-up")
box(519.2,526.6,"Charcoal worsted • fine navy knit — no tie")
box(526.8,532.6,"Worsted: smooth, hard-wearing",'Gold')
count(538.8,544.0,1990,1996,"{}",dur=1.0)
ev(539.8,544.0,'Title',r"{\an5\pos(960,650)\fad(250,250)}Cut bespoke — taken in twice since",3)
box(548.0,557.2,"Ready-made + sleeves & waist altered = just as sharp",'Gold')
box(568.6,574.4,"Grey flannel • White shirt • Brown suede")
count(575.2,579.4,1950,1986,"{}",dur=1.2)
ev(576.4,579.4,'Title',r"{\an5\pos(960,650)\fad(250,250)}A market in Cornwall",3)
quote(585.0,590.8,"\"Trust me, Malcolm.\\NIt's the one that will last.\"")
box(602.4,607.4,"Warmer than his thick sweaters",'Gold')
box(607.6,612.5,"The TIGHT knit made the difference")
box(612.5,617.9,"Mended at the elbow 3 times")
quote(618.5,627.6,"What we wear keeps\\Nthe people we love close")
# ---- recap ----
items=["Fit first","Soft cloth you'll wear","Thin layers before thick","Fine, tight knit"]
for i,t in enumerate(items):
    y=250+i*130
    ev(629.0+i*1.3,638.2,'Badge',r"{\an7\pos(120,%d)\fad(250,0)\move(60,%d,120,%d,0,250)}✔  %s"%(y,y,y,t),3)
box(638.4,644.0,"Build it from your own wardrobe",'Gold')
box(644.2,649.4,"Which one will you try first? Comment below")
ev(654.3,660.6,'Title',r"{\an5\pos(960,520)\fad(400,0)}Stay sharp, my friend.",3)
open('text3.ass','w').write(H+"\n".join(E)+"\n")
print(len(E))
