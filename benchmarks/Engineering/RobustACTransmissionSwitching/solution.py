"""Weak but legal fixed-topology baseline."""


def optimize_switching(problem, evaluate_plan):
    result = evaluate_plan({"open_lines": [], "generator_1_share": 0.40})
    return {"plan_id": result["plan_id"]}

