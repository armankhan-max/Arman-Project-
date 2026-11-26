#!/bin/sh
# Film Director AI on your own Mac or Linux computer: builds and starts the website in Docker, then opens it.
cd "$(dirname "$0")/.." || exit 1
command -v docker >/dev/null || { echo "Install Docker Desktop (free): https://www.docker.com/products/docker-desktop/ then run this again."; exit 1; }
docker info >/dev/null 2>&1 || { echo "Open Docker Desktop, wait until it is running, then run this again."; exit 1; }
CFG=run-local/owner-login.txt
if [ ! -f "$CFG" ]; then
  PW=$(LC_ALL=C tr -dc 'A-HJ-NP-Za-km-z2-9' </dev/urandom | head -c 12)
  KEY=$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 64)
  printf 'website: http://localhost:7860\nemail: owner@localhost\npassword: %s\nsecret: %s\n' "$PW" "$KEY" > "$CFG"; chmod 600 "$CFG"
fi
PW=$(sed -n 's/^password: //p' "$CFG"); KEY=$(sed -n 's/^secret: //p' "$CFG")
echo "Building the website (first time takes 5-15 minutes)..."
docker build -t film-director-ai -f deploy/huggingface/Dockerfile . || { echo "Build failed. Send the text above to Claude."; exit 1; }
docker rm -f film-director-ai >/dev/null 2>&1
docker run -d --name film-director-ai --restart unless-stopped -p 7860:7860 -v fda-data:/data -e FDA_ENV=local -e "FDA_OWNER_PASSWORD=$PW" -e "FDA_SECRET_KEY=$KEY" film-director-ai >/dev/null
i=0; while [ $i -lt 90 ] && ! curl -fs http://localhost:7860/api/health >/dev/null 2>&1; do sleep 2; i=$((i+1)); done
printf '\nREADY:  http://localhost:7860\nEmail:    owner@localhost\nPassword: %s\n(saved in run-local/owner-login.txt)\n' "$PW"
(open http://localhost:7860 || xdg-open http://localhost:7860) >/dev/null 2>&1 &
