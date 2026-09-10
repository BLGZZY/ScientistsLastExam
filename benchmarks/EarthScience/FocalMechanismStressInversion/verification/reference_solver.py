"""Public-input stress inversion with paired-mechanism averaging and active re-analysis.

Averaging double-couple tensors uses both noisy nodal-plane observations without
assuming either one is the fault. A four-parameter normalized-shear fit then selects
planes jointly with stress; paid observations target ambiguous plane choices. This is
an executable method reference, not proof of difficulty or independent certification.
"""
from __future__ import annotations

import itertools

import numpy as np
from scipy.optimize import minimize

GRID_SHAPE = (8, 6, 9, 4)
MULTISTART_COUNT = 3
# Chosen on development diagnostics; probes use independent gates and report sweeps.
MEAN_MISFIT_DEG = 20.0


def _normal_from_plane(strike, dip):
    tr, dp = np.deg2rad([strike, dip])
    return np.array([-np.sin(dp) * np.sin(tr), -np.sin(dp) * np.cos(tr), np.cos(dp)])


def _slip_from_plane(strike, dip, rake):
    tr, dp, lam = np.deg2rad([strike, dip, rake])
    return (np.cos(lam) * np.array([np.cos(tr), -np.sin(tr), 0.0])
            + np.sin(lam) * np.array([np.cos(dp) * np.sin(tr),
                                      np.cos(dp) * np.cos(tr), np.sin(dp)]))


def _planes(events):
    normals = np.array([[_normal_from_plane(*event[key][:2])
                         for key in ("plane_a", "plane_b")] for event in events])
    slips = np.array([[_slip_from_plane(*event[key])
                       for key in ("plane_a", "plane_b")] for event in events])
    return normals, slips


def _moment_observations(events):
    normals, slips = _planes(events)
    moments = (normals[:, :, :, None] * slips[:, :, None, :]
               + slips[:, :, :, None] * normals[:, :, None, :])
    return moments.mean(axis=1)


def _paired_planes(moments, events):
    # Project the mean symmetric moment tensor onto its double-couple directions.
    _, vectors = np.linalg.eigh(moments)
    normal = (vectors[:, :, 2] + vectors[:, :, 0]) / np.sqrt(2.0)
    slip = (vectors[:, :, 2] - vectors[:, :, 0]) / np.sqrt(2.0)
    observed_normals, _ = _planes(events)
    swap = (np.abs(np.sum(normal * observed_normals[:, 0], axis=1))
            < np.abs(np.sum(slip * observed_normals[:, 0], axis=1)))
    normal, slip = (np.where(swap[:, None], slip, normal),
                    np.where(swap[:, None], normal, slip))
    normals = np.stack([normal, slip], axis=1)
    slips = np.stack([slip, normal], axis=1)
    # A plane normal and its slip must flip together to preserve the moment tensor.
    signs = np.where(np.sum(normals * observed_normals, axis=2) >= 0.0, 1.0, -1.0)
    return normals * signs[:, :, None], slips * signs[:, :, None]


def _stress_frames(parameters):
    parameters = np.atleast_2d(parameters)
    trend, plunge, rotation = np.deg2rad(parameters[:, :3]).T
    ratio = parameters[:, 3]
    one = np.stack([np.cos(plunge) * np.cos(trend),
                    np.cos(plunge) * np.sin(trend), np.sin(plunge)], axis=1)
    tangent = np.stack([-np.sin(trend), np.cos(trend), np.zeros_like(trend)], axis=1)
    other = np.cross(one, tangent)
    three = np.cos(rotation)[:, None] * tangent + np.sin(rotation)[:, None] * other
    two = np.cross(three, one)
    tensors = (one[:, :, None] * one[:, None, :]
               + (1.0 - ratio[:, None, None]) * two[:, :, None] * two[:, None, :])
    return tensors, one, three


def _angles(tensors, normals, slips):
    traction = np.einsum("gij,epj->gepi", tensors, normals)
    shear = traction - normals[None] * np.sum(traction * normals[None], axis=-1)[..., None]
    magnitude = np.linalg.norm(shear, axis=-1)
    cosine = np.sum(shear * slips[None], axis=-1) / np.maximum(magnitude, 1e-12)
    # Slip polarity is observable. abs(cosine) would also admit reversed stress.
    return np.rad2deg(np.arccos(np.clip(cosine, -1.0, 1.0)))


def _parameter_grid(shape):
    return np.array(list(itertools.product(
        np.linspace(0.0, 360.0, shape[0], endpoint=False),
        np.linspace(0.0, 90.0, shape[1]),
        np.linspace(0.0, 180.0, shape[2], endpoint=False),
        np.linspace(0.05, 0.95, shape[3]))))


