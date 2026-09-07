"""Scientific regressions exposed by the ten-task construction review."""


import ast


import importlib.util


from pathlib import Path


import numpy as np


import pytest


ROOT = Path(__file__).resolve().parents[1]

_MODULE_CACHE = {}


def load(domain, task, file="verification/evaluator.py"):
    path=ROOT/"benchmarks"/domain/task/file
    tag=f"{domain}/{task}/{file}"
    if tag not in _MODULE_CACHE:
        spec=importlib.util.spec_from_file_location(task+file.replace('/','_'),path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        _MODULE_CACHE[tag]=module
    return _MODULE_CACHE[tag]


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


def test_pump_demand_ripple_is_not_derivable_from_the_public_phase():
    """The hidden ripple seed must differ from the visible phase and never leave the problem."""
    m=load('Engineering','ResilientPumpScheduling')
    assert len(m.INSTANCE_SPECS)>=12
    for spec in m.INSTANCE_SPECS:
        phase,seed=spec[7],spec[14]
        assert seed!=phase and seed not in (0,3,7,11,13,17,19,23),spec[0]
        assert spec[10]>0 and spec[12]>0 and spec[10]+spec[12]<=.045,spec[0]
    problem=m._problem(m.INSTANCE_SPECS[0])
    assert not any('ripple' in key or 'seed' in key for key in problem)
    tariffs={tuple(round(x,4) for x in np.roll(m.TARIFFS[spec[8]%len(m.TARIFFS)],spec[7]%3))
             for spec in m.INSTANCE_SPECS}
    assert len(tariffs)>=3,'tariff windows must vary across the instance set'


# --- 2026-09-07 shortcut probe pins ---------------------------------------------------------
# Each pin re-runs a measured low-dimensional family against the live evaluator and asserts the
# bound recorded in the task's references/known_best.md "2026-09-07 shortcut re-audit" section.
# Changing instances, witness or anchor strength re-trips these pins, which is the point.


def _laminate_lp_guided(problem, evaluator):
    """Lamination-parameter-guided greedy family; mirrors the 2026-09-07 probe verbatim."""
    import math
    angles=evaluator.ANGLES
    n_half=int(problem['ply_count'])//2
    t=float(problem['ply_thickness_m']); h=2*n_half*t
    edges=np.linspace(0.,.5*h,n_half+1)
    w=edges[1:]**3-edges[:-1]**3; w=w/w.sum()
    counts={a:int(problem['required_angle_counts'][str(a)])//2 for a in angles}
    cos2={a:math.cos(math.radians(2*a)) for a in angles}
    cos4={a:math.cos(math.radians(4*a)) for a in angles}
    best,best_q=None,-1.
    for xi1 in np.linspace(-.9,.9,9):
        for xi2 in np.linspace(-.9,.9,9):
            remaining=dict(counts); half=[]
            for k in range(n_half-1,-1,-1):
                cap=1 if k==0 else 2
                positions_left=k+1
                choice,choice_cost=None,None
                for a in angles:  # evaluator order (-45, 0, 45, 90), matching the measured probe
                    if remaining[a]<=0: continue
                    others=sum(v for b,v in remaining.items() if b!=a)
                    if remaining[a]-1>2*math.ceil(positions_left/3)+others: continue
                    run=0
                    for item in reversed(half):
                        if item!=a: break
                        run+=1
                    if run>=cap: continue
                    acc1=sum(w[i]*cos2[half[i]] for i in range(len(half)))
                    acc2=sum(w[i]*cos4[half[i]] for i in range(len(half)))
                    cost=(xi1-acc1-w[k]*cos2[a])**2+(xi2-acc2-w[k]*cos4[a])**2 \
                        +.05*(remaining[a]/max(sum(remaining.values()),1))
                    if choice_cost is None or cost<choice_cost-1e-12:
                        choice,choice_cost=a,cost
                if choice is None:
                    for a in sorted(remaining,key=lambda x:-remaining[x]):
                        run=0
                        for item in reversed(half):
                            if item!=a: break
                            run+=1
                        if remaining[a]>0 and run<max(cap,2):
                            choice=a; break
                    if choice is None:
                        choice=max(remaining,key=lambda a:remaining[a])
                half.append(choice); remaining[choice]-=1
            half=half[::-1]
            seq=half+half[::-1]
            try:
                evaluator._validate(problem,seq)
                repaired=seq
            except ValueError:
                repaired=None
                for i in range(len(half)-2,-1,-1):
                    if half[i]==half[-1]: continue
                    cand=half.copy(); cand[i],cand[-1]=cand[-1],cand[i]
                    try:
                        evaluator._validate(problem,cand+cand[::-1])
                        repaired=cand+cand[::-1]
                        break
                    except ValueError:
                        continue
            if repaired is None: continue
            q=evaluator._laminate(problem,repaired)
            if q>best_q: best,best_q=repaired,q
    return best


@pytest.mark.parametrize('task', ['CompositeLaminateStacking','ResilientPumpScheduling','WakeAwareFarmCoDesign'])
def test_witnesses_stay_in_the_admission_band(task):
    ev=load('Engineering',task)
    ref=load('Engineering',task,'verification/reference.py')
    entry=(ROOT/'benchmarks/Engineering'/task/'frontier_eval/entrypoint.txt').read_text().strip()
    result=ev.evaluate(getattr(ref,entry))
    assert result['valid']==1,task
    assert .5<result['combined_score']<.8,(task,result['combined_score'])


def test_laminate_shortcut_families_stay_pinned():
    ev=load('Engineering','CompositeLaminateStacking')
    lp_cache={}
    def lp(problem):
        key=(problem['ply_count'],tuple(sorted(problem['required_angle_counts'].items())))
        if key not in lp_cache:
            seq=_laminate_lp_guided(problem,ev)
            lp_cache[key]=seq
        return {'ply_angles_deg':list(lp_cache[key])}
    lp_score=ev.evaluate(lp)['combined_score']
    assert .28<lp_score<.48,lp_score            # measured 0.372152
    block_cache={}
    def block(problem):
        key=(problem['ply_count'],tuple(sorted(problem['required_angle_counts'].items())))
        if key not in block_cache:
            best,bq=None,-1.
            for seq in ev._block_patterns(problem):
                q=ev._laminate(problem,seq)
                if q>bq: best,bq=seq,q
            block_cache[key]=best
        return {'ply_angles_deg':list(block_cache[key])}
    block_score=ev.evaluate(block)['combined_score']
    # Admission bar: the structured block family must sit at least 0.15 below the reference
    # (measured 0.557119 against the 0.740840 witness after the run-limit-2 constraint and
    # the shear/twisting third load case; it was 0.992897 above the witness before them).
    ref=load('Engineering','CompositeLaminateStacking','verification/reference.py')
    witness_score=ev.evaluate(ref.design_laminate)['combined_score']
    assert .48<block_score<.64,block_score
    assert witness_score-block_score>=.15,(witness_score,block_score)


def _pump_constant_speeds(ev,problem,on):
    demand=np.asarray(problem['demand_forecast_m3_h'],dtype=float)
    hours=int(on.sum())
    if hours==0: return None
    speed=float(demand.sum()/(hours*float(problem['pump_capacity_m3_h'])))
    if speed<float(problem['minimum_operating_speed']) or speed>1.: return None
    return np.where(on,speed,0.)


def _pump_best_valid(ev,problem,trials):
    demand=np.asarray(problem['demand_forecast_m3_h'],dtype=float)
    best,bc=None,float('inf')
    for speeds in trials:
        if speeds is None: continue
        try:
            speeds=ev._validate(problem,speeds)
        except ValueError:
            continue
        sim=ev._simulate(problem,speeds,demand)
        if sim['feasible'] and sim['cost']<bc: best,bc=speeds,sim['cost']
    return best


def test_pump_shortcut_families_stay_pinned():
    ev=load('Engineering','ResilientPumpScheduling')

    def price_window(problem):
        prices=np.asarray(problem['electricity_usd_kwh'])
        order=np.argsort(prices,kind='stable')
        trials=[]
        for k in range(12,23):
            on=np.zeros(24,dtype=bool); on[order[:k]]=True
            trials.append(_pump_constant_speeds(ev,problem,on))
        return _pump_best_valid(ev,problem,trials)

    def threshold(problem):
        prices=np.asarray(problem['electricity_usd_kwh'])
        trials=[]
        for tau in np.unique(prices)[1:]:
            trials.append(_pump_constant_speeds(ev,problem,prices<tau))
        return _pump_best_valid(ev,problem,trials)

    def as_candidate(factory):
        def cand(problem):
            speeds=factory(problem)
            if speeds is None: raise ValueError('family has no feasible member')
            return {'pump_speed':speeds.tolist()}
        return cand

    for factory,measured in ((price_window,0.0),(threshold,0.0)):
        result=ev.evaluate(as_candidate(factory))
        assert result['combined_score']==measured,(factory,result['combined_score'])
        assert result['feasibility_rate']<1.,'constant-speed families must fail closed somewhere'

    def two_block(problem):
        demand=np.asarray(problem['demand_forecast_m3_h'],dtype=float)
        best,bc=None,float('inf')
        for total in (16,18,20):
            for w1 in (6,8,10,12):
                w2=total-w1
                if w2<4 or w2>14: continue
                for s1 in range(0,22,4):
                    if s1+w1>24: continue
                    for s2 in range(0,22,4):
                        if s2<=s1 or s2+w2>24 or s2<s1+w1: continue
                        on=np.zeros(24,dtype=bool); on[s1:s1+w1]=True; on[s2:s2+w2]=True
                        edges=np.diff(np.r_[False,on,False].astype(int))
                        if np.any(np.flatnonzero(edges==-1)-np.flatnonzero(edges==1)<2): continue
                        speeds=ev._continuous_schedule(problem,on)
                        if speeds is None: continue
                        cost=ev._simulate(problem,speeds,demand)['cost']
                        if cost<bc: best,bc=speeds,cost
        return best

    two_block_score=ev.evaluate(as_candidate(two_block))['combined_score']
    assert .58<two_block_score<.68,two_block_score   # measured 0.629644, below the 0.640556 witness


def test_wake_shortcut_families_stay_pinned():
    ev=load('Engineering','WakeAwareFarmCoDesign')
    directions=ev.DIRECTIONS
    zero=lambda n:{'yaw_by_direction_deg':np.zeros((len(directions),n)).tolist()}

    def row_staggered(problem):
        layout=ev._grid(problem,True)
        return {'layout_xy_m':layout.tolist(),**zero(len(layout))}

    def boundary(problem):
        n=int(problem['turbine_count'])
        W=float(problem['boundary_width_m']); H=float(problem['boundary_height_m'])
        R=float(problem['rotor_diameter_m'])*float(problem['minimum_spacing_rotor_diameters'])
        margin=R/2.+10.
        w,h=W-2*margin,H-2*margin; perimeter=2*(w+h)
        best,bq=None,-1e18
        for variant in range(6):
            pts=[]
            for i in range(n):
                s=((i+variant*.5)*perimeter/n)%perimeter
                if s<w: pts.append([margin+s,margin])
                elif s<w+h: pts.append([W-margin,margin+(s-w)])
                elif s<2*w+h: pts.append([W-margin-(s-w-h),H-margin])
                else: pts.append([margin,H-margin-(s-2*w-h)])
            layout=np.asarray(pts,dtype=float)
            yaw=np.zeros((len(directions),n))
            try:
                ev._validate(problem,{'layout_xy_m':layout,'yaw_by_direction_deg':yaw})
            except ValueError:
                continue
            q=ev._farm_value(problem,layout,yaw)
            if q>bq: best,bq=layout,q
        return {'layout_xy_m':best.tolist(),**zero(n)}

    def fixed_yaw_grid(problem):
        n=int(problem['turbine_count'])
        layout=ev._grid(problem,False)
        best,bq=None,-1e18
        for gamma in (-22.,-14.,-7.,0.,7.,14.,22.):
            yaw=np.full((len(directions),n),gamma)
            try:
                ev._validate(problem,{'layout_xy_m':layout,'yaw_by_direction_deg':yaw})
            except ValueError:
                continue
            q=ev._farm_value(problem,layout,yaw)
            if q>bq: best,bq=yaw,q
        return {'layout_xy_m':layout.tolist(),'yaw_by_direction_deg':best.tolist()}

    for factory,measured,valid in ((row_staggered,0.137746,1),(boundary,0.0,0),(fixed_yaw_grid,0.0,1)):
        result=ev.evaluate(factory)
        assert result['valid']==valid,(factory,result['valid'])
        assert abs(result['combined_score']-measured)<.02,(factory,result['combined_score'],measured)
    # Pure boundary packing must fail closed: the denser farms' perimeters cannot host every
    # turbine at minimum spacing, which is itself a measured negative result.
