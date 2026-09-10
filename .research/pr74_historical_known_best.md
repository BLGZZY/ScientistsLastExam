# Historical record through b565eac — superseded by PR74 revision

Commands below require checkout b565eac; they are not current-runtime commands.
The inherited-gate separation conclusion was rejected by the maintainer.

# Reference and admission record — FocalMechanismStressInversion

## 1. Reference method

`verification/reference_solver.py` is standalone and uses only the public catalog and
the charged re-analysis budget. Multi-start plane-choice initialization (all-a, all-b,
six seeded random rows), alternating linear least-squares deviatoric-tensor fits with
per-event plane swaps, re-analysis of the worst-misfit events within budget, and
refusal when the converged misfit distribution exceeds a mean of 18 degrees or a 35
degree tail fraction of 0.18. It is a method witness, not independent verification; it
deliberately lacks bootstrapped confidence intervals, gridded four-dimensional global
search, and multi-regime clustering.

## 2. Baseline and normalization

The shipped `solution.py` fits one tensor on the first-listed planes without iteration,
budget use or regime checks, and never abstains. Measured on 2026-09-05 the baseline
scores exactly `0.000000` development and `0.000000` robustness; submitting the true
axes, ratio and plane row scores one.

## 3. Capability comparisons and ablations

Current shipped level-3 replay (2026-09-08):

| variant | development | held out |
|---|---:|---:|
| complete reference | 0.622620 | 0.573022 |
| same solver, no paid re-analysis | 0.469429 | 0.139507 |
| same solver, no refusal gates | 0.022620 | 0.000000 |
| best of twelve constant regimes | 0.000000 | 0.000000 |

Reproduce with `python .research/pr20_diagnostics.py --output /tmp/pr20-focal.json`.
The script uses the public-input reference and charged interface, keeps the evaluator
unchanged, and reports host/runtime details. This is method diagnostic evidence,
not a clean frontier-model draw. Paid re-analysis adds 0.153192 development and
0.433516 held out; refusal contributes separately. Historical tables below are
retained with their original dates and do not describe the current default.


Historical level-1 oracle-direct ablations, measured 2026-09-05 (no longer the shipped default):

| variant | development | robustness | FDR | refusal |
|---|---:|---:|---:|---:|
| full reference | 0.6983 | 0.7307 | 0.00 | 1.00 |
| no re-analysis spend | 0.7195 | 0.6874 | 0.00 | 1.00 |
| no multistart (all-a only) | 0.6983 | 0.7307 | 0.00 | 1.00 |
| no refusal gates | 0.0983 | 0.0000 | 1.00 | 0.00 |

Re-analysis trades development smoothness for held-out robustness on these seeds; the
multistart is neutral on the frozen world set (it is insurance against the
plane-assignment local optimum observed during construction under an earlier converge
schedule) and the refusal gates carry most of the score. These are local debugging
numbers, not frozen benchmark evidence.

### 2026-09-07 paid re-analysis probe at difficulty levels 2–3

The free path (identical solver with the re-analysis spend disabled) was compared with the
full reference at coarse mechanism noise 4.0°/6.0°/8.5° (levels 1/2/3, the same public
ladder):

| level | full reference dev/rob | free path dev/rob |
|---:|---:|---:|
| 1 | 0.6983 / 0.7307 | 0.7195 / 0.6874 |
| 2 | 0.5293 / 0.6130 | 0.6304 / 0.6270 |
| 3 (historical run) | 0.6226 / 0.5730 | 0.4811 / 0.1395 |

The paid re-analysis is not uniformly necessary: at levels 1–2 the free path matches or beats
it, so "paid precision matters" would have been an overstatement at the former level-1 default. It becomes
decisive only at level 3 (8.5° coarse noise), where the free path loses 0.14 development and
0.43 robustness. Recorded honestly; no oracle or reference change was made.

## 4. Shortcut probes

### September 9 four-dimensional stress-grid review

The maintainer's PR20 review reports a 12x8x12x6 = 6912-point search at
**0.346496/0.081461 development/held-out**, and a 24x12x24x9 = 62208-point
search plus three refinement rounds at **0.246501/0.161891**. These numbers are
maintainer-reported, not claimed as our independent replay of unavailable source.
The search varies the principal-axis trend/plunge, orthogonal-axis rotation and R,
selects the lower angular residual of the two nodal planes per event, re-analyzes
the 16 worst events, and applies mean/tail residual refusal.

The independently reconstructed `.research/pr20_focal_grid_probe.py` uses the same
family and grid sizes, with all coordinates explicitly fixed in source. Under the
CI-pinned NumPy 1.24.4/SciPy 1.10.1 combination it scores **0.402325/0.000000**
(coarse) and **0.347491/0.159656** (dense plus refinement), versus the unchanged
reference's **0.622620/0.573022**. Grid endpoints and implementation choices differ
from the unavailable maintainer source, so the scores must not be equated.
Reproduce all three methods and the final reference residuals with
`.research/pr20_focal_review_diagnostics.py --output /tmp/focal-review.json`.

The review also reports clearly separated average angular residuals: supported
catalogs 7.35–14.34 degrees, mixed/incoherent catalogs 17.47–22.77 degrees for its
probe. Thus refusal is comparatively easy for that tested method/world inventory;
it is not evidence of a difficult open-set classification problem. Once refusal
is correct, the normalized score is driven by supported-world axis, ratio and
plane recovery through their geometric mean. Selecting whichever nodal plane fits
best can also lower residuals for a wrong stress tensor; low angular misfit alone
does not establish correct scientific recovery.

