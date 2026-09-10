#!/usr/bin/env python3
"""Read an optimization admission table and refuse to treat discovery as one Δ.

`report_admission_criterion.py` compares `combined_score` across paired arms. That is the
right question for optimization. For discovery it is the wrong one: a public score at 1.0
can sit on a held-out mechanism of 0.5 (SequenceLawRecovery, hy3-ioa Wave-1), and averaging
the triple pays a candidate that refuses every world.

This script does not invent a second Δ. It labels each admission row with the task's
scientific role, and for discovery it:

    * keeps the public-score verdict as a statement about the visible scalar only
    * refuses to promote that verdict to `measures_iteration`
    * lists which of mechanism / FDR / refusal are rates, counts-without-denominator,
      published on another split, or missing

Usage:
    python scripts/report_discovery_admission.py \\
        --admission experiments/opus5_admission_criterion_2026-09-02.json \\
        --output /tmp/discovery_admission.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sle.registry import list_tasks  # noqa: E402


def role_index() -> dict[str, str]:
    out = {}
    for spec in list_tasks(None):
        role = str(spec.metadata.get("scientific_role") or "")
        out[spec.task_id] = role
        out[spec.task_dir.name] = role
    return out


def classify_discovery_row(row: dict, role: str, axes: dict | None = None) -> dict:
    """Rewrite one admission row. Optimization rows pass through."""
    public = str(row.get("verdict") or "unknown")
    out = dict(row)
    out["scientific_role"] = role or "unspecified"
    if role != "discovery":
        return out
    out["public_score_verdict"] = public
    if public.startswith("measures_iteration"):
        out["verdict"] = "discovery_public_score_only"
        out["iteration_claim"] = (
            "not_from_combined_score: a discovery Δ on the public scalar is not an "
            "iteration claim; report mechanism, false-discovery and refusal separately"
        )
    elif public == "solved_at_ceiling":
        out["verdict"] = "public_score_at_ceiling"
        out["iteration_claim"] = (
            "public combined_score is at the ceiling; held-out mechanism may not be"
        )
    else:
        out["verdict"] = public
        out["iteration_claim"] = "public_score_only"
    axes = axes or {name: None for name in ("mechanism", "fdr", "refusal")}
    out["axes"] = axes
    out["count_without_denominator"] = [
        name for name, entry in axes.items()
        if entry is not None and entry.get("status") == "count_without_denominator"
    ]
    out["published_on_other_split"] = [
        name for name, entry in axes.items()
        if entry is not None and entry.get("status") == "published_on_other_split"
    ]
    out["missing_axes"] = [
        name for name in ("mechanism", "fdr", "refusal")
        if axes.get(name) is None
    ]
    return out


# Admission tables from report_admission_criterion.py are pooled across seeds.
# Triple reports are one row per run. Join on the run fields when both sides
# have them; otherwise require a unique coarse match instead of dropping axes.
COARSE_IDENTITY_FIELDS = (
    "task",
    "model",
    "llm_condition_sha256",
    "task_version",
    "runtime_source_sha256",
)
RUN_IDENTITY_FIELDS = COARSE_IDENTITY_FIELDS + ("seed", "feedback_mode")
IDENTITY_FIELDS = RUN_IDENTITY_FIELDS


def _identity_value(entry: dict, field: str) -> str:
    value = entry.get(field)
    return "" if value is None else str(value)


def triple_index(document: dict) -> dict[tuple[str, ...], dict]:
    """Index fully attributable triple rows by run identity, including seed and mode."""
    grouped: dict[tuple[str, ...], list[dict]] = {}
    for entry in document.get("rows") or []:
        if entry.get("status") != "ok":
            continue
        if any(entry.get(field) is None for field in COARSE_IDENTITY_FIELDS):
            continue
        key = tuple(_identity_value(entry, field) for field in RUN_IDENTITY_FIELDS)
        grouped.setdefault(key, []).append(entry)
    return {
        key: entries[0].get("axes")
        for key, entries in grouped.items()
        if len(entries) == 1
    }


def lookup_triple_axes(
    triples: dict[tuple[str, ...], dict], row: dict,
) -> tuple[dict | None, str]:
    """Join one admission row to triple axes without silently dropping multi-seed queues."""
    exact = tuple(_identity_value(row, field) for field in RUN_IDENTITY_FIELDS)
    if exact in triples:
        return triples[exact], "exact"
    named_run = row.get("seed") is not None or row.get("feedback_mode") is not None
    if named_run:
        return None, "no_match"
    coarse = tuple(_identity_value(row, field) for field in COARSE_IDENTITY_FIELDS)
    matches = [axes for key, axes in triples.items() if key[:5] == coarse]
    if len(matches) == 1:
        return matches[0], "unique_coarse"
    if len(matches) > 1:
        return None, "ambiguous_multi_run"
    return None, "no_match"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--admission", required=True,
                    help="JSON from report_admission_criterion.py")
    ap.add_argument("--output", required=True)
    ap.add_argument(
        "--triple",
        help="optional JSON from report_discovery_triple.py; absent axes are reported missing",
    )
    args = ap.parse_args(argv)

    document = json.loads(Path(args.admission).read_text(encoding="utf-8"))
    roles = role_index()
    triples = {}
    if args.triple:
        triple_doc = json.loads(Path(args.triple).read_text(encoding="utf-8"))
        triples = triple_index(triple_doc)
    rows_in = document.get("rows") or []
    rows = []
    for row in rows_in:
        task = str(row.get("task") or "")
        role = roles.get(task) or roles.get(task.split("/")[-1]) or ""
        axes, join_status = lookup_triple_axes(triples, row) if triples else (None, "no_triple")
        classified = classify_discovery_row(row, role, axes)
        classified["axes_join"] = join_status
        if join_status == "ambiguous_multi_run":
            classified["axes_join_reason"] = (
                "multiple triple runs share this identity; seed and feedback_mode "
                "are required to join axes"
            )
            classified["missing_axes"] = []
        rows.append(classified)

    discovery = [r for r in rows if r.get("scientific_role") == "discovery"]
    rewritten = sum(
        1 for r in discovery
        if r.get("verdict") != r.get("public_score_verdict")
    )
    report = {
        "schema_version": 2,
        "source_admission": str(Path(args.admission)),
        "note": (
            "Discovery rows never inherit measures_iteration from combined_score. "
            "Axes are not averaged. Multi-seed triple rows join on seed and "
            "feedback_mode; an admission row that omits them is not treated as "
            "missing every axis."
        ),
        "row_count": len(rows),
        "discovery_row_count": len(discovery),
        "discovery_verdicts_rewritten": rewritten,
        "discovery_rows_missing_axes": sum(
            bool(row.get("missing_axes")) for row in discovery
        ),
        "rows": rows,
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("discovery admission: %d rows, %d discovery, %d verdicts rewritten"
          % (len(rows), len(discovery), rewritten))
    print("report:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
