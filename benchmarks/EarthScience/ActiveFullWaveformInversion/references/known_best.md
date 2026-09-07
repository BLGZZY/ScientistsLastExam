# Reference and admission record — ActiveFullWaveformInversion

## 1. Reference method

`verification/reference_solver.py` is standalone and uses only public inputs and charged interfaces. Coarse-to-fine grid-continuation least squares: a 3x5 velocity correction grid is fitted against smoothed waveforms, upsampled into a 5x8 grid and refined twice (smoothed, then unsmoothed), with cubic-spline interpolation from the correction grid onto the model grid and signed corrections bounded at ±1350 m/s.
It is a method witness, not independent high-fidelity verification. Source design, richer parameter families and more complete inversion remain open.

## 2. Baseline and normalization

The shipped `solution.py` is the baseline. Tests check valid near-zero development scores.
Optimization references define one through recomputed objective differences; discovery scores
retain their fixed supported-world ceilings and refusal normalization. Changed oracle versions
must not be compared as if their score differences were model improvements.

## 3. Capability comparisons and ablations

Run `python scripts/diagnose_pr9_earth.py --output tmp/hardening/diagnostics.json --sweeps`.
On the current dirty macOS tree the grid-continuation reference scores `0.615339` development
(`mechanism_score=0.743559`) and `0.427110` robustness; replaying the historical public
smooth-lens method on the current oracle scores `0.249539` development
(`mechanism_score=0.499693`) and `0.209638` robustness. This is a method comparison, not an
isolated causal ablation: the reference and oracle both changed during hardening. A clean Linux
per-capability ladder remains unmeasured.

## 4. Shortcut probes

### 2026-09-07 shortcut re-audit

Three first-shot no-inversion families were implemented and run against the shipped evaluator
(unchanged since 2026-09-05). Each uses the reference solver's own public stage-1
null/attenuation classification (relative misfit < 0.006 or energy ratio < 0.95 against the
background traces abstains), so refusal and false-discovery behaviour match the reference:

| probe | construction | development | held-out robustness | FDR | refusal |
|---|---|---:|---:|---:|---:|
| (a) zero-inversion background return | one shot, classification only, returns the background grid | 0.327769 | 0.381455 | 0.000 | 1.000 |
| (b) constant lens | one fixed-shape Gaussian lens, single amplitude swept over 19 values, no spatial inversion | 0.379232 | 0.458013 | 0.000 | 1.000 |
| (c) travel-time only | first-break picks, straight-ray linearized mean-slowness update, no waveform fitting | 0.068824 | 0.071974 | 0.000 | 1.000 |

Finding: probe (b), which never inverts spatial structure, scored `0.379232` against the then-current
single-pass 3x5 reference's `0.356670` — the reference was below a no-inversion family. That closed
this audit's central exposure: the reference was rebuilt as the coarse-to-fine 3x5→5x8
grid-continuation fit above (`0.615339` development), and the probe margins are pinned in
`tests/test_pr9_earth_hardening.py` (bounds 0.35 / 0.40 / 0.10). Reproduce the pinned measurements with:

```bash
python -m pytest tests/test_pr9_earth_hardening.py -k fwi_shortcut -s
```

The historical smooth-lens replay (0.249539) is a cross-version comparison, not part of this sweep.
All numbers in this section are local macOS diagnostics, not frozen benchmark evidence.

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before exposure, must
show that the first proposal does not reach the competent reference. No calibration or external
review is implied by these local code changes. Server-held worlds and independent model review
remain required.

## 6. Construction errors and revisions

2026-09-07 revision: the shortcut re-audit above measured a constant lens above the 2026-09-05
single-pass 3x5 reference. The reference was replaced by the coarse-to-fine grid-continuation
fit (development `0.356670` → `0.615339`), and probe upper bounds were pinned in
`tests/test_pr9_earth_hardening.py`. The evaluator itself is unchanged.

2026-09-05 hardening: The reference then optimized signed spatial velocity corrections instead of
drawing a fixed negative lens. Standalone references no longer import the hidden evaluator. The task
card records the review lineage, licensing uncertainty and public-world contamination risk.
Earlier measurements below belong to the pre-hardening version and are retained only as history.

## 7. Robustness and reproducibility

Development and heldout metrics remain separate. The new tests cover anchor feasibility,
equivalent-parameter scoring, mass conservation, time refinement, forecast-unit invariance,
instrument error poisoning, malformed submissions and the three pinned shortcut probes as
applicable. Formal Linux sandbox replay, global evidence refresh and independent scientific
replication are still pending. See the task card citations for background; the explicitly
declared reduced model is not certified by those publications.

## Historical pre-hardening record (obsolete scores)

# Known best — ActiveFullWaveformInversion

## Scoring anchor

`verification/reference_solver.py` is the shipped truth-blind grid-continuation witness. The
evaluator recomputes its score from the same public acquisition interface available to a
candidate; it does not read the hidden velocity field.

Measured on 2026-09-07, the shipped baseline scores `0.000000` and the reference scores
`0.615339` on development worlds with `0.427110` robustness. The previous single-pass 3x5
reference measured `0.356670` / `0.189769` on 2026-09-05 and was replaced after the constant-lens
probe exceeded it. This is a reproducibility anchor, not a claim of optimality or real-Earth
validity. The task still requires model calibration, server-held worlds, higher-fidelity
replication and independent seismology review.

## Difficulty ladder measurement

The frozen grid-continuation witness was evaluated at all three levels on 2026-09-07:

| level | combined | held-out robustness |
|---:|---:|---:|
| 1 | 0.615339 | 0.427110 |
| 2 | 0.508952 | 0.204432 |
| 3 | 0.454213 | 0.155980 |

The development score decreases monotonically and the shipped baseline scores `0.000000` at every
level. These are initial ladder measurements rather than a claim of fully calibrated spacing.

## Reproduce

```bash
python scripts/measure_reference.py \
  --task EarthScience/ActiveFullWaveformInversion \
  --reference verification/reference_solver.py \
  --entry invert_velocity_model
```

`--task` takes the on-disk path under `benchmarks/`, not the logical task id: the public id and
`metadata.yaml` domain remain `WavePropagation/ActiveFullWaveformInversion` (the fine-grained
domain is registered under the `EarthScience` discipline in `sle/benchmark_layout.py`, which is
the sanctioned pattern). The pre-2026-09-07 command passed the logical id and resolved to no
directory; it has been corrected here and in the sibling earth tasks' records.
