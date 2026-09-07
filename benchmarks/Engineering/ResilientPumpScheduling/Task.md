# ResilientPumpScheduling — tariff-aware water-distribution operation

Implement `schedule_pumps(problem)` and return `{"pump_speed": [...]}` with one speed in `[0,1]`
for each of 24 hourly intervals. A running pump must be at or above
`minimum_operating_speed`; zero means off. The ramp limit applies between consecutive running
hours, with startup/shutdown completed inside one hourly interval. Each on-run, including the
last run in the horizon, must last at least `minimum_run_hours`; the initial pump is off.

The frozen extended-period oracle balances forecast-error-adjusted demand, pump inflow and tank
storage. It computes pump energy from flow, static head, the speed-dependent head curve and
wire-to-water efficiency. Every nominal hour must keep tank volume within bounds and remote-node
pressure above 20 m; terminal storage must recover to its published target. Submissions are
rejected rather than clipped or repaired.

`combined_score` is development energy-cost savings above a conservative constant-speed schedule,
normalized by the savings of a stronger reproducible feasible commitment-dispatch witness. The scale
is floored at zero and uncapped. Held-out systems, 12% demand growth and a four-hour peak-period
pump outage are reported separately and cannot be selected against. The true demand differs from
the published forecast by a small hidden realization; a schedule robust to the published demand
band stays feasible on it.

## Complete nominal model

Each hourly actual demand lies in `[0.955, 1.045]` times the corresponding public
`demand_forecast_m3_h` value. The realization is hidden; this bound is part of the
contract. For hour `h`, speed `s_h` gives flow `q_h = pump_capacity_m3_h * s_h`
in m³/h. With one-hour intervals, the end-of-hour storage is
`V_h = V_(h-1) + q_h - demand_h`. At that end-of-hour storage, the reduced pressure
model is:

```
tank_head_m = 43 + 10 * (V_h - tank_minimum_volume_m3)
                        / (tank_maximum_volume_m3 - tank_minimum_volume_m3)
remote_pressure_m = tank_head_m - 20 - 0.00023 * demand_h**2
```

The oracle requires storage within its public bounds and `remote_pressure_m >= 20`
at every hour, and terminal storage at least `terminal_minimum_volume_m3`.
The head-loss coefficient is a synthetic reduced-model coefficient, with units
chosen for demand in m³/h; there is no hidden pipe-network solve.

```
pump_head_m = pump_static_head_m + pump_speed_head_coefficient_m * s_h**2
power_kw = 9.81 * q_h * pump_head_m / (3600 * wire_to_water_efficiency)
```

While running, add `running_auxiliary_power_kw`. Total cost is the sum of hourly
electricity cost, plus `0.035 * sum(abs(s_h - s_(h-1)))` over the 23 within-horizon
transitions, plus `startup_cost_usd` for every off-to-on event, including the initial
start from off. The variation coefficient is USD per unit speed change. The hidden
demand-growth and outage checks are separate diagnostics and do not affect this
nominal objective. These equations specify the score's physical abstraction; they
do not prescribe a scheduling algorithm.

This compact model preserves the storage, tariff, pressure and outage couplings needed for a local
benchmark. It is not an EPANET hydraulic certification. Engineering claims require replay in a
frozen EPANET/WNTR network and independent water-systems review.

Public keys include the demand and tariff series, pump capacity/head/efficiency, tank limits,
terminal target and ramp limit. Use deterministic NumPy/SciPy/standard-library CPU code only; no
network, process creation, or reads from `verification/` and `frontier_eval/`.

References: EPA, *EPANET 2.2 User Manual*, EPA/600/R-20/133 (2020); Guidolin et al.,
*Drink. Water Eng. Sci.* 7, 53–63 (2014), doi:10.5194/dwes-7-53-2014.

## Complete public input contract

Numeric values below are the first public example; per-instance arrays and coefficients vary.
All keys and shapes are part of the contract; the demand and tariff arrays each contain
exactly `horizon_hours` samples at the supplied one-hour time step.

| Key | Type, shape or meaning |
|---|---|
| `horizon_hours` | 24 |
| `time_step_hours` | 1.0 |
| `demand_forecast_m3_h` | array [24] |
| `electricity_usd_kwh` | array [24] |
| `pump_capacity_m3_h` | 165.0 |
| `pump_static_head_m` | 36.36 |
| `pump_speed_head_coefficient_m` | 18.0 |
| `wire_to_water_efficiency` | 0.78 |
| `tank_initial_volume_m3` | 820.0 |
| `tank_minimum_volume_m3` | 310.0 |
| `tank_maximum_volume_m3` | 1510.0 |
| `terminal_minimum_volume_m3` | 820.0 |
| `maximum_speed_change` | 0.55 |
| `minimum_operating_speed` | 0.65; stable operating range when on |
| `minimum_run_hours` | 2; minimum consecutive on duration |
| `running_auxiliary_power_kw` | 2.5; electrical auxiliary draw while on |
| `startup_cost_usd` | 0.30 per off-to-on event, including the initial start |
| `contract` | zero or stable operating speed, minimum run and on-to-on ramp rules |

## 关系与区别 / Relationship to nearby tasks

GroundwaterRemediationDesign chooses remediation wells and an archive. This task submits a 24-hour open-loop pump schedule for a single storage system; it has no pipe-network hydraulic solve.

## Admission and reference scope

This package remains **candidate**. The metadata difficulty is a target, not a
certified result. The runnable reference uses public inputs only. Reference methods,
calibration measurements, shortcut probes and ablation diagnostics are recorded in
the maintainer-facing `references/known_best.md`, which is not served to candidates.
They do not replace clean Linux sandbox replay, independent domain review,
Frontier-Eng overlap review or a frozen frontier-model calibration draw.

### Public model scope

The cost adds running auxiliary electricity at the current tariff and the startup charge to
hydraulic electricity and speed variation. This creates a genuine discrete commitment decision:
an all-on continuous optimum can lose to a schedule that stores water and shuts down at expensive
hours. Minimum speed, run time and auxiliary load are synthetic equipment assumptions requiring
domain review. The model still has only one pump and one tank, and outage resilience remains a
separate reported diagnostic rather than part of the nominal objective.

## Frontier-Eng overlap comparison (2026-09-06)

同类不同题. Nearest catalog entries: BatteryFastChargingProfile; BatteryFastChargingSPMe; EV2GymSmartCharging; finite_horizon_dp. A 24-hour on/off and pump-speed plan obeys minimum run, pressure, tank storage and terminal recovery under demand/outage scenarios. FE schedules electrical charge or stock replenishment. Water storage dynamics and service constraints differ, though constrained energy/storage scheduling is shared.

See `.research/pr9_frontier_eng_overlap_2026-09-06.md` for the pinned 47-task paper and complete available repository catalog. The requested 95-entry source could not be reconciled with the available 78 rows (84 expanded tasks); source reconciliation and maintainer acceptance remain pending.
