"""Recompute public-input reference, ablations and independent grid diagnostics.

Run only after recording a source freeze before inspecting revised held-out scores.
These are method diagnostics, not frontier-model calibration or server-held evidence.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import platform
import subprocess
import time
from pathlib import Path
import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / 'benchmarks/EarthScience/FocalMechanismStressInversion'
THRESHOLDS = (12., 16., 20., 22., 25., 28., 32.)
TRAIN_SEEDS = (61001, 61007, 61013, 61019, 61027, 61031, 61043, 61051, 61057, 61063, 61069, 61081)
CONFIRM_SEEDS = (71011, 71017, 71023, 71039, 71047, 71051, 71059, 71063, 71069, 71081, 71089, 71099)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def model_files():
    return [TASK/'verification/evaluator.py', TASK/'verification/reference_solver.py',
            ROOT/'.research/pr74_grid_probe.py', TASK/'solution.py']


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in model_files()}


def gated_row(row, kind, mean, threshold):
    row = dict(row)
    if not row["valid"] or mean <= threshold:
        return row
    supported = kind == 'supported'
    row.update(abstained=True, mechanism_score=0. if supported else 1.,
               axis_score=0. if supported else 1., r_score=0. if supported else 1.,
               plane_score=0. if supported else 1., false_discovery=False,
               correct_refusal=not supported, confidence_score=.99)
    return row


def run(split, output, only=None):
    oracle = load(TASK/'verification/evaluator.py', 'focal_diagnostic_oracle')
    if split in ('heldout', 'confirmation'):
        freeze = json.loads((ROOT/'.research/pr74_source_freeze.json').read_text())
        if freeze['source_sha256'] != hashes():
            raise RuntimeError('runtime source changed after freeze; do not relabel retuned holdout evidence')
    if split == 'development':
        specs = list(oracle._BASE_DEVELOPMENT_SPECS)
    elif split == 'heldout':
        specs = list(oracle.HELDOUT_SPECS)
    elif split == 'training':
        specs = [(s, 'supported') for s in TRAIN_SEEDS] + [(61103, 'mixed'), (61109, 'mixed'), (61121, 'incoherent')]
    else:
        specs = [(s, 'supported') for s in CONFIRM_SEEDS] + [(71107, 'mixed'), (71113, 'mixed'), (71119, 'incoherent')]
    methods = {}
    configurations = {
        'reference': {}, 'no_paid_reanalysis': {'budget': 0},
        'no_pair_averaging': {'pair_averaging': False}, 'no_precision_weighting': {'weighted': False},
        'fixed_first_reanalysis': {'query_policy': 'first'},
        'no_continuous_refinement': {'continuous': False},
    }
    for name, config in configurations.items():
        reference = load(TASK/'verification/reference_solver.py', 'reference_'+name)
        options = dict(config)
        budget_override = options.pop('budget', None)
        def wrap(reference, options, override):
            def wrapped(problem, callback, budget):
                answer, diagnostic = reference._solve(problem, callback, budget if override is None else override,
                                                       refusal_threshold=float('inf'), **options)
                wrapped.last = diagnostic
                return answer
            return wrapped
        methods[name] = wrap(reference, options, budget_override)
    baseline = load(TASK/'solution.py', 'focal_baseline')
    methods['baseline'] = baseline.infer_stress_orientation
    old = load(ROOT/'.research/pr74_reference_before.py', 'historical_focal_reference')
    methods['historical_reference_on_revised_oracle'] = old.infer_stress_orientation
    grids = [
        ('raw1728', (8, 6, 9, 4), False, 'first', 0),
        ('raw6912', (12, 8, 12, 6), False, 'first', 0),
        ('raw6912_worst', (12, 8, 12, 6), False, 'worst', 0),
        ('raw62208', (24, 12, 24, 9), False, 'first', 0),
        ('raw62208_refined', (24, 12, 24, 9), False, 'first', 3),
        ('paired6912', (12, 8, 12, 6), True, 'ambiguous', 0),
        ('paired62208', (24, 12, 24, 9), True, 'ambiguous', 0),
        ('paired62208_refined', (24, 12, 24, 9), True, 'ambiguous', 3),
    ]
    for name, shape, paired, query, rounds in grids:
        probe = load(ROOT/'.research/pr74_grid_probe.py', name)
        probe.GRID_SHAPE, probe.PAIRED, probe.QUERY_POLICY = shape, paired, query
        probe.LOCAL_ROUNDS, probe.THRESHOLD_DEG = rounds, float('inf')
        def wrap(probe):
            def wrapped(problem, callback, budget):
                answer = probe.infer_stress_orientation(problem, callback, budget)
                wrapped.last = probe.LAST_DIAGNOSTICS
                return answer
            return wrapped
        methods[name] = wrap(probe)
    report = {'scope': 'method_diagnostics_not_model_calibration', 'split': split,
              'source_sha256': hashes(), 'platform': platform.platform(),
              'numpy': np.__version__, 'scipy': scipy.__version__,
              'git_revision': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'git_status': subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
              'world_specs': specs, 'results': {}}
    for name, method in methods.items():
        if only and name not in only:
            continue
        started = time.monotonic()
        rows, diagnostics = [], []
        for i, spec in enumerate(specs):
            rows.append(oracle._evaluate_world(method, spec, split, i))
            diagnostics.append(copy.deepcopy(getattr(method, 'last', {})))
        result = {'wall_seconds': time.monotonic()-started, 'ungated_rows': rows, 'ungated_summary': oracle._summary(rows, specs),
                  'public_input_diagnostics': diagnostics}
        if all('mean_residual_deg' in d for d in diagnostics):
            result['threshold_sweep'] = {
                str(t): oracle._summary([gated_row(r,s[1],d['mean_residual_deg'],t)
                                       for r,s,d in zip(rows,specs,diagnostics)],specs)
                for t in THRESHOLDS}
            result['configured_summary'] = result['threshold_sweep']['20.0' if name in configurations else '25.0']
        else:
            result['configured_summary'] = oracle._summary(rows,specs)
        report['results'][name] = result
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,indent=2)+'\n')
        print(split, name, json.dumps(result['configured_summary']), round(result['wall_seconds'],2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=('development','training','heldout','confirmation'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args()
    run(args.split,args.output,args.only)
