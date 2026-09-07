"""Deterministic classical-laminate oracle for stacking-sequence design.

The public contract fixes the laminate composition.  Candidates choose only the ply order.  The
trusted oracle assembles the extensional and bending matrices, evaluates a simply-supported
Navier buckling approximation and a Tsai-Hill first-ply reserve factor, then repeats the check
under sealed material and load shifts.  It is a screening model, not a certification analysis.
"""
from __future__ import annotations

import copy
import math

import numpy as np


DIFFICULTY = "hard"
ANGLES = (-45, 0, 45, 90)
MAX_RUN = 2
# Score-one anchor: a witness-level adjacency warm start, multi-start permutation sampling
# with full pair-exchange refinement to convergence, then iterated local search (random
# three-swap perturbations re-converged by full pair exchange). The ILS phase walks out of
# the pair-exchange basins a narrow adjacency witness can also reach. The anchor is a search
# bound, not a proof of optimality, sized to keep the six-instance sweep near half a minute
# on this builder machine and leave the candidate most of the evaluation budget.
ANCHOR_STARTS = 8
ANCHOR_ILS_ROUNDS = 12
ANCHOR_SEED = 91000
_REFERENCE_CACHE = {}


INSTANCE_SPECS = (
    # Every development and held-out panel carries THREE paired load/moment cases whose
    # optima conflict: an axial case (0-dominant), a transverse case (90-dominant) and a
    # shear/twist case (interleaved +/-45 dominant through the D16/D26 coupling that a
    # clustered stack cannot zero). No single clustered pattern is near-optimal on all
    # three. Half-stacks are 18-24 plies with deliberately uneven angle mixes; the
    # multinomial half-permutation counts are 3.1e8 (dev_axial_long), 5.6e9
    # (dev_biaxial_square), 1.3e11 (dev_shear_panel), 3.0e11 (dev_transverse),
    # 8.2e9 (heldout_orthotropic) and 5.5e11 (heldout_balanced_load), so exhaustive or
    # near-exhaustive screening of the half-stack is out of reach.
    {"name": "dev_axial_long", "split": "development", "plies": 36, "half_counts": (5, 6, 5, 2),
     "a": 1.20, "b": 0.72,
     "loads": ((6.8e4, 2.0e4, 0.6e4), (2.2e4, 6.6e4, -1.0e4), (2.8e4, 2.8e4, 7.3e4)),
     "moments": ((550.0, 121.0, 209.0), (-180.0, 500.0, -150.0), (85.0, 85.0, 940.0)),
     "material": (132e9, 9.2e9, 4.8e9, 0.29), "strength": (1.45e9, 1.05e9, 55e6, 185e6, 72e6)},
    {"name": "dev_biaxial_square", "split": "development", "plies": 40, "half_counts": (5, 7, 5, 3),
     "a": 0.92, "b": 0.92,
     "loads": ((5.4e4, 4.9e4, 2.2e4), (4.0e4, 8.6e4, -1.8e4), (3.6e4, 3.6e4, 9.0e4)),
     "moments": ((680.0, 360.0, -200.0), (-440.0, 640.0, 300.0), (105.0, 105.0, 1100.0)),
     "material": (145e9, 8.5e9, 5.2e9, 0.27), "strength": (1.60e9, 1.10e9, 48e6, 170e6, 68e6)},
    {"name": "dev_shear_panel", "split": "development", "plies": 44, "half_counts": (6, 6, 6, 4),
     "a": 1.05, "b": 0.66,
     "loads": ((9.7e4, 4.5e4, 1.0e5), (5.2e4, 9.6e4, -7.5e4), (4.7e4, 4.7e4, 1.4e5)),
     "moments": ((605.0, 330.0, 858.0), (-462.0, 968.0, -605.0), (130.0, 130.0, 1330.0)),
     "material": (126e9, 10.4e9, 5.0e9, 0.31), "strength": (1.35e9, 0.98e9, 62e6, 205e6, 78e6)},
    {"name": "dev_transverse", "split": "development", "plies": 48, "half_counts": (7, 8, 7, 2),
     "a": 0.78, "b": 1.18,
     "loads": ((5.0e4, 1.4e4, 0.5e4), (1.9e4, 1.35e5, -0.9e4), (4.5e4, 4.5e4, 9.7e4)),
     "moments": ((950.0, 300.0, -260.0), (-520.0, 1250.0, 420.0), (150.0, 150.0, 1450.0)),
     "material": (138e9, 9.7e9, 4.5e9, 0.28), "strength": (1.52e9, 1.02e9, 58e6, 190e6, 70e6)},
    {"name": "heldout_orthotropic", "split": "heldout", "plies": 40, "half_counts": (4, 6, 4, 6),
     "a": 1.32, "b": 0.81,
     "loads": ((6.5e4, 1.8e4, -2.7e4), (2.6e4, 6.4e4, 3.0e4), (3.2e4, 3.2e4, 7.7e4)),
     "moments": ((782.0, 212.0, -382.0), (-255.0, 833.0, 297.0), (115.0, 115.0, 970.0)),
     "material": (119e9, 11.2e9, 4.2e9, 0.30), "strength": (1.28e9, 0.92e9, 66e6, 215e6, 74e6)},
    {"name": "heldout_balanced_load", "split": "heldout", "plies": 48, "half_counts": (6, 9, 6, 3),
     "a": 0.86, "b": 1.04,
     "loads": ((9.3e4, 1.08e5, 7.7e4), (7.5e4, 1.42e5, -1.1e4), (4.2e4, 4.2e4, 1.0e5)),
     "moments": ((1040.0, 1152.0, 880.0), (-960.0, 1280.0, -608.0), (145.0, 145.0, 1500.0)),
     "material": (151e9, 8.1e9, 5.5e9, 0.26), "strength": (1.70e9, 1.18e9, 45e6, 165e6, 65e6)},
)


