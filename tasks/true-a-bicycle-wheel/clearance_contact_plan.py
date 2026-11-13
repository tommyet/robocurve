"""First-quarter candidate with a genuinely clear mouth approach and exit.

Native112 turned the nipple90.54degrees during the tightening stroke, but its
10mm mouth approach touched the square early and its withdrawal stayed jammed.
This route keeps the physical tool and forces unchanged, gives a14mm lead-in,
and holds after a slower16mm withdrawal before any cross-plane movement.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_plan import Compiler,load
from plan_turns import nominal_nipple,rz


def compile_clearance(source):
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    plan,actions=load(source)
    if plan['frames'][147]['stage']!='Clear approach nipple 0':
        raise ValueError('Expected the measured148-action clear approach prefix')
    c=Compiler();c.frames=[dict(f) for f in plan['frames'][:148]]
    c.audit=[e for e in plan['kinematic_audit'] if e['stage'] in {f['stage'] for f in c.frames}]
    a=actions[147];c.q={'left':a[:6].copy(),'right':a[7:13].copy()}
    c.opening={'left':float(a[6]),'right':float(a[13])}
    calibration=plan['held_grasp_calibration']
    c.tool_tcp=np.asarray(calibration['tcp_position_in_tool_m']);c.grip=np.asarray(calibration['tcp_rotation_in_tool'])
    clock=plan['wheel_clocking_deg']
    centre,n=nominal_nipple(0,np.deg2rad(plan['nipple_flat_phase_deg']),np.deg2rad(clock))
    R0=n[:,[1,2,0]]@np.diag((1.,-1.,-1.))@rz(np.pi);R1=R0@rz(np.pi/2)
    def tcp(p,R):return p+R@c.tool_tcp,R@c.grip
    def segment(label,seconds,**kwargs):
        before=len(c.frames);c.segment(label,seconds,**kwargs)
        for f in c.frames[before:]:f['nominal_wheel_clocking_deg']=clock
    segment('Approach nipple 0',1.,targets={'right':tcp(centre-.014*R0[:,1],R0)})
    segment('Approach nipple 0 settle',1.5)
    segment('Nipple 0 quarter 1 insert',2.,targets={'right':tcp(centre,R0)})
    segment('Nipple 0 quarter 1 insertion settle',1.5)
    segment('Nipple 0 quarter 1 tighten',4.,tool_path=lambda u:(centre,R0@rz(u*np.pi/2)))
    segment('Nipple 0 quarter 1 tightening settle',1.)
    withdrawn=centre-.016*R1[:,1]
    segment('Nipple 0 quarter 1 disengage',2.,targets={'right':tcp(withdrawn,R1)})
    segment('Nipple 0 quarter 1 disengagement settle',1.)
    segment('Nipple 0 quarter 1 clear front',1.,targets={'right':tcp(withdrawn-np.array((.045,0.,0.)),R1)})
    commands=np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in c.frames])
    limits=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+
                           [GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    ratio=float(np.max(np.abs(np.diff(commands,axis=0))/limits))
    if ratio>1.001:raise ValueError('Ordinary command speed exceeded')
    result=dict(plan);result.update(frames=c.frames,kinematic_audit=c.audit,action_count=len(c.frames),
        seconds=len(c.frames)/20,max_speed_fraction=ratio,requested_stage='clearance_first_quarter_diagnostic',
        compile_success=True,require_clear_mouth_before_cross_plane_m=.0002,
        limitations=['Native entry and release remain unverified. No physical material, geometry or effort changes.'],
        base_plan_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest())
    result['source_sha256']=dict(plan['source_sha256'])
    result['source_sha256']['clearance_contact_plan.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=compile_clearance(a.source);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('compile_success','action_count','seconds','max_speed_fraction')}))
