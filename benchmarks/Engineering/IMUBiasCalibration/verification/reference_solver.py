"""Truth-blind reference policy for IMUBiasCalibration."""
from __future__ import annotations

import numpy as np

GRAVITY = 9.80665
T_REF = 25.0


def infer_imu(problem):
    return _infer_imu(problem)


def _infer_imu(problem, disabled_faults=()):
    rows = problem["records"]
    X = np.asarray([[1.0, r["temperature_c"] - T_REF] for r in rows], dtype=float)
    Y = np.asarray([np.asarray(r["accel_mps2"], dtype=float) - GRAVITY * np.asarray(r["orientation"], dtype=float) for r in rows])
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    bias, drift = coef[0], coef[1]
    residual = Y - X @ coef
    rms = float(np.sqrt(np.mean(residual ** 2)))
    norms = np.linalg.norm(residual, axis=1)
    robust_scale = max(float(np.median(norms)), 0.01)

    dt = X[:, 1]
    X_quad = np.column_stack([np.ones(len(rows)), dt, dt ** 2])
    quadratic_detected = False
    for axis in range(3):
        qcoef, *_ = np.linalg.lstsq(X_quad, Y[:, axis], rcond=None)
        qres = Y[:, axis] - X_quad @ qcoef
        linear_ss = float(np.sum(residual[:, axis] ** 2))
        quad_ss = float(np.sum(qres ** 2))
        improvement = (linear_ss - quad_ss) / max(linear_ss, 1e-12)
        if abs(float(qcoef[2])) > 8e-5 and improvement > 0.18:
            quadratic_detected = True

    orientation = np.asarray([row["orientation"] for row in rows], dtype=float)
    coupling_detected = False
    for axis in range(3):
        ccoef, *_ = np.linalg.lstsq(GRAVITY * orientation, residual[:, axis], rcond=None)
        off_axis = np.delete(ccoef, axis)
        if float(np.max(np.abs(off_axis))) > 0.0045:
            coupling_detected = True

    diagnosis = "supported"
    abstain = False
    if "motion_contamination" not in disabled_faults and float(np.max(norms)) > max(0.10, 4.5 * robust_scale):
        diagnosis, abstain = "motion_contamination", True
    elif "thermal_nonlinearity" not in disabled_faults and quadratic_detected:
        diagnosis, abstain = "thermal_nonlinearity", True
    elif "axis_misalignment" not in disabled_faults and coupling_detected:
        diagnosis, abstain = "axis_misalignment", True
    prediction = GRAVITY * np.asarray(problem["prediction_orientation"]) + bias + drift * (problem["prediction_temperature_c"] - T_REF)
    return {
        "bias_mps2": bias.tolist(),
        "temperature_drift_mps2_per_c": drift.tolist(),
        "prediction_accel_mps2": prediction.tolist(),
        "diagnosis": diagnosis,
        "confidence": 0.95 if abstain else float(np.clip(0.99 - rms / 0.50, 0.0, 1.0)),
        "abstain": abstain,
        "evidence_ids": [r["record_id"] for r in rows],
    }
