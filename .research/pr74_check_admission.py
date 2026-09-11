"""Scientific separation audit. Exit 1 means draft blocker, not a software failure."""
import argparse
import json
import math


REQUIRED_PROBE = "paired62208_refined"


def score(summary):
    value = summary["normalized"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("normalized score must be finite and in [0, 1]")
    return value


def audit(reports):
    failures = []
    if not reports:
        failures.append({"reason": "missing_reports"})
    for report in reports:
        try:
            ref = score(report["results"]["reference"]["configured_summary"])
        except (KeyError, TypeError, ValueError) as exc:
            failures.append({"split": report.get("split"), "reason": "invalid_reference", "detail": str(exc)})
            continue
        if REQUIRED_PROBE not in report["results"]:
            failures.append({"split": report["split"], "reason": "missing_required_probe", "probe": REQUIRED_PROBE})
        for name, result in report["results"].items():
            if not name.startswith(("raw", "paired")):
                continue
            # Every independently swept threshold counts, not only the default gate.
            try:
                configured = score(result["configured_summary"])
                swept = [score(x) for x in result["threshold_sweep"].values()]
                if not swept:
                    raise ValueError("missing threshold sweep")
                # The fixed configuration must count even if omitted from a sweep.
                best = max([configured] + swept)
            except (KeyError, TypeError, ValueError) as exc:
                failures.append({"split": report["split"], "probe": name,
                                 "reason": "invalid_probe", "detail": str(exc)})
                continue
            # Decimal boundary values must not pass through floating-point rounding.
            gap_passed = ref > best + .15 and not math.isclose(ref, best + .15, rel_tol=0, abs_tol=1e-12)
            fraction_passed = best < .75 * ref and not math.isclose(best, .75 * ref, rel_tol=0, abs_tol=1e-12)
            if not (gap_passed and fraction_passed):
                failures.append({"split": report["split"], "probe": name,
                                 "reference": ref, "best_probe": best,
                                 "fixed_probe": configured,
                                 "absolute_gap": ref - best,
                                 "reference_required_above": max(best + .15, best / .75),
                                 "impossible_at_score_ceiling": best >= .75})
    return {"status": "BLOCKED" if failures else "separation_passed_not_certification",
            "requirements": {"absolute_gap_greater_than": .15, "probe_fraction_less_than": .75},
            "failures": failures}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+")
    args = parser.parse_args()
    reports = []
    for path in args.reports:
        with open(path) as source:
            payload = json.load(source)
        reports.extend(payload["reports"].values() if "reports" in payload else [payload])
    result = audit(reports)
    print(json.dumps(result, indent=2))
    raise SystemExit(result["status"] == "BLOCKED")
