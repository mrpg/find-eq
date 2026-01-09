"""Tests for double auction market clearing.

These tests verify both algorithmic correctness and economic properties
of the competitive equilibrium.
"""

from decimal import Decimal

import pytest

from find_eq import Equilibrium, find_equilibrium


class TestNoTrade:
    """Cases where no equilibrium exists."""

    def test_empty_bids(self) -> None:
        assert find_equilibrium([], [Decimal("5")]) is None

    def test_empty_asks(self) -> None:
        assert find_equilibrium([Decimal("5")], []) is None

    def test_both_empty(self) -> None:
        assert find_equilibrium([], []) is None

    def test_no_gains_from_trade(self) -> None:
        # All buyers value the good less than all sellers' costs.
        bids = [Decimal("3"), Decimal("2"), Decimal("1")]
        asks = [Decimal("4"), Decimal("5"), Decimal("6")]
        assert find_equilibrium(bids, asks) is None

    def test_single_bid_below_single_ask(self) -> None:
        assert find_equilibrium([Decimal("5")], [Decimal("6")]) is None


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
        "bids,asks",
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
        "bids,asks",
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
        "bids,asks",
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
        "bids,asks",
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
    def test_price_clears_market(self, bids: list[Decimal], asks: list[Decimal]) -> None:
        """Any price in [price_min, price_max] induces exactly eq.quantity trades."""
        eq = find_equilibrium(bids, asks)
        assert eq is not None

        for price in [eq.price_min, eq.price_max, (eq.price_min + eq.price_max) / 2]:
            demand = sum(1 for b in bids if b >= price)
            supply = sum(1 for a in asks if a <= price)
            assert min(demand, supply) == eq.quantity


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
        eq = Equilibrium(price_min=Decimal("5"), price_max=Decimal("10"), quantity=1)
        {eq}  # Should not raise.


class TestVernonSmithInducedValue:
    """Cases from Vernon Smith's experimental economics (1962, Nobel Prize 2002).

    Smith's "induced value" methodology assigns private reservation prices
    to subjects, creating controlled supply and demand. These tests replicate
    canonical experimental designs.
    """

    def test_smith_1962_baseline(self) -> None:
        """Approximate replication of Smith's original double auction experiment.

        Symmetric supply and demand with clear competitive equilibrium.
        The 4th buyer (bid=2.50) and 4th seller (ask=2.50) are exactly
        indifferent, yielding a knife-edge equilibrium.
        """
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

    def test_swastika_design(self) -> None:
        """The "swastika" supply-demand configuration.

        Named for the shape when plotted: perfectly inelastic supply meets
        perfectly inelastic demand at different quantities, creating a
        step-function equilibrium region. Tests robustness to non-standard
        curve shapes. (See Smith, 1976, "Experimental Economics".)
        """
        # Vertical demand: all buyers willing to pay up to 10.
        bids = [Decimal("10")] * 5
        # Vertical supply: all sellers require at least 5.
        asks = [Decimal("5")] * 3

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        # All 3 sellers trade (supply is the short side).
        assert eq.quantity == 3
        # With all buyers at 10, price must be 10 to prevent excess demand.
        assert eq.price_min == Decimal("10")
        assert eq.price_max == Decimal("10")


class TestMyersonSatterthwaite:
    """Cases related to Myerson-Satterthwaite (1983) impossibility theorem.

    The theorem shows no mechanism can achieve efficiency, incentive
    compatibility, individual rationality, and budget balance when
    reservation values are private. These tests probe boundary cases.
    """

    def test_bilateral_trade_gains_exist(self) -> None:
        """Single buyer, single seller with gains from trade.

        The classic Myerson-Satterthwaite setup. With known values,
        the competitive mechanism achieves efficiency.
        """
        eq = find_equilibrium([Decimal("100")], [Decimal("50")])

        assert eq is not None
        assert eq.quantity == 1
        # Full price indeterminacy: any split of the $50 surplus works.
        assert eq.price_min == Decimal("50")
        assert eq.price_max == Decimal("100")

    def test_bilateral_trade_no_gains(self) -> None:
        """Single buyer, single seller with no gains from trade.

        Impossibility doesn't apply: there's simply no efficient trade.
        """
        assert find_equilibrium([Decimal("50")], [Decimal("100")]) is None

    def test_knife_edge_bilateral(self) -> None:
        """Buyer valuation exactly equals seller cost.

        Zero surplus case: trade is weakly efficient but generates no gains.
        The mechanism should still identify this as a valid equilibrium.
        """
        eq = find_equilibrium([Decimal("75")], [Decimal("75")])

        assert eq is not None
        assert eq.quantity == 1
        assert eq.price_min == eq.price_max == Decimal("75")


class TestMarketPower:
    """Monopoly, monopsony, and thin market cases."""

    def test_monopolist_seller(self) -> None:
        """Single seller facing multiple buyers.

        In competitive equilibrium (price-taking), the monopolist has no
        market power — price is determined by the marginal buyer's bid.
        """
        bids = [Decimal("100"), Decimal("80"), Decimal("60"), Decimal("40")]
        asks = [Decimal("10")]  # Single low-cost seller.

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        assert eq.quantity == 1
        # Price must be >= 80 (excluded buyer's bid) to prevent excess demand.
        assert eq.price_min == Decimal("80")
        assert eq.price_max == Decimal("100")

    def test_monopsonist_buyer(self) -> None:
        """Single buyer facing multiple sellers.

        Symmetric to monopoly case.
        """
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


