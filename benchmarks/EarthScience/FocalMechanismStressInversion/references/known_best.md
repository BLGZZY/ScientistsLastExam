# Reference and admission record — FocalMechanismStressInversion

## 1. Reference method

The standalone NumPy/SciPy reference uses public observations and the 16-credit
interface. It averages the two observed double-couple tensors per event, projects
onto double-couple directions, fuses independent coarse/fine observations by inverse
angular variance, and minimizes signed normalized-shear angular squared error. A
1728-point global seed grid and three continuous L-BFGS-B starts fit the four stress
parameters; the updated fit additionally starts from the previous estimate. Paid
observations target ambiguous plane assignments. The mean-residual refusal threshold
is 20 degrees. This is an approximate SDR-noise treatment, not an exact likelihood.

Michael (1984), doi:10.1029/JB089iB13p11517, motivates linear stress fitting; Bott
(1959), doi:10.1017/S0016756800059987, motivates the shear-direction assumption.
Vavryčuk (2014), https://doi.org/10.1093/gji/ggu224, discusses the equal-shear assumption
and how fault-selection errors particularly affect the shape ratio. Our implementation
is a benchmark-specific method, not a reproduction or published SoTA claim.

## 2. Baseline and normalization

`solution.py` still fits one tensor to first-listed planes, without iteration,
re-analysis or refusal. The score formula and supported/refusal world inventories
are unchanged. Normalization subtracts the always-abstain score; axis, R and plane
recovery combine geometrically. Functional tests require a valid zero baseline and
a truth submission scoring one. Tests passing does not establish admission difficulty.

## 3. Capability comparisons and ablations

Clean committed-source Linux results at `6d36055`,
NumPy 1.26.4 / SciPy 1.13.1. Scores use the fixed
reference gate (20 degrees), grids' own gate (25 degrees), and unchanged normalization.

| method | development | held out | confirmation |
|---|---:|---:|---:|
| reference | 0.783503 | 0.796709 | 0.766461 |
| no_paid_reanalysis | 0.650629 | 0.721542 | 0.711099 |
| no_pair_averaging | 0.710719 | 0.646892 | 0.689676 |
| no_precision_weighting | 0.721272 | 0.793488 | 0.760454 |
| fixed_first_reanalysis | 0.745195 | 0.783597 | 0.755679 |
| no_continuous_refinement | 0.416545 | 0.535678 | 0.361081 |
| historical_reference_on_revised_oracle | 0.626122 | 0.579942 | 0.693671 |
| baseline | 0.000000 | 0.000000 | 0.000000 |

`no_pair_averaging` removes the complete moment-projection/fusion path, so it is not
an isolated ablation of projection alone. Precision weighting and acquisition policy
can have small or non-monotonic effects on different finite inventories. The additional
training inventory includes one mixed-world false acceptance by the reference; all
world rows and threshold sweeps are retained in `method_diagnostics_2026-09-10.json`.

Paid re-analysis gains are 0.132874 development,
0.075167 held out and 0.055362 confirmation. The revised method also
improves the free path. The regression therefore pins gains above 0.10 development
and 0.05 held out instead of the historical Michael solver's 0.30 held-out gap.
This asserts information value, not admission difficulty or universal necessity.

## 4. Shortcut probes and unresolved admission

**PR #74 remains draft: independent four-dimensional grids still approach or exceed
the reference.** `.research/pr74_grid_probe.py` imports neither reference nor evaluator.
It covers 1728-, 6912- and 62208-point grids, fixed-first or residual-based acquisition,
and dense grids with three local refinement rounds. The stronger paired variants
use both nodal-plane observations and uncertainty weighting, and target ambiguity.
All probes use their own default gate (25 degrees); diagnostics sweep 12,16,20,22,25,28,32.

| method | development | held out | confirmation |
|---|---:|---:|---:|
| raw1728 | 0.481383 | 0.602416 | 0.516338 |
| raw6912 | 0.553186 | 0.553314 | 0.540273 |
| raw6912_worst | 0.552374 | 0.592510 | 0.524922 |
| raw62208 | 0.617915 | 0.596107 | 0.562127 |
| raw62208_refined | 0.649482 | 0.592259 | 0.584944 |
| paired6912 | 0.701195 | 0.712214 | 0.648652 |
| paired62208 | 0.773284 | 0.753407 | 0.769789 |
| paired62208_refined | 0.775136 | 0.814230 | 0.758167 |

The dense refined paired grid exceeds the reference on held out. A dense paired
grid also matches it on confirmation. The full sweep, including thresholds that
outperform the default, is part of the admission audit; no family bound is claimed.
A weak inherited gate must not be treated as a shortcut-family upper bound.

