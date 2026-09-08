"""Pinned package contracts for the surviving 2026-09 earth candidate tasks.

The 2026-09-07 internal difficulty audit withdrew ChronologyAssimilation,
IceObservationNetworkDesign and MineralMixtureXRD from this PR; their pinned
invariants were removed with them (see the git history and
.research/pr9_frontier_eng_overlap_2026-09-06.md). What remains are the
repo-wide baseline/reference/bad-candidate contracts for the two retained
packages. Tests load evaluators directly; sandbox-dependent behaviour is out
of scope here.
"""


from __future__ import annotations


import importlib.util


import json


import unittest


from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


TASKS = {'WavePropagation/ActiveFullWaveformInversion':
         ('benchmarks/EarthScience/ActiveFullWaveformInversion', 'invert_velocity_model'),
         'Geophysics/FocalMechanismStressInversion':
         ('benchmarks/EarthScience/FocalMechanismStressInversion', 'infer_stress_orientation')}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EarthPackageContractTests(unittest.TestCase):
    def test_baselines_valid_zero_and_deterministic(self):
        for task_id, (directory, entrypoint) in TASKS.items():
            evaluator = _load(ROOT / directory / "verification" / "evaluator.py",
                              "r4_evaluator_" + entrypoint)
            baseline = _load(ROOT / directory / "solution.py",
                             "r4_baseline_" + entrypoint)
            first = evaluator.evaluate(getattr(baseline, entrypoint))
            second = evaluator.evaluate(getattr(baseline, entrypoint))
            self.assertEqual(first["valid"], 1.0, task_id)
            self.assertEqual(first["combined_score"], 0.0, task_id)
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


if __name__ == "__main__":
    unittest.main()
