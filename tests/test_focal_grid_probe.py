"""The advertised four-dimensional alternative remains below the focal witness."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / 'benchmarks/EarthScience/FocalMechanismStressInversion'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def reference_metrics():
    oracle = load(TASK / 'verification/evaluator.py', 'focal_grid_reference_oracle')
    reference = load(TASK / 'verification/reference_solver.py', 'focal_grid_reference')
    return oracle.evaluate(reference.infer_stress_orientation)


@pytest.mark.parametrize('grid,rounds', [((12,8,12,6),0), ((24,12,24,9),3)])
def test_four_dimensional_grid_cannot_match_reference(reference_metrics, grid, rounds):
    oracle = load(TASK / 'verification/evaluator.py', 'focal_grid_oracle')
    probe = load(ROOT / '.research/pr20_focal_grid_probe.py', 'focal_grid_probe')
    probe.GRID = grid
    probe.LOCAL_ROUNDS = rounds
    result = oracle.evaluate(probe.infer_stress_orientation)
    assert result['valid'] == 1.0
    assert result['heldout_feasibility_rate'] == 1.0
    for key in ('combined_score', 'robustness_score'):
        assert reference_metrics[key] > result[key] + 0.15
        assert result[key] < .75 * reference_metrics[key]
