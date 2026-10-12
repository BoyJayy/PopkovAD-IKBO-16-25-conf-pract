#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
sh "$PROJECT_DIR/run.sh" <<'EOF'
ls
exit
EOF
sh "$PROJECT_DIR/run.sh" \
    --vfs "$PROJECT_DIR/examples/виртуальная файловая система" \
    --prompt 'demo$ ' \
    --startup-script "$PROJECT_DIR/examples/success.txt"
