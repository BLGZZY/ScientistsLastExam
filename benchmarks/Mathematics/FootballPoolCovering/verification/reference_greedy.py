"""Data-free set-cover diagnostic: exact greedy gains and reverse deletion.

No record data or evaluator imports. Each call creates a local seeded RNG for
tie ranks. The algorithm examines all candidate balls at each greedy step.
This diagnostic is not a competitive research search reference.
"""

import argparse
import json

import numpy as np


def build_greedy_covering(n: int, seed: int = 0):
    """Return a full radius-one cover using fixed-rank greedy set cover."""
    if n not in range(6, 11):
        raise ValueError("unsupported covering length")
    total = 3 ** n
    values = np.arange(total, dtype=np.int32)
    words = np.array([(values // (3 ** i)) % 3 for i in range(n)],
                     dtype=np.int8).T
    balls = np.empty((total, 2 * n + 1), dtype=np.int32)
    balls[:, 0] = values
    for i in range(n):
        # Cast before multiplication: int8 deltas can overflow positional weights.
        digit = words[:, i].astype(np.int32)
        place = 3 ** i
        balls[:, 2 * i + 1] = values + (((digit + 1) % 3) - digit) * place
        balls[:, 2 * i + 2] = values + (((digit + 2) % 3) - digit) * place

    rng = np.random.default_rng(seed + n * 1009)
    order = rng.permutation(total)
    rank = np.empty(total, dtype=np.int32)
    rank[order] = np.arange(total)
    gains = np.full(total, 2 * n + 1, dtype=np.int32)
    covered = np.zeros(total, dtype=bool)
    code = []
    while not covered.all():
        # A one-unit gain improvement dominates every tie-rank difference.
        choice = int(np.argmax(gains * (total + 1) - rank))
        fresh = balls[choice][~covered[balls[choice]]]
        code.append(choice)
        covered[fresh] = True
        # Radius-one adjacency is symmetric. Remove one gain for each newly
        # covered word from every candidate ball containing that word.
        np.subtract.at(gains, balls[fresh].reshape(-1), 1)

    counts = np.bincount(balls[code].reshape(-1), minlength=total)
    for index in reversed(range(len(code))):
        if np.all(counts[balls[code[index]]] > 1):
            counts[balls[code[index]]] -= 1
            code.pop(index)
    return words[code].tolist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("n", type=int, choices=range(6, 11))
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(build_greedy_covering(args.n, args.seed)))
