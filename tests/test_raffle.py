import random
from collections import Counter

import pytest

from raffle_cli.raffle import Participant, Prize, Raffle, Winner, order_prizes

PEOPLE = [Participant(f"P{i}", "X") for i in range(5)]


def run_all(raffle):
    while not raffle.done:
        raffle.draw()
    return raffle.winners


def test_every_prize_is_awarded_once_each():
    winners = run_all(Raffle(PEOPLE, [Prize("a", 2), Prize("b", 1)], rng=random.Random(1)))
    assert Counter(w.item for w in winners) == {"a": 2, "b": 1}
    assert len({w.full_name for w in winners}) == 3  # nobody wins twice


def test_more_prizes_than_participants_are_shared_out_in_rounds():
    prizes = [Prize("a", 6), Prize("b", 4)]  # 10 prizes, 5 people
    winners = run_all(Raffle(PEOPLE, prizes, rng=random.Random(2)))
    assert len(winners) == 10
    assert set(Counter(w.full_name for w in winners).values()) == {2}  # fair: exactly two each


def test_nobody_gets_a_second_prize_before_everyone_has_one():
    raffle = Raffle(PEOPLE, [Prize("a", 7)], rng=random.Random(3))
    first_round = [raffle.draw() for _ in range(5)]
    assert len({w.full_name for w in first_round}) == 5


def test_same_item_is_avoided_in_later_rounds_when_possible():
    # 2 people, items x and y twice each: nobody should end up with two identical items
    people = PEOPLE[:2]
    for seed in range(20):
        winners = run_all(Raffle(people, [Prize("x", 2), Prize("y", 2)], rng=random.Random(seed), order="file"))
        assert len({(w.full_name, w.item) for w in winners}) == 4


def test_same_seed_same_result():
    a = run_all(Raffle(PEOPLE, [Prize("a", 3)], rng=random.Random(42)))
    b = run_all(Raffle(PEOPLE, [Prize("a", 3)], rng=random.Random(42)))
    assert a == b


def test_prizes_are_not_mutated():
    prizes = [Prize("a", 2)]
    run_all(Raffle(PEOPLE, prizes, rng=random.Random(0)))
    assert prizes == [Prize("a", 2)]


def test_resume_from_previous_winners():
    previous = [Winner("P0", "X", "a")]
    raffle = Raffle(PEOPLE, [Prize("a", 2), Prize("b", 1)], previous_winners=previous, rng=random.Random(0))
    assert raffle.remaining == [Prize("a", 1), Prize("b", 1)]
    winners = run_all(raffle)
    assert winners[0] == previous[0]
    assert len({w.full_name for w in winners}) == 3


def test_resume_rejects_unknown_item_or_person():
    with pytest.raises(ValueError, match="no such prizes"):
        Raffle(PEOPLE, [Prize("a", 1)], previous_winners=[Winner("P0", "X", "zzz")])
    with pytest.raises(ValueError, match="not in the participants"):
        Raffle(PEOPLE, [Prize("a", 1)], previous_winners=[Winner("Nobody", "X", "a")])


def test_needs_participants_and_cannot_overdraw():
    with pytest.raises(ValueError):
        Raffle([], [Prize("a", 1)])
    raffle = Raffle(PEOPLE, [Prize("a", 1)])
    raffle.draw()
    with pytest.raises(RuntimeError):
        raffle.draw()


@pytest.mark.parametrize(
    "order,expected",
    [("high-low", ["b", "c", "a"]), ("low-high", ["a", "c", "b"]), ("file", ["a", "b", "c"])],
)
def test_order_prizes(order, expected):
    prizes = [Prize("a", 1), Prize("b", 5), Prize("c", 2)]
    assert [p.item for p in order_prizes(prizes, order, random.Random(0))] == expected


def test_shuffle_and_invalid_order():
    prizes = [Prize(str(i), 1) for i in range(10)]
    assert sorted(p.item for p in order_prizes(prizes, "shuffle", random.Random(0))) == sorted(p.item for p in prizes)
    with pytest.raises(ValueError):
        order_prizes(prizes, "nope", random.Random(0))
