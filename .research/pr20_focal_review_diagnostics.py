"""Reproduce focal grid probes and final reference residuals; not calibration."""
import argparse
import hashlib
import importlib.util
import json
import platform
import time
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / 'benchmarks/EarthScience/FocalMechanismStressInversion'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    oracle = load(TASK / 'verification/evaluator.py', 'focal_oracle')
    reference = load(TASK / 'verification/reference_solver.py', 'focal_reference')
    last_fit = []
    fit = reference._fit

    def recording_fit(*inputs):
        result = fit(*inputs)
        last_fit[:] = result[1]
        return result

    # Observe the final residuals without altering the fit, decisions or outputs.
    reference._fit = recording_fit
    residuals = []

    def recording_reference(*inputs):
        submission = reference.infer_stress_orientation(*inputs)
        residuals.append({'mean_angle_deg':float(np.mean(last_fit)),
                          'tail_fraction':float(np.mean(np.asarray(last_fit) > 35.)),
                          'abstained':submission['abstain']})
        return submission

    paths = [TASK / 'verification/evaluator.py', TASK / 'verification/reference_solver.py',
             ROOT / '.research/pr20_focal_grid_probe.py', Path(__file__)]
    report = {'scope':'method_diagnostics_not_frontier_calibration',
              'platform':platform.platform(), 'numpy':np.__version__, 'scipy':scipy.__version__,
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'results':{}}
    candidates = {'reference':recording_reference}
    for name, shape, local in [('coarse_grid',(12,8,12,6),0),('dense_grid',(24,12,24,9),3)]:
        module = load(ROOT / '.research/pr20_focal_grid_probe.py',name)
        module.GRID = shape
        module.LOCAL_ROUNDS = local
        candidates[name] = module.infer_stress_orientation
    for name, candidate in candidates.items():
        started = time.monotonic()
        metrics = oracle.evaluate(candidate)
        metrics['wall_seconds'] = time.monotonic()-started
        report['results'][name] = metrics
        print(name,metrics['combined_score'],metrics['robustness_score'],flush=True)
    specs = list(oracle._BASE_DEVELOPMENT_SPECS)+list(oracle.HELDOUT_SPECS)
    report['reference_final_residuals'] = [dict(row,world_spec=spec) for row,spec in zip(residuals,specs)]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
