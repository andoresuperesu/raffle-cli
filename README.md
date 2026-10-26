# raffle-cli

A transparent terminal raffle for meetup giveaways (no money involved, just a fair, watchable way to give away swag), with a fireworks finale 🎆.

Built with [Typer](https://typer.tiangolo.com) and [Rich](https://github.com/Textualize/rich) (thank you @tiangolo and @willmcgugan), with an optional full-screen interface in [Textual](https://textual.textualize.io).

> 📘 **New to Python?** Read the beginner's guide, [`docs/how-raffle-cli-was-built.pdf`](docs/how-raffle-cli-was-built.pdf) (34 pages, with diagrams): how every part works, why each technical decision was made, and exercises to change the code yourself.
>
> 🤖 **Provenance:** the first prototype was written by the repo owner; version 0.2.0 (restructure, fixes, persistence, fireworks, Textual slot machine, tests, docs) was written together with [Claude](https://claude.com/claude-code). The commit trailers say so.

## Install

```bash
uv tool install git+https://github.com/andoresuperesu/raffle-cli          # classic interface
uv tool install "raffle-cli[tui] @ git+https://github.com/andoresuperesu/raffle-cli"   # + Textual interface
# or try it without installing:
uvx --from git+https://github.com/andoresuperesu/raffle-cli raffle-cli --help
# ...and with the Textual interface:
uvx --from git+https://github.com/andoresuperesu/raffle-cli --with textual raffle-cli --tui
```

Requires Python 3.10+. On Windows use [Windows Terminal](https://aka.ms/terminal); in PowerShell set variables with `$R = "..."` instead of `R="..."`. The project was developed and tested on Linux, so the full-screen interface is not verified on Windows yet.

## Quick start

```bash
mkdir my-event && cd my-event
raffle-cli setup        # creates config.yaml + sample CSVs
# edit participants.csv and prizes.csv
raffle-cli              # run the raffle
```

Press **Enter** to reveal each winner. Every winner is written to `winners.csv` the moment they are revealed, so a crash or Ctrl+C never loses results.

## Commands and options

| Command | What it does |
| --- | --- |
| `raffle-cli` | Run the raffle (classic interface). |
| `raffle-cli --tui` | Run it in the full-screen Textual interface (needs the `tui` extra). |
| `raffle-cli setup` | Create `config.yaml` and its CSV files. Existing files are kept unless you pass `--force`; use `--empty` for header-only CSVs. |
| `raffle-cli fireworks` | Preview the finale. |

Options for running a raffle:

| Option | Description |
| --- | --- |
| `-c, --config PATH` | Config file (default `./config.yaml`, any `<name>.yaml` works). |
| `--seed N` | Seed the draw. A random seed is used (and displayed in the results) if you don't pass one, so any draw can be reproduced. |
| `--order` | Order prizes are raffled: `high-low` (default), `low-high`, `shuffle`, or `file` (as listed). |
| `--fast` | Skip the suspense delays. |
| `-y, --yes` | Never wait for Enter (handy for scripts and tests). |
| `--fireworks / --no-fireworks` | Toggle the finale. |
| `--version` | Show the version. |

## Files

Relative paths in the config are resolved from the config file's folder.

`config.yaml`
```yaml
participants_file: participants.csv
prizes_file: prizes.csv
winners_file: winners.csv
recreate_from_winners: true   # true: resume from winners.csv; false: start fresh (old results saved to winners.csv.bak)
```

`participants.csv`: one row per person (a repeated name gets two chances; you'll get a warning).
```csv
name,lastname
Ada,Lovelace
```

`prizes.csv`: `qty` must be a whole number of at least 1.
```csv
item,qty
Mechanical keyboard,1
Python mug,2
```

`winners.csv` is written by the app:
```csv
name,lastname,item
```

Invalid files produce a list of every problem with line numbers, never a traceback. See [`examples/`](examples).

## How prizes are drawn

- Prizes are raffled one unit at a time, in the order given by `--order`.
- **Nobody wins a second prize until everybody has won one.** If there are more prizes than participants, the extra prizes are shared out in further rounds (and within a round nobody receives an item they already hold if there's any alternative).
- If the app stops half way, run it again with `recreate_from_winners: true` and it picks up where it left off.

## Fireworks and the Textual interface

After the last prize, the classic interface offers a full-screen fireworks show cycling through the winners (Ctrl+C skips it).

`--tui` opens a full-screen interface with prize and winner tables and an animated **slot machine**: pull the lever and the name and lastname reels spin, slow down and land on the winner one after the other. On wide terminals (120+ columns) the machine sits on the right; on narrower ones it moves to the top. Then the same fireworks play.

| Input | Action |
| --- | --- |
| **Enter / Space**, or **click the slot machine** | Pull the lever (draw the next prize) |
| **f** | Replay the fireworks |
| **q** | Quit |

## Technical decisions

The short version. The PDF guide explains each one in depth, with diagrams and the alternatives that were rejected.

| Decision | Why |
| --- | --- |
| The draw logic (`raffle.py`) is pure: no printing, no files | Both interfaces share it and it can be tested without a screen. |
| Small frozen dataclasses instead of dicts | Typos are caught early; values can't be modified by accident. |
| Draw by smallest `(wins, already_holds_item)` instead of "pick anyone, then swap" | Fair, easy to explain, can never loop forever when prizes outnumber people. |
| People are identified by position, not by name | Two people with the same name are two chances. |
| A seed is always shown; `random.Random(seed)` instead of `SystemRandom` | Anyone can reproduce and audit a draw (a receipt, not a secret). |
| The animation has its own random generator | Cosmetics can never change who wins, so `--seed` gives identical winners in both interfaces. |
| A winner is decided first, saved when revealed | The file never spoils the reveal; a crash loses nothing already announced. |
| Validation lists every problem with line numbers; files are never auto-repaired | Fix a spreadsheet in one go; real data is never overwritten. |
| Previous results are copied to `winners.csv.bak` when starting fresh | No silent data loss in front of an audience. |
| Textual is an optional extra, imported lazily | Light default install; the TUI is opt-in. |
| One fireworks simulation, rendered by Rich or Textual | No duplicated logic, no curses (works on Windows). |
| The slot machine is one custom widget animated with timers, not `sleep` loops | Frames stay consistent and the UI stays responsive to keys and mouse. |
| Plain-text names, no ASCII-art font | Long names, accents and non-Latin letters break big letters. |
| Tests drive the real apps headlessly (`CliRunner`, Textual's `Pilot`) | Keys, clicks and resizing are tested, not just functions. |

## Project layout

```
src/raffle_cli/
  raffle.py     the brain: who wins what (pure logic)
  files.py      read, validate and write the CSV files
  config.py     config.yaml loading and `setup`
  cli.py        Typer commands and options (the front door)
  ui.py         classic Rich interface
  fireworks.py  particle simulation + renderer
  tui.py        Textual app (optional extra)
  slot.py       the slot machine widget
tests/          43 tests: engine, files/config, CLI, Textual app
examples/       a ready-to-run config and CSVs
docs/           the beginner's guide (PDF) and its source (docs/guide-src/)
```

## Development

```bash
uv sync
uv run pytest
uv run raffle-cli --config examples/config.yaml --tui
```

## Contribute

PRs are welcome, thank you! The exercises at the end of the guide are good first contributions.

## License

MIT
