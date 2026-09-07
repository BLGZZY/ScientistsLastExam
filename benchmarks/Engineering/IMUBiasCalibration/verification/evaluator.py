"""Deterministic inertial-sensor bias and drift laboratory."""
from __future__ import annotations

import math
from typing import Any

import numpy as np

GRAVITY = 9.80665
T_REF = 25.0
VALID_DIAGNOSES = {
    "supported", "thermal_nonlinearity", "axis_misalignment", "motion_contamination",
    "undetermined",
}

PUBLIC_PROBLEM = {
    "schema_version": 1,
    "gravity_mps2": GRAVITY,
    "reference_temperature_c": T_REF,
    "prediction_temperature_c": 55.0,
    "prediction_orientation": [0.0, 0.0, 1.0],
    "diagnosis_values": sorted(VALID_DIAGNOSES),
    "measurement_model": "a = g*u + bias + temperature_drift*(T-T_ref) + noise",
    "abstain_when": "nonlinear temperature response, cross-axis misalignment, or motion contamination",
}

_ORIENTATIONS = np.asarray([
    [1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
    [0.0, -1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, -1.0],
], dtype=float)
_TEMPERATURES = (5.0, 20.0, 35.0, 50.0)

DEVELOPMENT_WORLDS = (
    {"kind": "supported", "seed": 1201, "bias": [0.11, -0.07, 0.16], "drift": [0.0015, -0.0020, 0.0010]},
    {"kind": "supported", "seed": 1202, "bias": [-0.18, 0.09, 0.05], "drift": [0.0022, 0.0010, -0.0018]},
    {"kind": "thermal_nonlinearity", "seed": 1203, "bias": [0.08, 0.04, -0.12], "drift": [0.0010, -0.0012, 0.0015], "quadratic_axis": 1, "quadratic": 0.00020},
    {"kind": "axis_misalignment", "seed": 1204, "bias": [0.12, -0.11, 0.06], "drift": [0.0010, 0.0014, -0.0010], "misalignment_scale": 0.44},
    {"kind": "motion_contamination", "seed": 1205, "bias": [-0.04, 0.13, 0.08], "drift": [0.0014, -0.0010, 0.0012], "motion": [0.22, -0.15, 0.12]},
)
HELDOUT_WORLDS = (
    {"kind": "supported", "seed": 2201, "bias": [0.20, 0.03, -0.09], "drift": [-0.0015, 0.0018, 0.0011]},
    {"kind": "supported", "seed": 2202, "bias": [-0.06, -0.16, 0.12], "drift": [0.0020, -0.0015, -0.0013]},
    {"kind": "thermal_nonlinearity", "seed": 2203, "bias": [0.05, -0.02, 0.10], "drift": [0.0012, 0.0010, -0.0014], "quadratic_axis": 2, "quadratic": 0.00017},
    {"kind": "axis_misalignment", "seed": 2204, "bias": [0.09, 0.07, -0.05], "drift": [-0.0011, 0.0013, 0.0016], "misalignment_scale": 0.38},
)


def _records(spec: dict[str, Any]) -> list[dict[str, Any]]:
    rng = np.random.default_rng(spec["seed"])
    bias = np.asarray(spec["bias"], dtype=float)
    drift = np.asarray(spec["drift"], dtype=float)
    rows = []
    for oi, orientation in enumerate(_ORIENTATIONS):
        for ti, temp in enumerate(_TEMPERATURES):
            u = orientation.copy()
            value = GRAVITY * u + bias + drift * (temp - T_REF)
            if spec["kind"] == "thermal_nonlinearity":
                value[spec["quadratic_axis"]] += spec["quadratic"] * (temp - T_REF) ** 2
            elif spec["kind"] == "axis_misalignment":
                scale = spec["misalignment_scale"]
                matrix = np.eye(3) + scale * np.asarray([[0.0, 0.018, -0.012], [-0.014, 0.0, 0.020], [0.010, -0.016, 0.0]])
                value = matrix @ (GRAVITY * u) + bias + drift * (temp - T_REF)
            elif spec["kind"] == "motion_contamination" and oi == 0 and ti in (1, 2):
                value = value + np.asarray(spec["motion"])
            value = value + rng.normal(0.0, 0.012, size=3)
            rows.append({
                "record_id": f"r{oi:02d}_{ti:02d}",
                "temperature_c": float(temp),
                "orientation": [float(x) for x in u],
                "accel_mps2": [float(x) for x in value],
            })
    return rows


def public_problem(spec: dict[str, Any]) -> dict[str, Any]:
    problem = dict(PUBLIC_PROBLEM)
    problem["records"] = _records(spec)
    return problem


def _validate(submission: Any, problem: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(submission, dict):
        raise ValueError("submission must be a mapping")
    required = {"bias_mps2", "temperature_drift_mps2_per_c", "prediction_accel_mps2", "diagnosis", "confidence", "abstain", "evidence_ids"}
    if set(submission) != required:
        raise ValueError("submission keys must match the public contract exactly")
    if not isinstance(submission["abstain"], bool):
        raise ValueError("abstain must be boolean")
    if submission["diagnosis"] not in VALID_DIAGNOSES:
        raise ValueError("unknown diagnosis")
    confidence = float(submission["confidence"])
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be in [0,1]")
    def vector(name: str) -> np.ndarray:
        value = submission[name]
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            raise ValueError(f"{name} must have length three")
        arr = np.asarray(value, dtype=float)
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{name} must be finite")
        return arr
    result = {name: vector(name) for name in ("bias_mps2", "temperature_drift_mps2_per_c", "prediction_accel_mps2")}
    ids = submission["evidence_ids"]
    allowed = {row["record_id"] for row in problem["records"]}
    if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)) or not set(ids).issubset(allowed):
        raise ValueError("evidence_ids must be unique record IDs")
    result.update({"diagnosis": submission["diagnosis"], "confidence": confidence, "abstain": submission["abstain"], "evidence_ids": ids})
    return result


