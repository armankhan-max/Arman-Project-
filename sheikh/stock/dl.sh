while read id name; do
  [ -s "$name.mp4" ] && continue
  for q in 1080 720; do
    code=$(curl -s -m 120 -o "$name.mp4" -w "%{http_code}" "https://assets.mixkit.co/videos/$id/$id-$q.mp4")
    [ "$code" = "200" ] && break
    rm -f "$name.mp4"
  done
  echo "$id $name $q $code"
done < ids.txt
