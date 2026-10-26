"""An animated slot machine for the Textual interface: two reels (name, lastname) and a lever."""

from __future__ import annotations

import random
from typing import Callable, Sequence

from rich.text import Text
from textual.message import Message
from textual.widget import Widget

from .raffle import Participant, Winner

LEVER_BALL_ROW = {0: 1, 1: 3, 2: 5}  # lever up / halfway / pulled
LEVER_BASE_ROW = 6
HEIGHT = 7


class Reel:
    def __init__(self, strip: list[str]) -> None:
        self.strip = strip
        self.pos = 1  # index of the name in the middle row
        self.target = 1
        self.landed = False


class SlotMachine(Widget):
    """Click it (or press Enter in the app) to pull the lever."""

    class Pulled(Message):
        """The user clicked the machine."""

    DEFAULT_CSS = "SlotMachine { height: 7; }"

    def __init__(self, participants: Sequence[Participant], *, fast: bool = False, id: str | None = None) -> None:
        super().__init__(id=id)
        self.fast = fast
        self.rng = random.Random()  # cosmetic only: never touch the raffle's own rng (keeps --seed reproducible)
        self.pools = [
            sorted({p.name for p in participants}),
            sorted({p.lastname for p in participants}),
        ]
        longest = max(len(s) for pool in self.pools for s in pool)
        self.cell = max(8, min(12, longest))
        self.lever = 0
        self.reels = [Reel(self._random_strip(i, 3)) for i in range(2)]
        self._pending = 0
        self._on_done: Callable[[], None] | None = None
        self.styles.width = 2 * (self.cell + 4) + 1 + 2 + 4  # borders + room for the lever
        self.styles.height = HEIGHT

    # --- animation ------------------------------------------------------
    def _random_strip(self, reel: int, length: int) -> list[str]:
        pool, strip = self.pools[reel], []
        for _ in range(length):
            choice = self.rng.choice(pool)
            if len(pool) > 1:
                while strip and choice == strip[-1]:
                    choice = self.rng.choice(pool)
            strip.append(choice)
        return strip

    def pull(self, winner: Winner, on_done: Callable[[], None]) -> None:
        """Pull the lever; `on_done` runs once both reels have landed on `winner`."""
        self._on_done = on_done
        step = 0.02 if self.fast else 0.09
        self._set_lever(1)
        self.set_timer(step, lambda: self._set_lever(2))
        self.set_timer(2 * step, lambda: self._start_reels(winner))
        self.set_timer(3 * step, lambda: self._set_lever(1))
        self.set_timer(4 * step, lambda: self._set_lever(0))

    def _set_lever(self, state: int) -> None:
        self.lever = state
        self.refresh()

    def _start_reels(self, winner: Winner) -> None:
        self._pending = len(self.reels)
        for i, part in enumerate((winner.name, winner.lastname)):
            steps = (3 if self.fast else 18) + i * (2 if self.fast else 12)  # the right reel spins longer
            strip = self._random_strip(i, steps + 2)
            strip[steps] = part
            for neighbour in (steps - 1, steps + 1):  # never show the winner's own name next to it
                alternatives = [x for x in self.pools[i] if x != part]
                if strip[neighbour] == part and alternatives:
                    strip[neighbour] = self.rng.choice(alternatives)
            reel = self.reels[i]
            reel.strip, reel.pos, reel.target, reel.landed = strip, 1, steps, False
            self._advance(i)

    def _advance(self, i: int) -> None:
        reel = self.reels[i]
        reel.pos += 1
        if reel.pos >= reel.target:
            reel.landed = True
            self._pending -= 1
            self.refresh()
            if self._pending == 0 and self._on_done:
                self.set_timer(0.05 if self.fast else 0.5, self._on_done)
            return
        self.refresh()
        # slow down like a real machine: 40ms per row at first, ~320ms for the last rows
        delay = 0.02 if self.fast else 0.04 + 0.28 * (reel.pos / reel.target) ** 3
        self.set_timer(delay, lambda: self._advance(i))

    def on_click(self) -> None:
        self.post_message(self.Pulled())

    # --- drawing --------------------------------------------------------
    def _fit(self, text: str) -> str:
        return text if len(text) <= self.cell else text[: self.cell - 1] + "…"

    def _cell(self, reel: Reel, offset: int) -> Text:
        label = self._fit(reel.strip[reel.pos + offset]).center(self.cell)
        if offset:
            return Text(f"  {label}  ", style="dim")
        style = "bold green on grey23" if reel.landed else "bold white on grey23"
        return Text(f"▶ {label} ◀", style=style)

    def _lever(self, row: int) -> Text:
        ball = LEVER_BALL_ROW[self.lever]
        if row == ball:
            return Text(" ●", style="bold red")
        if row == LEVER_BASE_ROW:
            return Text(" ┻", style="yellow")
        if ball < row < LEVER_BASE_ROW:
            return Text(" ┃", style="yellow")
        return Text("")

    def render(self) -> Text:
        width = self.cell + 4
        inner = 2 * width + 1
        border = "yellow"
        lines: list[Text] = [
            Text("╔" + "═" * inner + "╗", style=border),
            Text.assemble(("║", border), ("★  RAFFLE-CLI  ★".center(inner), "bold gold1"), ("║", border)),
            Text("╠" + "═" * width + "╦" + "═" * width + "╣", style=border),
        ]
        for offset in (-1, 0, 1):
            lines.append(
                Text.assemble(
                    ("║", border), self._cell(self.reels[0], offset), ("║", border),
                    self._cell(self.reels[1], offset), ("║", border),
                )
            )
        lines.append(Text("╚" + "═" * width + "╩" + "═" * width + "╝", style=border))
        out = Text()
        for row, line in enumerate(lines):
            out.append_text(line)
            out.append_text(self._lever(row))
            if row < len(lines) - 1:
                out.append("\n")
        return out
