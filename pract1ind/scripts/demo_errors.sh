#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
sh "$PROJECT_DIR/run.sh" \
    --vfs "$PROJECT_DIR/examples/vfs/several" \
    --prompt 'errors$ ' \
    --startup-script "$PROJECT_DIR/examples/errors.txt"
if sh "$PROJECT_DIR/run.sh" \
    --vfs "$PROJECT_DIR/examples/vfs/several" \
    --prompt 'missing$ ' \
    --startup-script "$PROJECT_DIR/examples/not-found.txt"; then
    printf '%s\n' 'Ошибка проверки: отсутствующий скрипт был принят' >&2
    exit 1
fi
if sh "$PROJECT_DIR/run.sh" --unknown; then
    printf '%s\n' 'Ошибка проверки: неизвестный параметр был принят' >&2
    exit 1
fi
