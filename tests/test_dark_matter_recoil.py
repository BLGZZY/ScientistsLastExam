"""Scientific and adversarial invariants for ParticlePhysics/DarkMatterRecoilAttribution."""
import copy
import importlib.util
import math
import platform
from pathlib import Path
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.linalg import expm
from sle.metric_visibility import search_visible_metrics
ROOT = Path(__file__).resolve().parents[1]

def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
MODULE = load(ROOT / 'benchmarks/Physics/DarkMatterRecoilAttribution/verification/evaluator.py')

def test_recoil_kernel_matches_independent_speed_integral():
    (mass, ratio, t, energy) = (43.0, 0.83, 1, MODULE.ENERGIES)
    (_, a, z) = MODULE.TARGETS[t]
    nucleus = 0.9315 * a
    reduced = mass * nucleus / (mass + nucleus)
    for j in (0, 8, 17):
        q = math.sqrt(2 * nucleus * energy[j] * 1e-06)
        threshold = 299792.458 * q / (2 * reduced)
        speed = MODULE.SPEEDS[1]
        integral = quad(lambda v: 4 / math.sqrt(math.pi) * v / speed ** 3 * math.exp(-(v / speed) ** 2), threshold, 15 * speed, epsabs=1e-14)[0]
        eta = integral * 260 * math.sqrt(math.pi) / 2
        form = math.exp(-(q * 1.2 * a ** (1 / 3) / 0.1973269804) ** 2 / 3)
        want = MODULE.bin_widths(energy)[j] * ((z + (a - z) * ratio) / 100) ** 2 * form * (q / 0.05) ** 2 * eta
        assert MODULE.recoil_kernel(mass, ratio, 2, t, energy)[j, 1] == pytest.approx(want, rel=1e-08)

def test_recoil_q2_is_rate_factor_and_target_sensitive():
    for (t, (_, a, _)) in enumerate(MODULE.TARGETS):
        base = MODULE.recoil_kernel(50, 1, 0, t, MODULE.ENERGIES)
        dependent = MODULE.recoil_kernel(50, 1, 2, t, MODULE.ENERGIES)
        assert np.allclose(dependent / base, (2 * 0.9315 * a * MODULE.ENERGIES * 1e-06 / 0.05 ** 2)[:, None])
    assert not np.allclose(MODULE.recoil_kernel(40, 1, 0, 0, MODULE.ENERGIES), MODULE.recoil_kernel(40, 1, 0, 2, MODULE.ENERGIES))

def test_counter_seeded_batch_and_query_order_equivalence():
    w = MODULE.make_world(23, 'q2')
    (a, b) = (MODULE.Campaign(w), MODULE.Campaign(w))
    batch = a({'target': 0, 'units': 2})
    first = b({'target': 0, 'units': 1})
    b({'target': 2, 'units': 1})
    second = b({'target': 0, 'units': 1})
    for key in ('counts', 'background_counts', 'calibration_counts'):
        assert np.array_equal(np.array(batch[key]), np.array(first[key]) + second[key])
    assert first != second
BAD = [None, {}, [], 'model', {'abstain': 1}, {'confidence': float('nan')}, {'model': []}, {'model': 'invalid'}, {'abstain': False, 'confidence': True}, {'abstain': True, 'confidence': float('inf')}, {'abstain': True, 'confidence': -1}, {'model': 'contact', 'mass_gev': float('nan')}, {'model': 'recurrent', 'feedback': True, 'report_feedback': 0.5}, {'model': 'report_only', 'feedback': 0.1, 'report_feedback': 0.5}]

@pytest.mark.parametrize('module', [MODULE])
@pytest.mark.parametrize('answer', BAD)
def test_malformed_answers_do_not_crash_or_gain_refusal_credit(module, answer):
    result = module.evaluate(lambda *args: answer)
    assert result['combined_score'] == result['valid'] == 0
    assert result['development_correct_refusal_rate'] == 0
    assert all((not r['valid'] for r in result['per_instance']))

