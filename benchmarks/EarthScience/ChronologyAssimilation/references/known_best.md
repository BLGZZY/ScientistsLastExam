# Reference and admission record

## 1. Runnable public-input method

The standalone reference uses charged dates to initialize monotone age-depth curves,
then jointly fits the public positive-accumulation family and an 81-point common
climate with sparse nonlinear least squares. Gaussian-process reconstruction uses
the refined ages and an approximate diagonal dating-error variance. Laboratory
calibration and cross-record coherence are separate adequacy tests. No seeds,
true ages, climate spectrum or evaluator imports are used.

Joint posterior uncertainty, correlated chronology errors and adaptive dating remain
headroom. The diagonal propagation approximation is included as an ablation; a tiny
score delta must not be described as evidence of a separate demanding capability.

The pseudoproxy context is Amrhein et al., DOI 10.1029/2020GL090485, and Badgeley
et al., DOI 10.5194/cp-16-1325-2020. The public positive-accumulation synthetic model
is inspired by age-uncertain reconstruction, not a reproduction of a published
climate reconstruction. All field and dating constants are in the local evaluator.

## 2. Baseline and normalization

The shipped legal baseline is confidently uninformative and scores zero. Full
abstention also scores zero, with distinct discovery coverage. See Task.md for the
complete numerical score. Invalid artifacts never become discovery attempts.
Chronology skill is exp(-age_MAE/65 - age_increment_MAE/12). Adjacent-sample
increments penalize an interpolant whose dated endpoints are right but accumulation
between them is wrong. Exact fields and ages achieve unit supported mechanism skill.

## 3. Capability ablations

`verification/replay_review.py` removes one capability at a time using legal public
inputs and charged callbacks. Current Linux measurements are in the table below;
all variants retain the original artifacts and remaining computations.

## 4. Low-dimensional shortcuts

The maintainer's old-head cheap strategy reached 0.698764 / 0.682105 versus
reference 0.736298 / 0.708775 (94.9% / 96.2%). Previous affine/offset probes retained
the reference climate and missed this direction. The new 1008-setting sweep varies
sample count, endpoint convention, constant standard deviation, calibration gate
and coherence gate. It buys dates, linearly interpolates, and averages unweighted
records. The best development strategy's held-out score is reported without retuning.

## 5. Frontier-model calibration

No current-revision frontier-model draw has been completed. The package remains
candidate; neither these numerical probes nor unit tests establish the required
first-proposal admission criterion. Builder lineage remains complete with honestly
empty calibration lists, as clarified by the maintainer's withdrawn review item.
Historical local/macOS proposals are not frozen calibration evidence.

## 6. Construction errors and review revisions

The previous score rewarded sparse interpolation almost as much as the reference,
while the reference never used proxy observations to refine chronology. Local
increment scoring and joint inference repair those two issues together. The old
known_best text listed unrelated mass/time/instrument tests that did not exist; that
template text and the external-fork “current comparison” link have been removed.
Nearest-neighbor documentation now includes UPbConcordiaInference, GravityInversion
and RadiativeTransferFit. SystemExit/KeyboardInterrupt fail closed during direct
oracle diagnostics. The wrapper retains its trusted subprocess and explicit timeout.

## 7. Robustness and reproduction

Run from a clean Linux checkout with the repository's pinned NumPy/SciPy environment:

```bash
python benchmarks/EarthScience/ChronologyAssimilation/verification/replay_review.py --output /tmp/review-replay.json
python benchmarks/EarthScience/ChronologyAssimilation/frontier_eval/run_eval.py --candidate benchmarks/EarthScience/ChronologyAssimilation/verification/reference_solver.py --metrics-out /tmp/reference.json
```

The replay records revision, clean-tree status, source hashes, Python/NumPy and OS.
It is a contributor numerical audit, not maintainer-owned frozen global evidence.
Linux sandbox replay and contribution checks are reported separately below.

## Current revision measurements

Pending clean Linux replay of the revised sources; no old scores are relabeled as current.
