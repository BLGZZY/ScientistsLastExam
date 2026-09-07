# Reference and admission record — CompositeLaminateStacking

Every number in the 2026-09-07 sections is produced by running code in this directory on this
tree. Reproduce the headline numbers with

```
python3 - <<'EOF'
import importlib.util
s=importlib.util.spec_from_file_location("ev","benchmarks/Engineering/CompositeLaminateStacking/verification/evaluator.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s2=importlib.util.spec_from_file_location("ref","benchmarks/Engineering/CompositeLaminateStacking/verification/reference.py")
r=importlib.util.module_from_spec(s2);s2.loader.exec_module(r)
print(m.evaluate(r.design_laminate))
EOF
```

## 1. Reference method

`verification/reference.py` is standalone and uses only public inputs and charged interfaces: ten
seeded permutation starts followed by one adjacent-exchange refinement pass over the symmetric
half stack. The evaluator independently computes the score-one anchor: tiled block-family seeds
(contiguous width-1-3 blocks over all angle orders), a ten-permutation adjacency warm start,
twelve random starts each refined by full pair exchange to convergence, and sixteen
iterated-local-search rounds (three random swaps re-converged). The witness deliberately does
NOT screen structured block families, which is why the block probe below outruns it; that risk is
recorded in section 4. Paired bending moments and both-face Tsai-Hill stress make first-ply
failure depend on stacking order. Independent anisotropic buckling review is pending.

## 2. Baseline and normalization (2026-09-07 instance scale-up)

Panels were scaled to 36-48 plies (symmetric half stacks of 18-24 plies) with deliberately uneven
angle mixes; multinomial half-permutation counts are 3.1e8, 5.6e9, 1.3e11, 3.0e11 (development)
and 8.2e9, 5.5e11 (held out), all above 1e8, so exhaustive half-stack screening is out of reach.
Every instance carries its own load mix and its own paired bending-moment cases; no two share a
moment vector. The interleaved baseline was generalized to largest-remaining-first placement with
a run cap and a mirror-junction repair so it stays feasible on uneven mixes.

| entry | development | held-out policy |
|---|---|---|
| shipped baseline (`solution.py`) | **0.000000** (valid=1) | 0.000 |
| runnable witness (`verification/reference.py`) | **0.768732** | 0.579723 |

Measured wall time on the 2026-09-07 builder machine (in-process `evaluate`): 72.3 s for the
baseline entry (this includes all six anchor searches, cached thereafter) and 0.2 s for the
witness; the metadata envelope is 90 s and the wrapper timeout 300 s, leaving roughly 225 s of
candidate search room. The previous 16-24-ply panels with shared moment cases were retired
because their 2.5e3-3.6e6 half-permutation spaces were nearly exhaustible (witness 0.732584
against a 900-start anchor in 1.6 s; pre-revision numbers retained below as history).

## 3. Capability comparisons and ablations

Run `python scripts/diagnose_pr9_engineering.py --output tmp/hardening/diagnostics.json --sweeps`.
On the pre-revision dirty macOS tree, ten starts plus one adjacent-exchange pass scored 0.732584
development / 0.724395 robustness and the historical random-screening construction clipped to
0.000000 development. On the current panels the ten-start adjacency witness scores 0.768732
against the structured-seed anchor; the anchor components (block seeds, full pair exchange, ILS)
were each added after measuring that a narrower anchor failed to dominate the probe families.

## 4. Shortcut probes

### 2026-09-07 shortcut re-audit (measured on the current tree)

Two families were implemented and run (`tmp/probe_laminate.py` on the builder tree):
lamination-parameter-guided stacking (81 bending-lamination-parameter targets on a 9x9 grid,
greedy outer-to-inner assembly with count-balance and run-cap rules, one candidate per target)
and block/clustered patterns (contiguous same-angle blocks of width 1-3 tiled round-robin over
all 24 angle orders; 322-704 valid patterns per panel).

| family | development | held-out policy |
|---|---|---|
| lamination-parameter-guided greedy | 0.615927 | 0.242384 |
| block/clustered patterns (width 1-3, all angle orders) | **0.992897** | 0.947302 |
| runnable witness (10-start adjacency) | 0.768732 | 0.579723 |

**The block/clustered family nearly closes the anchor gap and exceeds the shipped witness.**
This is the primary open difficulty risk of the package: a few hundred textbook tiled patterns
recover essentially the whole anchor improvement over the baseline. The anchor seeds itself with
these families so the normalization bound still dominates them (their score is 0.9929, not
above 1), but relative to the ten-start adjacency witness the family is a first-shot shortcut of
exactly the kind that led to PermutationFlowShop being withdrawn. Pre-merge decision required:
strengthen the witness (for example block screening plus adjacency, which would need a
correspondingly stronger anchor to stay in the 0.5-0.8 band) or redesign load cases to penalize
clustered stacks. These values are local diagnostics, not frozen benchmark evidence.

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before exposure, must
show that the first proposal does not reach the competent reference; given the block-family
result above, the reference design must be revisited before that draw is meaningful. Server-held
panels and independent model review remain required.

## 6. Construction errors and revisions

2026-09-07 hardening: instances scaled to 36-48 plies with uneven mixes and per-instance load
and moment cases; anchor rebuilt (block seeds + multi-start full pair exchange + ILS) because the
old 900-start random screen was both nearly exhaustible on the small panels and unaffordable on
the large ones; witness kept at ten starts plus one adjacency pass; witness/anchor scores
re-measured (0.768732 development); lamination-parameter and block-family probes measured and
pinned; Task.md spoilers (witness score and anchor mechanics) removed.
2026-09-05 hardening: the witness refines permutations rather than stopping after random
screening; paired bending moments and both-face Tsai-Hill stress make first-ply failure depend
on order; standalone references no longer import the hidden evaluator. Earlier measurements
below belong to the pre-hardening version and are retained only as history.

## 7. Robustness and reproducibility

Development and heldout metrics remain separate. Two consecutive in-process evaluations of the
witness are JSON-identical; all six shipped baselines and solution.py outputs validate. Formal
Linux sandbox replay, global evidence refresh and independent scientific replication are still
pending. See the task card citations for background; the explicitly declared reduced model is
not certified by those publications.

## Historical pre-hardening record (obsolete scores)

# Reference witness

The normalization witness performed 900 fixed-seed permutations of the public symmetric half
laminate and retained the best valid sequence under the same nominal CLT oracle. It is
truth-blind, deterministic and deliberately not a proof of global optimality. It defined score
one in the historical version and stronger sequences could exceed one. No frontier-model or
two-hour calibration has yet been run.
