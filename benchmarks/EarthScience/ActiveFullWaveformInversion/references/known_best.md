# Reference and admission record — ActiveFullWaveformInversion

## 1. Reference method and scope

The reference fits a smooth velocity correction using only public physics and paid
shots at 9/15/21. This central aperture was selected on development diagnostics;
heldout and confirmation scores did not select it. Explicit source subsets in the
budget audit are used unchanged. Coarse-to-fine fitting, minimum-change/spatial regularization and late trace
balancing remain in place. Exact discrete derivatives are the default; a numerical finite-difference comparison
is available in the audit. They are an implementation choice:
finite differences should converge to the same solution. They are not an additional
scientific capability and their use alone does not establish difficulty.
The old global-energy refusal gate was removed: supported velocity changes can also
change signal energy. Near-null detection and post-fit model adequacy remain separate.

## 2. World and scoring revision

The September 10 review found a continuous Gaussian probe above the old reference.
The new truth family is a smooth random Fourier field, independent of both the
Gaussian probe's shape family and the reference interpolation grid. It covers the
whole depth range. Acquired and sealed records extend from 210 to 300 samples to
observe later arrivals. Both splits contain ten supported worlds with disjoint
seeds, followed by three independent unsupported controls.

The unsupported reasons are unresolved near-null structure, incorrect source timing,
and attenuation over heterogeneous structure. Every regime varies with seed. Near-null
means spatial variation below the **joint** noise scale, not merely below each
sample’s noise. A regression bounds the noise-normalized squared waveform
separation for any three-shot sequence, including repeats, below 0.001 on the
shipped and predeclared confirmation nulls. The null remains a common negative
control; its independent noise draws are not new geological-transfer evidence.
Only the source-timing and attenuation controls test new non-null misspecification. Source delay is
an interpolated delayed source response, whereas attenuation acts inside the wave
recurrence. These are distinct physical departures; whether a candidate separates
their causes is not established merely by counting its correct refusals.

The structural and sealed-waveform formulas are unchanged. In particular deep cells
already participated in the metric: the repair puts genuine signal there instead of
claiming a new weighting fixed an old omission. The baseline and all-refusal scores
must remain exactly zero. The expanded instance distribution changes historical
score comparability; no old score is relabelled as a result on the new oracle.

## 3. Reference and acquisition measurements

Current clean Linux measurements will be recorded after the source freeze. The
source sweep in `scripts/audit_fwi_revision.py --budget-sweep` includes all five
single shots and all ten pairs, using the same inversion implementation. Source 3
alone is not a justified estimate of the best one-shot method. The first exhaustive
scan found pair 9/21 at 0.620585 development, above the old fixed triple
3/15/28 at 0.546014. The revised central triple measures 0.664800 in local
development diagnostics; clean Linux and confirmation numbers follow below. Budget is a charged
constraint; a large marginal value for the third shot must not be assumed. A 50-threshold sweep with a fresh, uncached replay of the
development-selected threshold also checks that low probe scores are not merely
caused by excessive refusal.

## 4. Continuous shortcut families

`.research/pr20_fwi_continuous_probe.py` is an independent implementation with its
own checked propagator and numerical finite differences. It fits one or three blobs,
then five with a noise discrepancy stop, then five with the additional depth cap.
Every stage starts from a 240-point spatial/amplitude grid. No evaluator/reference
imports, seed lookup or reference-spline coefficients enter the probe.

The old maintainer measurements were **0.820084/0.561552**, against the old
reference **0.714101/0.660180**. The previously published 58.7%/55.0% ratios were
only measurements of an incomplete family, not bounds. Existing 0.15 margin and
70% ratio guards are retained and extended to continuous fitting on both splits.
Exact maintainer source remains unavailable; the new probe is a reconstruction of
its described methods, not a claim of exact-source replay.

## 5. Sampling uncertainty and confirmation

The audit reports stratified world-bootstrap intervals (20,000 draws) and supported
world standard errors. The sample remains small and procedural; intervals are not
claims about independent geology. `--fresh` uses predeclared separate seeds, without
choosing them based on scores. Model calibration and external domain review remain
pending. These diagnostics do not certify the task.

## 6. Construction errors and history

A self-check found that the first near-null amplitude was below pointwise noise
but detectable by aggregating traces (best-three squared separation about 3435
and 3270). It was reduced before sandbox confirmation. The near-null is explicitly
a shared negative control, rather than using tiny seed differences to claim
independent geological worlds.

The first September 11 exploratory redesign used curved layers. It failed: the
reference development score was about 0.209, while a continuous depth-capped probe
scored about 0.358. It was rejected rather than reported as successful hardening.
Interpolation-grid texture experiments also produced unstable recovery. A batched
central-difference implementation was rejected because its full evaluation was
slower than the existing tangent implementation; it did not change the physics. The random
Fourier family was selected using development diagnostics, before confirmation;
this is builder development, not independent validation.

The September 10 review also showed that removing exact derivatives preserved score,
and that the best one/two-shot scores were 0.575212/0.691962 on the old oracle.
Those corrections supersede the earlier causal and acquisition claims. Full prior
history is retained in `known_best_pre_revision_2026-09-10.md`; all September 9 JSON
reports concern that archived oracle. Historical Linux command arrays mention Focal
because it was present before the PR split; no Focal task remains in this package.

## 7. Reproduction and evidence

```sh
OPENBLAS_NUM_THREADS=1 python scripts/audit_fwi_revision.py --output /tmp/fwi-review.json
OPENBLAS_NUM_THREADS=1 python scripts/audit_fwi_revision.py --methods reference finite_difference --budget-sweep --output /tmp/fwi-budget.json
OPENBLAS_NUM_THREADS=1 python scripts/audit_fwi_revision.py --fresh --output /tmp/fwi-fresh.json
python -m pytest tests/test_fwi_discrete_inversion.py tests/test_new_earth_science_tasks.py tests/test_pr9_earth_hardening.py tests/test_pr9_earth_contracts.py tests/test_earth_pr_review_regressions.py -q
```

The expanded 26-world evaluation exceeded the former 600-second cap in the Linux
method audit (700 seconds for the preceding fixed triple under concurrent load).
The wrapper and card now permit 1200 seconds; metadata gives a 900-second wall-time
estimate, not a second timeout. The higher compute cost is a limitation of this
revision, not evidence of greater scientific difficulty.

Publishable measurements require a clean Linux checkout and real sandbox replay.
Diagnostic reports retain source hashes, revision, dirty state, dependencies and
per-world failures. Global frozen evidence is maintained separately by maintainers.
Virieux & Operto (2009), DOI `10.1190/1.3238367`, supports the FWI methodology;
Symes (2020), arXiv `2003.14181`, is methodological background. Neither publication
claims performance on this synthetic world family.
