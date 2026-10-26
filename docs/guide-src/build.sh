#!/usr/bin/env bash
# Rebuilds docs/how-raffle-cli-was-built.pdf from the real source files.
# Usage: docs/guide-src/build.sh [output.pdf]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
out="${1:-$repo/docs/how-raffle-cli-was-built.pdf}"
html="$(mktemp --suffix=.html)"
trap 'rm -f "$html"' EXIT

# 1. HTML: prose + SVG diagrams + code snippets extracted from src/ and tests/ with `ast`
uv run --project "$repo" --with pygments python "$here/build.py" "$repo" "$html"
# 2. PDF: print the HTML with headless Chromium (Playwright)
node "$here/pdf.mjs" "$html" "$out"
echo "wrote $out"
