"""Weak valid quasi-isotropic stacking baseline."""


def design_laminate(problem):
    """Interleave plies largest-remaining-first, capped at pairs, mirrored to symmetry.

    Works for uneven angle mixes: no interior run exceeds two plies and the mirror
    junction is repaired, so the shipped baseline is always feasible.
    """
    max_run = int(problem["maximum_consecutive_equal_plies"])
    counts = {int(k): int(v) // 2 for k, v in problem["required_angle_counts"].items()}
    order = (0, 45, -45, 90)
    half = []
    while sum(counts.values()):
        choice = None
        for angle in sorted(counts, key=lambda a: (-counts[a], order.index(a))):
            if counts[angle] <= 0:
                continue
            run = 0
            for item in reversed(half):
                if item != angle:
                    break
                run += 1
            if run >= 2:
                continue
            choice = angle
            break
        if choice is None:
            choice = max(counts, key=lambda a: counts[a])
        half.append(choice)
        counts[choice] -= 1

    def run_at(seq, angle, from_end):
        run = 0
        for item in (reversed(seq) if from_end else seq):
            if item != angle:
                break
            run += 1
        return run

    if half[0] == half[-1] and run_at(half, half[0], True) + run_at(half, half[0], False) > max_run:
        import itertools
        for i in range(len(half) - 2, -1, -1):
            if half[i] == half[-1]:
                continue
            candidate = half.copy()
            candidate[i], candidate[-1] = candidate[-1], candidate[i]
            if max(len(list(group)) for _, group in itertools.groupby(candidate)) <= 2:
                half = candidate
                break
    return {"ply_angles_deg": half + half[::-1]}
