# Copyright (C) 2026 by Max R. P. Grossmann <m@max.pm>
# SPDX-License-Identifier: 0BSD

"""Tests for double auction market clearing.

These tests verify both algorithmic correctness and economic properties
of the competitive equilibrium.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Self, get_type_hints

import pytest

from find_eq import Equilibrium, find_equilibrium


@dataclass(frozen=True, slots=True, order=False, eq=False)
class _Bare:
    """A price type implementing exactly the `Ordered` protocol, and no more."""

    value: int

    def __lt__(self, other: Self) -> bool:
        return self.value < other.value

    def __le__(self, other: Self) -> bool:
        return self.value <= other.value


class TestEmptySides:
    """Empty-side markets have unbounded price sets and return `None`."""

    def test_empty_bids(self) -> None:
        assert find_equilibrium([], [Decimal("5")]) is None

    def test_empty_asks(self) -> None:
        assert find_equilibrium([Decimal("5")], []) is None

    def test_both_empty(self) -> None:
        assert find_equilibrium([], []) is None


class TestNoTrade:
    """Cases where equilibrium exists but no trade occurs (quantity = 0)."""

    def test_no_gains_from_trade(self) -> None:
        # All buyers value the good less than all sellers' costs.
        bids = [Decimal("3"), Decimal("2"), Decimal("1")]
        asks = [Decimal("4"), Decimal("5"), Decimal("6")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 0
        assert eq.price_min == Decimal("3")
        assert eq.price_max == Decimal("4")

    def test_single_bid_below_single_ask(self) -> None:
        eq = find_equilibrium([Decimal("5")], [Decimal("6")])

        assert eq is not None
        assert eq.quantity == 0
        assert eq.price_min == Decimal("5")
        assert eq.price_max == Decimal("6")


class TestBasicEquilibrium:
    """Standard cases with positive trade volume."""

    def test_docstring_example(self) -> None:
        bids = [Decimal("10"), Decimal("8"), Decimal("6")]
        asks = [Decimal("5"), Decimal("7"), Decimal("9")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        assert eq.price_min == Decimal("7")
        assert eq.price_max == Decimal("8")

    def test_single_unit_trade(self) -> None:
        eq = find_equilibrium([Decimal("10")], [Decimal("5")])

        assert eq is not None
        assert eq.quantity == 1
        assert eq.price_min == Decimal("5")
        assert eq.price_max == Decimal("10")

    def test_all_units_trade(self) -> None:
        # Every buyer can trade with every seller.
        bids = [Decimal("10"), Decimal("9"), Decimal("8")]
        asks = [Decimal("1"), Decimal("2"), Decimal("3")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3
        assert eq.price_min == Decimal("3")
        assert eq.price_max == Decimal("8")

    def test_price_interval_is_single_point(self) -> None:
        # Marginal bid equals marginal ask.
        bids = [Decimal("10"), Decimal("7")]
        asks = [Decimal("5"), Decimal("7")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        assert eq.price_min == eq.price_max == Decimal("7")

    def test_input_order_irrelevant(self) -> None:
        # Shuffled inputs should yield identical equilibrium.
        bids_ordered = [Decimal("10"), Decimal("8"), Decimal("6")]
        asks_ordered = [Decimal("5"), Decimal("7"), Decimal("9")]

        bids_shuffled = [Decimal("6"), Decimal("10"), Decimal("8")]
        asks_shuffled = [Decimal("9"), Decimal("5"), Decimal("7")]

        eq1 = find_equilibrium(bids_ordered, asks_ordered)
        eq2 = find_equilibrium(bids_shuffled, asks_shuffled)

        assert eq1 == eq2


class TestTiesAtMargin:
    """Cases with multiple agents at the same reservation price."""

    def test_multiple_bids_at_same_price(self) -> None:
        bids = [Decimal("10"), Decimal("10"), Decimal("10")]
        asks = [Decimal("5"), Decimal("7"), Decimal("9")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3
        assert eq.price_min == Decimal("9")
        assert eq.price_max == Decimal("10")

    def test_multiple_asks_at_same_price(self) -> None:
        bids = [Decimal("10"), Decimal("8"), Decimal("6")]
        asks = [Decimal("5"), Decimal("5"), Decimal("5")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3
        assert eq.price_min == Decimal("5")
        assert eq.price_max == Decimal("6")

    def test_tie_at_marginal_price(self) -> None:
        # Two buyers and two sellers all at price 7.
        bids = [Decimal("10"), Decimal("7"), Decimal("7")]
        asks = [Decimal("5"), Decimal("7"), Decimal("7")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3
        assert eq.price_min == Decimal("7")
        assert eq.price_max == Decimal("7")


class TestEconomicProperties:
    """Verify fundamental economic invariants hold."""

    @pytest.mark.parametrize(
        ("bids", "asks"),
        [
            ([Decimal("10")], [Decimal("5")]),
            (
                [Decimal("10"), Decimal("8"), Decimal("6")],
                [Decimal("5"), Decimal("7"), Decimal("9")],
            ),
            (
                [Decimal("100"), Decimal("50"), Decimal("25"), Decimal("10")],
                [Decimal("5"), Decimal("20"), Decimal("30"), Decimal("80")],
            ),
            (
                [Decimal("7"), Decimal("7"), Decimal("7")],
                [Decimal("7"), Decimal("7"), Decimal("7")],
            ),
        ],
    )
    def test_price_interval_is_valid(self, bids: list[Decimal], asks: list[Decimal]) -> None:
        eq = find_equilibrium(bids, asks)
        assert eq is not None
        assert eq.price_min <= eq.price_max

    @pytest.mark.parametrize(
        ("bids", "asks"),
        [
            (
                [Decimal("10"), Decimal("8"), Decimal("6")],
                [Decimal("5"), Decimal("7"), Decimal("9")],
            ),
            (
                [Decimal("100"), Decimal("50"), Decimal("25"), Decimal("10")],
                [Decimal("5"), Decimal("20"), Decimal("30"), Decimal("80")],
            ),
        ],
    )
    def test_all_trades_have_nonnegative_surplus(
        self, bids: list[Decimal], asks: list[Decimal]
    ) -> None:
        """Every executed trade generates non-negative gains from trade."""
        eq = find_equilibrium(bids, asks)
        assert eq is not None

        bids_sorted = sorted(bids, reverse=True)
        asks_sorted = sorted(asks)

        for i in range(eq.quantity):
            # The i-th highest bidder trades with the i-th lowest asker.
            # Gains from trade = bid - ask >= 0.
            assert bids_sorted[i] >= asks_sorted[i]

    @pytest.mark.parametrize(
        ("bids", "asks"),
        [
            (
                [Decimal("10"), Decimal("8"), Decimal("6")],
                [Decimal("5"), Decimal("7"), Decimal("9")],
            ),
            (
                [Decimal("100"), Decimal("50"), Decimal("25"), Decimal("10")],
                [Decimal("5"), Decimal("20"), Decimal("30"), Decimal("80")],
            ),
        ],
    )
    def test_no_additional_trade_is_profitable(
        self, bids: list[Decimal], asks: list[Decimal]
    ) -> None:
        """The (q+1)-th trade would have negative surplus."""
        eq = find_equilibrium(bids, asks)
        assert eq is not None

        bids_sorted = sorted(bids, reverse=True)
        asks_sorted = sorted(asks)

        if eq.quantity < min(len(bids_sorted), len(asks_sorted)):
            # The next potential trade would be unprofitable.
            assert bids_sorted[eq.quantity] < asks_sorted[eq.quantity]

    @pytest.mark.parametrize(
        ("bids", "asks"),
        [
            (
                [Decimal("10"), Decimal("8"), Decimal("6")],
                [Decimal("5"), Decimal("7"), Decimal("9")],
            ),
            (
                [Decimal("100"), Decimal("50"), Decimal("25"), Decimal("10")],
                [Decimal("5"), Decimal("20"), Decimal("30"), Decimal("80")],
            ),
        ],
    )
    def test_price_satisfies_strict_and_weak_participation_bounds(
        self, bids: list[Decimal], asks: list[Decimal]
    ) -> None:
        """Every sampled interval price satisfies the defining inequalities."""
        eq = find_equilibrium(bids, asks)
        assert eq is not None

        for price in [eq.price_min, eq.price_max, (eq.price_min + eq.price_max) / 2]:
            strict_demand = sum(1 for bid in bids if bid > price)
            weak_demand = sum(1 for bid in bids if bid >= price)
            strict_supply = sum(1 for ask in asks if ask < price)
            weak_supply = sum(1 for ask in asks if ask <= price)
            assert strict_demand <= eq.quantity <= weak_demand
            assert strict_supply <= eq.quantity <= weak_supply


class TestMaximumWelfare:
    """Verify the equilibrium maximizes total surplus."""

    def test_welfare_maximization(self) -> None:
        bids = [Decimal("10"), Decimal("8"), Decimal("6"), Decimal("4")]
        asks = [Decimal("3"), Decimal("5"), Decimal("7"), Decimal("9")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None

        bids_sorted = sorted(bids, reverse=True)
        asks_sorted = sorted(asks)

        # Total surplus at equilibrium.
        equilibrium_surplus = sum(bids_sorted[i] - asks_sorted[i] for i in range(eq.quantity))

        # Compare against all possible quantities.
        max_possible = min(len(bids), len(asks))
        for q in range(max_possible + 1):
            alternative_surplus = sum(bids_sorted[i] - asks_sorted[i] for i in range(q))
            assert equilibrium_surplus >= alternative_surplus


class TestDataclassProperties:
    """Verify the Equilibrium dataclass behaves correctly."""

    def test_frozen(self) -> None:
        eq = find_equilibrium([Decimal("10")], [Decimal("5")])
        assert eq is not None

        with pytest.raises(AttributeError):
            eq.quantity = 999  # type: ignore[misc]

    def test_equality(self) -> None:
        eq1 = Equilibrium(price_min=Decimal("5"), price_max=Decimal("10"), quantity=1)
        eq2 = Equilibrium(price_min=Decimal("5"), price_max=Decimal("10"), quantity=1)
        assert eq1 == eq2

    def test_hashable(self) -> None:
        eq1 = Equilibrium(price_min=Decimal("5"), price_max=Decimal("10"), quantity=1)
        eq2 = Equilibrium(price_min=Decimal("5"), price_max=Decimal("10"), quantity=1)
        assert hash(eq1) == hash(eq2)
        assert {eq1, eq2} == {eq1}


class TestInputValidation:
    """NaN rejection: NaN admits no total order, so it must be refused."""

    def test_nan_bid_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN"):
            find_equilibrium([Decimal("NaN")], [Decimal("5")])

    def test_nan_ask_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN"):
            find_equilibrium([1.0], [float("nan")])

    def test_signaling_decimal_nan_rejected(self) -> None:
        """Signaling NaNs must not leak Decimal's context-dependent exception."""
        with pytest.raises(ValueError, match="NaN"):
            find_equilibrium([Decimal("sNaN")], [Decimal("5")])

    def test_nan_is_rejected_even_when_the_other_side_is_empty(self) -> None:
        """Validation precedes the empty-input case, so bad input never reads as None."""
        with pytest.raises(ValueError, match="NaN"):
            find_equilibrium([float("nan")], [])

    def test_nan_rejection_does_not_consume_a_valid_iterator_twice(self) -> None:
        """Inputs are materialized once, so a generator of valid prices survives."""
        eq = find_equilibrium((float(b) for b in (3, 1)), (float(a) for a in (2, 4)))
        assert eq == Equilibrium(price_min=2.0, price_max=3.0, quantity=1)


