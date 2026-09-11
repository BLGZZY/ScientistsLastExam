"""Every number the task's documents quote, recomputed from the recorded runs and a fresh evaluation.

    .venv/bin/python .research/cache_policy/summary.py
"""
import collections
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from pkg_eval import CANDIDATES, ev  # noqa: E402


def jsonl(name):
    return [json.loads(line) for line in open(HERE / name)]


def fresh(name):
    for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
        spec["seed"] = ORIGINAL[spec["name"]]
    ev._WORLDS.clear()
    return ev.evaluate(CANDIDATES[name]())


ORIGINAL = {s["name"]: s["seed"] for s in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS}
for name in ("reference", "baseline"):
    m = fresh(name)
    print(name, {k: round(v, 4) for k, v in m.items() if isinstance(v, float)})
    print("  runs", [(r["split"][0] + "%02d" % (r["world_index"] + 1), r["runs_used"], r["mechanism_score"]) for r in m["per_instance"]])

robust = jsonl("pkg_reference_robust.jsonl")
dev, held = [r["dev"] for r in robust], [r["held"] for r in robust]
print("reference robustness: shifts", len(robust), "dev mean %.4f [%.4f, %.4f]" % (st.mean(dev), min(dev), max(dev)),
      "held mean %.4f [%.4f, %.4f]" % (st.mean(held), min(held), max(held)),
      "false discoveries", sum(1 for r in robust for x in r["rows"] if x[3]), "of", sum(len(r["rows"]) for r in robust))

ladder = collections.defaultdict(list)
for r in jsonl("ladder.jsonl") + jsonl("sweep.jsonl"):
    ladder[r["name"]].append(r)
ref = [r for r in ladder["reference"] if r["shift"] == 0][0]["dev"]
print("\n%-58s %6s %6s %6s %6s %5s %5s %4s %5s" % ("strategy", "g.dev", "g.held", "m.dev", "m.held", "fd.d", "fd.h", "n", "cov"))
for name, rs in sorted(ladder.items(), key=lambda kv: kv[0]):
    g = [r for r in rs if r["shift"] == 0][0]
    print("%-58s %6.3f %6.3f %6.3f %6.3f %5d %5d %4d %5.2f  %3.0f%%" % (
        name, g["dev"], g["held"], st.mean(r["dev"] for r in rs), st.mean(r["held"] for r in rs),
        sum(r["dev_fd"] for r in rs), sum(r["held_fd"] for r in rs), len(rs), g["dev_coverage"], 100 * g["dev"] / ref))
print("max run calls in one world, reference:", max(r["max_calls"] for r in ladder["reference"]),
      "total per evaluation:", [r["total_calls"] for r in ladder["reference"] if r["shift"] == 0][0])

det = jsonl("det_diag.jsonl")
for kind in ("deterministic", "randomized"):
    rows = [r for r in det if r["kind"] == kind]
    for n in ("24", "32"):
        zs = [r["det2"][n][0] for r in rows]
        ws = [r["det2"][n][1] for r in rows]
        print("det2 %-13s n=%s z [%.2f, %.2f] worst tail [%.2f, %.2f] det1 max %.2f  (%d world-runs)" % (
            kind, n, min(zs), max(zs), min(ws), max(ws), max(r["det1"] for r in rows), len(rows)))
for w in ("dev-10", "dev-11", "dev-12", "held-05", "held-06"):
    rows = [r for r in det if r["world"] == w]
    print("  %s min z at 24 %.2f, at 32 %.2f" % (w, min(r["det2"]["24"][0] for r in rows), min(r["det2"]["32"][0] for r in rows)))
