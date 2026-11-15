"""Contact-driven spring pegs with ideal static grip and native flexible cloth.

Measured finger compression opens the jaws. A peg follows a hand only after
its handles are between the pads. Releasing closes it; it stays on the line
only when the line is inside the mouth. Actual cloth vertices in that mouth
are constrained to the jaw until it is opened. No target hem or task score
selects captured material. Spring force, frictional slip and free-peg tumbling
are approximated; garment gravity, bending and self-contact remain native FEM.
"""
import math
import numpy as np


def ry(a):
    c,s=math.cos(a),math.sin(a)
    return np.array(((c,0,s),(0,1,0),(-s,0,c)))


def configure(stage, root):
    from pxr import UsdPhysics,PhysxSchema
    for prim in stage.Traverse():
        if str(prim.GetPath()).startswith(root+'/'):
            if prim.IsA(UsdPhysics.Joint):UsdPhysics.Joint(prim).CreateJointEnabledAttr(False)
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                UsdPhysics.RigidBodyAPI(prim).CreateKinematicEnabledAttr(True)
                PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateEnableCCDAttr(False)


class Peg:
    def __init__(self,position,angle):
        self.p=np.array(position,float);self.R=ry(angle);self.opening=-.075
        self.held=None;self.clipped=True;self.indices=[];self.local=None
        self.events=[];self.time=0.;self.v=np.zeros(3)

    def update(self,hands,points,dt):
        self.time+=dt;previous=self.held
        if self.held is None:
            for side,tcp,R,gap in hands:
                handle=(np.asarray(tcp)-self.p)@self.R
                # Handle centre and pad-closing direction, measured in jaw frame.
                if (np.linalg.norm(handle-[-.0175,0,0])<.012 and
                    abs(float(R[:,0]@self.R[:,2]))>.80 and gap<.024):
                    self.held=side;self.grip_p=R.T@(self.p-tcp);self.grip_R=R.T@self.R
                    self.events.append(dict(time_s=self.time,event='handles_grasped',side=side));break
        if self.held is not None:
            side,tcp,R,gap=next(h for h in hands if h[0]==self.held)
            self.p=np.asarray(tcp)+R@self.grip_p;self.R=R@self.grip_R
            if gap<.027:
                self.opening=-float(np.clip((.022-gap+.0003)/.0175,.075,.45))
                if self.opening<-.15:
                    if self.clipped:self.events.append(dict(time_s=self.time,event='opened'))
                    self.clipped=False;self.indices=[]
            else:
                self.held=None;self.opening=-.075
                point=np.array((.52,self.p[1],1.09));local=(point-self.p)@self.R
                # The3mm line lies within the30mm gripping mouth; jaw rotation
                # closes onto it. This geometric fit replaces submillimetre friction.
                self.clipped=bool(abs(self.p[1])<.235 and .020<local[0]<.036 and
                                  abs(local[1])<.004 and -.003<local[2]<.004)
                self.indices=[]
                if self.clipped:
                    q=(points-self.p)@self.R
                    inside=(q[:,0]>.015)&(q[:,0]<.036)&(abs(q[:,1])<.005)&(abs(q[:,2])<.006)
                    self.indices=np.flatnonzero(inside).tolist();self.local=q[self.indices].copy()
                self.events.append(dict(time_s=self.time,event='released',clipped=self.clipped,captured_vertices=len(self.indices)))
        elif not self.clipped:
            self.v[2]-=9.81*dt;self.p+=self.v*dt
            if self.p[2]<.7825:self.p[2]=.7825;self.v[:]=0.
        return previous!=self.held


