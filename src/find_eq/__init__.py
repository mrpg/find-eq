# Copyright (C) 2026 by Max R. P. Grossmann <m@max.pm>
# SPDX-License-Identifier: 0BSD

"""Competitive equilibrium in double auctions with unit demand and supply.

Setup. There are buyers with bids `b_1 >= b_2 >= ... >= b_m` and sellers
with asks `a_1 <= a_2 <= ... <= a_n`, each able to trade at most one
indivisible unit; a bid is a buyer's maximum willingness to pay and an ask
is a seller's minimum acceptable price.

Definition. A price `p` and a quantity `q` form an *equilibrium* iff

    |{i : b_i > p}| <= q <= |{i : b_i >= p}|,
    |{j : a_j < p}| <= q <= |{j : a_j <= p}|.

The left inequalities say every agent who strictly gains from trading does
trade; the right ones say only agents who weakly gain do. Agents whose
reservation price equals `p` exactly are indifferent, so they may be
rationed either way, which is what makes the inequalities loose. A demand
choice and a supply choice of the same size `q` therefore exist, with no
agent's participation constraint violated.

Theorem 1. Let `q* = max {k : b_k >= a_k}` (zero if no such `k` exists).
Then `q*` is the largest quantity that forms an equilibrium with some
price, and the set of prices forming an equilibrium with `q*` is exactly
the non-empty closed interval `[p_min, p_max]`, where

    p_min = max(a_{q*}, b_{q*+1}),    p_max = min(b_{q*}, a_{q*+1}),

omitting any term whose index falls outside its range.

Theorem 2. If prices lie in an ordered abelian group, so that surplus is
defined, matching the `q*` highest bids against the `q*` lowest asks
maximizes total surplus `sum (b - a)` over all matchings of any size.

`find_equilibrium` returns `q*` and its price interval. Smaller quantities
can also be equilibria, but only in the knife-edge case where the marginal
traders are exactly indifferent (`b_{q+1} == a_{q+1}`), and by Theorem 2
they are never more efficient, so reporting the maximal quantity loses
nothing.

Proofs are in `docs/proofs.md`; `tests/test_properties.py` checks the result
against a definition-level oracle on both generated and exhaustively
enumerated finite markets.
"""

from __future__ import annotations

# Runtime import keeps the public postponed annotations introspectable.
from collections.abc import Iterable  # noqa: TC003
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Self

__all__ = ["Equilibrium", "Ordered", "find_equilibrium"]


class Ordered(Protocol):
    """A totally ordered price type: `int`, `float`, `Fraction`, `Decimal`, ...

    Only comparisons are required, because this module never performs
    arithmetic on prices.
    """

    def __lt__(self, other: Self, /) -> bool:
        """Return whether `self` is strictly less than `other`."""

    def __le__(self, other: Self, /) -> bool:
        """Return whether `self` is less than or equal to `other`."""


@dataclass(frozen=True, slots=True)
class Equilibrium[P: Ordered]:
    """A market-clearing outcome of a double auction.

    Attributes:
        price_min: Lower endpoint of the clearing price interval, inclusive.
        price_max: Upper endpoint of the clearing price interval, inclusive.
        quantity: Number of units traded, the largest quantity that clears.

    Every price `p` with `price_min <= p <= price_max`, and no other price,
    forms an equilibrium with `quantity` units in the sense defined in the
    module docstring.
    """

    price_min: P
    price_max: P
    quantity: int


def _is_nan(value: object) -> bool:
    """Return whether `value` is a quiet or signaling NaN."""
    # A signaling Decimal NaN raises InvalidOperation even for `value != value`.
    # Decimal's predicate is context-independent and handles both NaN kinds.
    if isinstance(value, Decimal):
        return value.is_nan()
    return value != value  # noqa: PLR0124


