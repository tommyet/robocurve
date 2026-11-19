"""Disclosed no-slip pinch approximation, implemented as a compliant, force-limited native joint.

A material element must be between closing finger faces and inside their real
working area. The joint starts at the measured pose, without moving either body.
Its world anchor follows the observed hand, without changing task body poses.
It releases on opening or leaving the physical pad faces, and breaks at 30 N or 0.36 Nm. The 2 mm holding margin matches the native pad contact offset; capture still requires the stricter 1 mm margin. This approximates unresolved
finger friction; it does not move, fold, fit or score task material for the robot.
"""
import numpy as np
from scipy.spatial.transform import Rotation


def candidate(point, radius, hand, thickness, half_width, z_range, margin=.001, holding=False):
    local=(np.asarray(point)-hand['tcp'])@hand['rotation']
    q=np.asarray(hand.get('finger_joint_positions',[-hand['opening']*.04695]*2))
    left=q[0]+thickness;right=-q[1]-thickness
    # Opposed contact, allowing 1 mm solver/contact margin on either face.
    if holding:
        # Native contact can leave a small penetration while loaded. A face
        # overlapping the binding is still contact, not an air gap.
        if local[0]-radius>left+margin or local[0]+radius<right-margin:return None
    elif abs((local[0]-radius)-left)>margin or abs((local[0]+radius)-right)>margin:
        return None
    if abs(local[1])>half_width or not z_range[0]<=local[2]<=z_range[1]:return None
    return float(np.linalg.norm(local))


def segment_contact(a,b,radius,hand,thickness,half_width,z_range,margin=.002):
    """Does any part of the actual bound segment remain between both faces?"""
    a=(np.asarray(a)-hand['tcp'])@hand['rotation']
    b=(np.asarray(b)-hand['tcp'])@hand['rotation']
    q=np.asarray(hand.get('finger_joint_positions',[-hand['opening']*.04695]*2))
    lo=np.array([-q[1]-thickness-radius-margin,-half_width,z_range[0]])
    hi=np.array([q[0]+thickness+radius+margin,half_width,z_range[1]])
    if np.any(lo>hi):return False
    u0,u1=0.,1.
    for i in range(3):
        d=b[i]-a[i]
        if abs(d)<1e-12:
            if not lo[i]<=a[i]<=hi[i]:return False
        else:
            p0,p1=sorted([(lo[i]-a[i])/d,(hi[i]-a[i])/d])
            u0=max(u0,p0);u1=min(u1,p1)
            if u0>u1:return False
    return True


