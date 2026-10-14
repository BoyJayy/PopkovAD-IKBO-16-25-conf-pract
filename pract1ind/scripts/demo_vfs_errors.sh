#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
sh "$PROJECT_DIR/run.sh" --prompt 'empty$ ' <<'EOF'
vfs-info
vfs-info /not-found
exit
EOF
for variant in minimal several deep; do
    sh "$PROJECT_DIR/run.sh" \
        --vfs "$PROJECT_DIR/examples/vfs/$variant" \
        --prompt "$variant\$ " \
        --startup-script "$PROJECT_DIR/examples/stage3.txt"
done
for source in not-found minimal/hello.txt; do
    if sh "$PROJECT_DIR/run.sh" \
        --vfs "$PROJECT_DIR/examples/vfs/$source" \
        --prompt 'invalid$ ' \
        --startup-script "$PROJECT_DIR/examples/stage3.txt"; then
        printf '%s\n' 'Ошибка проверки: неверный источник VFS принят' >&2
        exit 1
    fi
done
