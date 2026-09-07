from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks" / "Engineering" / "IMUBiasCalibration"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class IMUBiasCalibrationTests(unittest.TestCase):
    def test_reference_is_deterministic_and_baseline_is_zero(self):
        oracle = _load("imu_evaluator", TASK / "verification" / "evaluator.py")
        reference = _load("imu_reference", TASK / "verification" / "reference_solver.py")

        def ref(problem):
            return reference.infer_imu(problem)

        first = oracle.evaluate(ref)
        second = oracle.evaluate(ref)
        self.assertEqual(first, second)
        self.assertGreater(first["combined_score"], 0.98)
        self.assertGreater(first["heldout_combined_score"], 0.98)
        unsupported = [row for row in first["per_instance"] if row["kind"] != "supported"]
        supported = [row for row in first["per_instance"] if row["kind"] == "supported"]
        self.assertTrue(all(row["correct_refusal"] for row in unsupported))
        self.assertTrue(all(not row["false_discovery"] for row in unsupported))
        self.assertTrue(all(not row["abstained"] for row in supported))

        baseline = _load("imu_baseline", TASK / "solution.py")
        base = oracle.evaluate(baseline.infer_imu)
        self.assertEqual(base["combined_score"], 0.0)
        self.assertEqual(base["valid"], 1.0)

    def test_malformed_submission_is_invalid(self):
        oracle = _load("imu_evaluator_bad", TASK / "verification" / "evaluator.py")
        result = oracle.evaluate(lambda problem: {})
        self.assertEqual(result["valid"], 0.0)
        self.assertEqual(result["combined_score"], 0.0)
