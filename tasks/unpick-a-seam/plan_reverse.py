"""Reverse the ripper along its entry path before moving between stitches.

The327-action first-cut/withdrawal prefix completed in native187. The full
six-cut plan remains unvalidated. No simulator is started.
The future runner must stop tool-pose compensation before intentional release.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from yam_arena import ik,station
from yam_arena.constants import FINGER_OPEN,READY,SHOULDER,WRIST,GRIPPER
from plan import DOWN
from plan_cut import GRASP_OFFSET
from tool_geometry import BLADE_OFFSET
from geometry import TABLE_TOP

base=Path('tasks/unpick-a-seam/evidence')
first=json.loads((base/'clamp-cut-plan.json').read_text())
frames=[dict(row) for row in first['frames'][:267]]
state={side:{'q':np.array(frames[-1]['action14'][offset:offset+6]),
             'finger':frames[-1]['action14'][offset+6]*FINGER_OPEN}
       for side,offset in (('left',0),('right',7))}
position_error=rotation_error=0.
phase_errors={}

def transition(seconds,label,goals):
    global position_error,rotation_error
    starts={side:(*ik.tcp_pose(s['q'],station.BASES[side]),s['finger']) for side,s in state.items()}
    count=round(seconds*20)
    for step in range(1,count+1):
        w=ik.smoothstep(step/count);action=[]
        for side,s in state.items():
            p0,r0,f0=starts[side];p1,r1,f1=goals.get(side,(p0,r0,f0))
            p=p0+(np.asarray(p1)-p0)*w;r=ik.slerp_matrix(r0,np.asarray(r1),w)
            q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(r),s['q'],station.BASES[side],iters=200,tol=1e-6)
            if pe>.001 or re>np.deg2rad(.5):raise RuntimeError((label,side,pe,re))
            position_error=max(position_error,pe);rotation_error=max(rotation_error,re)
            rec=phase_errors.setdefault(label,dict(position_m=0.,rotation_rad=0.))
            rec['position_m']=max(rec['position_m'],pe);rec['rotation_rad']=max(rec['rotation_rad'],re)
            s['q']=q;s['finger']=f0+(f1-f0)*w
            action.extend([*q.tolist(),float(np.clip(s['finger']/FINGER_OPEN,0.,1.))])
        frames.append(dict(phase=label,action14=action))

_,hand_r=ik.tcp_pose(state['right']['q'],station.BASES['right']);tool_r=hand_r@DOWN.T
blade=np.array((first['feed_blade_x_m'],.046,first['feed_blade_z_m']))
def tcp(edge):return edge-tool_r@np.asarray(BLADE_OFFSET)+tool_r@GRASP_OFFSET
transition(2.,'back the blade out along its entry path after the first cut',{'right':(tcp(blade),tool_r@DOWN,-.0055)})
blade[0]-=.030
transition(1.,'move the unhooked ripper clear of the first tack',{'right':(tcp(blade),tool_r@DOWN,-.0055)})
for number,y in enumerate((.018,.006,-.006,-.018,-.030),2):
    blade[1]=y+.016
    transition(1.,f'move clear of tack {number}',{'right':(tcp(blade),tool_r@DOWN,-.0055)})
    blade[0]=first['feed_blade_x_m']
    transition(1.,f'place leading point before tack {number}',{'right':(tcp(blade),tool_r@DOWN,-.0055)})
    blade[1]=y-.003
    transition(1.5,f'feed blade through tack {number}',{'right':(tcp(blade),tool_r@DOWN,-.0055)})
    blade[1]=y+.016
    transition(2.,f'back out along the entry path after tack {number}',{'right':(tcp(blade),tool_r@DOWN,-.0055)})
    blade[0]-=.020 if number==6 else .030
    transition(1.,f'withdraw from tack {number}',{'right':(tcp(blade),tool_r@DOWN,-.0055)})
    if number==6:
        # The final inward station approaches a wrist limit on a straight30mm
        # pull. After20mm normal clearance, move diagonally into free space.
        blade[0]-=.010;blade[1]+=.020
        transition(1.,'finish last withdrawal in free space',{'right':(tcp(blade),tool_r@DOWN,-.0055)})
# Move in front of the fixture before changing the tool orientation.
blade[0]=.215
transition(1.,'move ripper clear of repair fixture',{'right':(tcp(blade),tool_r@DOWN,-.0055)})
handle=np.array((.200,-.120,TABLE_TOP+.008))
transition(2.,'turn ripper above its table rest',{'right':(handle+GRASP_OFFSET+[0.,0.,.060],DOWN,-.0055)})
transition(2.,'lower ripper to table',{'right':(handle+GRASP_OFFSET,DOWN,-.0055)})
transition(.5,'settle ripper before releasing',{})
compensation_until=len(frames)
transition(1.,'release ripper handle',{'right':(handle+GRASP_OFFSET,DOWN,FINGER_OPEN)})
transition(1.,'withdraw open hand',{'right':(handle+GRASP_OFFSET+[0.,0.,.080],DOWN,FINGER_OPEN)})
transition(1.,'hold final inspection',{})
a=np.array([row['action14'] for row in frames]);limits=np.tile([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20],2)
ratio=np.abs(np.diff(np.vstack((np.tile(np.r_[READY,1.],2),a)),axis=0))/limits
if ratio.max()>1.001:raise RuntimeError(('rate limit',ratio.max()))
if not np.array_equal(a[:267],np.array([row['action14'] for row in first['frames'][:267]])):raise RuntimeError('Pickup/feed prefix changed')
r={k:v for k,v in first.items() if k not in ('frames','status','plan_source_sha256')}
r.update(status='unrun cut-all-first candidate; reverse blade along entry path before moving between tacks; fragment removal still required',frames=frames,
    maximum_ik_position_error_m=position_error,maximum_ik_rotation_error_rad=rotation_error,
    maximum_action_rate_fraction=float(ratio.max()),pose_assisted_entry_until_step=compensation_until,
    requires_pose_compensation_release_boundary=True,first_tack_prefix_actions=327,
    phase_ik_error=phase_errors,plan_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
out=Path('tasks/unpick-a-seam/seam-reverse-plan.json')
out.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ('status','maximum_ik_position_error_m','maximum_ik_rotation_error_rad','maximum_action_rate_fraction','pose_assisted_entry_until_step')}))
print('frames',len(frames),'seconds',len(frames)/20,'out',out)
