"""Pinned invariants for the 2026-09-05 round-four candidate tasks.

Each class pins the construction errors recorded in the task's known_best.md and
the repo-wide baseline/reference/bad-candidate contract. Tests load evaluators
directly; sandbox-dependent behaviour is out of scope here.
"""


from __future__ import annotations


import importlib.util


import json


import sys


import unittest


from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


TASKS = {'Algorithm/ScalingLawIdentification': ('benchmarks/ComputerScience/ScalingLawIdentification',
                                        'identify_scaling_law')}


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


class ScalingLawPins(unittest.TestCase):
    def test_reference_ladder_matches_public_nine_unit_budget(self):
        task = ROOT / "benchmarks/ComputerScience/ScalingLawIdentification"
        ev = _load(task / "verification/evaluator.py", "scale_budget_contract")
        ref = _load(task / "verification/reference_solver.py", "scale_ladder_contract")
        costs = [1 if size <= 64 else 2 if size <= 192 else 3
                 for size in ref.SIZES]
        self.assertEqual(ref.SIZES, (16, 16, 16, 13, 27, 55, 62, 192))
        self.assertEqual(sum(costs), ev.BUDGET_UNITS)
        self.assertEqual(ev.BUDGET_UNITS, 9)

    def test_branch_world_is_deterministic_in_size(self):
        ev = _load("benchmarks/ComputerScience/ScalingLawIdentification"
                   "/verification/evaluator.py", "r4_scale")
        world = ev._world((30041, "branch", "branch"))
        self.assertEqual(ev._true_runtime(world, 334), ev._true_runtime(world, 334))
        # The branch predicate splits sizes into two runtime regimes; under either
        # the mod-three or mod-seven design the split is at least 25x at size ~330.
        ratio = max(ev._true_runtime(world, 331) / ev._true_runtime(world, 332),
                    ev._true_runtime(world, 332) / ev._true_runtime(world, 331))
        self.assertGreater(ratio, 25.0)

    def test_tightened_statistics_beat_lazy_ladders(self):
        # The fixed-shape BIC reference with the predicate-agnostic branch scan
        # remains accurate while the evidence-efficiency axis prevents saturation;
        # free-slope regression (v1)
        # collapsed the power-law classes into one family and scored 0.470.
        ev = _load("benchmarks/ComputerScience/ScalingLawIdentification"
                   "/verification/evaluator.py", "r4_scale")
        ref = _load(ROOT / "benchmarks/ComputerScience/ScalingLawIdentification"
                    "/verification" / "reference_solver.py", "r4_scale_ref")
        reference = ev.evaluate(ref.identify_scaling_law)
        self.assertLess(reference["combined_score"], 0.75)
        self.assertGreater(reference["combined_score"], 0.65)
        self.assertAlmostEqual(reference["development_evidence_efficiency_score"], 0.75)
        self.assertEqual(reference["development_correct_refusal_rate"], 1.0)
        self.assertEqual(reference["development_false_discovery_rate"], 0.0)
        self.assertGreater(reference["robustness_score"], 0.60)

    def test_jitter_worlds_carry_a_lawful_family(self):
        ev = _load("benchmarks/ComputerScience/ScalingLawIdentification"
                   "/verification/evaluator.py", "r4_scale")
        for spec in ev._BASE_DEVELOPMENT_SPECS + ev.HELDOUT_SPECS:
            world = ev._world(spec)
            if world["kind"] != "branch":
                self.assertIn(world["family"], ev.CLASSES)


class ScalingLawRunnerIntegration(unittest.TestCase):
    """Launch frontier_eval/run_eval.py exactly as eval_command.txt does.

    The shipped runner was once an unrendered template: it wrote the metrics file
    and then died on a doubled-brace set literal, so every entrypoint run exited
    nonzero. This test executes the real command line so that class of defect
    cannot come back unnoticed.
    """

    def test_runner_executes_reference_end_to_end(self):
        import subprocess
        import tempfile

        task = ROOT / "benchmarks/ComputerScience/ScalingLawIdentification"
        command = [
            sys.executable, "frontier_eval/run_eval.py",
            "--candidate", str((task / "verification" / "reference_solver.py").resolve()),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            metrics_path = Path(tmp) / "metrics.json"
            command += ["--metrics-out", str(metrics_path)]
            completed = subprocess.run(command, cwd=str(task), capture_output=True,
                                       text=True, timeout=300)
            self.assertEqual(completed.returncode, 0, completed.stderr[-500:])
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            for key in ("combined_score", "valid", "robustness_score",
                        "mechanism_score"):
                self.assertIn(key, metrics)
            self.assertEqual(metrics["valid"], 1.0)
            self.assertNotIn("error_message", metrics)
            reported = json.loads(completed.stdout.strip().splitlines()[-1])
            self.assertEqual(reported["combined_score"], metrics["combined_score"])


if __name__ == "__main__":
    unittest.main()
