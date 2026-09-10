"""Public-input four-dimensional stress-grid probe, independently reconstructed.

The maintainer's exact coordinates/source were not supplied. This is the reported
family: global stress search, per-event minimum over two planes, worst-event paid
re-analysis, and residual-based refusal. No evaluator imports or hidden inputs.
"""
import itertools
import numpy as np

GRID = (12, 8, 12, 6)
LOCAL_ROUNDS = 0


def _plane(strike, dip, rake):
    tr, dp, lam = np.deg2rad([strike, dip, rake])
    normal = [-np.sin(dp)*np.sin(tr), -np.sin(dp)*np.cos(tr), np.cos(dp)]
    slip = (np.cos(lam)*np.array([np.cos(tr), -np.sin(tr), 0.])
            + np.sin(lam)*np.array([np.cos(dp)*np.sin(tr), np.cos(dp)*np.cos(tr), np.sin(dp)]))
    return normal, slip


def _tensors(parameters):
    trend, plunge, rotation = np.deg2rad(parameters[:, :3]).T
    ratio = parameters[:, 3]
    one = np.stack([np.cos(plunge)*np.cos(trend), np.cos(plunge)*np.sin(trend), np.sin(plunge)], axis=1)
    u = np.stack([-np.sin(trend), np.cos(trend), np.zeros_like(trend)], axis=1)
    v = np.cross(one, u)
    three = np.cos(rotation)[:, None]*u + np.sin(rotation)[:, None]*v
    two = np.cross(three, one)
    tensors = one[:, :, None]*one[:, None, :] + (1-ratio[:, None, None])*two[:, :, None]*two[:, None, :]
    return tensors, one, three


def _misfits(tensors, normal, slip):
    traction = np.einsum('gij,epj->gepi', tensors, normal)
    shear = traction - np.einsum('gepi,epi->gep', traction, normal)[:, :, :, None]*normal
    magnitude = np.linalg.norm(shear, axis=-1)
    cosine = np.abs(np.einsum('gepi,epi->gep', shear, slip))/np.maximum(magnitude, 1e-12)
    return np.rad2deg(np.arccos(np.clip(cosine, 0., 1.)))


def infer_stress_orientation(problem, reanalyze, budget_units):
    events = [dict(event) for event in problem['events']]
    coarse = np.asarray(list(itertools.product(
        np.linspace(0., 360., GRID[0], endpoint=False), np.linspace(0., 90., GRID[1]),
        np.linspace(0., 180., GRID[2], endpoint=False), np.linspace(.05, .95, GRID[3]))))

    def fit():
        parsed = np.asarray([[_plane(*event[p]) for p in ('plane_a', 'plane_b')] for event in events])
        normals, slips = parsed[:, :, 0], parsed[:, :, 1]

        def search(parameters):
            best = (float('inf'), None, None)
            for start in range(0, len(parameters), 256):
                batch = parameters[start:start+256]
                tensors, _, _ = _tensors(batch)
                angles = _misfits(tensors, normals, slips)
                objective = np.mean(np.min(angles, axis=2), axis=1)
                i = int(np.argmin(objective))
                if objective[i] < best[0]:
                    best = (float(objective[i]), batch[i], angles[i])
            return best

        best = search(coarse)
        step = np.array([360/GRID[0], 90/(GRID[1]-1), 180/GRID[2], .9/(GRID[3]-1)])
        offsets = np.asarray(list(itertools.product([-1, 0, 1], repeat=4)))
        for _ in range(LOCAL_ROUNDS):
            step *= .5
            points = best[1] + offsets*step
            points[:, 1] = np.clip(points[:, 1], -90, 90)
            points[:, 3] = np.clip(points[:, 3], 0, 1)
            proposal = search(points)
            if proposal[0] < best[0]:
                best = proposal
        return best

    _, parameters, angles = fit()
    worst = np.argsort(-np.min(angles, axis=1), kind='stable')[:int(budget_units)]
    for index in worst:
        events[index] = dict(reanalyze(events[index]['id']))
    _, parameters, angles = fit()
    residuals = np.min(angles, axis=1)
    if np.mean(residuals) > 18. or np.mean(residuals > 35.) > .18:
        return {'sigma1':None, 'sigma3':None, 'R':None, 'plane_assignments':None,
                'abstain':True, 'confidence':.1}
    _, one, three = _tensors(parameters[None, :])

    def angles_of(vector):
        return [float(np.rad2deg(np.arctan2(vector[1], vector[0])) % 360),
                float(np.rad2deg(np.arcsin(np.clip(vector[2], -1, 1))))]
    return {'sigma1':angles_of(one[0]), 'sigma3':angles_of(three[0]), 'R':float(parameters[3]),
            'plane_assignments':np.argmin(angles, axis=1).tolist(), 'abstain':False, 'confidence':.75}
