"""The classic Rich terminal interface: one prize at a time, press Enter to reveal."""

from __future__ import annotations

import time
from typing import Callable

from rich.align import Align
from rich.columns import Columns
from rich.console import Console, RenderableType
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from . import fireworks
from .raffle import Raffle, Winner


def table(headers: list[str], rows: list[tuple], empty: str) -> RenderableType:
    if not rows:
        return empty
    t = Table(show_header=True, header_style="bold magenta")
    for header in headers:
        t.add_column(header)
    for row in rows:
        t.add_row(*(escape(str(cell)) for cell in row))
    return t


def prizes_table(raffle: Raffle) -> RenderableType:
    return table(["item", "qty"], [(p.item, p.qty) for p in raffle.remaining], "No prizes left")


def winners_table(winners: list[Winner]) -> RenderableType:
    return table(["name", "lastname", "item"], [(w.name, w.lastname, w.item) for w in winners], "No winner data yet")


def title(console: Console, body: RenderableType, panel_title: str = "raffle-cli", subtitle: str = "Let's Raffle!") -> None:
    console.clear()
    console.print(Panel(Align.center(body), title=panel_title, subtitle=subtitle, title_align="left", subtitle_align="right"))


def delayed(console: Console, text: str, delay: float) -> None:
    """Print `text` one word at a time for suspense."""
    for word in text.split(" "):
        console.print(word, end=" ", markup=False, highlight=False)
        time.sleep(delay)
    console.print()


def pause(console: Console, prompt: str, auto: bool) -> None:
    if auto:
        return
    try:
        console.input(f"[dim]{prompt}[/]")
    except EOFError:  # piped stdin: carry on instead of crashing
        pass


def show_results(console: Console, winners: list[Winner], seed: int | None) -> None:
    subtitle = "Congratulations to all winners!" + (f" (seed {seed})" if seed is not None else "")
    title(console, winners_table(winners), "raffle-cli Results", subtitle)


def run(
    raffle: Raffle,
    console: Console,
    on_winner: Callable[[Winner], None],
    *,
    seed: int | None = None,
    fast: bool = False,
    auto: bool = False,
    show_fireworks: bool = True,
) -> None:
    """Run the raffle until every prize is awarded."""
    word_delay = 0.0 if fast else 0.3
    if not raffle.done:
        delayed(console, "Game starting in...", word_delay)
        delayed(console, "3 2 1 Go", 0 if fast else 1)
        time.sleep(0 if fast else 0.5)
    while not raffle.done:
        item = raffle.next_prize
        title(console, "[purple]ONGOING RAFFLE[/]", "raffle-cli", "Let's Raffle!")
        console.print(Panel(Columns([prizes_table(raffle), winners_table(raffle.winners)])))
        delayed(console, f"Next item to win is... {item}", word_delay)
        winner = raffle.draw()
        delayed(console, f"\tThe winner of {item} is.... ", word_delay)
        pause(console, "\tPress enter when ready.", auto)
        console.print(f"\t\t[bold green]{escape(winner.full_name)}[/]")
        on_winner(winner)
        if not raffle.done:
            pause(console, "Press enter to continue...", auto)

    show_results(console, raffle.winners, seed)
    if show_fireworks:
        pause(console, "\nPress enter for the finale...", auto)
        captions = [f"{w.full_name}  ·  {w.item}" for w in raffle.winners]
        fireworks.play(console, seconds=3 if fast else 10, captions=captions)
        show_results(console, raffle.winners, seed)
