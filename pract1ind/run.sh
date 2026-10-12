#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$PROJECT_DIR/src/main.py" "$@"
