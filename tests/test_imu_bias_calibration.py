from __future__ import annotations

import importlib.util
import copy
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
        self.assertGreater(first["combined_score"], 0.95)
        self.assertGreater(first["heldout_combined_score"], 0.95)
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

    def test_fault_matrix_fails_closed(self):
        oracle = _load("imu_faults", TASK / "verification/evaluator.py")
        baseline = _load("imu_base_faults", TASK / "solution.py")
        variants = [None, {}, [], "wrong"]
        mutations = [
            ("bias_mps2", [0, 0]), ("bias_mps2", [0, 0, float("nan")]),
            ("temperature_drift_mps2_per_c", [0, float("inf"), 0]),
            ("prediction_accel_mps2", [[0], [0], [0]]),
            ("confidence", float("nan")), ("confidence", -1), ("confidence", True),
            ("abstain", 1), ("diagnosis", []), ("diagnosis", "unknown"),
            ("evidence_ids", []), ("evidence_ids", ["fake"]),
            ("evidence_ids", [["r00_00"]]), ("evidence_ids", ["r00_00", "r00_00"]),
            ("extra", 1),
        ]
        for key, value in mutations:
            def bad(problem, key=key, value=value):
                answer = baseline.infer_imu(problem)
                answer[key] = value
                return answer
            variants.append(bad)
        for variant in variants:
            with self.subTest(variant=variant):
                result = oracle.evaluate(variant if callable(variant) else lambda p: variant)
                self.assertEqual(result["valid"], 0)
                self.assertEqual(result["combined_score"], 0)
                self.assertEqual(result["heldout_combined_score"], 0)

    def test_valid_blanket_strategies_are_zero(self):
        oracle = _load("imu_blanket", TASK / "verification/evaluator.py")
        reference = _load("imu_ref_blanket", TASK / "verification/reference_solver.py")
        for abstain in (True, False):
            for diagnosis in oracle.VALID_DIAGNOSES:
                for confidence in (0.0, 0.5, 1.0):
                    def policy(problem):
                        answer = reference.infer_imu(problem)
                        answer.update(abstain=abstain, diagnosis=diagnosis, confidence=confidence)
                        return answer
                    result = oracle.evaluate(policy)
                    self.assertEqual(result["valid"], 1)
                    self.assertEqual(result["combined_score"], 0)
                    self.assertEqual(result["heldout_combined_score"], 0)
                    self.assertEqual(result["attempted_discovery"], float(not abstain))

    def test_supported_abstention_and_wrong_diagnosis_get_no_credit(self):
        oracle = _load("imu_score", TASK / "verification/evaluator.py")
        spec = {"kind": "supported", "bias": [0, 0, 0], "drift": [0, 0, 0]}
        answer = {"abstain": False, "diagnosis": "supported", "confidence": 1,
                  "bias_mps2": [0, 0, 0], "temperature_drift_mps2_per_c": [0, 0, 0],
                  "prediction_accel_mps2": [0, 0, oracle.GRAVITY]}
        good = oracle._score(spec, answer, oracle.PUBLIC_PROBLEM)
        self.assertEqual(good["combined_score"], 1)
        for changes in ({"abstain": True}, {"diagnosis": "thermal_nonlinearity"}):
            row = oracle._score(spec, {**answer, **changes}, oracle.PUBLIC_PROBLEM)
            self.assertEqual(row["combined_score"], 0)
            self.assertEqual(row["prediction_score"], 0)
        fault = oracle._score({"kind": "axis_misalignment"},
                             {**answer, "abstain": True, "diagnosis": "thermal_nonlinearity"}, {})
        self.assertEqual(fault["combined_score"], 0)
        self.assertEqual(fault["prediction_score"], 0)

    def test_metric_denominators_include_missed_and_invalid_worlds(self):
        oracle = _load("imu_counts", TASK / "verification/evaluator.py")
        template = {"kind": "supported", "valid": True, "abstained": False,
                    "mechanism_correct": True, "correct_refusal": False, "false_discovery": False,
                    "combined_score": .4, "science_score": .3, "confidence_calibration_score": .5}
        rows = [template, {**template, "mechanism_correct": False, "false_discovery": True},
                {**template, "abstained": True, "mechanism_correct": False},
                {**template, "valid": False, "abstained": True, "mechanism_correct": False},
                {**template, "kind": "thermal_nonlinearity", "mechanism_correct": False,
                 "abstained": True, "correct_refusal": True},
                {**template, "kind": "axis_misalignment", "mechanism_correct": False,
                 "false_discovery": True}]
        metrics = oracle._summary(rows)
        self.assertEqual(metrics["mechanism_score"], 1/4)
        self.assertEqual(metrics["mechanism_denominator"], 4)
        self.assertEqual(metrics["discovery_coverage"], 2/4)
        self.assertEqual(metrics["discovery_denominator"], 4)
        self.assertEqual(metrics["false_discovery_rate"], 2/3)
        self.assertEqual(metrics["false_discovery_denominator"], 3)
        self.assertEqual(metrics["correct_refusal_rate"], 1/2)
        self.assertEqual(metrics["correct_refusal_denominator"], 2)
        self.assertNotEqual(metrics["mechanism_score"], metrics["science_score"])

    def test_candidate_cannot_mutate_validation_records_or_shared_problem(self):
        oracle = _load("imu_mutation", TASK / "verification/evaluator.py")
        baseline = _load("imu_mutation_base", TASK / "solution.py")
        original = copy.deepcopy(oracle.PUBLIC_PROBLEM)
        def mutate(problem):
            problem["prediction_orientation"][0] = 999
            problem["records"][0]["record_id"] = "fabricated"
            return baseline.infer_imu(problem)
        result = oracle.evaluate(mutate)
        self.assertEqual(result["valid"], 0)
        self.assertEqual(oracle.PUBLIC_PROBLEM, original)

    def test_fresh_session_and_metric_key_parity(self):
        oracle = _load("imu_session", TASK / "verification/evaluator.py")
        baseline = _load("imu_session_base", TASK / "solution.py")
        class Candidate:
            count = 0
            def reset_session(self):
                self.count += 1
            def __call__(self, problem):
                return baseline.infer_imu(problem)
        candidate = Candidate()
        good = oracle.evaluate(candidate)
        bad = oracle.evaluate(lambda p: {})
        self.assertEqual(candidate.count, len(good["per_instance"]))
        self.assertEqual(set(good), set(bad))
        self.assertEqual(set(good["per_instance"][0]), set(bad["per_instance"][0]))
        for split in ("development", "heldout"):
            for key in ("mechanism_score", "false_discovery_rate", "correct_refusal_rate", "discovery_coverage"):
                self.assertIn(split + "_" + key, good)
