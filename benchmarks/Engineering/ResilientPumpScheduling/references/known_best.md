> Current version (2026-09-08): the standalone reference performs two complete
> commitment-search sweeps. It scores approximately **0.977067/0.989029** against
> the new independently runnable global-commitment feasible witness. The older
> all-on reference omitted the central discrete decision; its 0.630 score was not
> evidence of headroom. Physical constants and the score formula are unchanged.
> The current standard-method near-saturation remains a difficulty blocker.

# Reference and admission record — ResilientPumpScheduling

The 2026-09-07 sections below are historical local diagnostics. Reproduce the
current reference through the current evaluator with

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

`verification/reference.py` is standalone and uses only public inputs; this task has
no charged observation interface. Starting from all-on convex dispatch, it searches
commitment blocks of width 2–4, solves each mask with linear storage/pressure/ramp
constraints and a switching epigraph, and keeps the best strict improvement. It uses
two complete sweeps, warm starts and a mask cache. The current evaluator anchor instead
uses binary on/start variables and tangent underestimators of the public convex
hydraulic-energy function in a mixed-integer linear program. A single-threaded,
fixed-2000-node HiGHS search chooses a commitment mask; the original exact convex
dispatch then supplies a feasible schedule. The score normalizes by that schedule's
recomputed actual cost, never by the relaxation objective or its lower bound.
`verification/reference_global.py` independently reproduces this stronger witness
without oracle imports. See the [SciPy MILP API](https://docs.scipy.org/doc/scipy-1.13.1/reference/generated/scipy.optimize.milp.html)
for the solver interface and bounds terminology. No invented fallback anchor is used
when the reference fails; an invalid anchor is an infrastructure error. This remains a
single-tank surrogate, not a pipe-network solver.

## 2. Baseline and normalization

Historical-anchor capability ladder (2026-09-08, same twelve systems, prior four-sweep anchor):

| public method | development | held-out policy |
|---|---:|---:|
| all-on convex dispatch (historical reference) | 0.629968 | 0.566628 |
| one full commitment sweep | 0.974300 | 0.944775 |
| two sweeps (current reference, historical normalization) | 1.000000 | 1.000000 |
| four sweeps (unchanged oracle anchor) | 1.000000 | 1.000000 |

All four methods were valid. The two-sweep method already converges to the prior four-sweep anchor on these
instances. An independent global search improved five systems. Against the stronger
feasible anchor the two-sweep reference scores approximately **0.977067/0.989029**;
it was not weakened to make it fit a desired score band. The global witness's
feasible public-band costs lie within 0.0016 USD of the MILP tangent-relaxation
lower bounds on all twelve systems. Those are bounds for the public ±4.5% robust
class, not a certificate for every nominal-only submission or for real hydraulics.
The relaxation solved at 1–3 branch-and-bound nodes per system (0.07–6.47 local
seconds in the diagnostic). This independently demonstrates that the current
single-pump instances are close to standard-method solvability, not expert difficulty.
The source fixes the iteration budget, not a target score. These local diagnostics
must not be presented as a frozen Linux model draw.

### Historical 2026-09-07 twelve-system re-derivation

| entry | development | held-out policy |
|---|---|---|
| shipped baseline (`solution.py`) | **0.000000** (valid=1) | 0.000 |
| historical all-on witness | **0.629968** | 0.566628 |

Measured wall time on the 2026-09-07 builder machine (in-process `evaluate`): 41.1 s for the
baseline entry (includes all twelve repeated-sweep anchor searches, cached thereafter) and
0.2 s for the witness; warm-starting every dispatch from the incumbent schedule is what makes
the repeated sweeps affordable. The metadata envelope is 150 s and the wrapper timeout 300 s.
On the previous six-system set the 2026-09-07 maintainer-method retest measured 34.8 s
baseline / 32.1 s reference with witness 0.569407; the maintainer's host ran the baseline at
79 s (2.3x slower), which is why the declared envelope anticipates slower machines. Two
consecutive in-process evaluations of the witness are JSON-identical.

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
instance. Historical 2026-09-07: the all-on witness scored 0.629968 development / 0.566628 held out on the
twelve-system set against the repeated-sweep anchor; discrete commitment is the measured
headroom. A commitment ladder measured against the strengthened anchor: all-on dispatch
0.629968, best single width-2 flip 0.853, best single width-3 flip 0.914, best widths-2-4 flip
0.974300, full multi-sweep anchor 1.0 by definition.

## 4. Shortcut probes

### Historical 2026-09-07 shortcut re-audit

Three families were implemented and run (`tmp/probe_pump.py` on the builder tree):

| family | development | held-out policy | valid |
|---|---|---|---|
| fixed-price-window charging (k cheapest hours, constant speed, k swept 12-22) | 0.000000 | 0.531225 | 0 |
| threshold commitment (run iff price < tau, constant speed, tau swept) | 0.000000 | 0.264491 | 0 |
| two-block commitment + public-band convex dispatch (widths 6-12, starts step 4) | **0.607706** | 0.735082 | 1 |
| runnable witness (all-on convex dispatch) | 0.629968 | 0.566628 | 1 |

The constant-speed families fail closed on development: no member is simultaneously tank-,
pressure- and terminal-feasible on every development system, which is itself a measured result
(scoring requires feasibility, not just cheap hours).

**Historical failure record: the two-block commitment family sat only 0.022 below
the deliberately restricted all-on witness.** The reference restriction was removed
on 2026-09-08; the current two-sweep reference scores 1.0. The following account
explains the earlier mistaken attempt to select a reference by score band: An honest widening attempt was made: the anchor
was strengthened from one block-exchange sweep to repeated warm-started sweeps (which lowered
the probe from 0.629644 to 0.607706), and witness designs between all-on dispatch and one
commitment flip were measured - best single width-2 flip 0.853, width-3 flip 0.914,
widths-2-4 flip 0.974, tariff-window flips 0.944-0.970. The commitment landscape is a cliff:
every bounded-commitment witness lands at 0.85-0.97, far above the 0.8 admission ceiling, and
the all-on witness lands at 0.63, so no reference design reaches the suggested 0.70 target
band while staying under 0.8. The gap cannot honestly exceed ~0.05 by witness or anchor
design; widening it further would require redesigning the cost structure (for example
instance-specific startup costs that make single flips much less effective), which is an
owner decision, not a unilateral builder change. These values are local diagnostics, not
frozen benchmark evidence.

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before exposure, must
show that the first proposal does not reach the competent reference. No calibration or external
review is implied by these local code changes. Server-held worlds and independent model review
remain required.

## 6. Construction errors and revisions

2026-09-08 review: restored commitment search to the standalone reference rather than
keeping an all-on method because it happened to score in the requested 0.5–0.8 band.
The restored two-sweep reference tied the old four-sweep anchor on every system.
An independent mixed-integer global search subsequently found better feasible costs
and now supplies the score-one anchor; the reference remains near-saturated at
0.977/0.989. The anchor is an executable witness, not an invented score constant. The prior
in-band score was an omitted capability, not scientific headroom. The task still
needs stronger instance/model design and clean calibration before expert-difficulty
claims; no rescaling or arbitrary coefficient changes were made.

The same review restored the complete public physical contract: the actual ±4.5%
demand bound, pressure equation, hydraulic power, auxiliary electricity, initial
startup and speed-variation charge. These were already in the evaluator, but their
absence from the candidate-visible description introduced hidden-model difficulty.
All equations and scores are unchanged. Historical local runtimes do not guarantee
the current whole-evaluation Linux budget.


2026-09-07 hardening (first pass): hidden two-frequency demand ripple decoupled from the
visible phase (previously seed = visible phase 0/3/7/11, offline-derivable); instances expanded
from six to twelve with four tariff-window structures, two demand shapes, and varied tank
sizes, pump capacities and ripple shapes; Task.md spoiler paragraph describing the anchor
heuristic deleted; price-window, threshold and two-block probes measured and pinned.
2026-09-07 admission-bar fix: anchor strengthened to repeated warm-started block-exchange
sweeps to convergence (runtime held at 41.1 s by warm starts); witness deliberately kept at
all-on dispatch after measuring that every bounded-commitment witness lands at 0.85-0.97,
outside the admission band; the 0.022 witness-to-two-block gap documented above as an explicit
owner-decision risk.
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
