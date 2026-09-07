"""Weak valid baseline: report zero calibration and decline the model."""


def infer_imu(problem):
    return {
        "bias_mps2": [0.0, 0.0, 0.0],
        "temperature_drift_mps2_per_c": [0.0, 0.0, 0.0],
        "prediction_accel_mps2": [0.0, 0.0, 0.0],
        "diagnosis": "undetermined",
        "confidence": 0.0,
        "abstain": True,
        "evidence_ids": [r["record_id"] for r in problem["records"]],
    }
