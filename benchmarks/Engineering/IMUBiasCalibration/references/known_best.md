# Known best - active IMUBiasCalibration, schema 2

## Reference

The truth-blind witness selects eighteen settings by approximate D-optimal design over the
joint supported/fault regression span. It fits the upper-triangular twelve-parameter model
by known-noise weighted least squares, residualizes each declared one-parameter fault
alternative against that null, and compares the resulting chi-square statistics with
Bonferroni familywise error control at 0.05. It reports the winning fault's response axis,
or the supported calibration and predictions at three transferred poses/temperatures.

Design and regression use only public settings and acquired measurements. No hidden seed,
family or coefficients enter the reference. The Gaussian one-parameter survival probability
is evaluated exactly as erfc(sqrt(statistic/2)), using the standard math library. Remaining
headroom comes from finite information, noisy coefficient recovery and near-threshold model
separation, not an intentionally missing calibration step. It is not a published sensor SoTA.

## Baseline

The baseline makes a confident supported claim for the factory identity matrix with zero
bias/drift, without measuring. The evaluator normalizes so never-refusing calibration and
all blanket-refusal variants are zero. The anchor is not a tuned reference score.

Supported quality weighs bias 0.25, drift 0.25, matrix 0.30 and transferred prediction 0.20.
Their public tolerances are 0.035 m/s^2, 0.0014 m/s^2/C, 0.006 Frobenius error and
0.07 m/s^2 RMS vector prediction error. These represent calibration-error scales, not
hardware specifications. Correct fault refusal requires both type and response axis.
The headline is clip((sum(quality)-U)/S,0,1)*(correct_refusals/U). Mechanism is separately
matrix recovery quality over all supported worlds; false discovery, refusal and coverage
retain their own counts/denominators. Confidence has no headline weight.

## Ablation ladder

`verification/calibrate.py` tests six and twelve measurements, central temperatures only,
sequential rather than information-designed settings, diagonal-only calibration, and removal
of each fault diagnostic. It also tests fixing every predicted fault axis, blanket refusal
and never-refusing claims. Every selected policy is independently replayed twice through the
Linux trusted driver and bubblewrap; the complete metrics must match.

## Shortcut probes

Two 900-policy grids fit the supported triangular calibration but use only whitened residual
RMS and peak thresholds to label faults and choose the largest-residual response axis. One
uses the reference's public-input design and one takes settings sequentially. Thresholds
and fault labels are selected using development only. Public transcripts of this fixed
trusted probe are cached for grid scoring; the selected policies are independently sandboxed.
The registered grid is not an exhaustive upper bound over all possible algorithms.

## Model calibration

The record `experiments/imu_bias_calibration_deepseek_calibration_2026-09-07.json` is strictly
historical passive-schema evidence. Its Windows in-process values cannot calibrate schema 2.
Intermediate Linux passive-schema revisions are also historical: after fixing metric
accounting and missing held-out motion coverage, Flash's first proposal scored 0.986466 on
development, exceeding the reference's 0.985196; Pro scored 0.973504. An earlier Pro draw
was invalid because its generated abstention path called .tolist() on a Python list.
Those observations triggered the scientific redesign rather than a reference-score adjustment.
Fresh active-schema model results must identify their exact clean source revision and
effective thinking configuration. DeepSeek evidence alone is not independent frontier admission.

## Construction errors

1. The original passive laboratory made all data free and faults conspicuous. An early Flash
   draw exceeded the first reference; changing a few thresholds did not remove on-ramp difficulty.
2. Maintainer review found absent top-level discovery axes, missing denominators, recovery credit
   on supported abstentions, free prediction credit on wrong refusals, and two invalid citations.
3. Fixing those defects exposed missing held-out motion coverage; adding that family corrected
   the split but did not solve simplicity. A fresh first proposal still reached the reference.
4. The active redesign removes the free table, expands six coefficients to twelve, moves faults
   toward single-measurement noise, and requires axis localization. Budget enforcement is sticky:
   catching the callback's exception cannot restore validity. Query evidence cannot be fabricated.

No model program, provider configuration, prompt, key or raw request is committed. Historical
failures are retained; they are not evidence for the current score or reference difficulty.

## Robustness and limitations

Both development and held-out splits contain twelve supported worlds and nine faults, three
per named family, with independent seeds, settings, noise and coefficients. Public settings
and uncertainties have identical distributions across families. Noise on repeated requests
is deterministic by world, setting and call number but independent across repeats. Every
world starts a new candidate session. This remains a finite, public procedural family, not
real-device replication; unknown mounting rotation, hysteresis, mixed faults and full
six-degree-of-freedom motion are outside scope. A server-held family and external domain
review are still required for certification. No full-repository test suite or maintainer-owned
global evidence refresh is run for this contribution.

## Verified sources

- Woodman (2007), *An introduction to inertial navigation*, UCAM-CL-TR-696,
  DOI 10.48456/tr-696. Publisher record: https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.html.
  This supports sensor bias, scale and alignment-error modeling; the exact fault polynomials,
  triangular coordinate convention and temperature coefficients here are synthetic assumptions.
- Kiefer and Wolfowitz (1960), *The Equivalence of Two Extremum Problems*,
  DOI 10.4153/CJM-1960-030-4. Foundation for information-based experimental design;
  the greedy finite-catalog implementation is an approximation, not globally optimal design.
- Wilks (1938), *The Large-Sample Distribution of the Likelihood Ratio for Testing Composite
  Hypotheses*, DOI 10.1214/aoms/1177732360. General model-comparison background; with the
  known Gaussian noise and one linear added coefficient here the null chi-square law is exact.

Titles/identifiers verified against publisher/Crossref records on 2026-09-08. The removed
10.1109/5.554205 is Hall and Llinas's unrelated multisensor-fusion introduction; the removed
10.1109/TIM.2014.2325662 did not resolve. Neither is retained as supporting evidence.
