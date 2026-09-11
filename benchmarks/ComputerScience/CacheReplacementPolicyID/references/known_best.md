# CacheReplacementPolicyID: known best

## Post-builder admission status: hold

The numerical reference and ladder tables below are historical builder observations.
The 0.556 reference deliberately omits permutation-family inference, while its existing
headroom rung reports 0.778 development and 0.750 heldout. The lower line is rejected as an
admission threshold. `verification/reference_permutation_augmented.py` is a standalone
candidate restoring this family; its full current-source measurement, false-positive guard
review and new first-proposal calibration remain pending. The machine contract records null
expected scores. These repairs and construction fixtures do not establish difficulty.

Each world starts a fresh candidate process, imported state and private tmpfs. All charged
run callbacks in that world remain in one session. Catching a malformed-trace or budget
exception does not restore the validity of that world. The published world set is synthetic;
noise-seed shifts repeat the same policies with new observations, not new hidden mechanisms.

## Reference (truth-blind): victim queries, two determinism tests, a policy library, capped L*

`verification/reference_lstar_family.py`. It reads only the public problem and the outcomes that
`run` returns, and it works in four stages.

- **Victim queries.** The one question it asks is which way a miss evicts after a given sequence
  of accesses. It replays the sequence, accesses a fresh block, then re-accesses the old blocks in
  a shuffled order. Hits change nothing about what is in the set, so the first of them that misses
  is the block that left. Each answer is a likelihood over the ways, accumulated over repeated runs
  until one way leads the next by a factor of 10^4, and remembered.
- **Determinism.** A per-position tail test runs six random traces ten times each. A pooled
  minority test runs 32 bursts of misses and loops over more blocks than there are ways, 48 times
  each. Under a deterministic policy every position's minority count is at most Binomial(48, 0.02).
  If either test fails, the reference refuses.
- **Library.** 2064 age-table policies (two or four ages, every hit table, every insertion age,
  with and without ageing every way to the top on a miss) are scored on 24 mixed traces by
  majority vote over three runs. Survivors within two mismatches of the best that still differ are
  settled by the victim query their difference names. The winner is checked on 16 traces.
- **L*.** Otherwise, L* for Mealy machines (Angluin 1987; Shahbaz and Groz 2009) learns a machine
  from victim queries, with Rivest-Schapire counterexample processing. Its equivalence queries are
  64 targeted traces at five runs each: random traces, bursts of misses and hit permutations. Every
  disagreement with the hypothesis is confirmed by six more runs before it counts. A hypothesis
  above 32 states is not claimed.

| split | score | recovery | false discovery | refusal | coverage | accesses per world |
|---|---|---|---|---|---|---|
| development | 0.556 | 0.556 | 0.00 | 1.00 | 0.56 | 92226 |
| held out | 0.500 | 0.500 | 0.00 | 1.00 | 0.50 | - |

World by world on the development split, the library recovers the 255-state and the 15-state
age-table policies in about 38600 accesses each. L* recovers the two 24-state permutation policies
and LRU in 58000 to 129000. The six-way 720-state permutation policy, tree PLRU on eight ways (128
states) and the switch policy (120) exhaust the budget or the cap and are declined. So is the
134-state policy whose fills age every other way. The age table with random tie breaking is
refused by the per-position test after 2640 accesses, and the two rarer randomised policies by the
pooled test. Held out, the library recovers the 40-state age table and L* the 24-state
permutation policy. The six-way 720-state permutation policy and the 78-state fill-ageing policy
are declined, and both randomised policies are refused.

What it leaves on the table, by design:

- **It stops L* at 32 states.** L* on a machine of hundreds of states runs out of budget well
  before it is done. A hypothesis past 32 states is more often a wrong one than a nearly right one.
- **It knows one family by name.** A permutation policy that is not small is never recovered.

The recoverable headroom is a permutation-policy fit in the style of Abel and Reineke (2013),
`.research/cache_policy/ladder.py headroom`. Positions are defined by eviction rank under W
consecutive misses. Each hit permutation is read off one hit and W victim queries, and the miss
permutation off one miss. The fitted machine is checked with the reference's 64 targeted traces
before L* runs. It scores 0.778 on the development split and 0.750 held out with no false
discovery. It recovers both six-way permutation policies and tree PLRU on eight ways, which is a
permutation policy too, and it leaves the switch policy and the fill-ageing policies to L*, which
declines them.

## Model draws

