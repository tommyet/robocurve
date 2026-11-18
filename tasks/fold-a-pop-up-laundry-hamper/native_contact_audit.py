"""Record native finger collision vertices in the closed gripper/TCP frame."""
import json
import numpy as np
from common import rotation


def record(base, out):
    from pxr import Usd, UsdGeom, UsdPhysics, Gf
    import omni.usd
    from yam_arena.constants import TCP_OFFSET
    stage=omni.usd.get_context().get_stage();cache=UsdGeom.XformCache();result={}
    def array(a):return getattr(a,'torch',a).detach().cpu().numpy()
    for side in ['left','right']:
        robot=base.scene[side+'_robot'];poses=array(robot.data.body_link_pose_w)[0]
        names=list(robot.body_names);g=poses[names.index('gripper')];gR=rotation(g[3:]);tcp=g[:3]+gR@TCP_OFFSET
        result[side]=dict(shapes=[],gripper_force_limit_N=array(robot.data.joint_effort_limits)[0].tolist(),gripper_stiffness=array(robot.data.joint_stiffness)[0].tolist())
        arm='LeftArm' if side=='left' else 'RightArm'
        for name,joint,sign in [('tip_left','joint7',1.),('tip_right','joint8',-1.)]:
            links=[p for p in stage.Traverse() if p.GetName()==name and arm in str(p.GetPath()) and p.HasAPI(UsdPhysics.RigidBodyAPI)]
            assert len(links)==1,(side,name,len(links))
            link=links[0];pose=poses[names.index(name)];R=rotation(pose[3:]);joint_id=robot.find_joints(joint)[0][0];q=float(array(robot.data.joint_pos)[0,joint_id])
            for prim in Usd.PrimRange(link):
                if not prim.HasAPI(UsdPhysics.CollisionAPI):continue
                if prim.IsA(UsdGeom.Mesh):vertices=np.asarray(UsdGeom.Mesh(prim).GetPointsAttr().Get(),float)
                elif prim.IsA(UsdGeom.Cube):
                    size=UsdGeom.Cube(prim).GetSizeAttr().Get();vertices=np.array([[x,y,z] for x in [-.5,.5] for y in [-.5,.5] for z in [-.5,.5]])*size
                else:continue
                relative=cache.GetLocalToWorldTransform(prim)*cache.GetLocalToWorldTransform(link).GetInverse()
                points=np.array([relative.Transform(Gf.Vec3d(*v)) for v in vertices]);closed=((points@R.T+pose[:3]-tcp)@gR)-[sign*abs(q),0,0]
                result[side]['shapes'].append(dict(link=name,path=str(prim.GetPath()),vertices_closed_tcp_m=closed.tolist()))
    (out/'native-gripper-geometry.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
