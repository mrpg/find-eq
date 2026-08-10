<!-- Copyright (C) 2026 by Max R. P. Grossmann <m@max.pm> -->
<!-- SPDX-License-Identifier: 0BSD -->

# Correctness of `find_equilibrium`

This document proves the two theorems that `find_equilibrium` implements. `tests/test_properties.py` checks them against a direct transcription of Definition 1 on generated markets and on an exhaustively enumerated finite domain.

## Setup

Fix a totally ordered set of prices $(\mathcal{P}, \leq)$. A *market* is a pair of non-empty finite multisets $B, A$ over $\mathcal{P}$: the *bids* $b_1 \geq b_2 \geq \dots \geq b_m$ of $m$ buyers and the *asks* $a_1 \leq a_2 \leq \dots \leq a_n$ of $n$ sellers, each agent trading at most one indivisible unit. A buyer with bid $b$ strictly prefers trading at price $p$ to not trading iff $p < b$, is indifferent iff $p = b$, and strictly prefers not trading iff $p > b$; a seller with ask $a$ strictly prefers trading iff $p > a$, and so on symmetrically.

Write $q^{*} = \max \{k \in \{1, \dots, \min(m, n)\} : b_k \geq a_k\}$, with $q^{*} = 0$ when no such $k$ exists.

**Definition 1.** A price $p \in \mathcal{P}$ and a quantity $q \in \mathbb{N}_0$ form an *equilibrium* iff

$$|\{i : b_i > p\}| \leq q \leq |\{i : b_i \geq p\}| \quad \text{and} \quad |\{j : a_j < p\}| \leq q \leq |\{j : a_j \leq p\}| .$$

The lower bounds require that every agent who strictly gains from trading does trade; the upper bounds require that only agents who weakly gain do. Agents whose reservation price is exactly $p$ are indifferent, and the definition permits rationing them either way, which is why the bounds are loose. Each pair of bounds guarantees a size-$q$ subset of weakly willing agents that contains every strictly willing agent. The selected buyers and sellers can then be matched arbitrarily, so demand and supply choices of the same size exist and the implied allocation is feasible.

For concise boundary formulas, adjoin two *formal* elements $\bot < p < \top$ for every $p \in \mathcal{P}$. Adopt the conventions $b_k = \top$ and $a_k = \bot$ for $k \leq 0$, and $b_k = \bot$ and $a_k = \top$ for $k > m$ and $k > n$ respectively. The symbols $\bot$ and $\top$ are not price values, even when $\mathcal{P}$ itself contains values called positive or negative infinity. Every occurrence below is a bound that becomes vacuous, matching an omitted term in the implementation.

## Lemma 1 (order translation)

For every $p \in \mathcal{P}$ and $q \in \mathbb{N}_0$:

1. $q \leq |\{i : b_i \geq p\}| \iff p \leq b_q$,
2. $|\{i : b_i > p\}| \leq q \iff b_{q+1} \leq p$,
3. $q \leq |\{j : a_j \leq p\}| \iff a_q \leq p$,
4. $|\{j : a_j < p\}| \leq q \iff p \leq a_{q+1}$.

*Proof.* (1) If $q = 0$ both sides hold vacuously, and if $q > m$ both fail. Otherwise, $b$ is sorted non-increasingly, so at least $q$ bids are $\geq p$ iff the $q$-th largest is, i.e. iff $b_q \geq p$. (2) At most $q$ bids exceed $p$ iff the $(q+1)$-st largest does not, i.e. iff $b_{q+1} \leq p$; for $q \geq m$ both sides hold. (3) and (4) are the same arguments applied to the non-decreasing sequence $a$. $\square$

So $(p, q)$ is an equilibrium iff

$$\max(a_q,\, b_{q+1}) \leq p \leq \min(b_q,\, a_{q+1}). \tag{$\ast$}$$

## Lemma 2 (monotone feasibility)

