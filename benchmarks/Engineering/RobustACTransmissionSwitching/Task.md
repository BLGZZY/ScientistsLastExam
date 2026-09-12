# RobustACTransmissionSwitching — secure a nonlinear AC grid by switching lines

## Scientific setting

Transmission switching can relieve loop-flow congestion, but each opening changes a nonlinear
alternating-current network and may make a later outage unsafe. This task asks for one preventive
topology and one participation factor that remain feasible across a frozen set of load changes and
single-line contingencies. The trusted callback solves the polar AC power-flow equations; a plan is
feasible only if every scenario satisfies active and reactive balance, voltage bounds, generator
limits, connectivity, and apparent-power thermal limits.

This is a small, deterministic surrogate of robust security-constrained AC optimal transmission
switching. It tests topology screening and continuous/discrete search, not control-room readiness.

## Your task

Implement:

```python
def optimize_switching(problem, evaluate_plan):
    result = evaluate_plan({
        "open_lines": ["l12"],
        "generator_1_share": 0.65,
    })
    return {"plan_id": result["plan_id"]}
```

`open_lines` must contain at most `maximum_open_lines` distinct switchable branch IDs.
`generator_1_share` is the fraction of total active load scheduled at bus 1; the slack generator
at bus 0 supplies the remainder and AC losses. The value must lie inside
`generator_1_share_bounds`.

Each call costs one of `evaluation_budget_calls == 48` units and returns:

| key | meaning |
|---|---|
| `plan_id` | opaque ID that may be returned as the final answer |
| `feasible` | whether every frozen operating scenario passes all checks |
| `robust_cost` | worst-scenario quadratic generation cost plus switching charge; `1e6` if infeasible |
| `worst_thermal_loading` | maximum apparent-power flow divided by its branch limit |
| `minimum_voltage_pu`, `maximum_voltage_pu` | voltage extrema over all scenarios |
| `budget_cost`, `remaining_budget` | charged units for this call and units left |

Repeated calls cost again. Invalid calls and overruns fail the world even when caught. Return
exactly `{"plan_id": ...}` using an ID from the current callback session.

## AC model and evaluation

For every active line with series admittance `y_ij = 1 / (r_ij + j x_ij)`, the oracle assembles
`Y` and solves

```text
S_i = V_i conj((Y V)_i)
```

in polar coordinates. Bus 0 is slack, bus 1 is PV, and buses 2–4 are PQ. Both line directions are
checked against the published apparent-power limits. The frozen scenario set lies within the
published load-scale interval and contains the published number of single-line outages.

`combined_score` is the mean development reduction in worst-case operating cost, normalized so
the shipped fixed-topology policy is zero and the 48-call single-switch screen/refine witness is
one. The upper side is not clipped: a better double-switch or participation strategy can score
above one. Feasibility rate is search-visible; source-held policy score and per-world diagnostics
remain evaluator-only.

## Inputs the candidate receives

Every `problem` key is part of the public contract:

| key | meaning |
|---|---|
| `bus_count` | number of buses |
| `slack_bus` | voltage-angle reference and balancing generator bus |
| `participating_generator_bus` | bus controlled by `generator_1_share` |
| `base_active_loads_pu` | active load at buses 1–4, in per unit |
| `load_power_factor` | common lagging load power factor |
| `branches` | branch `id`, endpoint buses, per-unit resistance/reactance, thermal limit, and switchability |
| `generator_0_cost`, `generator_1_cost` | `[constant, linear, quadratic]` cost coefficients |
| `generator_active_bounds_pu` | active limits for generators 0 and 1 |
| `generator_reactive_bounds_pu` | reactive limits for generators 0 and 1 |
| `generator_1_share_bounds` | allowed participation-factor interval |
| `voltage_bounds_pu` | allowed voltage-magnitude interval |
| `maximum_open_lines` | preventive switching budget |
| `evaluation_budget_calls` | callback-call budget |
| `contingency_count` | number of outage scenarios |
| `load_scale_bounds` | minimum and maximum frozen load multipliers |

## Relationship to nearby tasks

`TrussWeightMinimization` and `HeatExchangerDesign` are continuous engineering design problems
under one simulator. `DistributionNetworkTopology` (on an unmerged candidate branch) is Boolean
tomography of broken water pipes. This task instead searches a mixed discrete/continuous control
policy, and each candidate must survive nonlinear AC physics across multiple electrical-grid
contingencies. It does not duplicate any Frontier-Eng task listed in the repository's overlap
audit.

## Rules and scope

- Only edit `solution.py`; keep `optimize_switching(problem, evaluate_plan)`.
- Deterministic CPU code only. NumPy, SciPy, and the standard library are available.
- No network or process creation; do not read `verification/` or `frontier_eval/`.
- The five-bus systems are deliberately synthetic and omit protection, dynamics, stability,
  harmonics, transformer controls, unit commitment, and cascading failure. A high score is an
  algorithmic result, not an operational switching recommendation.

References: Fisher et al., *IEEE Transactions on Power Systems* 23 (2008), DOI
`10.1109/TPWRS.2008.922256`; Bienstock and Verma, *Operations Research Letters* 47 (2019), DOI
`10.1016/j.orl.2019.08.009`.

