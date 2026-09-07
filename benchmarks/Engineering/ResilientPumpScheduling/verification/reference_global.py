"""Standalone stronger global-commitment witness. No oracle imports or hidden instance access.

The public model is reproduced here; independent high-fidelity validation is pending.
"""
import math
import copy
import numpy as np

HOURS=24
REFERENCE_MAX_PASSES=2
_REFERENCE_CACHE={}

def _validate(problem, value):
    if isinstance(value, dict): value = value.get("pump_speed")
    speeds = np.asarray(value, dtype=float)
    if speeds.shape != (HOURS,) or not np.all(np.isfinite(speeds)):
        raise ValueError("pump_speed must contain 24 finite values")
    if np.any(speeds < 0.0) or np.any(speeds > 1.0):
        raise ValueError("pump speeds lie outside [0,1]")
    on = speeds > 1e-9
    if np.any(on & (speeds < problem["minimum_operating_speed"] - 1e-9)):
        raise ValueError("running speed below stable operating range")
    edges = np.diff(np.r_[False,on,False].astype(int))
    if np.any(np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1) < problem["minimum_run_hours"]):
        raise ValueError("minimum run duration violated")
    if np.any((np.abs(np.diff(speeds)) > float(problem["maximum_speed_change"]) + 1e-12) & on[1:] & on[:-1]):
        raise ValueError("speed ramp limit exceeded")
    return speeds

def _simulate(problem, speeds, demand, outage=None):
    outage = set(outage or ())
    volume = float(problem["tank_initial_volume_m3"])
    minimum, maximum = float(problem["tank_minimum_volume_m3"]), float(problem["tank_maximum_volume_m3"])
    cap = float(problem["pump_capacity_m3_h"]); eta = float(problem["wire_to_water_efficiency"])
    costs, volumes, pressure_margins = [], [volume], []
    feasible = True
    for h in range(HOURS):
        speed = 0.0 if h in outage else float(speeds[h])
        flow = cap * speed
        volume += flow - float(demand[h])
        volumes.append(volume)
        feasible &= minimum - 1e-9 <= volume <= maximum + 1e-9
        tank_head = 43.0 + 10.0*(volume-minimum)/max(maximum-minimum, 1e-9)
        remote_pressure = tank_head - 20.0 - 0.00023*float(demand[h])**2
        pressure_margins.append(remote_pressure - 20.0)
        feasible &= remote_pressure >= 20.0
        head = float(problem["pump_static_head_m"]) + float(problem["pump_speed_head_coefficient_m"])*speed*speed
        power_kw = 9.81 * flow * head / (3600.0 * eta)
        if speed > 1e-9:
            power_kw += problem["running_auxiliary_power_kw"]
        costs.append(power_kw * float(problem["electricity_usd_kwh"][h]))
    feasible &= volume >= float(problem["terminal_minimum_volume_m3"]) - 1e-9
    switching = 0.035 * sum(abs(float(x)) for x in np.diff(speeds))
    on = np.asarray(speeds) > 1e-9
    switching += problem["startup_cost_usd"] * np.count_nonzero(on & ~np.r_[False,on[:-1]])
    return {"feasible": bool(feasible), "cost": float(sum(costs)+switching),
            "minimum_volume": float(min(volumes)), "maximum_volume": float(max(volumes)),
            "terminal_volume": float(volume), "minimum_pressure_margin_m": float(min(pressure_margins))}

def _baseline(problem):
    demand = np.asarray(problem["demand_forecast_m3_h"], dtype=float)
    average = max(float(np.mean(demand))/float(problem["pump_capacity_m3_h"])*1.14, 0.1)
    return np.full(HOURS, min(0.94, average))

def _continuous_schedule(problem, on, warm=None):
    from scipy.optimize import minimize, LinearConstraint, Bounds
    demand = np.asarray(problem["demand_forecast_m3_h"])
    prices = np.asarray(problem["electricity_usd_kwh"])
    capacity = float(problem["pump_capacity_m3_h"])
    minimum = float(problem["tank_minimum_volume_m3"])
    maximum = float(problem["tank_maximum_volume_m3"])
    initial = float(problem["tank_initial_volume_m3"])
    # Pressure >=20 gives a time-varying minimum storage, affine in speeds.
    high = 1.045 * demand; low = .955 * demand
    pressure_min = minimum + (maximum - minimum) * (.00023 * high**2 - 3.0) / 10.0
    lower = np.maximum(minimum, pressure_min) - initial + np.cumsum(high)
    lower[-1] = max(lower[-1], problem["terminal_minimum_volume_m3"] - initial + high.sum())
    upper = maximum - initial + np.cumsum(low)
    cumulative = capacity * np.tril(np.ones((HOURS, HOURS)))
    difference = np.diff(np.eye(HOURS), axis=0)
    ramp = float(problem["maximum_speed_change"])
    # Auxiliary epigraph variables make the switching term differentiable and convex.
    matrices = [np.c_[cumulative, np.zeros((HOURS,HOURS-1))],
                np.c_[difference, np.zeros((HOURS-1,HOURS-1))],
                np.c_[difference, -np.eye(HOURS-1)],
                np.c_[-difference, -np.eye(HOURS-1)]]
    lb = np.r_[lower + 1e-4, np.where(on[1:] & on[:-1], -ramp+1e-6, -1.), np.full(2*(HOURS-1),-np.inf)]
    ub = np.r_[upper - 1e-4, np.where(on[1:] & on[:-1], ramp-1e-6, 1.), np.zeros(2*(HOURS-1))]
    factor = 9.81 * capacity * prices / (3600 * problem["wire_to_water_efficiency"])
    h0 = problem["pump_static_head_m"]; h2 = problem["pump_speed_head_coefficient_m"]
    def objective(z):
        x=z[:HOURS]
        return float(np.sum(factor*(h0*x+h2*x**3)) + .035*np.sum(z[HOURS:])) / 100.0
    def jac(z):
        return np.r_[factor*(h0+3*h2*z[:HOURS]**2), np.full(HOURS-1,.035)] / 100.0
    start = _baseline(problem)
    if warm is not None:
        start = np.clip(np.asarray(warm, dtype=float).copy(),
                        on * float(problem["minimum_operating_speed"]), on.astype(float))
    result = minimize(objective, np.r_[start,np.abs(np.diff(start))], jac=jac,
                      method="SLSQP", bounds=Bounds(np.r_[on * problem["minimum_operating_speed"],np.zeros(HOURS-1)],
                                    np.r_[on.astype(float),np.ones(HOURS-1)]),
                      constraints=[LinearConstraint(np.vstack(matrices),lb,ub)],
                      options={"maxiter":150,"ftol":1e-10})
    speeds = result.x[:HOURS]
    if (not result.success or not _simulate(problem,speeds,high)["feasible"]
            or not _simulate(problem,speeds,low)["feasible"]):
        return None
    return speeds

