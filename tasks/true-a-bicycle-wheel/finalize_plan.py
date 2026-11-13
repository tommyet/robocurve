"""Append physical tool release and an ordinary rim-spin attempt to a service plan.

Offline kinematics only. No object setter, native force, attachment or scorer is
used. A recorded complete released revolution must still prove feasibility.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_plan import Compiler,load
from wheel_scene import WRENCH_ORIGIN_M


def complete_plan(source):
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    plan,actions=load(source)
    if plan.get('requested_stage')!='repair_candidate' or not plan.get('compile_success'):
        raise ValueError('A compiled complete repair candidate is required')
    c=Compiler();c.frames=list(plan['frames']);c.audit=list(plan['kinematic_audit'])
    c.q={'left':actions[-1,:6].copy(),'right':actions[-1,7:13].copy()}
    c.opening={'left':actions[-1,6],'right':actions[-1,13]}
    cal=plan['held_grasp_calibration'];c.tool_tcp=np.asarray(cal['tcp_position_in_tool_m']);c.grip=np.asarray(cal['tcp_rotation_in_tool'])
    clock=plan['frames'][-1]['nominal_wheel_clocking_deg']
    def segment(*args,**kwargs):
        begin=len(c.frames);c.segment(*args,**kwargs)
        for frame in c.frames[begin:]:frame['nominal_wheel_clocking_deg']=clock
    def tcp(root,R):return np.asarray(root)+R@c.tool_tcp,R@c.grip
    p,R=ik.tcp_pose(c.q['right'],station.BASES['right'])
    tool_R=R@c.grip.T;tool_p=p-tool_R@c.tool_tcp
    parked=np.array((.23,-.005,.88))
    segment('Carry the key to front workspace',1.5,{'right':tcp(parked,tool_R)})
    segment('Lay the key flat above the table',1.5,tool_path=lambda u:(parked,ik.slerp_matrix(tool_R,np.eye(3),u)))
    initial=np.array(WRENCH_ORIGIN_M)
    segment('Return the key above its resting place',.8,{'right':tcp(initial+[0.,0.,.055],np.eye(3))})
    segment('Lower the key onto the table',.8,{'right':tcp(initial,np.eye(3))})
    release_step=len(c.frames)+1
    segment('Release the key',.5,openings={'right':1.})
    segment('Clear the key',.7,{'right':tcp(initial+[0.,0.,.07],np.eye(3))})
    origin=np.array((.35,0.,1.005));p0,R0=ik.tcp_pose(c.q['left'],station.BASES['left'])
    max_pe=max_re=0.
    for k in range(1,10):
        t=k/20;omega=1.5;rise=.15
        theta=.5*omega/rise*t*t if t<=rise else omega*(t-.5*rise)
        co,si=np.cos(theta),np.sin(theta);rot=np.array(((1.,0.,0.),(0.,co,-si),(0.,si,co)))
        p=origin+rot@(p0-origin);R=rot@R0
        q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),c.q['left'],station.BASES['left'],iters=400,damping=.008,tol=1e-7)
        if pe>.0001 or re>.001:raise ValueError(('Rim spin reach',k,pe,re))
        max_pe=max(max_pe,pe);max_re=max(max_re,re);c.q['left']=q
        # The hand opens while still moving tangentially. Physics must transfer
        # the impulse and carry the wheel after release; no angle is imposed.
        fraction=np.clip((t-.15)/.25,0.,1.)
        c.opening['left']=float(.16+(.80-.16)*fraction)
        c.frames.append(dict(stage='Spin the rim and open the hand',nominal_wheel_clocking_deg=clock+np.degrees(theta),action14=np.r_[q,c.opening['left'],c.q['right'],c.opening['right']].tolist()))
    clock+=np.degrees(theta)
    c.audit.append(dict(stage='Spin the rim and open the hand',seconds=.45,interpolation='constant-speed rim arc after acceleration',max_position_error_m=max_pe,max_rotation_error_rad=max_re))
    # Clear radially before crossing the wheel plane. An axial-only withdrawal
    # swept a far-side fingertip through a spoke in the full-frame hull audit.
    radial=p-origin;radial[0]=0.;radial/=np.linalg.norm(radial)
    clear=p+.03*radial
    segment('Open clear of the rim radially',.6,{'left':(clear,R)},openings={'left':1.})
    segment('Clear the spinning wheel plane',.7,{'left':(clear-np.array((.08,0.,0.)),R)})
    segment('Observe the released wheel',12.)
    limits=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    all_actions=np.asarray([np.r_[READY,1.,READY,1.]]+[r['action14'] for r in c.frames])
    ratio=float(np.max(np.abs(np.diff(all_actions,axis=0))/limits))
    if ratio>1.001 or len(c.frames)>1200:raise ValueError(('Ordinary action budget/speed exceeded',len(c.frames),ratio,np.unravel_index(np.argmax(np.abs(np.diff(all_actions,axis=0))/limits),np.diff(all_actions,axis=0).shape)))
    plan.update(requested_stage='repair_and_released_revolution_candidate',frames=c.frames,kinematic_audit=c.audit,action_count=len(c.frames),seconds=len(c.frames)/20,max_speed_fraction=ratio,released_tool={'from_step':release_step,'position_m':initial.tolist(),'rotation':np.eye(3).tolist()},limitations=['Offline candidate only; robot repair, released tool and complete free revolution all need native evidence.'])
    plan['source_sha256']['finalize_plan.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    plan['base_plan_sha256']=hashlib.sha256(Path(source).read_bytes()).hexdigest()
    return plan


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();plan=complete_plan(a.base);a.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:plan[k] for k in ('action_count','seconds','max_speed_fraction','released_tool')}))
