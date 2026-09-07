"""Pinned invariants for the 2026-09-05 round-four candidate tasks.

Each class pins the construction errors recorded in the task's known_best.md and
the repo-wide baseline/reference/bad-candidate contract. Tests load evaluators
directly; sandbox-dependent behaviour is out of scope here.
"""


from __future__ import annotations


import importlib.util


import json


import subprocess


import sys


import tempfile


import unittest


from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


TASKS = {'Mathematics/EllipticCurveRecovery': ('benchmarks/Mathematics/EllipticCurveRecovery',
                                       'recover_curve')}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RoundFourPackageTests(unittest.TestCase):
    def test_baselines_valid_zero_and_deterministic(self):
        for task_id, (directory, entrypoint) in TASKS.items():
            evaluator = _load(ROOT / directory / "verification" / "evaluator.py",
                              "r4_evaluator_" + entrypoint)
            baseline = _load(ROOT / directory / "solution.py",
                             "r4_baseline_" + entrypoint)
            first = evaluator.evaluate(getattr(baseline, entrypoint))
            second = evaluator.evaluate(getattr(baseline, entrypoint))
            self.assertEqual(first["valid"], 1.0, task_id)
            self.assertLessEqual(abs(first["combined_score"]), 0.01, task_id)
            self.assertEqual(json.dumps(first, sort_keys=True, default=str),
                             json.dumps(second, sort_keys=True, default=str), task_id)

    def test_references_valid_and_above_floor(self):
        for task_id, (directory, entrypoint) in TASKS.items():
            evaluator = _load(ROOT / directory / "verification" / "evaluator.py",
                              "r4_evaluator_ref_" + entrypoint)
            reference = _load(ROOT / directory / "verification" / "reference_solver.py",
                              "r4_reference_" + entrypoint)
            result = evaluator.evaluate(getattr(reference, entrypoint))
            self.assertEqual(result["valid"], 1.0, task_id)
            self.assertGreater(result["combined_score"], 0.05, task_id)

    def test_bad_candidates_score_invalid_without_crashing(self):
        def raises(*args, **kwargs):
            raise RuntimeError("candidate failure")

        for task_id, (directory, entrypoint) in TASKS.items():
            evaluator = _load(ROOT / directory / "verification" / "evaluator.py",
                              "r4_evaluator_bad_" + entrypoint)
            for candidate in (raises, lambda *a, **k: {}, lambda *a, **k: "junk"):
                result = evaluator.evaluate(candidate)
                self.assertEqual(result["valid"], 0.0, task_id)
                self.assertEqual(result["combined_score"], 0.0, task_id)


class EllipticCurvePins(unittest.TestCase):
    def test_public_budget_matches_evaluator_contract(self):
        task = ROOT / "benchmarks/Mathematics/EllipticCurveRecovery"
        ev = _load(task / "verification/evaluator.py", "ec_budget_contract")
        task_text = (task / "Task.md").read_text(encoding="utf-8")
        self.assertEqual(ev.BUDGET_UNITS, 8)
        self.assertIn("budget_units      8", task_text)

    def test_exact_reference_leaves_room_for_a_smaller_prime_certificate(self):
        task = ROOT / "benchmarks/Mathematics/EllipticCurveRecovery"
        ev = _load(task / "verification/evaluator.py", "r4_ec_calibration")
        ref = _load(task / "verification/reference_solver.py", "r4_ec_reference")
        result = ev.evaluate(ref.recover_curve)
        self.assertEqual(result["valid"], 1.0)
        self.assertAlmostEqual(result["combined_score"], 0.75)
        self.assertAlmostEqual(result["development_evidence_efficiency_score"], 0.75)
        self.assertEqual(result["development_correct_refusal_rate"], 1.0)
        self.assertEqual(result["development_false_discovery_rate"], 0.0)

    def test_counts_match_direct_enumeration(self):
        ev = _load("benchmarks/Mathematics/EllipticCurveRecovery/verification/evaluator.py",
                   "r4_ec")
        self.assertEqual(ev._legendre_count_cubic(11, 0, 1), 12)  # 11 + 1 + 0? direct:
        # y^2 = x^3 + 1 over F_11 has 12 points (a classical count).
        self.assertEqual(ev._legendre_count_cubic(7, 0, 0), 7 + 1 + 0)

    def test_singular_worlds_have_zero_discriminant(self):
        ev = _load("benchmarks/Mathematics/EllipticCurveRecovery/verification/evaluator.py",
                   "r4_ec")
        for spec in ev._BASE_DEVELOPMENT_SPECS + ev.HELDOUT_SPECS:
            world = ev._world(spec)
            if world["kind"] == "singular":
                self.assertEqual(4 * world["a"] ** 3 + 27 * world["b"] ** 2, 0)


class RunnerIntegrationTests(unittest.TestCase):
    """The black-box entrypoint must survive a real subprocess launch.

    Pins the 2026-09-07 fix for the unrendered-template artifacts: an f-string
    with literal ``{{...}}`` braces and a set-literal ``{{key: ...}}`` print that
    crashed the runner with ``TypeError: unhashable type: 'dict'`` *after* the
    metrics file was already written, so exit code 1 hid a completed evaluation.
    """

    SCORE_KEYS = ("combined_score", "raw_score", "robustness_score", "valid",
                  "development_evidence_efficiency_score",
                  "heldout_evidence_efficiency_score")

    def _run_entrypoint(self, candidate: str) -> tuple[int, dict, dict]:
        task = ROOT / "benchmarks/Mathematics/EllipticCurveRecovery"
        with tempfile.TemporaryDirectory() as tmp:
            metrics_path = Path(tmp) / "metrics.json"
            completed = subprocess.run(
                [sys.executable, str(task / "frontier_eval" / "run_eval.py"),
                 "--candidate", str(task / candidate),
                 "--metrics-out", str(metrics_path)],
                cwd=ROOT, capture_output=True, text=True, timeout=120)
            stdout = json.loads(completed.stdout.strip().splitlines()[-1])
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        return completed.returncode, stdout, metrics

    def test_reference_exits_zero_and_reports_score_keys(self):
        returncode, stdout, metrics = self._run_entrypoint(
            "verification/reference_solver.py")
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, {"combined_score": 0.75, "valid": 1.0})
        for key in self.SCORE_KEYS:
            self.assertIn(key, metrics)
        self.assertEqual(metrics["valid"], 1.0)
        self.assertAlmostEqual(metrics["combined_score"], 0.75)
        self.assertAlmostEqual(metrics["robustness_score"], 0.75)
        self.assertNotIn("error_message", metrics)

    def test_baseline_exits_zero_with_a_written_metrics_file(self):
        returncode, stdout, metrics = self._run_entrypoint("solution.py")
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout["valid"], 1.0)
        for key in self.SCORE_KEYS:
            self.assertIn(key, metrics)
        self.assertAlmostEqual(metrics["combined_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