class TestOrderedProtocolContract:
    """The declared protocol must be all that is actually required.

    `find_equilibrium` sorts and calls `max`/`min`, which use `<` and `>`.
    Python falls back to the reflected operation for those, so `__lt__` and
    `__le__` really do suffice, and this test pins that down: an
    implementation that reached for `>` directly, or for a sort key, would
    break for a type providing no more than the protocol promises.
    """

    def test_type_implementing_only_the_protocol_is_accepted(self) -> None:
        eq = find_equilibrium([_Bare(10), _Bare(8), _Bare(6)], [_Bare(5), _Bare(7), _Bare(9)])
        assert eq is not None
        assert (eq.price_min.value, eq.price_max.value, eq.quantity) == (7, 8, 2)

    def test_public_type_hints_resolve_at_runtime(self) -> None:
        """Postponed annotations remain usable by runtime introspection tools."""
        assert set(get_type_hints(find_equilibrium)) == {"bids", "asks", "return"}


class TestGenericPriceTypes:
    """The algorithm is ordinal, so any totally ordered price type works."""

    def test_int_prices(self) -> None:
        eq = find_equilibrium([10, 8, 6], [5, 7, 9])
        assert eq == Equilibrium(price_min=7, price_max=8, quantity=2)

    def test_float_prices(self) -> None:
        eq = find_equilibrium([10.5, 8.5], [5.5, 9.5])
        assert eq == Equilibrium(price_min=8.5, price_max=9.5, quantity=1)

    def test_fraction_prices(self) -> None:
        eq = find_equilibrium([Fraction(3, 2)], [Fraction(1, 2)])
        assert eq == Equilibrium(price_min=Fraction(1, 2), price_max=Fraction(3, 2), quantity=1)

    def test_mutually_comparable_price_types_can_be_mixed(self) -> None:
        eq = find_equilibrium([Fraction(3, 2)], [0.5])
        assert eq == Equilibrium(price_min=0.5, price_max=Fraction(3, 2), quantity=1)

    def test_infinities_are_ordered_values_not_nan(self) -> None:
        eq = find_equilibrium([Decimal("Infinity")], [Decimal("-Infinity")])
        assert eq == Equilibrium(
            price_min=Decimal("-Infinity"),
            price_max=Decimal("Infinity"),
            quantity=1,
        )

    def test_generator_inputs(self) -> None:
        eq = find_equilibrium((Decimal(b) for b in ("10", "8")), iter([Decimal("5")]))
        assert eq == Equilibrium(price_min=Decimal("8"), price_max=Decimal("10"), quantity=1)

    def test_empty_iterator_inputs(self) -> None:
        no_bids: list[Decimal] = []
        assert find_equilibrium(iter(no_bids), iter([Decimal("5")])) is None

    def test_mutable_inputs_are_not_modified(self) -> None:
        bids = [3, 1, 2]
        asks = [6, 4, 5]
        bids_before = bids.copy()
        asks_before = asks.copy()

        find_equilibrium(bids, asks)

        assert bids == bids_before
        assert asks == asks_before


