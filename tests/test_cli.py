import asyncio
import random

from typer.testing import CliRunner

from raffle_cli import app, files
from raffle_cli.fireworks import Fireworks
from raffle_cli.raffle import Participant, Prize, Raffle

runner = CliRunner()


def setup_event(tmp_path, *extra):
    cfg = tmp_path / "config.yaml"
    result = runner.invoke(app, ["setup", "--config", str(cfg), *extra])
    assert result.exit_code == 0, result.output
    return cfg


def test_setup_does_not_start_a_raffle(tmp_path):
    cfg = setup_event(tmp_path)
    assert cfg.exists() and "Game starting" not in runner.invoke(app, ["setup", "-c", str(cfg)]).output


def test_full_run_saves_winners_and_is_reproducible(tmp_path):
    cfg = setup_event(tmp_path)
    args = ["--config", str(cfg), "--yes", "--fast", "--no-fireworks", "--seed", "7"]
    first = runner.invoke(app, args)
    assert first.exit_code == 0, first.output
    saved = files.read_winners(tmp_path / "winners.csv")
    assert len(saved) == 6  # 3 + 1 + 2 sample prizes
    # recreate_from_winners is true: a second run resumes and has nothing left to do
    again = runner.invoke(app, args)
    assert again.exit_code == 0 and "Resuming" in again.output
    assert files.read_winners(tmp_path / "winners.csv") == saved


def test_fresh_run_when_not_resuming(tmp_path):
    cfg = setup_event(tmp_path)
    cfg.write_text(cfg.read_text().replace("recreate_from_winners: true", "recreate_from_winners: false"))
    args = ["--config", str(cfg), "--yes", "--fast", "--no-fireworks"]
    assert runner.invoke(app, args).exit_code == 0
    assert runner.invoke(app, args).exit_code == 0
    assert len(files.read_winners(tmp_path / "winners.csv")) == 6
    assert (tmp_path / "winners.csv.bak").exists()


def test_more_prizes_than_people_works(tmp_path):
    cfg = setup_event(tmp_path)
    (tmp_path / "participants.csv").write_text("name,lastname\nSolo,Dolo\n")
    result = runner.invoke(app, ["-c", str(cfg), "--yes", "--fast", "--no-fireworks"])
    assert result.exit_code == 0, result.output
    assert len(files.read_winners(tmp_path / "winners.csv")) == 6


def test_bad_files_give_clear_errors_not_tracebacks(tmp_path):
    cfg = setup_event(tmp_path)
    (tmp_path / "prizes.csv").write_text("item,qty\nMug,zero\n")
    result = runner.invoke(app, ["-c", str(cfg), "--yes"])
    assert result.exit_code == 1 and "prizes.csv" in result.output and "qty must be" in result.output


def test_missing_config_non_interactive(tmp_path):
    result = runner.invoke(app, ["-c", str(tmp_path / "nope.yaml"), "--yes"])
    assert result.exit_code == 1 and "raffle-cli setup" in result.output


def test_invalid_order(tmp_path):
    cfg = setup_event(tmp_path)
    assert runner.invoke(app, ["-c", str(cfg), "--yes", "--order", "wat"]).exit_code == 1


def test_version():
    assert "raffle-cli" in runner.invoke(app, ["--version"]).output


def test_fireworks_simulation_and_render():
    show = Fireworks(60, 20, random.Random(1), title="WIN", captions=["Ada · Laptop"])
    for _ in range(120):
        show.step()
    text = show.render()
    lines = text.plain.split("\n")
    assert len(lines) == 20 and all(len(line) == 60 for line in lines)
    assert "WIN" in text.plain and "Ada" in text.plain
    assert all(-1 <= s.x <= 60 for s in show.sparks)


def test_tui_draws_everything_and_persists():
    from raffle_cli.tui import FireworksScreen, RaffleApp

    raffle = Raffle([Participant("A", "A"), Participant("B", "B")], [Prize("Mug", 2), Prize("Pen", 1)], rng=random.Random(0))
    saved = []

    async def go():
        app_ = RaffleApp(raffle, saved.append, seed=0, fast=True)
        async with app_.run_test(size=(100, 30)) as pilot:
            for _ in range(3):
                await pilot.press("enter")
                await pilot.pause(1.0)
            await pilot.pause(1.2)
            assert isinstance(app_.screen, FireworksScreen)
            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app_.screen, FireworksScreen)

    asyncio.run(go())
    assert raffle.done and saved == raffle.winners and len(saved) == 3


def test_finished_raffle_explains_how_to_start_over(tmp_path):
    cfg = setup_event(tmp_path)
    args = ["-c", str(cfg), "--yes", "--fast", "--no-fireworks"]
    runner.invoke(app, args)
    assert "already been awarded" in runner.invoke(app, args).output


def test_tui_missing_extra_message_is_not_eaten_by_markup(tmp_path, monkeypatch):
    import sys
    cfg = setup_event(tmp_path)
    monkeypatch.setitem(sys.modules, "raffle_cli.tui", None)  # simulate textual not installed
    out = runner.invoke(app, ["-c", str(cfg), "--yes", "--tui"]).output
    assert "raffle-cli[tui]" in out and "--with textual" in out



def test_tui_lever_click_draws_and_layout_is_responsive():
    from raffle_cli.slot import SlotMachine
    from raffle_cli.tui import RaffleApp

    people = [Participant("Ada", "Lovelace"), Participant("Guido", "van Rossum")]
    raffle = Raffle(people, [Prize("Mug", 2)], rng=random.Random(0))
    saved = []

    async def go():
        app_ = RaffleApp(raffle, saved.append, seed=0, fast=True, show_fireworks=False)
        async with app_.run_test(size=(140, 40)) as pilot:
            main = app_.query_one("#main")
            assert main.has_class("wide")
            await pilot.click(SlotMachine)  # mouse pulls the lever
            await pilot.pause(1.0)
            assert len(saved) == 1
            machine = app_.query_one(SlotMachine)
            assert [r.landed for r in machine.reels] == [True, True]
            assert [r.strip[r.pos] for r in machine.reels] == [saved[0].name, saved[0].lastname]
            assert machine.lever == 0
            await pilot.resize_terminal(90, 30)
            await pilot.pause()
            assert not main.has_class("wide")

    asyncio.run(go())


def test_tui_animation_leaves_the_seeded_draw_untouched():
    from raffle_cli.tui import RaffleApp

    people = [Participant(f"P{i}", "X") for i in range(6)]

    def winners(use_tui):
        raffle = Raffle(people, [Prize("Mug", 3)], rng=random.Random(99))
        if not use_tui:
            while not raffle.done:
                raffle.draw()
            return raffle.winners

        async def go():
            app_ = RaffleApp(raffle, lambda w: None, seed=99, fast=True, show_fireworks=False)
            async with app_.run_test(size=(100, 30)) as pilot:
                for _ in range(3):
                    await pilot.press("enter")
                    await pilot.pause(1.0)

        asyncio.run(go())
        return raffle.winners

    assert winners(True) == winners(False)
