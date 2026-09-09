"""Numerical correctness and spatial-search regressions for PR20 FWI."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/EarthScience/ActiveFullWaveformInversion"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_batched_forward_and_tangent_match_independent_oracle():
    oracle = load(TASK / "verification/evaluator.py", "tangent_oracle")
    reference = load(TASK / "verification/reference_solver.py", "tangent_reference")
    rng = np.random.default_rng(823)
    velocity = oracle._background() + rng.uniform(-200.0, 200.0, oracle.GRID_SHAPE)
    sources = [3, 15, 28]
    model = reference._Acoustic(oracle.GRID_SHAPE, oracle.SPACING_M,
                               np.arange(oracle.N_TIME) * oracle.DT_S, sources,
                               oracle.RECEIVER_X_M)
    expected = np.asarray([oracle.simulate_waveforms(velocity, s) for s in sources])
    np.testing.assert_allclose(model.forward(velocity), expected, atol=1e-12, rtol=1e-12)
    # Include dense random and boundary-localized directions; the latter catches
    # mistakes in the damped stencil's boundary and source-injection derivatives.
    directions = rng.normal(size=(*oracle.GRID_SHAPE, 3))
    directions[:, :, 2] = 0.0
    directions[1:4, 2:5, 2] = 1.0
    prediction, jacobian = model.jacobian(velocity, directions.reshape((-1, 3)))
    np.testing.assert_allclose(prediction, expected, atol=1e-12, rtol=1e-12)
    step = 0.01
    for i in range(3):
        plus = np.asarray([oracle.simulate_waveforms(velocity + step * directions[:, :, i], s)
                           for s in sources])
        minus = np.asarray([oracle.simulate_waveforms(velocity - step * directions[:, :, i], s)
                            for s in sources])
        numerical = (plus - minus) / (2 * step)
        relative_error = np.linalg.norm(jacobian[:, :, :, i] - numerical) / np.linalg.norm(numerical)
        assert relative_error < 1e-6


def test_spatial_probe_propagation_matches_oracle():
    oracle = load(TASK / "verification/evaluator.py", "spatial_probe_oracle")
    probe = load(ROOT / ".research/pr20_fwi_spatial_probe.py", "spatial_probe_forward")
    models = np.asarray([oracle._background(), oracle._world(oracle.DEVELOPMENT_SPECS[0])["velocity"]])
    sources = [3, 15, 28]
    expected = np.asarray([[oracle.simulate_waveforms(v, s) for s in sources] for v in models])
    actual = probe.simulate(models, sources, oracle.SPACING_M,
                            np.arange(oracle.N_TIME) * oracle.DT_S, oracle.RECEIVER_X_M)
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=1e-12)


def test_paired_velocity_controls_have_independent_reproducible_noise():
    oracle = load(TASK / "verification/evaluator.py", "independent_noise_oracle")
    seed = 41023
    worlds = [oracle._world((seed, kind, 2))
              for kind in ("supported", "structured_attenuation")]
    np.testing.assert_array_equal(worlds[0]["velocity"], worlds[1]["velocity"])
    standardized = []
    for world, attenuation in zip(worlds, (0.0, 1.8)):
        a = oracle._Acquisition(world).acquire(15)
        b = oracle._Acquisition(world).acquire(15)
        np.testing.assert_array_equal(a["pressure"], b["pressure"])
        clean = oracle.simulate_waveforms(world["velocity"], 15, 12.0, attenuation)
        standardized.append((a["pressure"] - clean).ravel() / a["noise_std"])
    # The previous implementation reused exactly the same normal draws.
    assert abs(np.corrcoef(standardized)[0, 1]) < 0.10
    assert not np.allclose(standardized[0], standardized[1])


@pytest.fixture(scope="module")
def reference_metrics():
    oracle = load(TASK / "verification/evaluator.py", "spatial_regression_oracle")
    reference = load(TASK / "verification/reference_solver.py", "spatial_regression_reference")
    return oracle.evaluate(reference.invert_velocity_model)


@pytest.mark.parametrize("refine,threshold,lenses", [(False, 0.12, 1), (False, 0.24, 1), (True, 0.20, 1), (False, 0.20, 2), (False, 0.20, 3)])
def test_spatial_search_is_below_reference_on_both_splits(reference_metrics, refine, threshold, lenses):
    oracle = load(TASK / "verification/evaluator.py", "spatial_comparison_oracle")
    probe = load(ROOT / ".research/pr20_fwi_spatial_probe.py", "spatial_comparison_probe")
    probe.REFINE = refine
    probe.THRESHOLD = threshold
    probe.LENSES = lenses
    result = oracle.evaluate(probe.invert_velocity_model)
    assert result["valid"] == 1.0
    # Spatial degrees of freedom are essential here: the earlier regression only
    # swept a fixed lens's amplitude. Require a margin on BOTH evaluation splits.
    for metric in ("combined_score", "robustness_score"):
        assert reference_metrics[metric] > result[metric] + 0.15
        assert result[metric] < 0.7 * reference_metrics[metric]