class FinitePinch:
    def __init__(self,model,names,radius,thickness,half_width,z_range):
        from pxr import UsdPhysics,PhysicsSchemaTools
        from omni.physx import get_physx_interface
        from omni.physx.bindings._physx import SimulationEvent
        self.m=model;self.names=list(names);self.radius=radius;self.thickness=thickness
        self.radii={name:(.0015 if name.startswith("band_contact_") else radius) for name in names}
        from geometry import BODIES
        self.lengths={b['name']:b['shapes'][0].get('length',0.) for b in BODIES if b['name'] in self.names}
        self.half_width=half_width;self.z_range=z_range;self.held={};self.history={s:[] for s in ['left','right']};self.blocked=set();self.serial=0
        self.grippers={};self.body_paths={}
        for p in model.stage.Traverse():
            if not p.HasAPI(UsdPhysics.RigidBodyAPI):continue
            path=str(p.GetPath())
            if p.GetName()=='gripper':
                for side,arm in [('left','LeftArm'),('right','RightArm')]:
                    if arm in path:self.grippers[side]=path
            if '/materials/' in path and p.GetName() in self.names:self.body_paths[p.GetName()]=path
        assert set(self.grippers)=={'left','right'} and len(self.body_paths)==len(self.names)
        self.root=next(iter(self.body_paths.values())).rsplit('/',1)[0]
        def event(e):
            if e.type!=int(SimulationEvent.JOINT_BREAK):return
            path=str(PhysicsSchemaTools.decodeSdfPath(*e.payload['jointPath']))
            for side,g in list(self.held.items()):
                if path==g['path']:
                    self.m.events.append(dict(event='pinch_slipped',side=side,body=g['body'],time=self.m.time,force_limit_n=30.,torque_limit_nm=.36))
                    g['joint'].GetJointEnabledAttr().Set(False);self.held.pop(side);self.blocked.add(side)
        self.subscription=get_physx_interface().get_simulation_event_stream_v2().create_subscription_to_pop(event)

    def update(self,hands):
        from pxr import UsdPhysics,Sdf,Gf
        from yam_arena.constants import TCP_OFFSET
        for side,h in hands.items():
            if hasattr(self.m,'band_pinch') and side in self.m.band_pinch.held:continue
            history=self.history[side];history.append(float(h['opening']));del history[:-8]
            q=np.asarray(h.get('finger_joint_positions',[-h['opening']*.04695]*2))
            aperture=-q.sum()-2*self.thickness
            held_radius=self.radii[self.held[side]['body']] if side in self.held else max(self.radii.values())
            if aperture>2*held_radius+.002:
                if side in self.held:
                    g=self.held.pop(side);g['joint'].GetJointEnabledAttr().Set(False)
                    self.m.events.append(dict(event='pinch_released',side=side,body=g['body'],time=self.m.time))
                if h['opening']>.30:self.blocked.discard(side)
                continue
            if side in self.held:
                g=self.held[side];now=(self.m.p(g['body'])-h['tcp'])@h['rotation']
                length=self.lengths[g['body']]
                if not segment_contact(self.m.p(g['body'],[0,0,-length/2]),self.m.p(g['body'],[0,0,length/2]),self.radii[g['body']],h,self.thickness,self.half_width,self.z_range):
                    g['joint'].GetJointEnabledAttr().Set(False);self.held.pop(side);self.blocked.add(side)
                    self.m.events.append(dict(event='pinch_slipped',side=side,body=g['body'],time=self.m.time,reason='binding left the physical pad contact region'))
            if side in self.held:
                g=self.held[side];target=np.asarray(h['tcp'])+h['rotation']@g['local_point']
                q=Rotation.from_matrix(h['rotation']@g['local_rotation']).as_quat()
                with Sdf.ChangeBlock():
                    g['joint'].GetLocalPos0Attr().Set(Gf.Vec3f(*target))
                    g['joint'].GetLocalRot0Attr().Set(Gf.Quatf(float(q[3]),Gf.Vec3f(*q[:3])))
            if side in self.held or side in self.blocked or max(history)-h['opening']<.008:continue
            used={g['body'] for g in self.held.values()};choices=[]
            for name in self.names:
                if name in used:continue
                distance=candidate(self.m.p(name),self.radii[name],h,self.thickness,self.half_width,self.z_range)
                if distance is not None:choices.append((distance,name))
            if not choices:continue
            _,name=min(choices);self.serial+=1;path=self.root+f'/pinch_constraint_{side}_{self.serial}'
            joint=UsdPhysics.Joint.Define(self.m.stage,path)
            joint.CreateJointEnabledAttr(False)
            with Sdf.ChangeBlock():
                joint.CreateExcludeFromArticulationAttr(True)
                joint.CreateBody1Rel().SetTargets([Sdf.Path(self.body_paths[name])])
                p=self.m.p(name);q=Rotation.from_matrix(self.m.orientation(name)).as_quat()
                joint.CreateLocalPos0Attr(Gf.Vec3f(*p));joint.CreateLocalPos1Attr(Gf.Vec3f(0,0,0))
                joint.CreateLocalRot0Attr(Gf.Quatf(float(q[3]),Gf.Vec3f(*q[:3])));joint.CreateLocalRot1Attr(Gf.Quatf(1.,Gf.Vec3f(0,0,0)))
                joint.CreateBreakForceAttr(30.);joint.CreateBreakTorqueAttr(.36);joint.CreateCollisionEnabledAttr(True)
                # A force-limited friction approximation, not an infinitely stiff weld.
                for axis in ('transX','transY','transZ','rotX','rotY','rotZ'):
                    linear=axis.startswith('trans')
                    if linear:
                        limit=UsdPhysics.LimitAPI.Apply(joint.GetPrim(),axis);limit.CreateLowAttr(-.05);limit.CreateHighAttr(.05)
                    drive=UsdPhysics.DriveAPI.Apply(joint.GetPrim(),axis);drive.CreateTypeAttr('force')
                    drive.CreateStiffnessAttr(20000. if linear else 2.0*np.pi/180.)
                    drive.CreateDampingAttr(2. if linear else .02*np.pi/180.)
                    drive.CreateMaxForceAttr((30. if linear else 0.36)/np.sqrt(3.))
                    drive.CreateTargetPositionAttr(0.)
                joint.GetJointEnabledAttr().Set(True)
            self.held[side]=dict(body=name,path=path,joint=joint,local_point=((self.m.p(name)-h['tcp'])@h['rotation']).copy(),local_rotation=h['rotation'].T@self.m.orientation(name))
            self.m.events.append(dict(event='pinch_captured',side=side,body=name,time=self.m.time,force_limit_n=30.,torque_limit_nm=.36,local_point=((self.m.p(name)-h['tcp'])@h['rotation']).tolist(),opening=float(h['opening'])))
        self.m.grasp_state={side:dict(body=g['body'],force_limit_n=30.,torque_limit_nm=.36) for side,g in self.held.items()}
