#!/bin/bash
# One of several parallel workers: claims parts not yet done (mkdir lock), makes them, waits out usage limits.
# Usage: worker.sh [part to finish first] [its running run folder]
G=/home/user/Arman-Project-/gta-tatiana; S=~/.claude/skills/gta/scripts; J=$G/voice-video; C=$G/claims
mkdir -p $C
log(){ echo "$(date '+%H:%M') [w$$] $*" >> $G/drive.log; }
do_part(){
  n=$1; NN=$(printf %02d $n); prev=""; R="$2"
  for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
    if [ -n "$R" ] && pgrep -f "run_sealed.py $R\$" >/dev/null; then
      while pgrep -f "run_sealed.py $R\$" >/dev/null; do sleep 30; done
    else
      python3 $G/tools/make_pack.py $n >/dev/null 2>&1
      extra=(); [ -n "$prev" ] && extra=(--work-before "$prev")
      R=$(python3 $S/new_run.py --job $J --part $n --total 15 --look --name tat$attempt "${extra[@]}" --notes "$(cat $G/tools/notes.txt)" 2>&1 | tail -1)
      log "part $n attempt $attempt: $R"
      python3 $S/run_sealed.py "$R" > /root/gta-runs/p$NN-$$.out 2>&1
    fi
    if [ -f "$R/broll.mp4" ]; then
      python3 $S/finish_part.py "$R" $J $n >> $G/finish.log 2>&1 && { log "part $n finished"; return; }
    fi
    log "part $n: no video (limit or error); waiting 30 min"
    prev="$R"; R=""; sleep 1800
  done
}
if [ -n "$1" ]; then do_part $1 "$2"; fi
for n in $(seq 3 15); do
  NN=$(printf %02d $n)
  [ -f $J/parts/part$NN/PREVIEW.mp4 ] && continue
  mkdir $C/part$NN 2>/dev/null || continue
  do_part $n
done
all=1; for n in $(seq 1 15); do [ -f $J/parts/part$(printf %02d $n)/PREVIEW.mp4 ] || all=0; done
if [ $all = 1 ] && mkdir $C/join 2>/dev/null; then
  python3 $S/join_parts.py $J >> $G/finish.log 2>&1 && log "JOINED"
fi
