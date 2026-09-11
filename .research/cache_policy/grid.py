"""A fixed grid of low-dimensional shortcut strategies on the package's own evaluator.

Every cell is assembled from the reference's parts through ladder.py's `learn`, with at least one
of the reference's four learners (library, permutation fit, L*, the checks) left out or replaced
by a textbook template fit. The grid is declared here in full before any cell runs; nothing is
added or dropped after a score is seen. One JSON line per cell and shift is appended to grid.jsonl.

    .venv/bin/python .research/cache_policy/grid.py list
    .venv/bin/python .research/cache_policy/grid.py run PART OF [shift ...]
    .venv/bin/python .research/cache_policy/grid.py best K [shift ...]

`run PART OF` runs cells PART, PART+OF, PART+2*OF, ... of the declared order (for parallel
processes); `best K` re-runs the K highest development cells of shift 0 on further shifts.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ladder import CALLS, CONFIGS, build, templates  # noqa: E402
from pkg_eval import ev  # noqa: E402

HERE = Path(__file__).parent

DET = {"det": {}, "pooled_only": {"per_position": False}, "position_only": {"pooled": False},
       "no_det": {"per_position": False, "pooled": False}}
CHECK = {"nocheck": {"check": False}, "c4": {"checks": 4}, "c16": {"checks": 16}, "c64": {"checks": 64},
         "c128": {"checks": 128}}
CAPS = (8, 16, 24, 32, 64, 128, 256, 1024)


def _cells():
    cells = []
    for name in sorted(templates(4)):
        cells.append(("blind_" + name, None))
    none = {"library": False, "lstar": False, "permfit": False}
    for loose in (0.005, 0.01, 0.02, 0.05, 0.1):
        for ck, c in CHECK.items():
            if ck == "c128":
                continue
            for dk, d in DET.items():
                cells.append(("template_l%g_%s_%s" % (loose, ck, dk), {**none, "templates": True, "loose": loose, **c, **d}))
    for ck, c in CHECK.items():
        if ck == "c128":
            continue
        for dk, d in DET.items():
            cells.append(("library_%s_%s" % (ck, dk), {"lstar": False, "permfit": False, **c, **d}))
            cells.append(("permfit_%s_%s" % (ck, dk), {"library": False, "lstar": False, **c, **d}))
            cells.append(("template_permfit_%s_%s" % (ck, dk), {"library": False, "lstar": False, "templates": True, **c, **d}))
    for cap in CAPS:
        for ck, c in CHECK.items():
            if ck == "nocheck":
                continue
            for dk in ("det", "no_det"):
                d = DET[dk]
                cells.append(("lstar_cap%d_%s_%s" % (cap, ck, dk), {"library": False, "permfit": False, "cap": cap, **c, **d}))
                cells.append(("library_lstar_cap%d_%s_%s" % (cap, ck, dk), {"permfit": False, "cap": cap, **c, **d}))
                cells.append(("permfit_lstar_cap%d_%s_%s" % (cap, ck, dk), {"library": False, "cap": cap, **c, **d}))
    for ck, c in CHECK.items():
        if ck == "c128":
            continue
        for dk in ("det", "no_det"):
            d = DET[dk]
            cells.append(("template_library_%s_%s" % (ck, dk), {"lstar": False, "permfit": False, "templates": True, **c, **d}))
            cells.append(("template_lstar_cap32_%s_%s" % (ck, dk), {"library": False, "permfit": False, "templates": True, **c, **d}))
    return cells


CELLS = _cells()


def _run(name, cfg, shift):
    original = {s["name"]: s["seed"] for s in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS}
    for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
        spec["seed"] = original[spec["name"]] + 7919 * shift
    ev._WORLDS.clear()
    CALLS.clear()
    CONFIGS["_grid"] = cfg or {}
    start = time.time()
    m = ev.evaluate(build(name if cfg is None else "_grid"))
    for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
        spec["seed"] = original[spec["name"]]
    rows = m["per_instance"]
    return {"name": name, "cfg": cfg, "shift": shift, "seconds": round(time.time() - start, 1),
            "dev": round(m["development_mechanism_score"], 4), "held": round(m["heldout_mechanism_score"], 4),
            "dev_fd": sum(r["false_discovery"] for r in rows if r["split"] == "development"),
            "held_fd": sum(r["false_discovery"] for r in rows if r["split"] == "heldout"),
            "dev_coverage": round(m["development_discovery_coverage"], 3),
            "max_calls": max(CALLS), "total_calls": sum(CALLS),
            "rows": [(r["split"][0] + "%02d" % (r["world_index"] + 1), r["mechanism_score"],
                      "FD" if r["false_discovery"] else "", r["runs_used"]) for r in rows]}


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "list":
        print(len(CELLS), "cells")
        for name, cfg in CELLS:
            print(name, json.dumps(cfg))
        sys.exit()
    if mode == "run":
        part, of = int(sys.argv[2]), int(sys.argv[3])
        shifts = [int(x) for x in sys.argv[4:]] or [0]
        chosen = CELLS[part::of]
    else:
        k = int(sys.argv[2])
        shifts = [int(x) for x in sys.argv[3:]] or [1, 2, 3, 4, 5, 6, 7]
        done = [json.loads(line) for line in open(HERE / "grid.jsonl")]
        top = sorted((r for r in done if r["shift"] == 0), key=lambda r: (-r["dev"], -r["held"]))[:k]
        by_name = dict(CELLS)
        chosen = [(r["name"], by_name[r["name"]]) for r in top]
    with open(HERE / "grid.jsonl", "a") as fh:
        for name, cfg in chosen:
            for shift in shifts:
                rec = _run(name, cfg, shift)
                fh.write(json.dumps(rec) + "\n"); fh.flush()
                print(name, shift, rec["dev"], rec["held"], rec["dev_fd"], rec["held_fd"], rec["seconds"], flush=True)
