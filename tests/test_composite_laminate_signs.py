"""Independent membrane limits for the public compression-positive load convention.

Uniform 0/45-degree stacks isolate the constitutive calculation; they intentionally
do not satisfy the optimization problem's composition constraints. Expected reserves
come from force balance and stress rotation, not a second copy of the CLT assembly.
"""
import importlib.util
import math
from pathlib import Path

import pytest


VERIFICATION = (Path(__file__).resolve().parents[1] / "benchmarks" / "Engineering"
                / "CompositeLaminateStacking" / "verification")


@pytest.fixture(params=["evaluator", "reference"])
def model(request):
    spec = importlib.util.spec_from_file_location(request.param, VERIFICATION / f"{request.param}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def panel(load):
    return {
        "ply_thickness_m": .001,
        "panel_length_m": 1., "panel_width_m": 1.,
        "load_cases_n_per_m": [load], "moment_cases_n": [[0., 0., 0.]],
        "material": {"e1_pa": 132e9, "e2_pa": 9.2e9, "g12_pa": 4.8e9,
                     "nu12": .29, "xt_pa": 1.45e9, "xc_pa": 1.05e9,
                     "yt_pa": 55e6, "yc_pa": 185e6, "s_pa": 72e6},
    }


@pytest.mark.parametrize("axis", [0, 1])
@pytest.mark.parametrize("compression_sign", [-1, 1])
def test_zero_degree_normal_force_selects_tensile_or_compressive_strength(
        model, axis, compression_sign):
    stress = 10e6
    thickness = 2 * .001
    load = [0., 0., 0.]
    load[axis] = compression_sign * stress * thickness
    problem = panel(load)
    strength_key = ("x" if axis == 0 else "y") + ("c_pa" if compression_sign > 0 else "t_pa")
    expected = problem["material"][strength_key] / stress
    result = model._laminate(problem, [0, 0], return_components=True)
    assert result["first_ply_reserve"] == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("angle", [-45, 45])
@pytest.mark.parametrize("shear_sign", [-1, 1])
def test_signed_shear_retains_its_orientation_in_material_stresses(model, angle, shear_sign):
    shear = shear_sign * 10e6
    thickness = 2 * .001
    problem = panel([0., 0., shear * thickness])
    # Pure global shear rotated by +/-45 degrees gives s1=+/-tau, s2=-s1, t12=0.
    s1 = (1 if angle > 0 else -1) * shear
    material = problem["material"]
    x = material["xt_pa"] if s1 > 0 else material["xc_pa"]
    y = material["yc_pa"] if s1 > 0 else material["yt_pa"]
    expected = 1. / math.sqrt(2. * (s1 / x)**2 + (s1 / y)**2)
    result = model._laminate(problem, [angle, angle], return_components=True)
    assert result["first_ply_reserve"] == pytest.approx(expected, rel=1e-12)
