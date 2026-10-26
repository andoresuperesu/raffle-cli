"""Full-screen Textual interface (`raffle-cli --tui`). Needs the `tui` extra."""

from __future__ import annotations

from typing import Callable

from rich.console import Group, RenderableType
from rich.markup import escape
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, Static

from .bigtext import big_name
from .fireworks import Fireworks
from .raffle import Participant, Raffle, Winner


class FireworksScreen(Screen):
    BINDINGS = [("escape,enter,space,q", "app.pop_screen", "Close")]

    def __init__(self, winners: list[Winner]) -> None:
        super().__init__()
        self._captions = [f"{w.full_name}  ·  {w.item}" for w in winners]
        self._show: Fireworks | None = None

    def compose(self) -> ComposeResult:
        yield Static(id="sky")

    def on_mount(self) -> None:
        self._show = Fireworks(self.size.width, self.size.height, title="CONGRATULATIONS", captions=self._captions)
        for _ in range(8):
            self._show._launch()
        self.set_interval(1 / 20, self._tick)

    def _tick(self) -> None:
        assert self._show is not None
        self._show.resize(self.size.width, self.size.height)
        self._show.step()
        self.query_one("#sky", Static).update(self._show.render())


class RaffleApp(App):
    TITLE = "raffle-cli"
    CSS = """
    #tables { height: 12; }
    #tables > Vertical { width: 1fr; padding: 0 1; }
    #stage { height: 1fr; min-height: 12; content-align: center middle; text-align: center; border: round $accent; margin: 0 1; }
    """
    BINDINGS = [
        Binding("enter,space", "draw", "Draw next", priority=True),  # tables would otherwise swallow the key
        ("f", "fireworks", "Fireworks"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        raffle: Raffle,
        on_winner: Callable[[Winner], None],
        *,
        seed: int | None = None,
        fast: bool = False,
        show_fireworks: bool = True,
    ) -> None:
        super().__init__()
        self.raffle = raffle
        self.on_winner = on_winner
        self.fast = fast
        self.show_fireworks = show_fireworks
        self.sub_title = f"seed {seed}" if seed is not None else ""
        self._busy = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="tables"):
            with Vertical():
                yield Label("[b]Prizes left[/]")
                yield DataTable(id="prizes", show_cursor=False)
            with Vertical():
                yield Label("[b]Winners[/]")
                yield DataTable(id="winners", show_cursor=False)
        yield Static(id="stage")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#prizes", DataTable).add_columns("item", "qty")
        self.query_one("#winners", DataTable).add_columns("name", "lastname", "item")
        self._refresh()

    # --- helpers --------------------------------------------------------
    def _stage(self, content: RenderableType) -> None:
        self.query_one("#stage", Static).update(content)

    def _name_art(self, who: Participant | Winner, style: str, reserve: int) -> RenderableType:
        """The person's name in big letters, sized to fill the stage (plain bold text if nothing fits)."""
        stage = self.query_one("#stage", Static)
        art = big_name(who.name, who.lastname, stage.size.width - 4, stage.size.height - reserve)
        if art is None:
            return Text(who.full_name, style=f"bold {style}", justify="center")
        return Text("\n".join(art), style=style, justify="center", no_wrap=True)

    def _stage_name(self, headline: str, who: Participant | Winner, style: str, footer: str = "") -> None:
        parts: list[RenderableType] = [Text.from_markup(headline, justify="center"), Text("")]
        parts.append(self._name_art(who, style, reserve=5 if footer else 3))
        if footer:
            parts += [Text(""), Text.from_markup(footer, justify="center")]
        self._stage(Group(*parts))

    def _refresh(self) -> None:
        prizes = self.query_one("#prizes", DataTable)
        prizes.clear()
        for p in self.raffle.remaining:
            prizes.add_row(p.item, str(p.qty))
        winners = self.query_one("#winners", DataTable)
        winners.clear()
        for w in self.raffle.winners:
            winners.add_row(w.name, w.lastname, w.item)
        winners.scroll_end(animate=False)
        if self.raffle.done:
            self._stage("[b green]All prizes awarded![/]\n\nPress [b]f[/] to replay the fireworks, [b]q[/] to quit.")
        else:
            self._stage(f"Next prize:\n\n[b yellow]{escape(self.raffle.next_prize)}[/]\n\nPress [b]Enter[/] to draw")

    # --- actions --------------------------------------------------------
    def action_draw(self) -> None:
        if self._busy or self.raffle.done:
            return
        self._busy = True
        item = self.raffle.next_prize
        winner = self.raffle.draw()  # decided now; the spin below is just for show
        people = self.raffle.participants
        steps = 4 if self.fast else 32
        state = {"n": 0}

        def spin() -> None:
            state["n"] += 1
            if state["n"] < steps:
                who = self.raffle.rng.choice(people)
                self._stage_name(f"Drawing [b yellow]{escape(item)}[/]", who, "grey58")
                # slow down like a real roulette wheel: 50ms at first, ~350ms for the last spins
                delay = 0.05 if self.fast else 0.05 + 0.3 * (state["n"] / steps) ** 3
                self.set_timer(delay, spin)
                return
            self.on_winner(winner)
            self._refresh()
            last = "\n[dim]That was the last prize![/]" if self.raffle.done else "\n[dim]Press Enter for the next prize[/]"
            self._stage_name(f"[b yellow]{escape(item)}[/] goes to", winner, "bold green", last)
            self._busy = False
            if self.raffle.done and self.show_fireworks:
                self.set_timer(0.5 if self.fast else 3.0, self.action_fireworks)

        spin()

    def action_fireworks(self) -> None:
        if self.raffle.winners and not isinstance(self.screen, FireworksScreen):
            self.push_screen(FireworksScreen(self.raffle.winners))
