"""Truth-blind reference policy for IMUBiasCalibration."""
from __future__ import annotations

import numpy as np

GRAVITY = 9.80665
T_REF = 25.0


def infer_imu(problem):
    rows = problem["records"]
    X = np.asarray([[1.0, r["temperature_c"] - T_REF] for r in rows], dtype=float)
    Y = np.asarray([np.asarray(r["accel_mps2"], dtype=float) - GRAVITY * np.asarray(r["orientation"], dtype=float) for r in rows])
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    bias, drift = coef[0], coef[1]
    residual = Y - X @ coef
    rms = float(np.sqrt(np.mean(residual ** 2)))
    orientation_resid = []
    for row, resid in zip(rows, residual):
        orientation_resid.append(float(np.linalg.norm(resid)))
    max_resid = max(orientation_resid)
    by_temp = {}
    for row, resid in zip(rows, residual):
        by_temp.setdefault(row["temperature_c"], []).append(float(np.linalg.norm(resid)))
    temp_pattern = max(np.mean(v) for v in by_temp.values()) - min(np.mean(v) for v in by_temp.values())
    diagnosis = "supported"
    abstain = False
    if max_resid > 0.30 and rms < 0.20:
        diagnosis, abstain = "motion_contamination", True
    elif rms > 0.08 and temp_pattern > 0.03:
        diagnosis, abstain = "thermal_nonlinearity", True
    elif rms > 0.08:
        diagnosis, abstain = "axis_misalignment", True
    prediction = GRAVITY * np.asarray(problem["prediction_orientation"]) + bias + drift * (problem["prediction_temperature_c"] - T_REF)
    return {
        "bias_mps2": bias.tolist(),
        "temperature_drift_mps2_per_c": drift.tolist(),
        "prediction_accel_mps2": prediction.tolist(),
        "diagnosis": diagnosis,
        "confidence": float(np.clip(1.0 - rms / 0.25, 0.0, 1.0)),
        "abstain": abstain,
        "evidence_ids": [r["record_id"] for r in rows],
    }
