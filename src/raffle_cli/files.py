"""CSV reading, validation and writing."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

from .raffle import Participant, Prize, Winner

PARTICIPANT_COLUMNS = ("name", "lastname")
PRIZE_COLUMNS = ("item", "qty")
WINNER_COLUMNS = ("name", "lastname", "item")

SAMPLE_PARTICIPANTS = [
    ("Ada", "Lovelace"), ("Grace", "Hopper"), ("Guido", "van Rossum"),
    ("Margaret", "Hamilton"), ("Linus", "Torvalds"), ("Katherine", "Johnson"),
]
SAMPLE_PRIZES = [("Laptop sticker pack", 3), ("Mechanical keyboard", 1), ("Python mug", 2)]


class DataFileError(Exception):
    """A work file is missing or invalid; `problems` lists everything wrong with it."""

    def __init__(self, path: Path, problems: list[str]) -> None:
        self.path = path
        self.problems = problems
        super().__init__(f"{path.name}: " + "; ".join(problems))


def _read_rows(path: Path, columns: tuple[str, ...]) -> list[tuple[int, dict[str, str]]]:
    """Read `path`, check its header and return (line_number, stripped_row) pairs."""
    if not path.exists():
        raise DataFileError(path, [f"file not found ({path}). Run `raffle-cli setup` to create it."])
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = [h.strip().lower() for h in (reader.fieldnames or [])]
        if not header:
            raise DataFileError(path, [f"missing header row, expected: {','.join(columns)}"])
        if set(header) != set(columns) or len(header) != len(columns):
            raise DataFileError(
                path, [f"expected columns {','.join(columns)} but found {','.join(header)}"]
            )
        reader.fieldnames = header
        rows = []
        for row in reader:
            clean = {k: (v or "").strip() for k, v in row.items() if k is not None}
            if any(clean.values()):
                rows.append((reader.line_num, clean))
    return rows


def read_participants(path: Path) -> tuple[list[Participant], list[str]]:
    """Return (participants, warnings). Duplicate names are allowed but reported."""
    problems: list[str] = []
    people: list[Participant] = []
    seen: dict[tuple[str, str], int] = {}
    warnings: list[str] = []
    for line, row in _read_rows(path, PARTICIPANT_COLUMNS):
        if not row["name"] or not row["lastname"]:
            problems.append(f"line {line}: name and lastname are both required")
            continue
        key = (row["name"].casefold(), row["lastname"].casefold())
        if key in seen:
            warnings.append(
                f"{path.name} line {line}: '{row['name']} {row['lastname']}' "
                f"also appears on line {seen[key]} (they will have two chances)"
            )
        seen.setdefault(key, line)
        people.append(Participant(row["name"], row["lastname"]))
    if not problems and not people:
        problems.append("no participants found")
    if problems:
        raise DataFileError(path, problems)
    return people, warnings


def read_prizes(path: Path) -> list[Prize]:
    problems: list[str] = []
    prizes: list[Prize] = []
    for line, row in _read_rows(path, PRIZE_COLUMNS):
        if not row["item"]:
            problems.append(f"line {line}: item is required")
            continue
        try:
            qty = int(row["qty"])
        except ValueError:
            problems.append(f"line {line}: qty must be a whole number, got '{row['qty']}'")
            continue
        if qty < 1:
            problems.append(f"line {line}: qty must be at least 1, got {qty}")
            continue
        prizes.append(Prize(row["item"], qty))
    if not problems and not prizes:
        problems.append("no prizes found")
    if problems:
        raise DataFileError(path, problems)
    return prizes


def read_winners(path: Path) -> list[Winner]:
    """Read previous winners; a missing file means nobody has won yet."""
    if not path.exists():
        return []
    problems: list[str] = []
    winners: list[Winner] = []
    for line, row in _read_rows(path, WINNER_COLUMNS):
        if not all(row[c] for c in WINNER_COLUMNS):
            problems.append(f"line {line}: name, lastname and item are all required")
            continue
        winners.append(Winner(row["name"], row["lastname"], row["item"]))
    if problems:
        raise DataFileError(path, problems)
    return winners


def _write(path: Path, columns: tuple[str, ...], rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        writer.writerows(rows)


def write_participants(path: Path, people: list[tuple[str, str]]) -> None:
    _write(path, PARTICIPANT_COLUMNS, people)


def write_prizes(path: Path, prizes: list[tuple[str, int]]) -> None:
    _write(path, PRIZE_COLUMNS, prizes)


def reset_winners(path: Path, winners: list[Winner] = ()) -> None:
    """Start `path` afresh, keeping a `.bak` copy of any previous results."""
    if path.exists() and len(path.read_text(encoding="utf-8-sig").strip().splitlines()) > 1:
        shutil.copyfile(path, path.with_name(path.name + ".bak"))
    _write(path, WINNER_COLUMNS, [(w.name, w.lastname, w.item) for w in winners])


def append_winner(path: Path, winner: Winner) -> None:
    """Persist one winner immediately, so a crash mid-event loses nothing."""
    if not path.exists():
        reset_winners(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow((winner.name, winner.lastname, winner.item))
