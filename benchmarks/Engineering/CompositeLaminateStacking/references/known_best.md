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

`verification/reference.py` is standalone and uses only public inputs and charged interfaces:
thirteen seeded permutation starts followed by adjacent-exchange refinement of the symmetric
half stack to convergence. The evaluator independently computes the score-one anchor: tiled
block-family seeds (contiguous width-1-3 blocks over all angle orders, filtered by the run
limit), a twenty-four-permutation adjacency warm start, eight random starts each refined by
full pair exchange to convergence, and twelve iterated-local-search rounds. Paired bending
moments and both-face Tsai-Hill stress make first-ply failure depend on stacking order.
Independent anisotropic buckling review is pending.

## 2. Baseline and normalization (2026-09-07 second revision: run limit 2, three conflicting cases)

Panels span 36-48 plies (symmetric half stacks of 18-24 plies) with deliberately uneven angle
mixes; multinomial half-permutation counts are 3.1e8, 5.6e9, 1.3e11, 3.0e11 (development) and
8.2e9, 5.5e11 (held out). Every instance carries THREE paired load/moment cases whose optima
conflict: an axial case (0-dominant), a transverse case (90-dominant) and a shear/twisting case
(Mxy-dominant, which punishes the D16/D26 coupling that clustered +/-45 blocks cannot zero).
The manufacturing limit is now at most TWO consecutive equal plies, a standard matrix-cracking
constraint that removes tiled width-3 block patterns outright.

| entry | development | held-out policy |
|---|---|---|
| shipped baseline (`solution.py`) | **0.000000** (valid=1) | 0.000 |
| runnable witness (`verification/reference.py`) | **0.740840** | 0.874556 |
| block/clustered family (probe) | 0.557119 | 0.820202 |
| lamination-parameter-guided family (probe) | 0.372152 | 0.597202 |

Measured wall time on the 2026-09-07 builder machine (in-process `evaluate`): 20.4 s for the
baseline entry (includes all six anchor searches, cached thereafter) and 0.3 s for the witness;
the metadata envelope is 45 s and the wrapper timeout 300 s, leaving over 250 s of candidate
search room. The witness score is sensitive to its start count (0.616 at ten starts, 0.784 at
fourteen); thirteen starts are pinned by the regression tests.

## 3. Capability comparisons and ablations

Run `python scripts/diagnose_pr9_engineering.py --output tmp/hardening/diagnostics.json`.
Revision history on this tree: the pre-2026-09-07 16-24-ply two-case panels carried a witness
of 0.732584 against a 900-start anchor; the first scale-up (two cases, run limit 3) measured the
ten-start witness at 0.768732 but let the block family reach 0.992897; the second revision
(three conflicting cases, run limit 2) measures the thirteen-start witness at 0.740840 with the
block family at 0.557119, 0.184 below the reference. Earlier measurements are retained here
only as history.

## 4. Shortcut probes

### 2026-09-07 shortcut re-audit (measured on the current tree)

Two families are implemented and run (`tmp/probe_laminate.py` on the builder tree;
lamination-parameter-guided: 81 bending-lamination-parameter targets on a 9x9 grid with greedy
outer-to-inner assembly, count-balance and run-cap rules; block/clustered: contiguous
same-angle blocks of width 1-3 tiled round-robin over all 24 angle orders, 96-240 valid
patterns per panel under the run limit):

| family | development | held-out policy | gap to witness |
|---|---|---|---|
| lamination-parameter-guided greedy | 0.372152 | 0.597202 | 0.369 below |
| block/clustered patterns (width 1-3, all angle orders) | **0.557119** | 0.820202 | **0.184 below** |
| runnable witness (13-start adjacency to convergence) | 0.740840 | 0.874556 | — |

**The near-ceiling clustering shortcut is closed.** On the pre-revision two-case run-limit-3
panels the block family measured 0.992897, above the then-witness of 0.768732 - the same
first-shot disease that led to PermutationFlowShop being withdrawn. Two physics changes fixed
it: the run limit of two consecutive plies (a real matrix-cracking constraint) and the
shear/twisting third load case whose Mxy-dominant moments punish clustered stacks through the
bending-twisting coupling they cannot avoid. The best block variant now sits 0.184 below the
reference, and the lamination-parameter family 0.369 below. These values are local
diagnostics, not frozen benchmark evidence.

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before exposure, must
show that the first proposal does not reach the competent reference. Server-held panels and
independent model review remain required.

## 6. Construction errors and revisions

2026-09-07 second hardening (admission-bar fix): the block-family probe at 0.992897 exceeded
the witness; resolved by the run-limit-2 manufacturing constraint, three conflicting
load/moment cases per panel (axial/transverse/shear-twist), a thirteen-start
adjacency-to-convergence witness and a twenty-four-draw anchor warm start. All numbers
re-measured and pinned.
2026-09-07 first hardening: instances scaled to 36-48 plies with uneven mixes and per-instance
load and moment cases; anchor rebuilt as block seeds plus multi-start full pair exchange plus
ILS; witness/anchor spoilers removed from Task.md; probes measured and pinned.
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

The normalization witness performed 900 fixed-seed permutations of the public symmetric half
laminate and retained the best valid sequence under the same nominal CLT oracle. It is
truth-blind, deterministic and deliberately not a proof of global optimality. It defined score
one in the historical version and stronger sequences could exceed one. No frontier-model or
two-hour calibration has yet been run.
