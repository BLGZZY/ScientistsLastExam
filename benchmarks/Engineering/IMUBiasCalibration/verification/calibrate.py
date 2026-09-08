"""Trusted builder probes; select only on development and replay winners in bubblewrap."""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "Sensors/IMUBiasCalibration"


def shortcut(problem, rms_threshold, peak_threshold, middle_label, peak_label):
    rows = problem["records"]
    dt = np.asarray([r["temperature_c"] - problem["reference_temperature_c"] for r in rows])
    X = np.column_stack([np.ones(len(rows)), dt])
    Y = np.asarray([r["accel_mps2"] for r in rows]) - problem["gravity_mps2"] * np.asarray(
        [r["orientation"] for r in rows])
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    residual = Y - X @ coef
    rms = float(np.sqrt(np.mean(residual ** 2)))
    peak = float(np.max(np.linalg.norm(residual, axis=1)))
    label = peak_label if peak > peak_threshold else middle_label if rms > rms_threshold else "supported"
    prediction = (problem["gravity_mps2"] * np.asarray(problem["prediction_orientation"]) + coef[0]
                  + coef[1] * (problem["prediction_temperature_c"] - problem["reference_temperature_c"]))
    return {"bias_mps2": coef[0].tolist(), "temperature_drift_mps2_per_c": coef[1].tolist(),
            "prediction_accel_mps2": prediction.tolist(), "diagnosis": label,
            "confidence": 1.0, "abstain": label != "supported",
            "evidence_ids": [r["record_id"] for r in rows]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        raise RuntimeError("Calibration evidence requires the Linux sandbox host")
    clean = not subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    if not clean:
        raise RuntimeError("Commit source before generating evidence")
    spec = importlib.util.spec_from_file_location("imu_oracle", HERE / "evaluator.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    labels = ("thermal_nonlinearity", "axis_misalignment", "motion_contamination")
    best_score, best_parameters, count = -1, None, 0
    for parameters in itertools.product(np.linspace(.008, .085, 12), np.linspace(.025, .35, 12), labels, labels):
        # These fixed public-input policies are trusted builder code. Do not run arbitrary
        # model submissions in process. Held-out metrics never select grid parameters.
        rows = [oracle._evaluate_world(world, "development", i, lambda p: shortcut(p, *parameters))
                for i, world in enumerate(oracle.DEVELOPMENT_WORLDS)]
        score = oracle._summary(rows)["combined_score"]
        count += 1
        if score > best_score:
            best_score = score
            best_parameters = (float(parameters[0]), float(parameters[1]), *parameters[2:])
    import inspect
    ref = (HERE / "reference_solver.py").read_text()
    library = ref + "\n" + inspect.getsource(shortcut)
    policies = {"reference": ref, "baseline": (HERE.parent / "solution.py").read_text()}
    for fault in labels:
        policies["without_" + fault] = library + "\ndef infer_imu(problem):\n    return _infer_imu(problem, disabled_faults=(%r,))\n" % fault
    policies["threshold_grid_winner"] = library + "\ndef infer_imu(problem):\n    return shortcut(problem, *%r)\n" % (best_parameters,)
    for name, changes in (
        ("all_abstain_ols", {"abstain": True}),
        ("all_abstain_fixed_fault", {"abstain": True, "diagnosis": "thermal_nonlinearity", "confidence": 0}),
        ("never_refuse", {"abstain": False, "diagnosis": "supported"}),
    ):
        policies[name] = library + "\ndef infer_imu(problem):\n    answer = _infer_imu(problem)\n    answer.update(%r)\n    return answer\n" % changes
    policies["zero_calibration_fixed_fault"] = policies["baseline"].replace('"undetermined"', '"thermal_nonlinearity"')
    report = {"task": TASK_ID,
              "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "source_tree_clean": clean,
              "execution": "Linux trusted-driver / bubblewrap; trusted development-only in-process grid selection",
              "grid": {"policy_count": count, "best_development_score": best_score, "best_parameters": best_parameters},
              "probes": {}}
    with tempfile.TemporaryDirectory(prefix="imu-review-") as tmp:
        for name, source in policies.items():
            candidate = Path(tmp) / (name + ".py")
            candidate.write_text(source)
            results = []
            for _ in range(2):
                run = subprocess.run([sys.executable, "-m", "sle", "eval", "--allow-uncertified",
                                      "--task", TASK_ID, "--candidate", str(candidate)],
                                     cwd=ROOT, capture_output=True, text=True, timeout=360)
                if run.returncode:
                    raise RuntimeError(run.stderr[-1500:])
                results.append(json.loads(run.stdout))
            if results[0] != results[1] or results[0]["valid"] != 1:
                raise AssertionError("invalid or nondeterministic: " + name)
            report["probes"][name] = {"complete_metrics_identical_twice": True, "metrics": results[0]}
            print(name, results[0]["combined_score"], results[0]["heldout_combined_score"], flush=True)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    for metric in ("combined_score", "heldout_combined_score"):
        if report["probes"]["threshold_grid_winner"]["metrics"][metric] >= report["probes"]["reference"]["metrics"][metric]:
            raise AssertionError("shortcut reaches reference on " + metric + "; hardening required")


if __name__ == "__main__":
    main()