class TestStructuredStepSchedules:
    """Hand-constructed schedules with sharp steps and marginal ties."""

    def test_symmetric_schedule_with_marginal_equality(self) -> None:
        """The fourth pair has zero surplus and the fifth has negative surplus."""
        # Buyers with decreasing valuations.
        bids = [Decimal(v) for v in ["3.25", "3.00", "2.75", "2.50", "2.25"]]
        # Sellers with increasing costs.
        asks = [Decimal(v) for v in ["1.75", "2.00", "2.25", "2.50", "2.75"]]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        # Equilibrium: 4 units trade (bid[3]=2.50 >= ask[3]=2.50).
        # The 5th trade fails: bid[4]=2.25 < ask[4]=2.75.
        assert eq.quantity == 4
        # Price is exactly 2.50 (marginal bid = marginal ask).
        assert eq.price_min == Decimal("2.50")
        assert eq.price_max == Decimal("2.50")

    def test_unequal_side_sizes_with_identical_values(self) -> None:
        """Excess buyers at one value pin the price to their bid."""
        bids = [Decimal("10")] * 5
        asks = [Decimal("5")] * 3

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        # All 3 sellers trade (supply is the short side).
        assert eq.quantity == 3
        # With all buyers at 10, price must be 10 to prevent excess demand.
        assert eq.price_min == Decimal("10")
        assert eq.price_max == Decimal("10")