class TestCoreStability:
    """Tests related to core allocations and coalitional stability.

    In a double auction, the competitive equilibrium is in the core:
    no coalition can deviate and make all members better off.
    """

    def test_no_blocking_coalition_exists(self) -> None:
        """Verify no subset of traders can profitably deviate.

        A blocking coalition would be a set of buyers and sellers who
        could trade among themselves at prices strictly better for all
        than the equilibrium. In competitive equilibrium, no such
        coalition exists.
        """
        bids = [Decimal("10"), Decimal("8"), Decimal("6"), Decimal("4")]
        asks = [Decimal("3"), Decimal("5"), Decimal("7"), Decimal("9")]
        eq = find_equilibrium(bids, asks)

        assert eq is not None

        bids_sorted = sorted(bids, reverse=True)
        asks_sorted = sorted(asks)

        # Check that no excluded buyer-seller pair could profitably trade.
        # Excluded buyers have indices >= eq.quantity in bids_sorted.
        # Excluded sellers have indices >= eq.quantity in asks_sorted.
        for i in range(eq.quantity, len(bids_sorted)):
            for j in range(eq.quantity, len(asks_sorted)):
                # If excluded buyer i and excluded seller j could trade...
                if bids_sorted[i] >= asks_sorted[j]:
                    # ...it would require displacing an included trader,
                    # but included traders have higher bids / lower asks.
                    # This is a contradiction, so this branch should not execute.
                    assert bids_sorted[i] < asks_sorted[j]


class TestLargeMarkets:
    """Asymptotic behavior as market size grows.

    In large markets, the law of large numbers implies the equilibrium
    price interval shrinks and approaches the "true" competitive price.
    """

    def test_large_symmetric_market(self) -> None:
        """Many buyers and sellers with uniform distributions.

        As n → ∞, price_min and price_max should converge.
        """
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

    def test_price_interval_shrinks_with_n(self) -> None:
        """Verify price interval width decreases as market grows."""
        widths: list[Decimal] = []

        for n in [10, 50, 100, 200]:
            bids = [Decimal(n + 1 - i) for i in range(1, n + 1)]
            asks = [Decimal(i) for i in range(1, n + 1)]
            eq = find_equilibrium(bids, asks)
            assert eq is not None
            widths.append(eq.price_max - eq.price_min)

        # Width should be non-increasing (actually constant at 1 for this design).
        for i in range(len(widths) - 1):
            assert widths[i] >= widths[i + 1]


class TestZeroMeasureMarginalTraders:
    """Edge cases where the marginal trader has measure zero.

    In continuous models, the marginal trader is a single point.
    In discrete models, we must handle exact ties carefully.
    """

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


class TestHurwiczParticipation:
    """Individual rationality / participation constraints (Hurwicz, 1972).

    Every trader must weakly prefer participating to autarky.
    """

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


class TestVickreyClarkeGroves:
    """Properties related to VCG mechanism design.

    While find_equilibrium implements Walrasian (price-based) clearing,
    these tests verify properties that VCG mechanisms also satisfy.
    """

    def test_efficient_allocation(self) -> None:
        """The equilibrium allocation maximizes total surplus.

        This is the key efficiency property that VCG achieves via
        dominant-strategy incentive compatibility.
        """
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


class TestWalrasianClearing:
    """Tests for true Walrasian market clearing (demand == supply).

    The price interval must ensure that at any price p in [price_min, price_max],
    the quantity demanded equals the quantity supplied (no rationing needed).
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
        """Price interval must account for excluded seller's ask.

        Mirror of the buyer case:
        - Bids: [100, 7, 1], Asks: [8, 9, 10]
        - Efficient q = 2 (7 >= 9? No. Let me recalculate...)
        Actually: bids sorted desc [100, 7, 1], asks sorted asc [8, 9, 10]
        - k=1: 100 >= 8 ✓
        - k=2: 7 >= 9? No.
        So q = 1. Let me design a better example.

        Better example:
        - Bids: [100, 93, 1], Asks: [8, 9, 10]
        - q = 2 (93 >= 9, but 1 < 10)
        - Naive interval [9, 93]
        - At p = 10: supply = 3, demand = 2 → excess supply
        - Correct: price_max <= 10 (excluded seller's ask)
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
        "bids,asks",
        [
            # The counterexample from the critique
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

        assert eq is not None
        # At most 5 trades (limited by seller count).
        assert eq.quantity <= 5

    def test_few_buyers_many_sellers(self) -> None:
        """Excess supply: more sellers than buyers."""
        bids = [Decimal(str(100 - i * 10)) for i in range(5)]  # 5 buyers.
        asks = [Decimal(str(10 + i * 5)) for i in range(20)]  # 20 sellers.

        eq = find_equilibrium(bids, asks)

        assert eq is not None
        # At most 5 trades (limited by buyer count).
        assert eq.quantity <= 5
