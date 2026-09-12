# CrystalStructurePolymorphSearch anchors and construction record

## 1. Reference witness

`verification/reference_multistart.py` is truth-blind. It spends all 24 calls on eight cubic and
sixteen anisotropic deterministic random seeds, then evaluates every three-member subset using the
public archive objective. It scores 1.0 by construction but supplies no global lower bound.

## 2. Baseline

`solution.py` submits three deterministic random seeds and returns all three relaxed IDs. It is
valid in every world and defines score 0.0.

## 3. Capability ladder

A three-start cubic-only search scores `0.3089156287047785`, leaving a margin of about 0.69 to the
24-start witness. The remaining ablations—removing volume variation, anisotropy, energy-aware
archive selection, or diversity selection—await clean Linux calibration.

## 4. Shortcut probe

The executable shortcut is `verification/shortcut_cubic.py`. It uses only three random cubic seeds,
the same trusted relaxation, and no hidden state. Its declared score is recomputed by the standard
sandbox gate; this is a cheap-strategy guard, not evidence against untested prototype memorization.

## 5. Frontier draw

No frontier-model draw has been run. First-proposal difficulty, paired feedback advantage, and
two-hour material headroom are unmeasured, so the task remains `candidate`.

## 6. Construction errors and corrections

The first implementation used Python loops over every atom/image pair and exceeded a practical
evaluation budget. The energy was vectorized and the local relaxation reduced to 35 iterations.
A first multistart witness was also beaten by an eight-start cubic probe because its archive
selection traded away too much energy. The final witness includes those cubic starts and exactly
maximizes the published three-member archive utility; both corrections are retained here.

## 7. Robustness and limits

Three development and two held-out worlds vary stoichiometry, pair parameters, pressure, and cell
volume. They remain small analytic surrogate landscapes. No DFT, phonon, finite-temperature,
experimental, or large-cell conclusion follows.

Sources: Abraham and Probert (2006), DOI `10.1103/PhysRevB.73.224104`; Oganov and Glass (2006),
DOI `10.1016/j.cpc.2006.07.020`.

