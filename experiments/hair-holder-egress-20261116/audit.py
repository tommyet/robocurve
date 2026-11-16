import sys,json,hashlib,importlib.util
from pathlib import Path
import numpy as np
sys.path.insert(0,'/private/tmp/spray-yam-source')
from yam_arena.urdf import quat_xyzw_to_matrix
from yam_arena import YAM_URDF
CAP=Path('/private/tmp/revision-completed-before-roll/yam-eval/hair-opposite-sweep-002')
spec=importlib.util.spec_from_file_location('holder_mesh_geometry',CAP/'source/switch_geometry.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);geometry=mod.FingerGeometry()
spec=importlib.util.spec_from_file_location('holder_config',CAP/'source/config.py');cfg=importlib.util.module_from_spec(spec);spec.loader.exec_module(cfg)
x,y,z=cfg.DRYER_START;T=cfg.TOP;h=z-.026-T-.012
holders=[('foot',np.array((x+.035,y,T+.006)),np.array((.12,.15,.012)))]
for i,sign in enumerate([-1,1]):holders += [(f'post_{i}',np.array((x+.060,y+sign*.055,T+.012+h/2)),np.array((.016,.016,h))),(f'cradle_{i}',np.array((x+.005,y+sign*.032,z-.026)),np.array((.080,.015,.020))),(f'bracket_{i}',np.array((x+.060,y+sign*.043,z-.026)),np.array((.016,.035,.020)))]

def boxgap(tri,p,size):
 v=tri-p;flat=v.reshape(-1,3);half=size/2
 broad=float(np.maximum(flat.min(0)-half,-half-flat.max(0)).max())
 if broad>.002:return broad
 edges=np.concatenate((v[:,1]-v[:,0],v[:,2]-v[:,1],v[:,0]-v[:,2]));normals=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);axes=np.concatenate((np.eye(3),normals,np.cross(edges,[1,0,0]),np.cross(edges,[0,1,0]),np.cross(edges,[0,0,1])))
 n=np.linalg.norm(axes,axis=1);axes=np.unique(np.round(axes[n>1e-10]/n[n>1e-10,None],8),axis=0);pr=flat@axes.T;rad=np.abs(axes)@half
 return float(np.maximum(pr.min(0)-rad,-rad-pr.max(0)).max())

def worldpieces(row):
 owners=row['native_owner_poses'];links={p.rsplit('/',1)[-1]:np.array(v) for p,v in owners.items() if '/LeftArm/' in p}
 return [(n,tri@quat_xyzw_to_matrix(links[n][3:]).T+links[n][:3]) for n,tri in geometry.meshes]

def audit(row):
 best=(10.,None,None);inside=(0.,None,None);pieces=worldpieces(row)
 for k,(n,t) in enumerate(pieces):
  for label,p,size in holders:
   broad=float(np.maximum(t.min((0,1))-(p+size/2),(p-size/2)-t.max((0,1))).max())
   if broad>best[0] and broad>.002:continue
   gap=boxgap(t,p,size)
   if gap<best[0]:best=(gap,n,label,k)
   if broad<0:
    depth=np.min(size/2-np.abs(t.reshape(-1,3)-p),axis=1).max()
    if depth>inside[0]:inside=(float(depth),n,label,k)
 return {'time_s':row['time'],'phase':row['phase'],'gap_m':best[0],'pair':best[1:],'max_mesh_vertex_inside_holder_m':inside[0],'inside_pair':inside[1:]}

if __name__=='__main__':
 rows=[json.loads(l) for l in (CAP/'trajectory.jsonl').open()];records=[audit(r) for r in rows]
 lift=[r for r in records if r['phase']=='lift_dryer'];nonpositive=[r for r in records if r['gap_m']<=0];lin=[r for r in lift if r['gap_m']<=0]
 report={'scope':'Native POSTSTEP body_link poses and corrected URDF collision-origin XYZ/RPY; signed convex SAT is geometry, NOT force/contact readback. Mesh vertices strictly inside holder prove geometric overlap independently.','trace_sha256':hashlib.sha256((CAP/'trajectory.jsonl').read_bytes()).hexdigest(),'urdf_sha256':hashlib.sha256(Path(YAM_URDF).read_bytes()).hexdigest(),'holder_boxes':[{'name':n,'center':p.tolist(),'size':s.tolist()} for n,p,s in holders],'rows':len(rows),'first_nonpositive':nonpositive[0] if nonpositive else None,'first_lift_nonpositive':lin[0] if lin else None,'minimum':min(records,key=lambda r:r['gap_m']),'minimum_lift':min(lift,key=lambda r:r['gap_m']),'last':records[-1],'records':records}
 Path('/private/tmp/hair-holder-egress-cpu/report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['records','holder_boxes']},indent=2))
