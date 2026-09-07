# Known best — IMUBiasCalibration

## Scoring

`combined_score` is clipped to `[0, 1]`, with zero at the valid zero-calibration abstention
baseline. The reference is an evaluation anchor for the reduced-order simulator, not a field
calibration ceiling.

## Scientific target

The reference fits the public gravity-subtracted accelerations to an affine function of temperature,
predicts a sealed-temperature vector, and refuses worlds whose residual structure indicates a
nonlinear thermal response, cross-axis misalignment or motion contamination.

## Baseline

The shipped baseline returns zero bias and drift, an invalid prediction, and `undetermined` refusal.
It is valid and scores `0.000000` by construction.

## Reference

The truth-blind reference is recomputed from the candidate-visible records for each world. Its
development and held-out scores are recorded after the final implementation and deterministic
replay.

## Model calibration

DeepSeek Flash and Pro calibration runs, when authorized, are recorded in the compact experiment
JSON under `experiments/` with model IDs, seed, valid proposal count and best split scores only.

## Limitations

This is a procedural stationary-accelerometer laboratory. It excludes gyro coupling, coning,
scale-factor nonlinearity, vibration rectification, thermal hysteresis and real hardware effects.

## Provenance

Woodman (2007), *An introduction to inertial navigation*; Skog et al. (2016), aided inertial
navigation systems, DOI `10.1109/5.554205`; and temperature-calibration work for MEMS inertial
sensors, DOI `10.1109/TIM.2014.2325662`.
