"""Audit and freeze a naturally settled diagnostic as a candidate reset asset.

This is an offline tool. It does not connect to a running simulator or write a
cloth state during a policy episode. Passing is necessary, not a demonstration
of contact calibration, grasping or task success; images still need review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from fixture_clearance import fixture_intersections


def digest(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--probe',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--max-speed',type=float,default=.01,
                   help='Maximum nodal speed over the last half second, metres/second')
    args=p.parse_args()
    if not 0 < args.max_speed <= .02:
        p.error('settling threshold must be in (0, .02] m/s')
    report=json.loads((args.probe/'probe.json').read_text())
    if report.get('status')!='complete':
        raise ValueError('Only a complete native probe can supply a reset')
    data=np.load(args.probe/'nodes.npz',allow_pickle=False)
    points=np.asarray(data['positions'],dtype=float)
    if points.ndim!=3 or points.shape[-1]!=3 or len(points)<11 or not np.isfinite(points).all():
        raise ValueError('At least half a second of finite settled-state evidence is required')
    times=data['times_s'] if 'times_s' in data else np.arange(len(points))/20
    if len(times)!=len(points) or np.any(np.diff(times)<=0):
        raise ValueError('Native states require matching increasing sample times')
    late=times[:-1]>=times[-1]-.5-1e-9
    if not late.any():raise ValueError('Missing settling intervals')
    speed=np.linalg.norm(np.diff(points,axis=0)/np.diff(times)[:,None,None],axis=-1)
    max_speed=float(speed[late].max())
    if max_speed > args.max_speed:
        raise ValueError(f'Cloth is still moving: late maximum {max_speed:.5f} m/s')
    if Path(__file__).parent.name=='peg-out-a-tshirt':
        from scene import support_geometry,TABLE
        if report['mode']!='task-layout':
            raise ValueError('Shirt reset requires the actual task-layout probe')
        fixtures=support_geometry(report.get('support_board_thickness_m',.008))
        if report.get('peg_rests_candidate'):
            from peg_rests import geometry
            fixtures.update(geometry())
    else:
        from layout import fixture_geometry,TABLE
        if report['mode']!='collar-drape':
            raise ValueError('Tie reset requires the actual collar-drape probe')
        fixtures=fixture_geometry()
    fixtures['Table']=dict(kind='box',size=(1.1,1.3,.06),center=(.36,0.,TABLE-.03))
    # A 50 um contracted solid avoids declaring mere surface touch a penetration.
    hits=fixture_intersections(points[-1],data['faces'],fixtures,margin=-.00005)
    count={k:len(v) for k,v in hits.items()}
    if any(count.values()):
        raise ValueError('Settled cloth penetrates a static solid: '+repr(count))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    if args.out.exists() or args.out.with_suffix('.json').exists():
        raise FileExistsError('Choose a new reset candidate path')
    np.savez_compressed(args.out,points=points[-1],rest=data['rest'],faces=data['faces'])
    manifest=dict(kind='candidate_naturally_settled_reset',score=None,
                  native_probe_source_sha256=report['provenance'],probe_mode=report['mode'],
                  probe_seconds=report['seconds'],physics_hz=report['physics_hz'],
                  final_points_sha256=digest(points[-1]),rest_sha256=digest(data['rest']),
                  faces_sha256=digest(data['faces']),
                  probe_nodes_sha256=hashlib.sha256((args.probe/'nodes.npz').read_bytes()).hexdigest(),
                  late_max_nodal_speed_m_s=max_speed,settling_threshold_m_s=args.max_speed,
                  fixture_intersections=count,solid_contraction_m=.00005,
                  image_review='pending',dynamic_contact_fidelity='not_certified')
    args.out.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':
    main()