def _problem(spec):
    counts = {str(a): int(c) * 2 for a, c in zip(ANGLES, spec["half_counts"])}
    e1, e2, g12, nu12 = spec["material"]
    xt, xc, yt, yc, s = spec["strength"]
    return {
        "ply_count": int(spec["plies"]), "allowed_angles_deg": list(ANGLES),
        "required_angle_counts": counts, "symmetric": True, "balanced": True,
        "maximum_consecutive_equal_plies": MAX_RUN, "ply_thickness_m": 0.000125,
        "panel_length_m": float(spec["a"]), "panel_width_m": float(spec["b"]),
        "load_cases_n_per_m": [[0.01*value for value in row] for row in spec["loads"]],
        "moment_cases_n": [[float(value) for value in row] for row in spec["moments"]],
        "material": {"e1_pa": e1, "e2_pa": e2, "g12_pa": g12, "nu12": nu12,
                     "xt_pa": xt, "xc_pa": xc, "yt_pa": yt, "yc_pa": yc, "s_pa": s},
        "model": "classical laminate A/D matrices; simply-supported Navier buckling modes 1..4; Tsai-Hill first-ply reserve under membrane and bending loads",
    }


def _qbar(material, angle):
    e1, e2, g, nu12 = (float(material[k]) for k in ("e1_pa", "e2_pa", "g12_pa", "nu12"))
    nu21 = nu12 * e2 / e1
    d = 1.0 - nu12 * nu21
    q11, q22, q12, q66 = e1 / d, e2 / d, nu12 * e2 / d, g
    r = math.radians(angle); m, n = math.cos(r), math.sin(r)
    m2, n2, m4, n4 = m*m, n*n, m**4, n**4
    q16 = (q11-q12-2*q66)*m**3*n - (q22-q12-2*q66)*m*n**3
    q26 = (q11-q12-2*q66)*m*n**3 - (q22-q12-2*q66)*m**3*n
    return np.array([
        [q11*m4 + 2*(q12+2*q66)*m2*n2 + q22*n4,
         (q11+q22-4*q66)*m2*n2 + q12*(m4+n4), q16],
        [(q11+q22-4*q66)*m2*n2 + q12*(m4+n4),
         q11*n4 + 2*(q12+2*q66)*m2*n2 + q22*m4, q26],
        [q16, q26, (q11+q22-2*q12-2*q66)*m2*n2 + q66*(m4+n4)],
    ], dtype=float)


