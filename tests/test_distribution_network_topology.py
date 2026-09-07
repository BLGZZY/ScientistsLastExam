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
from _sandbox_tools import skip_unless_sandbox
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


TASKS = {'WaterDistribution/DistributionNetworkTopology': ('benchmarks/Engineering/DistributionNetworkTopology',
                                                   'recover_network')}


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


class DistributionNetworkPins(unittest.TestCase):
    def test_default_level_carries_three_break_ambiguity(self):
        ev = _load("benchmarks/Engineering/DistributionNetworkTopology"
                   "/verification/evaluator.py", "r4_water")
        self.assertEqual(ev.DIFFICULTY, 3)
        self.assertEqual(ev._difficulty_profile()["max_broken"], 3)

    def test_twin_pipes_share_route_signatures(self):
        ev = _load("benchmarks/Engineering/DistributionNetworkTopology"
                   "/verification/evaluator.py", "r4_water")
        incidence = {}
        for route_id, pipes in zip(ev.ROUTE_IDS, ev.ROUTES):
            for pipe in pipes:
                incidence.setdefault(pipe, set()).add(route_id)
        self.assertEqual(incidence["s11"], incidence["s21"])
        covered = set(incidence)
        self.assertEqual(covered, set(ev.PIPE_IDS))

    def test_supported_break_sets_are_signature_unique(self):
        ev = _load("benchmarks/Engineering/DistributionNetworkTopology"
                   "/verification/evaluator.py", "r4_water")
        for spec in ev._BASE_DEVELOPMENT_SPECS + ev.HELDOUT_SPECS:
            world = ev._world(spec)
            if world["kind"] == "supported":
                self.assertTrue(ev._identifiable(world["broken"], 3), spec)


@skip_unless_sandbox("bwrap")
class RunEvalIntegrationTests(unittest.TestCase):
    """The frontier_eval runner must execute through the Linux candidate sandbox.

    It pins the eval_command.txt contract:
    exit 0, a summary line on stdout, and the full metrics file with the task's
    real score keys.
    """

    def test_reference_candidate_runs_through_run_eval(self):
        task = ROOT / "benchmarks/Engineering/DistributionNetworkTopology"
        with tempfile.TemporaryDirectory() as tmp:
            metrics_path = Path(tmp) / "metrics.json"
            completed = subprocess.run(
                [sys.executable,
                 str(task / "frontier_eval" / "run_eval.py"),
                 "--candidate",
                 str(task / "verification" / "reference_solver.py"),
                 "--metrics-out", str(metrics_path)],
                cwd=str(ROOT), capture_output=True, text=True, timeout=300,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        self.assertEqual(set(summary), {"combined_score", "valid"})
        self.assertEqual(summary["valid"], 1.0)
        self.assertEqual(summary["combined_score"], metrics["combined_score"])
        for key in ("combined_score", "valid", "feasibility_rate",
                    "mechanism_score", "development_set_f1",
                    "development_correct_refusal_rate", "robustness_score",
                    "per_world"):
            self.assertIn(key, metrics)
        self.assertEqual(metrics["valid"], 1.0)
        # The reference measures 0.600 on the level-3 default (known_best.md);
        # require the documented neighbourhood, not the exact float.
        self.assertGreaterEqual(metrics["combined_score"], 0.5)



class ReviewContractRegressions(unittest.TestCase):
    def test_invalid_rows_are_not_discovery_attempts(self):
        ev = _load(ROOT / "benchmarks/Engineering/DistributionNetworkTopology/verification/evaluator.py", "review_invalid")
        result = ev.evaluate(lambda *args: {})
        self.assertEqual(result["valid"], 0.0)
        self.assertEqual(result["combined_score"], 0.0)
        self.assertEqual(result["development_discovery_attempt_count"], 0)
        self.assertEqual(result["development_discovery_coverage"], 0.0)
        self.assertEqual(result["heldout_discovery_attempt_count"], 0)
        self.assertEqual(result["heldout_discovery_coverage"], 0.0)
        self.assertGreater(result["heldout_unsupported_world_count"], 0)
        self.assertEqual(result["heldout_false_discovery_count"], 0)

    def test_runner_routes_through_trusted_harness_without_importing_candidate(self):
        import contextlib
        import io
        import tempfile
        import subprocess
        runner = _load(ROOT / "benchmarks/Engineering/DistributionNetworkTopology/frontier_eval/run_eval.py", "review_runner")
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate.py"
            candidate.write_text("raise AssertionError('must never import here')\n")
            metrics = Path(tmp) / "metrics.json"
            completed = subprocess.CompletedProcess([], 0, '{"combined_score": 0.2, "valid": 1.0}', '')
            with patch.object(sys, "argv", ["run_eval.py", "--candidate", str(candidate), "--metrics-out", str(metrics)]), patch.object(runner.subprocess, "run", return_value=completed) as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(), 0)
            command = run.call_args.args[0]
            self.assertEqual(command[1:4], ["-m", "sle", "eval"])
            self.assertEqual(command[command.index("--task") + 1], "WaterDistribution/DistributionNetworkTopology")
            self.assertEqual(command[command.index("--candidate") + 1], str(candidate.resolve()))
            self.assertEqual(json.loads(metrics.read_text())["combined_score"], 0.2)


class TomographyScienceRegressions(unittest.TestCase):
    def setUp(self):
        self.ev = _load(ROOT / "benchmarks/Engineering/DistributionNetworkTopology/verification/evaluator.py", "review_tomography")

    def test_every_alias_is_structurally_unidentifiable(self):
        for seed in range(30):
            world = self.ev._world((seed, "alias"))
            self.assertFalse(self.ev._identifiable(world["broken"], 4))
        self.assertTrue(self.ev._identifiable(["h00"], 4))

    def test_bit_signatures_match_route_incidence(self):
        from itertools import combinations
        from collections import Counter
        subsets = [subset for size in (1, 2) for subset in combinations(self.ev.PIPE_IDS, size)]
        counts = Counter(self.ev._signature(subset) for subset in subsets)
        for subset in subsets:
            expected = sum(1 << i for i, route in enumerate(self.ev.ROUTES) if set(subset) & set(route))
            self.assertEqual(self.ev._signature_bits(subset), expected)
            self.assertEqual(self.ev._identifiable(subset, 2), counts[self.ev._signature(subset)] == 1)

    def test_confident_wrong_set_does_not_get_perfect_calibration(self):
        row = self.ev._evaluate_world(lambda *args: {"broken_pipes": ["s11"], "abstain": False, "confidence": 1.0}, (34011, "supported"), "development", 0)
        self.assertTrue(row["valid"])
        self.assertEqual(row["set_f1"], 0.0)
        self.assertEqual(row["confidence_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
