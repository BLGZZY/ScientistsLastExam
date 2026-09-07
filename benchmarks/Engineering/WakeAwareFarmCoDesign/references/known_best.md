# Reference and admission record — WakeAwareFarmCoDesign

Every number in the 2026-09-07 sections below is produced by running code in this directory on
this tree; nothing is copied from a table. Reproduce with

```
python3 - <<'EOF'
import importlib.util
s=importlib.util.spec_from_file_location("ev","benchmarks/Engineering/WakeAwareFarmCoDesign/verification/evaluator.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s2=importlib.util.spec_from_file_location("ref","benchmarks/Engineering/WakeAwareFarmCoDesign/verification/reference.py")
r=importlib.util.module_from_spec(s2);s2.loader.exec_module(r)
print(m.evaluate(r.design_wind_farm))
EOF
```

## 1. Reference method

`verification/reference.py` is standalone and uses only public inputs and charged interfaces. It
uses ten seeded layout starts, coordinate yaw search and one 80 m feasible layout-refinement
scale; the evaluator independently runs the stronger 180-start, three-scale anchor. It is a
method witness, not independent high-fidelity verification. Cross-model robustness, restarts and
independent FLORIS validation remain open.

## 2. Baseline and normalization (2026-09-07 public-expansion re-derivation)

Development scoring now evaluates the PUBLIC wake expansion (`wake_expansion_public` = 0.055)
exactly as published in Task.md; the previous 0.061 development variant was removed because the
score must be computable from the public contract. The widened (0.074), +7°-rotated,
turbulence-penalized variant is a robustness tier only and never controls `combined_score`.

| entry | development | held-out policy | robustness tier |
|---|---|---|---|
| shipped grid baseline (`solution.py`) | **0.000000** (valid=1) | 0.000 | 0.000 |
| runnable witness (`verification/reference.py`) | **0.741503** | 0.738009 | 0.613817 (mean) |

Measured wall time on the 2026-09-07 builder machine (in-process `evaluate`): 12.6 s for the
baseline entry (includes all six anchor searches) and 10.5 s for the witness; the wrapper timeout
stays 300 s. The scale is floored at zero and uncapped; additional starts and finer 40/20 m
layout moves remain the measured headroom.

## 3. Capability comparisons and ablations

Run `python scripts/diagnose_pr9_engineering.py --output tmp/hardening/diagnostics.json`.
On the current dirty macOS tree (pre-revision, hidden-expansion scoring) ten layout starts,
coordinate yaw and one 80 m layout-refinement scale scored `0.741392` development and the
historical yaw-only construction `0.490932`; the added layout refinement and restarts contributed
`0.250460`. These pre-revision numbers are retained as history; the current public-expansion
numbers are those in section 2.

## 4. Shortcut probes

### 2026-09-07 shortcut re-audit (measured on the current tree)

Three low-dimensional layout families were implemented and run against the current evaluator
(`tmp/probe_wake.py` on the builder tree; equal-arc perimeter spacing for boundary packing, six
ring offsets; uniform yaw swept over {-22,-14,-7,0,7,14,22} degrees for the fixed-yaw grid):

| family | development | held-out policy | robustness tier |
|---|---|---|---|
| row-staggered grid, zero yaw | 0.137746 | 0.171621 | 0.201601 |
| equal-arc boundary packing, zero yaw | 0.000000 (valid=0) | 0.097734 | 0.203067 |
| regular grid, uniform fixed yaw (best sweep) | 0.000000 | 0.000000 | 0.000000 |
| runnable witness | **0.741503** | 0.738009 | 0.613817 |

Boundary packing fails closed on development: with equal arc-length spacing the perimeter of the
denser farms cannot host all turbines at the minimum spacing, so no member of the family is
valid on two of the four development systems (an earlier draft silently fell back to a staggered
grid and scored 0.140246; that fallback is not boundary packing and was removed). No measured
structured layout family comes near the witness, so the remaining reference-to-anchor gap is
genuine joint layout-yaw search, not a low-dimensional shortcut.

Earlier probe record: the regular-grid zero-yaw baseline scores zero and the historical yaw-only
search reached `0.490932` under the pre-revision hidden-expansion scoring. These values are local
diagnostics, not frozen benchmark evidence.

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before exposure, must
show that the first proposal does not reach the competent reference. No calibration or external
review is implied by these local code changes. Server-held worlds and independent model review
remain required.

## 6. Construction errors and revisions

2026-09-07 hardening: development scoring moved to the public wake expansion; the complete
objective (per-turbine Gaussian/Jensen deficit, RSS superposition with 0.18 floor, cos^1.88 yaw
self-loss, 3.6 MW cap, 0.20 structural-load penalty) was written into the public Task.md so the
score is a function of published information only; row-stagger, boundary-packing and fixed-yaw
shortcut families were measured and pinned.
2026-09-05 hardening: adds layout refinement after yaw selection. Cross-model robustness,
restarts and independent FLORIS validation remain open.
Standalone references no longer import the hidden evaluator. Earlier measurements belong to the
pre-hardening version and are retained only as history.

## 7. Robustness and reproducibility

Development and heldout metrics remain separate. Two consecutive in-process evaluations of the
witness are JSON-identical. Formal Linux sandbox replay, global evidence refresh and independent
scientific replication are still pending. See the task card citations for background; the
explicitly declared reduced model is not certified by those publications.

## Historical pre-hardening record (obsolete scores)

The witness screens 180 deterministic valid jitters around a staggered grid and then performs
coordinate yaw refinement using only the public wake model and wind rose. It is not a global
layout or yaw optimum, so the historical normalization remained uncapped above it. FLORIS cross-model rankings and
frontier-model calibration are pending.
