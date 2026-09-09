"""Replay the recorded incumbent for analysis without selecting on sealed metrics."""
from __future__ import annotations

import json
import math
from pathlib import Path


def _score(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("trajectory score must be a finite number")
    return float(value)


def read_incumbents(path: Path) -> list[dict]:
    """Return the selected artifact at every step, including the baseline.

    Modern traces record acceptance explicitly (a late result may be valid but not
    accepted). Legacy traces without that field use strict score improvement.
    """
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
              if line.strip()]
    return incumbent_events(events)


def incumbent_events(events: list[dict]) -> list[dict]:
    """Replay an in-memory batch snapshot using the same selection rule."""
    incumbent = None
    selected = []
    for step, event in enumerate(events):
        if not isinstance(event, dict) or event.get("step") != step:
            raise ValueError("trajectory steps must be contiguous from baseline zero")
        valid = event.get("valid")
        if valid not in (True, False, 0, 1):
            raise ValueError("trajectory validity must be boolean")
        score = _score(event.get("score"))
        if step == 0:
            if not valid:
                raise ValueError("trajectory baseline must be valid")
            incumbent = event
        else:
            accepted = event.get("accepted", bool(valid and score > _score(incumbent["score"])))
            if not isinstance(accepted, bool):
                raise ValueError("trajectory acceptance must be boolean")
            if accepted:
                if not valid or score <= _score(incumbent["score"]):
                    raise ValueError("accepted proposal must strictly improve the incumbent")
                incumbent = event
        if "best_score" in event and _score(event["best_score"]) != _score(incumbent["score"]):
            raise ValueError("recorded best score differs from the selected artifact")
        selected.append(incumbent)
    return selected
