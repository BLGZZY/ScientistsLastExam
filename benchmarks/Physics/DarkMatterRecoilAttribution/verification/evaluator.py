"""Frozen multi-target recoil inference; synthetic rates, not real DM discovery."""
from __future__ import annotations

import copy
import math

import numpy as np

TARGETS = (("Xe", 131, 54), ("Ge", 73, 32), ("Ar", 40, 18))
ENERGIES = np.geomspace(2.0, 65.0, 18)
SPEEDS = np.array([160.0, 260.0, 380.0])
BUDGET = 12
LAWS = ("contact", "q2")


def bin_widths(energy):
    e = np.asarray(energy)
    edges = np.r_[e[0]**2/np.sqrt(e[0]*e[1]), np.sqrt(e[:-1]*e[1:]),
                  e[-1]**2/np.sqrt(e[-1]*e[-2])]
    return np.diff(edges)


def recoil_kernel(mass, ratio, power, target, energy):
    """Isotropic Maxwell speed-mixture inverse speeds and a Gaussian form factor.

    q is in GeV, E in keV, v in km/s. Rates are normalized benchmark units;
    isotopic abundance, lab boost, escape truncation and detector smearing omitted.
    """
    _, a, z = TARGETS[target]
    nucleus = 0.9315 * a
    reduced = mass * nucleus / (mass + nucleus)
    e = np.asarray(energy)
    q = np.sqrt(2.0 * nucleus * e * 1e-6)
    vmin = 299792.458 * q / (2.0 * reduced)
    radius = 1.2 * a ** (1.0 / 3.0)
    form = np.exp(-(q * radius / 0.1973269804) ** 2 / 3.0)
    coherence = ((z + (a - z) * ratio) / 100.0) ** 2
    eta = np.exp(-(vmin[:, None] / SPEEDS) ** 2) * (260.0 / SPEEDS)
    return bin_widths(e)[:, None] * coherence * form[:, None] * (q[:, None] / 0.05) ** power * eta


def make_world(seed, kind):
    rng = np.random.default_rng(seed)
    mass = float(np.exp(rng.uniform(np.log(22), np.log(125))))
    ratio = float(rng.uniform(0.65, 1.35))
    weights = rng.dirichlet([2, 2, 2]) * rng.uniform(55, 100)
    background = rng.uniform(4, 12, 3)
    gain = rng.uniform(0.75, 1.25, 3)
    energy = ENERGIES * rng.uniform(0.92, 1.08)
    rates = []
    for t in range(3):
        if kind == "none":
            signal = np.zeros_like(energy)
        else:
            power = {"contact": 0, "q2": 2, "unsupported": 0}[kind]
            signal = recoil_kernel(mass, ratio, power, t, energy) @ weights
            if kind == "unsupported":
                # An instrumental recoil-like excess violates the shared-halo spectrum.
                signal += rng.uniform(25, 55) * np.exp(
                    -0.5 * ((energy - rng.uniform(18, 35)) / 2.5) ** 2)
        rates.append(gain[t] * (signal + bin_widths(energy) * (background[t] * np.exp(-energy / 32.0) + 1.5)))
    problem = {
        "targets": [{"name": name, "mass_number": a, "protons": z}
                    for name, a, z in TARGETS],
        "energy_kev": energy.tolist(), "bin_widths_kev": bin_widths(energy).tolist(),
        "speed_components_kms": SPEEDS.tolist(),
        "budget_units": BUDGET, "mass_bounds_gev": [10.0, 250.0],
        "coupling_ratio_bounds": [0.5, 1.5], "interaction_laws": list(LAWS),
        "background_scale_kev": 32.0, "flat_background_rate": 1.5,
        "calibration_rate": 100.0, "background_control_factor": 8.0,
        "reference_momentum_gev": 0.05,
    }
    return dict(seed=seed, kind=kind, mass=mass, ratio=ratio, weights=weights,
                background=background, gain=gain, energy=energy, rates=np.array(rates),
                problem=problem)


class Campaign:
    def __init__(self, world):
        self.world = world
        self.used = 0
        self.violated = False
        self.repeats = [0, 0, 0]

    def __call__(self, request):
        try:
            if not isinstance(request, dict) or set(request) != {"target", "units"}:
                raise ValueError("invalid request")
            t, n = request["target"], request["units"]
            if type(t) is not int or not 0 <= t < 3 or type(n) is not int or n < 1:
                raise ValueError("invalid target or exposure")
            if self.used + n > BUDGET:
                raise ValueError("budget exceeded")
            self.used += n
            w = self.world
            counts = np.zeros(len(w["energy"]), dtype=np.int64)
            controls = np.zeros_like(counts)
            calibration = 0
            # A repeated unit is a new observation. Batching/reordering does not change it.
            for k in range(self.repeats[t], self.repeats[t] + n):
                rng = np.random.default_rng([w["seed"], 901, t, k])
                counts += rng.poisson(w["rates"][t])
                controls += rng.poisson(8 * w["gain"][t] * (
                    bin_widths(w["energy"]) * (w["background"][t] * np.exp(-w["energy"] / 32.0) + 1.5)))
                calibration += int(rng.poisson(100 * w["gain"][t]))
            self.repeats[t] += n
            return {"target": t, "units": n, "counts": counts.tolist(),
                    "background_counts": controls.tolist(), "calibration_counts": calibration}
        except Exception:
            self.violated = True
            raise ValueError("invalid experiment or exhausted budget") from None


