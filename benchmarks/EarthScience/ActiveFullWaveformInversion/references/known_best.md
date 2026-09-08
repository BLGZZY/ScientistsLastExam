# Reference and admission record — ActiveFullWaveformInversion

## 1. Reference method

`verification/reference_solver.py` is standalone and uses only public inputs and charged
interfaces. It fits a 3x5 velocity-correction grid against smoothed waveforms, upsamples into
5x8, and refines against smoothed then unsmoothed traces. Cubic interpolation and signed
corrections bounded at ±1350 m/s are unchanged in the September 9 revision. The public
acoustic forward model is reproduced in the candidate; no hidden field or evaluator is read.

The witness is not independent high-fidelity verification. Acquisition design, richer velocity
parameterizations and improved nonlinear inversion remain possible improvements. Model
calibration and independent seismology review are still pending.

## 2. Baseline and normalization

The baseline acquires one central shot and confidently reports the supplied background on every
world. It is valid and scores exactly zero on development and held-out worlds at all three levels.
Always abstaining is a separate zero-score candidate.

For depth-weighted relative velocity error `r` measured against the background error, structure
now scores `max(0, (exp(-1.5*r) - exp(-1.5)) / (1-exp(-1.5)))`. Thus exact truth scores one,
background or worse scores zero, and the score is continuous at the background. This removes
the former `exp(-1.5)` floor without changing the sealed-waveform metric or the geometric-mean
combination. The aggregate remains normalized above always refusing; refusal alone cannot earn
positive credit without recovery of supported structure.

Both the structural score and the world inventory changed on September 9. Scores across this
revision are not directly comparable; the reference algorithm itself did not improve.

## 3. Capability comparisons and ablations

Current level-1 method measurements, rounded to six decimals:

| method | development | held-out robustness |
|---|---:|---:|
| baseline | 0.000000 | 0.000000 |
| same reference, one shot | 0.172959 | 0.186975 |
| complete reference, three shots | 0.436901 | 0.290150 |

The single-shot run passes budget=1 to the same solver. It retains source 3, the first shot of
the three-shot acquisition (sources 3/15/28); fitting stages, tolerances, parameterization and
iteration limits are identical. Every world consumes exactly one versus three shots. The gain
is 0.263942 development and 0.103176 held out. This measures the additional acquisitions under
the same fitting procedure, not equal wall-clock compute: more observations also cost more
simulation time. Both versions correctly refuse all three unsupported worlds in each split.

Reproduce with `.research/pr20_fwi_diagnostics.py`. Its report includes source hashes, host,
NumPy version, runtime and per-world metrics. These are method diagnostics, not model draws.
Linux source-bound results are stored in `method_diagnostics_2026-09-09.json` (NumPy 1.26.4,
one BLAS thread). The complete evaluation took 105.18 seconds; one shot took 24.92 seconds.
The previous levels 2/3 numbers in the historical table below do not apply to this revision.

Additional development-machine diagnostics on the revised oracle gave level 2
0.240130/0.000000 and level 3 0.231598/0.000000 (development/heldout). These are exploratory
macOS measurements, not Linux calibration evidence. The stricter skill score exposes that the
current reference does not improve over the background on the supported held-out fields at
these levels. Levels 2/3 are stress settings, not validated competent-reference tiers;
level 1 remains the shipped default. No difficulty-certification claim follows from the ladder.

## 4. Shortcut probes

The three pre-existing candidate methods are retained unchanged:

| probe | development | held-out robustness | development false discovery |
|---|---:|---:|---:|
| background plus old central-shot classification | 0.000000 | 0.000000 | 0.333333 |
| fixed Gaussian lens, 19 amplitudes, three shots | 0.140991 | 0.238192 | 0.000000 |
| straight-ray first-break mean-slowness update | 0.000000 | 0.000000 | 0.000000 |

