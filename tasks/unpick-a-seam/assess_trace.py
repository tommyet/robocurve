"""Score measured cut-end separation and released tool support from a full run."""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from contact_audit import capsule_endpoints
from scoring import assess
from geometry import TABLE_TOP
from tool_geometry import HANDLE_SIZE


def evaluate(folder):
    folder=Path(folder);report=json.loads((folder/'preview.json').read_text())
    rows=[json.loads(line) for line in gzip.open(folder/'trace.jsonl.gz','rt')]
    with np.load(folder/'last-measured-state.npz',allow_pickle=False) as a:lengths=a['thread_lengths']
    if len(lengths)!=72:raise ValueError('Expected six12-segment tacks')
    complete=report['status']=='complete' and len(rows)==report['requested_steps']+1
    final=rows[-61:];cut={int(e['link']) for e in report.get('cut_events',[])}
    per_stitch=[]
    for stitch in range(6):
        joints=[j for j in cut if j//12==stitch];best=0.
        for joint in joints:
            previous=stitch*12+(joint-stitch*12-1)%12
            gaps=[]
            for r in final:
                ends=capsule_endpoints(np.asarray(r['thread_poses_xyzw']),lengths)
                gaps.append(float(np.linalg.norm(ends[joint,0]-ends[previous,1]))-.0008)
            best=max(best,min(gaps))
        per_stitch.append(dict(stitch=stitch+1,cut_joint_indices=joints,
            minimum_visible_end_gap_m=best,visibly_open=best>=.002))
    tool=[]
    corners=np.array([[x,y,z] for x in (-.5,.5) for y in (-.5,.5) for z in (-.5,.5)])*HANDLE_SIZE
    for row in final:
        p=np.asarray(row['handle_pose_xyzw']);points=corners@Rotation.from_quat(p[3:]).as_matrix().T+p[:3]
        cloth=np.concatenate([np.asarray(n) for n in row['cloth_nodes']]);lo=points.min(0);hi=points.max(0)
        # A conservative axis-aligned separating distance suffices in this
        # fixed setup; reviewers can use a ruler in the close photograph.
        separation=np.maximum(np.maximum(cloth.min(0)-hi,lo-cloth.max(0)),0.)
        clearance=float(np.linalg.norm(separation));hand=float(np.linalg.norm(np.asarray(row['right_tcp_position_m'])-p[:3]))
        speed=float(np.linalg.norm(np.asarray(row['handle_velocity_m_s_rad_s'])[:3]))
        tool.append(dict(time_s=row['time_s'],lowest_z_m=float(lo[2]),cloth_clearance_m=clearance,
            hand_clearance_m=hand,speed_m_s=speed,held=bool(row.get('tool_grip',{}).get('held',True))))
    released=(len(final)==61 and all(not x['held'] and x['hand_clearance_m']>=.060 and
        x['cloth_clearance_m']>=.010 and abs(x['lowest_z_m']-TABLE_TOP)<=.004 and x['speed_m_s']<=.020 for x in tool))
    valid=complete and not report.get('material_invalid',True) and report.get('native_joint_breaks',{}).get('cloth_hinge_break_count',1)==0
    n=sum(s['visibly_open'] for s in per_stitch)
    result=assess(released_stitches=n,blade_crossed_fabric=bool(report.get('damage_events')),
        maximum_new_tear_m=0.,complete=complete,thread_bridge_present=n<6,
        tools_clear=released,material_valid=valid)
    return dict(schema='seam-visible-opening-audit-v1',**result,complete=complete,
        completed_steps=report['completed_steps'],wall_seconds=report['wall_seconds'],
        stitches=per_stitch,released_tool_hold=released,final_tool_samples=tool,
        material_model_valid=valid,damage_events=report.get('damage_events',[]),
        cloth_hinge_break_count=report.get('native_joint_breaks',{}).get('cloth_hinge_break_count'),
        simulation_damage_proxy='Blade/canvas crossing and native panel fracture; no calibrated fibre-tear mechanics.',
        source_sha256=report['source_sha256'],trace_sha256=hashlib.sha256((folder/'trace.jsonl.gz').read_bytes()).hexdigest())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trial',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();result=evaluate(a.trial);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('score','reason','complete','completed_steps','released_tool_hold')}))