def validate(answer):
    if not isinstance(answer, dict):
        raise ValueError("answer must be a mapping")
    if type(answer.get("abstain", False)) is not bool:
        raise ValueError("abstain must be boolean")
    confidence = answer.get("confidence", 1.0)
    if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("invalid confidence")
    if answer.get("abstain", False):
        return "abstain", None, float(confidence)
    model = answer.get("model")
    if not isinstance(model, str) or model not in (*LAWS, "none"):
        raise ValueError("invalid model")
    mass = answer.get("mass_gev")
    if model != "none" and (type(mass) not in (float, int) or
                             not math.isfinite(mass) or not 10 <= mass <= 250):
        raise ValueError("invalid mass")
    return model, mass, float(confidence)


def score_world(world, answer):
    model, mass, confidence = validate(answer)
    kind = world["kind"]
    accepted = model not in ("abstain", "none")
    correct = model == kind or (kind == "unsupported" and model == "abstain")
    parameter_score = 0.0
    if kind in LAWS and model == kind:
        parameter_score = max(0.0, 1.0 - abs(math.log(mass / world["mass"])) / 0.25)
    mechanism = parameter_score if kind in LAWS else float(correct)
    return {"valid": True, "model": model, "mechanism": mechanism,
            "claim": accepted, "false_claim": bool(accepted and not correct),
            "abstain": model == "abstain", "correct_refusal": kind == "unsupported" and model == "abstain",
            "confidence_brier": (confidence - float(correct)) ** 2}


def evaluate(candidate):
    all_rows = []
    results = {}
    for split, seed_base in (("development", 731500), ("heldout", 941700)):
        rows = []
        kinds = ["contact", "q2"] * 3 + ["none"] * 2 + ["unsupported"] * 2
        # Public instruments and call count carry no seed, split or class indicator.
        for i in np.random.default_rng(seed_base + 79).permutation(len(kinds)):
            i = int(i)
            kind = kinds[i]
            w = make_world(seed_base + i * 101, kind)
            lab = Campaign(w)
            try:
                # A fresh process and tmpfs per world, including the split boundary.
                if (all_rows or rows) and hasattr(candidate, "reset_session"):
                    candidate.reset_session()
                ans = candidate(copy.deepcopy(w["problem"]), lab)
                if lab.violated:
                    raise ValueError("campaign invalidated")
                row = score_world(w, ans)
            except Exception:
                row = {"valid": False, "model": "invalid", "mechanism": 0.0,
                       "claim": False, "false_claim": False, "abstain": False,
                       "correct_refusal": False, "confidence_brier": 1.0}
            row.update(split=split, kind=kind, units=lab.used)
            rows.append(row)
        n = len(rows)
        raw = sum(r["mechanism"] for r in rows) / n
        claims = sum(r["claim"] for r in rows)
        false = sum(r["false_claim"] for r in rows)
        supported = [r for r in rows if r["kind"] in LAWS]
        rejected = [r for r in rows if r["kind"] == "unsupported"]
        values = {"mechanism_score": max(0.0, (raw - 0.2) / 0.8),
                  "false_discovery_rate": false / claims if claims else 0.0,
                  "false_discovery_count": false, "claim_count": claims,
                  "correct_refusal_rate": sum(r["correct_refusal"] for r in rejected) / len(rejected),
                  "refusal_world_count": len(rejected),
                  "discovery_coverage": sum(r["claim"] for r in supported) / len(supported),
                  "supported_world_count": len(supported),
                  "none_correct_rate": sum(r["model"] == "none" for r in rows if r["kind"] == "none") / 2,
                  "valid_rate": sum(r["valid"] for r in rows) / n,
                  "mean_units": sum(r["units"] for r in rows) / n,
                  "confidence_brier": sum(r["confidence_brier"] for r in rows) / n}
        results.update({split + "_" + k: round(float(v), 10) for k, v in values.items()})
        all_rows.extend(rows)
    results.update(combined_score=results["development_mechanism_score"],
                   valid=float(all(r["valid"] for r in all_rows)),
                   feasibility_rate=results["development_valid_rate"], per_instance=all_rows)
    return results
