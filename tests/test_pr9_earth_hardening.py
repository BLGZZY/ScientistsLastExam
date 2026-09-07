"""Scientific regressions exposed by the earth-task construction review.

The 2026-09-07 internal difficulty audit withdrew ChronologyAssimilation and
IceObservationNetworkDesign; their regressions were removed with them (see the
git history). The regressions below pin the surviving packages, including the
2026-09-07 FWI shortcut re-audit whose measured numbers are recorded in
benchmarks/EarthScience/ActiveFullWaveformInversion/references/known_best.md.
"""


import ast


import importlib.util


from pathlib import Path


import numpy as np


import pytest


ROOT = Path(__file__).resolve().parents[1]

def load(domain, task, file="verification/evaluator.py"):
    path=ROOT/"benchmarks"/domain/task/file
    spec=importlib.util.spec_from_file_location(task+file.replace('/','_'),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def test_groundwater_mass_conservation_and_time_refinement():
    m=load('EarthScience','GroundwaterRemediationDesign')
    p=m._public_problem(m.DEVELOPMENT_SPECS[0]);x,y=p['source_location_m']
    wells=np.array([[x+1400,y,2.13,800.]])
    coarse=m._plan_metrics(p,wells)
    fine=m._plan_metrics(dict(p,transport_step_days=15.),wells)
    assert coarse['mass_balance_error_kg']<1e-8
    assert fine['mass_balance_error_kg']<1e-8
    assert coarse['captured_mass_kg']>0
    assert abs(coarse['remaining_mass_kg']-fine['remaining_mass_kg'])<.001*p['initial_contaminant_mass_kg']
    no_pumping=m._plan_metrics(p,np.array([[x,y,0.,0.]]))
    assert no_pumping['captured_mass_kg']==0
    assert no_pumping['remaining_mass_kg']>coarse['remaining_mass_kg']


def test_source_well_shortcut_no_longer_beats_groundwater_reference():
    m=load('EarthScience','GroundwaterRemediationDesign')
    def source(p):
        x,y=p['source_location_m']
        return {'plans':[[[x,y,0.,rate]] for rate in np.linspace(80.,950.,16)]}
    result=m.evaluate(source)
    assert result['valid']==1
    assert result['combined_score']<.5
    assert result['heldout_score']<.5


@pytest.mark.parametrize('domain,task', [('EarthScience', 'ActiveFullWaveformInversion'), ('EarthScience', 'GroundwaterRemediationDesign')])
def test_twelve_malformed_candidates_fail_closed(domain,task):
    m=load(domain,task)
    invalid=[None,{},'',True,12,float('nan'),float('inf'),[],[0],{'plans':[]},
             {'abstain':'yes'},{'confidence':float('nan')}]
    for value in invalid:
        result=m.evaluate(lambda *args,**kwargs:value)
        assert result['valid']==0,(task,value)
        assert result['combined_score']==0,(task,value)


def test_caught_malformed_instrument_call_still_invalidates_world():
    fwi=load('EarthScience','ActiveFullWaveformInversion')
    def bad_shot(*args):
        try:args[-2](3.5)
        except ValueError:pass
        return {'velocity_m_s':[],'confidence':0.,'abstain':True}
    assert fwi.evaluate(bad_shot)['valid']==0