def _fit_reference(problem: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    rows = problem["records"]
    X = np.asarray([[1.0, row["temperature_c"] - T_REF] for row in rows], dtype=float)
    Y = np.asarray([np.asarray(row["accel_mps2"]) - GRAVITY * np.asarray(row["orientation"]) for row in rows])
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    bias, drift = coef[0], coef[1]
    residual = Y - X @ coef
    return bias, drift, residual, float(np.sqrt(np.mean(residual ** 2)))


def _score(spec: dict[str, Any], result: dict[str, Any], problem: dict[str, Any]) -> dict[str, Any]:
    unsupported = spec["kind"] != "supported"
    correct_refusal = unsupported and result["abstain"] and result["diagnosis"] == spec["kind"]
    false_discovery = unsupported and not result["abstain"]
    if unsupported:
        science = 1.0 if correct_refusal else 0.0
        prediction = 1.0 if result["abstain"] else 0.0
    else:
        truth_b = np.asarray(spec["bias"])
        truth_d = np.asarray(spec["drift"])
        be = float(np.linalg.norm(result["bias_mps2"] - truth_b))
        de = float(np.linalg.norm(result["temperature_drift_mps2_per_c"] - truth_d))
        target = GRAVITY * np.asarray(problem["prediction_orientation"]) + truth_b + truth_d * (problem["prediction_temperature_c"] - T_REF)
        pe = float(np.linalg.norm(result["prediction_accel_mps2"] - target))
        science = float(np.clip(1.0 - 0.55 * be / 0.35 - 0.30 * de / 0.006 - 0.15 * pe / 0.5, 0.0, 1.0))
        prediction = float(np.clip(1.0 - pe / 0.5, 0.0, 1.0))
    confidence_score = float(np.clip(1.0 - abs(result["confidence"] - science), 0.0, 1.0))
    combined = float(np.clip(0.70 * science + 0.20 * prediction + 0.10 * confidence_score, 0.0, 1.0))
    return {"science_score": round(science, 6), "prediction_score": round(prediction, 6), "confidence_calibration_score": round(confidence_score, 6), "correct_refusal": bool(correct_refusal), "false_discovery": bool(false_discovery), "combined_score": round(combined, 6)}


def _evaluate_world(spec: dict[str, Any], split: str, index: int, candidate) -> dict[str, Any]:
    problem = public_problem(spec)
    base = {"split": split, "world_index": index, "kind": spec["kind"]}
    try:
        result = _validate(candidate(problem), problem)
        row = dict(base)
        row.update(_score(spec, result, problem))
        row.update({"valid": True, "abstained": result["abstain"], "confidence": round(result["confidence"], 6), "evidence_count": len(result["evidence_ids"])})
        return row
    except Exception as exc:  # noqa: BLE001
        row = dict(base)
        row.update({"combined_score": 0.0, "science_score": 0.0, "prediction_score": 0.0, "confidence_calibration_score": 0.0, "correct_refusal": False, "false_discovery": False, "valid": False, "abstained": True, "confidence": 0.0, "evidence_count": 0, "reason": f"{type(exc).__name__}: {exc}"})
        return row


def evaluate(candidate) -> dict[str, Any]:
    development = [_evaluate_world(spec, "development", i, candidate) for i, spec in enumerate(DEVELOPMENT_WORLDS)]
    heldout = [_evaluate_world(spec, "heldout", i, candidate) for i, spec in enumerate(HELDOUT_WORLDS)]
    def summary(rows):
        raw = float(np.mean([r["combined_score"] for r in rows]))
        normalized = float(np.clip((raw - 0.22) / 0.78, 0.0, 1.0))
        return {"combined_score": round(normalized, 6), "raw_combined_score": round(raw, 6), "valid": float(all(r["valid"] for r in rows)), "science_score": round(float(np.mean([r["science_score"] for r in rows])), 6), "correct_refusal_rate": round(float(np.mean([r["correct_refusal"] for r in rows if r["kind"] != "supported"])), 6), "false_discovery_rate": round(float(np.mean([r["false_discovery"] for r in rows if r["kind"] != "supported"])), 6), "world_count": len(rows)}
    dev, held = summary(development), summary(heldout)
    return {"combined_score": dev["combined_score"], "valid": dev["valid"], "raw_score": dev["combined_score"], "development": dev, "heldout": held, "development_combined_score": dev["combined_score"], "heldout_combined_score": held["combined_score"], "per_instance": development + heldout}
