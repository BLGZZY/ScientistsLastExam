# FootballPoolCovering — small ternary radius-one covering codes

## Scientific question

For n football matches with three possible outcomes, choose as few tickets as
possible while guaranteeing at least n-1 correct predictions for every outcome.
Equivalently, construct a code C in `{0,1,2}^n` whose Hamming balls of radius one
cover the whole space. The minimum size is `K_3(n,1)`.

The cited tables leave n=6..10 unresolved, with constructive upper bounds
73/186/486/1269/3645. The first three codes were published by van Laarhoven,
Aarts, van Lint and Wille in 1989. A 2026 Lean project rechecked those constructions;
this establishes their validity, not a new record or a complete current-record audit.

## Submission contract

Edit `solution.py` to define:

```python
def build_covering(n: int) -> list:
    """Return length-n words over {0,1,2}, covering every word within distance 1."""
```

The only input is `n`, taking **6,7,8,9,10**; no other arguments or keys are passed.
Return a list of length-n words. Tuples and numeric NumPy arrays are also supported
by the transport; materialize iterators before returning. Finite integral floats
are accepted. Booleans, strings, nonintegral numbers, NaN/Inf and symbols outside
`{0,1,2}` are invalid. There may be at most `3^n` submitted words. Duplicate words
are legal but counted, so removing a duplicate can improve size without hurting
coverage.

## Verification

For every submitted word, the oracle marks that word and its `2n` one-coordinate
neighbors using base-3 index arithmetic. Every one of the `3^n` outcomes must be
marked. The checker computes size itself. Invalid outputs score zero for that n;
malformed values do not abort evaluation.

## Scoring and the meaning of 0 and 1

The zero anchor is an executable **[4,2,3]₃ Hamming-code product**, not the much
larger fixed-first-symbol enumeration. Nine words cover all four-coordinate inputs;
appending every possible length-(n-4) suffix preserves covering radius one. Thus
`B(n)=9*3^(n-4)`. The oracle recomputes the construction size.

The full-score target `L(n)` is the cited published **lower bound**, separate from
the published constructive upper bound `U(n)`:

| n | Hamming product B (score 0) | published size U | cited lower bound L (score 1) |
|---|---|---|---|
| 6 | 81 | 73 | 71 |
| 7 | 243 | 186 | 156 |
| 8 | 729 | 486 | 402 |
| 9 | 2187 | 1269 | 1060 |
| 10 | 6561 | 3645 | 2854 |

```text
score(n) = clip((B(n) - size) / (B(n) - L(n)), 0, 1)
combined_score = mean(score(n))
```

One means a valid submitted cover reaches the cited lower bound; its optimality
follows conditional on that external bound. The oracle checks coverage, not the
published nonexistence argument. These bounds have not been independently replayed
inside this package. **Attainability is unknown**: a lower/upper-bound gap does not
prove a smaller construction exists or measure agent search headroom. The task
remains a candidate pending coding-theory review and calibration.

For n=8, sizes 729,486,485,402 have scores 0,0.743119,0.746177,1. The last two are
normalization examples, not known constructions. A purported valid cover below L
contradicts the cited bound and is flagged for audit instead of silently receiving
full score. Equality with a valid lower bound would establish optimality.

Per-instance results retain `size`, `baseline_size`, `sota_ref` (published U),
`record_gap = size-U`, `lower_bound`, `lower_bound_gap = size-L`, `target_attained`
and `beats_known_record`. `beat_sota` reports any record improvement separately;
`target_attainment_rate` is the fraction attaining the cited bound. Keep original
sizes when comparing improvements: a one-word reduction has different normalized
weight across n.

The top-level `raw_score` is the negative mean submitted size across all five
instances when all are valid: a larger value means fewer codewords.
It is an unnormalized scientific metric. If any instance is invalid, `raw_score`
is the sentinel 0 and must be interpreted together with `valid=0`.

## Diagnostic ladder and limitations

The following local development diagnostics have executable methods. They are not
clean-Linux calibration evidence or proof of a model difficulty threshold:

| Method | sizes for n=6..10 | mean score |
|---|---|---|
| Hamming product, no record data | 81/243/729/2187/6561 | 0.000000 |
| Full greedy set cover + reverse deletion, seed 0 | 89/240/661/1823/5069 | 0.193579 |
| Same algorithm, seed 2 | 91/240/659/1817/5046 | 0.197108 |
| Public 1989 codes for n6..8 + free-suffix product | 73/186/486/1458/4374 | 0.687021 |

The last row is **reconstruction with public record data**, not an independent
search reference. Removing that data and using the Hamming product loses 0.687021;
this is a lookup-dependence probe, not a scientific capability ablation. The n9
and n10 extensions do not match their published records. Matching all five listed
records would yield 0.759893 by normalization arithmetic; this package does not
supply the n9/n10 record artifacts and does not claim to have reverified them.

Public-data replication can still earn substantial score. No strong truth-blind
search reference or frontier-model draw has been supplied. The older claim that
only a dozen codewords separate generic greedy from the records was inaccurate.

## Rules

- Only edit `solution.py`; keep the signature and list-of-words output.
- Use NumPy/stdlib, CPU, seconds to a minute per instance.
- Do not read `verification/` or `frontier_eval/`.

## Relations and differences

- `Mathematics/NonlinearCodeRecords` is a binary packing problem with a minimum
  pairwise distance; this task minimizes a ternary covering with radius one.
  Packing and covering differ but can share algebraic constructions such as
  Hamming codes; they are not disjoint bodies of theory.
- `SyntheticBiology/OrthogonalDNACodewords` has biological constraints absent here.
- `Mathematics/CapSet` and `Mathematics/RamseyLowerBound` optimize other extremal
  set/coloring properties rather than full Hamming-space coverage.
- `Algorithm/SortingNetworkSize` and `Mathematics/DegreeDiameter` also verify
  combinatorial constructions but use circuit and graph semantics respectively.

Sources: [Kéri's covering-code tables](https://old.sztaki.hu/~keri/codes/index.htm),
[Haas's lower-bound proof for n7/n8](https://www.maths.tcd.ie/EMIS/journals/EJC/Volume_14/PDF/v14i1r27.pdf),
and [the 2026 Lean reconstruction](https://arxiv.org/html/2606.09600v1).
