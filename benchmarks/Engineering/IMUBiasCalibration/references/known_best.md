# Known best - IMUBiasCalibration

## Reference

The truth-blind witness fits gravity-subtracted public accelerations by NumPy least squares,
then checks sparse residual outliers, quadratic thermal response and off-axis coupling. It reads
no hidden labels, seeds or coefficients. The review revision retains its numerical method and
thresholds; the optional diagnostic-disable argument exists only to reproduce ablations.

For supported worlds only a non-abstained `supported` diagnosis earns parameter/prediction/
confidence quality. Unsupported worlds earn one only for a correctly attributed refusal.
Normalization subtracts the maximum blanket-refusal reward U, divides by supported count S,
clips to [0,1], and multiplies by correct-refusal rate. Thus every blanket-refusal policy and
every never-refusing policy earns exactly zero, regardless of fitted numerical values.
The extra refusal multiplier is an explicit review-era scoring choice, not an independent axis.
Mechanism accuracy, FDR over actual claims, fault-labelled refusal and supported coverage remain
separately reported with counts and denominators. Mechanism means supported label accuracy,
not the continuous parameter composite. Incorrect supported claims count toward coverage/FDR;
abstentions and invalid outputs remain in supported denominators.

## Baseline

The shipped zero-calibration, zero-confidence `undetermined` abstention is valid. Its zero
prediction is scientifically wrong but contract-valid. The all-abstain class now scores zero,
not just that one baseline. The witness is not a normalization constant or published SoTA.

## Ablation ladder

`verification/calibrate.py` removes the motion, quadratic and coupling diagnostics one at a
time, without refitting thresholds or changing the other reference operations. It also replays
never-refusing and all-abstaining OLS fits. The same executable is evaluated twice per policy
through the Linux trusted driver and bubblewrap; full JSON payload equality is checked.

## Shortcut probes

The fixed 1,296-policy grid uses OLS coefficients, residual RMS and peak residual norm, with
12 RMS thresholds, 12 peak thresholds and independent three-way fault labels above each
threshold. It lacks structured quadratic/orientation diagnostics. Selection uses development
only; the selected winner is then replayed on both splits in the sandbox. A grid maximum is
not a universal algorithmic upper bound. The candidate code reads public records only.

## Model calibration

Historical record: `experiments/imu_bias_calibration_deepseek_calibration_2026-09-07.json`.
On that old objective the reference scored 0.988562/0.987844, Flash 0.461999/0.647238 and Pro
0.599130/0.733479. Those Windows in-process first proposals are not Linux sandbox evidence for
the revised objective. Old refusal/FDR and composite semantics differ; do not compare the
numbers to the new split axes. No frontier-model admission claim follows from DeepSeek.

## Construction errors

The initial reference was exceeded by a Flash proposal, prompting the historical reductions
of fault amplitudes and stronger reference diagnostics documented in the original record.
The 2026-09-08 review then identified three independent errors: discovery axes were nested
or missing; supported abstentions retained fitted recovery credit and wrong fault refusals
retained free prediction credit; two bibliographic identifiers were incorrect. All three
require correction irrespective of model performance. The revision also fixes external
evaluation paths and delegates run_eval to the trusted sle subprocess, copies public inputs
before candidate calls, and resets sandbox sessions between worlds.

## Robustness and limitations

The review adds the missing held-out motion family after the initial shortcut replay exposed
its absence. Existing world parameters, generator equations and reference thresholds are
unchanged; the new world has an independent seed and bias/drift/motion vector. It supplies all
24 six-orientation/four-temperature records, has only six affine parameters, strong fault signals
and two supported worlds per split. These are meaningful limitations: the high reference score and
simple diagnostics may put it at on-ramp difficulty, not expert-level admission. Adding a
measurement budget, full scale/misalignment calibration or noise-overlapping faults would be a
separate scientific redesign, not a bookkeeping fix. The task remains candidate pending
independent review, server-held regimes and hardware replication. No full-repository tests or
maintainer-owned global evidence refresh are performed for this revision.

## Verified provenance

Oliver J. Woodman (2007), *An introduction to inertial navigation*, University of Cambridge,
Computer Laboratory, report **UCAM-CL-TR-696**, DOI **10.48456/tr-696**.
Publisher record: https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.html
(title, author, date and DOI verified 2026-09-08).

This supports the inertial sensor-error setting; the exact linear temperature law, quadratic
fault, fixed cross-axis matrix and sparse motion perturbations are explicitly synthetic
reduced-order approximations, not parameters quoted from that report. No device-accuracy
claim is made. The removed DOI 10.1109/5.554205 is Hall and Llinas's unrelated multisensor
fusion introduction; 10.1109/TIM.2014.2325662 did not resolve. Neither supports this oracle.
