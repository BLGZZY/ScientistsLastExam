> Version note (2026-09-07, third local hardening): twelve systems (eight development, four held
> out) with varied tariff windows, two demand shapes, tank sizes, pump capacities and hidden
> two-frequency demand ripples whose phase constants no longer derive from the visible forecast
> phase. The anchor is one deterministic block-exchange sweep. Earlier sections describe the
> six-system set and are retained as history.

# Reference and admission record — ResilientPumpScheduling

Every number in the 2026-09-07 sections is produced by running code in this directory on this
tree. Reproduce the headline numbers with

```
python3 - <<'EOF'
import importlib.util
s=importlib.util.spec_from_file_location("ev","benchmarks/Engineering/ResilientPumpScheduling/verification/evaluator.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s2=importlib.util.spec_from_file_location("ref","benchmarks/Engineering/ResilientPumpScheduling/verification/reference.py")
r=importlib.util.module_from_spec(s2);s2.loader.exec_module(r)
print(m.evaluate(r.schedule_pumps))
EOF
```

## 1. Reference method

`verification/reference.py` is standalone and uses only public inputs and charged interfaces. It
solves public-demand-band convex dispatch on a conservative all-on commitment with linear
storage/pressure/ramp constraints and a switching epigraph. The evaluator's score-one anchor is
one deterministic block-exchange sweep (commitment blocks of width 2-4 flipped from all-on at
every start, convex dispatch per mask, cache-aware). No invented fallback anchor is used when the
reference fails; an invalid anchor is an infrastructure error. This remains a single-tank
surrogate, not a pipe-network solver.

## 2. Baseline and normalization (2026-09-07 twelve-system re-derivation)

| entry | development | held-out policy |
|---|---|---|
| shipped baseline (`solution.py`) | **0.000000** (valid=1) | 0.000 |
| runnable witness (`verification/reference.py`) | **0.640556** | 0.596813 |

Measured wall time on the 2026-09-07 builder machine (in-process `evaluate`): 62.1 s for the
baseline entry (includes all twelve anchor searches, cached thereafter) and 0.5 s for the
witness. The metadata envelope is 150 s and the wrapper timeout 300 s. On the previous
six-system set the 2026-09-07 maintainer-method retest measured 34.8 s baseline / 32.1 s
reference with witness 0.569407; the maintainer's host ran the baseline at 79 s (2.3x slower),
which is why the anchor was reduced from two block-exchange passes to one when the instance
count doubled. Two consecutive in-process evaluations of the witness are JSON-identical.

The true demand is now the public forecast times a hidden two-frequency ripple
(a1 sin(f1 t + seed) + a2 cos(f2 t + 1.7 seed)) with per-instance amplitudes, frequencies and
phase constants held only in the instance spec. The visible phase still shapes the published
forecast and tariff windows but no longer seeds the ripple, so the actual demand cannot be
reconstructed offline; ripple peaks stay inside the public +-4.5% band, keeping band-robust
public schedules feasible on actual demand (all twelve anchors and both normalization entries
verify on the hidden realization).

## 3. Capability comparisons and ablations

Run `python scripts/diagnose_pr9_engineering.py --output tmp/hardening/diagnostics.json`.
Historical: on the six-system set the convex all-on dispatch scored 0.569407 development /
0.493703 held out and the historical coordinate-move method was invalid on every development
instance. Current: the all-on witness scores 0.640556 development / 0.596813 held out on the
twelve-system set against the one-sweep anchor; discrete commitment is the measured headroom.

## 4. Shortcut probes

### 2026-09-07 shortcut re-audit (measured on the current tree)

Three families were implemented and run (`tmp/probe_pump.py` on the builder tree):

| family | development | held-out policy | valid |
|---|---|---|---|
| fixed-price-window charging (k cheapest hours, constant speed, k swept 12-22) | 0.000000 | 0.580927 | 0 |
| threshold commitment (run iff price < tau, constant speed, tau swept) | 0.000000 | 0.311717 | 0 |
| two-block commitment + public-band convex dispatch (widths 6-12, starts step 4) | **0.629644** | 0.783692 | 1 |
| runnable witness (all-on convex dispatch) | 0.640556 | 0.596813 | 1 |

The constant-speed families fail closed on development: no member is simultaneously tank-,
pressure- and terminal-feasible on every development system, which is itself a measured result
(scoring requires feasibility, not just cheap hours). The two-block commitment family comes
within 0.011 of the all-on witness on development but remains below it and well below the
anchor, so discrete commitment is genuine search headroom rather than a two-parameter shortcut.
These values are local diagnostics, not frozen benchmark evidence.

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before exposure, must
show that the first proposal does not reach the competent reference. No calibration or external
review is implied by these local code changes. Server-held worlds and independent model review
remain required.

## 6. Construction errors and revisions

2026-09-07 hardening: hidden two-frequency demand ripple decoupled from the visible phase
(previously seed = visible phase 0/3/7/11, offline-derivable); instances expanded from six to
twelve with four tariff-window structures, two demand shapes, and varied tank sizes, pump
capacities and ripple shapes; anchor reduced to one deterministic block-exchange sweep to keep
the twelve-instance runtime inside the evaluation budget; Task.md spoiler paragraph describing
the anchor heuristic deleted; price-window, threshold and two-block probes measured and pinned.
One held-out system (heldout_growth) was resized (tank maximum 1950 -> 1650 m3) after its
baseline failed the remote-pressure gate by 0.35 m.
2026-09-05 hardening: replaces tariff coordinate moves with constrained convex optimization. No
invented 0.92-baseline anchor is used when the reference fails; an invalid anchor is an
infrastructure error. Standalone references no longer import the hidden evaluator. Earlier
measurements below belong to the pre-hardening version and are retained only as history.

## 7. Robustness and reproducibility

Development and heldout metrics remain separate. The regression tests cover anchor feasibility,
mass conservation, commitment/auxiliary cost accounting, malformed submissions and determinism.
Formal Linux sandbox replay, global evidence refresh and independent scientific replication are
still pending. See the task card citations for background; the explicitly declared reduced model
is not certified by those publications.

## Historical pre-hardening record (obsolete scores)

# Reference witness

The normalization witness performed deterministic public-demand coordinate moves that reduce
costly-hour pumping while replaying public storage, pressure and ramp constraints. It never saw
forecast error or outage hours. It was a strong feasible witness rather than a global optimum
for the nonlinear energy model; in the historical version it defined score one and stronger
savings could exceed 1.0. EPANET/WNTR replication and frontier-model calibration are pending.
