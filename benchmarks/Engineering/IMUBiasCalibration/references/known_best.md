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

The truth-blind reference is recomputed from the candidate-visible records for each world. On the
frozen evaluator it scores `0.988562` on development and `0.987844` on held-out worlds, correctly
refuses every unsupported world, and has zero false discoveries. Complete replay is deterministic.

## Model calibration

One fresh, thinking-disabled first proposal from each model was evaluated after the oracle freeze.
`deepseek-v4-flash` scored `0.461999` development and `0.647238` held-out;
`deepseek-v4-pro` scored `0.599130` and `0.733479`. Both submissions were valid and materially
above the baseline, but each correctly attributed only one third of development faults and one half
of held-out faults. The compact record is
`experiments/imu_bias_calibration_deepseek_calibration_2026-09-07.json`.

## Limitations

This is a procedural stationary-accelerometer laboratory. It excludes gyro coupling, coning,
scale-factor nonlinearity, vibration rectification, thermal hysteresis and real hardware effects.

## Provenance

Woodman (2007), *An introduction to inertial navigation*; Skog et al. (2016), aided inertial
navigation systems, DOI `10.1109/5.554205`; and temperature-calibration work for MEMS inertial
sensors, DOI `10.1109/TIM.2014.2325662`.
