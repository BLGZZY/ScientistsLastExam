# NeuralReportAttribution: witness and construction record

## 1. Reference and sources

`verification/reference_fit.py` independently constructs the public four-population
frequency response and jointly fits neural and instrument nuisance parameters to
response and calibration likelihoods. It compares null, report-only and intrinsic
feedback models, and rejects excessive residuals. It imports no evaluator or truth.
Score 1 is the explicit correct-parameter ceiling, not an empirical reference literal.

[Friston et al., 2003, DOI 10.1016/S1053-8119(03)00202-7](https://doi.org/10.1016/S1053-8119(03)00202-7)
motivates input-state-output identification and effective connectivity. This task is
a linearized local system, **not** an implementation of full DCM, its hemodynamic
forward model, or a validated theory of consciousness. [Cogitate 2025](https://www.nature.com/articles/s41586-025-08888-1)
motivates separating theoretical subclaims and report confounds; no Cogitate data
or theory-specific prediction is used as a simulated ground-truth label.

An independent time-domain check numerically integrates exp(A t)exp(−iωt) and checks
the implemented transfer response including observation mixing and feedthrough.
This tests the numerical equation, not its adequacy as a model of a human brain.

## 2. Baseline

The shipped candidate reads one report-on response and announces the maximum allowed
feedback coefficients. It is legal and scores zero. It exemplifies overinterpreting
measured propagation as strong intrinsic coupling. A blanket null or refusal also
scores exactly zero under the stated 0.2-offset normalization. Null means no
interpopulation coupling in this local model; it never means no subjective experience.

## 3. Ablation ladder

`scripts/audit_neural_report.py` runs secure witness/baseline repeats and:

- `one_unit`: reduce each repeated calibration/response bundle to one unit, lowering
  total acquisition from 14 to 10 units.
- `ignore_instruments`: assume identity actuator/sensor mixing and zero observer lag
  and direct feedthrough despite the supplied calibration measurements.

The report retains every signed delta, including any ablation improvement. Joint
likelihood fitting includes finite calibration uncertainty; it is not a plug-in
calibration witness that gains false apparent headroom by omitting standard practice.

Linux secure measurements (full precision and provenance in
`experiments/neural_report_2026-09-10.json` at repository root):

| Strategy | Development | Heldout | Development loss vs reference |
|---|---:|---:|---:|
| baseline | 0.000000 | 0.000000 | +0.877046 |
| reference | 0.877046 | 0.740333 | +0.000000 |
| one_unit | 0.840246 | 0.703612 | +0.036800 |
| ignore_instruments | 0.000000 | 0.000000 | +0.877046 |

The reference has zero observed false positive model claims, full supported-world
coverage and correct refusal on both outside-family worlds in each split. Each split
has only ten worlds: these rates are finite-sample diagnostics, not population guarantees.

The one-unit loss is only 0.036800 on development and 0.036721 on heldout.
The reference is already strong; neither its remaining gap nor a zero-score raw
inverse shortcut establishes that a frontier model will struggle.

## 4. Shortcut probe

A grid of 972 strategies sees only one low-frequency report-on response, inverts
the raw measured response as if it were neural state transfer, thresholds apparent
intrinsic feedback and scales two inferred couplings. Development selects the grid
point, then heldout evaluates it once. This tests a concrete instrument-confounded
shortcut, not every inverse-system method and not an independent searcher cohort.


Recorded best development score: 0.000000; its single heldout
confirmation: 0.000000. Selection parameters and all probe
scope qualifications are retained in the machine-readable evidence.

## 5. Frontier draw

No independent language-model draw, saturation study or evolution-gap run has been
performed: no configured general model endpoint/credentials were available to this
task. Status is `candidate`; the intended `hard` tier remains uncalibrated. Passing
unit/security tests or recovering synthetic parameters is not proof of frontier difficulty.

## 6. Construction errors and corrections

- The first reference treated noisy instruments as exact; joint response/calibration
  likelihood fitting replaced it. Its stronger result is retained rather than hiding
  the initial under-built witness.
- Parameter error originally contributed to false discovery. It now contributes only
  to continuous coupling recovery; false-discovery rate counts wrong positive models.
- Calibration can change between report conditions; a raw no-report/report difference
  cannot be interpreted as intrinsic feedback without accounting for both instruments.
- Outside-family slow-state mediation is distinct from a legal zero-feedback circuit.
  The latter must be considered a positive report-only model or a valid all-zero null,
  not automatically labelled “unknown”.

## 7. Robustness, contamination and headroom

Construction tests check stability for both frozen seed sets and twenty extra seeds
under every model class and report condition; no latent labels are passed to the
candidate. Repetition adds independent noise and costs units. API validation is
strict and permanently latches violations, including caught overspend. Search
visibility excludes heldout, per-world labels, false-discovery and refusal axes.

The idealized calibration operation presumes a controllable simulator. It is not
available as an exact human neural-state clamp and does not calibrate experience.
The omitted-state generator is one model-misspecification case; other unmodelled
effects may remain undetected. Source-visible seeds need a server-held replacement.
Adaptive experimental allocation, treatment of nonlinear likelihood uncertainty and
broader misspecification checks remain possible improvements. Independent neuroscience
review and actual model calibration are still required for scientific admission.

The evaluator resets the candidate process and private temporary filesystem before
every subsequent world, including the development/heldout boundary. An actual
Bubblewrap regression candidate tests both module globals and a `/tmp` marker.
