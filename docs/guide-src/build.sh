#!/usr/bin/env bash
# Rebuilds the guide PDFs from the real source files.
# Usage: docs/guide-src/build.sh [en|es|all] [output.pdf]     (default: all, written into docs/)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
which="${1:-all}"

build() {  # build <lang> <output.pdf> <footer title>
  local html
  html="$(mktemp --suffix=.html)"
  # 1. HTML: prose + SVG diagrams + code snippets extracted from src/ and tests/ with `ast`
  uv run --project "$repo" --with pygments python "$here/build.py" "$repo" "$html" "$1"
  # 2. PDF: print the HTML with headless Chromium (Playwright)
  node "$here/pdf.mjs" "$html" "$2" "$3"
  rm -f "$html"
  echo "wrote $2"
}

case "$which" in
  en)  build en "${2:-$repo/docs/how-raffle-cli-was-built.pdf}" "how raffle-cli was built" ;;
  es)  build es "${2:-$repo/docs/como-se-construyo-raffle-cli.pdf}" "cómo se construyó raffle-cli" ;;
  all) build en "$repo/docs/how-raffle-cli-was-built.pdf" "how raffle-cli was built"
       build es "$repo/docs/como-se-construyo-raffle-cli.pdf" "cómo se construyó raffle-cli" ;;
  *)   echo "usage: $0 [en|es|all] [output.pdf]" >&2; exit 1 ;;
esac
