# PR 72 scoring revision validation

The Linux sandbox audit and full-suite run use clean source commit
`fcddf93266c66343ebaefae77765e8689c707a4e`, which includes upstream main
`913ebe5`. The immediate evidence follow-up changes only document measurements, correct a docstring,
remove an unused research-script import and attach evidence. Upstream main later
advanced to `eb9fca9` (clock-read fix, rebound preflight evidence and README count
checks); merge `7557aff` incorporates it and updates README to 86 tasks / 81
candidates / 44 discovery / 10 evidence tasks. Supplemental post-merge tests are
recorded separately. The production
reference implementation is unchanged from the reviewed PR.

- `full-suite.txt` / `full-suite.json`: 1203 passed, 50 skipped, 117 deprecation
  warnings, 498 subtests passed; exit 0 in 2109.48 seconds on the clean source above.
  PR-mode frozen-inventory policy matches GitHub Actions (`SLE_REQUIRE_FROZEN_INVENTORY=0`).
- `../dark_matter_recoil_revision_2026-09-10.json`: clean-revision trusted sandbox
  evidence; repeated complete baseline/reference metrics identical; all ablations
  valid; exact continuous constant-mass and completed four-way shortcut gates pass.
- `contribution.json` / `contribution.txt`: all 15 contribution checks pass, including
  sandbox baseline, determinism, malformed and blanket-abstention candidates.
- `wrapper-reference.json`: the outer runner's complete output equals the audit's
  reference metrics exactly (score 0.5484845249, valid 1).
- `wrapper-missing.json`: nonexistent candidate gives valid 0 and retains
  `candidate is not a regular file`; failure is not silently converted to success.
- `../dark_matter_recoil_review_reproduction_2026-09-10.json`: in-process Linux
  reproduction of reviewed source `a222b592`, using the completed current probe.
  Constant mass with reference decisions reaches 0.657192, and a legal single-target
  full-budget strategy reaches 0.644077, both above the old 0.523728 reference.
  This explicitly distinguishes oracle-assisted bounds from legal candidates.
- `isolation-cleanup-test.txt`: after removing the last single-case test
  parametrization at `a536d1c`, the actual Bubblewrap global/tmpfs isolation test
  passes again (same generated candidate and assertions).
- `main-sync-tests.txt`: upstream merge `7557aff`, README counts, clock/protocol,
  recovery/preflight and sentinel checks: 83 passed, 1 skipped, 7 subtests passed.
- `maturity-summary.json`: 86 tasks, no issues or stale tasks; four candidate tasks
  await maintainer freezing, including this new task.
- `linux-focused.txt`: final documented source `f7785a6`, 110 passed with no skips;
  includes genuine Bubblewrap process/tmpfs isolation and all new scoring regressions.
- `local-focused.txt`: CI-pinned NumPy 1.24.4 / SciPy 1.10.1 on macOS, 101 passed,
  9 platform-dependent tests skipped. This is not a substitute for Linux isolation.

Additional structural checks: taxonomy has 86 tasks and no issues; regenerating
TASKS.md leaves it byte-identical; the numeric-key audit reports no prose values.
The generic documented-key audit does not inspect this dynamically built problem,
so actual simulator dictionaries were checked separately: all 13 public problem
keys, 5 response keys, request fields and submission fields are documented.

Historical pre-review evidence is retained separately and is not claimed as evidence
for this revision. The new 56-world campaign keeps the per-world budget at 12 and the
runner timeout at 300 seconds. Two secure reference runs took 36.12 / 36.07 seconds.

Limitations remain explicit: both splits informed construction; heldout fixed-halo
ablation improves by 0.040096; heldout reference refusal is 3/4 and false discovery
is 1/21. Model calibration, external domain review and a server-held reissue are still
outstanding; the task remains candidate. Global frozen evidence is a maintainer
integration step, not self-certification by this PR.
