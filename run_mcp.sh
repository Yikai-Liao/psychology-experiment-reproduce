#!/usr/bin/env sh
set -eu

# Resolve the directory that contains this script so the command works from anywhere.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

uv run fastmcp run main.py
