"""Command line entry points (Typer)."""

from __future__ import annotations

import random
import secrets
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markup import escape
from typing_extensions import Annotated

from . import __version__, fireworks, ui
from .config import DEFAULT_CONFIG, ConfigError, RaffleConfig, load_config, setup_files
from .files import DataFileError, append_winner, read_participants, read_prizes, read_winners, reset_winners
from .raffle import ORDERS, Raffle

app = typer.Typer(help="Run a transparent raffle for your meetup giveaways.", add_completion=False)
console = Console()

ConfigOption = Annotated[
    Optional[Path],
    typer.Option("--config", "-c", help=f"Path to the config .yaml file (default: ./{DEFAULT_CONFIG})."),
]


def fail(message: str) -> typer.Exit:
    console.print(f"[bold red]Error:[/] {message}")
    return typer.Exit(1)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"raffle-cli {__version__}")
        raise typer.Exit()


def build_raffle(config_path: Path, seed: int, order: str, interactive: bool) -> tuple[Raffle, RaffleConfig]:
    """Load everything, validate it and return a ready-to-run raffle."""
    if not config_path.exists():
        console.print(f"[bold]Ups[/], {config_path} does not exist.")
        if not interactive or not typer.confirm("Create a sample setup here?", default=True):
            raise fail("Run `raffle-cli setup` to create a config and sample files.")
        report_setup(setup_files(config_path))
    try:
        cfg = load_config(config_path)
        participants, warnings = read_participants(cfg.participants_file)
        prizes = read_prizes(cfg.prizes_file)
        previous = read_winners(cfg.winners_file) if cfg.recreate_from_winners else []
    except ConfigError as exc:
        raise fail(str(exc))
    except DataFileError as exc:
        lines = "\n".join(f"  • {escape(p)}" for p in exc.problems)
        raise fail(f"[bold]{escape(str(exc.path))}[/] needs attention:\n{lines}")
    for warning in warnings:
        console.print(f"[yellow]Warning:[/] {escape(warning)}")
    try:
        raffle = Raffle(participants, prizes, previous_winners=previous, rng=random.Random(seed), order=order)
    except ValueError as exc:
        raise fail(str(exc))
    if previous:
        console.print(f"[cyan]Resuming:[/] {len(previous)} prize(s) already awarded in {cfg.winners_file.name}.")
        if raffle.done:
            console.print(
                "[yellow]Every prize has already been awarded.[/] For a fresh raffle, set "
                f"`recreate_from_winners: false` in {config_path.name} or delete {cfg.winners_file.name}."
            )
    else:
        reset_winners(cfg.winners_file)
    return raffle, cfg


def report_setup(results: list[tuple[Path, str]]) -> None:
    for path, state in results:
        console.print(f"  {'✅' if state != 'kept' else '➖'} {state:<11} {path}")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config: ConfigOption = None,
    seed: Annotated[Optional[int], typer.Option(help="Seed the draw so it can be reproduced. Shown in the results.")] = None,
    order: Annotated[str, typer.Option(help=f"Order prizes are raffled: {', '.join(ORDERS)}.")] = "high-low",
    fast: Annotated[bool, typer.Option("--fast", help="Skip the suspense delays.")] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Never wait for Enter (non-interactive).")] = False,
    fireworks_flag: Annotated[bool, typer.Option("--fireworks/--no-fireworks", help="Finish with fireworks.")] = True,
    tui: Annotated[bool, typer.Option("--tui", help="Use the full-screen Textual interface.")] = False,
    version: Annotated[bool, typer.Option("--version", callback=version_callback, is_eager=True, help="Show the version.")] = False,
) -> None:
    """Run the raffle (or a subcommand)."""
    ctx.obj = {"config": config}
    if ctx.invoked_subcommand is not None:
        return
    if order not in ORDERS:
        raise fail(f"--order must be one of: {', '.join(ORDERS)}.")
    seed = secrets.randbits(32) if seed is None else seed
    raffle, cfg = build_raffle(config or DEFAULT_CONFIG, seed, order, interactive=not yes)

    def save(winner) -> None:
        append_winner(cfg.winners_file, winner)

    if tui:
        try:
            from .tui import RaffleApp
        except ImportError:
            raise fail(
                "The Textual interface needs the [bold]tui[/] extra: "
                + escape("pip install 'raffle-cli[tui]'")
                + " (with uvx: add [bold]--with textual --with pyfiglet[/])"
            )
        RaffleApp(raffle, save, seed=seed, fast=fast, show_fireworks=fireworks_flag).run()
        ui.show_results(console, raffle.winners, seed)
    else:
        ui.run(raffle, console, save, seed=seed, fast=fast, auto=yes, show_fireworks=fireworks_flag)
    console.print(f"\nResults saved to [bold]{cfg.winners_file}[/]. Reproduce this draw order with [bold]--seed {seed}[/].")


@app.command()
def setup(
    ctx: typer.Context,
    config: ConfigOption = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite files that already exist.")] = False,
    empty: Annotated[bool, typer.Option("--empty", help="Create header-only CSVs instead of sample data.")] = False,
) -> None:
    """Create a config.yaml and its CSV files."""
    path = config or (ctx.obj or {}).get("config") or DEFAULT_CONFIG
    try:
        report_setup(setup_files(path, force=force, samples=not empty))
    except ConfigError as exc:
        raise fail(str(exc))
    console.print("\nEdit the CSV files, then run [bold]raffle-cli[/].")


@app.command("fireworks")
def fireworks_demo(seconds: Annotated[float, typer.Option(help="How long to run the show.")] = 8.0) -> None:
    """Preview the fireworks finale."""
    fireworks.play(console, seconds=seconds, captions=["Ada Lovelace  ·  Laptop", "Guido van Rossum  ·  Keyboard"])


def main_cli() -> None:
    app()
