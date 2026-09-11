# CacheReplacementPolicyID: which replacement policy does this cache set run?

## 关系与区别 / How this differs from the nearest tasks in this repository

- **`Mathematics/SequenceLawRecovery`** and **`DynamicalSystems/ActiveLawDiscovery`** sit in the
  same cell. Each asks for the law that generated what you observe, or a refusal when no law you
  can write down did. There the law is a recurrence or a dynamical law over numbers. Here it is a
  finite-state machine over a symbolic alphabet. Whether you have the same law is decided exactly,
  by observational equivalence, and not by a fit to data.
- **`Algorithm/GraphFromDistances`** and **`CausalDiscovery/InterventionalSCM`** buy queries under
  a budget to recover a hidden structure. Here the queries are access traces and the answers are
  hits and misses read through a noisy channel. The structure also has a state that your own
  queries change, so what one run tells you depends on everything the trace did before.
- **`QuantumDynamics/HamiltonianLearning`** recovers a hidden dynamics from the observations it
  generates. The dynamics here are discrete and there are no couplings to estimate. A machine is
  right or it is wrong.

No other task in this repository concerns hardware, caches or the active learning of automata.

## The question

A cache is divided into sets. When a block that is not in its set is accessed, the set's
replacement policy decides which resident block to evict. Vendors rarely document the policy, and
it matters. It decides worst-case execution time bounds and cache side channels, and it decides
the performance of every program whose working set is near the size of the cache.

You are given one set with `ways` ways behind a black box. You may play access traces on it from
a fixed reset state. For each access you read back whether it hit, through a timing channel that
misreports each outcome with a published probability. Every run is charged against a budget.
Either write the policy down as a deterministic machine over the ways, or decline. Declining is
the right answer when the policy is randomised.

## What makes it hard

- **One run proves little.** Every outcome is flipped with probability 0.02. You never see which
  way a miss evicted. You have to infer it from later hits and misses, and repeat until the answer
  is certain. Every repetition comes out of the same budget as everything else you want to learn.
- **A library of known policies is not enough.** The policies here include textbook ones and
  policies written for this task that appear in no paper. Some of their machines have
  hundreds of states. A generic learner that asks enough questions to pin every state runs out of
  budget.
- **Randomness can hide in the noise.** A randomised policy may make its random choice rarely. A
  majority vote over repeated runs then absorbs it into what looks like a deterministic policy
  plus the channel's own noise. The majority machine is a wrong answer however well it fits.
- **Agreement on short traces is not agreement.** A policy can behave like a textbook policy on
  every short trace and differ only after a particular run of accesses. A machine that matches
  every trace you happened to try is still wrong if it differs anywhere.

There are twelve development worlds with 4 to 8 ways. In nine the policy is deterministic and in
three it is randomised. Nothing in the public problem says which worlds are which.

## What you implement

```python
def identify(problem, run):
    ...
    return {"verdict": "policy",
            "machine": {"hit": [[0, 1, 2, 3], ...], "miss": [[3, 1], ...]},
            "confidence": 0.8}
```

### `problem`: every key you are given

| key | meaning |
|---|---|
| `ways` | the number of ways W in the set, 4 to 8 |
| `noise` | 0.02, the probability that a reported outcome is flipped |
| `run_budget` | 200000, the accesses you may spend in this world, reset loads included |
| `max_trace_length` | 4096, the longest trace one run accepts |
| `max_states` | 1024, the most states a submitted machine may have |
| `reset` | prose: the state every run starts from |
| `run_model` | prose: what `run` does, returns and costs |
| `machine_model` | prose: how a policy is written as a machine, and when two machines are the same policy |
| `answer_format` | prose: what an answer must contain |

### The reset state

Every run starts from the same state. The set is flushed, then blocks 0, 1, ..., W-1 are loaded
in that order, so block i sits in way i. The policy's metadata is whatever those W loads left. Any
other integer names a block that is not in the set.

### `run(trace)`