def find_equilibrium[P: Ordered](bids: Iterable[P], asks: Iterable[P]) -> Equilibrium[P] | None:
    """Find the competitive equilibrium of a double auction.

    Prices may be of any totally ordered type, mixed freely as long as they
    are mutually comparable, since only comparisons are performed. See the
    module docstring for the equilibrium notion computed here.

    Args:
        bids: Buyers' reservation prices, one per buyer, in any order.
        asks: Sellers' reservation prices, one per seller, in any order.

    Returns:
        The equilibrium quantity and its exact interval of clearing prices,
        or `None` if `bids` or `asks` is empty. Empty input is not a failure
        but an unbounded answer: with no buyers, every price at or below the
        lowest ask clears the market at zero quantity; with no sellers, every
        price at or above the highest bid does; and with neither side present,
        every price does. No finite pair of input-derived endpoints can report
        these cases uniformly for every supported price type.

    Raises:
        ValueError: If `bids` or `asks` contains a NaN, which no total order
            admits. Left unchecked, a NaN would raise `InvalidOperation`
            from deep inside the sort for `Decimal`, or silently corrupt the
            sort order and the result for `float`.

    Complexity:
        Time `O((m + n) log(m + n))`, dominated by sorting; space `O(m + n)`.

    Example:
        >>> from decimal import Decimal
        >>> bids = [Decimal("10"), Decimal("8"), Decimal("6")]
        >>> asks = [Decimal("5"), Decimal("7"), Decimal("9")]
        >>> find_equilibrium(bids, asks)
        Equilibrium(price_min=Decimal('7'), price_max=Decimal('8'), quantity=2)

        Two units trade: the third buyer's 6 is below the third seller's 9.
        Any price from 7 to 8 clears, 7 being where the marginal seller
        breaks even and 8 where the marginal buyer does.

        >>> find_equilibrium([10, 8, 6], [5, 7, 9])
        Equilibrium(price_min=7, price_max=8, quantity=2)
        >>> find_equilibrium([1, 2], [8, 9])
        Equilibrium(price_min=2, price_max=8, quantity=0)
        >>> print(find_equilibrium([], [5]))
        None
    """
    # Materialize first, so that iterator inputs are consumed exactly once
    # and can be validated before anything tries to sort them.
    bids_sorted = list(bids)
    asks_sorted = list(asks)

    if any(map(_is_nan, bids_sorted)) or any(map(_is_nan, asks_sorted)):
        msg = "bids and asks must not contain NaN"
        raise ValueError(msg)

    if not bids_sorted or not asks_sorted:
        return None

    bids_sorted.sort(reverse=True)  # b_1 >= b_2 >= ... >= b_m, the demand schedule
    asks_sorted.sort()  # a_1 <= a_2 <= ... <= a_n, the supply schedule

    # Matching the k best bids with the k best asks is feasible iff even its
    # least-surplus pair has non-negative surplus, that is iff a_k <= b_k.
    # Since a_k is non-decreasing in k while b_k is non-increasing,
    # feasibility is monotone, so the first infeasible k determines q*.
    pairs = min(len(bids_sorted), len(asks_sorted))
    quantity = 0
    while quantity < pairs and asks_sorted[quantity] <= bids_sorted[quantity]:
        quantity += 1

    if quantity == 0:
        # Only the two constraints on the unmatched marginal traders bind:
        # the price is high enough that the best buyer does not demand, and
        # low enough that the best seller does not supply. The interval is
        # non-empty because b_1 < a_1 is why no trade occurs.
        return Equilibrium(price_min=bids_sorted[0], price_max=asks_sorted[0], quantity=0)

    # Matched traders must weakly gain: a_q <= p <= b_q.
    price_min = asks_sorted[quantity - 1]
    price_max = bids_sorted[quantity - 1]

    # Unmatched marginal traders must not strictly want to trade, which
    # tightens the interval to b_{q+1} <= p <= a_{q+1} where they exist.
    if quantity < len(bids_sorted):
        price_min = max(price_min, bids_sorted[quantity])
    if quantity < len(asks_sorted):
        price_max = min(price_max, asks_sorted[quantity])

    # The interval is non-empty: a_q <= b_q and a_q <= a_{q+1} and
    # b_{q+1} <= b_q hold by sortedness and by the choice of q, and when
    # both marginal traders exist b_{q+1} < a_{q+1} is why the scan stopped.
    return Equilibrium(price_min=price_min, price_max=price_max, quantity=quantity)
