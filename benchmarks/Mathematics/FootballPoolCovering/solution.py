"""Generic zero anchor: a perfect four-coordinate Hamming code times free suffixes.

The two parity checks yield nine words covering all 81 four-symbol inputs.
Appending every suffix preserves radius one and costs 9*3**(n-4) words.
No published record code is used.
"""

import itertools


def build_covering(n: int):
    """Extend the [4,2,3]_3 Hamming code with all possible length-(n-4) suffixes."""
    if n < 4:
        raise ValueError("this baseline requires n >= 4")
    c4 = [list(w) for w in itertools.product(range(3), repeat=4)
          if (w[0] + w[2] + w[3]) % 3 == 0
          and (w[1] + w[2] + 2 * w[3]) % 3 == 0]
    return [w + list(rest) for w in c4
            for rest in itertools.product(range(3), repeat=n - 4)]
