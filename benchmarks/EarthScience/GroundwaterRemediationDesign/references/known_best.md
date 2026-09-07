# Reference and admission record — GroundwaterRemediationDesign

## 1. Reference method

`verification/reference_solver.py` is standalone and uses only public inputs and charged interfaces. Public moving-plume mass-balance search over single wells and treatment transects on a coarse two-rate (380/650 m³/day) sweep, greedily selecting a hypervolume archive.
It is a method witness, not independent high-fidelity verification. Local extraction uses Q*C at the evolving plume position, with activation-aware integration and an extracted/decayed/remaining mass ledger. Three public initial plume components replace the spatially collapsed capture-at-start model.

## 2. Baseline and normalization

The shipped `solution.py` is the zero baseline (measured `0.000000` development and held-out on
the current tree, 2026-09-07). The runnable public reference deliberately searches only the
coarse two-rate transect grid and returns all sixteen selected archive entries. On the
2026-09-08 local re-review it scores `0.929416` development, `0.895475` worst-stress robustness,
`0.924310` held-out transfer and `0.872430` held-out worst-stress robustness, with full validity.
The prior five-plan truncation scored `0.647861` / `0.636191`; it was removed because discarding
useful entries creates artificial reference headroom. The evaluator's internal `_reference_archive`
recomputes a sixteen-plan greedy archive from a denser rate/encounter search (7 pumping rates
x 8 encounter offsets x 1-5 well transects, plus a 32-point single-well rate sweep) on the same
public transport model; that archive's exact-model hypervolume is score one. The anchor is
compute-type headroom, not hidden physics: matching it takes a denser search of the same public
plan family, and scoring above one takes an archive that dominates the evaluator's greedy archive
under the hidden exact transport. Wider or better Pareto coverage remains visible above one.
Changed oracle versions must not be compared as if their score differences were model improvements.

## 3. Capability comparisons and ablations

Run `python scripts/diagnose_pr9_earth.py --output tmp/hardening/diagnostics.json --sweeps`.
The current complete sixteen-plan reference scores `0.929416` development / `0.895475`
robustness (local diagnostic, 2026-09-08). On the 2026-09-07 tree the historical five-plan coarse-grid reference scores `0.647861` development
and `0.636191` robustness, the shipped baseline `0.000000` / `0.000000`. Replaying the historical
public archive on the current oracle scores `0.402759` / `0.200312`. A source-centred, single-well
rate sweep scores `0.030574` / `0.000000`. These are method comparisons rather than isolated
causal ablations because the transport oracle also changed during hardening.

## 4. Shortcut probes

The 16-point source-centred rate sweep is the measured low-dimensional probe and reaches only
`0.030574`. The historical plume-aligned archive reaches `0.402759`, below the current reference.
The complete coarse-greedy construction uses all sixteen allowed archive entries and reaches
`0.929416`; it is now the shipped reference. The score-one anchor uses a denser rate/encounter
grid. One is a reproducible search reference, not a hard score ceiling: better archives remain
measurable above one. The remaining gap to that anchor is mostly search density over the same
public plan family. This honest complete-reference result does not close the owner's difficulty
concern. A clean frontier draw must establish whether unconstrained well positions, activation
times and rates, or robust allocation across interacting plume components, require meaningful
scientific optimization beyond the public coarse family. No entries are discarded and no
arbitrary efficiency penalty is used to lower the reference score. All values in this section are local diagnostics, not frozen
benchmark evidence.

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before exposure, must
show that the first proposal does not reach the competent reference. No calibration or external
review is implied by these local code changes. Server-held worlds and independent model review
remain required.

## 6. Construction errors and revisions

2026-09-05 hardening: Local extraction uses Q*C at the evolving plume position, with activation-aware integration and an extracted/decayed/remaining mass ledger. Three public initial plume components replace the spatially collapsed capture-at-start model.
Standalone references no longer import the hidden evaluator. The task card records the review
lineage, licensing uncertainty and public-world contamination risk. Earlier measurements below
belong to the pre-hardening version and are retained only as history.

## 7. Robustness and reproducibility

Development and heldout metrics remain separate. The new tests cover anchor feasibility,
equivalent-parameter scoring, mass conservation, time refinement, forecast-unit invariance,
instrument error poisoning and malformed submissions as applicable. Formal Linux sandbox
replay, global evidence refresh and independent scientific replication are still pending.
See the task card citations for background; the explicitly declared reduced model is not
certified by those publications.

## Historical pre-hardening record (obsolete scores)

# Known best — GroundwaterRemediationDesign

## Scoring anchor

`verification/reference_solver.py` was the shipped truth-blind plume-aligned multirate archive.
The evaluator recomputed its exact-model hypervolume for every aquifer and assigned it score 1.0.
The shipped baseline scores 0.0.

The normalization was floored at zero and deliberately not capped above one. The reference was a
search witness, not a proven global optimum; a candidate archive with greater exact-model
hypervolume remained visible above 1.0.

The reference and all procedural aquifers were introduced on 2026-09-05. They still require model
calibration, server-held aquifers, MODFLOW replication and independent hydrogeology review.

## Difficulty ladder measurement

The same frozen truth-blind witness was evaluated at all three levels on 2026-09-05. Because this
witness defined the per-level normalization anchor, its combined score remained one; raw
hypervolume and worst-shift robustness expose the changed regime.

| level | exact HV | proxy HV | robustness |
|---:|---:|---:|---:|
| 1 | 0.554781 | 0.540886 | 1.000000 |
| 2 | 0.557896 | 0.521516 | 1.000000 |
| 3 | 0.551663 | 0.488367 | 0.250000 |

The growing proxy/exact separation and level-3 robustness loss confirm that the tighter compliance
and stress settings reach the scored path. Candidate calibration is still required to space the
three levels reliably.

## Reproduce

```bash
python scripts/measure_reference.py \
  --task EarthScience/GroundwaterRemediationDesign \
  --reference verification/reference_solver.py \
  --entry design_remediation
```

`--task` takes the on-disk path under `benchmarks/`, not the logical id
`Hydrology/GroundwaterRemediationDesign` (the fine-grained domain stays in `metadata.yaml`);
the pre-2026-09-07 command passed the logical id and resolved to no directory.

### 2026-09-08 contract and reference correction

The external runner now uses the trusted `sle eval` sandbox path. Transport-stress
multipliers are recomputed when DIFFICULTY changes, rather than remaining frozen at
import-time level 1. The witness returns the complete sixteen-plan archive; a regression
no longer treats an arbitrary reference cutoff of 0.8 as scientific validity. The existing
uncapped normalization is retained. These are local corrections, not frozen Linux evidence
or independent hydrogeology certification.
