# PR74 scientific revision plan (2026-09-10)

Baseline: b565eac69e7c8e5d713fc5ac4b9ba3b7c032a222. The dated earlier
measurements are historical, not evidence of a shortcut-family upper bound.

1. Repair the orientation contract before tuning difficulty: canonicalize a
   normal/slip pair by flipping both signs, and wrap noisy plane coordinates
   through vectors instead of clipping dip. A zero-noise observation must retain
   its double-couple tensor for either hemisphere and near horizontal/vertical
   planes. Preserve the existing scoring formula for the initial method study.
2. Build independent grid probes with their own refusal thresholds, both fixed
   and adaptive paid-observation schedules, and signed/unsigned angular loss.
   The exact maintainer source is unavailable; reconstructed variants must not
   be called an exact reproduction of the maintainer's reported numbers.
3. Develop a complete public-input reference with normalized shear-direction
   fitting, uncertainty weighting, multiple starts and adaptive re-analysis.
   Compare against coarse/dense grids and grid plus local refinement. Report
   ordinary methods that approach the reference rather than selecting weak gates.
4. Develop on the existing development split and additional training seeds
   61001, 61007, 61013, 61019, 61027, 61031, 61043, 61051, 61057, 61063,
   61069, 61081 (supported), plus 61103/61109 (mixed) and 61121 (incoherent).
   If event count or shear floor changes, justify the scientific change and
   compare methods on the same resulting oracle; do not weaken the reference or
   alter score constants merely to land inside an admission interval.
5. Before new-oracle held-out evaluation, freeze the selected reference, oracle
   and probes with SHA-256. Then run the original held-out split and predeclared
   confirmation seeds 71011, 71017, 71023, 71039, 71047, 71051, 71059, 71063,
   71069, 71081, 71089, 71099 (supported), 71107/71113 (mixed), 71119 (incoherent).
   These additional worlds are local confirmation, not secure server-held or
   frontier-model calibration. Do not tune on them then relabel them as untouched.
6. Measure score components, plane accuracy, ratio error, axis angular error,
   coverage/refusal and acquisition benefit. Maintain true-zero malformed and
   degenerate baselines, candidate isolation, and source/order invariants.
   Keep the PR draft if the improved ordinary grid family remains close to the
   reference; a scoring-policy exception is the maintainer's decision.

Primary source consulted: Vavryčuk (2014), doi:10.1093/gji/ggu224, sections 2–5.
It explicitly distinguishes equal-shear Michael fitting from fault-selection
error in R; principal directions alone do not establish difficult recovery.