def _laminate(problem, sequence, material=None, loads=None, return_components=False):
    material = material or problem["material"]
    loads = loads or problem["load_cases_n_per_m"]
    t = float(problem["ply_thickness_m"]); h = len(sequence) * t
    edges = np.linspace(-0.5*h, 0.5*h, len(sequence)+1)
    a_mat = np.zeros((3, 3)); d_mat = np.zeros((3, 3)); qbars = []
    for k, angle in enumerate(sequence):
        q = _qbar(material, angle); qbars.append(q)
        a_mat += q * (edges[k+1]-edges[k])
        d_mat += q * (edges[k+1]**3-edges[k]**3) / 3.0
    a, b = float(problem["panel_length_m"]), float(problem["panel_width_m"])
    reserve = float("inf")
    buckling_reserve = first_ply_reserve = float("inf")
    for load_index, (nx, ny, nxy) in enumerate(loads):
        best = float("inf")
        for mx in range(1, 5):
            for my in range(1, 5):
                x, y = mx*math.pi/a, my*math.pi/b
                numerator = d_mat[0,0]*x**4 + 2*(d_mat[0,1]+2*d_mat[2,2])*x*x*y*y + d_mat[1,1]*y**4
                denominator = max(nx*x*x + ny*y*y + 2*abs(nxy)*x*y, 1e-12)
                best = min(best, numerator / denominator)
        strain = np.linalg.solve(a_mat, np.asarray([nx, ny, nxy], dtype=float))
        curvature = np.linalg.solve(d_mat, np.asarray(problem["moment_cases_n"][load_index]))
        failure_index = 0.0
        for ply, (angle, q) in enumerate(zip(sequence, qbars)):
            # Check both ply faces: bending stresses depend on distance from the midplane.
            for face in (edges[ply], edges[ply + 1]):
                sx, sy, txy = q @ (strain + face * curvature)
                r = math.radians(angle); m, n = math.cos(r), math.sin(r)
                s1 = m*m*sx+n*n*sy+2*m*n*txy
                s2 = n*n*sx+m*m*sy-2*m*n*txy
                t12 = -m*n*sx+m*n*sy+(m*m-n*n)*txy
                xallow = material["xt_pa"] if s1 >= 0 else material["xc_pa"]
                yallow = material["yt_pa"] if s2 >= 0 else material["yc_pa"]
                idx = (s1/xallow)**2 - (s1*s2)/(xallow*xallow) + (s2/yallow)**2 + (t12/material["s_pa"])**2
                failure_index = max(failure_index, float(idx))
        first_ply = 1.0 / math.sqrt(max(failure_index, 1e-18))
        reserve = min(reserve, best, first_ply)
        buckling_reserve = min(buckling_reserve, best)
        first_ply_reserve = min(first_ply_reserve, first_ply)
    if return_components:
        return {"reserve_factor":float(reserve), "buckling_reserve":float(buckling_reserve),
                "first_ply_reserve":float(first_ply_reserve)}
    return float(reserve)


def _validate(problem, value):
    if isinstance(value, dict):
        value = value.get("ply_angles_deg")
    if not isinstance(value, (list, tuple)) or len(value) != int(problem["ply_count"]):
        raise ValueError("return exactly ply_count angles")
    sequence = []
    for item in value:
        number = float(item)
        if not math.isfinite(number) or number not in ANGLES:
            raise ValueError("illegal ply angle")
        sequence.append(int(number))
    expected = {int(k): int(v) for k, v in problem["required_angle_counts"].items()}
    if {a: sequence.count(a) for a in ANGLES} != expected:
        raise ValueError("angle counts changed")
    if sequence != list(reversed(sequence)):
        raise ValueError("laminate must be symmetric")
    if sequence.count(45) != sequence.count(-45):
        raise ValueError("laminate must be balanced")
    if max(len(list(group)) for _, group in __import__("itertools").groupby(sequence)) > MAX_RUN:
        raise ValueError("too many consecutive equal plies")
    return sequence


