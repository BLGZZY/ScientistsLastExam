# DarkMatterRecoilAttribution: witness and construction record

## 1. Reference and sources

`verification/reference_profile.py` is an unchanged, truth-blind Poisson-deviance
witness. It reads only `problem` and charged observations. Three mass starts jointly
profile the speed weights, coupling ratio, target backgrounds and calibration gains;
null, residual and law-separation checks allow refusal. It is not a published record.
Score 1 follows from exact parameters and correct decisions, not a reference literal.

[Cherry et al., arXiv:1405.1420](https://arxiv.org/abs/1405.1420) motivates common
velocity structure and target-dependent kinematics for momentum-dependent scattering.
The three unboosted Maxwell components, Gaussian form factor and midpoint detector
model are our explicit approximations. An independent numerical quadrature of the
normalized Maxwell speed density checks the inverse-speed kernel in the task tests.
No LZ likelihood or experimental data is copied; [LZ v3](https://arxiv.org/abs/2410.17036v3)
is not the simulator's ground truth and does not define its normalization.

The revised outside-family construction uses the same allowed kernel at each target,
but target masses are separated around a log-mass interval. A single target has an
exact supported-world twin, including its sampled counts and controls. This is a
synthetic joint-consistency test, not a claim that real particles have target-dependent
mass. Tests check those twins at all three targets, including full-budget acquisition.

## 2. Baseline

The legal baseline buys one xenon unit then asserts a 10 GeV contact signal. All
supported masses are at least 22 GeV, so it receives no parameter credit. Incorrect
positive claims on null/outside-family worlds also receive none.

Each split now contains 20 supported, 4 null and 4 outside-family worlds. Blanket
`none` and blanket `abstain` each have mean utility 1/7. Normalization is
`max(0, (mean_utility - 1/7)/(6/7))`; both blanket strategies and the baseline score
exactly zero, while a perfect oracle scores 1. Perfectly distinguishing only null and
refusal can still earn 1/6. This limited non-discovery credit is explicit; coverage
and claim denominators are reported separately. Heldout remains diagnostic only.

## 3. Ablation ladder

Run on Linux with Bubblewrap:

```bash
OPENBLAS_NUM_THREADS=1 python3 scripts/audit_dark_matter_recoil.py \
  --output experiments/dark_matter_recoil_revision_2026-09-10.json
```

The audit evaluates the baseline and unchanged reference twice in the real sandbox,
and each reference ablation through the same boundary. `one_unit` buys one rather
than four units per target; `ignore_gain` fixes gain to unity; `fixed_halo` constrains
all three speed amplitudes to be equal. Scores can vary slightly with SciPy version:
the original audit and external review differed by about 2e-4 on one ablation.

Revision construction measurements (local CI-pinned NumPy 1.24.4 / SciPy 1.10.1;
Linux sandbox replay is recorded separately before submission):

| Strategy | Development | Heldout | Development loss vs reference |
|---|---:|---:|---:|
| baseline | 0.000000 | 0.000000 | 0.548432 |
| reference | 0.548432 | 0.499973 | 0.000000 |
| one_unit | 0.366044 | 0.235573 | 0.182388 |
| ignore_gain | 0.341797 | 0.222797 | 0.206634 |
| fixed_halo | 0.438221 | 0.540079 | 0.110211 |

The fixed-halo restriction improves heldout by 0.040106. This can reflect finite-data
regularization and mass/halo degeneracy; it does not support a claim that free halo
fitting is always necessary. No seed was selected to make every ablation lose on
heldout. The reference refuses all four development outside-family worlds, but only
three of four heldout ones; heldout false-discovery rate is 1/21. These are small
synthetic samples, not population guarantees or calibrated discovery significance.

## 4. Shortcut probe

The completed probe has all four decisions: `none`, `contact`, `q2`, `abstain`.
It scans every target with 1, 3 and 12 units, excess and hardness thresholds,
48 constant masses, and two versions of a three-bin narrow-peak residual (Poisson
standardized and fractional). The infinite peak threshold includes the old no-refusal
family. In total it evaluates 233,280 configurations using cached observations.
Selection uses development only; the selected candidate is evaluated once on heldout.
The vectorized selection result is checked against the actual public-input candidate
callback. This is a finite builder search, not an exhaustive algorithmic upper bound.

| Probe | Development | Heldout | Interpretation |
|---|---:|---:|---|
| Best four-way single-target strategy | 0.249535 | 0.130670 | development-selected once |
| Any constant mass, perfect law/null/refusal decisions | 0.296772 | 0.294044 | exact per-split upper bound |

The legal selected strategy uses one germanium unit; its configuration is recorded
in the JSON report. It reaches 45.5% of reference on development. The constant-mass
bounds are stronger than the reviewer's attack: every classification is granted
correct, including negative worlds. They reach 54.1% / 58.8% of reference. These are
builder oracle-assisted bounds, **not** legal zero-query candidates.

The constant bound covers the entire legal interval [10,250], not a discrete mass
sweep: utility is piecewise linear in log mass, so testing every true mass, its
±0.25 log-radius breakpoints and legal endpoints finds the exact maximum.

Regression tests and the audit fail unless that bound is at most 0.6 times reference
on both splits. The selected four-way strategy must stay below 0.7 times reference
and at least 0.15 below it on both splits. The test calls the same full probe as the
evidence audit, rather than a hand-picked weaker member of its family.

Historical evidence is retained in `experiments/dark_matter_recoil_2026-09-10.json`.
The original 480-strategy audit omitted refusal, so its reported 0.380949 maximum was
not the four-way family's maximum. The external reviewer found 0.507354 against
reference 0.523729; using reference decisions and constant mass 57.8 yielded 0.657182.
Run `.research/pr72_review_reproduction.py` to remeasure original commit `a222b592`
with the completed probe and exact constant bounds. It labels oracle-assisted bounds
separately from legal candidates and records source hashes and environment versions.

## 5. Frontier draw

Not run. The package remains `candidate`; `hard` is an intended tier, not measured
admission. These builder checks are not a fresh frontier-model draw, independent
calibration, long-horizon evidence or proof of an open cosmology discovery.

## 6. Construction errors and corrections

- Earlier drafts conflated mass error with a false law discovery, omitted bin widths,
  and used plug-in gains. These were corrected before external review. Charged,
  counter-keyed sampling and sticky query failure were already present.
- PR 72 review exposed five of six development signal masses sharing one scoring
  window. The revision keeps both base seeds and the physical mass interval, expands
  to 20 signals per split, and partitions log mass into 20 paired strata with bounded
  within-stratum jitter. Each pair assigns one mass to each law at random. This
  prevents both aggregate clustering and a law-specific constant-mass advantage.
- An initial revision independently stratified the laws: its perfect-decision constant
  bound still reached 63.5% of heldout reference. Pairing the strata makes coverage a
  generator invariant instead of relying on two independently lucky draws. Both
  splits informed construction checks and must not be called fresh confirmation.
- The original unsupported worlds had obvious narrow peaks and the probe omitted
  refusal. Both defects are removed: every target marginal now belongs exactly to a
  supported kernel, while shared-mass consistency fails jointly; the probe includes
  refusal, all targets, and both sparse and full-budget single-target acquisitions.
- Changed mixture weights are derived from the actual class counts, including null
  correctness denominators. Blanket decisions and the oracle ceiling are rechecked.
- Candidate-visible reference/ablation/shortcut scores were removed from `Task.md`.
  PTAHellingsDowns is now named explicitly as a nearest neighbour, and copied neural
  test terms, dead branches, unused imports and single-element parametrizations are
  removed. The inventory uses the repository's half-width punctuation.

## 7. Robustness, contamination and remaining headroom

The two base seeds remain 731500 and 941700. Physical mass and law are not exposed
in public problems; controls and call budgets do not name the split. Processes and
private temporary filesystems reset between every world. The Linux regression tests
both Python globals and a `/tmp` marker through actual Bubblewrap.

All seeds are nevertheless repository-visible, and both splits were inspected during
construction. A real evaluation needs a server-held reissue and external domain
review. The exact constant bound and marginal-twin checks hold for the implemented
families; neither excludes arbitrary learned or multi-target shortcuts.

The unchanged reference uses equal allocation and point estimates. Adaptive target
allocation and treatment of mass/halo uncertainty remain possible improvements.
It does not attain perfect joint-family rejection on heldout; no artificial optimizer
failure or hidden-answer lookup was introduced to lower its score. The expanded
56-world campaign retains the 12-unit per-world budget and 300-second runner timeout;
metadata allows 120 seconds for evaluation, subject to measured hardware load.
