"""Builds the guide as one HTML file.  Usage: python build.py <repo> <out.html> <en|es>"""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common  # noqa: E402  (reads sys.argv)

importlib.import_module(f"guide_{common.LANG}")
common.OUT.write_text(common.render(), encoding="utf-8")
print("wrote", common.OUT, len(common.P), "blocks;", f"reveal={common.REVEAL:.2f}s", f"tests={common.TOTAL}")
import diagrams  # noqa: E402

if diagrams.MISSING:
    print("untranslated diagram labels:", *sorted(diagrams.MISSING), sep="\n  ")
