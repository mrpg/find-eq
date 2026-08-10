<!-- Copyright (C) 2026 by Max R. P. Grossmann <m@max.pm> -->
<!-- SPDX-License-Identifier: 0BSD -->

# find-eq

Find the competitive equilibrium in a double auction market.

Buyers and sellers can each trade at most one indivisible unit, at a reservation price they name. `find_equilibrium` reports how many units trade and *exactly* which prices clear the market: not one clearing price out of many, and not a superset, but the full closed interval and nothing else.

## Install

```sh
uv add "find-eq @ git+https://github.com/mrpg/find-eq.git"
# or: pip install "find-eq @ git+https://github.com/mrpg/find-eq.git"
```

No runtime dependencies. Requires Python 3.13 or newer. Ships type information (`py.typed`).

## Usage

```python
>>> from find_eq import find_equilibrium
>>> bids = [10, 8, 6]   # Buyers' maximum willingness to pay
>>> asks = [5, 7, 9]    # Sellers' minimum acceptable price
>>> eq = find_equilibrium(bids, asks)
>>> eq.quantity
2
>>> eq.price_min, eq.price_max
(7, 8)

```

Two units trade, because the third buyer's 6 is below the third seller's 9. Every price from 7 through 8 clears the market, 7 being where the marginal seller breaks even and 8 where the marginal buyer does. Below 7 the marginal seller withdraws; above 8 the marginal buyer does.

Excluded traders can narrow the interval further, which is easy to get wrong:

```python
>>> find_equilibrium([10, 9, 8], [1, 7, 100])
Equilibrium(price_min=8, price_max=9, quantity=2)

```

Here the marginal seller asks 7, but 7 is *not* a clearing price: at 7 the third buyer would also want to buy, and there is no third seller willing to sell at 7. The price must be at least 8 to keep that buyer out of the market.

## Edge cases

When no gains from trade exist, an equilibrium still exists, at zero quantity. The result is not `None`:

```python
>>> find_equilibrium([3, 2, 1], [4, 5, 6])
Equilibrium(price_min=3, price_max=4, quantity=0)

```

At any price from 3 through 4, no agent strictly wants to trade. An agent who is indifferent at an endpoint may be rationed out, so zero units clear throughout the interval.

`None` is returned only when one side is empty, where the answer exists but is unbounded and so cannot be reported uniformly by two input-derived endpoints: with no buyers, every price at or below the lowest ask clears at zero quantity; with no sellers, every price at or above the highest bid does; with both sides empty, every price does.

```python
>>> print(find_equilibrium([], [5]))
None

```

A thin market can leave the price almost entirely indeterminate:

```python
>>> find_equilibrium([100], [10])
Equilibrium(price_min=10, price_max=100, quantity=1)

```

Excess supply from identical sellers collapses it to a point; at that price the indifferent sellers are rationed:

```python
>>> find_equilibrium([50], [10, 10, 10])
Equilibrium(price_min=10, price_max=10, quantity=1)

```

Ties at the margin are handled exactly, with no epsilons:

```python
>>> find_equilibrium([10, 7], [5, 7])
Equilibrium(price_min=7, price_max=7, quantity=2)

```

## Price types

The algorithm is purely ordinal: it sorts and compares, and never does arithmetic on prices. So any totally ordered, mutually comparable price type works, and `Equilibrium` is generic in it.

```python
>>> from decimal import Decimal
>>> from fractions import Fraction
>>> find_equilibrium([Decimal("2.50")], [Decimal("1.75")])
Equilibrium(price_min=Decimal('1.75'), price_max=Decimal('2.50'), quantity=1)
>>> find_equilibrium([Fraction(3, 2)], [0.5])
Equilibrium(price_min=0.5, price_max=Fraction(3, 2), quantity=1)

```

Prefer `Decimal` or `Fraction` for money: results are then exact, since no rounding can occur anywhere in the computation. Negative and zero prices are fine, and mean what they say (a negative ask is a seller paying to have the good taken away).

NaN is rejected rather than silently mishandled, because it has no place in a total order:

```python
>>> find_equilibrium([1.0], [float("nan")])
Traceback (most recent call last):
    ...
ValueError: bids and asks must not contain NaN

```

## Guarantees

Write $b_1 \geq \dots \geq b_m$ for the sorted bids, $a_1 \leq \dots \leq a_n$ for the sorted asks, and $q^{*} = \max \{k : b_k \geq a_k\}$. Then `find_equilibrium` returns quantity $q^{*}$ with the interval

$$[\max(a_{q^{*}}, b_{q^{*}+1}),\; \min(b_{q^{*}}, a_{q^{*}+1})],$$

dropping out-of-range terms, and:

- **Exactness.** A price clears the market at quantity $q^{*}$ if and only if it lies in the reported interval.
- **Maximality.** No larger quantity clears the market at any price. Smaller quantities can, but only where the marginal traders are exactly indifferent, and then they are no more efficient.
- **Non-emptiness.** Whenever an interval is returned, it is never empty, so `price_min <= price_max` always holds.
- **Efficiency.** The reported quantity maximizes total surplus over matchings of every size, whenever prices support subtraction.
- **Order invariance.** Only the multisets of bids and asks matter, not their order.

The equilibrium notion behind "clears the market" is stated in the [correctness proofs](https://github.com/mrpg/find-eq/blob/master/docs/proofs.md). `tests/test_properties.py` compares the implementation with a direct transcription of that definition on generated markets and on an exhaustively enumerated finite domain. For each market, a finite set of representative prices provably covers every possible ordering relative to the reservation prices.

Running time is $O((m + n) \log(m + n))$, dominated by sorting.

## Development

```sh
uv sync --dev
uv run pytest                       # tests, doctests, and 100% branch coverage
uv run mypy                         # strict, plus extra error codes
uv run ruff check .                 # every ruff rule, minus a documented few
uv run black . && uv run isort .
uv build --no-sources               # validated wheel and source distribution
```

## License

0BSD. See the [license](https://github.com/mrpg/find-eq/blob/master/LICENSE).
