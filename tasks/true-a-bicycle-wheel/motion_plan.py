"""Compile ordinary YAM joint commands from the published fixed wheel layout.

No simulator state, contact flags, material values or scorer feedback enter the
plan. Reachability is not evidence of grip, collision clearance or task success.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from plan_turns import nominal_nipple,rz
from wheel_scene import WRENCH_ORIGIN_M,WRENCH_TCP_M

CLOCKING_DEG=50.
FLAT_PHASE_DEG=45.
TOOL_TCP=np.array(WRENCH_TCP_M)
GRIP=np.diag((1.,-1.,-1.))


class Compiler:
    def __init__(self):
        from yam_arena import ik,station
        from yam_arena.constants import READY
        self.ik,self.station=ik,station
        self.tool_tcp=TOOL_TCP.copy();self.grip=GRIP.copy()
        self.q={side:np.asarray(READY,float).copy() for side in ('left','right')}
        self.opening={side:1. for side in self.q};self.frames=[];self.audit=[]

    def segment(self,label,seconds,targets=None,openings=None,joint=False,tool_path=None):
        targets=targets or {};openings=openings or {};ik=self.ik
        start={side:ik.tcp_pose(q,self.station.BASES[side]) for side,q in self.q.items()}
        q0={side:q.copy() for side,q in self.q.items()};opening0=self.opening.copy()
        goals={};max_pe=max_re=0.
        if joint:
            for side,(p,R) in targets.items():
                q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),self.q[side],self.station.BASES[side],iters=400,damping=.008,tol=1e-7)
                if pe>.0001 or re>.001:raise ValueError(f'Unreachable {label}/{side}: {pe}m,{re}rad')
                goals[side]=q
        count=max(1,round(seconds*20))
        for step in range(1,count+1):
            u=ik.smoothstep(step/count)
            for side in self.q:
                if side in goals:self.q[side]=q0[side]+u*(goals[side]-q0[side])
                elif side in targets or (side=='right' and tool_path is not None):
                    if side=='right' and tool_path is not None:
                        center,R=tool_path(u);p=center+R@self.tool_tcp;R=R@self.grip
                    else:
                        p0,R0=start[side];p1,R1=targets[side]
                        p=p0+u*(np.asarray(p1)-p0);R=ik.slerp_matrix(R0,R1,u)
                    q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),self.q[side],self.station.BASES[side],iters=120,damping=.008,tol=1e-7)
                    max_pe=max(max_pe,pe);max_re=max(max_re,re);self.q[side]=q
                    if pe>.0001 or re>.001:raise ValueError(f'Path unreachable {label}/{side} step{step}: {pe}m,{re}rad')
                self.opening[side]=opening0[side]+u*(openings.get(side,opening0[side])-opening0[side])
            self.frames.append(dict(stage=label,action14=np.r_[self.q['left'],self.opening['left'],self.q['right'],self.opening['right']].tolist()))
        self.audit.append(dict(stage=label,seconds=count/20,interpolation='joint' if joint else 'Cartesian/tool',max_position_error_m=max_pe,max_rotation_error_rad=max_re))


def compile_plan(stage='pickup'):
    from yam_arena import ik,YAM_URDF
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    c=Compiler();tilt=np.deg2rad(-45.);z=np.array((0.,np.sin(tilt),-np.cos(tilt)));x=np.array((1.,0.,0.))
    left_R=np.column_stack((x,np.cross(z,x),z))
    # A point on the continuous rim70 degrees around from its bottom; this
    # stays fixed in world coordinates for any explicit initial wheel clocking.
    radial=np.array((0.,np.sin(np.deg2rad(70.)),-np.cos(np.deg2rad(70.))))
    rim=np.array((.35,0.,1.005))+.210*radial
    left_hold=rim-.008*z;left_above=rim-.048*z
    pickup=np.array(WRENCH_ORIGIN_M);above=pickup+np.array((0.,0.,.0645))
    tcp=lambda center,R:(center+R@TOOL_TCP,R@GRIP)
    c.segment('Approach wrench and rim',1.5,{'left':(left_above,left_R),'right':tcp(above,np.eye(3))},openings={'left':.35},joint=True)
    c.segment('Lower to handle and rim',.75,{'left':(left_hold,left_R),'right':tcp(pickup,np.eye(3))})
    c.segment('Grip handle and steady rim',.6,openings={'left':.16,'right':.10})
    lifted=pickup+np.array((0.,0.,.080))
    c.segment('Lift the free wrench',.75,{'right':tcp(lifted,np.eye(3))})
    c.segment('Hold pickup for inspection',.5)
    if stage=='turns':
        for spoke in (0,2):
            center,nipple=nominal_nipple(spoke,np.deg2rad(FLAT_PHASE_DEG),np.deg2rad(CLOCKING_DEG))
            R0=nipple[:,[1,2,0]]@np.diag((1.,-1.,-1.))@rz(np.pi)
            R1=R0@rz(np.pi/2);pre=center-.014*R0[:,1]
            clear=pre-np.array((.10,0.,0.))
            c.segment(f'Clear approach to nipple {spoke}',1.,{'right':tcp(clear,R0)},joint=True)
            c.segment(f'Approach nipple {spoke}',.7,{'right':tcp(pre,R0)})
            for turn in range(3):
                prefix=f'Nipple {spoke}, quarter turn {turn+1}'
                c.segment(prefix+': insert wrench',.3,{'right':tcp(center,R0)})
                c.segment(prefix+': tighten',.9,tool_path=lambda u,p=center,R=R0:(p,R@rz(u*np.pi/2)))
                withdrawn=center-.014*R1[:,1]
                c.segment(prefix+': disengage mouth',.3,{'right':tcp(withdrawn,R1)})
                # The nipple stays in the clear front quadrant during this
                # reset arc. The14mm lateral withdrawal clears the6mm jaw.
                c.segment(prefix+': reset wrench angle',.5,tool_path=lambda u,p=withdrawn:(p,ik.slerp_matrix(R1,R0,u)))
                c.segment(prefix+': return mouth',.4,{'right':tcp(pre,R0)})
        c.segment('Withdraw the wrench',.7,{'right':tcp(pre-np.array((.10,0.,0.)),R0)})
        c.segment('Release the rim',.6,openings={'left':.35})
        c.segment('Hands clear for inspection',.75,{'left':(left_above,left_R)})
        c.segment('Released settling',1.)
    initial=np.r_[READY,1.,READY,1.];actions=np.asarray([initial]+[r['action14'] for r in c.frames])
    limits=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    delta=np.abs(np.diff(actions,axis=0));ratio=np.max(delta/limits)
    if ratio>1.001:raise ValueError(f'Ordinary joint speed limit exceeded by{ratio:.3f}x')
    return dict(schema='wheel-fixed-motion-v1',kind='diagnostic_joint_commands_not_task_demo',control_hz=20,
        requested_stage=stage,robot_success=False,task_score=None,wheel_clocking_deg=CLOCKING_DEG,nipple_flat_phase_deg=FLAT_PHASE_DEG,
        reset_profile='two-defect-candidate',source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
          for name in ('motion_plan.py','wheel_scene.py','plan_turns.py','fixture_layout.py')},urdf_sha256=hashlib.sha256(Path(YAM_URDF).read_bytes()).hexdigest(),
        action_count=len(c.frames),seconds=len(c.frames)/20,max_speed_fraction=float(ratio),
        limitations=['No native grasp or collision proof','Turns stage does not yet include a released revolution judging demonstration'],
        frames=c.frames,kinematic_audit=c.audit)


def load(path):
    plan=json.loads(Path(path).read_text())
    if plan.get('schema')!='wheel-fixed-motion-v1' or plan.get('control_hz')!=20:raise ValueError('Unexpected wheel action plan')
    actions=np.asarray([r['action14'] for r in plan['frames']],float)
    if actions.ndim!=2 or actions.shape[1]!=14 or not 1<=len(actions)<=1200 or not np.isfinite(actions).all():raise ValueError('Invalid bounded14-D commands')
    if np.any(actions[:,[6,13]]<0) or np.any(actions[:,[6,13]]>1):raise ValueError('Invalid gripper opening')
    return plan,actions


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=('pickup','turns'),default='pickup');parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();plan=compile_plan(a.stage);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:plan[k] for k in ('requested_stage','action_count','seconds','max_speed_fraction')}))
