# raffle-cli

A transparent terminal raffle for meetup giveaways (no money involved, just a fair, watchable way to give away swag), with a fireworks finale 🎆.

Built with [Typer](https://typer.tiangolo.com) and [Rich](https://github.com/Textualize/rich) (thank you @tiangolo and @willmcgugan), with an optional full-screen interface in [Textual](https://textual.textualize.io).

## Install

```bash
uv tool install git+https://github.com/andoresuperesu/raffle-cli          # classic interface
uv tool install "raffle-cli[tui] @ git+https://github.com/andoresuperesu/raffle-cli"   # + Textual interface
# or try it without installing:
uvx --from git+https://github.com/andoresuperesu/raffle-cli raffle-cli --help
# ...and with the Textual interface:
uvx --from git+https://github.com/andoresuperesu/raffle-cli --with textual raffle-cli --tui
```

Requires Python 3.10+.

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

After the last prize, the classic interface offers a full-screen fireworks show cycling through the winners (Ctrl+C skips it). In `--tui` mode, you get prize/winner tables, a slot-machine style name spin and the same show; keys: **Enter/Space** draw, **f** fireworks, **q** quit.

## Development

```bash
uv sync
uv run pytest
```

The code lives in `src/raffle_cli/`: `raffle.py` (pure draw logic), `files.py` / `config.py` (validation and setup), `ui.py` (classic interface), `tui.py` (Textual), `fireworks.py` (particle show), `cli.py` (Typer commands).

## Contribute

PRs are welcome, thank you!

## License

MIT
