# EllipticCurveRecovery — recover curve coefficients from prime point counts

## Scientific setting

An elliptic curve y^2 = x^3 + ax + b with integer coefficients is studied through
its reduction modulo primes: for a chosen prime p, the exact number of points on
the reduced curve over the finite field F_p is an obtainable measurement.
Coefficients live in a bounded integer window. Not every world is such a curve:
two break the elliptic premise — a singular cubic and a genus-two quartic — and
their measurements are not reproducible by any admissible pair (a, b).

## Your task

```python
def recover_curve(problem, count_points, budget_units):
    """Return {"a": int, "b": int within public bounds, "abstain": bool,
               "confidence": float in [0,1]}."""
```

`problem` is a mapping with the keys

```text
curve_family      y^2 = x^3 + a*x + b, |a|,|b| <= 1200, nonzero discriminant
prime_list        the queryable primes
cost_tiers        prime <= 100 costs 1, <= 1000 costs 2, otherwise 3
budget_units      8
answer_semantics  the oracle returns #E(F_p) exactly
refusal_note      singular cubics and genus-two quartics must be refused
```

`count_points(prime)` charges by tier and returns `{prime, point_count,
budget_cost}`. Overspending or unknown primes invalidate the world even when
caught.

## Evaluation

- `combined_score` is development coefficient recovery above the always-abstain
  baseline: exp(-6 x normalized total absolute error of a and b), multiplied on
  supported curves by `1 - 0.25 * budget_used / 8`. Recovery that spends less
  budget therefore retains more score.
- Singular and genus-two worlds score refusal only; abstaining scores one and any
  coefficient claim scores zero. Refusal credit is not efficiency-weighted, so an
  evidence-backed refusal is not penalized relative to blind abstention.
- Intrinsic and efficiency-adjusted recovery, evidence efficiency, false discovery rate, correct refusal rate and discovery coverage are reported
  with denominators; a full abstention scores exactly zero.
- `robustness_score` repeats the audit on held-out curves and failures.

The aggregate efficiency diagnostics are `development_evidence_efficiency_score` and
`heldout_evidence_efficiency_score`; per-world rows also retain
`intrinsic_mechanism_score`, `mechanism_score`, `evidence_efficiency_score` and
`budget_used`. Split membership and hidden truth are never candidate inputs.

This is exact integer arithmetic, not a numerical experiment.

## Rules

- Only edit `solution.py`; keep the complete function signature.
- Deterministic Python/NumPy/SciPy/stdlib code only; no network or process creation.
- Do not read `verification/` or `frontier_eval/`.
- Oracle errors and overspending invalidate the world even when caught.
- Use `sle.contract_lint` for free local shape checks before returning an inference.

Reference: Silverman, *The Arithmetic of Elliptic Curves*, ISBN `9780387094939`.

## 关系与区别 / Relationship to nearby tasks

SequenceLawRecovery infers recurrences from integer terms; ExactIdentityEvidence
certifies identities from purchasable digits. This task inverts exact arithmetic
objects — point counts over finite fields — under a prime-query budget, with
refusal worlds that break the curve family itself.

## Admission and reference scope

This package remains **candidate**. The runnable reference uses public inputs
only; its method is recorded in `references/known_best.md`, which is
maintainer-facing and not served to candidates. Local shortcut and ablation
diagnostics there do not replace clean Linux sandbox replay, independent review
or a frozen frontier-model calibration draw.

## Frontier-Eng overlap comparison (2026-09-07)

无. Nearest catalog entries: AES-128 CTR; SHA-256; SHA3-256. Query finite-field point counts at chosen primes and recover an integer elliptic-curve coefficient pair or refuse. FE implements symmetric cryptographic throughput, with no arithmetic-geometry inverse problem.

See `.research/elliptic_curve_recovery_frontier_eng_overlap_2026-09-07.md` for
the task-specific comparison against the pinned paper and available repository
catalog. Independent mathematics review and maintainer acceptance remain pending.
