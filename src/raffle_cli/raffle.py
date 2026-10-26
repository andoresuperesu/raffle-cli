"""Pure raffle logic: no I/O, no printing, easy to test."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Sequence

ORDERS = ("high-low", "low-high", "shuffle", "file")


@dataclass(frozen=True)
class Participant:
    name: str
    lastname: str

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.lastname}"


@dataclass(frozen=True)
class Prize:
    item: str
    qty: int


@dataclass(frozen=True)
class Winner:
    name: str
    lastname: str
    item: str

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.lastname}"


def order_prizes(prizes: Sequence[Prize], order: str, rng: random.Random) -> list[Prize]:
    """Return a new list of prizes sorted by `order` ('high-low', 'low-high', 'shuffle' or 'file')."""
    ordered = list(prizes)
    if order == "shuffle":
        rng.shuffle(ordered)
    elif order == "low-high":
        ordered.sort(key=lambda p: p.qty)
    elif order == "high-low":
        ordered.sort(key=lambda p: p.qty, reverse=True)
    elif order != "file":
        raise ValueError(f"Invalid order {order!r}. Choose from {', '.join(ORDERS)}.")
    return ordered


class Raffle:
    """Draws winners one prize unit at a time.

    Everybody gets a first prize before anybody gets a second one, so when there are more
    prizes than participants the extra prizes are shared out in further rounds. Within a
    round, a participant is not given an item they already hold unless there is no alternative.
    """

    def __init__(
        self,
        participants: Sequence[Participant],
        prizes: Sequence[Prize],
        *,
        previous_winners: Iterable[Winner] = (),
        rng: random.Random | None = None,
        order: str = "high-low",
    ) -> None:
        if not participants:
            raise ValueError("A raffle needs at least one participant.")
        self.rng = rng or random.Random()
        self.participants = list(participants)
        self.winners: list[Winner] = []
        self._wins = [0] * len(self.participants)
        self._held: list[set[str]] = [set() for _ in self.participants]
        self._units: list[str] = [
            p.item for p in order_prizes(prizes, order, self.rng) for _ in range(p.qty)
        ]
        for winner in previous_winners:
            self._restore(winner)

    def _restore(self, winner: Winner) -> None:
        try:
            self._units.remove(winner.item)
        except ValueError:
            raise ValueError(
                f"Winners file lists '{winner.item}' for {winner.full_name}, "
                "but there are no such prizes left in the prizes file."
            ) from None
        candidates = [
            i for i, p in enumerate(self.participants)
            if p.name == winner.name and p.lastname == winner.lastname
        ]
        if not candidates:
            raise ValueError(f"Winner {winner.full_name} is not in the participants file.")
        i = min(candidates, key=lambda c: self._wins[c])
        self._record(i, winner.item)

    def _record(self, index: int, item: str) -> Winner:
        self._wins[index] += 1
        self._held[index].add(item)
        p = self.participants[index]
        winner = Winner(p.name, p.lastname, item)
        self.winners.append(winner)
        return winner

    @property
    def next_prize(self) -> str | None:
        return self._units[0] if self._units else None

    @property
    def done(self) -> bool:
        return not self._units

    @property
    def remaining(self) -> list[Prize]:
        """Prizes still to be drawn, grouped by item in draw order."""
        counts: dict[str, int] = {}
        for item in self._units:
            counts[item] = counts.get(item, 0) + 1
        return [Prize(item, qty) for item, qty in counts.items()]

    def draw(self) -> Winner:
        if self.done:
            raise RuntimeError("All prizes have been awarded.")
        item = self._units.pop(0)
        keys = [(self._wins[i], item in self._held[i]) for i in range(len(self.participants))]
        best = min(keys)
        pool = [i for i, key in enumerate(keys) if key == best]
        return self._record(self.rng.choice(pool), item)
