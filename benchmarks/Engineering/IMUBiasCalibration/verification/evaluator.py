"""Deterministic inertial-sensor bias and drift laboratory."""
from __future__ import annotations

import math
import copy
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
    problem = copy.deepcopy(PUBLIC_PROBLEM)
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
    if not isinstance(submission["diagnosis"], str) or submission["diagnosis"] not in VALID_DIAGNOSES:
        raise ValueError("unknown diagnosis")
    if isinstance(submission["confidence"], bool) or not isinstance(submission["confidence"], (int, float)):
        raise ValueError("confidence must be numeric")
    confidence = float(submission["confidence"])
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be in [0,1]")
    def vector(name: str) -> np.ndarray:
        value = submission[name]
        if not isinstance(value, (list, tuple)) or len(value) != 3 or any(
            isinstance(x, bool) or not isinstance(x, (int, float)) for x in value
        ):
            raise ValueError(f"{name} must have length three")
        arr = np.asarray(value, dtype=float)
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{name} must be finite")
        return arr
    result = {name: vector(name) for name in ("bias_mps2", "temperature_drift_mps2_per_c", "prediction_accel_mps2")}
    ids = submission["evidence_ids"]
    allowed = {row["record_id"] for row in problem["records"]}
    if not isinstance(ids, list) or not ids or not all(isinstance(x, str) for x in ids) or len(ids) != len(set(ids)) or not set(ids).issubset(allowed):
        raise ValueError("evidence_ids must be unique record IDs")
    result.update({"diagnosis": submission["diagnosis"], "confidence": confidence, "abstain": submission["abstain"], "evidence_ids": ids})
    return result


def _score(spec: dict[str, Any], result: dict[str, Any], problem: dict[str, Any]) -> dict[str, Any]:
    unsupported = spec["kind"] != "supported"
    correct_refusal = unsupported and result["abstain"] and result["diagnosis"] == spec["kind"]
    claimed = not result["abstain"]
    mechanism_correct = not unsupported and claimed and result["diagnosis"] == "supported"
    false_discovery = claimed and not mechanism_correct
    if unsupported:
        science = 1.0 if correct_refusal else 0.0
        prediction = 0.0
    elif mechanism_correct:
        truth_b = np.asarray(spec["bias"])
        truth_d = np.asarray(spec["drift"])
        be = float(np.linalg.norm(result["bias_mps2"] - truth_b))
        de = float(np.linalg.norm(result["temperature_drift_mps2_per_c"] - truth_d))
        target = GRAVITY * np.asarray(problem["prediction_orientation"]) + truth_b + truth_d * (problem["prediction_temperature_c"] - T_REF)
        pe = float(np.linalg.norm(result["prediction_accel_mps2"] - target))
        science = float(np.clip(1.0 - 0.55 * be / 0.35 - 0.30 * de / 0.006 - 0.15 * pe / 0.5, 0.0, 1.0))
        prediction = float(np.clip(1.0 - pe / 0.5, 0.0, 1.0))
    else:
        science = prediction = 0.0
    confidence_score = float(np.clip(1.0 - abs(result["confidence"] - science), 0.0, 1.0))
    # Refusals earn one unit only for correct fault attribution. No free confidence
    # or prediction credit is awarded to missed or incorrectly labelled findings.
    combined = float(correct_refusal) if unsupported else (
        0.70 * science + 0.20 * prediction + 0.10 * confidence_score if mechanism_correct else 0.0
    )
    return {"science_score": round(science, 6), "prediction_score": round(prediction, 6), "confidence_calibration_score": round(confidence_score, 6), "correct_refusal": bool(correct_refusal), "false_discovery": bool(false_discovery), "mechanism_correct": bool(mechanism_correct), "combined_score": round(combined, 6)}


def _evaluate_world(spec: dict[str, Any], split: str, index: int, candidate) -> dict[str, Any]:
    problem = public_problem(spec)
    base = {"split": split, "world_index": index, "kind": spec["kind"]}
    try:
        if hasattr(candidate, "reset_session"):
            candidate.reset_session()
        result = _validate(candidate(copy.deepcopy(problem)), problem)
        row = dict(base)
        row.update(_score(spec, result, problem))
        row.update({"valid": True, "abstained": result["abstain"], "confidence": round(result["confidence"], 6), "evidence_count": len(result["evidence_ids"]), "reason": ""})
        return row
    except Exception as exc:  # noqa: BLE001
        row = dict(base)
        row.update({"combined_score": 0.0, "science_score": 0.0, "prediction_score": 0.0, "confidence_calibration_score": 0.0, "correct_refusal": False, "false_discovery": False, "mechanism_correct": False, "valid": False, "abstained": True, "confidence": 0.0, "evidence_count": 0, "reason": f"{type(exc).__name__}: {exc}"})
        return row


def _summary(rows):
    supported = [r for r in rows if r["kind"] == "supported"]
    unsupported_count = len(rows) - len(supported)
    claims = sum(r["valid"] and not r["abstained"] for r in rows)
    supported_claims = sum(r["valid"] and not r["abstained"] for r in supported)
    mechanism_count = sum(r["mechanism_correct"] for r in supported)
    refusal_count = sum(r["correct_refusal"] for r in rows)
    false_count = sum(r["false_discovery"] for r in rows)
    raw = float(np.mean([r["combined_score"] for r in rows]))
    refusal_rate = refusal_count / unsupported_count if unsupported_count else 1.0
    # Subtract the maximum reward available without any supported finding.
    # The additional refusal multiplier makes never-refusing fits score zero too.
    normalized = float(np.clip((sum(r["combined_score"] for r in rows) - unsupported_count)
                              / max(1, len(supported)), 0.0, 1.0)) * refusal_rate
    valid = float(all(r["valid"] for r in rows))
    return {
        "combined_score": round(normalized, 6) if valid else 0.0,
        "raw_combined_score": round(raw, 6), "valid": valid,
        "science_score": round(float(np.mean([r["science_score"] for r in rows])), 6),
        "mechanism_score": mechanism_count / max(1, len(supported)),
        "mechanism_correct_count": mechanism_count, "mechanism_denominator": len(supported),
        "false_discovery_rate": false_count / max(1, claims),
        "false_discovery_count": false_count, "false_discovery_denominator": claims,
        "correct_refusal_rate": refusal_rate,
        "correct_refusal_count": refusal_count, "correct_refusal_denominator": unsupported_count,
        "discovery_coverage": supported_claims / max(1, len(supported)),
        "discovery_count": supported_claims, "discovery_denominator": len(supported),
        "attempted_discovery": float(claims > 0), "claim_count": claims,
        "confidence_calibration_score": float(np.mean([r["confidence_calibration_score"] for r in rows])),
        "world_count": len(rows),
    }


def evaluate(candidate) -> dict[str, Any]:
    development = [_evaluate_world(spec, "development", i, candidate) for i, spec in enumerate(DEVELOPMENT_WORLDS)]
    heldout = [_evaluate_world(spec, "heldout", i, candidate) for i, spec in enumerate(HELDOUT_WORLDS)]
    dev, held = _summary(development), _summary(heldout)
    metrics = {"combined_score": dev["combined_score"], "valid": min(dev["valid"], held["valid"]), "raw_score": dev["combined_score"], "development": dev, "heldout": held, "robustness_score": held["combined_score"], "attempted_discovery": dev["attempted_discovery"], "per_instance": development + heldout}
    for split, summary in (("development", dev), ("heldout", held)):
        metrics.update({f"{split}_{key}": value for key, value in summary.items()})
    if not metrics["valid"]:
        metrics["combined_score"] = metrics["raw_score"] = 0.0
    return metrics
