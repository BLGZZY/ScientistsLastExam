"""Regression contracts for FocalMechanismStressInversion."""
from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path
import numpy as np
from sle.registry import find_task
ROOT = Path(__file__).resolve().parents[1]
EARTH = ROOT / 'benchmarks' / 'EarthScience'
TASKS = {'Geophysics/FocalMechanismStressInversion': ('FocalMechanismStressInversion', 'infer_stress_orientation', 'discovery')}

def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

class NewEarthSciencePackageTests(unittest.TestCase):

    def test_inventory_has_one_discovery_task(self):
        roles = []
        for (task_id, (_, _, role)) in TASKS.items():
            spec = find_task(task_id, include_uncertified=True)
            self.assertEqual(spec.discipline, 'EarthScience')
            self.assertEqual(spec.metadata['scientific_role'], role)
            roles.append(role)
        self.assertEqual(roles.count('discovery'), 1)

    def test_baselines_are_valid_zero_and_deterministic(self):
        for (task_id, (directory, entrypoint, _)) in TASKS.items():
            evaluator = _load(EARTH / directory / 'verification' / 'evaluator.py', 'new_earth_evaluator_' + directory)
            baseline = _load(EARTH / directory / 'solution.py', 'new_earth_baseline_' + directory)
            first = evaluator.evaluate(getattr(baseline, entrypoint))
            second = evaluator.evaluate(getattr(baseline, entrypoint))
            self.assertEqual(first['valid'], 1.0, task_id)
            self.assertEqual(first['combined_score'], 0.0, task_id)
            self.assertEqual(json.dumps(first, sort_keys=True, default=str), json.dumps(second, sort_keys=True, default=str), task_id)

    def test_truth_blind_references_leave_measurable_headroom(self):
        for (task_id, (directory, entrypoint, role)) in TASKS.items():
            evaluator = _load(EARTH / directory / 'verification' / 'evaluator.py', 'new_earth_reference_evaluator_' + directory)
            reference = _load(EARTH / directory / 'verification' / 'reference_solver.py', 'new_earth_reference_' + directory)
            result = evaluator.evaluate(getattr(reference, entrypoint))
            self.assertEqual(result['valid'], 1.0, task_id)
            self.assertGreater(result['combined_score'], 0.05, task_id)
            self.assertGreater(result['combined_score'], 0.3, task_id)
            self.assertLess(result['combined_score'], 0.8, task_id)

    def test_bad_candidates_score_invalid_without_crashing_evaluator(self):

        def raises(*args, **kwargs):
            del args, kwargs
            raise RuntimeError('candidate failure')

        def empty(*args, **kwargs):
            del args, kwargs
            return {}

        def wrong_type(*args, **kwargs):
            del args, kwargs
            return 'not a scientific artifact'
        for (task_id, (directory, _, _)) in TASKS.items():
            evaluator = _load(EARTH / directory / 'verification' / 'evaluator.py', 'new_earth_bad_candidate_' + directory)
            for candidate in (raises, empty, wrong_type):
                result = evaluator.evaluate(candidate)
                self.assertEqual(result['valid'], 0.0, task_id)
                self.assertEqual(result['combined_score'], 0.0, task_id)
if __name__ == '__main__':
    unittest.main()
