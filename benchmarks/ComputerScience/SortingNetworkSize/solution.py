"""Generic zero anchor: Batcher odd-even mergesort with +infinity padding.

No published network data are used. The output counts at n=13..17 are
48/53/59/63/85. Smaller valid networks make progress toward the cited lower bound.
"""

def build_network(n: int):
    """Batcher odd-even mergesort on N = 2^ceil(log2 n) wires, sentinel gates removed.

    A sorting network on N >= n wires restricted to the real wires (padding with +inf
    sentinels makes every gate touching a sentinel a no-op) still sorts the first n
    wires, so deleting those gates yields a legal baseline network for any n.
    """
    size = 1
    while size < n:
        size <<= 1
    net = []

    def compare(i: int, j: int) -> None:
        if max(i, j) < n:
            net.append([min(i, j), max(i, j)])

    def merge(lo: int, length: int, r: int) -> None:
        m = r * 2
        if m < length:
            merge(lo, length, m)
            merge(lo + r, length, m)
            for i in range(lo + r, lo + length - r, m):
                compare(i, i + r)
        else:
            compare(lo, lo + r)

    def sort(lo: int, length: int) -> None:
        if length > 1:
            sort(lo, length // 2)
            sort(lo + length // 2, length // 2)
            merge(lo, length, 1)

    sort(0, size)
    return net
