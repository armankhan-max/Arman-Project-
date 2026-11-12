#!/bin/bash
# Full background pipeline: render changed shots, then handles + assembly. Resumable.
cd "$(dirname "$0")/.."
tools/render_all.sh A B E1 G1 G2 T
SPP=8 tools/render_all.sh S
tools/assemble.sh
