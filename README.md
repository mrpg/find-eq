# find-eq

Find competitive equilibrium in double auction markets.

## Usage

```python
from find_eq import find_equilibrium

# Buyers' maximum willingness to pay
bids = [10, 8, 6]
# Sellers' minimum acceptable price
asks = [5, 7, 9]

eq = find_equilibrium(bids, asks)

eq.quantity   # 2 units trade
eq.price_min  # 7 (lowest clearing price)
eq.price_max  # 8 (highest clearing price)
```

Any price in `[price_min, price_max]` clears the market.

## More Examples

```python
# No trade possible (all asks exceed all bids)
find_equilibrium([3, 2, 1], [4, 5, 6])  # None

# Single trade with wide price range
find_equilibrium([100], [10])
# Equilibrium(price_min=10, price_max=100, quantity=1)

# Exact match at margin
find_equilibrium([10, 7], [5, 7])
# Equilibrium(price_min=7, price_max=7, quantity=2)
```

## License

0BSD
