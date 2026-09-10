"""Recompute PR 20 method probes; local diagnostics, not model calibration.

Run: python .research/pr20_diagnostics.py --output /absolute/path/report.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load(task, relative):
    path = ROOT / 'benchmarks/EarthScience' / task / relative
    spec = importlib.util.spec_from_file_location(task + relative.replace('/', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    task = 'FocalMechanismStressInversion'
    oracle = load(task, 'verification/evaluator.py')
    reference = load(task, 'verification/reference_solver.py')
    rows = {}

    def measure(name, candidate):
        start = time.monotonic()
        metrics = oracle.evaluate(candidate)
        rows[name] = {k: v for k, v in metrics.items() if isinstance(v, (float, int, bool))}
        rows[name]['wall_seconds'] = time.monotonic() - start
        print(name, rows[name]['combined_score'], rows[name]['robustness_score'], flush=True)

    measure('full_reference', reference.infer_stress_orientation)
    measure('no_reanalysis', lambda problem, reanalyze, budget: reference.infer_stress_orientation(problem, reanalyze, 0))
    reference.MEAN_MISFIT_DEG = float('inf')
    reference.TAIL_FRACTION = float('inf')
    measure('no_refusal', reference.infer_stress_orientation)
    for azimuth in range(0, 360, 30):
        def constant(problem, reanalyze, budget, azimuth=azimuth):
            return {'sigma1': [azimuth, 0.], 'sigma3': [(azimuth + 90) % 360, 0.],
                    'R': .5, 'plane_assignments': [0] * problem['event_count'],
                    'abstain': False, 'confidence': .5}
        measure('constant_%03d' % azimuth, constant)
    report = {'scope': 'local_method_diagnostics_not_model_calibration',
              'platform': platform.platform(), 'numpy': np.__version__,
              'task': task, 'difficulty': oracle.DIFFICULTY, 'results': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
