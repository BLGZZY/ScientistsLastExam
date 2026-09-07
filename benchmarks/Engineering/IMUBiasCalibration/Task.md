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

The clipped `combined_score` averages parameter recovery, sealed-temperature prediction and
confidence calibration. Development and held-out worlds contain supported affine calibration and
three distinct unsupported mechanisms. Correct refusal, false discovery, validity and held-out
transfer are reported separately. The reference is a truth-blind robust affine fit with residual
diagnostics; it is an evaluation anchor, not a claim of field calibration accuracy.

## Contract and rules

`sle.contract_lint` can check mapping, finite vectors, ranges and evidence IDs before spending an
evaluation call. Only edit `solution.py`; use deterministic CPU-only Python, NumPy and the standard
library. Do not read `verification/` or create network requests/processes.

## Inputs

Every candidate-visible key is listed here: `schema_version`, `gravity_mps2`,
`reference_temperature_c`, `prediction_temperature_c`, `prediction_orientation`,
`diagnosis_values`, `measurement_model`, `abstain_when`, and `records`; each record key is
`record_id`, `temperature_c`, `orientation`, and `accel_mps2`.

## Relationship to nearby tasks

`Sensors/QuartzCrystalMicrobalanceLab` infers thin-film deposition from complex QCM admittance and
resonance shifts. This task instead calibrates triaxial inertial measurements against known gravity
orientations and attributes sensor faults; it has no resonance, deposition or complex-I/Q contract.

## References

Woodman, *An introduction to inertial navigation*, University of Cambridge, 2007. The affine bias,
scale and thermal-drift calibration problem follows standard IMU error modeling; the oracle is a
small deterministic reduced-order laboratory rather than a field deployment prescription.
