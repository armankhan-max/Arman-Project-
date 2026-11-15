def ts(t):
    h=int(t//3600);m=int(t%3600//60);s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
H="""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Num,DejaVu Sans,230,&H0033CCFF,&H000000FF,&H00101010,&H90000000,1,0,0,0,100,100,0,0,1,10,6,5,0,0,0,1
Style: Title,DejaVu Sans,82,&H00FFFFFF,&H000000FF,&H00202020,&HC0000000,1,0,0,0,100,100,1,0,3,18,0,5,0,0,0,1
Style: Box,DejaVu Sans,64,&H00FFFFFF,&H000000FF,&H00141414,&H80000000,1,0,0,0,100,100,0,0,3,16,0,2,80,80,90,1
Style: Gold,DejaVu Sans,64,&H0033CCFF,&H000000FF,&H00141414,&H80000000,1,0,0,0,100,100,0,0,3,16,0,2,80,80,90,1
Style: Big,DejaVu Sans,150,&H00FFFFFF,&H000000FF,&H00101010,&H90000000,1,0,0,0,100,100,2,0,1,9,5,5,0,0,0,1
Style: Badge,DejaVu Sans,46,&H00FFFFFF,&H000000FF,&H001E3A8A,&H00000000,1,0,0,0,100,100,0,0,3,14,0,9,0,50,45,1
Style: Quote,DejaVu Serif,74,&H00FFFFFF,&H000000FF,&H00101010,&H90000000,1,1,0,0,100,100,0,0,1,6,4,5,0,0,0,1
Style: Red,DejaVu Sans,70,&H00FFFFFF,&H000000FF,&H000000CC,&H00000000,1,0,0,0,100,100,1,0,3,20,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
E=[]
def ev(a,b,style,txt,layer=1):E.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{txt}")
POP=r"{\fscx30\fscy30\t(0,220,\fscx112\fscy112)\t(220,380,\fscx100\fscy100)\fad(0,250)}"
def box(a,b,txt,style='Box'):ev(a,b,style,POP+txt)
def card(t,n,title,dur=4.2):
    ev(t,t+dur,'Num',r"{\an5\pos(960,400)\fscx20\fscy20\t(0,260,\fscx120\fscy120)\t(260,420,\fscx100\fscy100)\fad(0,300)}"+f"#{n}",2)
    ev(t+0.35,t+dur,'Title',r"{\an5\pos(960,640)\fad(250,300)\move(960,700,960,640,0,300)}"+title,2)
def count(a,b,v0,v1,fmt,y=480,dur=1.0,style='Big'):
    steps=20
    for i in range(steps):
        t0=a+dur*i/steps;t1=a+dur*(i+1)/steps if i<steps-1 else b
        v=v0+(v1-v0)*(i+1)/steps
        ev(t0,t1,style,r"{\an5\pos(960,%d)}"%y+fmt.format(int(round(v))),2)
def badge(a,b,n):ev(a,b,'Badge',r"{\fad(300,300)}"+f"MISTAKE #{n}",1)
def quote(a,b,txt):ev(a,b,'Quote',r"{\an5\pos(960,540)\fad(400,400)}"+txt,2)
