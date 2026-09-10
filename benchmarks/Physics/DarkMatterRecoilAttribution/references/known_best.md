# DarkMatterRecoilAttribution: witness and construction record

## 1. Reference and sources

`verification/reference_profile.py` is a truth-blind Poisson-deviance witness. It only
uses `problem` and the charged experiment callback; its three mass starts jointly
profile speed-component weights, coupling ratio, target backgrounds and calibration
gains. The null decision and fit-residual/model-separation checks can decline evidence.
It is not a published best-known record. Score 1 is algebraically recomputable from
correct decisions and exact parameters; no numerical score literal anchors the oracle.

[Cherry et al., arXiv:1405.1420](https://arxiv.org/abs/1405.1420) supports the scientific
role of target-dependent recoil kinematics and common velocity structure when
distinguishing momentum-dependent scattering. Our three unboosted Maxwell components,
Gaussian nuclear form factor and midpoint detector model are stated approximations.
The exponential inverse-speed component is independently checked by quadrature of
a normalized Maxwell speed density in `tests/test_dark_matter_recoil.py`.
No LZ likelihood or experimental data is copied. The experimental upper limits in
[LZ v3](https://arxiv.org/abs/2410.17036v3) are not the ground truth of this simulator
and are not used for normalization.

## 2. Baseline

The shipped legal candidate spends one xenon unit then asserts a 10 GeV contact
signal. The non-null generator's mass range guarantees no mass credit for that
claim; incorrect positives on null/outside-family cases earn none. Zero is checked,
not assumed. Blanket `none` and blanket `abstain` each have mean utility 0.2, so the
normalization makes both exactly zero. Selective null/refusal without positive
discovery can still obtain limited utility; coverage and denominators expose that.

## 3. Ablation ladder

Run `python scripts/audit_dark_matter_recoil.py --output <path>` on clean Linux.
It evaluates the reference and baseline twice through Bubblewrap, and runs these
otherwise identical reference ablations through the same boundary:

- `one_unit`: one exposure per target instead of four (3 rather than 12 units).
- `ignore_gain`: replace the unknown target gain with unity, despite available controls.
- `fixed_halo`: force equal amplitudes across all three speed components.

Report each development/heldout score and delta; do not silently suppress an ablation
that happens to improve a finite-sample point estimate. Such a result is a design
limitation to investigate, not permission to choose a more flattering seed.

Linux secure measurements (full precision and provenance in
`experiments/dark_matter_recoil_2026-09-10.json` at repository root):

| Strategy | Development | Heldout | Development loss vs reference |
|---|---:|---:|---:|
| baseline | 0.000000 | 0.000000 | +0.523728 |
| reference | 0.523728 | 0.572739 | +0.000000 |
| one_unit | 0.235410 | 0.336504 | +0.288319 |
| ignore_gain | 0.317555 | 0.250000 | +0.206173 |
| fixed_halo | 0.512025 | 0.490536 | +0.011703 |

The reference has zero observed false positive model claims, full supported-world
coverage and correct refusal on both outside-family worlds in each split. Each split
has only ten worlds: these rates are finite-sample diagnostics, not population guarantees.

The fixed-halo ablation loses only 0.011703 on development (0.082202 on heldout).
That is weak development evidence for the necessity of fitting the halo weights;
no strong multi-nuisance difficulty claim follows from this ablation.

## 4. Shortcut probe

The same script tests 480 strategies using only three xenon exposure units: threshold
the control-subtracted excess, use a high/low-energy ratio to choose the law, and
return a grid-selected constant mass. The grid is selected on development only;
the selected strategy is then scored once on heldout. This is a builder-only finite
probe, not independent model calibration or a bound on all possible algorithms.


Recorded best development score: 0.380949; its single heldout
confirmation: 0.000000. Selection parameters and all probe
scope qualifications are retained in the machine-readable evidence.

## 5. Frontier draw

Not run: no configured general language-model endpoint or credentials were available
in this task's execution environment. This package remains `candidate`; metadata
`hard` is the intended tier, not a measured admission result. No model superiority,
open-loop saturation, positive evolution gap, or long-horizon claim is made.

## 6. Construction errors and corrections

- The initial draft counted large mass error as a false discovery. Corrected: false
  discovery concerns the interaction-law claim; mass error has its own continuous score.
- Initial spectrum values omitted bin width. Corrected with explicit disjoint bins
  and midpoint quadrature, also used in background controls and the independent check.
- Initial gain estimation was a plug-in step. Replaced with joint gain/control fitting
  so the reference does not discard a routine nuisance-uncertainty treatment.
- Query unit streams are keyed per target and repeat index; batching and reordering
  cannot buy free repeated measurements. Bad requests latch the entire campaign invalid.

## 7. Robustness, contamination and remaining headroom

Candidate-visible instruments have no latent kind/seed/split key. Development and
heldout use separate seeds; evaluator records never enter the search-visible view.
Nevertheless, all source seeds are in the repository, so memorization is possible
outside the sandbox. Real evaluation needs a server-held reissue and domain review.
The two law families and finite halo basis are restricted; the omitted-family examples
do not prove reliable rejection of every real detector nuisance or new interaction.
Mass/halo degeneracy and fixed equal exposure allocation leave genuine statistical
headroom. The present witness does not marginalize over mass/halo uncertainty or
adapt its next target to information already measured. No artificial optimization
failure or exact hidden answer is used to define the reference score.

The evaluator resets the candidate process and private temporary filesystem before
every subsequent world, including the development/heldout boundary. An actual
Bubblewrap regression candidate tests both module globals and a `/tmp` marker.
