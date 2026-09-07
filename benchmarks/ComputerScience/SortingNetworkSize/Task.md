# SortingNetworkSize — small sorting networks for 13–17 inputs

## Scientific question

A sorting network is a fixed sequence of compare-exchange gates `[i,j]`, with
`0 <= i < j < n`. Each gate puts the smaller value on wire `i` and the larger on
wire `j`. Find a network that sorts every input using as few comparators as possible.
This is circuit-size optimization with an exact checker; gate order matters.

The published constructive records for n=13..17 are 45/51/56/60/71 gates. Their
optimality remains unresolved in the cited record compilation. Juillé's 1995 search
improved n=13 from 46 to 45; Green's n=16 construction dates to 1969. Matching a
public construction is replication, while a verified smaller network is a potential
record improvement that requires a fresh literature check.

## Submission contract

Edit `solution.py` to define:

```python
def build_network(n: int) -> list:
    """Return [i,j] compare-exchange gates, with integral 0 <= i < j < n."""
```

The only input is `n`, which takes **13, 14, 15, 16, 17**. No other arguments or
problem keys are passed. Return a list of pairs; tuples and numeric NumPy arrays
are also supported by the transport. Materialize iterators before returning them.
Finite integral floats such as `5.0` are accepted. Strings, booleans, nonintegral
numbers, NaN/Inf and out-of-range indices are invalid. At most `n*n` gates are
accepted; duplicates and redundant gates are legal but counted.

## Verification

The oracle checks every one of the `2^n` Boolean inputs using bit masks. The 0-1
principle makes this sufficient for sorting all inputs. It never trusts reported
size or correctness. Invalid outputs score zero for that n; malformed values do
not abort the evaluator. The checker budget is a maximum output size, not a score
cap on otherwise valid discoveries.

## Scoring and the meaning of 0 and 1

The zero anchor `B(n)` is recomputed from **Batcher odd-even mergesort**, padding
with positive-infinity sentinel wires and deleting gates that touch them. This is
the executable `solution.py` baseline, not insertion sort.

The target `L(n)` is the **size lower bound reported by the cited Dobbelaere
compilation**, separate from the size of its best published construction:

| n | Batcher B (score 0) | published size U | cited lower bound L (score 1) | record score |
|---|---|---|---|---|
| 13 | 48 | 45 | 44 | 0.750000 |
| 14 | 53 | 51 | 48 | 0.400000 |
| 15 | 59 | 56 | 53 | 0.500000 |
| 16 | 63 | 60 | 57 | 0.500000 |
| 17 | 85 | 71 | 63 | 0.636364 |

```text
score(n) = clip((B(n) - size) / (B(n) - L(n)), 0, 1)
combined_score = mean(score(n))
```

One means that the submitted valid construction attains the cited lower bound;
**its optimality follows conditional on the external lower-bound result**. The
oracle proves the construction sorts, not the lower-bound theorem. The source's
2025-04-21 update attributes its tighter bounds to Jelmer Firet using Van Voorhis's
principles; this package has not independently formalized that derivation and needs
algorithms review. Attainability is unknown. The interval below 1 is not evidence
that the remaining improvement is possible or achievable within an agent budget.

A smaller construction is rewarded even when it beats the published record: for
n=16, sizes 63,60,59,57 correspond to scores 0,0.5,2/3,1 respectively. The last two
are arithmetic illustrations, not claims that those networks exist. A purported
valid construction below L contradicts the cited bound and is flagged for audit,
rather than silently receiving full score.

Per-instance metrics preserve `size`, `baseline_size`, `sota_ref` (published U),
`record_gap = size-U`, `lower_bound`, `lower_bound_gap = size-L`, `target_attained`
and `beats_known_record`. The legacy `beat_sota` aggregate reports any record
improvement, independently of the normalized score. `target_attainment_rate`
reports the fraction of instances attaining the cited bound.

The top-level `raw_score` is the negative mean submitted size across all five
instances when all are valid: a larger value means fewer comparators.
It is an unnormalized scientific metric. If any instance is invalid, `raw_score`
is the sentinel 0 and must be interpreted together with `valid=0`.

## Diagnostic ladder and limitations

A local development check reverified all five published SorterHunter gate lists:
45/51/56/60/71 and mean **0.557273**, versus Batcher's **0.000000**. Removing access
to those data in this reconstruction program leaves Batcher and loses 0.557273;
this is a lookup-dependence probe, not a search-method ablation. Insertion sort also
scores zero and remains a worse legal fallback.

A runnable, attributed reconstruction and its exact data hashes are supplied under
`verification/` for reviewers. It uses public data and is **not** a truth-blind
search reference. Reweighting stops public record lookup from scoring 1; it does
not demonstrate research difficulty or remove contamination. No frontier-model
calibration, strong independent search reference, capability ablation ladder or
clean Linux evidence is claimed. The task remains a candidate.

## Rules

- Only edit `solution.py`; keep the signature and pair-list output.
- Use NumPy/stdlib, CPU, seconds per instance.
- Do not read `verification/` or `frontier_eval/`.

## Relations and differences

- `Algorithm/TensorRank555` and `Algorithm/MatrixMultiplicationRank` optimize
  algebraic decompositions; here the artifact is an ordered comparator circuit.
- `Mathematics/Superpermutation` optimizes string length; this task checks circuit
  behavior on every Boolean input.
- `Mathematics/CapSet` and `Mathematics/RamseyLowerBound` build extremal sets or
  colorings rather than sorting circuits.
- `Mathematics/FootballPoolCovering` also measures progress toward a size lower
  bound, but verifies ternary coverage rather than sequential circuit semantics.

Sources: [Dobbelaere's record compilation](https://bertdobbelaere.github.io/sorting_networks.html),
[Harder's size-bound paper](https://arxiv.org/abs/2012.04400), and
[Valsalam–Miikkulainen 2013](https://jmlr.org/papers/volume14/valsalam13a/valsalam13a.pdf).
