#!/bin/bash
# Makes parts 2..15 one at a time, waits out usage limits, then joins the final video.
G=/home/user/Arman-Project-/gta-tatiana; S=~/.claude/skills/gta/scripts; J=$G/voice-video
log(){ echo "$(date '+%H:%M') $*" | tee -a $G/drive.log; }
for n in $(seq 2 15); do
  NN=$(printf %02d $n)
  [ -f $J/parts/part$NN/PREVIEW.mp4 ] && { log "part $n already done"; continue; }
  prev=""
  for attempt in 1 2 3 4 5 6 7 8; do
    python3 $G/tools/make_pack.py $n >/dev/null 2>&1
    R=$(ls -d /root/gta-runs/*tatiana-part$NN* 2>/dev/null | tail -1)
    if [ -z "$R" ] || [ -n "$prev" ]; then
      extra=(); [ -n "$prev" ] && extra=(--work-before "$prev")
      R=$(python3 $S/new_run.py --job $J --part $n --total 15 --look --name tatiana${attempt} "${extra[@]}" --notes "$(cat $G/tools/notes.txt)" 2>&1 | tail -1)
    fi
    log "part $n attempt $attempt: $R"
    python3 $S/run_sealed.py "$R" > /root/gta-runs/p$NN.out 2>&1
    if [ -f "$R/broll.mp4" ]; then
      python3 $S/finish_part.py "$R" $J $n >> $G/drive.log 2>&1 && log "part $n finished" && break
    fi
    log "part $n: no video (limit or error); waiting 40 min"
    prev="$R"; sleep 2400
  done
done
python3 $S/join_parts.py $J >> $G/drive.log 2>&1 && log "JOINED"
