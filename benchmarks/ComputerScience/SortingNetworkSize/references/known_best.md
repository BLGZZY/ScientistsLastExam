# SortingNetworkSize — bounds, constructions and unresolved evidence

## 1. Executable reference and source

`verification/reference_reconstruction.py` reads actual SorterHunter comparator
lists and returns a network; it never returns a literature score in place of a
construction. It is a public-data reconstruction/shortcut probe, **not a
truth-blind independent search reference**. Run it from the task directory:

```sh
python verification/reference_reconstruction.py 13
```

The five upstream JSON files are pinned to commit
`392762f916688756242d90febced98ad157bc6d2`; source URLs and SHA-256 hashes are in
`reference_sources.json`. Bert Dobbelaere's MIT notice is retained in
`SorterHunter-LICENSE.txt`. No paper prose was copied.

| n | Batcher baseline B | published size U | reported lower bound L | reconstruction score |
|---|---|---|---|---|
| 13 | 48 | 45 | 44 | 0.750000 |
| 14 | 53 | 51 | 48 | 0.400000 |
| 15 | 59 | 56 | 53 | 0.500000 |
| 16 | 63 | 60 | 57 | 0.500000 |
| 17 | 85 | 71 | 63 | 0.636364 |

Size records and reported bounds: [Dobbelaere](https://bertdobbelaere.github.io/sorting_networks.html).
The page's 2025-04-21 changelog credits tighter size bounds to Jelmer Firet using
Van Voorhis's principles. The package relies on those reported bounds; it has not
independently reproduced their full derivation. They require algorithms review.
This is not a claim that the bounds are conjectures or incorrect.

An independent, weaker source cross-check is executable as
`evaluator.conservative_lower_bound(n)`: [Harder](https://arxiv.org/pdf/2012.04400),
p.2, states Van Voorhis's `S(n)>=S(n-1)+ceil(log2 n)` and proves `S(12)=39`.
Iterating gives 43/47/51/55/60. These weaker values are **not score targets**, since
the cited compilation already reports tighter bounds. The construction checker
does not certify either external theorem. A construction attaining the scoring
bound is optimal conditional on that bound; attainability remains unresolved.

[Valsalam–Miikkulainen 2013](https://jmlr.org/papers/volume14/valsalam13a/valsalam13a.pdf)
provides the n17 result and states on p.306 that Juillé improved n13 from 46 to 45
in 1995. Green's n16 60-gate result is credited to 1969 by the record compilation.
Record updates must change the ledger and raw record-gap context; they do not
change the score target automatically. Lower-bound updates are an oracle revision.

## 2. Baseline and normalization

`solution.py` builds Batcher odd-even mergesort with positive-infinity padding,
deleting gates that touch sentinel wires. The oracle independently reruns the
same defined construction to compute B. Sizes48/53/59/63/85 are all valid and
score 0. The score is `clip((B-size)/(B-L),0,1)`; published U is not the full-score
anchor. All instances retain raw size, record gap and bound gap. The original
insertion-sort baseline remains legal but is no longer the zero-anchor definition.

The search-visible top-level `raw_score` is minus the mean actual artifact size
when all five are valid, and the sentinel 0 when any is invalid. Raw-score values
from invalid outputs are not performance measurements.

## 3. Diagnostic ladder and ablations

Local development diagnostic on 2026-09-08: Batcher mean 0; the five actual public
networks all pass exact verification and mean 0.5572727273. Removing the network
lookup from the reconstruction and falling back to Batcher loses 0.5572727273.
This only measures data dependence. It is not a capability-complete search ablation.
A strong independent search reference and proper capability ablations are missing.

## 4. Shortcut probes

Public network transcription is an intentional recorded shortcut. It previously
scored 1 under insertion-to-record normalization; it now scores 0.5572727273.
This change fixes the meaning of the anchors, not contamination or model difficulty.
These are reproducible development checks, not a maintainer-controlled formal freeze
or model calibration.
No exhaustive low-dimensional search sweep is claimed.

## 5. Frontier-model draw

Not run. No calibration run IDs, first-proposal comparison or maintainer-controlled
formal freeze exist for this revision. Development tests and Linux sandbox
diagnostics do not establish these. Remain candidate.

## 6. Construction errors and corrections

The earlier file confused meeting a lower bound with violating it and miscredited
Juillé's1995 improvement as a rediscovery; both are corrected. Non-finite float
indices previously escaped from `int(f)` in the checker. They are now rejected
with `is_integer()`, and verifier exceptions are caught at the per-instance boundary.
The official RPC already rejects NaN/Inf; this is an additional oracle-level fix.
Score1 now means attaining a cited bound, not copying a published construction.

## 7. Robustness and remaining limitations

Tests compare bit-mask simulation with independent Boolean simulation, reverify
baseline/public constructions, check attributed asset hashes, malformed outputs,
determinism and target/record separation. No lower-bound proof certificate,
independent domain review, maintainer-controlled formal freeze, model calibration, two-hour search
headroom or global evidence refresh is claimed. A positive gap to L does not prove
an improvement exists. Scores below 1 cannot establish available scientific headroom.

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
