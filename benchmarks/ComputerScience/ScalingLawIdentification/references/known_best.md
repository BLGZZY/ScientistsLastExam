# Reference and admission record

## 1. Runnable public-input method

The standalone reference fits each public timing family with a bounded finite-size
correction, tests known-noise goodness of fit, then checks class-likelihood separation.
Its design uses public bounds and costs only; there is no hidden modulus or seed.
The scale and the nuisance coefficient are fitted jointly. Remaining headroom is
adaptive experimental design and marginalization over scale/correction uncertainty.

### 1a. Maintainer construction and identifiability certificate

Wide worlds use log-noise sigma 0.16, bounds [8,384], and a uniform coefficient in
[-2,2]. Narrow ambiguity worlds use [64,72] and sigma 0.12; narrow supported controls
use exponential timing with the identical sigma 0.12 and correction in [-2,-1].
Their public problem mappings are identical, so neither domain nor noise metadata
is a refusal label. The class-separating slope must be measured. Scale uncertainty
on the narrow interval remains real headroom. The observed noise precision is public.
Misspecified worlds add `1.4*sin(3*log(m))` to log runtime; its exact form is hidden.

For each ambiguous world, pair linear and linearithmic families, match their scale
at the midpoint of the log-ratio range, and keep nuisance/noise identical. At any
size, conditional KL is squared log-mean difference divided by twice noise variance.
The chain rule bounds every adaptive transcript by `budget*max(KL_per_query/cost)`.
Pinsker yields equal-prior binary accuracy at most 0.623423, even for a method told
both candidate parameter settings. This does not assert zero recoverable information;
it rules out reliable class identification. The counterpart is in the public family.
A full-domain enumerator in `ambiguity_information_bound` independently computes
the bound. Narrow supported controls prevent bounds alone from serving as labels.

The class forms follow CLRS (ISBN 9780262033848); finite empirical measurement and
finite-size concerns are motivated by McGeoch (ISBN 9781107001732),
https://assets.cambridge.org/97811070/01732/excerpt/9781107001732_excerpt.pdf.
The particular noise/correction constants are original synthetic choices.

## 2. Baseline and normalization

The shipped legal baseline is confidently uninformative and scores zero. Full
abstention also scores zero, with distinct discovery coverage. See Task.md for the
complete numerical score. Invalid artifacts never become discovery attempts.
The budget is a hard constraint; the old 25% full-budget discount has been removed.
Probability-weighted extrapolation replaces winner-take-all class selection.

## 3. Capability ablations

`verification/replay_review.py` removes one capability at a time using legal public
inputs and charged callbacks. Current Linux measurements are in the table below;
all variants retain the original artifacts and remaining computations.

## 4. Low-dimensional shortcuts

The maintainer's old-head grid reached 0.863028 development / 0.858821 held out;
the untuned doubling ladder reached 0.792895 / 0.799391, above the old reference
0.710786 / 0.702993. The earlier “No low-dimensional family reaches the reference”
claim is withdrawn. The revised 2304-setting sweep varies ladders, RMS gates,
probability mass and inclusion of a bounded nuisance fit. Selection uses development
score; held-out performance of that same strategy is reported, not retuned.

## 5. Frontier-model calibration

No current-revision frontier-model draw has been completed. The package remains
candidate; neither these numerical probes nor unit tests establish the required
first-proposal admission criterion. Builder lineage remains complete with honestly
empty calibration lists, as clarified by the maintainer's withdrawn review item.
Historical local/macOS proposals are not frozen calibration evidence.

## 6. Construction errors and review revisions

The original jitter label demanded refusal despite recoverable classes. The original
reference explicitly used a hidden mod-three predicate; an efficiency discount then
hid intrinsic saturation. Those constructions have been replaced. An intermediate
small ensemble still let a nuisance-aware three-point probe win by chance; replicated
class/scale/nuisance worlds and a separate held-out ensemble now expose that failure.
Noise sweeps (0.08, 0.12, 0.16, 0.20) guided the chosen 0.16 instrument regime; this
is disclosed task design, not a blind calibration draw. Refusal labels derive from
model inadequacy or the pairwise information bound, never a high-noise label alone.
Integer-valued float sizes now match integer timings; one invalid world no longer
erases other valid results. The taxonomy follows the planned finite-n evidence
variant. Removed cross-PR findings are retained in their originating PR history.

## 7. Robustness and reproduction

Run from a clean Linux checkout with the repository's pinned NumPy/SciPy environment:

```bash
python benchmarks/ComputerScience/ScalingLawIdentification/verification/replay_review.py --output /tmp/review-replay.json
python benchmarks/ComputerScience/ScalingLawIdentification/frontier_eval/run_eval.py --candidate benchmarks/ComputerScience/ScalingLawIdentification/verification/reference_solver.py --metrics-out /tmp/reference.json
```

The replay records revision, clean-tree status, source hashes, Python/NumPy and OS.
It is a contributor numerical audit, not maintainer-owned frozen global evidence.
Linux sandbox replay and contribution checks are reported separately below.

## Current revision measurements

Pending clean Linux replay of the revised sources; no old scores are relabeled as current.
