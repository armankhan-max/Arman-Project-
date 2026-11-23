#!/bin/bash
# One-time setup in a fresh cloud session (~3-5 min).
set -e
pip install -q faster-whisper rembg opencv-python-headless onnxruntime pillow 2>&1 | grep -v WARN || true
python3 -c "import torch" 2>/dev/null || pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu 2>&1 | grep -v WARN || true
python3 -c "import df" 2>/dev/null || pip install -q deepfilternet 2>&1 | grep -v WARN || true
pip install -q "numpy>=2.1" 2>&1 | grep -v -E "WARN|dependency|deepfilternet" || true
# torchaudio>=2.x dropped torchaudio.backend; patch DeepFilterNet's import
F=$(python3 -c "import df,os;print(os.path.dirname(df.__file__))" 2>/dev/null)/io.py
grep -q "AudioMetaData = object" "$F" || sed -i 's/^from torchaudio.backend.common import AudioMetaData/try:\n    from torchaudio.backend.common import AudioMetaData\nexcept Exception:\n    AudioMetaData = object/' "$F"
# DeepFilterNet3 model (github.com/raw is blocked by the proxy; raw.githubusercontent works)
mkdir -p ~/.cache/DeepFilterNet
if [ ! -d ~/.cache/DeepFilterNet/DeepFilterNet3 ]; then
  curl -sSL -o ~/.cache/DeepFilterNet/DeepFilterNet3.zip https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/models/DeepFilterNet3.zip
  (cd ~/.cache/DeepFilterNet && unzip -oq DeepFilterNet3.zip)
fi
python3 -c "from df.enhance import init_df; init_df(); import faster_whisper; print('SETUP OK')" 2>&1 | tail -1