def _fit_stress(normals, slips, weights, grid, previous=None, continuous=True):
    tensors, _, _ = _stress_frames(grid)
    objectives = []
    for begin in range(0, len(grid), 256):
        angles = _angles(tensors[begin:begin + 256], normals, slips)
        objectives.extend(np.mean(np.min(angles, axis=2) ** 2 * weights[None], axis=1))
    order = np.argsort(objectives, kind="stable")
    parameters = grid[order[0]].copy()
    if continuous:
        def objective(candidate):
            angles = _angles(_stress_frames(candidate)[0], normals, slips)[0]
            return float(np.mean(np.min(angles, axis=1) ** 2 * weights))

        starts = [grid[i] for i in order[:MULTISTART_COUNT]]
        if previous is not None:
            starts.insert(0, previous)
        best = objective(parameters)
        for start in starts:
            result = minimize(objective, start, method="L-BFGS-B",
                              bounds=[(None, None), (-90.0, 90.0), (None, None), (0.0, 1.0)],
                              options={"maxiter": 180, "ftol": 1e-11})
            # Keep the best finite candidate, even if an iteration limit was reached.
            if np.isfinite(result.fun) and result.fun < best:
                parameters, best = result.x, float(result.fun)
    angles = _angles(_stress_frames(parameters)[0], normals, slips)[0]
    return parameters, angles


def _axis_angles(axis):
    return [float(np.rad2deg(np.arctan2(axis[1], axis[0])) % 360.0) % 360.0,
            float(np.rad2deg(np.arcsin(np.clip(axis[2], -1.0, 1.0))))]


def _solve(problem, reanalyze, budget_units, *, pair_averaging=True,
           continuous=True, weighted=True, query_policy="ambiguous", grid_shape=GRID_SHAPE,
           refusal_threshold=MEAN_MISFIT_DEG):
    input_events = list(problem["events"])
    events = [dict(event) for event in sorted(input_events, key=lambda event: event["id"])]
    coarse_sigma = float(problem["noise_sigma_deg"])
    fine_sigma = float(problem["reanalysis_sigma_deg"])
    moments = _moment_observations(events)
    uncertainty = np.full(len(events), coarse_sigma)
    grid = _parameter_grid(grid_shape)

    def fit(previous=None):
        normals, slips = (_paired_planes(moments, events) if pair_averaging else _planes(events))
        weights = (coarse_sigma / uncertainty) ** 2 if weighted else np.ones(len(events))
        return _fit_stress(normals, slips, weights, grid, previous, continuous)

    parameters, angles = fit()
    count = min(int(budget_units), len(events))
    if query_policy == "first":
        indices = np.arange(count)
    elif query_policy == "worst":
        indices = np.argsort(-np.min(angles, axis=1), kind="stable")[:count]
    elif query_policy == "ambiguous":
        indices = np.argsort(np.abs(angles[:, 0] - angles[:, 1]), kind="stable")[:count]
    else:
        raise ValueError("unknown acquisition policy")
    queried = []
    for index in indices:
        refreshed = dict(reanalyze(events[index]["id"]))
        new_moment = _moment_observations([refreshed])[0]
        precision = 1.0 / coarse_sigma ** 2 + 1.0 / fine_sigma ** 2
        moments[index] = (moments[index] / coarse_sigma ** 2 + new_moment / fine_sigma ** 2) / precision
        uncertainty[index] = precision ** -0.5
        events[index] = refreshed
        queried.append(refreshed["id"])
    if count:
        parameters, angles = fit(parameters)
    mean_residual = float(np.mean(np.min(angles, axis=1)))
    diagnostics = {"mean_residual_deg": mean_residual, "queried_ids": queried,
                   "parameters": parameters.tolist(), "angles_deg": angles.tolist()}
    if mean_residual > refusal_threshold:
        return {"sigma1": None, "sigma3": None, "R": None, "plane_assignments": None,
                "abstain": True, "confidence": 0.1}, diagnostics
    _, one, three = _stress_frames(parameters)
    assignment_by_id = {event["id"]: int(choice)
                        for event, choice in zip(events, np.argmin(angles, axis=1))}
    return {"sigma1": _axis_angles(one[0]), "sigma3": _axis_angles(three[0]),
            "R": float(parameters[3]),
            "plane_assignments": [assignment_by_id[event["id"]] for event in input_events],
            "abstain": False, "confidence": 0.75}, diagnostics


def infer_stress_orientation(problem, reanalyze, budget_units):
    return _solve(problem, reanalyze, budget_units)[0]
