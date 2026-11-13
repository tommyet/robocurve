"""Read native cloth evidence offline; report measurements without a task score."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from fixture_clearance import fixture_intersections
from cloth_mesh import edge_strain


def interpret(folder):
    report=json.loads((folder/'probe.json').read_text())
    if report.get('status')!='complete':
        raise ValueError('Native probe did not complete')
    with np.load(folder/'nodes.npz',allow_pickle=False) as data:
        frames=data['positions'];rest=data['rest'];faces=data['faces']
        times=data['times_s'] if 'times_s' in data else np.arange(len(frames))/20
    if len(frames)!=len(times) or len(times)<2 or np.any(np.diff(times)<=0):
        raise ValueError('Need matching strictly increasing native sample times')
    speed=np.linalg.norm(np.diff(frames,axis=0)/np.diff(times)[:,None,None],axis=-1)
    late=(times[1:]>=times[-1]-.5-1e-9)
    strain=edge_strain(rest,frames[-1],faces)
    result=dict(kind='offline_native_probe_measurements_not_task_score',score=None,
        mode=report['mode'],sample_times_s=times.tolist(),
        late_max_nodal_speed_m_s=float(speed[late].max()),
        late_median_nodal_speed_m_s=float(np.median(speed[late])),
        final_abs_edge_strain_percentiles={str(q):float(np.percentile(np.abs(strain),q)) for q in (50,95,99,100)},
        final_bounds_m=dict(min=frames[-1].min(0).tolist(),max=frames[-1].max(0).tolist()),
        source_nodes_sha256=hashlib.sha256((folder/'nodes.npz').read_bytes()).hexdigest(),
        native_source_sha256=report['provenance'],
        interpretation='Requires native image review, controls and material judgment; no automatic success conclusion')
    mode=report['mode'];fixtures={};points=frames[-1]
    if mode=='drape':
        # The generic cylinder audit is Z-aligned. Permute the complete frame
        # and rail consistently; this is an offline coordinate change only.
        points=points[:,[1,2,0]]
        fixtures['Rail']=dict(kind='cylinder',center=(0.,.32,.05),radius=.005,height=.55)
    elif mode=='task-layout':
        from scene import support_geometry,TABLE
        fixtures=support_geometry()
        fixtures['Table']=dict(kind='box',size=(1.1,1.3,.06),center=(.36,0.,TABLE-.03))
    elif mode=='collar-drape':
        from layout import fixture_geometry,TABLE
        fixtures=fixture_geometry()
        fixtures['Table']=dict(kind='box',size=(1.1,1.3,.06),center=(.36,0.,TABLE-.03))
    elif mode in ('clamp','open-clamp'):
        root=rest[:,0]<=.030001
        result['coupon_root_patch']=dict(material_nodes=int(root.sum()),
            initial_s_interval_m=[0.,.03],final_centroid_m=frames[-1,root].mean(0).tolist(),
            final_z_bounds_m=[float(frames[-1,root,2].min()),float(frames[-1,root,2].max())],
            fraction_above_48cm=float(np.mean(frames[-1,root,2]>.48)))
    if fixtures:
        hits=fixture_intersections(points,faces,fixtures,margin=-.00005)
        result['final_fixture_intersection_counts']={name:len(v) for name,v in hits.items()}
        result['solid_contraction_m']=.00005
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('probe',type=Path)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    result=interpret(args.probe)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
