"""Shared helpers for the guide: snippet extraction (ast), callouts, derived numbers, CSS and HTML rendering.

Usage (via build.py): python build.py <repo> <out.html> <en|es>"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import textwrap
from html import escape
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer, get_lexer_by_name

sys.path.insert(0, str(Path(__file__).parent))
import diagrams as D  # noqa: E402

REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
LANG = sys.argv[3] if len(sys.argv) > 3 else "en"
D.LANG = LANG
SRC = REPO / "src" / "raffle_cli"
FMT = HtmlFormatter(nowrap=True, style="friendly")


# --------------------------------------------------------------------- helpers
def hl(code: str, lang: str = "python") -> str:
    lexer = PythonLexer() if lang == "python" else get_lexer_by_name(lang)
    return highlight(code, lexer, FMT)


def snip(code: str, lang: str = "python", caption: str = "") -> str:
    cap = f'<div class="cap">{escape(caption)}</div>' if caption else ""
    body = textwrap.dedent(code).strip(chr(10))
    long_cls = " long" if body.count(chr(10)) > 22 else ""
    return f'<div class="code{long_cls}">{cap}<pre>{hl(body, lang)}</pre></div>'


def code(file: str, qual: str, caption: str | None = None, strip_doc: bool = False) -> str:
    path = (REPO / file) if "/" in file else (SRC / file)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = tree
    for part in qual.split("."):
        node = next(n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == part)
    start = min([node.lineno] + [d.lineno for d in node.decorator_list])
    lines = source.splitlines()[start - 1 : node.end_lineno]
    text = textwrap.dedent("\n".join(lines))
    return snip(text, "python", caption or f"{path.relative_to(REPO)} · {qual}")


def lines_of(file: str, a: str, b: str, lang="python", caption="") -> str:
    """Snippet between the first line containing `a` and the first following line containing `b` (inclusive)."""
    path = (REPO / file) if "/" in file else (SRC / file)
    ls = path.read_text(encoding="utf-8").splitlines()
    i = next(k for k, l in enumerate(ls) if a in l)
    j = next(k for k in range(i, len(ls)) if b in ls[k])
    return snip("\n".join(ls[i : j + 1]), lang, caption or f"{path.relative_to(REPO)}")


def callout(kind: str, title: str, body: str) -> str:
    return f'<div class="callout {kind}"><div class="ct">{title}</div>{body}</div>'


DECISION_PREFIX = {"en": "Technical decision", "es": "Decisión técnica"}


def decision(title: str, body: str) -> str:
    return callout("decision", f"{DECISION_PREFIX[LANG]}: {title}", body)


def tip(title: str, body: str) -> str:
    return callout("tip", title, body)


def warn(title: str, body: str) -> str:
    return callout("warn", title, body)


def chapter(num: int | str, title: str, anchor: str) -> str:
    return f'<h1 id="{anchor}"><span class="num">{num}</span>{title}</h1>'


# ---------------------------------------------------------------- derived data
def loc(name: str) -> int:
    return len((SRC / name).read_text().splitlines())


def reel_time(steps: int) -> float:
    return sum(0.04 + 0.28 * (p / steps) ** 3 for p in range(2, steps))


T1 = 0.18 + reel_time(18)
T2 = 0.18 + reel_time(30)
REVEAL = T2 + 0.5

collected = subprocess.run(
    [sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=REPO, capture_output=True, text=True
).stdout
counts: dict[str, int] = {}
for line in collected.splitlines():
    m = re.match(r"tests/(\w+)\.py::", line)
    if m:
        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
TOTAL = sum(counts.values())


P: list[str] = []
add = P.append


CSS = (
    HtmlFormatter(style="friendly").get_style_defs(".code pre")
    + """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
