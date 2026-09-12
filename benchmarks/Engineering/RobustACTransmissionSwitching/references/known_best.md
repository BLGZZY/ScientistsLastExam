# RobustACTransmissionSwitching anchors and construction record

## 1. Reference witness

`verification/reference_screen_refine.py` is truth-blind and uses only the public problem plus the
charged callback. It spends exactly 48 calls: 40 on the intact and seven single-open topologies at
five participation factors, then eight refinements. It scores 1.0 by construction and leaves every
double-open topology unexplored. It is an admission witness, not a global optimum.

## 2. Baseline

`solution.py` evaluates the all-lines-closed topology once at participation 0.40. It is feasible in
all six worlds and scores 0.0 by definition.

## 3. Capability ladder

The committed tests establish the endpoints and the key mechanism: at a high cheap-generator
share, the intact network violates the `l12` bottleneck while opening that line reroutes the AC
flow and is feasible. A ten-point participation sweep that never switches a line scores
`0.5820883141862041`, so topology search contributes materially beyond continuous tuning. Full
frontier-model ablations await a clean Linux calibration run.

## 4. Shortcut probe

The construction probe exhaustively evaluated all zero-, one-, and two-open topologies on a fixed
21-point participation grid. It confirms feasible double-switch plans exist beyond the single-line
reference search. Because the grid and all worlds are synthetic, this is evidence of numerical
headroom only; it is not a frontier-model or long-horizon result.

## 5. Frontier draw

No frontier-model draw has been run. The package must remain `candidate`; the first-proposal bar,
paired feedback control, and two-hour material-headroom criterion are unmeasured.

## 6. Construction errors and corrections

An initial cost model made the intact topology globally attractive because opening a line only
increased losses. The final construction gives bus 1 a cheaper generator and a deliberately tight
loop-flow branch, so switching can admit more cheap generation while still requiring every outage
scenario to pass full AC checks. This correction is retained here rather than hidden.

## 7. Robustness and limits

Development uses four worlds and source-held reporting uses two worlds with different loads,
reactances, costs, and load multipliers. All reuse one five-bus graph and two contingency line IDs.
No claim is made about large-network scaling, transient stability, protection, or operational use.

Scientific sources: Fisher et al. (2008), DOI `10.1109/TPWRS.2008.922256`; Bienstock and Verma
(2019), DOI `10.1016/j.orl.2019.08.009`.