None. The task was built on a machine without a model endpoint. The card records
`calibration_evidence_status: missing`; the frontier draw and the global evidence refresh are owed
before certification.

## Baseline: the closest textbook policy, never declining

`solution.py`. It plays ten random traces of 32 accesses once each and counts how often LRU, FIFO
and tree PLRU (when W is a power of two) would have reported something else. It submits the
machine of whichever disagrees least, at confidence 0.9.

| split | score | raw | recovery | false discovery | refusal | coverage |
|---|---|---|---|---|---|---|
| development | 0.000 | -0.417 | 0.22 | 0.83 | 0.00 | 1.00 |
| held out | 0.000 | - | 0.00 | 1.00 | 0.00 | 1.00 |

It is right on LRU and on tree PLRU with eight ways, and wrong in the other ten development worlds,
including the three randomised ones. The normalisation takes it to zero.

## Difficulty ladder

`.research/cache_policy/ladder.py`, one reference choice changed at a time. The graded seeds are
the evaluator's own. The last columns re-draw every world's run seed eight times (four for the
sweep rows), so the runs change and the worlds do not.

| strategy | development | held out | mean over re-drawn seeds (dev / held) | false discoveries (dev / held) | coverage (dev) |
|---|---|---|---|---|---|
| reference | **0.556** | 0.500 | 0.556 / 0.469 | 0 / 0 | 0.56 |
| without the library (L* alone) | 0.444 | 0.250 | 0.417 / 0.188 | 1 / 2 | 0.44 |
| without L* (the library alone) | 0.222 | 0.250 | 0.222 / 0.219 | 0 / 0 | 0.22 |
| without the pooled determinism test | 0.333 | 0.000 | 0.389 / 0.094 | 11 / 13 | 0.56 |
| without either determinism test | 0.444 | 0.250 | 0.375 / 0.094 | 13 / 13 | 0.56 |
| 4 equivalence checks instead of 64 | 0.000 | 0.000 | 0.153 / 0.062 | 17 / 11 | 0.67 |
| no check anywhere | 0.000 | 0.000 | 0.000 / 0.000 | 56 / 25 | 1.00 |
| claim cap 1024 | 0.556 | 0.500 | 0.542 / 0.406 | 1 / 2 | 0.56 |
| claim cap 1024, no pooled test | 0.222 | 0.000 | 0.306 / 0.094 | 17 / 13 | 0.67 |
| claim cap 16, 32 or 128 checks | 0.222 | 0.250 | 0.222 / 0.188 | 0 / 0 | 0.22 |
| claim cap 64, 128 checks | 0.556 | 0.500 | 0.556 / 0.438 | 0 / 0 | 0.56 |
| claim cap 128, 32 checks | 0.444 | 0.500 | 0.528 / 0.375 | 1 / 1 | 0.67 |
| **headroom**: a permutation-policy fit before L* | 0.778 | 0.750 | 0.778 / 0.719 | 0 / 0 | 0.78 |
| the headroom with the templates and a cap of 1024 | 0.667 | 0.750 | 0.708 / 0.750 | 5 / 0 | 0.89 |

The library and L* each earn a separate part of the score. The checks are what make a claim safe.
Without them every hypothesis is claimed and most are wrong. With four instead of 64 they catch
too little. Without the pooled test the rarely random policies pass as deterministic and their
majority machines are claimed: on the graded seed all four randomised worlds whose randomness is
rare, two on each split. Dropping the per-position test as well changes the random draws that
follow and happens to claim fewer of them, and over re-drawn seeds it is no safer. A larger claim
cap claims nothing more on these worlds. At 1024 it matches the reference on the graded seed and
claims three wrong machines over eight re-drawn seeds. At 64 or 128 with 128 checks it matches the
reference on the graded seed. A smaller cap loses the 24-state policies. Adding the headroom's
permutation fit gains three worlds with no false discovery. Adding the textbook templates and the
large cap as well claims the switch policy wrongly.

## Shortcut probe

`.research/cache_policy/ladder.py`, the rows that do not contain the reference's full pipeline,
52 distinct strategies in five families:

| family | strategies | best development | held out | best strategy |
|---|---|---|---|---|
| textbook policies written out without a run (LRU, FIFO, NRU, SRRIP-HP, SRRIP-FP, LIP, tree PLRU) | 7 | 0.000 | 0.000 | any |
| the same templates fitted to 24 noisy traces at mismatch tolerances of 0.5 to 5 per cent, with and without a check and the determinism tests | 17 | 0.222 | 0.000 | any tolerance, with the check and the tests |
| the reference's age-table library alone, with and without its check and the determinism tests | 4 | 0.222 | 0.250 | any of them |
| a permutation-policy fit alone, with 16 to 128 checks or none, with and without the determinism tests | 6 | 0.333 | 0.250 | checked, with the tests |
| L* alone at claim caps of 8, 16, 32, 64, 128 and 1024 states with 16, 64 or 128 checks | 18 | **0.444** | 0.250 | cap 32, 64 or 128 checks |

The best strategy reaches 0.444 on the development split, 80 per cent of the reference, and 0.250
held out. It is the ladder's rung without the library. Over eight re-drawn seeds it averages 0.417
and 0.188 with three false discoveries in 144 world-runs, where the reference averages 0.556 and
0.469 with none. L* at caps above 32 states scores 0.444 at best and makes false discoveries held
out. Every blind claim scores zero. It is right in at most one development world, wrong in the
other deterministic ones, and a false discovery in every randomised one.

## Construction errors caught on the way

- The first L* processed counterexamples in the manner of Maler and Pnueli, adding every suffix
  to the table. Every added suffix costs a victim query for every row of the table, and L* ran
  out of budget. Rivest-Schapire processing adds one suffix per counterexample.
- Victim queries stopped at a likelihood lead of 200. One wrong victim early in a remembered
  prefix then corrupted every row that extended it. The lead is now 10^4, which costs a run or two
  more per query.
- Equivalence checks on random traces alone missed a deep LRU state, which only a particular order
  of hits reaches. The checks now mix in bursts of misses and permutations of the resident blocks.
- L* claimed a wrong 88-state and then a wrong 110-state machine for the switch policy, whose
  difference from LRU needs six misses in a row. No hypothesis above 32 states is claimed.
- A tree PLRU with a random victim once in 64 misses passed the per-position test. The pooled
  test on bursts and loops was added, and the rarest randomised policies are now 1/32 on the
  development split and 1/16 held out.
- While a 60-state five-way insertion policy was on the development split, the reference with its
  cap raised to 1024 tied the reference. That world is now a 720-state six-way permutation policy.
- L* checked with 24 traces claimed a wrong 24-state machine on one prototype seed. It now uses 64.
- Moved to the package's own evaluator, whose run seeding differs from the prototype's, the pooled
  test at 24 traces let the 1/32 policy through on two of 24 re-drawn seeds, at z of 3.90 and
  3.95. At 32 traces it separates the kinds with z at most 2.55 in every deterministic world and at
  least 5.83 in every randomised one. The change costs 8640 accesses per world.

## Robustness

`.research/cache_policy/pkg_eval.py reference 0 1 ... 15` re-runs the reference with every world's
seed shifted. Over sixteen shifts it averages 0.542 on the development split, from 0.444 to 0.556,
and 0.484 held out, from 0.250 to 0.500, with no false discovery in 288 world-runs. The graded seed
ties its best draw on both splits. The headroom averages 0.778 and 0.719 over eight shifts with none.

`.research/cache_policy/det_diag.py` records both determinism statistics in every world over 24
shifts. The per-position test's largest value in a deterministic world is 4.52 against a threshold
of 6. The pooled z at 32 traces lies between -2.67 and 2.55 in deterministic worlds and between
5.83 and 99.26 in randomised ones.

`tests/test_cache_replacement_policy_id.py` checks that the simulator behind `run` and the scored
machine are the same policy on random traces with the noise off. It checks that the thirteen
deterministic worlds are pairwise inequivalent minimal machines of the recorded sizes and that the
switch policy differs from LRU first at six misses. It checks that two evaluations of the reference
agree key for key and that declining everything scores 0.000 in both forms. It checks 29 malformed
candidate shapes, including overspending, a patched budget, malformed machines and malformed
traces. All of them score valid 0, combined 0 and feasibility 0 without raising. A reference
evaluation takes about 2.5 seconds in process. It makes at most 11823 calls to `run` in one world
and 76755 in one evaluation, which the sandboxed evaluation carries as RPC calls.
`.research/cache_policy/summary.py` recomputes every number on this page.

Not done: the sandbox half of `scripts/check_task_contribution.py` (no Bubblewrap on the build
machine), a frontier-model draw, the global evidence refresh.
