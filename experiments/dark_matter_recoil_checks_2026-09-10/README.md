# ParticlePhysics/DarkMatterRecoilAttribution: independent branch validation

Clean tested source: `1004b6e3f7f906a423a9478ce7c137a80e4b1060`. Later commits add only experiment evidence.
The branch contains one new task and has no runtime/test dependency on another
new task package. This is builder and engineering evidence, not model calibration.

- Linux focused tests: **80 passed, 86 warnings, 17 subtests passed in 20.59s**.
- Local focused tests: 45 passed, 1 Linux-only skip; the skipped isolation test passed on Linux.
- Contribution gate: passed, including secure baseline repeats, discovery axes,
  blanket refusal and malformed candidates (`contribution.json`).
- Black-box wrapper: valid legal baseline, score 0 (`wrapper.json`).
- Reference and baseline each evaluated twice through the sandbox; all metric keys
  match. All ablations are valid. Full precision and finite-grid probes are in
  `../dark_matter_recoil_2026-09-10.json`.
- No full-repository run is claimed for this branch; GitHub PR CI supplies that check.

Linux used Python 3.12.3, NumPy 1.26.4, SciPy 1.13.1 and one OpenBLAS thread.
This host requires sudo for the trusted harness to establish namespaces; candidate
workers still run as UID/GID 65534 with unshared namespaces, seccomp, read-only
mounts and per-world private tmpfs. No host-wide security setting was changed.
`validation.json` records source provenance, commands and exit statuses.

Reproduce on a configured Linux sandbox host from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 python3 scripts/audit_dark_matter_recoil.py --output /tmp/dark_matter_recoil.json
python3 scripts/check_task_contribution.py --task ParticlePhysics/DarkMatterRecoilAttribution
OPENBLAS_NUM_THREADS=1 python3 -m pytest -q tests/test_dark_matter_recoil.py tests/test_secure_eval.py tests/test_task_cards.py tests/test_benchmark_layout.py tests/test_task_inventory_document.py tests/test_exam_taxonomy.py
```

Task status remains candidate. Independent model calibration, domain review and
server-held reissue are outstanding. Neither clean-source execution nor passing
security tests establishes frontier difficulty or contamination resistance.
