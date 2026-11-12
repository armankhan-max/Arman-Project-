#!/bin/bash
# Full background pipeline (resumable): finish the long shot, then handles + assembly.
cd "$(dirname "$0")/.."
SPP=8 tools/render_all.sh S
tools/assemble.sh
