"""Pinned invariants for FootballPoolCovering.

The tests pin the exact coverage checker (a base-3 index marking pass over all 3^n
words), its neighbour arithmetic (no positional carry), the Hamming-product baseline's
exact 0.0 anchor, the ledger/evaluator anchor match, and fail-closed behaviour
against malformed candidates. They reverify attributed public constructions and their independent raw metrics.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import random
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks" / "Mathematics" / "FootballPoolCovering"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def digits_of(x: int, n: int):
    d = []
    for _ in range(n):
        d.append(x % 3)
        x //= 3
    return d


def brute_covers(code, n: int) -> bool:
    """Independent O(3^n * |C| * n) Hamming-distance coverage check."""
    for x in range(3 ** n):
        wx = digits_of(x, n)
        if not any(sum(1 for a, b in zip(w, wx) if a != b) <= 1 for w in code):
            return False
    return True


def perfect_ternary_hamming_4():
    """The [4, 2, 3]_3 Hamming code: 9 words covering all 81 words of {0,1,2}^4
    at radius 1 exactly (9 * 9 = 81, a perfect code). Independent anchor: the
    proven value K_3(4,1) = 9."""
    return [w for w in itertools.product(range(3), repeat=4)
            if (w[0] + w[2] + w[3]) % 3 == 0 and (w[1] + w[2] + 2 * w[3]) % 3 == 0]


class FootballPoolCoveringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ev = _load(TASK / "verification" / "evaluator.py", "fpc_evaluator")
        cls.sol = _load(TASK / "solution.py", "fpc_baseline")

    # --------------------------------------------- exact coverage checker

    def test_exported_reference_runs_without_adjacent_data_files(self):
        reference = _load(TASK / "verification/reference_reconstruction.py", "export_reference")
        namespace = {}
        exec(compile(reference.export_source(), "isolated_reference.py", "exec"), namespace)
        for n in self.ev.SIZES:
            self.assertEqual(namespace["build_covering"](n), reference.build_covering(n))

    def test_checker_agrees_with_brute_force_on_random_codes(self):
        rng = random.Random(20260908)
        for n in (2, 3, 4, 5):
            for _ in range(20):
                size = rng.randint(1, min(3 ** n, 18))
                code = [[rng.randrange(3) for _ in range(n)] for _ in range(size)]
                ok, sz, reason = self.ev.verify_covering(code, n)
                self.assertEqual(ok, brute_covers(code, n), (n, code, reason))
                self.assertEqual(sz, size)

    def test_checker_rejects_code_missing_exactly_one_word(self):
        # delete the whole radius-1 ball around a target word: the target is then
        # provably uncovered, and putting back one ball word must repair it
        for n in (3, 4):
            target = digits_of(3 ** n // 2, n)
            def dist1(w):
                return sum(1 for a, b in zip(w, target) if a != b) <= 1
            code = [w for w in itertools.product(range(3), repeat=n) if not dist1(w)]
            ok, _, reason = self.ev.verify_covering([list(w) for w in code], n)
            self.assertFalse(ok, n)
            self.assertIn("not covered", reason)
            self.assertFalse(brute_covers(code, n))
            repaired = [list(w) for w in code] + [list(target)]   # distance 0 back in
            ok2, _, _ = self.ev.verify_covering(repaired, n)
            self.assertTrue(ok2, n)

    def test_neighbour_marking_has_no_positional_carry(self):
        # A single all-2s word exercises every digit at its maximum: a buggy
        # neighbour index (idx + 3^i instead of a symbol-dependent delta) would
        # carry out of the array at 3^n - 1 + 1 and crash or mark a wrong word.
        for n in (3, 5, 7):
            ok, size, _ = self.ev.verify_covering([[2] * n], n)
            self.assertFalse(ok)                          # 1 word never covers
            self.assertEqual(size, 1)
            # and the closed ball of radius 1 around the all-0 word covers exactly
            # the words at distance <= 2 from 0, so it must not cover anything else
            ball = [digits_of(x, n) for x in range(3 ** n)
                    if sum(1 for d in digits_of(x, n) if d != 0) <= 1]
            self.assertEqual(len(ball), 2 * n + 1)
            ok2, _, _ = self.ev.verify_covering(ball, n)
            self.assertEqual(ok2, brute_covers(ball, n))
            self.assertFalse(ok2)

    def test_perfect_ternary_hamming_code_is_a_valid_9_word_covering(self):
        code = [list(w) for w in perfect_ternary_hamming_4()]
        self.assertEqual(len(code), 9)
        self.assertEqual(len({tuple(w) for w in code}), 9)
        ok, size, reason = self.ev.verify_covering(code, 4)
        self.assertTrue(ok, reason)
        self.assertEqual(size, 9)
        self.assertTrue(brute_covers(code, 4))

    def test_tripled_perfect_code_covers_n5_with_27_words(self):
        c4 = perfect_ternary_hamming_4()
        code = [[a] + list(w) for a in range(3) for w in c4]
        ok, size, _ = self.ev.verify_covering(code, 5)
        self.assertTrue(ok)
        self.assertEqual(size, 27)                        # the proven K_3(5,1) = 27

    # --------------------------------------------- baseline and anchors

    def test_baseline_is_valid_and_scores_exactly_zero_everywhere(self):
        for n, ref in sorted(self.ev.SIZES.items()):
            self.assertEqual(ref["baseline"], 9 * 3 ** (n - 4))
            raw = self.sol.build_covering(n)
            ok, size, reason = self.ev.verify_covering(raw, n)
            self.assertTrue(ok, (n, reason))
            self.assertEqual(size, 9 * 3 ** (n - 4))
        result = self.ev.evaluate(self.sol.build_covering)
        self.assertEqual(result["combined_score"], 0.0)
        self.assertEqual(result["valid"], 1.0)
        self.assertFalse(result["beat_sota"])

    def test_known_best_ledger_matches_evaluator_anchors(self):
        text = (TASK / "references" / "known_best.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", text, re.M)
        ledger = {int(n): (int(base), int(rec)) for n, base, rec in rows}
        self.assertEqual(set(ledger), set(self.ev.SIZES))
        for n, ref in self.ev.SIZES.items():
            self.assertEqual(ledger[n], (ref["baseline"], ref["sota_ref"]), n)
        entries = json.loads((TASK / "references" / "anchors.json").read_text())["anchors"]
        bounds = {entry["name"]: entry["value"] for entry in entries}
        for n, ref in self.ev.SIZES.items():
            self.assertEqual(bounds[f"lower_bound_n{n}"], ref["lower_bound"])

    def test_record_sizes_are_strictly_below_baselines(self):
        for n, ref in self.ev.SIZES.items():
            self.assertLess(ref["sota_ref"], ref["baseline"], n)
            self.assertLess(ref["lower_bound"], ref["sota_ref"], n)

    def test_hamming_product_is_a_valid_cover_without_record_data(self):
        for n in (4, 5, 6):
            code = self.sol.build_covering(n)
            self.assertTrue(brute_covers(code, n))
            self.assertEqual(len(code), 3 ** (n - 2))

    def test_reconstruction_and_greedy_remain_separate_methods(self):
        reconstruction = _load(TASK / "verification" / "reference_reconstruction.py", "fpc_reconstruction")
        metrics = self.ev.evaluate(reconstruction.build_covering)
        self.assertEqual(metrics["valid"], 1.0)
        self.assertGreater(metrics["combined_score"], 0.0)
        self.assertLess(metrics["combined_score"], 1.0)
        self.assertEqual(metrics["raw_score"], -(73 + 186 + 486 + 1458 + 4374) / 5)
        for row in metrics["per_n"]:
            self.assertGreater(row["lower_bound_gap"], 0)
            self.assertFalse(row["target_attained"])
            if row["n"] <= 8:
                self.assertEqual(row["record_gap"], 0)
        greedy = _load(TASK / "verification" / "reference_greedy.py", "fpc_greedy")
        first = greedy.build_greedy_covering(6, seed=0)
        self.assertTrue(self.ev.verify_covering(first, 6)[0])
        import numpy as np
        np.random.seed(123)
        np.random.random(100)
        self.assertEqual(first, greedy.build_greedy_covering(6, seed=0))

    def test_reconstruction_asset_matches_attributed_hash(self):
        import hashlib
        sources = json.loads((TASK / "references" / "reference_sources.json").read_text())
        for entry in sources["files"]:
            self.assertEqual(hashlib.sha256((TASK / entry["path"]).read_bytes()).hexdigest(), entry["sha256"])

    def test_clipped_target_is_the_lower_bound_not_a_record(self):
        helper = self.ev._normalized
        self.assertEqual(helper(-81, -81, -71), 0.0)
        self.assertAlmostEqual(helper(-73, -81, -71), 0.8)
        # Formula test only: existence of a 71-word covering is not assumed.
        self.assertEqual(helper(-71, -81, -71), 1.0)
        self.assertEqual(helper(-70, -81, -71), 1.0)

    # --------------------------------------------- contract edges

    def test_duplicates_are_legal_but_counted(self):
        word = [0] * 6
        ok, size, _ = self.ev.verify_covering([list(word), list(word)], 6)
        self.assertFalse(ok)                              # 2 words never cover 729
        rng = random.Random(5)
        base = self.sol.build_covering(6)
        doubled = base + [list(rng.choice(base)) for _ in range(10)]
        ok, size, _ = self.ev.verify_covering(doubled, 6)
        self.assertTrue(ok)
        self.assertEqual(size, len(base) + 10)

    def test_numpy_and_integral_float_symbols_are_accepted(self):
        import numpy as np
        raw = self.sol.build_covering(6)[:50]
        as_floats = [[float(s) for s in w] for w in raw]
        ok, size, _ = self.ev.verify_covering(as_floats, 6)
        self.assertFalse(ok)                              # 50 words cannot cover
        full = self.sol.build_covering(6)
        as_np = [np.array(w, dtype=np.int64) for w in full]
        ok, size, _ = self.ev.verify_covering(as_np, 6)
        self.assertTrue(ok)
        self.assertEqual(size, len(full))
        mixed = [[float(s) for s in w] for w in full]
        ok, size, _ = self.ev.verify_covering(mixed, 6)
        self.assertTrue(ok)

    # --------------------------------------------- malformed candidates

    def test_malformed_candidates_all_fail_closed_without_raising(self):
        n = 6
        word = [0] * n
        good = self.sol.build_covering(n)

        def infinite_words(_n):
            return ([0] * _n for _ in itertools.count())

        def too_many(_n):
            return [digits_of(x, _n) for x in range(3 ** _n + 1)]

        bads = [
            ("none", lambda _n: None),
            ("string", lambda _n: "012345"),
            ("dict", lambda _n: {"size": 73}),
            ("int", lambda _n: 73),
            ("float", lambda _n: 73.0),
            ("bool", lambda _n: True),
            ("raises", lambda _n: (_ for _ in ()).throw(ValueError("boom"))),
            ("empty", lambda _n: []),
            ("infinite generator", infinite_words),
            ("over cap", too_many),
            ("word wrong length", lambda _n: good[:10] + [[0] * (_n - 1)] + good[10:]),
            ("word too long", lambda _n: [[0, 1] * _n]),
            ("bad symbol 0.5", lambda _n: [[0.5] + [0] * (_n - 1)]),
            ("bad symbol NaN", lambda _n: [[float("nan")] + [0] * (_n - 1)]),
            ("bad symbol inf", lambda _n: [[float("inf")] + [0] * (_n - 1)]),
            ("bad symbol string", lambda _n: [["0"] + [0] * (_n - 1)]),
            ("bad symbol bool", lambda _n: [[True] + [0] * (_n - 1)]),
            ("symbol out of range", lambda _n: [[3] + [0] * (_n - 1)]),
            ("symbol negative", lambda _n: [[-1] + [0] * (_n - 1)]),
            ("row scalar", lambda _n: [5] * 20),
            ("row none", lambda _n: [None] * 20),
            ("row dict", lambda _n: [{"w": 0}] * 20),
            ("infinite row", lambda _n: [(s for s in itertools.repeat(0))]),
            ("set of short words", lambda _n: {tuple(w[:-1]) for w in good}),
        ]
        self.assertGreaterEqual(len(bads), 10)
        for name, fn in bads:
            with self.subTest(malformed=name):
                res = self.ev.evaluate(fn)                 # must not raise, must not hang
                self.assertEqual(res["combined_score"], 0.0, name)
                self.assertEqual(res["raw_score"], 0.0, name)
                self.assertEqual(res["valid"], 0.0, name)
                self.assertEqual(res["feasibility_rate"], 0.0, name)
                self.assertFalse(res["beat_sota"], name)

    def test_single_valid_instance_is_reported_per_n(self):
        # a candidate valid only on n = 6 still reports the others as invalid
        good6 = self.sol.build_covering(6)
        res = self.ev.evaluate(lambda _n: good6 if _n == 6 else None)
        self.assertEqual(res["valid"], 0.0)
        self.assertEqual(res["feasibility_rate"], 0.2)
        per = {r["n"]: r for r in res["per_n"]}
        self.assertTrue(per[6]["valid"])
        self.assertEqual(per[6]["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
