# Copyright (C) 2026 by Max R. P. Grossmann <m@max.pm>
# SPDX-License-Identifier: 0BSD

"""Pathological edge cases from Micro 101 - extreme market scenarios.

These tests probe boundary conditions that might cause numerical,
algorithmic, or economic edge cases in market clearing.
"""

from decimal import Decimal

import pytest

from find_eq import Equilibrium, find_equilibrium


class TestNegativePrices:
    """Markets with negative reservation prices.

    Economically valid: e.g., waste disposal where you pay someone to take it,
    or goods with negative externalities. The algebra should work identically.
    """

    def test_negative_asks_positive_bids(self) -> None:
        """Sellers willing to pay buyers to take goods (waste disposal)."""
        bids = [Decimal("10"), Decimal("5"), Decimal("0")]
        asks = [Decimal("-20"), Decimal("-10"), Decimal("-5")]  # Sellers pay to offload.

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3  # All trades profitable.
        # Marginal bid = 0, marginal ask = -5.
        assert eq.price_min == Decimal("-5")
        assert eq.price_max == Decimal("0")

    def test_all_negative_prices(self) -> None:
        """Both sides have negative reservation prices."""
        bids = [Decimal("-5"), Decimal("-10"), Decimal("-15")]  # Buyers want compensation.
        asks = [Decimal("-30"), Decimal("-20"), Decimal("-10")]  # Sellers really want to offload.

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        # bid[0]=-5 >= ask[0]=-30 ✓
        # bid[1]=-10 >= ask[1]=-20 ✓
        # bid[2]=-15 >= ask[2]=-10? No, -15 < -10.
        assert eq.quantity == 2
        # Marginal: ask=-20, bid=-10.
        # Tightening: excluded bid=-15, excluded ask=-10.
        # price_min = max(-20, -15) = -15, price_max = min(-10, -10) = -10.
        assert eq.price_min == Decimal("-15")
        assert eq.price_max == Decimal("-10")

    def test_mixed_positive_negative(self) -> None:
        """Some positive, some negative reservation prices."""
        bids = [Decimal("10"), Decimal("0"), Decimal("-5")]
        asks = [Decimal("-10"), Decimal("5"), Decimal("15")]

        eq = find_equilibrium(bids, asks)

        # bid[0]=10 >= ask[0]=-10, but bid[1]=0 < ask[1]=5, so one unit
        # trades. The interval is pinned by the excluded traders on both
        # sides: [max(-10, 0), min(10, 5)].
        assert eq == Equilibrium(price_min=Decimal("0"), price_max=Decimal("5"), quantity=1)