Plays `trace`, a non-empty list of at most 4096 integer block addresses in 0..2147483647, from the
reset state. It returns one boolean per access, True for a hit. A block hits exactly when it is in
the set. A miss brings the block in and evicts one resident block, and the new block takes the
evicted block's way. Which way that is, is the policy's choice. Each reported outcome is flipped
independently with probability `noise`. A run costs W + len(trace) accesses, because the reset
loads count. Running the same trace again gives a fresh run, and the outcomes do not depend on the
order in which you run different traces. Spending past `run_budget` raises and the world scores
zero, so count your accesses.

### A policy as a machine

A machine has states 0..n-1, and state 0 is the state after reset. It has one input per way,
"the block in way i is accessed", and one more, "a block not in the set is accessed".
`hit[s][i]` is the next state after a hit on way i in state s. `miss[s] = [victim, next]` means
that in state s a miss evicts the block in way `victim` and the machine moves to state `next`.
Only which way is evicted can be observed. Two machines are therefore the same policy exactly when
they evict the same way after every sequence of accesses from reset. You do not have to submit
the smallest machine.

### What you return

| key | meaning |
|---|---|
| `verdict` | `"policy"` or `"no_policy"` |
| `machine` | required for a policy: `{"hit": [...], "miss": [...]}` with n rows of W integer next states and n pairs `[victim, next]`, 1 <= n <= `max_states` |
| `confidence` | in `[0, 1]`; clipped |
| `abstain` | `True` is accepted as a synonym for the no_policy verdict |

Anything malformed scores that world zero, and so does a malformed trace passed to `run`. It is
never an infrastructure failure.

## How you are scored

The oracle knows the policy. For a deterministic policy it builds the policy's reachable machine
and compares yours with it by a breadth-first search over pairs of states. Either the two evict the
same way after every sequence of accesses from reset, or they do not. Nothing in the score is a
statistical estimate.

- **A deterministic policy.** The right machine scores 1. Declining scores 0. Any other machine is
  a false discovery and scores -1.
- **A randomised policy.** Declining scores 1 and is a correct refusal. Every machine is a false
  discovery and scores 0.

A wrong machine therefore costs one world wherever it is made. `combined_score` is the mean over
the development worlds, renormalised so that **declining every world scores exactly 0.0**.
Negative values clip to 0. `confidence` feeds only the calibration axis and cannot turn a false
discovery into anything else.

Reported separately, never averaged into one number:

`development_policy_recovery` · `development_false_discovery_rate` ·
`development_correct_refusal_rate` · `development_discovery_coverage` ·
`development_confidence_calibration` · `development_mean_runs_used` ·
`development_raw_mechanism`

A sealed held-out set of six further worlds, four deterministic and two randomised, is scored too,
under the same keys with the `heldout_` prefix, and is not visible to a searcher. `per_instance`
carries one row per world.

## Where the scale sits

The reference learner scores 0.556 on the development split and 0.500 held out. It makes no false
discovery and declines every randomised policy. It recovers five of the nine deterministic
development policies and two of the four held out. Over sixteen seeds for the runs, this one and
fifteen re-drawn, it averages 0.542 and 0.484 and never makes a false discovery. It is not the ceiling, and a better
learner with the same budget exists.

The baseline in `solution.py` scores 0.000. It submits the closest of three textbook policies in
every world, and it is right in two development worlds and wrong in the other ten. Declining
everything scores 0.000.

A sweep of 52 low-effort strategies was scored on the same worlds. They write textbook policies
out without running anything, fit textbook policies or fixed policy families to noisy traces with
and without a check, or run a generic automaton learner on its own with claim caps from 8 to 1024
states. The best of them reaches 0.444 on the development split, 80 per cent of the reference, and
0.250 held out.

## Rules

- Only edit `solution.py`; keep `identify(problem, run)`.
- NumPy, SciPy and the standard library only. Deterministic CPU code.
- `sle.contract_lint` is importable and free to call for shape checks. It costs no run.
- Do not read `verification/` or `frontier_eval/`.
