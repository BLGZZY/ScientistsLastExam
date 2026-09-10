#!/usr/bin/env python3
"""Scoped Linux evidence: secure witnesses/ablations and bounded shortcut probes.

No model calls. Builder probes access evaluator labels only to score a fixed grid
on development, then evaluate the selected strategy once on heldout. They are not
independent model calibration or a proof that every shortcut has been excluded.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import itertools
import json
import platform
import sys
import tempfile
from pathlib import Path
import numpy as np
import scipy
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sle.evaluate import evaluate_candidate
from sle.provenance import source_provenance, finalize_report_trust
from sle.registry import find_task
TASKS = {'Neuroscience/NeuralReportAttribution': ('reference_fit.py', 'infer_circuit', ['one_unit', 'ignore_instruments'])}

def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def shortcut_probe(spec):
    module = load(spec.task_dir / 'verification/evaluator.py')
    dark = spec.task_id.startswith('ParticlePhysics/')
    kinds = ['recurrent', 'report_only'] * 3 + ['none'] * 2 + ['unsupported'] * 2
    bases = (381900, 527300)
    step = 113
    cache = []
    for base in bases:
        rows = []
        for (i, kind) in enumerate(kinds):
            world = module.make_world(base + i * step, kind)
            lab = module.Campaign(world)
            obs = lab({'kind': 'response', 'report': 1, 'frequency': 0, 'units': 1})
            h = np.array(obs['real']) + 1j * np.array(obs['imag'])
            a = -np.linalg.pinv(h).real
            feature = (float(a[1, 2]), float(a[1, 3]))
            rows.append((world, feature))
        cache.append(rows)
    grid = itertools.product(np.linspace(-0.2, 0.3, 9), np.linspace(0.2, 1.8, 12), np.linspace(0.2, 1.8, 9))

    def score(config, rows):
        utilities = []
        for (world, feature) in rows:
            (threshold, scale_f, scale_r) = config
            (f, r) = feature
            answer = {'model': 'recurrent' if f > threshold else 'report_only', 'feedback': float(np.clip(f * scale_f, 0, 1.2)) if f > threshold else 0.0, 'report_feedback': float(np.clip(r * scale_r, 0, 1.2))}
            utilities.append(module.score_world(world, answer)['mechanism'])
        return max(0.0, (sum(utilities) / len(utilities) - 0.2) / 0.8)
    best = (-1, None)
    count = 0
    for config in grid:
        count += 1
        value = score(config, cache[0])
        if value > best[0]:
            best = (value, config)
    return {'strategies': count, 'development_best': best[0], 'selected_parameters': [float(v) for v in best[1]], 'heldout_selected_once': score(best[1], cache[1]), 'observations': 'uncalibrated one-response inverse transfer entries', 'scope': 'finite builder probe, not exhaustive shortcut exclusion'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args()
    if platform.system() != 'Linux':
        raise SystemExit('Run scoped evidence on Linux with Bubblewrap; local unit checks are separate.')
    report = {'schema_version': 1, 'source_provenance': source_provenance(ROOT), 'environment': {'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__, 'scipy': scipy.__version__}, 'evidence_scope': 'secure baselines, truth-blind witnesses and ablations; builder-only finite probes', 'model_calibration': 'not_run_no_configured_model_endpoint', 'tasks': []}
    passed = True
    for (task_id, (filename, entry, ablations)) in TASKS.items():
        spec = find_task(task_id, include_uncertified=True)
        reference = spec.task_dir / 'verification' / filename
        rows = {}
        for (name, path) in (('baseline', spec.initial_program_path), ('reference', reference)):
            first = evaluate_candidate(spec, path, timeout_s=args.timeout)
            second = evaluate_candidate(spec, path, timeout_s=args.timeout)
            ok = first == second and first.get('valid') == 1 and (not first.get('infrastructure_failure'))
            if name == 'baseline':
                ok = ok and first.get('combined_score') == 0
            passed = passed and ok
            rows[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'deterministic': first == second, 'metrics': first, 'passed': ok}
            print(task_id, name, first.get('combined_score'), 'passed', ok, flush=True)
        rows['ablations'] = {}
        for ablation in ablations:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'candidate.py'
                source = reference.read_text().replace('ablation=None', f'ablation={ablation!r}', 1)
                path.write_text(source)
                metrics = evaluate_candidate(spec, path, timeout_s=args.timeout)
                valid = metrics.get('valid') == 1 and (not metrics.get('infrastructure_failure'))
                passed = passed and valid
                rows['ablations'][ablation] = {'candidate_sha256': hashlib.sha256(source.encode()).hexdigest(), 'metrics': metrics, 'delta_from_reference': rows['reference']['metrics']['combined_score'] - metrics['combined_score']}
                print(task_id, ablation, metrics.get('combined_score'), flush=True)
        rows['shortcut_probe'] = shortcut_probe(spec)
        rows['task'] = task_id
        report['tasks'].append(rows)
    finalize_report_trust(report, passed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return 0 if passed else 1
if __name__ == '__main__':
    raise SystemExit(main())
