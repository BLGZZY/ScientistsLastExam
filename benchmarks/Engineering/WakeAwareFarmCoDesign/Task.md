# WakeAwareFarmCoDesign — wind-farm layout and yaw co-design

Implement `design_wind_farm(problem)` and return a mapping containing `layout_xy_m` with shape
`[turbine_count,2]` and `yaw_by_direction_deg` with one yaw angle per public wind direction and
turbine. Every turbine must lie inside the rectangular boundary, respect minimum Euclidean
spacing, and stay within the yaw limit. Invalid designs are rejected, never repaired.

## Complete objective (the score is a function of exactly what follows)

For each public wind direction `d` (angle `θ_d`, speed `u_d`, probability `p_d`), rotate the
layout into wind axes: `down = x·cosθ + y·sinθ`, `cross = −x·sinθ + y·cosθ`. Process turbines in
order of increasing `down`. For turbine `j`, sum contributions from every turbine `i` strictly
upwind of it (`dx = down_j − down_i > 0`), with the yaw angle `γ_i = yaw_by_direction_deg[d, i]`
in radians:

```
σ      = R + k·dx                     with R = rotor_diameter_m/2, k = wake_expansion_public
center = cross_i + 0.055·dx·sin(γ_i)   (yaw-induced wake displacement)
δ_i    = 2a·cos²(γ_i) / (1 + k·dx/R)² · exp(−0.5·((cross_j − center)/σ)²)
a      = 0.5·(1 − sqrt(1 − Ct)),  Ct = thrust_coefficient
```

The deficits superpose in root-sum-square and are floored:

```
u_eff,j = u_d · max(0.18, 1 − sqrt(Σ_i δ_i²))
```

Turbine power applies a `cos^1.88` yaw self-loss and a rated cap:

```
P_j = min(0.5·ρ·π·R²·Cp·u_eff,j³·cos(γ_j)^1.88, 3.6e6 W)      ρ = air_density_kg_m3, Cp = power_coefficient
```

Annual value and the structural-load proxy accumulate over the rose:

```
V = Σ_d p_d · (Σ_j P_j) · 8760 / 1e9                (GWh)
L = Σ_d p_d · mean_j( (u_eff,j/u_d)² · (1 + 0.22·|γ_j|) )
```

The objective the score depends on is `value = V − 0.20·L`. Development scoring evaluates
exactly this public model with the public `wake_expansion_public`. `combined_score` is the
improvement of `value` over a regular zero-yaw grid, normalized by the improvement of a
stronger reproducible oracle search; the scale is floored at zero and uncapped. Held-out farm
geometries are scored separately, and a sealed robustness tier re-evaluates the design under a
wider wake expansion, a rotated wind rose and a turbulence-value penalty; neither controls
`combined_score`.

The oracle is a reduced engineering wake model, not wind-tunnel or field truth. Before admission,
the trajectories and rankings must be independently reproduced in a pinned FLORIS version and
reviewed by a wind-energy specialist.

Use only the supplied problem mapping and deterministic NumPy/SciPy/standard-library CPU code.
No network, process creation, or reads from `verification/` and `frontier_eval/`.

References: Fleming et al., *Journal of Physics: Conference Series* 1618, 022028 (2020),
doi:10.1088/1742-6596/1618/2/022028; NREL FLORIS documentation.

## Complete public input contract

Numeric values below are the first public example; per-instance arrays and coefficients vary.
All keys and shapes are part of the contract; forecasts contain exactly `horizon_steps` samples.

| Key | Type, shape or meaning |
|---|---|
| `turbine_count` | 9 |
| `boundary_width_m` | 1900.0 |
| `boundary_height_m` | 1700.0 |
| `rotor_diameter_m` | 120.0 |
| `minimum_spacing_rotor_diameters` | 4.0 |
| `wind_directions_deg` | array [12] |
| `wind_speeds_m_s` | array [12] |
| `wind_probabilities` | array [12] |
| `yaw_limit_deg` | 25.0 |
| `air_density_kg_m3` | 1.225 |
| `power_coefficient` | 0.44 |
| `thrust_coefficient` | 0.8 |
| `wake_expansion_public` | 0.055 |
| `contract` | return layout_xy_m [n,2] and yaw_by_direction_deg [12,n] |

## 关系与区别 / Relationship to nearby tasks

ResilientPumpScheduling optimizes time allocation, CompositeLaminateStacking optimizes discrete order, and DiffractionGratingDesign optimizes optical propagation. This task jointly chooses spatial turbine positions and wind-direction-dependent yaw; its wake model is a reduced screening model.

## Admission and reference scope

This package remains **candidate**. The metadata difficulty is a target, not a certified result. The runnable reference uses public inputs only. Local shortcut and ablation diagnostics are recorded in `references/known_best.md`; they do not replace clean Linux sandbox replay, independent domain review, Frontier-Eng overlap review or a frozen frontier-model calibration draw.

### Current reference and remaining difficulty

The runnable witness is a truth-blind seeded layout-screening, coordinate yaw-search and feasible
layout-refinement method; the evaluator independently recomputes a stronger multi-start,
multi-scale anchor as score one. The witness reaches the 0.5–0.8 development band on the current
panels; denser restarts, finer refinement scales and joint layout-yaw moves are the measured
headroom. Cross-model robustness and independent FLORIS validation remain open. This calibration
does not certify difficulty.

## Frontier-Eng overlap comparison (2026-09-06)

无. Nearest catalog entries: UAVInspectionCoverageWithWind; DawnAircraftDesignOptimization. Joint static turbine locations and directional yaw optimize farm value with wake interactions and wind-rose transfer. FE optimizes flight coverage in wind or aircraft mass/geometry, without turbine-to-turbine wakes or wind-farm yield.

See `.research/pr9_frontier_eng_overlap_2026-09-06.md` for the pinned 47-task paper and complete available repository catalog. The requested 95-entry source could not be reconciled with the available 78 rows (84 expanded tasks); source reconciliation and maintainer acceptance remain pending.
