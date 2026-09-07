# Reference and admission record — PermutationFlowShop

## 1. Reference method

**Current (2026-09-08):** the runnable reference performs **128** fixed ILS cycles,
including perturbation, complete insertion descent, acceptance and periodic elite
restart. A direct local evaluation with vectorized independent insertion positions
returned **0.9827586206896551 development / 0.9638888888888889 held out**, valid=1,
in **141.1 seconds** while other diagnostics shared the CPU. Integer recurrence and
tie order are unchanged, and insertion values are checked against brute force.
The declared evaluation envelope is now 180 seconds with the existing 300-second
candidate timeout. Clean Linux timing remains required.


`verification/reference_solver.py` is NEH construction refined by seeded iterated
local search: three-random-insertion perturbations, best-insertion descent with
better-or-equal acceptance, restarts from the elite, and the accelerated insertion
evaluation (prefix completion tables and suffix tail tables, O(machines) per candidate
position — verified against brute-force makespans on thirty random cases). The
descent at 3000 iterations with seed 0 freezes the record makespans. The former
400-iteration default took 236 seconds on the maintainer's host; the shipped runnable
reference was reduced to one cycle on 2026-09-06. That omitted adequate search
effort and is superseded by the 128-cycle reference restored on 2026-09-08. The frozen record is
not a claimed optimum. The small instance sizes alone do not establish expert difficulty.
A local direct evaluation of the runnable reference took 0.93 seconds on 2026-09-06.
The 2026-09-07 maintainer-method retest (in-process `evaluate` on both entries) measured
0.71 s for the reference and 0.24 s for the baseline, with 0.636364 development and the
baseline exactly zero. These are historical runtime/score measurements, not difficulty approval; the
budget now also appears in TASK_CARD.yaml as `evaluation_budget`.

## 2. Baseline and normalization

Zero is anchored at the NEH construction, computed inside the oracle (the as-given
order is so weak that any competent construction closes over ninety percent of the
gap, which would flatten the scale). The shipped `solution.py` (as-given order) scores
exactly `0.000000` after flooring, as does NEH itself by construction. The frozen
3000-iteration record anchors score one per instance:

| instance | size | as-given baseline | NEH zero anchor | witness |
|---|---|---:|---:|---:|
| pfs_44011 | 20x5 | 1586 | 1226 | 1180 |
| pfs_44017 | 30x10 | 2686 | 2211 | 2182 |
| pfs_44023 | 50x5 | 3469 | 3033 | 3023 |
| pfs_44029 | 50x10 | 3983 | 3067 | 2979 |
| pfs_44037 (held-out) | 20x5 | 1445 | 1240 | 1222 |
| pfs_44041 (held-out) | 30x5 | 2161 | 1749 | 1734 |
| pfs_44043 (held-out) | 50x10 | 3763 | 3204 | 3012 |

Beating the frozen record scores above one with no cap.

## 3. Capability comparisons and ablations

| variant | development | held-out |
|---|---:|---:|
| frozen record (3000 iterations) | 1.000 | 1.000 |
| current runnable reference (128 iterations) | 0.982759 | 0.963889 |
| 256 iterations | 0.982759 | 0.963889 |
| 64 iterations | 0.940145 | 0.956944 |
| 20 iterations | 0.929 | 0.957 |
| 2 iterations | 0.849 | 0.805 |
| historical restricted reference (1 iteration) | 0.636 | 0.773 |
| NEH construction only | 0.000 | 0.000 (zero anchor) |

These are historical local debugging measurements, not frozen benchmark evidence.
Increasing an iteration count measures additional search effort, not an independent
scientific capability ablation.

## 4. Shortcut probes

NEH alone and the shipped baseline both score zero under the current normalization.
The previous statement that NEH scored roughly 0.85 referred to an older scale and
was stale. A permutation artifact does not exempt a task from shortcut searches: job
priority rules, parameterized insertion/tie-breaking, bounded ILS and multi-start
methods remain relevant. The recorded two-iteration standard method already exceeds
the one-iteration runnable reference (0.849 vs 0.636 development). Twenty iterations
reach 0.929/0.957. The 2026-09-08 review therefore restored a competent 128-cycle
reference; 256 cycles produced no further improvement on the shipped instances.
This repairs reference undercapacity while exposing a near-ceiling standard-method
plateau. Difficulty remains an unresolved gate. No scoring coefficient or witness
value was changed to conceal it.

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before
exposure, must show that the first proposal does not reach the competent runnable
reference, rather than merely staying below the much stronger score-one anchor.
Independent operations-research review remains required.

## 6. Construction errors and revisions

One construction error was caught locally on 2026-09-05 before any model saw the task:
the pure-Python insertion descent cost ten seconds per iteration on 100-job instances,
making any fixed-iteration witness irreproducible in CPU minutes. The instance family
was capped at fifty jobs and the descent was rebuilt on accelerated prefix/suffix tables, with the
accelerated evaluation pinned against brute force. Recorded in
`tests/test_permutation_flow_shop.py`.

### 2026-09-08 evaluator review

The old index validator accepted distinct fractional indices and then truncated them
in `makespan`. Repeating each instance's cheapest repeated-job index with distinct
fractional offsets scored **15.675 development / 4.485185 held out, valid=1** in a
local diagnostic. Indices are now required to be actual integers (excluding bool),
so that submission is invalid and scores zero. The new regression computes the
exploit from public processing times; it does not encode answers.

A direct in-process candidate could also overwrite its processing-time input with
zeros and receive 1.0/1.0. The candidate now receives a deep copy, so mutations cannot
change the matrix, dimensions or anchors used for scoring. The regression requires
its result to equal the unmodified as-given order. This fixes the evaluator contract;
formal candidate isolation still requires the Linux sandbox path.

The reference budget was also restored from one to 128 cycles after measuring 64,
128 and 256 on the same deterministic trajectories. Original-loop local wall times
were 75.7, 144.9 and 287.8 seconds respectively under shared CPU load. The score
plateau at 128 motivated the budget choice; a target score band did not.

The baseline table now distinguishes the as-given order from the actual NEH zero
anchor. The local reproduction command below uses the physical benchmark directory,
not the metadata domain. Earlier NEH scores and blanket anti-contamination/difficulty
claims were corrected, rather than used as current admission evidence.

## 7. Robustness and reproducibility

Verification is exact integer simulation, so determinism holds by construction; the
held-out instances use fresh seeds of the same sizes. The package declares 180 seconds
expected evaluation time and a 300-second candidate timeout. Formal Linux sandbox replay,
global evidence refresh and independent replication are pending. See the task card
citations for background; the fresh-seeded instances are not the published Taillard
tables.

## Reproduce

```bash
python scripts/measure_reference.py \
  --task Engineering/PermutationFlowShop \
  --reference verification/reference_solver.py \
  --entry schedule_flow_shop
```
