"""Regression contracts for FocalMechanismStressInversion."""
import ast
import importlib.util
from pathlib import Path
import numpy as np
import pytest
ROOT = Path(__file__).resolve().parents[1]

def load(domain, task, file='verification/evaluator.py'):
    path = ROOT / 'benchmarks' / domain / task / file
    spec = importlib.util.spec_from_file_location(task + file.replace('/', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('domain,task', [('EarthScience', 'FocalMechanismStressInversion')])
def test_twelve_malformed_candidates_fail_closed(domain, task):
    m = load(domain, task)
    invalid = [None, {}, '', True, 12, float('nan'), float('inf'), [], [0], {'plans': []}, {'abstain': 'yes'}, {'confidence': float('nan')}]
    for value in invalid:
        result = m.evaluate(lambda *args, **kwargs: value)
        assert result['valid'] == 0, (task, value)
        assert result['combined_score'] == 0, (task, value)
