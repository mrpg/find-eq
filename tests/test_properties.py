# Copyright (C) 2026 by Max R. P. Grossmann <m@max.pm>
# SPDX-License-Identifier: 0BSD

"""Property-based tests against a brute-force oracle.

The example-based suites pin down specific markets. These tests instead
check the theorems in the module docstring on randomly generated markets,
comparing `find_equilibrium` against a direct transcription of the
definition of equilibrium.

Prices are drawn as integers so that all oracle arithmetic is exact, and
candidate prices are `Fraction`s so that strict interior points exist. The
two types are mutually comparable, which is all `find_equilibrium` needs.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations_with_replacement, pairwise, product
from typing import TYPE_CHECKING

from hypothesis import example, given
from hypothesis import strategies as st

from find_eq import Equilibrium, find_equilibrium

if TYPE_CHECKING:
    from collections.abc import Sequence
    from random import Random

Price = int | Fraction

# Small markets, so that a failure shrinks to something a human can read,
# with a narrow price range to make ties and knife-edge cases frequent.
reservation_prices = st.integers(min_value=-8, max_value=8)
nonempty_side = st.lists(reservation_prices, min_size=1, max_size=7)
possibly_empty_side = st.lists(reservation_prices, max_size=7)


def clears(bids: Sequence[int], asks: Sequence[int], price: Price, quantity: int) -> bool:
    """Return whether `price` and `quantity` form an equilibrium.

    A literal transcription of the definition: every trader who strictly
    gains at `price` trades, and only traders who weakly gain do.
    """
    # Strict counts are the agents who must trade, weak counts the agents
    # who may; the quantity has to fit between them on both sides.
    strict_demand = sum(b > price for b in bids)
    weak_demand = sum(b >= price for b in bids)
    strict_supply = sum(a < price for a in asks)
    weak_supply = sum(a <= price for a in asks)
    return strict_demand <= quantity <= weak_demand and strict_supply <= quantity <= weak_supply


def candidate_prices(bids: Sequence[int], asks: Sequence[int]) -> list[Price]:
    """Return prices sufficient to decide every equilibrium claim exactly.

    Whether a price clears depends on it only through how it compares with
    each reservation price. So the reservation prices themselves, one point
    strictly between each pair of neighbours, and one point beyond each end
    cover every possible pattern of comparisons, and hence every price.
    """
    reservations = sorted(set(bids) | set(asks))
    interior: list[Price] = [Fraction(lower + upper, 2) for lower, upper in pairwise(reservations)]
    return [reservations[0] - 1, *reservations, *interior, reservations[-1] + 1]


def best_surplus(bids: Sequence[int], asks: Sequence[int], quantity: int) -> int:
    """Return the total surplus of the best matching of exactly `quantity` pairs.

    The surplus of a matching is `sum(bid - ask)` over its pairs, which does
    not depend on who is matched with whom. So the best matching of a given
    size simply takes the highest bids and the lowest asks, and maximizing
    over sizes needs no enumeration of pairings.
    """
    return sum(sorted(bids, reverse=True)[:quantity]) - sum(sorted(asks)[:quantity])


@given(bids=nonempty_side, asks=nonempty_side)
@example(bids=[0], asks=[0])  # Knife-edge: zero surplus, so q = 0 also clears.
@example(bids=[1, 0], asks=[0, 1])  # Marginal traders indifferent on both sides.
def test_interval_is_exactly_the_set_of_clearing_prices(bids: list[int], asks: list[int]) -> None:
    """Theorem 1: the reported interval is sound and complete.

    Every price in it clears the market at the reported quantity, and no
    price outside it does.
    """
    eq = find_equilibrium(bids, asks)
    assert eq is not None
    reservations = [*bids, *asks]
    # The implementation is ordinal, so each finite endpoint must be one of
    # the input prices. Together with one representative from every open cell,
    # this makes the candidate set decisive for the entire ordered domain.
    assert eq.price_min in reservations
    assert eq.price_max in reservations

    for price in candidate_prices(bids, asks):
        inside = eq.price_min <= price <= eq.price_max
        assert clears(bids, asks, price, eq.quantity) == inside, (
            f"price {price} clears == {not inside} but lies "
            f"{'inside' if inside else 'outside'} {eq}"
        )


def test_exhaustive_small_integer_markets_match_the_definition() -> None:
    """Exhaustively verify every market over a small, tie-rich finite domain.

    Hypothesis explores larger shapes and shrinks failures well; this test
    complements it with complete coverage of every multiset of one to three
    agents per side whose prices lie in {-2, -1, 0, 1, 2}.
    """
    sides = [
        side for size in range(1, 4) for side in combinations_with_replacement(range(-2, 3), size)
    ]

    for bids, asks in product(sides, repeat=2):
        eq = find_equilibrium(bids, asks)
        assert eq is not None

        clearing_quantities: set[int] = set()
        for quantity in range(min(len(bids), len(asks)) + 1):
            for price in candidate_prices(bids, asks):
                does_clear = clears(bids, asks, price, quantity)
                if does_clear:
                    clearing_quantities.add(quantity)
                if quantity == eq.quantity:
                    inside = eq.price_min <= price <= eq.price_max
                    assert does_clear == inside, (bids, asks, price, eq)

        assert eq.quantity == max(clearing_quantities), (bids, asks, eq)


@given(bids=nonempty_side, asks=nonempty_side)
def test_reported_quantity_is_the_largest_that_clears(bids: list[int], asks: list[int]) -> None:
    """Theorem 1: no larger quantity clears at any price."""
    eq = find_equilibrium(bids, asks)
    assert eq is not None

    for quantity in range(eq.quantity + 1, min(len(bids), len(asks)) + 1):
        for price in candidate_prices(bids, asks):
            assert not clears(bids, asks, price, quantity)


@given(bids=nonempty_side, asks=nonempty_side)
def test_smaller_quantities_clear_only_when_marginal_traders_are_indifferent(
    bids: list[int], asks: list[int]
) -> None:
    """Equilibrium quantity is unique except in the knife-edge case.

    A quantity below the reported one can clear, but only where the traders
    it excludes are exactly indifferent, so nothing is given up by
    reporting the largest.
    """
    eq = find_equilibrium(bids, asks)
    assert eq is not None

    bids_sorted = sorted(bids, reverse=True)
    asks_sorted = sorted(asks)

    for quantity in range(eq.quantity):
        for price in candidate_prices(bids, asks):
            if clears(bids, asks, price, quantity):
                assert bids_sorted[quantity] == asks_sorted[quantity] == price


@given(bids=nonempty_side, asks=nonempty_side)
def test_reported_quantity_maximizes_total_surplus(bids: list[int], asks: list[int]) -> None:
    """Theorem 2: the reported quantity is efficient."""
    eq = find_equilibrium(bids, asks)
    assert eq is not None

    equilibrium_surplus = best_surplus(bids, asks, eq.quantity)
    for quantity in range(min(len(bids), len(asks)) + 1):
        assert equilibrium_surplus >= best_surplus(bids, asks, quantity)


@given(bids=nonempty_side, asks=nonempty_side)
def test_every_matched_trader_weakly_gains(bids: list[int], asks: list[int]) -> None:
    """Individual rationality holds at both endpoints of the interval."""
    eq = find_equilibrium(bids, asks)
    assert eq is not None

    bids_sorted = sorted(bids, reverse=True)
    asks_sorted = sorted(asks)

    for price in (eq.price_min, eq.price_max):
        for i in range(eq.quantity):
            assert bids_sorted[i] >= price
            assert asks_sorted[i] <= price


@given(bids=possibly_empty_side, asks=possibly_empty_side)
def test_result_is_none_exactly_when_a_side_is_empty(bids: list[int], asks: list[int]) -> None:
    """The only unreportable case is the one with an unbounded answer."""
    assert (find_equilibrium(bids, asks) is None) == (not bids or not asks)


@given(bids=possibly_empty_side, asks=possibly_empty_side, rng=st.randoms())
def test_result_does_not_depend_on_input_order(
    bids: list[int],
    asks: list[int],
    rng: Random,
) -> None:
    """Only the multisets of bids and asks matter, not their order."""
    shuffled_bids = rng.sample(bids, len(bids))
    shuffled_asks = rng.sample(asks, len(asks))
    assert find_equilibrium(bids, asks) == find_equilibrium(shuffled_bids, shuffled_asks)


@given(bids=nonempty_side, asks=nonempty_side)
def test_buyer_seller_duality(bids: list[int], asks: list[int]) -> None:
    """Negating all prices exchanges the roles of buyers and sellers.

    A seller with ask `a` is a buyer of the mirrored good with bid `-a`, so
    the mirrored market must trade the same quantity at the mirrored prices.
    """
    eq = find_equilibrium(bids, asks)
    mirrored = find_equilibrium([-a for a in asks], [-b for b in bids])

    assert eq is not None
    assert mirrored == Equilibrium(
        price_min=-eq.price_max,
        price_max=-eq.price_min,
        quantity=eq.quantity,
    )


@given(bids=nonempty_side, asks=nonempty_side, new_price=reservation_prices)
def test_adding_a_buyer_raises_quantity_by_zero_or_one(
    bids: list[int],
    asks: list[int],
    new_price: int,
) -> None:
    """Comparative statics: entry on one side weakly increases volume.

    Adding a buyer raises every entry of the sorted bid schedule weakly, so
    it can only make matchings easier, and it adds only one unit of demand.
    """
    before = find_equilibrium(bids, asks)
    after = find_equilibrium([*bids, new_price], asks)

    assert before is not None
    assert after is not None
    assert before.quantity <= after.quantity <= before.quantity + 1


@given(bids=nonempty_side, asks=nonempty_side, new_price=reservation_prices)
def test_adding_a_seller_raises_quantity_by_zero_or_one(
    bids: list[int],
    asks: list[int],
    new_price: int,
) -> None:
    """Comparative statics: the mirror image of buyer entry."""
    before = find_equilibrium(bids, asks)
    after = find_equilibrium(bids, [*asks, new_price])

    assert before is not None
    assert after is not None
    assert before.quantity <= after.quantity <= before.quantity + 1


@given(bids=nonempty_side, asks=nonempty_side, increase=st.integers(0, 16))
def test_raising_a_bid_weakly_increases_quantity(
    bids: list[int],
    asks: list[int],
    increase: int,
) -> None:
    """Comparative statics: a more eager buyer never reduces volume."""
    before = find_equilibrium(bids, asks)
    after = find_equilibrium([bids[0] + increase, *bids[1:]], asks)

    assert before is not None
    assert after is not None
    assert after.quantity >= before.quantity
