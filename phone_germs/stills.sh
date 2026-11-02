#!/bin/bash
# usage: ./stills.sh frame1 frame2 ...  -> review/f<frame>.jpg
cd "$(dirname "$0")"
for fr in "$@"; do
  npx remotion still src/index.ts Main review/f$fr.jpg --frame=$fr --image-format=jpeg --log=error >/dev/null 2>&1 || echo "fail $fr"
done
