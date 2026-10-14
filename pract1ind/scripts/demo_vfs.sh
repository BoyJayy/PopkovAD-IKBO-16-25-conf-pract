#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
for variant in minimal several deep; do
    sh "$PROJECT_DIR/run.sh" \
        --vfs "$PROJECT_DIR/examples/vfs/$variant" \
        --prompt "$variant\$ " \
        --startup-script "$PROJECT_DIR/examples/stage3.txt"
done
