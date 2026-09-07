# FootballPoolCovering — bounds, constructions and unresolved evidence

## 1. Executable reference and source

`verification/reference_reconstruction.py` decodes the actual 73/186/486-word codes
published by van Laarhoven, Aarts, van Lint and Wille (JCTA 52, 1989, 304–312).
The packed integer arrays come from Andreas Florath's
[Lean source](https://github.com/florath/covering-codes-lean/blob/460df105545c2d6b04ba71f29de6b56dbda92825/CoveringCodes/Database/Sources/VanLaarhoven1989.lean),
commit 460df105545c2d6b04ba71f29de6b56dbda92825, under BSD-3-Clause. The attribution,
source hash, extraction description and local data hash are in `reference_sources.json`;
`CoveringCodes-LICENSE.txt` retains the upstream copyright and license. No proof
code or paper prose is copied. Run from the task directory:

```sh
python verification/reference_reconstruction.py 8
python verification/reference_greedy.py 8 --seed 2
```

For n9,10, reconstruction appends all possible suffixes to the n8 code, giving
1458/4374 words; these are **not** the published records. This is a replication
shortcut reference, not a truth-blind search method. The data-free greedy program
is a separate executable diagnostic, not a claim of research-level competitiveness.

| n | Hamming product B | published size U | cited lower bound L |
|---|---|---|---|
| 6 | 81 | 73 | 71 |
| 7 | 243 | 186 | 156 |
| 8 | 729 | 486 | 402 |
| 9 | 2187 | 1269 | 1060 |
| 10 | 6561 | 3645 | 2854 |

The numeric ledger is `anchors.json`. The reference table is
[Kéri, ternary bounds](https://old.sztaki.hu/~keri/codes/3_tables.pdf), last revised 2011,
with revision/author context at [the table index](https://old.sztaki.hu/~keri/codes/index.htm).
The n9 upper bound is [Di Pasquale–Östergård2003](https://www.sciencedirect.com/science/article/pii/S0097316503000104);
the n10 upper bound is credited by Kéri to Blokhuis–Lam1984.
For the lower bounds, n6=71 is the large computational result of
[Linderoth–Margot–Thain](https://jlinderoth.github.io/papers/Linderoth-Margot-Thain-07-TR-2.pdf);
n7=156 and n8=402 are proved by [Haas2007](https://www.maths.tcd.ie/EMIS/journals/EJC/Volume_14/PDF/v14i1r27.pdf);
n9=1060 is credited to [Habsieger1996](https://www.combinatorics.org/ojs/index.php/eljc/article/view/v3i2r23),
and n10=2854 to Haas2002 in Kéri's table. This package has not replayed these
nonexistence proofs/computations; the n6 source itself discusses its computational
trust assumptions. The full-score interpretation is conditional on the cited
lower bounds, and requires external coding-theory review.

The [2026 Lean paper](https://arxiv.org/html/2606.09600v1) proves coverage of the
first three old constructions, not their optimality or their latest-record status.
The [2026 Marosi paper](https://arxiv.org/abs/2608.19872) concerns larger alphabets.
Our checks found no conflicting ternary record; they are not a complete literature
or expert audit. None of the five cited lower bounds is known here to be attained.

## 2. Baseline and normalization

`solution.py` uses the two parity checks of the perfect[4,2,3]₃ Hamming code and
appends all free suffixes. Its nine-word core covers 81 inputs; every length-n word
is within distance1 of the core word paired with its own suffix. Thus B=9*3^(n-4),
which the evaluator recomputes by building the code. The score is
`clip((B-size)/(B-L),0,1)`. L is a lower bound, not an invented performance target.
Meeting it with a valid construction would imply optimality conditional on that
bound. A positive bound gap does not prove a better construction is possible.
The fixed-first-symbol enumeration remains a legal but much worse zero-scoring
fallback; it is no longer the normalization anchor.

The search-visible top-level `raw_score` is minus the mean actual artifact size
when all five are valid, and the sentinel 0 when any is invalid. Raw-score values
from invalid outputs are not performance measurements.

## 3. Diagnostic ladder and ablations

Local development checks on 2026-09-08, not formal calibration evidence:

| executable method | sizes n6..10 | mean |
|---|---|---|
| Hamming product | 81/243/729/2187/6561 | 0.000000 |
| exact greedy gains + reverse deletion, seed0 | 89/240/661/1823/5069 | 0.1935793973 |
| same, seed1 | 91/242/666/1841/5057 | 0.1833766948 |
| same, seed2 | 91/240/659/1817/5046 | 0.1971083083 |
| same, seed3 | 91/239/667/1826/5059 | 0.1922156561 |
| public n6..8 codes + free suffixes | 73/186/486/1458/4374 | 0.6870213311 |

The last row has per-instance scores 0.8/0.655172/0.743119/0.646850/0.589965.
Removing its public data and falling back to Hamming loses 0.6870213311; this is
lookup dependence, not an independent-search capability ablation. The data-free
greedy runs do not reach the desired competitive reference tier. A strong search
reference and its capability ablations remain missing.

## 4. Shortcut probes

Actual data reconstruction was reverified against full coverage and previously
scored 0.983766 under fixed-first-symbol-to-record normalization. Under the new
scientific anchors it scores 0.6870213311. Matching all five published record sizes
would score 0.759893 by arithmetic; n9/n10 record constructions are not supplied
or reverified by this package. Public lookup remains possible and is not evidence
of original discovery. No low-dimensional sweep beyond the four declared greedy
seeds is claimed. The former sampled-greedy0.896 probe had no shipped implementation;
it is historical context, not a reproducible reference for this revision.

## 5. Frontier-model draw

Not run. No maintainer-controlled formal freeze, first-proposal comparison, strong
truth-blind search reference or model calibration exists for this revision.
Development tests and Linux sandbox diagnostics do not establish these. Remain candidate.

## 6. Construction errors and corrections

The previous hypothetical n8=400 example contradicted the cited lower bound 402;
it is replaced by 485. Equality with a lower bound is now correctly distinguished
from violation. The unsupported claim of guaranteed improvement from a bounds gap
is removed. The old greedy-to-record gaps were 18/58/178/570/1507, not a dozen words
per instance. Code now catches lazy-iterator/verification exceptions per instance.
Earlier build-time base-3 carry and non-finite-symbol errors remain fixed and tested.

## 7. Robustness and remaining limitations

Tests compare coverage with an independent Hamming-distance implementation, check
the core Hamming code and products, reverify the shipped public constructions,
check asset hashes and per-call greedy determinism, and exercise malformed values.
Published lower-bound arguments and n9/n10 record artifacts are external; no
independent proof replay is claimed. No expert review, maintainer-controlled formal
freeze, frontier draw, global evidence refresh or measured two-hour headroom is claimed.
The score is meaningful bound-gap progress, not proof that every unearned point
is attainable. Public-data contamination is explicitly present.

## Single-file sandbox reproduction

The loader above reads adjacent public data locally. Export a self-contained
candidate before passing it to the networkless, single-file RPC sandbox:

```sh
python verification/reference_reconstruction.py --export /tmp/reference_candidate.py
python frontier_eval/run_eval.py --candidate /tmp/reference_candidate.py --metrics-out /tmp/reference_metrics.json
```

The exported candidate embeds only the attributed public construction and license
notice; it neither imports the evaluator nor reads adjacent files. This is still
a public reconstruction probe, not a truth-blind search reference.

Overlap review: see [frontier_overlap.md](frontier_overlap.md) for both source inventories and their actual counts.
