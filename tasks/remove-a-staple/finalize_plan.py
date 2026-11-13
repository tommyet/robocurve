"""Append ordinary remover placement/release to a proposed extraction plan.

The staple may stay in the released tool, at least10mm clear of either paper.
This is an offline motion candidate; contact and extraction require native proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_plan import Compiler,load
from plan_reach import TOOL_TCP,GRIP,tool_frame,heel_supported_pose
from full_scene import TABLE_TOP


def complete_plan(source):
    from yam_arena import ik
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    plan,actions=load(source)
    if plan['requested_stage']!='lever':raise ValueError('A complete proposed lever plan is required')
    c=Compiler();c.frames=list(plan['frames']);c.audit=list(plan['kinematic_audit'])
    c.q={'left':actions[-1,:6].copy(),'right':actions[-1,7:13].copy()}
    c.opening={'left':actions[-1,6],'right':actions[-1,13]}
    initial=np.array((.28,-.20,TABLE_TOP+.003));parked=initial+[0.,0.,.08]
    R=tool_frame(0.)
    def tcp(root,R):return np.asarray(root)+R@TOOL_TCP,R@GRIP
    c.segment('Carry the remover above its resting place',1.,{'right':tcp(parked,R)})
    c.segment('Orient the remover flat for release',1.,tool_path=lambda u:(parked,ik.slerp_matrix(R,np.eye(3),u)))
    c.segment('Lower the remover onto the table',1.,{'right':tcp(initial,np.eye(3))})
    release_step=len(c.frames)+1
    c.segment('Release the remover and extracted staple',.5,openings={'right':1.})
    c.segment('Clear the released remover',.8,{'right':tcp(parked,np.eye(3))})
    c.segment('Inspect the released papers and staple',3.2)
    limits=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    sequence=np.asarray([np.r_[READY,1.,READY,1.]]+[r['action14'] for r in c.frames])
    fraction=float(np.max(np.abs(np.diff(sequence,axis=0))/limits))
    if fraction>1.001 or len(c.frames)>600:raise ValueError(('Ordinary action budget exceeded',len(c.frames),fraction))
    plan.update(requested_stage='extraction_and_release_candidate',frames=c.frames,kinematic_audit=c.audit,
        action_count=len(c.frames),seconds=len(c.frames)/20,max_speed_fraction=fraction,
        released_tool={'from_step':release_step,'position_m':initial.tolist(),'rotation':np.eye(3).tolist()},
        limitations=['Offline candidate; no native remover grasp, valid extraction or final release demonstrated.'])
    plan['source_sha256']['finalize_plan.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    plan['base_plan_sha256']=hashlib.sha256(Path(source).read_bytes()).hexdigest()
    return plan


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();plan=complete_plan(a.base);a.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:plan[k] for k in ('action_count','seconds','max_speed_fraction','released_tool')}))