* { box-sizing: border-box; }
body { font-family: Inter, Helvetica, Arial, sans-serif; font-size: 10.4pt; line-height: 1.5; color: #1f2937; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 0.88em; background: #f3f4f6; padding: 0.5px 4px; border-radius: 3px; color: #111827; }
h1 { font-size: 21pt; margin: 0 0 10px; padding-top: 4px; border-bottom: 3px solid #2563eb; padding-bottom: 6px; page-break-before: always; line-height: 1.2; }
h1 .num { display: inline-block; background: #2563eb; color: #fff; border-radius: 6px; padding: 0 10px; margin-right: 10px; font-size: 18pt; }
h2 { font-size: 14pt; margin: 20px 0 6px; color: #1e3a8a; break-after: avoid; }
h3 { font-size: 11.5pt; margin: 14px 0 4px; color: #374151; break-after: avoid; }
p { margin: 6px 0; } ul, ol { margin: 6px 0 6px 20px; padding: 0; } li { margin: 3px 0; }
.cover { height: 235mm; padding-top: 28mm; page-break-after: always; }
.cover .kicker { color: #2563eb; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; font-size: 10pt; }
.cover h1.title { border: 0; font-size: 36pt; page-break-before: avoid; margin: 8px 0 8px; line-height: 1.1; }
.cover h1.title code { white-space: nowrap; }
.cover .subtitle { font-size: 15pt; color: #4b5563; margin: 0 0 24px; }
.coverbox { background: #eff6ff; border-left: 5px solid #2563eb; padding: 10px 16px; margin: 18px 0; border-radius: 4px; font-size: 10.5pt; }
.how { font-size: 11pt; }
.toc { page-break-after: always; } .toc h2 { margin-top: 0; font-size: 18pt; }
.toc ol { list-style: none; margin: 0; } .toc li { padding: 5px 0; border-bottom: 1px solid #e5e7eb; font-size: 11.5pt; }
.toc a { color: #1f2937; text-decoration: none; } .toc span { display: inline-block; width: 28px; color: #2563eb; font-weight: 700; }
table.t { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.2pt; }
table.t th { background: #1e3a8a; color: #fff; text-align: left; padding: 5px 8px; }
table.t td { border-bottom: 1px solid #e5e7eb; padding: 5px 8px; vertical-align: top; }
table.t tr:nth-child(even) td { background: #f9fafb; } table.t tr { break-inside: avoid; }
table.dec { font-size: 7.8pt; } table.dec td, table.dec th { padding: 3px 6px; } table.dec td:first-child { font-weight: 600; }
table.gloss td:first-child { width: 28%; white-space: nowrap; }
.code { margin: 10px 0; border: 1px solid #d1d5db; border-radius: 6px; overflow: hidden; break-inside: avoid; }
.code.long { break-inside: auto; }
.code .cap { background: #e5e7eb; font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; padding: 3px 10px; color: #374151; }
.code pre { margin: 0; padding: 8px 10px; background: #fbfbfb; font-family: "DejaVu Sans Mono", monospace; font-size: 7.6pt; line-height: 1.38; white-space: pre-wrap; word-break: break-word; }
.callout { margin: 12px 0; padding: 8px 14px; border-radius: 6px; border-left: 5px solid; break-inside: avoid; font-size: 9.8pt; }
.callout .ct { font-weight: 700; margin-bottom: 2px; }
.callout.decision { background: #eef2ff; border-color: #4f46e5; } .callout.decision .ct { color: #3730a3; }
.callout.tip { background: #ecfdf5; border-color: #10b981; } .callout.tip .ct { color: #047857; }
.callout.warn { background: #fffbeb; border-color: #f59e0b; } .callout.warn .ct { color: #b45309; }
figure.diagram { margin: 12px 0; text-align: center; break-inside: avoid; }
figure.diagram svg { width: 100%; height: auto; max-height: 215mm; }
.bx { stroke-width: 1.6; } .bx.plain { fill: #f9fafb; stroke: #9ca3af; } .bx.io { fill: #eef2ff; stroke: #6366f1; }
.bx.door { fill: #fff7ed; stroke: #f97316; } .bx.brain { fill: #e0f2fe; stroke: #0284c7; stroke-width: 2.6; }
.bx.face { fill: #ecfdf5; stroke: #10b981; } .bx.fx { fill: #fdf2f8; stroke: #ec4899; } .bx.disk { fill: #f3f4f6; stroke: #6b7280; stroke-dasharray: 5 3; }
.bt { font-size: 13px; font-weight: 700; fill: #111827; } .bs { font-size: 10.5px; fill: #374151; }
.lb { font-size: 11px; fill: #374151; } .lbd { font-size: 11px; fill: #6b7280; } .lbw { font-size: 12px; fill: #fff; font-weight: 700; }
.ar { fill: none; stroke: #4b5563; stroke-width: 2; } .ar.dash { stroke-dasharray: 6 5; } .ar.blue { stroke: #2563eb; }
"""
)


TITLES = {"en": "How raffle-cli was built", "es": "Cómo se construyó raffle-cli"}


def render() -> str:
    return (
        f'<!doctype html><html lang="{LANG}"><head><meta charset="utf-8"><title>{TITLES[LANG]}</title>'
        f"<style>{CSS}</style></head><body>{''.join(P)}</body></html>"
    )
