"""Big ASCII-art names for the Textual roulette (uses pyfiglet, part of the `tui` extra)."""

from __future__ import annotations

import unicodedata
from functools import lru_cache

from pyfiglet import Figlet

# Biggest first; the first one that fits the available space wins.
FONTS = ("ansi_shadow", "big", "standard", "small", "mini")


def _ascii(text: str) -> str:
    """figlet can't draw accents (José -> Jos), so fold them away first."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


@lru_cache(maxsize=2048)
def _render(text: str, font: str) -> tuple[str, ...]:
    raw = Figlet(font=font, width=1000).renderText(_ascii(text))
    lines = [line.rstrip() for line in raw.split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    if not lines:
        return ()
    width = max(map(len, lines))
    return tuple(line.ljust(width) for line in lines)


def big_name(name: str, lastname: str, width: int, height: int) -> list[str] | None:
    """Largest rendering of the name that fits `width` x `height`, or None to fall back to plain text.

    Tries one line ("Ada Lovelace") first, then two stacked lines, for each font from big to small.
    """
    for font in FONTS:
        single = _render(f"{name} {lastname}", font)
        if single and len(single[0]) <= width and len(single) <= height:
            return list(single)
        top, bottom = _render(name, font), _render(lastname, font)
        if top and bottom:
            block_width = max(len(top[0]), len(bottom[0]))
            if block_width <= width and len(top) + len(bottom) + 1 <= height:
                pad = lambda rows: [row.ljust(block_width) for row in rows]  # noqa: E731
                return pad(top) + [" " * block_width] + pad(bottom)
    return None
