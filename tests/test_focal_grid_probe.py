"""Geometry and public-input validity, separate from scientific admission.

The old inherited-gate separation assertions hid a strong grid family. The
explicit admission audit in .research/pr74_check_admission.py retains those
separation requirements and reports failure; passing this module cannot admit it.
"""
import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/EarthScience/FocalMechanismStressInversion"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def modules():
    return (load(TASK / "verification/evaluator.py", "geometry_oracle"),
            load(TASK / "verification/reference_solver.py", "geometry_reference"),
            load(ROOT / ".research/pr74_grid_probe.py", "independent_probe"))


def test_independent_tensor_and_signed_shear_match_oracle(modules):
    oracle, reference, probe = modules
    rng = np.random.default_rng(871)
    points = np.column_stack([rng.uniform(0, 360, 20), rng.uniform(-90, 90, 20),
                              rng.uniform(0, 180, 20), rng.uniform(.05, .95, 20)])
    tensors, one, three = probe.tensors_from_points(points)
    for i, tensor in enumerate(tensors):
        np.testing.assert_allclose(tensor, oracle._stress_tensor(one[i], three[i], points[i, 3]), atol=1e-14)
    np.testing.assert_allclose(tensors, reference._stress_frames(points)[0], atol=1e-14)
    world = oracle._world((33011, "supported"))
    events = oracle.problem_statement(world)["events"]
    normals, slips = probe.read_planes(events)
    angles = probe.angular_errors(tensors, normals, slips)
    np.testing.assert_allclose(angles, reference._angles(tensors, normals, slips), atol=1e-10)
    for i in range(10):
        shear = oracle._shear(tensors[i], normals[i, 0])
        angle = np.degrees(np.arccos(np.clip(shear @ slips[i, 0] / np.linalg.norm(shear), -1, 1)))
        assert angles[i, i, 0] == pytest.approx(angle)
    np.testing.assert_allclose(angles + probe.angular_errors(-tensors, normals, slips), 180., atol=1e-10)


def test_zero_noise_paired_projection_preserves_labeled_planes(modules):
    oracle, reference, probe = modules
    world = oracle._world((33011, "supported"))
    events = [{"id": i, "plane_a": oracle._plane_from_normal_slip(n, s),
               "plane_b": oracle._plane_from_normal_slip(s, n)}
              for i, (n, s) in enumerate(world["events"])]
    moments = probe.moment_mean(events)
    for project in (probe.denoised_planes, reference._paired_planes):
        normals, slips = project(moments, events)
        for i, (n, s) in enumerate(world["events"]):
            assert abs(normals[i, 0] @ n) == pytest.approx(1.)
            assert abs(normals[i, 1] @ s) == pytest.approx(1.)
            for j in (0, 1):
                np.testing.assert_allclose(np.outer(normals[i,j], slips[i,j]) + np.outer(slips[i,j], normals[i,j]), moments[i], atol=1e-12)


@pytest.mark.parametrize("method", ["reference", "paired_probe"])
def test_public_event_order_and_plane_swap_equivariance(modules, method):
    oracle, reference, probe = modules
    probe.PAIRED, probe.QUERY_POLICY = True, "ambiguous"
    solve = reference.infer_stress_orientation if method == "reference" else probe.infer_stress_orientation
    world = oracle._world((33011, "supported"))
    original = oracle.problem_statement(world)
    def run(reverse, swap):
        problem = copy.deepcopy(original)
        if reverse:
            problem["events"].reverse()
        if swap:
            for event in problem["events"]:
                event["plane_a"], event["plane_b"] = event["plane_b"], event["plane_a"]
        observatory = oracle._Observatory(copy.deepcopy(world))
        queried = []
        def callback(event_id):
            queried.append(event_id)
            event = dict(observatory.reanalyze(event_id))
            if swap:
                event["plane_a"], event["plane_b"] = event["plane_b"], event["plane_a"]
            return event
        result = solve(problem, callback, 16)
        assert not result["abstain"]
        assert len(queried) == len(set(queried)) == 16
        return result, queried
    first, calls = run(False, False)
    for reverse, swap in ((True, False), (False, True)):
        result, new_calls = run(reverse, swap)
        assert new_calls == calls
        for key in ("R", "sigma1", "sigma3"):
            np.testing.assert_allclose(result[key], first[key], atol=1e-5)
        expected = list(reversed(first["plane_assignments"])) if reverse else [1-x for x in first["plane_assignments"]]
        assert result["plane_assignments"] == expected


def test_grid_gate_is_independent_and_produces_valid_artifacts(modules):
    oracle, reference, probe = modules
    assert probe.THRESHOLD_DEG != reference.MEAN_MISFIT_DEG
    for spec in oracle._BASE_DEVELOPMENT_SPECS:
        row = oracle._evaluate_world(probe.infer_stress_orientation, spec, "development", 0)
        assert row["valid"], spec
    # Near-zero negative azimuth previously rounded modulo 360 to exactly 360.
    probe.GRID_SHAPE = (8, 6, 9, 4)
    probe.THRESHOLD_DEG = float("inf")
    row = oracle._evaluate_world(probe.infer_stress_orientation, oracle._BASE_DEVELOPMENT_SPECS[7], "development", 7)
    assert row["valid"]
