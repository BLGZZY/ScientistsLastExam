import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/Engineering/RobustACTransmissionSwitching"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_baseline_and_reference_are_deterministic_anchors():
    evaluator = _load(TASK / "verification/evaluator.py", "rats_eval_anchor")
    baseline = _load(TASK / "solution.py", "rats_baseline")
    reference = _load(TASK / "verification/reference_screen_refine.py", "rats_reference")
    first = evaluator.evaluate(baseline.optimize_switching)
    second = evaluator.evaluate(baseline.optimize_switching)
    witness = evaluator.evaluate(reference.optimize_switching)
    assert first == second
    assert first["valid"] == 1.0
    assert first["feasibility_rate"] == 1.0
    assert first["combined_score"] == 0.0
    assert witness["valid"] == 1.0
    assert witness["feasibility_rate"] == 1.0
    assert abs(witness["combined_score"] - 1.0) < 1e-12


def test_switching_changes_ac_feasibility_at_high_participation():
    evaluator = _load(TASK / "verification/evaluator.py", "rats_eval_mechanism")
    world = evaluator.WORLDS[0]
    closed = evaluator._evaluate_plan(
        world, {"open_lines": [], "generator_1_share": 0.85}
    )
    switched = evaluator._evaluate_plan(
        world, {"open_lines": ["l12"], "generator_1_share": 0.85}
    )
    assert not closed["feasible"]
    assert switched["feasible"]
    assert switched["worst_thermal_loading"] <= 1.0


def test_malformed_candidates_score_zero_without_crashing():
    evaluator = _load(TASK / "verification/evaluator.py", "rats_eval_bad")

    def empty(_problem, _callback):
        return {}

    def bad_query(_problem, callback):
        try:
            callback({"open_lines": ["fixed-or-unknown"], "generator_1_share": 0.5})
        except ValueError:
            pass
        return {"plan_id": "invented"}

    def overrun(_problem, callback):
        last = None
        for _ in range(evaluator.CALL_BUDGET + 1):
            try:
                last = callback({"open_lines": [], "generator_1_share": 0.4})
            except ValueError:
                pass
        return {"plan_id": last["plan_id"]}

    for candidate in (empty, bad_query, overrun):
        result = evaluator.evaluate(candidate)
        assert result["valid"] == 0.0
        assert result["combined_score"] == 0.0