Our unchanged-reference instrumentation separately measures supported means
7.982–17.446 degrees, mixed means 25.052–31.905 degrees and incoherent means
28.482–30.427 degrees. These are reference residuals, not the reviewer's grid-probe
residuals; both sets indicate separation on this finite world inventory. Exact
per-world values and source hashes are in `review_diagnostics_2026-09-09.json`.

Current level-3 values are in section 3. The following two numbers are historical level-1 measurements, not the shipped level-3 default.

- Constant-regime family (twelve fixed azimuths, R = 0.5, plane-a everywhere):
  **0.000** best.
- Removing the refusal gates (always report): **0.098** with false-discovery rate 1.0.

The 2026-09-10 maintainer review supersedes the earlier shortcut-separation claim.
A 6912-point grid with an independent 22–28 degree refusal threshold scores
0.586586/0.496309; an 864-point grid scores 0.455447/0.542578, versus the
reference 0.622620/0.573022. These are maintainer-reported measurements, not a
new author reproduction. The local probe inherits a stricter reference gate and
its scores do not represent this family's upper bound. Passing the existing
grid-probe tests is therefore not admission evidence. This draft remains blocked
until the reference or scientific regimes establish sufficient separation.
Source: https://github.com/Geniusyingmanji/ScientistsLastExam/pull/20#issuecomment-5614869028

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before
exposure, must show that the first proposal does not reach the competent reference.
Server-held catalogs and independent seismology review remain required.

## 6. Construction errors and revisions

Three construction errors were caught locally on 2026-09-05 before any model saw the
task. (i) The plane-row generator referenced an undefined loop variable and invalidated
every reference run. (ii) A single-start fit converged to a plane-assignment local
optimum on a held-out world (mean misfit 26.6 degrees) and falsely abstained a
supported catalog; the converge schedule and starts were rebuilt. (iii) Refusal gates
set against pre-reanalysis misfits misfired in both directions — a mixed world passed
(mean 21.3 against a 22-degree gate) and a supported world failed; gates were
recalibrated against the converged distribution (18 degrees / 0.18 tail). All three
are pinned in `tests/test_focal_mechanism_stress_inversion.py`.

## 7. Robustness and reproducibility

Development and held-out metrics stay separate; the held-out set uses fresh tensors,
mixtures, incoherent catalogs and noise. Determinism was checked by comparing two full
evaluation dictionaries. Real Linux sandbox replay is now recorded below; global
evidence refresh and independent replication remain pending. See the task card citations for background; the
explicitly declared synthetic catalog is not certified by those publications.

At clean revision `05d15d2`, two full Linux sandbox runs produced identical metrics:
0.622620424 development / 0.573022358 held out, in 3.22 / 3.32 seconds. The full
contribution gate passed 15/15 checks. The combined task/framework suite passed
204 tests and 40 subtests without skips, and the clean audit covered 85 tasks.
Python 3.12.3, NumPy 1.26.4 and SciPy 1.13.1 were already installed. Existing
administrator permission was used for namespace setup while the original
bubblewrap/seccomp candidate restrictions and host settings remained unchanged.
`linux_validation_2026-09-09.json` records both outputs, source hashes and commands.
These results are contributor validation, separate from GitHub CI and domain acceptance.

## Reproduce

```bash
python scripts/measure_reference.py \
  --task EarthScience/FocalMechanismStressInversion \
  --reference verification/reference_solver.py \
  --entry infer_stress_orientation
```

`--task` takes the on-disk path under `benchmarks/`, not the logical id
`Geophysics/FocalMechanismStressInversion` (the fine-grained domain stays in `metadata.yaml`);
the pre-2026-09-07 command passed the logical id and resolved to no directory.

### 2026-09-08 evaluator-contract re-review

The external `frontier_eval/run_eval.py` entrypoint now delegates to the trusted
`sle eval` sandbox path instead of importing candidate code in the oracle process.
Malformed submissions no longer count as discovery attempts. Confidence calibration
uses actual supported-world mechanism recovery as its target, and zero for refusals
or unsupported worlds; the combined-score normalization is unchanged. These changes
have targeted local regressions; they do not imply independent domain certification
or replace clean Linux sandbox replay.
Principal axes must be orthogonal; abstention requires empty or null axes and plane
assignments with null R. Re-analysis rejects boolean/floating-point IDs. Both split
confidence metrics and the discovery-attempt count are now published separately.

### 2026-09-08 default moves to the measured paid-information regime

Level 3 is now the shipped default (8.5-degree coarse, 2.6-degree re-analysis noise).
The scientific generator and three-level ladder are unchanged. A fresh local probe of
the complete reference gives `0.622620` development / `0.573022` held out. Calling the
same reference with a zero re-analysis budget gives `0.469429` / `0.139507`; this drops
development recovery by `0.153192` and held-out recovery by `0.433516`. The baseline
remains valid with exactly zero development and held-out scores at all three levels.
Unlike the former default, the active regime makes paid precision useful. The historical
probe table above is preserved; the current no-budget method differs from that earlier
ablation and is not silently substituted into its record. These remain local diagnostics,
not a frozen frontier-model calibration draw.