@pytest.mark.parametrize('module', [MODULE])
def test_exceptions_are_sanitized(module):

    def candidate(*args):
        raise RuntimeError('candidate-controlled-token-do-not-echo')
    result = module.evaluate(candidate)
    assert result['valid'] == result['combined_score'] == 0
    assert 'candidate-controlled' not in str(result)

@pytest.mark.parametrize('module', [MODULE])
def test_caught_overbudget_is_sticky(module):

    def candidate(problem, experiment):
        req = {'target': 0, 'units': problem['budget_units'] + 1}
        try:
            experiment(req)
        except ValueError:
            pass
        return {'abstain': True}
    result = module.evaluate(candidate)
    assert result['valid'] == result['combined_score'] == 0

@pytest.mark.parametrize('module', [MODULE])
def test_degenerate_strategies_and_global_rng_independence(module):
    for answer in ({'abstain': True}, {'model': 'none'}):
        first = module.evaluate(lambda *args: answer)
        np.random.seed(777)
        np.random.random(1000)
        second = module.evaluate(lambda *args: answer)
        assert first == second
        assert first['combined_score'] == 0 and first['valid'] == 1
        assert first['development_claim_count'] == 0
        assert first['development_false_discovery_rate'] == 0
        visible = search_visible_metrics(first)
        assert not any((k.startswith('heldout') or 'refusal' in k for k in visible))
        assert 'per_instance' not in visible

def test_correct_law_wrong_parameter_not_reclassified_as_false_discovery():
    w = MODULE.make_world(72, 'contact')
    row = MODULE.score_world(w, {'model': 'contact', 'mass_gev': 250})
    assert row['mechanism'] == 0 and row['false_claim'] is False

def test_oracle_ceiling_recomputable_without_reference_score_literal():
    for (module, kinds) in ((MODULE, ['contact', 'q2', 'none', 'unsupported']),):
        for kind in kinds:
            w = module.make_world(512, kind)
            answer = {'model': kind}
            if kind == 'unsupported':
                answer = {'abstain': True}
            elif True and kind != 'none':
                answer['mass_gev'] = w['mass']
            elif False and kind != 'none':
                answer.update(feedback=w['parameters']['edges'][-2], report_feedback=w['parameters']['edges'][-1])
            assert module.score_world(w, answer)['mechanism'] == 1

@pytest.mark.parametrize('module', [MODULE])
def test_mutating_public_problem_cannot_raise_budget(module):

    def candidate(problem, experiment):
        problem['budget_units'] = 10 ** 9
        try:
            experiment({'target': 0, 'units': 999})
        except ValueError:
            pass
        return {'abstain': True}
    assert module.evaluate(candidate)['valid'] == 0

@pytest.mark.parametrize('module', [MODULE])
def test_world_boundaries_reset_candidate_session_including_split(module):

    class StatefulProxy:
        resets = 0
        calls = 0

        def reset_session(self):
            self.resets += 1

        def __call__(self, problem, experiment):
            assert self.resets == self.calls
            self.calls += 1
            return {'abstain': True}
    candidate = StatefulProxy()
    result = module.evaluate(candidate)
    assert result['valid'] == 1
    assert candidate.calls == 20 and candidate.resets == 19

@pytest.mark.skipif(platform.system() != 'Linux', reason='Bubblewrap requires Linux')
@pytest.mark.parametrize('task,entry', [('ParticlePhysics/DarkMatterRecoilAttribution', 'infer_recoil')])
def test_secure_worlds_cannot_share_globals_or_tmpfs(task, entry, tmp_path):
    from sle.evaluate import evaluate_candidate
    from sle.registry import find_task
    path = tmp_path / 'candidate.py'
    path.write_text(f"from pathlib import Path\nseen = False\ndef {entry}(problem, experiment):\n    global seen\n    marker = Path('/tmp/previous_world')\n    if seen or marker.exists():\n        return []\n    seen = True\n    marker.write_text('visited')\n    return {{'model': 'none'}}\n")
    result = evaluate_candidate(find_task(task, include_uncertified=True), path, timeout_s=60)
    assert result['valid'] == 1 and result['combined_score'] == 0
    assert result['development_valid_rate'] == result['heldout_valid_rate'] == 1
