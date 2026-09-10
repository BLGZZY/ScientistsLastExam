"""Scientific separation audit. Exit 1 means draft blocker, not a software failure."""
import argparse
import json


def audit(reports):
    failures = []
    for report in reports:
        ref = report["results"]["reference"]["configured_summary"]["normalized"]
        for name, result in report["results"].items():
            if not name.startswith(("raw", "paired")):
                continue
            # Every independently swept threshold counts, not only the default gate.
            best = max(x["normalized"] for x in result["threshold_sweep"].values())
            if ref <= best + .15 or best >= .75 * ref:
                failures.append({"split": report["split"], "probe": name,
                                 "reference": ref, "best_probe": best,
                                 "absolute_gap": ref - best})
    return {"status": "BLOCKED" if failures else "separation_passed_not_certification",
            "requirements": {"absolute_gap_greater_than": .15, "probe_fraction_less_than": .75},
            "failures": failures}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+")
    args = parser.parse_args()
    result = audit([json.load(open(path)) for path in args.reports])
    print(json.dumps(result, indent=2))
    raise SystemExit(result["status"] == "BLOCKED")
