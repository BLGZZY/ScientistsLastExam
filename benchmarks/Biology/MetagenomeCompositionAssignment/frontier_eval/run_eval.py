"""Task-local black-box entrypoint for metagenome composition evaluation.

The candidate is evaluated only through ``python -m sle eval``, which keeps it
inside the repository's candidate sandbox. This wrapper publishes the small
selection allowlist and discards held-out and per-world diagnostics instead of
placing them beside the searcher's metrics file.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
TASK_ID = "Microbiology/MetagenomeCompositionAssignment"
EVAL_TIMEOUT_S = 600.0
SEARCH_VISIBLE_KEYS = (
    "combined_score",
    "valid",
    "feasibility_rate",
    "constraint_violations",
    "raw_score",
    "error_message",
    "timeout",
)
SENSITIVE_MARKERS = (
    "API_KEY",
    "AUTHORIZATION",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "CREDENTIAL",
)
EXPECTED_TASK_DIR = Path(__file__).resolve().parents[1].name
if TASK_ID.rsplit("/", 1)[-1] != EXPECTED_TASK_DIR:
    raise SystemExit("TASK_ID does not match this task directory")


def _child_environment():
    environment = {
        key: value
        for key, value in os.environ.items()
        if not any(marker in key.upper() for marker in SENSITIVE_MARKERS)
    }
    environment["PYTHONPATH"] = str(ROOT)
    return environment


def _clear_output(path):
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return False
    return True


def _write_public_metrics(path, metrics):
    rendered = json.dumps(metrics, indent=2, default=str, allow_nan=False) + "\n"
    temporary = path.with_name(".%s.%d.tmp" % (path.name, os.getpid()))
    try:
        temporary.write_text(rendered, encoding="utf-8")
        os.replace(str(temporary), str(path))
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--metrics-out", required=True)
    parser.add_argument("--timeout", type=float, default=EVAL_TIMEOUT_S)
    args = parser.parse_args(argv)
    output = Path(args.metrics_out).resolve()
    if not _clear_output(output):
        print("evaluation output could not be cleared", file=sys.stderr)
        return 2
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        print("evaluation timeout must be positive and finite", file=sys.stderr)
        return 2

    command = [
        sys.executable,
        "-m",
        "sle",
        "eval",
        "--task",
        TASK_ID,
        "--allow-uncertified",
        "--candidate",
        str(Path(args.candidate).resolve()),
        "--timeout",
        str(args.timeout),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=args.timeout + 120.0,
            env=_child_environment(),
        )
        if completed.returncode:
            print(
                "trusted evaluation infrastructure failed (exit %d)"
                % completed.returncode,
                file=sys.stderr,
            )
            return 2
        result = json.loads(completed.stdout)
        if not isinstance(result, dict):
            raise ValueError("trusted metrics are not an object")
        if result.get("infrastructure_failure"):
            print("trusted evaluation infrastructure failed", file=sys.stderr)
            return 2
        for key in ("combined_score", "valid"):
            value = result.get(key)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("trusted metrics require finite " + key)
        result.setdefault("raw_score", result["combined_score"])
        public = {key: result[key] for key in SEARCH_VISIBLE_KEYS if key in result}
        _write_public_metrics(output, public)
        print(json.dumps(public, default=str, allow_nan=False))
        return 0
    except (json.JSONDecodeError, OSError, subprocess.TimeoutExpired, ValueError):
        _clear_output(output)
        print("trusted evaluation infrastructure failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
