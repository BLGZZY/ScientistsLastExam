"""Regression contracts for FocalMechanismStressInversion."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
ROOT = Path(__file__).resolve().parents[1]

def load(task, relative='verification/evaluator.py'):
    path = ROOT / 'benchmarks' / 'EarthScience' / task / relative
    spec = importlib.util.spec_from_file_location(task + relative.replace('/', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('task,task_id', [('FocalMechanismStressInversion', 'Geophysics/FocalMechanismStressInversion')])
def test_external_entrypoints_delegate_without_importing_candidate(task, task_id, tmp_path, monkeypatch):
    runner = load(task, 'frontier_eval/run_eval.py')
    candidate = tmp_path / 'candidate.py'
    marker = tmp_path / 'unsandboxed-import'
    candidate.write_text('from pathlib import Path\nPath(%r).touch()\n' % str(marker))
    output = tmp_path / 'metrics.json'
    calls = []

    def trusted_eval(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps({'combined_score': 0.4, 'valid': 1.0}), stderr='')
    monkeypatch.setattr(runner.subprocess, 'run', trusted_eval)
    monkeypatch.setattr(runner.sys, 'argv', ['run_eval.py', '--candidate', str(candidate), '--metrics-out', str(output)])
    assert runner.main() == 0
    assert not marker.exists()
    (command, kwargs) = calls[0]
    assert command[1:4] == ['-m', 'sle', 'eval']
    assert command[command.index('--task') + 1] == task_id
    assert command[command.index('--candidate') + 1] == str(candidate.resolve())
    assert '--allow-uncertified' in command
    assert Path(kwargs['cwd']) == ROOT
    assert json.loads(output.read_text())['combined_score'] == 0.4

@pytest.mark.parametrize('task', ['FocalMechanismStressInversion'])
def test_invalid_artifacts_do_not_count_as_discoveries(task):
    result = load(task).evaluate(lambda *args: {})
    assert result['valid'] == 0.0
    assert result['discovery_attempt_count'] == 0
    assert result['development_discovery_coverage'] == 0.0
    assert result['heldout_discovery_coverage'] == 0.0

def test_stress_axes_must_describe_a_physical_orthogonal_frame():
    oracle = load('FocalMechanismStressInversion')
    world = oracle._world(oracle._BASE_DEVELOPMENT_SPECS[0])
    answer = {'sigma1': [0.0, 0.0], 'sigma3': [90.0, 0.0], 'R': 0.5, 'plane_assignments': [0] * len(world['catalog']), 'abstain': False, 'confidence': 0.5}
    oracle._validate(answer, world)
    for axis in ([0.0, 0.0], [45.0, 0.0], [90.0, 45.0]):
        if axis == [90.0, 45.0]:
            oracle._validate(dict(answer, sigma3=axis), world)
        else:
            with pytest.raises(ValueError, match='orthogonal'):
                oracle._validate(dict(answer, sigma3=axis), world)

@pytest.mark.parametrize('event_id', [True, False, 0.0, '0', None, [], {}, -1, 999])
def test_bad_stress_event_ids_poison_even_caught_calls(event_id):
    oracle = load('FocalMechanismStressInversion')
    world = oracle._world(oracle._BASE_DEVELOPMENT_SPECS[0])
    observatory = oracle._Observatory(world)
    with pytest.raises((ValueError, TypeError)):
        observatory.reanalyze(event_id)
    assert observatory.violated
    assert observatory.used == 0

def test_stress_refusal_contract_and_calibration_are_reported_separately():
    oracle = load('FocalMechanismStressInversion')
    refusal = {'sigma1': None, 'sigma3': None, 'R': None, 'plane_assignments': None, 'abstain': True, 'confidence': 0.2}
    result = oracle.evaluate(lambda *args: dict(refusal))
    assert result['valid'] == 1.0
    assert result['combined_score'] == 0.0
    assert result['discovery_attempt_count'] == 0
    assert result['development_correct_refusal_rate'] == 1.0
    assert 0.0 < result['development_confidence_calibration_score'] < 1.0
    assert 0.0 < result['heldout_confidence_calibration_score'] < 1.0
    world = oracle._world(oracle._BASE_DEVELOPMENT_SPECS[0])
    for (field, value) in (('R', 0.5), ('sigma1', [0.0, 0.0]), ('sigma3', 0), ('plane_assignments', [0])):
        with pytest.raises(ValueError):
            oracle._validate(dict(refusal, **{field: value}), world)
    oracle._validate(dict(refusal, sigma1=np.array([]), sigma3=np.array([]), plane_assignments=np.array([])), world)

@pytest.mark.parametrize('task', ['FocalMechanismStressInversion'])
def test_confidence_tracks_recovered_mechanism_not_only_world_support(task, monkeypatch):
    oracle = load(task)
    monkeypatch.setattr(oracle, '_mechanism_score', lambda *args: (0.0, 0.0, 0.0, 0.0))
    spec = oracle._BASE_DEVELOPMENT_SPECS[0]
    candidate = lambda problem, *args: {'sigma1': [0.0, 0.0], 'sigma3': [90.0, 0.0], 'R': 0.5, 'plane_assignments': [0] * problem['event_count'], 'confidence': 1.0, 'abstain': False}
    row = oracle._evaluate_world(candidate, spec, 'development', 0)
    assert row['valid']
    assert row['confidence_score'] == 0.0