def _baseline(problem):
    """Quasi-isotropic interleaved baseline that stays valid for uneven angle mixes.

    Greedy largest-remaining-first placement capped at two consecutive equal plies keeps
    interior runs short and makes the mirror junction safe (at most 2+2 at the symmetry
    plane only when the first and last ply angles coincide, which the start-count rule
    avoids for every shipped mix); an explicit repair swap covers the remaining case.
    """
    counts = {int(k): int(v)//2 for k, v in problem["required_angle_counts"].items()}
    half = []
    while sum(counts.values()):
        choice = None
        for angle in sorted(counts, key=lambda a: (-counts[a], (0, 45, -45, 90).index(a))):
            if counts[angle] <= 0:
                continue
            run = 0
            for item in reversed(half):
                if item != angle:
                    break
                run += 1
            if run >= 2:
                continue
            choice = angle
            break
        if choice is None:  # only reachable if a single angle dominates everything
            choice = max(counts, key=lambda a: counts[a])
        half.append(choice)
        counts[choice] -= 1
    # Mirror-junction repair: the full stack joins half[-1] to half[0].
    def _run_at(seq, angle, from_end):
        run = 0
        for item in (reversed(seq) if from_end else seq):
            if item != angle:
                break
            run += 1
        return run
    if half[0] == half[-1] and _run_at(half, half[0], True) + _run_at(half, half[0], False) > MAX_RUN:
        for i in range(len(half) - 2, -1, -1):
            if half[i] == half[-1]:
                continue
            candidate = half.copy()
            candidate[i], candidate[-1] = candidate[-1], candidate[i]
            if max(len(list(group)) for _, group in __import__("itertools").groupby(candidate)) <= 2:
                half = candidate
                break
    return half + half[::-1]


def _block_patterns(problem):
    """Structured tiled families: contiguous same-angle blocks of width 1-3 round-robined
    over every angle order. Deterministic, a few hundred sequences, used as anchor seeds so
    the search bound also covers textbook clustered stacking patterns."""
    import itertools
    counts = {a: int(problem["required_angle_counts"][str(a)])//2 for a in ANGLES}
    out = []
    for widths in itertools.product((1, 2, 3), repeat=4):
        for order in itertools.permutations(ANGLES):
            blocks = {a: [] for a in ANGLES}
            for a, width in zip(ANGLES, widths):
                left = counts[a]
                while left > 0:
                    take = min(width, left)
                    blocks[a].append(take); left -= take
            half = []
            idx = {a: 0 for a in ANGLES}
            exhausted = False
            while not exhausted:
                exhausted = True
                for a in order:
                    if idx[a] < len(blocks[a]):
                        exhausted = False
                        half.extend([a]*blocks[a][idx[a]])
                        idx[a] += 1
            if len(half) != sum(counts.values()):
                continue
            seq = half + half[::-1]
            try:
                out.append(_validate(problem, seq))
            except ValueError:
                continue
    return out


def _reference(problem):
    """Score-one anchor: structured-family seeds plus multi-start full pair exchange.

    Tiled block families and a ten-permutation adjacency sweep (the witness's own strength)
    seed the incumbent, so the anchor dominates any narrower witness and any structured
    pattern family by construction; ANCHOR_STARTS further random halves are then sampled and
    the incumbent refined by every feasible pair exchange to convergence, followed by
    iterated local search. The anchor is a search bound, not a proof of optimality.
    """
    key = (problem["ply_count"], problem["panel_length_m"], problem["panel_width_m"],
           tuple(tuple(x) for x in problem["load_cases_n_per_m"]),
           tuple(tuple(x) for x in problem["moment_cases_n"]),
           tuple(sorted(problem["material"].items())))
    if key in _REFERENCE_CACHE:
        return list(_REFERENCE_CACHE[key])
    base = _baseline(problem); half = base[:len(base)//2]
    rng = np.random.default_rng(ANCHOR_SEED + problem["ply_count"])
    best, best_q = base, _laminate(problem, base)
    for seed_seq in _block_patterns(problem):
        q = _laminate(problem, seed_seq)
        if q > best_q: best, best_q = seed_seq, q
    # Warm start: a wider witness-shape adjacency sweep with the anchor's own seed,
    # so the anchor is never weaker than the thirteen-start adjacency witness.
    for _ in range(24):
        trial_half = list(rng.permutation(half)); trial = trial_half + trial_half[::-1]
        try:
            trial = _validate(problem, trial)
        except ValueError:
            continue
        q = _laminate(problem, trial)
        if q > best_q: best, best_q = trial, q
    for i in range(len(best)//2 - 1):
        h = best[:len(best)//2]; j = i + 1
        if h[i] == h[j]:
            continue
        trial_half = h.copy(); trial_half[i], trial_half[j] = trial_half[j], trial_half[i]
        trial = trial_half + trial_half[::-1]
        try:
            _validate(problem, trial)
        except ValueError:
            continue
        q = _laminate(problem, trial)
        if q > best_q + 1e-14: best, best_q = trial, q
    for _ in range(ANCHOR_STARTS):
        trial_half = list(rng.permutation(half)); trial = trial_half + trial_half[::-1]
        try:
            trial = _validate(problem, trial)
        except ValueError:
            continue
        q = _laminate(problem, trial)
        if q > best_q: best, best_q = trial, q
        # Full pair exchange to convergence from the incumbent.
        while True:
            improved = False
            h = best[:len(best)//2]
            for i in range(len(h)):
                for j in range(i + 1, len(h)):
                    if h[i] == h[j]:
                        continue
                    trial_half = h.copy()
                    trial_half[i], trial_half[j] = trial_half[j], trial_half[i]
                    trial = trial_half + trial_half[::-1]
                    try:
                        _validate(problem, trial)
                    except ValueError:
                        continue
                    quality = _laminate(problem, trial)
                    if quality > best_q + 1e-14:
                        best, best_q = trial, quality
                        improved = True
            if not improved:
                break
    # Iterated local search: perturb the incumbent half by up to three random distinct-angle
    # swaps, re-converge the perturbed sequence by full pair exchange, keep it if better.
    for _ in range(ANCHOR_ILS_ROUNDS):
        h = best[:len(best)//2]
        pert = h.copy()
        for _swap in range(3):
            i, j = rng.choice(len(pert), size=2, replace=False)
            if pert[i] != pert[j]:
                pert[i], pert[j] = pert[j], pert[i]
        trial = pert + pert[::-1]
        try:
            trial = _validate(problem, trial)
        except ValueError:
            continue
        cand, cand_q = trial, _laminate(problem, trial)
        while True:
            improved = False
            ch = cand[:len(cand)//2]
            for i in range(len(ch)):
                for j in range(i + 1, len(ch)):
                    if ch[i] == ch[j]:
                        continue
                    trial_half = ch.copy()
                    trial_half[i], trial_half[j] = trial_half[j], trial_half[i]
                    cand_trial = trial_half + trial_half[::-1]
                    try:
                        _validate(problem, cand_trial)
                    except ValueError:
                        continue
                    quality = _laminate(problem, cand_trial)
                    if quality > cand_q + 1e-14:
                        cand, cand_q = cand_trial, quality
                        improved = True
            if not improved:
                break
        if cand_q > best_q + 1e-14:
            best, best_q = cand, cand_q
    _REFERENCE_CACHE[key] = tuple(best)
    return list(best)


def _shifted_quality(problem, sequence):
    material = copy.deepcopy(problem["material"])
    material["e2_pa"] *= 0.90; material["g12_pa"] *= 0.88
    material["yt_pa"] *= 0.92; material["s_pa"] *= 0.90
    loads = [[1.12*x, 1.08*y, 1.20*z] for x, y, z in problem["load_cases_n_per_m"]]
    return _laminate(problem, sequence, material=material, loads=loads)


def _score_instance(candidate, spec):
    problem = _problem(spec)
    baseline = _baseline(problem); reference = _reference(problem)
    low, high = _laminate(problem, baseline), _laminate(problem, reference)
    try:
        sequence = _validate(problem, candidate(copy.deepcopy(problem)))
        quality = _laminate(problem, sequence)
        robust = _shifted_quality(problem, sequence)
        score = (quality-low) / max(high-low, 1e-12)
        robust_low, robust_high = _shifted_quality(problem, baseline), _shifted_quality(problem, reference)
        robust_score = (robust-robust_low) / max(robust_high-robust_low, 1e-12)
        return {"name": spec["name"], "split": spec["split"], "valid": True,
                "score": float(score), "reserve_factor": quality,
                "robustness_score": float(robust_score), "robust_reserve_factor": robust}
    except Exception as exc:
        return {"name": spec["name"], "split": spec["split"], "valid": False,
                "score": 0.0, "reserve_factor": 0.0, "robustness_score": 0.0,
                "robust_reserve_factor": 0.0, "reason": f"{type(exc).__name__}: {exc}"}


def evaluate(design_laminate):
    rows = [_score_instance(design_laminate, spec) for spec in INSTANCE_SPECS]
    dev = [r for r in rows if r["split"] == "development"]
    held = [r for r in rows if r["split"] == "heldout"]
    return {
        "combined_score": max(0.0, float(np.mean([r["score"] for r in dev]))) if all(r["valid"] for r in dev) else 0.0,
        "valid": float(all(r["valid"] for r in dev)),
        "feasibility_rate": float(np.mean([r["valid"] for r in dev])),
        "robustness_score": float(np.mean([r["robustness_score"] for r in dev])),
        "heldout_policy_score": float(np.mean([r["score"] for r in held])),
        "heldout_robustness_score": float(np.mean([r["robustness_score"] for r in held])),
        "heldout_feasibility_rate": float(np.mean([r["valid"] for r in held])),
        "per_instance": rows,
    }
