from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

import numpy as np

from sle.registry import find_task


ROOT = Path(__file__).resolve().parents[1]
EARTH = ROOT / "benchmarks" / "EarthScience"
TASKS = {
    "WavePropagation/ActiveFullWaveformInversion":
        ("ActiveFullWaveformInversion", "invert_velocity_model", "discovery"),
    "Hydrology/GroundwaterRemediationDesign":
        ("GroundwaterRemediationDesign", "design_remediation", "optimization"),
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class NewEarthSciencePackageTests(unittest.TestCase):
    def test_inventory_has_one_discovery_and_one_optimization_task(self):
        roles = []
        for task_id, (_, _, role) in TASKS.items():
            spec = find_task(task_id, include_uncertified=True)
            self.assertEqual(spec.discipline, "EarthScience")
            self.assertEqual(spec.metadata["scientific_role"], role)
            roles.append(role)
        self.assertEqual(roles.count("discovery"), 1)
        self.assertEqual(roles.count("optimization"), 1)

    def test_baselines_are_valid_zero_and_deterministic(self):
        for task_id, (directory, entrypoint, _) in TASKS.items():
            evaluator = _load(EARTH / directory / "verification" / "evaluator.py",
                              "new_earth_evaluator_" + directory)
            baseline = _load(EARTH / directory / "solution.py",
                             "new_earth_baseline_" + directory)
            first = evaluator.evaluate(getattr(baseline, entrypoint))
            second = evaluator.evaluate(getattr(baseline, entrypoint))
            self.assertEqual(first["valid"], 1.0, task_id)
            self.assertLessEqual(abs(first["combined_score"]), 0.01, task_id)
            self.assertEqual(json.dumps(first, sort_keys=True, default=str),
                             json.dumps(second, sort_keys=True, default=str), task_id)

    def test_truth_blind_references_leave_measurable_headroom(self):
        for task_id, (directory, entrypoint, role) in TASKS.items():
            evaluator = _load(EARTH / directory / "verification" / "evaluator.py",
                              "new_earth_reference_evaluator_" + directory)
            reference = _load(EARTH / directory / "verification" / "reference_solver.py",
                              "new_earth_reference_" + directory)
            result = evaluator.evaluate(getattr(reference, entrypoint))
            self.assertEqual(result["valid"], 1.0, task_id)
            self.assertGreater(result["combined_score"], 0.05, task_id)
            if role == "optimization":
                # One is a reproducible search anchor, not a score ceiling. Keep
                # the complete witness: do not discard valid archive entries to
                # meet an arbitrary reference-score cutoff.
                self.assertGreater(result["development_exact_hypervolume"], 0.0, task_id)

    def test_bad_candidates_score_invalid_without_crashing_evaluator(self):
        def raises(*args, **kwargs):
            del args, kwargs
            raise RuntimeError("candidate failure")

        def empty(*args, **kwargs):
            del args, kwargs
            return {}

        def wrong_type(*args, **kwargs):
            del args, kwargs
            return "not a scientific artifact"

        for task_id, (directory, _, _) in TASKS.items():
            evaluator = _load(EARTH / directory / "verification" / "evaluator.py",
                              "new_earth_bad_candidate_" + directory)
            for candidate in (raises, empty, wrong_type):
                result = evaluator.evaluate(candidate)
                self.assertEqual(result["valid"], 0.0, task_id)
                self.assertEqual(result["combined_score"], 0.0, task_id)


class NewEarthScienceInvariantTests(unittest.TestCase):
    def test_fixed_grid_metrics_preserve_units_and_reject_broadcasting(self):
        fwi = _load(EARTH / "ActiveFullWaveformInversion" / "verification" / "evaluator.py",
                    "new_earth_numpy_fwi_metric")
        zeros = np.zeros((fwi.N_TIME, len(fwi.RECEIVER_INDICES)))
        self.assertEqual(fwi._waveform_relative_l2(zeros, zeros), 0.0)

        self.assertAlmostEqual(fwi._waveform_relative_l2(2 * np.ones_like(zeros),
                                                        np.ones_like(zeros)), 1.0)
        with self.assertRaises(ValueError):
            fwi._waveform_relative_l2(zeros[:, :1], zeros)

    def test_difficulty_ladders_change_scientific_regimes(self):
        fwi = _load(EARTH / "ActiveFullWaveformInversion" / "verification" / "evaluator.py",
                    "new_earth_fwi_ladder")
        self.assertLess(fwi._difficulty_profile(1)["noise_multiplier"],
                        fwi._difficulty_profile(3)["noise_multiplier"])
        fwi.DIFFICULTY = 1
        easy_fwi = fwi._world(fwi.DEVELOPMENT_SPECS[0])
        fwi.DIFFICULTY = 3
        hard_fwi = fwi._world(fwi.DEVELOPMENT_SPECS[0])
        self.assertGreater(hard_fwi["noise"], easy_fwi["noise"])
        self.assertFalse(np.array_equal(hard_fwi["velocity"], easy_fwi["velocity"]))

        groundwater = _load(
            EARTH / "GroundwaterRemediationDesign" / "verification" / "evaluator.py",
            "new_earth_groundwater_ladder",
        )
        groundwater.DIFFICULTY = 1
        easy_groundwater = groundwater._public_problem(groundwater.DEVELOPMENT_SPECS[0])
        groundwater.DIFFICULTY = 3
        hard_groundwater = groundwater._public_problem(groundwater.DEVELOPMENT_SPECS[0])
        self.assertLess(hard_groundwater["concentration_limit_kg_m3"],
                        easy_groundwater["concentration_limit_kg_m3"])

    def test_fwi_exact_model_has_unit_structure_and_waveform_scores(self):
        evaluator = _load(EARTH / "ActiveFullWaveformInversion" / "verification" / "evaluator.py",
                          "new_earth_fwi_invariant")
        world = evaluator._world(evaluator.DEVELOPMENT_SPECS[0])
        model, waveform, mechanism = evaluator._supported_scores(world, world["velocity"])
        self.assertAlmostEqual(model, 1.0, places=10)
        self.assertAlmostEqual(waveform, 1.0, places=10)
        self.assertAlmostEqual(mechanism, 1.0, places=10)

    def test_groundwater_reference_beats_baseline_and_is_shift_feasible(self):
        evaluator = _load(EARTH / "GroundwaterRemediationDesign" / "verification" / "evaluator.py",
                          "new_earth_groundwater_invariant")
        for spec in evaluator.DEVELOPMENT_SPECS:
            problem = evaluator._public_problem(spec)
            baseline, _ = evaluator._hypervolume(problem, evaluator._baseline_archive(problem))
            reference, _ = evaluator._hypervolume(problem, evaluator._reference_archive(problem))
            self.assertGreater(reference, baseline)
            for shift in evaluator._stress_shifts():
                shifted, _ = evaluator._hypervolume(problem, evaluator._reference_archive(problem), shift)
                self.assertGreater(shifted, 0.0)

    def test_groundwater_exact_world_differs_from_public_proxy(self):
        evaluator = _load(EARTH / "GroundwaterRemediationDesign" / "verification" / "evaluator.py",
                          "new_earth_groundwater_proxy_exact")
        spec = evaluator.DEVELOPMENT_SPECS[0]
        problem = evaluator._public_problem(spec)
        plans = evaluator._reference_archive(problem)
        proxy, _ = evaluator._hypervolume(problem, plans)
        exact, _ = evaluator._hypervolume(problem, plans, evaluator._exact_shift(spec))
        self.assertNotAlmostEqual(proxy, exact, places=10)

    def test_optimization_reference_normalization_is_uncapped(self):
        evaluator = _load(EARTH / "GroundwaterRemediationDesign" / "verification" / "evaluator.py",
                          "new_earth_uncapped_GroundwaterRemediationDesign")
        self.assertAlmostEqual(evaluator._normalize(1.0, 0.0, 1.0), 1.0)
        self.assertGreater(evaluator._normalize(1.5, 0.0, 1.0), 1.0)
        self.assertEqual(evaluator._normalize(-1.0, 0.0, 1.0), 0.0)


if __name__ == "__main__":
    unittest.main()
