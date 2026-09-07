"""Exact ternary radius-one covering checker with clipped bound-gap progress.

Zero is a runnable Hamming-code product; one is the cited size lower bound,
not a published construction. Attainability is unknown. The coverage checker
proves the submitted cover, not the external lower-bound theorem.
"""

from __future__ import annotations

from itertools import islice
import itertools
import numpy as np


def _normalized(value: float, baseline: float, target: float) -> float:
    """Higher-is-better normalization: generic construction=0, cited bound=1."""
    if target <= baseline:
        raise ValueError("target must improve on the zero anchor")
    return float(min(1.0, max(0.0, (value - baseline) / (target - baseline))))


def _cap(n: int) -> int:
    return 3 ** n


def _baseline_covering(n: int):
    """Extend the [4,2,3]_3 Hamming code with all possible length-(n-4) suffixes."""
    if n < 4:
        raise ValueError("this baseline requires n >= 4")
    c4 = [list(w) for w in itertools.product(range(3), repeat=4)
          if (w[0] + w[2] + w[3]) % 3 == 0
          and (w[1] + w[2] + 2 * w[3]) % 3 == 0]
    return [w + list(rest) for w in c4
            for rest in itertools.product(range(3), repeat=n - 4)]


# Published lower bounds and constructive records, with separate roles.
# The coverage checker does not re-prove these literature lower bounds.
LOWER_BOUNDS = {6: 71, 7: 156, 8: 402, 9: 1060, 10: 2854}
KNOWN_SIZES = {6: 73, 7: 186, 8: 486, 9: 1269, 10: 3645}
SIZES = {n: {"baseline": len(_baseline_covering(n)), "lower_bound": bound,
             "sota_ref": KNOWN_SIZES[n]} for n, bound in LOWER_BOUNDS.items()}


def _as_symbol(value):
    """Integral ternary symbol or None (accepts int/numpy integer/1.0; rejects
    bool, 0.5, strings, and any symbol outside {0, 1, 2})."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, np.integer)):
        sym = int(value)
    elif isinstance(value, (float, np.floating)):
        f = float(value)
        if not f.is_integer():                  # also rejects NaN and +/-inf
            return None
        sym = int(f)
    else:
        return None
    return sym if sym in (0, 1, 2) else None


def verify_covering(raw, n: int) -> tuple[bool, int, str]:
    """Parse and fully re-check a candidate covering; returns (ok, size, reason)."""
    if raw is None or isinstance(raw, (str, bytes, dict, int, float, bool)):
        return False, 0, "covering must be a sequence of length-n ternary words"
    cap = _cap(n)
    if isinstance(raw, (list, tuple)):
        items = list(raw)
    else:
        try:                                    # bounded even for infinite generators
            items = list(islice(iter(raw), cap + 1))
        except TypeError:
            return False, 0, "covering is not iterable"
    if len(items) > cap:
        return False, len(items), f"{len(items)} codewords exceed checker cap {cap}"
    if len(items) == 0:
        return False, 0, "empty code never covers all 3^n words"
    words = []
    for pos, row in enumerate(items):
        if row is None or isinstance(row, (str, bytes, dict, int, float, bool)):
            return False, 0, f"codeword {pos} is not a sequence of ternary symbols"
        try:                                    # rows may also be lazy generators
            entries = list(islice(iter(row), n + 1))
        except TypeError:
            return False, 0, f"codeword {pos} is not iterable"
        if len(entries) != n:
            return False, 0, f"codeword {pos} has length {len(entries)} != {n}"
        digits = []
        for j, entry in enumerate(entries):
            sym = _as_symbol(entry)
            if sym is None:
                return False, 0, f"codeword {pos}, symbol {j} is not one of 0, 1, 2"
            digits.append(sym)
        words.append(digits)
    total = cap                                 # 3 ** n
    covered = bytearray(total)
    place = [3 ** i for i in range(n)]          # positional weights, digit i weight 3^i
    for digits in words:
        idx = 0
        for i in range(n):
            idx += digits[i] * place[i]
        covered[idx] = 1
        for i in range(n):                      # the 2n radius-1 neighbours:
            s = digits[i]                       # replace symbol i by each of the
            if s == 0:                          # other two, without touching any
                covered[idx + place[i]] = 1     # other position (base-3 deltas
                covered[idx + 2 * place[i]] = 1
            elif s == 1:
                covered[idx - place[i]] = 1
                covered[idx + place[i]] = 1
            else:
                covered[idx - 2 * place[i]] = 1
                covered[idx - place[i]] = 1
    if 0 in covered:
        missing = covered.count(0)
        return False, len(words), f"{missing} of {total} words are not covered"
    return True, len(words), "ok"

def score_n(n: int, ref: dict, build_covering) -> dict:
    try:
        raw = build_covering(n)
        ok, size, reason = verify_covering(raw, n)
    except Exception as exc:  # malformed values and lazy iterators also fail closed
        return {"n": n, "valid": False, "reason": f"raised: {exc}", "score": 0.0}
    if not ok:
        return {"n": n, "valid": False, "reason": reason, "size": size, "score": 0.0}
    base, target, known = ref["baseline"], ref["lower_bound"], ref["sota_ref"]
    if size < target:
        return {"n": n, "valid": False, "size": size, "score": 0.0,
                "reason": "verified artifact contradicts cited lower bound; audit required"}
    return {
        "n": n, "valid": True, "size": size, "baseline_size": base,
        "lower_bound": target, "sota_ref": known,
        "record_gap": size - known, "lower_bound_gap": size - target,
        "target_attained": size == target, "beats_known_record": size < known,
        "score": _normalized(float(-size), float(-base), float(-target)),
    }


def evaluate(build_covering) -> dict:
    per = [score_n(n, ref, build_covering) for n, ref in SIZES.items()]
    n_valid = sum(1 for r in per if r.get("valid"))
    return {
        "combined_score": float(np.mean([r["score"] for r in per])),
        "raw_score": -float(np.mean([r["size"] for r in per])) if n_valid == len(SIZES) else 0.0,
        "valid": 1.0 if n_valid == len(SIZES) else 0.0,
        "feasibility_rate": n_valid / len(SIZES),
        "beat_sota": bool(any(r.get("beats_known_record", False) for r in per)),
        "target_attainment_rate": sum(r.get("target_attained", False) for r in per) / len(SIZES),
        "per_n": per,
    }
