"""A little terminal fireworks show for the grand finale.

`Fireworks` is a tiny particle simulation that renders to a `rich.text.Text`, so the same
show can run in a plain terminal (`play`) or inside the Textual interface.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from rich.console import Console
from rich.live import Live
from rich.text import Text

PALETTE = ["red1", "orange1", "yellow1", "green1", "cyan1", "dodger_blue1", "magenta", "hot_pink", "gold1", "white"]
ASPECT = 2.0  # terminal cells are about twice as tall as they are wide
GRAVITY = 0.035
DRAG = 0.9


@dataclass
class Spark:
    x: float
    y: float
    vx: float
    vy: float
    ttl: int
    color: str
    life: int = 0

    def __post_init__(self) -> None:
        self.life = self.ttl


@dataclass
class Rocket:
    x: float
    y: float
    vy: float
    apex: float
    color: str


class Fireworks:
    def __init__(
        self,
        width: int,
        height: int,
        rng: random.Random | None = None,
        *,
        title: str = "",
        captions: tuple[str, ...] | list[str] = (),
        launch_rate: float = 0.2,
        caption_ticks: int = 40,
    ) -> None:
        self.width, self.height = width, height
        self.rng = rng or random.Random()
        self.title = title
        self.captions = list(captions)
        self.launch_rate = launch_rate
        self.caption_ticks = caption_ticks
        self.tick = 0
        self.sparks: list[Spark] = []
        self.rockets: list[Rocket] = []

    # --- simulation -----------------------------------------------------
    def step(self) -> None:
        self.tick += 1
        if self.rng.random() < self.launch_rate:
            self._launch()
        for rocket in self.rockets[:]:
            rocket.y += rocket.vy
            self.sparks.append(Spark(rocket.x, rocket.y + 1, 0, 0, 5, "orange3"))
            if rocket.y <= rocket.apex:
                self.rockets.remove(rocket)
                self._explode(rocket)
        for s in self.sparks[:]:
            s.x += s.vx
            s.y += s.vy
            s.vx *= DRAG
            s.vy = s.vy * DRAG + GRAVITY
            s.life -= 1
            if s.life <= 0 or not (-1 <= s.x <= self.width and -1 <= s.y <= self.height):
                self.sparks.remove(s)

    def _launch(self) -> None:
        self.rockets.append(
            Rocket(
                x=self.rng.uniform(0.1, 0.9) * self.width,
                y=self.height - 1,
                vy=-self.rng.uniform(0.9, 1.4),
                apex=self.rng.uniform(0.1, 0.5) * self.height,
                color=self.rng.choice(PALETTE),
            )
        )

    def _explode(self, rocket: Rocket) -> None:
        rng = self.rng
        count = rng.randint(30, 55)
        shape = rng.choice(["ring", "burst"])
        colors = [rocket.color] if rng.random() < 0.6 else [rocket.color, rng.choice(PALETTE)]
        ttl = rng.randint(14, 24)
        for i in range(count):
            angle = 2 * math.pi * i / count
            speed = 0.75 if shape == "ring" else rng.uniform(0.25, 0.8)
            self.sparks.append(
                Spark(
                    rocket.x,
                    rocket.y,
                    math.cos(angle) * speed * ASPECT,
                    math.sin(angle) * speed,
                    ttl + rng.randint(-3, 3),
                    rng.choice(colors),
                )
            )

    # --- rendering ------------------------------------------------------
    def resize(self, width: int, height: int) -> None:
        self.width, self.height = width, height

    def _caption(self) -> str:
        if not self.captions:
            return ""
        return self.captions[(self.tick // self.caption_ticks) % len(self.captions)]

    def render(self) -> Text:
        w, h = max(self.width, 1), max(self.height, 1)
        grid: list[list[tuple[str, str]]] = [[(" ", "")] * w for _ in range(h)]
        for rocket in self.rockets:
            self._plot(grid, rocket.x, rocket.y, "|", "bold white")
        for s in self.sparks:
            ratio = s.life / s.ttl
            char = "*" if ratio > 0.66 else "+" if ratio > 0.33 else "."
            style = s.color if ratio > 0.33 else f"dim {s.color}"
            self._plot(grid, s.x, s.y, char, style)
        if self.tick > 12:
            self._overlay(grid, h // 2 - 1, f"★  {self.title}  ★" if self.title else "", "bold gold1 on dark_red")
            self._overlay(grid, h // 2 + 1, self._caption(), "bold white on dark_blue")

        text = Text(no_wrap=True, overflow="crop")
        for r, row in enumerate(grid):
            run, style = "", None
            for char, st in row:
                if st != style and run:
                    text.append(run, style=style or None)
                    run = ""
                run, style = run + char, st
            text.append(run, style=style or None)
            if r < h - 1:
                text.append("\n")
        return text

    @staticmethod
    def _plot(grid: list[list[tuple[str, str]]], x: float, y: float, char: str, style: str) -> None:
        col, row = int(round(x)), int(round(y))
        if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
            grid[row][col] = (char, style)

    @staticmethod
    def _overlay(grid: list[list[tuple[str, str]]], row: int, message: str, style: str) -> None:
        if not message or not (0 <= row < len(grid)):
            return
        width = len(grid[0])
        message = f" {message} "[:width]
        start = (width - len(message)) // 2
        for i, char in enumerate(message):
            grid[row][start + i] = (char, style)


def play(
    console: Console,
    *,
    seconds: float = 8.0,
    fps: int = 20,
    title: str = "CONGRATULATIONS",
    captions: list[str] | tuple[str, ...] = (),
    rng: random.Random | None = None,
) -> None:
    """Run the show full-screen. Ctrl+C skips it. Does nothing when not attached to a terminal."""
    if not console.is_terminal:
        return
    width, height = console.size
    show = Fireworks(width, height, rng, title=title, captions=captions)
    for _ in range(8):
        show._launch()
    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            for _ in range(int(seconds * fps)):
                show.resize(*console.size)
                show.step()
                live.update(show.render(), refresh=True)
                time.sleep(1 / fps)
    except KeyboardInterrupt:
        pass