class TestBilateralMarkets:
    """Markets with exactly one potential trading pair."""

    def test_bilateral_trade_gains_exist(self) -> None:
        """A single buyer and seller have strictly positive gains from trade."""
        eq = find_equilibrium([Decimal("100")], [Decimal("50")])

        assert eq is not None
        assert eq.quantity == 1
        # Full price indeterminacy: any split of the $50 surplus works.
        assert eq.price_min == Decimal("50")
        assert eq.price_max == Decimal("100")

    def test_bilateral_trade_no_gains(self) -> None:
        """A single buyer and seller have strictly negative gains from trade."""
        eq = find_equilibrium([Decimal("50")], [Decimal("100")])

        assert eq is not None
        assert eq.quantity == 0
        assert eq.price_min == Decimal("50")
        assert eq.price_max == Decimal("100")

    def test_knife_edge_bilateral(self) -> None:
        """Buyer valuation exactly equals seller cost.

        Zero surplus case: trade is weakly efficient but generates no gains.
        The function should still identify this as a valid equilibrium.
        """
        eq = find_equilibrium([Decimal("75")], [Decimal("75")])

        assert eq is not None
        assert eq.quantity == 1
        assert eq.price_min == eq.price_max == Decimal("75")


class TestThinMarkets:
    """One side or both sides contain very few agents."""

    def test_single_seller_facing_multiple_buyers(self) -> None:
        """The highest excluded bid supplies the lower price bound."""
        bids = [Decimal("100"), Decimal("80"), Decimal("60"), Decimal("40")]
        asks = [Decimal("10")]  # Single low-cost seller.

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        # Price must be >= 80 (excluded buyer's bid) to prevent excess demand.
        assert eq.price_min == Decimal("80")
        assert eq.price_max == Decimal("100")

    def test_single_buyer_facing_multiple_sellers(self) -> None:
        """The lowest excluded ask supplies the upper price bound."""
        bids = [Decimal("100")]  # Single high-value buyer.
        asks = [Decimal("10"), Decimal("30"), Decimal("50"), Decimal("70")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        # Price must be <= 30 (excluded seller's ask) to prevent excess supply.
        assert eq.price_min == Decimal("10")
        assert eq.price_max == Decimal("30")

    def test_thin_market_single_trade(self) -> None:
        """Few traders with dispersed valuations: only one trade clears.

        Second-highest bid (1) < second-lowest ask (999999), so only
        one unit trades despite two traders on each side.
        """
        bids = [Decimal("1000000"), Decimal("1")]
        asks = [Decimal("0.01"), Decimal("999999")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        # Interval constrained by excluded agents: [max(0.01, 1), min(1000000, 999999)]
        assert eq.price_min == Decimal("1")
        assert eq.price_max == Decimal("999999")

    def test_thin_market_two_trades(self) -> None:
        """Few traders with dispersed valuations: two trades clear.

        Both bid-ask pairs have non-negative gains from trade.
        """
        bids = [Decimal("1000000"), Decimal("500000")]
        asks = [Decimal("1"), Decimal("100000")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        assert eq.price_min == Decimal("100000")
        assert eq.price_max == Decimal("500000")


class TestExcludedPairs:
    """Pairs excluded from the maximal allocation have negative surplus."""

    def test_every_fully_excluded_pair_has_negative_surplus(self) -> None:
        bids = [Decimal("10"), Decimal("8"), Decimal("6"), Decimal("4")]
        asks = [Decimal("3"), Decimal("5"), Decimal("7"), Decimal("9")]
        eq = find_equilibrium(bids, asks)

        assert eq == Equilibrium(price_min=Decimal("6"), price_max=Decimal("7"), quantity=2)

        bids_sorted = sorted(bids, reverse=True)
        asks_sorted = sorted(asks)

        # Excluded buyers and sellers are those at indices >= eq.quantity.
        # Every excluded bid is below every excluded ask, because the best
        # such bid is already below the best such ask.
        for excluded_bid in bids_sorted[eq.quantity :]:
            for excluded_ask in asks_sorted[eq.quantity :]:
                assert excluded_bid < excluded_ask


class TestLargeDeterministicMarkets:
    """Larger inputs exercise scan boundaries and deterministic scaling."""

    def test_large_symmetric_market(self) -> None:
        """One hundred symmetric integer steps clear at the central pair."""
        n = 100
        # Buyers: valuations from 100 down to 1.
        bids = [Decimal(101 - i) for i in range(1, n + 1)]
        # Sellers: costs from 1 up to 100.
        asks = [Decimal(i) for i in range(1, n + 1)]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        # Equilibrium at q = 50 (where bid[49] = 51 >= ask[49] = 50,
        # but bid[50] = 50 < ask[50] = 51).
        assert eq.quantity == 50
        assert eq.price_min == Decimal("50")
        assert eq.price_max == Decimal("51")

    def test_interval_width_stays_constant_for_scaled_integer_steps(self) -> None:
        """This construction has width one at every tested scale."""
        widths: list[Decimal] = []

        for n in [10, 50, 100, 200]:
            bids = [Decimal(n + 1 - i) for i in range(1, n + 1)]
            asks = [Decimal(i) for i in range(1, n + 1)]
            eq = find_equilibrium(bids, asks)
            assert eq is not None
            widths.append(eq.price_max - eq.price_min)

        assert widths == [Decimal("1")] * 4


class TestMarginalTies:
    """Exact equality at the margin permits indifferent rationing."""

    def test_all_traders_identical(self) -> None:
        """Every buyer and seller has the same reservation price.

        Degenerate case: all gains from trade are zero.
        """
        bids = [Decimal("50")] * 10
        asks = [Decimal("50")] * 10

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 10
        assert eq.price_min == eq.price_max == Decimal("50")

    def test_single_marginal_unit(self) -> None:
        """Only the marginal trade has zero surplus; others have positive."""
        bids = [Decimal("100"), Decimal("50")]
        asks = [Decimal("25"), Decimal("50")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        # Marginal trade: bid[1]=50, ask[1]=50 → zero surplus.
        assert eq.price_min == eq.price_max == Decimal("50")


class TestIndividualRationality:
    """Every selected trader weakly prefers trading to not trading."""

    def test_all_traders_satisfy_participation(self) -> None:
        """No trader is made worse off by the equilibrium allocation."""
        bids = [Decimal("20"), Decimal("15"), Decimal("10"), Decimal("5")]
        asks = [Decimal("6"), Decimal("9"), Decimal("12"), Decimal("18")]

        eq = find_equilibrium(bids, asks)
        assert eq is not None

        bids_sorted = sorted(bids, reverse=True)
        asks_sorted = sorted(asks)

        # For any clearing price p in [price_min, price_max]:
        for p in [eq.price_min, eq.price_max]:
            # Each trading buyer pays p <= their bid (non-negative surplus).
            for i in range(eq.quantity):
                assert bids_sorted[i] >= p
            # Each trading seller receives p >= their ask (non-negative surplus).
            for i in range(eq.quantity):
                assert p >= asks_sorted[i]


class TestEfficiencyAndSurplusAccounting:
    """The selected quantity is efficient and surplus decomposes exactly."""

    def test_efficient_allocation(self) -> None:
        """The equilibrium allocation maximizes total surplus."""
        bids = [Decimal("90"), Decimal("70"), Decimal("50"), Decimal("30")]
        asks = [Decimal("20"), Decimal("40"), Decimal("60"), Decimal("80")]

        eq = find_equilibrium(bids, asks)
        assert eq is not None

        bids_sorted = sorted(bids, reverse=True)
        asks_sorted = sorted(asks)

        # Efficient quantity: trade while bid >= ask.
        efficient_q = 0
        for i in range(min(len(bids), len(asks))):
            if bids_sorted[i] >= asks_sorted[i]:
                efficient_q = i + 1
            else:
                break

        assert eq.quantity == efficient_q

    def test_surplus_decomposition(self) -> None:
        """Total surplus equals sum of buyer and seller surpluses."""
        bids = [Decimal("100"), Decimal("80"), Decimal("60")]
        asks = [Decimal("30"), Decimal("50"), Decimal("70")]

        eq = find_equilibrium(bids, asks)
        assert eq is not None

        bids_sorted = sorted(bids, reverse=True)
        asks_sorted = sorted(asks)

        # Use midpoint price for concrete surplus calculation.
        p = (eq.price_min + eq.price_max) / 2

        buyer_surplus = sum(bids_sorted[i] - p for i in range(eq.quantity))
        seller_surplus = sum(p - asks_sorted[i] for i in range(eq.quantity))
        total_surplus = sum(bids_sorted[i] - asks_sorted[i] for i in range(eq.quantity))

        assert buyer_surplus + seller_surplus == total_surplus


class TestExcludedTraderBounds:
    """Excluded marginal agents can tighten either endpoint.

    At an endpoint, indifferent agents may be rationed. At a strict interior
    price, no reservation price is crossed, so strict and weak demand and
    supply are all exactly the reported quantity.
    """

    def test_excluded_buyer_constrains_price_min(self) -> None:
        """Price interval must account for excluded buyer's bid.

        Counterexample from microeconomic analysis:
        - Bids: [10, 9, 8], Asks: [1, 7, 100]
        - Efficient q = 2 (9 >= 7, but 8 < 100)
        - Naive interval [7, 9] fails: at p=7, demand=3, supply=2 (excess demand)
        - Correct interval must have price_min >= 8 (excluded buyer's bid)
        """
        bids = [Decimal("10"), Decimal("9"), Decimal("8")]
        asks = [Decimal("1"), Decimal("7"), Decimal("100")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        # price_min must be >= 8 to exclude the third buyer
        assert eq.price_min >= Decimal("8")
        assert eq.price_max == Decimal("9")

    def test_excluded_seller_constrains_price_max(self) -> None:
        """Price interval must account for the excluded seller's ask.

        Mirror image of the excluded-buyer case:
        - Bids [100, 93, 1], asks [8, 9, 10], so q = 2 (93 >= 9, but 1 < 10).
        - The naive interval [a_2, b_2] = [9, 93] is too wide: at p = 10 the
          third seller would supply while only two buyers demand.
        - So price_max must be at most 10, the excluded seller's ask.
        """
        bids = [Decimal("100"), Decimal("93"), Decimal("1")]
        asks = [Decimal("8"), Decimal("9"), Decimal("10")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        assert eq.price_min == Decimal("9")
        # price_max must be <= 10 to exclude the third seller
        assert eq.price_max <= Decimal("10")

    def test_both_sides_constrain_interval(self) -> None:
        """Both excluded buyer and seller constrain the interval."""
        bids = [Decimal("20"), Decimal("15"), Decimal("12")]
        asks = [Decimal("5"), Decimal("10"), Decimal("14")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        # Excluded buyer bids 12, excluded seller asks 14
        # Interval must be [max(10, 12), min(15, 14)] = [12, 14]
        assert eq.price_min >= Decimal("12")
        assert eq.price_max <= Decimal("14")

    @pytest.mark.parametrize(
        ("bids", "asks"),
        [
            # Excluded buyer constrains.
            (
                [Decimal("10"), Decimal("9"), Decimal("8")],
                [Decimal("1"), Decimal("7"), Decimal("100")],
            ),
            # Excluded seller constrains
            (
                [Decimal("100"), Decimal("93"), Decimal("1")],
                [Decimal("8"), Decimal("9"), Decimal("10")],
            ),
            # Both sides constrain
            (
                [Decimal("20"), Decimal("15"), Decimal("12")],
                [Decimal("5"), Decimal("10"), Decimal("14")],
            ),
            # Original docstring example
            (
                [Decimal("10"), Decimal("8"), Decimal("6")],
                [Decimal("5"), Decimal("7"), Decimal("9")],
            ),
        ],
    )
    def test_demand_equals_supply_at_interior_price(
        self, bids: list[Decimal], asks: list[Decimal]
    ) -> None:
        """At strict interior prices, demand equals supply exactly."""
        eq = find_equilibrium(bids, asks)
        assert eq is not None

        # At a strict interior price (if interval has positive width), market clears exactly
        if eq.price_min < eq.price_max:
            price = (eq.price_min + eq.price_max) / 2
            demand = sum(1 for b in bids if b >= price)
            supply = sum(1 for a in asks if a <= price)
            assert demand == supply == eq.quantity, (
                f"At price {price}: demand={demand}, supply={supply}, "
                f"expected quantity={eq.quantity}"
            )


class TestAsymmetricMarkets:
    """Markets with unequal numbers of buyers and sellers."""

    def test_many_buyers_few_sellers(self) -> None:
        """Excess demand: more buyers than sellers."""
        bids = [Decimal(str(100 - i * 5)) for i in range(20)]  # 20 buyers.
        asks = [Decimal(str(10 + i * 10)) for i in range(5)]  # 5 sellers.

        eq = find_equilibrium(bids, asks)

        # All 5 sellers trade, the short side. The price is pinned from below
        # by the sixth buyer's bid of 75 rather than by the marginal ask of
        # 50, since 15 buyers are left over.
        assert eq == Equilibrium(price_min=Decimal("75"), price_max=Decimal("80"), quantity=5)

    def test_few_buyers_many_sellers(self) -> None:
        """Excess supply: more sellers than buyers."""
        bids = [Decimal(str(100 - i * 10)) for i in range(5)]  # 5 buyers.
        asks = [Decimal(str(10 + i * 5)) for i in range(20)]  # 20 sellers.

        eq = find_equilibrium(bids, asks)

        # All 5 buyers trade, the short side. Symmetrically, the price is
        # pinned from above by the sixth seller's ask of 35 rather than by
        # the marginal bid of 60.
        assert eq == Equilibrium(price_min=Decimal("30"), price_max=Decimal("35"), quantity=5)
