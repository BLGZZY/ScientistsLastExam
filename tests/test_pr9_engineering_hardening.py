"""Scientific regressions exposed by the ten-task construction review."""


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


@pytest.mark.parametrize('task',[
    'CompositeLaminateStacking','ResilientPumpScheduling',
    'WakeAwareFarmCoDesign'])
def test_engineering_references_do_not_import_oracle(task):
    source=(ROOT/'benchmarks/Engineering'/task/'verification/reference.py').read_text()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node,ast.Import):
            assert all(a.name.split('.')[0] in {'numpy','scipy','math','copy'} for a in node.names)
        if isinstance(node,ast.ImportFrom):
            assert node.module.split('.')[0] in {'numpy','scipy','math','copy'}


@pytest.mark.parametrize('domain,task', [('Engineering', 'CompositeLaminateStacking'), ('Engineering', 'ResilientPumpScheduling'), ('Engineering', 'WakeAwareFarmCoDesign')])
def test_twelve_malformed_candidates_fail_closed(domain,task):
    m=load(domain,task)
    invalid=[None,{},'',True,12,float('nan'),float('inf'),[],[0],{'plans':[]},
             {'abstain':'yes'},{'confidence':float('nan')}]
    for value in invalid:
        result=m.evaluate(lambda *args,**kwargs:value)
        assert result['valid']==0,(task,value)
        assert result['combined_score']==0,(task,value)


def test_laminate_bending_activates_order_dependent_ply_strength():
    m=load('Engineering','CompositeLaminateStacking')
    p=m._problem(m.INSTANCE_SPECS[2])
    first=m._baseline(p)
    second=m._reference(p)
    a=m._laminate(p,first,return_components=True)
    b=m._laminate(p,second,return_components=True)
    assert abs(a['first_ply_reserve']-b['first_ply_reserve'])>.01
    without=dict(p,moment_cases_n=[[0.,0.,0.]]*len(p['moment_cases_n']))
    no_a=m._laminate(without,first,return_components=True)
    no_b=m._laminate(without,second,return_components=True)
    assert no_a['first_ply_reserve']==pytest.approx(no_b['first_ply_reserve'])
    assert no_a['first_ply_reserve']>10*a['first_ply_reserve']


def test_pump_commitment_contract_and_auxiliary_cost():
    m=load('Engineering','ResilientPumpScheduling')
    p=m._problem(m.INSTANCE_SPECS[0])
    with pytest.raises(ValueError,match='stable operating'):
        m._validate(p,np.full(24,.4))
    speed=np.zeros(24);speed[5]=.8
    with pytest.raises(ValueError,match='run duration'):
        m._validate(p,speed)
    speed[6]=.8
    m._validate(p,speed)  # Startup/shutdown is allowed within an hourly interval.
    actual=np.asarray(p['demand_forecast_m3_h'])
    with_cost=m._simulate(p,speed,actual)['cost']
    no_aux=m._simulate(dict(p,running_auxiliary_power_kw=0.,startup_cost_usd=0.),speed,actual)['cost']
    assert with_cost-no_aux==pytest.approx(.3+2.5*sum(p['electricity_usd_kwh'][5:7]))