def install(base,cloth_name='tshirt'):
    import torch,omni.usd,omni.physics.tensors as tensors
    from pxr import UsdUtils,Sdf,Vt,Gf,UsdGeom
    from scipy.spatial.transform import Rotation
    from interpret_motion import rotation_xyzw
    from yam_arena.constants import FINGER_JOINTS,TCP_OFFSET
    from arena_props import PEG_SPECS
    stage=omni.usd.get_context().get_stage();cache=UsdUtils.StageCache.Get()
    stage_id=cache.GetId(stage).ToLongInt()
    if stage_id<0:cache.Insert(stage);stage_id=cache.GetId(stage).ToLongInt()
    sim=tensors.create_simulation_view('torch',stage_id);sim.set_subspace_roots('/')
    cloth=base.scene[cloth_name];root='/World/envs/env_0/';cloth_path=root+cloth_name
    hands=[]
    for side in ('left','right'):
        r=base.scene[side+'_robot'];hands.append((side,r,list(r.body_names).index('gripper'),r.find_joints(list(FINGER_JOINTS),preserve_order=True)[0]))
    items={}
    for name,spec in PEG_SPECS.items():
        peg=Peg(spec.pos,spec.base_angle)
        view=sim.create_rigid_body_view([root+name+'/lower',root+name+'/upper'])
        paths=list(view.prim_paths);order=[paths.index(root+name+'/'+s) for s in ('lower','upper')]
        attachment=stage.DefinePrim(root+name+'_cloth_grip','OmniPhysicsVtxXformAttachment')
        attachment.CreateRelationship('omniphysics:src0').SetTargets([Sdf.Path(cloth_path)])
        attachment.CreateRelationship('omniphysics:src1').SetTargets([Sdf.Path(root+name+'/lower')])
        enabled=attachment.CreateAttribute('omniphysics:attachmentEnabled',Sdf.ValueTypeNames.Bool);enabled.Set(False)
        indices=attachment.CreateAttribute('omniphysics:vtxIndicesSrc0',Sdf.ValueTypeNames.IntArray);indices.Set([])
        positions=attachment.CreateAttribute('omniphysics:localPositionsSrc1',Sdf.ValueTypeNames.Point3fArray);positions.Set([])
        ops=[]
        for side in ('lower','upper'):
            xform=UsdGeom.Xformable(stage.GetPrimAtPath(root+name+'/'+side))
            by_type={op.GetOpType():op for op in xform.GetOrderedXformOps()}
            translation=by_type.get(UsdGeom.XformOp.TypeTranslate)
            orient=by_type.get(UsdGeom.XformOp.TypeOrient)
            if translation is None:translation=xform.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble)
            if orient is None:orient=xform.AddOrientOp(UsdGeom.XformOp.PrecisionDouble)
            xform.SetXformOpOrder([translation,orient]);ops.append((translation,orient))
        items[name]=(peg,view,order,enabled,indices,positions,ops)
    original=base.scene.write_data_to_sim
    def array(x):return getattr(x,'torch',x).detach().cpu().numpy()
    def apply(*args,**kwargs):
        result=original(*args,**kwargs);observed=[];points=array(cloth.data.nodal_pos_w)[0]
        for side,r,body,fingers in hands:
            pose=array(r.data.body_link_pose_w)[0,body];R=rotation_xyzw(pose[3:]);gap=float(abs(array(r.data.joint_pos)[0,fingers]).sum())
            observed.append((side,pose[:3]+R@np.asarray(TCP_OFFSET),R,gap))
        for name,(peg,view,order,enabled,indices,positions,ops) in items.items():
            old=tuple(peg.indices);peg.update(observed,points,float(base.physics_dt))
            if tuple(peg.indices)!=old:
                enabled.Set(False)
                if peg.indices:
                    indices.Set(peg.indices);positions.Set(Vt.Vec3fArray(peg.local.tolist()));enabled.Set(True)
            # GPU rigid-body tensors do not implement kinematic targets in
            # this Isaac build. PhysX reads ordinary USD transforms for
            # kinematic bodies; retain the native colliders and attachments.
            with Sdf.ChangeBlock():
                for (translation,orient),R in zip(ops,(peg.R,peg.R@ry(peg.opening))):
                    q=Rotation.from_matrix(R).as_quat()
                    translation.Set(Gf.Vec3d(*map(float,peg.p)))
                    value=Gf.Quatd(float(q[3]),Gf.Vec3d(*map(float,q[:3])))
                    if orient.GetPrecision()==UsdGeom.XformOp.PrecisionFloat:value=Gf.Quatf(value)
                    orient.Set(value)
        return result
    base.scene.write_data_to_sim=apply
    # Keep the parent tensor view alive for the complete simulation.
    return dict(simulation_view=sim,pegs={name:item[0] for name,item in items.items()})