The old grid-separation unit test was removed because it encoded that misleading
claim. Geometry, valid artifacts, signed shear, budget and permutation invariance
are now tested independently. The scientific admission audit retains the previous
requirements (absolute reference gap greater than 0.15 AND probe below 75% of reference)
and exits 1 when any swept probe violates them:

```bash
python .research/pr74_check_admission.py /tmp/development.json /tmp/heldout.json
```

This is an explicit unresolved audit, not an expected failure hidden in a green suite.
The maintainer's September 10 review motivated this correction:
https://github.com/Geniusyingmanji/ScientistsLastExam/pull/20#issuecomment-5614869028
Exact maintainer source is unavailable; these probes are independent members of the
same family, not an exact replay of the reported numbers.

## 5. Frontier-model calibration

Not run. Server-held catalogs, independent seismology review, and frozen frontier-model
calibration remain absent. Local seed confirmation and Linux sandbox validation do not
replace them. No scoring-policy exception has been requested or assumed.

## 6. Construction errors and revisions

The September 10 revision fixes a geometry error: negative-z normal representations
could produce dips above 90 degrees, then `_perturb_plane` clipped dip even at zero
noise. Simultaneous normal/slip sign flips now preserve the moment tensor, and noisy
SDR coordinates are canonicalized through vectors. Full-sphere, horizontal/vertical
and auxiliary-plane tests cover this failure. A grid output near zero azimuth could
also round to exactly 360 degrees; reference and probe now wrap the final float.

The revised level 3 has 96 events (formerly 48), 10/3 degree coarse/fine SDR noise
(formerly 8.5/2.6), and a normalized shear floor of 0.04 (formerly 0.14). This admits
more weak-shear mechanisms and reduces the fraction that can be reanalyzed. It does
not change scoring constants and has not solved the shortcut-separation problem.
Noise is coordinate-dependent; the stress-axis prior is not isotropic; the sampling
floor is a normalized shear magnitude, not frictional slip tendency. Independent
scientific review of these modeling choices remains required.

Historical documentation is archived in `.research/pr74_historical_known_best.md`.
The former oracle and Michael solver are preserved as `.research/pr74_evaluator_before.py`
and `.research/pr74_reference_before.py`. September 9 JSON evidence describes that
historical implementation only. Obsolete PR20 drivers were removed because their
gate mutation and private-helper instrumentation no longer match the reference.

## 7. Robustness and reproducibility

Source hashes were frozen in `.research/pr74_source_freeze.json` after development
and predeclared training, before revised held-out and confirmation evaluation.
The additional 15-world training/confirmation inventories were predeclared in
`.research/pr74_revision_plan.md`. They are local method tests, not secret held-out
worlds. Reference/oracle/probe parameters were not retuned after confirmation.

```bash
python .research/pr74_diagnostics.py --split development --output /tmp/development.json
python .research/pr74_diagnostics.py --split heldout --output /tmp/heldout.json
python .research/pr74_diagnostics.py --split confirmation --output /tmp/confirmation.json
python scripts/measure_reference.py \
  --task EarthScience/FocalMechanismStressInversion \
  --reference verification/reference_solver.py --entry infer_stress_orientation
```

The last command uses the on-disk EarthScience path; the logical registry ID remains
`Geophysics/FocalMechanismStressInversion`. Committed-source Linux replay is
recorded in `linux_validation_2026-09-10.json`. The sandbox
entrypoint, charged interface, orthogonality/abstention contracts and separate
confidence calibration remain intact.

Continuous optimization is sensitive to numerical-library versions; repeatability is
verified within the recorded Linux environment, not bitwise across platforms.

### Linux validation of the revised implementation

162 passed, 87 warnings, 8 subtests passed in 188.38s (0:03:08). Contribution gate: 15/15. Two real sandbox reference
runs returned identical complete metric dictionaries in 16.96 / 17.41 seconds, within the 300-second
limit. The scientific admission audit explicitly exits 1 (BLOCKED). The full repository
suite and GitHub CI are not claimed passed. Existing administrator permission was used
for namespace creation; candidate uid/gid 65534 and bubblewrap/seccomp remain intact.
Global evidence refresh and certification remain maintainer responsibilities.

For a real sandbox replay on Linux, use:

```bash
python -m sle eval --task Geophysics/FocalMechanismStressInversion \
  --candidate benchmarks/EarthScience/FocalMechanismStressInversion/verification/reference_solver.py \
  --timeout 300 --allow-uncertified
```
