import importlib.util
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/Chemistry/CrystalStructurePolymorphSearch"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_baseline_and_reference_are_deterministic_anchors():
    evaluator = _load(TASK / "verification/evaluator.py", "csp_eval_anchor")
    baseline = _load(TASK / "solution.py", "csp_baseline")
    reference = _load(TASK / "verification/reference_multistart.py", "csp_reference")
    first = evaluator.evaluate(baseline.search_crystals)
    second = evaluator.evaluate(baseline.search_crystals)
    witness = evaluator.evaluate(reference.search_crystals)
    assert first == second
    assert first["valid"] == 1.0
    assert first["combined_score"] == 0.0
    assert witness["valid"] == 1.0
    assert abs(witness["combined_score"] - 1.0) < 1e-12
    assert abs(witness["heldout_policy_score"] - 1.0) < 1e-12


def test_periodic_energy_is_common_translation_invariant():
    evaluator = _load(TASK / "verification/evaluator.py", "csp_eval_periodic")
    world = evaluator.WORLDS[0]
    seed = evaluator._baseline_seed(world, 0)
    lengths = np.asarray(seed["cell_lengths"])
    coords = np.asarray(seed["fractional_coordinates"])
    shifted = (coords + np.asarray([0.231, 0.417, 0.119])) % 1.0
    assert abs(evaluator._enthalpy(world, lengths, coords) -
               evaluator._enthalpy(world, lengths, shifted)) < 1e-10


def test_malformed_candidates_score_zero_without_crashing():
    evaluator = _load(TASK / "verification/evaluator.py", "csp_eval_bad")

    def empty(_problem, _callback):
        return {}

    def collision(problem, callback):
        n = problem["atom_count"]
        try:
            callback({"cell_lengths": [2.2, 2.2, 2.2],
                      "fractional_coordinates": [[0.0, 0.0, 0.0]] * n})
        except ValueError:
            pass
        return {"candidate_ids": ["invented-a", "invented-b", "invented-c"]}

    def overrun(problem, callback):
        seed = _load(TASK / "solution.py", "csp_bad_seed")._seed(problem, 0)
        rows = []
        for _ in range(evaluator.CALL_BUDGET + 1):
            try:
                rows.append(callback(seed))
            except ValueError:
                pass
        return {"candidate_ids": [row["candidate_id"] for row in rows[:3]]}

    for candidate in (empty, collision, overrun):
        result = evaluator.evaluate(candidate)
        assert result["valid"] == 0.0
        assert result["combined_score"] == 0.0

