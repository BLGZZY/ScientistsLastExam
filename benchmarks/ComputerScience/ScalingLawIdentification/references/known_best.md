# Reference and admission record — ScalingLawIdentification

## 1. Reference method

`verification/reference_solver.py` is standalone: an eight-call ladder
`(16, 16, 16, 13, 27, 55, 62, 192)` with six unique sizes. It puts five calls
on the `size % 3 == 1` side and three on the other side of the branching
runtime, repeats size 16 three times for the noise floor, and costs exactly nine
budget units; per-class
one-parameter log-space regression with an exponent penalty (and a closed form
for the constant class); a split-fit branch test (scan the plausible moduli,
three and seven, at every residue pivot, and refuse when the subsets' best
classes differ and the F statistic comparing the pooled single-law residual sum
against the split residual sums clears a Bonferroni-doubled gate of fifty); a
jitter gate (refuse when the repeat-estimated noise floor — the mean pairwise
log gap of the size-16 repeats — exceeds thirteen percent). It deliberately
lacks adaptive ladders and information-criterion averaging.

## 1a. Maintainer-only design constants (withheld from candidates)

This file is not served to the sandbox (see `frontier_eval/agent_files.txt`:
Task.md, solution.py, constraints only), so it is where the guidance removed
from the agent-visible surfaces lives. The branch predicate is: sizes
congruent to 1 mod 3 run `c*m^2`, all other sizes run `c*m*log2(m)`. Supported
worlds carry seven percent multiplicative noise (`NOISE_SIGMA = 0.07`), jitter
worlds sixty percent (`JITTER_SIGMA = 0.60`), and the reference jitter gate is
`JITTER_GATE = 0.13` on the mean pairwise log gap. PR review removed the
"public mod-3 branch split" phrase from Task.md and the "well above five
percent" figure from the runtime `refusal_note`: candidates must recover the
predicate by split-hypothesis fitting over their own ladder and the noise
criterion by repeat measurement. That measurement-first discovery is the
intended difficulty; do not re-disclose either constant in any agent-served
file (`Task.md`, `solution.py`, `frontier_eval/constraints.txt`, or the
evaluator's runtime problem mapping).

## 2. Baseline and normalization

The shipped `solution.py` times one size and guesses uniformly: `0.000000`. Supported
mechanism recovery is multiplied by `1 - 0.25 * budget_used / 9`; correct-refusal
credit stays unweighted and separately reported. The full-budget reference therefore
has profiling efficiency `0.750`. Re-measured on 2026-09-07, it reaches `0.710786`
development and `0.702993` robustness with zero false discoveries and full refusal.

## 3. Capability comparisons and ablations

| variant | development | robustness |
|---|---:|---:|
| full reference | 0.710786 | 0.702993 |
| minimal first-shot ladder (reconstructed 2026-09-07, no refusal gates) | 0.407258 | 0.073549 |
| jitter gate disabled | 0.544119 | 0.369660 |

The 2026-09-07 remeasurement uses a freshly reconstructed first-shot (one timing per
size on the ascending geometric ladder `(16, 32, 64, 128, 256)` — cost eight units —
fixed-shape selection, no branch or jitter gates), because the original 2026-09-06
audit harness was not preserved; it is a weaker, honestly labelled baseline than the
historical competent first-shot, whose
original 0.692 predates efficiency weighting and is no longer comparable. The
reconstruction is fully specified this time so the row re-runs exactly: rerun both
ablations with the reference module's `JITTER_GATE` set to infinity and with a
gateless fixed-shape solver over that ladder. Local
debugging numbers, not frozen benchmark evidence.

## 4. Shortcut probes

Uniform probabilities with a fixed scale score zero; the discriminating axes are the
class probability sharpening and the sealed extrapolation. No low-dimensional family
reaches the reference.

## 5. Frontier-model calibration

Not run. This task remains `candidate`. A clean Linux model draw, frozen before
exposure, must show that the first proposal does not reach the reference.

## 6. Construction errors and revisions

Six construction errors were caught locally, the sixth in the 2026-09-06
difficulty rework. (i) Jitter worlds carried a non-class family field and crashed
the oracle. (ii) The constant class had no shape column and its regression went
degenerate. (iii) After the ladder grew, the repeated-size index pointed at a
unique size and the jitter gate silently skipped. (iv) The branch split held one
point. (v) The branch criterion compared regression exponents that are both near
one by construction; it now compares split-versus-pooled residuals. (vi) The
difficulty audit found a competent first-shot ladder outscoring the shipped
reference (0.937 vs 0.929) under three percent noise — noise rose to seven
percent (the first attempt at eight and a half silently failed to land — the
lesson is pinned: patch-verify by grep, not by print), sizes capped at 384, the budget tightened to nine, the ladder
shortened, the branch predicate made public (sizes 1 mod 3 run quadratic) and
the oracle's stray mod-7 predicate corrected to match; the reconstructed
gateless first-shot now sits 0.30 below the reference (section 3). PR review
(2026-09-07) withdrew that public
disclosure — the predicate moved to section 1a here — after a clean-room
proposal built from the leaked Task.md alone scored 0.709, at reference level.
All pinned in
`tests/test_scaling_law_identification.py`.

## 7. Robustness and reproducibility

Development and held-out worlds use fresh seeds; branch runtimes are exact functions
of the size. Determinism was checked by comparing two full evaluation dictionaries.
Formal Linux sandbox replay, global evidence refresh and independent replication are
pending.

## Reproduce

```bash
python scripts/measure_reference.py \
  --task ComputerScience/ScalingLawIdentification \
  --reference verification/reference_solver.py \
  --entry identify_scaling_law
```
