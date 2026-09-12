"""Deterministic robust AC transmission-switching oracle.

The candidate searches a mixed discrete/continuous preventive policy through a
charged callback.  The trusted side solves the polar AC power-flow equations for
every frozen load/contingency scenario and independently checks engineering limits.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping
from functools import lru_cache

import numpy as np
from scipy.optimize import root


ROBUST_AC_TRANSMISSION_SWITCHING_V1 = True
CALL_BUDGET = 48
MAX_OPEN = 2
SWITCH_COST = 0.20
V_MIN, V_MAX = 0.90, 1.10
SHARE_MIN, SHARE_MAX = 0.25, 0.85

_BASE_BRANCHES = (
    ("l01", 0, 1, 0.020, 0.180, 2.00, False),
    ("l02", 0, 2, 0.015, 0.160, 2.00, True),
    ("l12", 1, 2, 0.012, 0.120, 0.66, True),
    ("l13", 1, 3, 0.020, 0.200, 2.00, True),
    ("l23", 2, 3, 0.010, 0.100, 2.00, True),
    ("l24", 2, 4, 0.020, 0.180, 2.00, True),
    ("l34", 3, 4, 0.012, 0.110, 2.00, True),
    ("l04", 0, 4, 0.025, 0.220, 2.00, True),
)


def _world(name, split, loads, x_scale, cheap_cost, scenarios):
    branches = []
    for line_id, i, j, r, x, rate, switchable in _BASE_BRANCHES:
        branches.append((line_id, i, j, r, x * x_scale, rate, switchable))
    return {
        "name": name,
        "split": split,
        "loads": tuple(float(v) for v in loads),
        "branches": tuple(branches),
        "cheap_cost": tuple(float(v) for v in cheap_cost),
        "scenarios": tuple(scenarios),
    }


WORLDS = (
    _world("d0", "development", (0.22, 0.70, 0.61, 0.51), 0.96, (10.0, 2.0),
           ((0.94, None), (1.04, None), (1.08, "l34"), (1.00, "l24"))),
    _world("d1", "development", (0.27, 0.73, 0.58, 0.54), 1.00, (10.8, 1.8),
           ((0.92, None), (1.05, None), (1.09, "l34"), (1.01, "l24"))),
    _world("d2", "development", (0.24, 0.76, 0.64, 0.48), 1.04, (9.6, 2.2),
           ((0.95, None), (1.03, None), (1.07, "l34"), (1.00, "l24"))),
    _world("d3", "development", (0.29, 0.69, 0.62, 0.52), 0.98, (10.3, 2.0),
           ((0.93, None), (1.06, None), (1.08, "l34"), (1.02, "l24"))),
    _world("h0", "heldout", (0.25, 0.72, 0.66, 0.49), 1.02, (9.9, 2.1),
           ((0.91, None), (1.04, None), (1.10, "l34"), (0.99, "l24"))),
    _world("h1", "heldout", (0.23, 0.78, 0.57, 0.55), 0.94, (10.5, 1.9),
           ((0.94, None), (1.07, None), (1.09, "l34"), (1.01, "l24"))),
)


def _problem(world):
    return {
        "bus_count": 5,
        "slack_bus": 0,
        "participating_generator_bus": 1,
        "base_active_loads_pu": list(world["loads"]),
        "load_power_factor": 0.9524241472,
        "branches": [
            {
                "id": row[0], "from_bus": row[1], "to_bus": row[2],
                "resistance_pu": row[3], "reactance_pu": row[4],
                "thermal_limit_pu": row[5], "switchable": row[6],
            }
            for row in world["branches"]
        ],
        "generator_0_cost": [0.0, 20.0, 7.0],
        "generator_1_cost": [0.0, *world["cheap_cost"]],
        "generator_active_bounds_pu": [[0.0, 3.0], [0.0, 2.5]],
        "generator_reactive_bounds_pu": [[-0.8, 1.5], [-0.8, 1.5]],
        "generator_1_share_bounds": [SHARE_MIN, SHARE_MAX],
        "voltage_bounds_pu": [V_MIN, V_MAX],
        "maximum_open_lines": MAX_OPEN,
        "evaluation_budget_calls": CALL_BUDGET,
        "contingency_count": sum(row[1] is not None for row in world["scenarios"]),
        "load_scale_bounds": [min(row[0] for row in world["scenarios"]),
                              max(row[0] for row in world["scenarios"])],
    }


def _finite(value, name, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(name + " must be numeric")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(name + " must be finite")
    if low is not None and value < low:
        raise ValueError(name + " is below its bound")
    if high is not None and value > high:
        raise ValueError(name + " is above its bound")
    return value


def _normalize_plan(plan, world):
    if not isinstance(plan, Mapping) or set(plan) != {"open_lines", "generator_1_share"}:
        raise ValueError("plan must contain exactly open_lines and generator_1_share")
    opened = plan["open_lines"]
    if not isinstance(opened, (list, tuple)) or len(opened) > MAX_OPEN:
        raise ValueError("open_lines has the wrong shape")
    if any(not isinstance(v, str) for v in opened) or len(set(opened)) != len(opened):
        raise ValueError("open_lines must be distinct text identifiers")
    switchable = {row[0] for row in world["branches"] if row[6]}
    if not set(opened).issubset(switchable):
        raise ValueError("open_lines contains an unknown or fixed line")
    share = _finite(plan["generator_1_share"], "generator_1_share", SHARE_MIN, SHARE_MAX)
    return tuple(sorted(opened)), share


def _connected(active):
    seen = {0}
    for _ in range(5):
        for _, i, j, *_ in active:
            if i in seen:
                seen.add(j)
            if j in seen:
                seen.add(i)
    return len(seen) == 5


def _scenario(world, opened, share, load_scale, outage):
    active = [row for row in world["branches"] if row[0] not in opened and row[0] != outage]
    if not _connected(active):
        return None
    ybus = np.zeros((5, 5), dtype=complex)
    admittances = {}
    for line_id, i, j, r, x, rate, _ in active:
        y = 1.0 / complex(r, x)
        admittances[line_id] = y
        ybus[i, i] += y
        ybus[j, j] += y
        ybus[i, j] -= y
        ybus[j, i] -= y

    p_load = np.asarray((0.0,) + world["loads"], dtype=float) * load_scale
    q_load = p_load * math.tan(math.acos(0.9524241472))
    specified_p = -p_load
    specified_p[1] += share * float(np.sum(p_load))

    def residual(x):
        angles = np.r_[0.0, x[:4]]
        magnitudes = np.r_[1.03, 1.01, np.exp(np.clip(x[4:], -0.3, 0.3))]
        voltage = magnitudes * np.exp(1j * angles)
        injections = voltage * np.conj(ybus @ voltage)
        return np.r_[injections.real[1:] - specified_p[1:],
                     injections.imag[2:] + q_load[2:]]

    solved = root(residual, np.zeros(7), method="hybr")
    if not solved.success or float(np.max(np.abs(residual(solved.x)))) > 1.0e-7:
        return None
    angles = np.r_[0.0, solved.x[:4]]
    magnitudes = np.r_[1.03, 1.01, np.exp(np.clip(solved.x[4:], -0.3, 0.3))]
    voltage = magnitudes * np.exp(1j * angles)
    injections = voltage * np.conj(ybus @ voltage)
    p0 = float(injections.real[0] + p_load[0])
    p1 = float(specified_p[1] + p_load[1])
    q0 = float(injections.imag[0] + q_load[0])
    q1 = float(injections.imag[1] + q_load[1])
    if not (0.0 <= p0 <= 3.0 and 0.0 <= p1 <= 2.5 and -0.8 <= q0 <= 1.5 and -0.8 <= q1 <= 1.5):
        return None
    if float(np.min(magnitudes)) < V_MIN or float(np.max(magnitudes)) > V_MAX:
        return None

    loading = 0.0
    for line_id, i, j, _r, _x, rate, _ in active:
        y = admittances[line_id]
        s_ij = voltage[i] * np.conj((voltage[i] - voltage[j]) * y)
        s_ji = voltage[j] * np.conj((voltage[j] - voltage[i]) * y)
        loading = max(loading, abs(s_ij) / rate, abs(s_ji) / rate)
    if loading > 1.0 + 1.0e-9:
        return None
    c1, c2 = world["cheap_cost"]
    cost = 20.0 * p0 + 7.0 * p0 * p0 + c1 * p1 + c2 * p1 * p1
    return cost, loading, float(np.min(magnitudes)), float(np.max(magnitudes))


def _evaluate_plan(world, plan):
    opened, share = _normalize_plan(plan, world)
    rows = [_scenario(world, opened, share, scale, outage)
            for scale, outage in world["scenarios"]]
    if any(row is None for row in rows):
        return {"feasible": False, "robust_cost": 1.0e6,
                "worst_thermal_loading": 2.0, "minimum_voltage_pu": 0.0,
                "maximum_voltage_pu": 2.0}
    return {
        "feasible": True,
        "robust_cost": float(max(row[0] for row in rows) + SWITCH_COST * len(opened)),
        "worst_thermal_loading": float(max(row[1] for row in rows)),
        "minimum_voltage_pu": float(min(row[2] for row in rows)),
        "maximum_voltage_pu": float(max(row[3] for row in rows)),
    }


class _Oracle:
    def __init__(self, world):
        self.world = world
        self.calls = 0
        self.failure = None
        self.records = {}

    def evaluate_plan(self, plan):
        if self.calls >= CALL_BUDGET:
            self.failure = self.failure or "budget_exceeded"
            raise ValueError("evaluation budget exceeded")
        try:
            normalized = _normalize_plan(plan, self.world)
        except Exception:
            self.failure = self.failure or "invalid_query"
            raise
        self.calls += 1
        plan_id = "plan-%02d" % self.calls
        result = _evaluate_plan(self.world, {"open_lines": list(normalized[0]),
                                             "generator_1_share": normalized[1]})
        self.records[plan_id] = result
        return {"plan_id": plan_id, **result, "budget_cost": 1,
                "remaining_budget": CALL_BUDGET - self.calls}


def _evaluate_world(optimize_switching, world, index):
    oracle = _Oracle(world)
    try:
        answer = optimize_switching(_problem(world), oracle.evaluate_plan)
        if oracle.failure is not None:
            raise ValueError("callback contract was violated")
        if not isinstance(answer, Mapping) or set(answer) != {"plan_id"}:
            raise ValueError("submission must contain exactly plan_id")
        if not isinstance(answer["plan_id"], str) or answer["plan_id"] not in oracle.records:
            raise ValueError("plan_id was not returned by this session")
        result = oracle.records[answer["plan_id"]]
    except Exception:
        return {"world_index": index, "split": world["split"], "valid": False,
                "feasible": False, "robust_cost": 1.0e6, "calls": oracle.calls,
                "failure_kind": oracle.failure or "invalid_submission"}
    return {"world_index": index, "split": world["split"], "valid": True,
            "calls": oracle.calls, "failure_kind": None, **result}


def _reference_plan(world):
    candidates = []
    switchable = [row[0] for row in world["branches"] if row[6]]
    coarse_shares = (0.35, 0.475, 0.60, 0.725, 0.85)
    for opened in [()] + [(line,) for line in switchable]:
        for share in coarse_shares:
            result = _evaluate_plan(world, {"open_lines": opened, "generator_1_share": share})
            if result["feasible"]:
                candidates.append((result["robust_cost"], opened, share))
    if not candidates:
        raise RuntimeError("reference search found no feasible policy")
    candidates.sort()
    _, best_open, best_share = candidates[0]
    for share in np.linspace(max(SHARE_MIN, best_share - 0.12),
                             min(SHARE_MAX, best_share + 0.12), 8):
        result = _evaluate_plan(world, {"open_lines": best_open,
                                        "generator_1_share": float(share)})
        if result["feasible"]:
            candidates.append((result["robust_cost"], best_open, float(share)))
    return min(candidates)


@lru_cache(maxsize=1)
def _anchors():
    anchors = {}
    for world in WORLDS:
        baseline = _evaluate_plan(world, {"open_lines": [], "generator_1_share": 0.40})
        if not baseline["feasible"]:
            raise RuntimeError("baseline policy is not feasible")
        reference_cost, opened, share = _reference_plan(world)
        if reference_cost >= baseline["robust_cost"] - 0.5:
            raise RuntimeError("reference lacks material headroom")
        anchors[world["name"]] = (baseline["robust_cost"], reference_cost, opened, share)
    return anchors


def _split_metrics(rows):
    scores = []
    anchors = _anchors()
    for row in rows:
        world = WORLDS[row["world_index"]]
        baseline, reference, _, _ = anchors[world["name"]]
        if row["feasible"]:
            score = max((baseline - row["robust_cost"]) / (baseline - reference), 0.0)
        else:
            score = 0.0
        scores.append(float(score))
    return {
        "score": float(np.mean(scores)),
        "feasibility_rate": float(np.mean([row["feasible"] for row in rows])),
        "mean_calls": float(np.mean([row["calls"] for row in rows])),
        "mean_robust_cost": float(np.mean([row["robust_cost"] for row in rows])),
    }


def evaluate(optimize_switching):
    records = [_evaluate_world(optimize_switching, world, i)
               for i, world in enumerate(WORLDS)]
    development = [row for row in records if row["split"] == "development"]
    heldout = [row for row in records if row["split"] == "heldout"]
    dev = _split_metrics(development)
    hold = _split_metrics(heldout)
    valid = float(all(row["valid"] for row in records))
    return {
        "combined_score": dev["score"] if valid else 0.0,
        "valid": valid,
        "feasibility_rate": dev["feasibility_rate"],
        "development_mean_calls": dev["mean_calls"],
        "development_mean_robust_cost": dev["mean_robust_cost"],
        "heldout_policy_score": hold["score"],
        "heldout_feasibility_rate": hold["feasibility_rate"],
        "heldout_mean_robust_cost": hold["mean_robust_cost"],
        "per_world": records,
    }
