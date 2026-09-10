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

Use `.research/pr74_diagnostics.py` for reference, no-paid-observation, no-pair-averaging,
no-precision-weighting, fixed-first acquisition, no-continuous-refinement and historical
Michael-reference comparisons on the same revised oracle. Reports contain per-world
components, public residuals, acquisition IDs, ungated scores and gate sweeps.

The revised reference also improves the free path. The paid-information test therefore
requires a development gain above 0.10 and held-out gain above 0.05, replacing the old
Michael solver's held-out gain above 0.30. This narrower claim concerns information
value, not difficulty or certification. Paid observations need not always be essential.

## 4. Shortcut probes and unresolved admission

**PR #74 remains draft: independent four-dimensional grids still approach or exceed
the reference.** `.research/pr74_grid_probe.py` imports neither reference nor evaluator.
It covers 1728-, 6912- and 62208-point grids, fixed-first or residual-based acquisition,
and dense grids with three local refinement rounds. The stronger paired variants
use both nodal-plane observations and uncertainty weighting, and target ambiguity.
All probes use their own default gate (25 degrees); diagnostics sweep 12,16,20,22,25,28,32.
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
`Geophysics/FocalMechanismStressInversion`. Current committed-source Linux replay is
recorded separately in `linux_validation_2026-09-10.json` when completed. The sandbox
entrypoint, charged interface, orthogonality/abstention contracts and separate
confidence calibration remain intact.