If $1 \leq k \leq k' \leq \min(m, n)$ and $b_{k'} \geq a_{k'}$, then $b_k \geq a_k$. Consequently $\{k : b_k \geq a_k\} = \{1, \dots, q^{*}\}$.

*Proof.* Sortedness gives $b_k \geq b_{k'} \geq a_{k'} \geq a_k$. Hence the feasible set is downward closed, so it is exactly $\{1, \dots, q^{*}\}$ and the linear scan in the implementation, which stops at the first $k$ with $a_k > b_k$, returns $q^{*}$. $\square$

## Theorem 1 (exactness of the reported interval)

Let $p_{\min} = \max(a_{q^{*}}, b_{q^{*}+1})$ and $p_{\max} = \min(b_{q^{*}}, a_{q^{*}+1})$. Then:

1. **(Maximality.)** If $(p, q)$ is an equilibrium for some $p$, then $q \leq q^{*}$.
2. **(Non-emptiness.)** $p_{\min} \leq p_{\max}$, and both are elements of $\mathcal{P}$ rather than the formal boundary symbols.
3. **(Exactness.)** $(p, q^{*})$ is an equilibrium iff $p_{\min} \leq p \leq p_{\max}$.

*Proof.*

**(1)** Let $(p, q)$ be an equilibrium with $q \geq 1$ (for $q = 0$ there is nothing to show). By $(\ast)$, $a_q \leq p \leq b_q$, so neither $a_q$ nor $b_q$ can be the boundary symbol on its prohibitive side. Thus the corresponding entries exist, $q \leq \min(m, n)$, and $b_q \geq a_q$. Lemma 2 gives $q \leq q^{*}$.

**(2)** First, both endpoints are actual price values. If $q^{*} = 0$ then $p_{\min} = \max(a_0, b_1) = b_1$ and $p_{\max} = \min(b_0, a_1) = a_1$, which belong to $\mathcal{P}$ because $B$ and $A$ are non-empty. If $q^{*} \geq 1$ then $a_{q^{*}}$ and $b_{q^{*}}$ are actual entries by $q^{*} \leq \min(m, n)$, so the maximum defining $p_{\min}$ and the minimum defining $p_{\max}$ each involve an actual value on the non-vacuous side and cannot select a formal boundary symbol.

Now the inequality. It suffices to check all four pairings:

- $a_{q^{*}} \leq b_{q^{*}}$: for $q^{*} \geq 1$ this is the defining property of $q^{*}$; for $q^{*} = 0$ the left side is $\bot$.
- $a_{q^{*}} \leq a_{q^{*}+1}$: sortedness of $a$.
- $b_{q^{*}+1} \leq b_{q^{*}}$: sortedness of $b$.
- $b_{q^{*}+1} \leq a_{q^{*}+1}$: if $q^{*}+1 > \min(m, n)$ then at least one side is a formal boundary symbol that makes the inequality immediate. Otherwise $q^{*}+1 \leq \min(m, n)$, and $b_{q^{*}+1} \geq a_{q^{*}+1}$ would contradict the maximality of $q^{*}$, so $b_{q^{*}+1} < a_{q^{*}+1}$.

**(3)** Immediate from $(\ast)$ with $q = q^{*}$. $\square$

Part (3) is the sense in which the returned interval is not merely a set of clearing prices but *the* set: no clearing price is omitted, and no non-clearing price is included.

## Theorem 2 (efficiency)

Suppose additionally that $\mathcal{P}$ is an ordered abelian group, so that the *surplus* of a matching $M$ of buyers to sellers, $\sigma(M) = \sum_{(i, j) \in M} (b_i - a_j)$, is defined. Then $\sigma$ is maximized by the matching $M^{*}$ that pairs the $q^{*}$ highest bids with the $q^{*}$ lowest asks.

*Proof.* The summand depends only on which agents appear in $M$, not on who is matched with whom, so for a matching of size $k$,

$$\sigma(M) = \sum_{i \in I} b_i - \sum_{j \in J} a_j$$

for the sets $I, J$ of matched buyers and sellers, $|I| = |J| = k$. For each $0 \leq k \leq \min(m,n)$ this is maximized over $k$-element sets by taking the $k$ largest bids and the $k$ smallest asks, giving $\sigma_k = \sum_{i \leq k} (b_i - a_i)$ as the best surplus at size $k$. For $1 \leq k \leq \min(m,n)$, the increment $\sigma_{k} - \sigma_{k-1} = b_k - a_k$ is non-negative exactly when $k \leq q^{*}$ and is negative when $k > q^{*}$. Thus $\sigma_k$ is non-decreasing up to $q^{*}$ and strictly decreasing after it, and $\sigma_{q^{*}} = \max_{0 \leq k \leq \min(m,n)} \sigma_k$. $\square$

Note that Theorem 2, unlike Theorem 1, needs arithmetic. `find_equilibrium` performs none, which is why it accepts any totally ordered price type; efficiency is a statement about those price types that also support subtraction.

## Remark (uniqueness of the quantity)

Quantities below $q^{*}$ can also be equilibrium quantities, but only in a knife-edge case. If $(p, q)$ is an equilibrium with $q < q^{*}$, then $q + 1 \leq q^{*} \leq \min(m, n)$, so $b_{q+1}$ and $a_{q+1}$ are actual entries, and $(\ast)$ gives $b_{q+1} \leq p \leq a_{q+1}$ while Lemma 2 gives $b_{q+1} \geq a_{q+1}$. Hence

$$b_{q+1} = a_{q+1} = p,$$

so the marginal excluded traders are exactly indifferent and gain nothing from being included. More strongly, for every $q < k \leq q^{*}$, sortedness and feasibility give

$$p = b_{q+1} \geq b_k \geq a_k \geq a_{q+1} = p,$$

hence $b_k = a_k = p$. When the arithmetic assumptions of Theorem 2 hold, every intervening surplus increment is zero, so $q$ and $q^{*}$ attain the same maximal surplus. Independently of arithmetic, $a_{q^{*}} = b_{q^{*}} = p$, while any existing $b_{q^{*}+1} \leq p \leq a_{q^{*}+1}$. Formula $(\ast)$ therefore shows directly that $p$ also clears at $q^{*}$. Reporting $q^{*}$ loses no clearing price and, whenever surplus is defined, no efficiency.

## Remark (empty input)

Definition 1 still has solutions when a side is empty, but they are unbounded. With $B = \emptyset$ and $A \ne \emptyset$, the constraints reduce to $q = 0$ and $p \leq a_1$, so the clearing prices are the entire downward-closed set below $a_1$; with $A = \emptyset$ and $B \ne \emptyset$, they are everything above $b_1$; with both empty, all of $\mathcal{P}$. These sets need not have two endpoints in $\mathcal{P}$, so `find_equilibrium` returns `None` consistently rather than inventing bounds for price types that do not possess them.
