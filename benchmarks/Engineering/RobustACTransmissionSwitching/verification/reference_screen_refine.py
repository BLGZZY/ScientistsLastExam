"""Truth-blind 48-call topology screening and participation-factor refinement."""

def optimize_switching(problem, evaluate_plan):
    lines = [row["id"] for row in problem["branches"] if row["switchable"]]
    records = []
    for opened in [[]] + [[line] for line in lines]:
        for share in (0.35, 0.475, 0.60, 0.725, 0.85):
            result = evaluate_plan({"open_lines": opened, "generator_1_share": share})
            if result["feasible"]:
                records.append(result)
    if not records:
        return {"plan_id": evaluate_plan({"open_lines": [],
                                            "generator_1_share": 0.40})["plan_id"]}
    best = min(records, key=lambda row: row["robust_cost"])
    # Spend the remaining eight calls on a high-share refinement for the empirically
    # useful single-line candidates; this leaves all double switches as headroom.
    for line in lines[:4]:
        for share in (0.775, 0.825):
            result = evaluate_plan({"open_lines": [line], "generator_1_share": share})
            if result["feasible"] and result["robust_cost"] < best["robust_cost"]:
                best = result
    return {"plan_id": best["plan_id"]}

