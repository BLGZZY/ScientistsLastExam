# CompositeLaminateStacking — robust composite-laminate sequencing

## Task

Implement:

```python
def design_laminate(problem):
    return {"ply_angles_deg": [...]}
```

Choose the order of a fixed multiset of unidirectional plies. The number of plies, permitted
angles and exact count of every angle are supplied in `problem`. The returned laminate must be
symmetric and balanced and may not contain more than the published number of consecutive equal
plies (two on every shipped panel, a standard matrix-cracking limit). Values are checked
exactly; the oracle never repairs a submission.

The public model is classical laminate theory. The trusted evaluator assembles the `A` and `D`
matrices, searches simply-supported Navier modes `(m,n)=1..4` for buckling, and computes a
Tsai-Hill first-ply reserve factor at both ply faces over every supplied membrane and bending-moment load case. The smaller reserve is
the design quality. This is a deterministic screening abstraction; certification of a real panel
would require finite-element analysis, damage-tolerance checks and tests.

`combined_score` is the mean development reserve improvement above the shipped quasi-isotropic
baseline, normalized by the improvement of a stronger reproducible oracle search anchor. The
scale is floored at zero and uncapped. The evaluator separately reports held-out panels and a
sealed material/load-degradation check.

Important public keys are `ply_count`, `allowed_angles_deg`, `required_angle_counts`,
`maximum_consecutive_equal_plies`, `ply_thickness_m`, panel dimensions, `load_cases_n_per_m`, and
the orthotropic elastic/strength values in `material`.

Use deterministic NumPy/SciPy/standard-library CPU code. Do not read `verification/` or
`frontier_eval/`, access the network, or create processes.

References: Le Riche & Haftka, *AIAA Journal* 31(5), 951–956 (1993),
doi:10.2514/3.11710; Zhao, Sun & Silberschmidt, *Composite Structures* 149, 186–194 (2016),
doi:10.1016/j.compstruct.2016.01.052.

## Complete public input contract

Numeric values below are the first public example; per-instance arrays and coefficients vary.
All keys and shapes are part of the contract; forecasts contain exactly `horizon_steps` samples.

| Key | Type, shape or meaning |
|---|---|
| `ply_count` | 36 |
| `allowed_angles_deg` | array [4]; [-45, 0, 45, 90] |
| `required_angle_counts` | mapping; fields listed below |
| `required_angle_counts.-45` | 10 |
| `required_angle_counts.0` | 12 |
| `required_angle_counts.45` | 10 |
| `required_angle_counts.90` | 4 |
| `symmetric` | True |
| `balanced` | True |
| `maximum_consecutive_equal_plies` | 2 |
| `ply_thickness_m` | 0.000125 |
| `panel_length_m` | 1.2 |
| `panel_width_m` | 0.72 |
| `load_cases_n_per_m` | array [3, 3] |
| `moment_cases_n` | array [3, 3]; per-instance bending moments paired with the load cases |
| `material` | mapping; fields listed below |
| `material.e1_pa` | 132000000000.0 |
| `material.e2_pa` | 9200000000.0 |
| `material.g12_pa` | 4800000000.0 |
| `material.nu12` | 0.29 |
| `material.xt_pa` | 1450000000.0 |
| `material.xc_pa` | 1050000000.0 |
| `material.yt_pa` | 55000000.0 |
| `material.yc_pa` | 185000000.0 |
| `material.s_pa` | 72000000.0 |
| `model` | classical laminate A/D matrices; simply-supported Navier buckling modes 1..4; Tsai-Hill first-ply reserve |

## 关系与区别 / Relationship to nearby tasks

TrussWeightMinimization optimizes member sizes, HeatExchangerDesign optimizes thermal geometry, and ModalDamageAttribution infers damage. This task orders a fixed ply multiset and checks bending stiffness under loads; it does not identify damage or change laminate composition.

## Admission and reference scope

This package remains **candidate**. The metadata difficulty is a target, not a certified result. The runnable reference uses public inputs only. Local shortcut and ablation diagnostics are recorded in `references/known_best.md`; they do not replace clean Linux sandbox replay, independent domain review, Frontier-Eng overlap review or a frozen frontier-model calibration draw.

### Current reference and remaining difficulty

The runnable witness is a truth-blind seeded permutation-search method with adjacent-exchange
refinement over the symmetric half stack; the evaluator independently recomputes a stronger
structured-seed, multi-start full pair-exchange plus iterated-local-search anchor as score one.
Panels span 36–48 plies (half-stacks of 18–24 plies) with deliberately uneven angle mixes, so
the half-permutation counts exceed 1e8 everywhere and exhaustive screening is out of reach.
Every instance carries THREE paired load/moment cases whose optima conflict - an axial case, a
transverse case and a shear/twisting case - so no single clustered stacking is near-optimal on
all three; the run limit of two consecutive equal plies further removes tiled block patterns.
The hardened model evaluates both faces of every ply using membrane strain plus depth times
curvature, so material failure depends on order. Independent anisotropic buckling validation is
still pending. This calibration does not certify difficulty.

`moment_cases_n` has shape `[number_of_load_cases,3]`, with `[Mx,My,Mxy]` in N·m (moment per unit panel width), paired with `load_cases_n_per_m`. The symmetric laminate uses `strain=A^-1*N`, `curvature=D^-1*M` and global ply-face stress `Qbar*(strain+z*curvature)` before material-axis Tsai-Hill evaluation. The current Navier screening expression still neglects anisotropic mode coupling in buckling; external finite-element review is required.

## Frontier-Eng overlap comparison (2026-09-06)

同类不同题. Nearest catalog entries: ISCSO2015; ISCSO2023; TopologyOptimization; PyMOTOSIMPCompliance; EngDesign/YJ_02; EngDesign/YJ_03; DawnAircraftDesignOptimization. Order a fixed balanced symmetric ply multiset under manufacturing constraints to improve buckling and first-ply reserve. FE varies truss sections, continuum density, crack-tip material layout or aircraft geometry/mass. Fixed material composition and ply order are the decision space here; structural-design family overlap is disclosed.

See `.research/pr9_frontier_eng_overlap_2026-09-06.md` for the pinned 47-task paper and complete available repository catalog. The requested 95-entry source could not be reconciled with the available 78 rows (84 expanded tasks); source reconciliation and maintainer acceptance remain pending.
