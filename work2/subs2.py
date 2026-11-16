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

# ---- intro ----
box(5.4,8.3,"Something is wrong... AGAIN")
box(8.9,10.7,"Sleeves swallow your hands")
box(11.3,13.1,"Shoulders slump down")
box(15.0,18.1,"Rides up — lets the cold in")
box(26.8,30.3,"It's NOT you.",'Gold')
box(30.9,33.9,"Nobody taught you how a coat should fit")
count(36.8,40.3,0,5,"{} COATS",dur=0.9)
box(40.9,45.5,"#1 = the ONE coat for life",'Gold')
lower(46.1,51.5,"MALCOLM ASHBY  {\\c&H33CCFF&}• Tailor, 72")
count(55.9,60.6,0,50,"{} YEARS",dur=1.3)
box(61.3,64.3,"Bankers • Bus drivers • Grooms • Grandfathers")
lower(64.5,67.7,"A small shop in London")
lower(68.0,74.2,"Evelyn {\\c&H33CCFF&}• kept the books")
quote(76.7,82.0,"Why \"extra room\"\\Ncan make you {\\c&H33CCFF&}COLDER")
# ---- 4 checks ----
ev(86.0,89.0,'Big',r"{\an5\pos(960,470)\fscx40\fscy40\t(0,250,\fscx105\fscy105)\t(250,380,\fscx100\fscy100)\fad(0,300)}4 CHECKS",3)
box(90.7,94.7,"Before you look at a single coat")
card(95.4,"1","TRY IT OVER YOUR THICKEST LAYER"); badge(99.5,124.0,"CHECK 1 • THICKEST LAYER")
box(99.9,103.3,"Thin shirt in the shop...")
box(109.4,115.2,"...thick sweater in January = TOO TIGHT")
box(115.7,123.1,"Shop wearing jacket + sweater",'Gold')
card(124.2,"2","THE SHOULDERS"); badge(128.4,154.6,"CHECK 2 • SHOULDERS")
quote(129.3,131.8,"\"The shoulders never lie.\"")
box(132.1,138.1,"Seam at the EDGE of your shoulder",'Gold')
box(138.6,141.4,"Sleeves: easy fix")
count(141.9,148.5,0,200,"${}",dur=1.0)
ev(142.9,148.5,'Title',r"{\an5\pos(960,650)\fad(250,250)}to move a shoulder",3)
box(148.9,154.0,"Shoulders wrong? Put it BACK.",'Gold')
card(154.8,"3","MOVE IN IT"); badge(159.0,179.7,"CHECK 3 • MOVE")
box(161.3,164.9,"① Arms out in front")
box(165.2,167.1,"② Reach for the top shelf")
box(167.9,169.3,"③ Fold across your chest")
box(169.7,176.4,"Jumps to your belt? TOO SMALL")
card(179.9,"4","THE SLEEVES"); badge(184.1,207.3,"CHECK 4 • SLEEVES")
box(181.7,186.1,"Hinge of the wrist — covers jacket cuff",'Gold')
count(189.8,193.5,0,35,"${}",y=420,dur=0.7)
ev(190.6,193.5,'Big',r"{\an5\pos(960,610)\fscx70\fscy70\c&H33CCFF&\fad(200,0)}to $65",3)
quote(194.3,199.0,"\"Measure it again, lad.\"")
box(202.4,206.9,"Pin it • Mirror • Measure again")
# ---- countdown ----
ev(207.5,210.6,'Big',r"{\an5\pos(960,470)\fscx40\fscy40\t(0,250,\fscx105\fscy105)\t(250,380,\fscx100\fscy100)\fad(0,300)}THE COATS",3)
card(210.8,"#5","THE WOOL CAR COAT"); badge(215.0,249.2,"#5 • CAR COAT")
box(219.2,222.9,"Single-breasted • Mid-thigh")
box(223.3,230.3,"Sit in a car or bus — no bunching")
box(230.8,234.6,"Covers the seat of your trousers",'Gold')
box(235.2,240.1,"Bend to tie your shoe — no tent")
for i,(c,t) in enumerate([("&H5A2A12&","NAVY"),("&H4A4A4A&","CHARCOAL"),("&H2A4A7A&","SOFT BROWN")]):
    ev(240.7+i*0.9,245.6,'Badge',r"{\an7\pos(%d,780)\3c%s\fad(200,0)\fscx40\fscy40\t(0,200,\fscx100\fscy100)}%s"%(260+i*480,c,t),3)
