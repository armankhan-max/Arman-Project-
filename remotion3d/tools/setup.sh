#!/bin/bash
# One-time tool install for a fresh machine: Blender, Cycles (bpy 5.x), MPFB humans, voiceover.
set -e
cd "$(dirname "$0")/.."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends blender python3-numpy
python3 -m venv /opt/bpyenv
/opt/bpyenv/bin/pip install -q bpy numpy edge-tts
mkdir -p /opt/blender-addons/mpfb /opt/blender-addons/packs
EXT=https://extensions.blender.org/download
curl -sSL -o /opt/blender-addons/mpfb/mpfb.zip \
  "$EXT/sha256:c075b3e9b94b8e5556a5f03f4653602d02ea306de08126e8f55ed6dee28a2dad/add-on-mpfb-v2.0.18.zip"
curl -sSL -o /opt/blender-addons/packs/sys.zip \
  https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip
/opt/bpyenv/bin/python blender/install_mpfb.py /opt/blender-addons/mpfb/mpfb.zip /opt/blender-addons/packs/sys.zip
npm install
