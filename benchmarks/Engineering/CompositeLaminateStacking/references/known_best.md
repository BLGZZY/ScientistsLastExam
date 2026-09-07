# Reference and admission record — CompositeLaminateStacking

## Current model and corrected measurements (2026-09-08)

The normal-load sign audit found a scientific inconsistency: the buckling screen treated
positive `Nx,Ny` as compression, while the first-ply calculation interpreted the same positive
loads as tensile stress and selected tensile strengths. Both the oracle and standalone
reference now solve `strain=A^-1*[-Nx,-Ny,Nxy]`. Signed engineering shear is retained;
`Nxy=integral(tau_xy dz)`. Moments follow `M=integral(z*stress dz)` with tensile-positive
normal stress and are unchanged. See Nettles, [NASA RP-1351, sections III.C-D, pp. 15–17](https://ntrs.nasa.gov/citations/19950009349)
for force/moment resultants and the tensile-positive CLT convention.

Independent uniform 0-degree membrane limits now select `Xc,Yc` under compression and
`Xt,Yt` under tension. For example, 10 MPa longitudinal compression with `Xc=1.05 GPa`
must give a first-ply reserve of 105; the old code returned 145 from the tensile strength,
and the correction returns 105. Signed shear on uniform ±45-degree stacks also agrees
with independently rotated stresses. Sixteen parameterized cases check both implementations.
These tests establish constitutive consistency; they are not finite-element or domain certification.

No material coefficient, load, strength, normalization formula or search budget was changed.
The existing reference and anchor were rerun on the corrected model:

| entry | development | heldout | valid |
|---|---:|---:|---:|
| shipped baseline (`solution.py`) | 0.000000 | 0.000000 | 1 |
| full runnable reference (`verification/reference.py`) | 0.7398856153431821 | 0.8909542521094814 | 1 |

The reference's sealed-degradation metrics are 0.7622405484472773 development and
0.8779567780853759 heldout. Repeat evaluation is identical. One heldout instance reaches
1.0170274247147306 on the uncapped scale: the finite search anchor is not a global optimum.
A local macOS Python 3.12 / NumPy 1.26.4 run took 27.03 seconds for the baseline including
all six anchor searches, and another 0.46 seconds for the full reference with the anchor
cached. Metadata retains a 45-second envelope and the secure wrapper a 300-second candidate
timeout. Linux sandbox replay remains required; local in-process checks are not black-box evidence.

Reproduce current headline metrics from the repository root:

```python
import importlib.util

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

task = "benchmarks/Engineering/CompositeLaminateStacking"
ev = load("ev", f"{task}/verification/evaluator.py")
ref = load("ref", f"{task}/verification/reference.py")
print(ev.evaluate(ref.design_laminate))
```

## Reference and normalization methods

The standalone public-input reference uses thirteen seeded permutation starts followed by
up to eight adjacent-exchange sweeps of the symmetric half stack, stopping on convergence.
The independently computed score-one anchor uses tiled block-family seeds, a
24-permutation adjacency warm start, eight random starts each refined by full pair exchange,
and twelve iterated-local-search rounds. Neither search is claimed globally optimal or a
published record. These budgets were preserved through the sign correction.

Panels contain 36–48 plies, uneven fixed angle counts, three paired membrane/moment cases,
and a synthetic maximum run of two equal plies. Symmetry removes extension/bending coupling;
full A/D assembly and both-face stresses make bending and first-ply failure order-dependent.
The buckling formula is a Navier-inspired screen with an absolute-shear denominator term;
it omits anisotropic mode coupling and D16/D26 in buckling. Those terms still enter bending
stress. Independent high-fidelity validation remains pending.

## Historical construction and shortcut diagnostics — not current calibration

**Every number in this section predates the 2026-09-08 sign correction.** These historical
measurements cannot establish a current shortcut gap, admission threshold or runtime.
Updated shortcut sweeps and capability ablations are pending; they were not rerun merely
to preserve a previous score band. The algorithms in `tests/test_pr9_engineering_hardening.py`
and `scripts/diagnose_pr9_engineering.py` retain the diagnostic paths for remeasurement.

| historical 2026-09-07 entry | development | heldout |
|---|---:|---:|
| 13-start adjacent-exchange reference | 0.740840 | 0.874556 |
| tiled block/cluster family | 0.557119 | 0.820202 |
| 81-target lamination-parameter greedy family | 0.372152 | 0.597202 |

The old block-family gap of 0.184 and the claim that it closed the clustering shortcut are
superseded until the corrected oracle is calibrated. Likewise, the historical reference
scores 0.616 at ten starts and 0.784 at fourteen starts do not establish a scientific reason
to target a score band. The current thirteen-start method is retained, not weakened.
The historical 20.4-second anchor timing also belongs to the earlier oracle.

Earlier construction versions used smaller 16–24-ply panels (reference 0.732584 against a
900-start random anchor), then larger two-case panels with a run limit of three (reference
0.768732, clustered shortcut 0.992897), followed by the three-case/run-limit-two version
above. These are historical task changes, not comparable current evidence. The run limit
is a synthetic assumption; the former assertion that it is a universal matrix-cracking
constraint is withdrawn.

## Remaining admission work

The task remains `candidate`. No frozen frontier-model calibration draw or two-hour search
study has been run. Corrected-model shortcut/ablation measurements, Linux sandbox replay,
independent anisotropic buckling/first-ply review, Frontier-Eng overlap acceptance and
server-held confirmation panels remain required. Public procedural generation cannot
rule out contamination or heuristic transfer. The cited sources establish background
mechanics, not the validity or difficulty of this particular reduced benchmark.
