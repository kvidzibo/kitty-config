#!/usr/bin/env bash
set -euo pipefail

exec kitty +runpy 'import os, runpy, sys; sys.path.insert(0, os.path.dirname(sys.argv[1])); runpy.run_path(sys.argv[1])["main"](sys.argv[1:])' \
    "$(dirname -- "${BASH_SOURCE[0]}")/kitty-image-preview.py" "$@"
