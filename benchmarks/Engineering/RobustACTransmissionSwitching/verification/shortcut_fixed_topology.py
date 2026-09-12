"""Cheap legitimate probe: tune participation but never change topology."""


def optimize_switching(problem, evaluate_plan):
    best = None
    for share in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75):
        result = evaluate_plan({"open_lines": [], "generator_1_share": share})
        if result["feasible"] and (best is None or result["robust_cost"] < best["robust_cost"]):
            best = result
    if best is None:
        best = evaluate_plan({"open_lines": [], "generator_1_share": 0.40})
    return {"plan_id": best["plan_id"]}
