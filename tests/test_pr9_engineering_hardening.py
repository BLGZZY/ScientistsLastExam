"""Scientific regressions for the two retained engineering candidate tasks."""


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
    'CompositeLaminateStacking',
    'WakeAwareFarmCoDesign'])
def test_engineering_references_do_not_import_oracle(task):
    for path in (ROOT/'benchmarks/Engineering'/task/'verification').glob('reference*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Import):
                assert all(a.name.split('.')[0] in {'numpy','scipy','math','copy','warnings'} for a in node.names)
            if isinstance(node,ast.ImportFrom):
                assert node.module.split('.')[0] in {'numpy','scipy','math','copy','warnings'}


@pytest.mark.parametrize('domain,task', [('Engineering', 'CompositeLaminateStacking'), ('Engineering', 'WakeAwareFarmCoDesign')])
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


@pytest.mark.parametrize('task', ['CompositeLaminateStacking','WakeAwareFarmCoDesign'])
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
