# IMUBiasCalibration — recover bias and temperature drift from static IMU records

## Scientific setting

An inertial measurement unit reports specific force, so a stationary device should measure the
gravity vector plus sensor bias. Bias and temperature sensitivity are coupled calibration terms;
cross-axis misalignment, nonlinear thermal response, and motion contamination can make a linear
calibration misleading.

## Your task

Implement:

```python
def infer_imu(problem):
    """Return a calibrated bias, drift, prediction and diagnosis."""
```

`problem` contains `schema_version`, `gravity_mps2`, `reference_temperature_c`,
`prediction_temperature_c`, `prediction_orientation`, `diagnosis_values`, `measurement_model`,
`abstain_when`, and `records`. Each record has `record_id`, `temperature_c`, `orientation`, and
`accel_mps2`; orientations are known unit vectors and accelerations are three-element vectors.

Return exactly these keys:

- `bias_mps2`: three bias components at the reference temperature;
- `temperature_drift_mps2_per_c`: three linear drift components;
- `prediction_accel_mps2`: predicted acceleration at the supplied prediction temperature and
  orientation;
- `diagnosis`: one of `supported`, `thermal_nonlinearity`, `axis_misalignment`,
  `motion_contamination`, or `undetermined`;
- `confidence`: a finite number in `[0, 1]`;
- `abstain`: a boolean; unsupported or contaminated records should be refused;
- `evidence_ids`: unique IDs drawn from the supplied records.

For a supported world, fit the declared affine model and publish the bias, drift and prediction.
For nonlinear thermal response, cross-axis misalignment, or motion contamination, identify the
failure and set `abstain=True`. Do not assume record order, hidden seeds, or a fixed fault.

## Evaluation

On supported worlds, abstention or a diagnosis other than `supported` receives zero. A correct
claim receives `q = 0.70*s + 0.20*p + 0.10*c`. With Euclidean bias, drift and prediction errors
`eb`, `ed`, `ep`, `s = clip(1 - 0.55*eb/0.35 - 0.30*ed/0.006 - 0.15*ep/0.5, 0, 1)`,
`p = clip(1 - ep/0.5, 0, 1)` and `c = 1 - abs(confidence-s)`.
An unsupported world contributes one only for abstention with the correct fault diagnosis;
wrong-label abstention receives no prediction or confidence credit.

For each split, let `S` and `U` be the supported and unsupported counts, and `R` the number of
correctly attributed refusals. The headline is
`clip((sum(q)-U)/S, 0, 1) * R/U`. The subtraction removes the maximum reward available from
blanket refusal; the additional refusal multiplier also makes never-refusing calibration zero.
Both splits contain supported and unsupported worlds. Invalid submissions receive zero.

Separate development/held-out diagnostics publish numerators and denominators:
`mechanism_score` is correct non-abstained supported diagnoses / all supported worlds, not
parameter recovery; `false_discovery_rate` is false claims / actual non-abstained claims (zero
if none); `correct_refusal_rate` is correct fault-labelled refusals / all unsupported worlds;
`discovery_coverage` is supported claims, including wrong ones / all supported worlds.
`attempted_discovery` indicates any valid non-abstained claim. Invalid and abstained supported
worlds remain in the mechanism and coverage denominators. Composite `science_score`, confidence
calibration and normalized held-out `robustness_score` are separate diagnostics and are not
search-visible feedback.

## Contract and rules

`sle.contract_lint` can check mapping, finite vectors, ranges and evidence IDs before spending an
evaluation call. Only edit `solution.py`; use deterministic CPU-only Python, NumPy and the standard
library. Do not read `verification/` or create network requests/processes.

## Inputs

Every candidate-visible key is listed here: `schema_version`, `gravity_mps2`,
`reference_temperature_c`, `prediction_temperature_c`, `prediction_orientation`,
`diagnosis_values`, `measurement_model`, `abstain_when`, and `records`; each record key is
`record_id`, `temperature_c`, `orientation`, and `accel_mps2`.

## References

Woodman, *An introduction to inertial navigation*, University of Cambridge, 2007. The affine bias,
scale and thermal-drift calibration problem follows standard IMU error modeling; the oracle is a
small deterministic reduced-order laboratory rather than a field deployment prescription.
Report UCAM-CL-TR-696, DOI `10.48456/tr-696`. The thermal polynomial and sparse motion faults
are synthetic error-model approximations, not fitted device measurements.

## Relations and differences

- `StructuralEngineering/ModalDamageAttribution` also separates thermal confounding from
  out-of-family failure, but localizes stiffness loss from budgeted modal measurements; this task
  estimates sensor bias and thermal drift from supplied static vector records.
- `HeatTransfer/ConvectionDiffusionOpt` identifies transport and designs heaters through charged
  PDE experiments; this task diagnoses a measurement model without controlling a thermal field.
- `Sensors/QuartzCrystalMicrobalanceLab` reconstructs resonance admittance and deposition,
  rather than gravitational accelerometer calibration.