The fixed-lens and travel-time candidates acquire three shots but classify using the first
shot. The background probe acquires one central shot. They must not all be described as
single-shot methods. The fixed-lens held-out gap to the reference is only 0.051958, substantially
smaller than its development gap; this limitation is disclosed rather than called certification.

A structured attenuating case is added to each split, retaining the old background-only null
and attenuation controls. The development case pairs the supported seed 41023 velocity field
with attenuation; the held-out case uses separate seed 51053 and variant 8. Both carry smooth
anomalies plus the existing reduced-order attenuation parameter, 1.8. No new physical law or
field-fidelity claim is introduced.

On the new development case, the three-shot energy ratio against the background is about 1.230,
so the old `energy_ratio < 0.95` shortcut does not reject it. The complete reference rejects it
after waveform fitting. The central-shot background shortcut incorrectly claims structure,
which the false-discovery metric now exposes. The new held-out case is still rejected by the
old energy gate: the revision demonstrates one concrete failure of that shortcut, not that
all energy-based classification is impossible. Regression tests check non-background fields
in both splits and acoustic-model discrepancy exceeding the stated noise.

## 5. Frontier-model calibration

Not run. No frozen model draw, two-hour headroom, server-held-world result or independent
seismology certification is claimed. This package remains `candidate`. Local software checks
and method comparisons do not establish frontier-model difficulty.

## 6. Construction errors and revisions

- September 9: remove the background structural-score floor, add structure-plus-attenuation
  worlds to both splits, and measure the same solver with one versus three paid shots.
- September 8: the runner delegates to trusted `sle eval`; invalid artifacts no longer count
  as discovery attempts, confidence targets actual recovery, and the baseline makes a legal
  confident background claim. Forward physics are disclosed to avoid simulator-guessing.
- September 7: a constant-lens shortcut outperformed the old single-pass 3x5 reference, prompting
  the current 3x5-to-5x8 continuation reference. Its old 0.615339/0.427110 scores are historical.
- Earlier versions used a fixed-sign lens; the standalone reference now uses signed spatial
  corrections and imports no hidden evaluator.

Historical measurements, **obsolete for the September 9 oracle**:

| reference level before this revision | development | held out |
|---|---:|---:|
| 1 | 0.615339 | 0.427110 |
| 2 | 0.508952 | 0.204432 |
| 3 | 0.454213 | 0.155980 |

Historical background/lens/travel-time probes scored 0.327769/0.379232/0.068824 development.
These values describe prior method diagnostics, not current targets or calibration evidence.

## 7. Robustness and reproducibility

Tests verify exact-field unit scores, zero background/worse-field scores, continuity and
monotonic improvement, structured attenuation in both splits, paid-shot ablation, deterministic
zero baselines at all levels, malformed artifacts, poisoned budgets and external sandbox
entrypoints. Earlier template claims about mass conservation and unrelated forecasting tests
are removed; those were not FWI verification evidence.

```sh
python .research/pr20_fwi_diagnostics.py --output /tmp/fwi-methods.json
python .research/pr20_fwi_diagnostics.py --methods three_shots --level 2 --output /tmp/fwi-level2.json
python .research/pr20_fwi_diagnostics.py --methods three_shots --level 3 --output /tmp/fwi-level3.json
python -m pytest tests/test_new_earth_science_tasks.py tests/test_earth_pr_review_regressions.py \
  tests/test_pr9_earth_hardening.py tests/test_pr9_earth_contracts.py -q
python benchmarks/EarthScience/ActiveFullWaveformInversion/frontier_eval/run_eval.py \
  --candidate benchmarks/EarthScience/ActiveFullWaveformInversion/verification/reference_solver.py \
  --metrics-out /tmp/fwi-reference-sandbox.json
```

The on-disk package is `EarthScience/ActiveFullWaveformInversion`; the registered task ID is
`WavePropagation/ActiveFullWaveformInversion`. Shared frozen evidence is not regenerated by
these contributor diagnostics.