def _global_schedule(p):
 """Public-model mixed-integer commitment search plus exact feasible dispatch.

 The MILP uses tangent underestimators of convex hydraulic electricity cost. Its
 objective bound is diagnostic only; normalization uses the returned feasible
 schedule, recomputed by _simulate. Single-threaded fixed-node search is deterministic.
 """
 import warnings
 from scipy.optimize import milp, Bounds, LinearConstraint
 n=24;size=4*n+n-1
 # x=flow fraction, z=commitment, u=start, y=convex hydraulic-cost epigraph, t=variation.
 x=np.arange(n);z=x+n;u=x+2*n;y=x+3*n;t=np.arange(n-1)+4*n
 obj=np.zeros(size);obj[y]=1;obj[z]=p['running_auxiliary_power_kw']*np.array(p['electricity_usd_kwh']);obj[u]=p['startup_cost_usd'];obj[t]=.035
 lo=np.zeros(size);hi=np.full(size,np.inf);hi[x]=1;hi[z]=1;hi[u]=1;hi[t]=1;hi[u[-1]]=0
 integ=np.zeros(size);integ[z]=1;integ[u]=1
 A=[];lbs=[];ubs=[]
 def add(items,lower=-np.inf,upper=np.inf):
  row=np.zeros(size)
  for indexes,value in items:row[indexes]+=value
  A.append(row);lbs.append(lower);ubs.append(upper)
 cap=p['pump_capacity_m3_h'];d=np.array(p['demand_forecast_m3_h']);high=1.045*d;low=.955*d;vmin=p['tank_minimum_volume_m3'];vmax=p['tank_maximum_volume_m3'];initial=p['tank_initial_volume_m3']
 floor=np.maximum(vmin,vmin+(vmax-vmin)*(.00023*high**2-3)/10)
 lower=floor-initial+np.cumsum(high);lower[-1]=max(lower[-1],p['terminal_minimum_volume_m3']-initial+high.sum());upper=vmax-initial+np.cumsum(low)
 factor=9.81*cap*np.array(p['electricity_usd_kwh'])/(3600*p['wire_to_water_efficiency']);h0=p['pump_static_head_m'];h2=p['pump_speed_head_coefficient_m'];ramp=p['maximum_speed_change']
 for h in range(n):
  add([(x[h],1),(z[h],-1)],upper=0);add([(x[h],1),(z[h],-p['minimum_operating_speed'])],lower=0)
  add([(x[:h+1],cap)],lower=lower[h]+1e-4,upper=upper[h]-1e-4)
  start=[(u[h],1),(z[h],-1)]
  if h:start.append((z[h-1],1))
  add(start,lower=0)
  if h<n-1:add([(z[h:h+2],1),(u[h],-2)],lower=0)
  for point in np.r_[0.,np.linspace(p['minimum_operating_speed'],1.,32)]:
   f=factor[h]*(h0*point+h2*point**3);grad=factor[h]*(h0+3*h2*point**2)
   add([(y[h],1),(x[h],-grad)],lower=f-grad*point)
  if h:
   add([(t[h-1],1),(x[h],-1),(x[h-1],1)],lower=0);add([(t[h-1],1),(x[h],1),(x[h-1],-1)],lower=0)
   add([(x[h],1),(x[h-1],-1),(z[h],1),(z[h-1],1)],upper=ramp+2)
   add([(x[h],-1),(x[h-1],1),(z[h],1),(z[h-1],1)],upper=ramp+2)
 with warnings.catch_warnings():
  warnings.filterwarnings('ignore',message='Unrecognized options detected')
  res=milp(obj,integrality=integ,bounds=Bounds(lo,hi),constraints=LinearConstraint(np.array(A),lbs,ubs),options={'node_limit':2000,'mip_rel_gap':1e-7,'threads':1,'random_seed':0})
 if res.x is None:
  raise RuntimeError('global commitment search returned no feasible incumbent')
 on=res.x[z]>.5
 clean=_continuous_schedule(p,on,warm=res.x[x])
 if clean is None:
  raise RuntimeError('global commitment failed exact feasible dispatch refinement')
 _validate(p,clean)
 return clean

def schedule_pumps(problem):
    """Independent runnable global-commitment witness; public inputs only."""
    return {"pump_speed": _global_schedule(problem).tolist()}