card(249.4,"#4","THE PADDED COAT"); badge(253.6,295.7,"#4 • PADDED COAT")
box(260.8,266.4,"Warmer & lighter than wool",'Gold')
box(270.0,278.5,"Mistake: buying a size TOO BIG")
quote(279.2,282.3,"\"A bag with a man inside it.\"")
box(282.5,286.5,"Sit close — room for ONE sweater",'Gold')
box(291.3,295.2,"Hem rides up? Size up in LENGTH, not width")
ev(299.7,306.0,'Red',r"{\an5\pos(780,560)\fscx30\fscy30\t(0,250,\fscx110\fscy110)\t(250,400,\fscx100\fscy100)\fad(0,300)}LIKE",4)
ev(302.9,307.8,'Red',r"{\an5\pos(1150,560)\fscx30\fscy30\t(0,250,\fscx110\fscy110)\t(250,400,\fscx100\fscy100)\fad(0,300)}SUBSCRIBE",4)
card(321.8,"#3","HERRINGBONE WOOL"); badge(326.0,391.8,"#3 • HERRINGBONE")
box(340.0,343.2,"Zig-zag weave — like fish bones")
quote(346.6,348.8,"Texture hides\\N{\\c&H33CCFF&}EVERYTHING")
box(349.3,358.4,"Rain spots • Lint • Creases • Shine")
count(358.9,362.0,0,5,"{} WINTERS",dur=0.7)
box(362.0,366.5,"A soft brush on Sunday evening",'Gold')
box(371.2,375.3,"Single-breasted • Knee length")
box(375.9,380.5,"Collar flat — NO gap",'Gold')
box(381.1,385.7,"Gap = draught = cold neck")
box(386.5,391.7,"Grey or brown mix — not loud")
card(392.0,"#2","THE NAVY DUFFEL COAT"); badge(396.2,442.8,"#2 • DUFFEL COAT")
box(394.9,401.6,"Wooden toggles • Big hood")
box(411.7,416.9,"Toggles work with GLOVES ON",'Gold')
box(421.8,427.3,"Cut generously — check the fit!")
box(437.3,442.5,"Arm-lift check: 10 seconds",'Gold')
quote(443.1,447.8,"The promise...")
box(451.8,455.4,"Warmth ≠ thick cloth")
box(455.8,459.6,"A still layer of WARM AIR",'Gold')
box(463.7,468.8,"Too big = a bellows pumping heat out")
count(479.7,483.0,1950,1978,"{}",dur=1.0)
quote(494.7,497.7,"\"A coat rack that went\\Nout for a walk.\"")
box(501.8,505.8,"Room for ONE good sweater. Not an inch more.",'Gold')
box(506.1,511.4,"Big handful at the chest = TOO BIG")
card(515.3,"#1","CHARCOAL WORSTED OVERCOAT",4.6); badge(520.0,602.4,"#1 • CHARCOAL OVERCOAT")
box(523.4,527.5,"Single-breasted • Charcoal grey")
box(527.9,532.9,"Worsted: smooth, strong — wears for decades",'Gold')
lower(539.1,543.7,"Evelyn's rule {\\c&H33CCFF&}• charcoal before black")
box(548.3,553.7,"Black goes flat & shows every speck")
box(553.7,558.7,"Charcoal goes with navy, brown, grey",'Gold')
box(562.3,563.8,"Knee length or a touch below")
box(565.8,571.5,"Sleeves cover the jacket cuff")
box(572.4,579.8,"The gorge: neat, level, no ripple")
count(586.5,589.5,0,20,"{} WINTERS",dur=1.0)
box(590.1,597.2,"Passes the checks? Keep it. Wear it proudly.",'Gold')
# ---- recap ----
items=["Try it over your thickest layer","Check the shoulders","Lift your arms","Room for ONE sweater"]
for i,t in enumerate(items):
    y=250+i*130
    ev(605.2+i*1.6,611.2,'Badge',r"{\an7\pos(120,%d)\fad(250,0)\move(60,%d,120,%d,0,250)}✔  %s"%(y,y,y,t),3)
quote(611.3,615.3,"Measure twice.\\NBuy once.")
box(617.9,627.4,"TONIGHT: lift both arms in the mirror",'Gold')
box(627.8,632.9,"Tell me in the comments")
box(646.0,651.2,"NEXT: Shirt colours & collar gaps")
ev(651.7,655.0,'Title',r"{\an5\pos(960,520)\fad(400,0)}Stay sharp, my friend.",3)
open('text2.ass','w').write(H+"\n".join(E)+"\n")
print(len(E))
