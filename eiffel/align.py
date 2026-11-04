import re,json,sys
from pocketsphinx import Decoder
W='/tmp/claude-0/-home-user-Arman-Project-/d8bac737-4b11-57bd-b81f-a284f475629e/scratchpad/vo16.wav'
raw=open(W,'rb').read()[44:]
txt=open('script.txt').read()
disp=txt.split()
d=Decoder(samprate=16000,loglevel='FATAL')
# map display words -> spoken tokens
spoken={'1925,':['nineteen','twenty','five'],'Lustig':['lustig'],'André':['andre']}
custom={'lustig':'L AH S T IH G','andre':'AA N D R EY','poisson':'P W AA S AA N','letterheads':'L EH T ER HH EH D Z','fanciest':'F AE N S IY AH S T'}
for k,v in custom.items():
    if d.lookup_word(k) is None: d.add_word(k,v,True)
toks=[];owner=[]
for i,w in enumerate(disp):
    base=re.sub(r"[^\w'é]","",w)
    sp=spoken.get(w) or spoken.get(base) or [base.lower().replace('é','e')]
    for s in sp:
        if d.lookup_word(s) is None: print('MISSING',s)
        toks.append(s);owner.append(i)
d.set_align_text(' '.join(toks))
d.start_utt();d.process_raw(raw,full_utt=True);d.end_utt()
d.set_alignment();d.start_utt();d.process_raw(raw,full_utt=True);d.end_utt()
seg=[(s.name,s.start,s.duration) for s in d.get_alignment()]
words=[x for x in seg if x[0] not in ('<s>','</s>','<sil>') ]
print(len(words),len(toks))
res=[]
j=0
for name,st,du in words:
    i=owner[j];j+=1
    if res and res[-1]['i']==i: res[-1]['end']=(st+du)/100
    else: res.append({'i':i,'w':disp[i],'start':st/100,'end':(st+du)/100})
json.dump(res,open('words.json','w'),indent=0)
print(' '.join(f"{r['w']}@{r['start']:.2f}" for r in res))