class TestZeroPrices:
    """Edge cases with zero reservation prices."""

    def test_all_zeros(self) -> None:
        """Everyone values the good at exactly zero."""
        bids = [Decimal("0")] * 5
        asks = [Decimal("0")] * 5

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 5
        assert eq.price_min == eq.price_max == Decimal("0")

    def test_bids_zero_asks_negative(self) -> None:
        """Buyers indifferent, sellers desperate to sell."""
        bids = [Decimal("0"), Decimal("0"), Decimal("0")]
        asks = [Decimal("-10"), Decimal("-5"), Decimal("-1")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3
        assert eq.price_min == Decimal("-1")
        assert eq.price_max == Decimal("0")

    def test_bids_positive_asks_zero(self) -> None:
        """Sellers have zero cost."""
        bids = [Decimal("10"), Decimal("5"), Decimal("1")]
        asks = [Decimal("0"), Decimal("0"), Decimal("0")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3
        assert eq.price_min == Decimal("0")
        assert eq.price_max == Decimal("1")


class TestExtremeValues:
    """Very large or very small numbers - precision edge cases."""

    def test_very_large_values(self) -> None:
        """Prices in the trillions."""
        bids = [Decimal("1e18"), Decimal("1e15"), Decimal("1e12")]
        asks = [Decimal("1e9"), Decimal("1e11"), Decimal("1e14")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        # Marginal: ask=1e11, bid=1e15.
        # Tightening: excluded bid=1e12, excluded ask=1e14.
        # price_min = max(1e11, 1e12) = 1e12, price_max = min(1e15, 1e14) = 1e14.
        assert eq.price_min == Decimal("1e12")
        assert eq.price_max == Decimal("1e14")

    def test_very_small_values(self) -> None:
        """Prices in the nano range."""
        bids = [Decimal("1e-9"), Decimal("1e-12"), Decimal("1e-15")]
        asks = [Decimal("1e-18"), Decimal("1e-14"), Decimal("1e-10")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        assert eq.price_min == Decimal("1e-14")
        assert eq.price_max == Decimal("1e-12")

    def test_mixed_magnitude_values(self) -> None:
        """Prices spanning many orders of magnitude."""
        bids = [Decimal("1e12"), Decimal("1"), Decimal("1e-12")]
        asks = [Decimal("1e-15"), Decimal("0.5"), Decimal("1e9")]

        eq = find_equilibrium(bids, asks)

        # 1e12 >= 1e-15 and 1 >= 0.5, but 1e-12 < 1e9, so two units trade
        # across 27 orders of magnitude with no loss of precision.
        assert eq == Equilibrium(price_min=Decimal("0.5"), price_max=Decimal("1"), quantity=2)


class TestIdenticalReservationValues:
    """Repeated values with equal and unequal numbers of agents."""

    def test_equal_side_sizes_at_distinct_values(self) -> None:
        """Equal side sizes leave the whole surplus interval available."""
        bids = [Decimal("100")] * 5  # 5 buyers, all pay up to 100.
        asks = [Decimal("10")] * 5  # 5 sellers, all accept 10 or more.

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 5
        # Any price in [10, 100] clears the market.
        assert eq.price_min == Decimal("10")
        assert eq.price_max == Decimal("100")

    def test_excess_identical_sellers_collapse_the_interval(self) -> None:
        """An excluded seller at the same ask supplies the upper bound."""
        bids = [Decimal("100")] * 3  # 3 buyers.
        asks = [Decimal("10")] * 7  # 7 sellers.

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3  # Demand is short side.
        # Marginal: ask=10, bid=100.
        # But excluded seller (4th) also asks 10!
        # price_max = min(100, 10) = 10, price_min = 10.
        # Excess supply of identical sellers forces price to their reservation.
        assert eq.price_min == Decimal("10")
        assert eq.price_max == Decimal("10")

    def test_single_buyer_many_identical_sellers(self) -> None:
        """One buyer facing many identical sellers."""
        bids = [Decimal("50")]
        asks = [Decimal("10")] * 100

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        # 99 excluded sellers at 10, so price_max = 10.
        assert eq.price_min == Decimal("10")
        assert eq.price_max == Decimal("10")

    def test_many_identical_buyers_single_seller(self) -> None:
        """Many identical buyers facing one seller."""
        bids = [Decimal("50")] * 100
        asks = [Decimal("10")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        # 99 excluded buyers at 50, so price_min = 50.
        assert eq.price_min == Decimal("50")
        assert eq.price_max == Decimal("50")


class TestFlatAskSchedule:
    """A repeated ask value against a strictly descending bid schedule."""

    def test_horizontal_supply_meets_downward_demand(self) -> None:
        """All sellers at same price, buyers with varying valuations."""
        bids = [Decimal("100"), Decimal("80"), Decimal("60"), Decimal("40"), Decimal("20")]
        asks = [Decimal("50")] * 10

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        # Trades where bid >= 50: 100, 80, 60 → 3 trades.
        assert eq.quantity == 3
        # Marginal buyer bids 60, excluded buyer bids 40.
        # price_min = max(50, 40) = 50, price_max = min(60, 50) = 50.
        assert eq.price_min == Decimal("50")
        assert eq.price_max == Decimal("50")


class TestMarginalEqualityAndGap:
    """The best bid either equals or narrowly misses the best ask."""

    def test_single_zero_surplus_pair(self) -> None:
        """Exactly one bid-ask pair has non-negative surplus."""
        bids = [Decimal("5"), Decimal("4"), Decimal("3")]
        asks = [Decimal("5"), Decimal("6"), Decimal("7")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        # Only bid[0]=5 >= ask[0]=5.
        assert eq.quantity == 1
        assert eq.price_min == Decimal("5")
        assert eq.price_max == Decimal("5")

    def test_curves_just_miss(self) -> None:
        """Highest bid is epsilon below lowest ask - no trade, but equilibrium exists."""
        bids = [Decimal("4.99"), Decimal("4"), Decimal("3")]
        asks = [Decimal("5"), Decimal("6"), Decimal("7")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 0
        assert eq.price_min == Decimal("4.99")
        assert eq.price_max == Decimal("5")


class TestMassiveIndifference:
    """Many traders with identical reservation prices."""

    def test_thousand_identical_on_each_side(self) -> None:
        """Massive tie at the margin."""
        n = 1000
        bids = [Decimal("100")] * n
        asks = [Decimal("50")] * n

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == n
        # All bids are 100 and all asks are 50, leaving interval [50, 100].
        assert eq.price_min == Decimal("50")
        assert eq.price_max == Decimal("100")

    def test_ten_thousand_at_same_price(self) -> None:
        """Everyone - buyers and sellers - at the same price."""
        n = 10000
        price = Decimal("42.00")
        bids = [price] * n
        asks = [price] * n

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == n
        assert eq.price_min == eq.price_max == price


class TestDisjointRanges:
    """Cases where bid and ask ranges don't overlap."""

    def test_gap_between_ranges(self) -> None:
        """Large gap between max bid and min ask."""
        bids = [Decimal("10"), Decimal("5"), Decimal("1")]
        asks = [Decimal("100"), Decimal("200"), Decimal("300")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 0
        assert eq.price_min == Decimal("10")
        assert eq.price_max == Decimal("100")

    def test_adjacent_ranges(self) -> None:
        """Max bid == min ask exactly."""
        bids = [Decimal("100"), Decimal("50"), Decimal("25")]
        asks = [Decimal("100"), Decimal("150"), Decimal("200")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        assert eq.price_min == eq.price_max == Decimal("100")


class TestSingleTrader:
    """Degenerate markets with just one trader on one side."""

    def test_single_bid_multiple_asks(self) -> None:
        """One buyer, many sellers."""
        eq = find_equilibrium([Decimal("50")], [Decimal("10"), Decimal("20"), Decimal("30")])

        assert eq is not None
        assert eq.quantity == 1
        assert eq.price_min == Decimal("10")
        assert eq.price_max == Decimal("20")  # Constrained by excluded seller.

    def test_single_ask_multiple_bids(self) -> None:
        """One seller, many buyers."""
        eq = find_equilibrium([Decimal("100"), Decimal("80"), Decimal("60")], [Decimal("50")])

        assert eq is not None
        assert eq.quantity == 1
        assert eq.price_min == Decimal("80")  # Constrained by excluded buyer.
        assert eq.price_max == Decimal("100")

    def test_single_bid_single_ask_equal(self) -> None:
        """A bilateral market with zero surplus."""
        eq = find_equilibrium([Decimal("75")], [Decimal("75")])

        assert eq is not None
        assert eq.quantity == 1
        assert eq.price_min == eq.price_max == Decimal("75")


class TestCompleteOverlap:
    """Every possible trade is profitable."""

    def test_all_bids_above_all_asks(self) -> None:
        """Lowest bid exceeds highest ask."""
        bids = [Decimal("100"), Decimal("90"), Decimal("80")]
        asks = [Decimal("10"), Decimal("20"), Decimal("30")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3  # All trade.
        # price_min = max ask = 30, price_max = min bid = 80.
        assert eq.price_min == Decimal("30")
        assert eq.price_max == Decimal("80")


class TestRepeatedValues:
    """Multiple ties at various price levels."""

    def test_three_way_tie_both_sides(self) -> None:
        """Three buyers and three sellers all at same price."""
        price = Decimal("50")
        bids = [price, price, price]
        asks = [price, price, price]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 3
        assert eq.price_min == eq.price_max == price

    def test_duplicate_at_margin_only(self) -> None:
        """Ties only at the marginal price."""
        bids = [Decimal("100"), Decimal("50"), Decimal("50"), Decimal("50")]
        asks = [Decimal("10"), Decimal("50"), Decimal("50"), Decimal("90")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        # bid[0]=100 >= ask[0]=10 ✓
        # bid[1]=50 >= ask[1]=50 ✓
        # bid[2]=50 >= ask[2]=50 ✓
        # bid[3]=50 >= ask[3]=90? No.
        assert eq.quantity == 3
        assert eq.price_min == eq.price_max == Decimal("50")


class TestAsymmetricExtremes:
    """Highly asymmetric market structures."""

    def test_one_eager_buyer_many_reluctant_sellers(self) -> None:
        """Buyer with huge valuation vs sellers with high costs."""
        bids = [Decimal("1000000")]
        asks = [Decimal("999999"), Decimal("999998"), Decimal("999997")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        assert eq.price_min == Decimal("999997")
        assert eq.price_max == Decimal("999998")

    def test_many_eager_buyers_one_reluctant_seller(self) -> None:
        """Many high-value buyers vs one high-cost seller."""
        bids = [Decimal("1000000"), Decimal("999999"), Decimal("999998")]
        asks = [Decimal("999997")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        assert eq.price_min == Decimal("999999")
        assert eq.price_max == Decimal("1000000")


class TestEconomicInvariants:
    """Verify economic properties hold for pathological cases."""

    @pytest.mark.parametrize(
        ("bids", "asks"),
        [
            # Negative prices.
            (
                [Decimal("-5"), Decimal("-10")],
                [Decimal("-30"), Decimal("-20")],
            ),
            # Zero prices.
            (
                [Decimal("0"), Decimal("0")],
                [Decimal("0"), Decimal("0")],
            ),
            # Extreme magnitudes.
            (
                [Decimal("1e15"), Decimal("1e12")],
                [Decimal("1e9"), Decimal("1e11")],
            ),
            # All identical.
            (
                [Decimal("50")] * 100,
                [Decimal("50")] * 100,
            ),
            # A single zero-surplus pair.
            (
                [Decimal("10"), Decimal("5")],
                [Decimal("10"), Decimal("15")],
            ),
        ],
    )
    def test_price_interval_valid(self, bids: list[Decimal], asks: list[Decimal]) -> None:
        """Price min <= price max for all equilibria."""
        eq = find_equilibrium(bids, asks)
        assert eq is not None
        assert eq.price_min <= eq.price_max

    @pytest.mark.parametrize(
        ("bids", "asks"),
        [
            # Negative prices.
            (
                [Decimal("-5"), Decimal("-10")],
                [Decimal("-30"), Decimal("-20")],
            ),
            # All identical.
            (
                [Decimal("50")] * 10,
                [Decimal("50")] * 10,
            ),
            # Extreme spread.
            (
                [Decimal("1e18"), Decimal("1")],
                [Decimal("0.001"), Decimal("1e17")],
            ),
        ],
    )
    def test_market_clears_at_equilibrium_price(
        self, bids: list[Decimal], asks: list[Decimal]
    ) -> None:
        """Every sampled interval price satisfies the defining bounds."""
        eq = find_equilibrium(bids, asks)
        assert eq is not None

        for price in [eq.price_min, eq.price_max, (eq.price_min + eq.price_max) / 2]:
            strict_demand = sum(1 for bid in bids if bid > price)
            weak_demand = sum(1 for bid in bids if bid >= price)
            strict_supply = sum(1 for ask in asks if ask < price)
            weak_supply = sum(1 for ask in asks if ask <= price)
            assert strict_demand <= eq.quantity <= weak_demand
            assert strict_supply <= eq.quantity <= weak_supply


class TestPriceIndeterminacy:
    """Cases with maximal price indeterminacy (wide intervals)."""

    def test_bilateral_market_huge_surplus(self) -> None:
        """Single buyer/seller with massive gains from trade."""
        bids = [Decimal("1000000")]
        asks = [Decimal("1")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        # Entire surplus range is valid.
        assert eq.price_min == Decimal("1")
        assert eq.price_max == Decimal("1000000")
        # Interval width = 999999.
        assert eq.price_max - eq.price_min == Decimal("999999")

    def test_no_excluded_traders_wide_interval(self) -> None:
        """All traders participate, leaving wide price freedom."""
        bids = [Decimal("100"), Decimal("90")]
        asks = [Decimal("10"), Decimal("20")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 2
        # No excluded traders, so interval = [marginal ask, marginal bid].
        assert eq.price_min == Decimal("20")
        assert eq.price_max == Decimal("90")


class TestQuantityEdgeCases:
    """Edge cases around the quantity traded."""

    def test_one_positive_and_one_zero_surplus_trade(self) -> None:
        """The maximal allocation includes its zero-surplus marginal pair."""
        bids = [Decimal("5"), Decimal("4"), Decimal("3")]
        asks = [Decimal("5"), Decimal("4"), Decimal("3")]

        eq = find_equilibrium(bids, asks)

        # Sorted: bids [5, 4, 3], asks [3, 4, 5]. The second pair breaks even
        # at 4 >= 4, the third fails at 3 < 5, and the interval collapses to
        # the single point 4 where the marginal pair is indifferent.
        assert eq == Equilibrium(price_min=Decimal("4"), price_max=Decimal("4"), quantity=2)

    def test_only_first_trade_profitable(self) -> None:
        """Rapidly diverging curves."""
        bids = [Decimal("100"), Decimal("1")]
        asks = [Decimal("1"), Decimal("100")]

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        # Excluded: bid[1]=1, ask[1]=100.
        assert eq.price_min == Decimal("1")
        assert eq.price_max == Decimal("100")
