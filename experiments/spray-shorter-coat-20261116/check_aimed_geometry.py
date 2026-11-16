"""CPU predicted command geometry; not native contacts or a new robot trajectory."""
import sys,json,struct,xml.etree.ElementTree as ET,argparse
from pathlib import Path
import numpy as np
from pxr import Usd,UsdGeom
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tasks/uncap-spray-panel'))
from yam_arena import YAM_URDF,ik
from yam_arena.urdf import forward_kinematics,rpy_matrix
import aimed_demo,recorded_demo
TOP=.7475;BASES=(np.array([0,.305,.75]),np.array([0,-.305,.75]))

def gap(tri,p,R,size):
 v=(tri-p)@R;flat=v.reshape(-1,3);half=np.asarray(size)/2;bbox=np.maximum(flat.min(0)-half,-half-flat.max(0))
 if bbox.max()>.0003:return float(bbox.max())
 edges=np.concatenate([v[:,1]-v[:,0],v[:,2]-v[:,1],v[:,0]-v[:,2]]);normals=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);axes=np.concatenate([np.eye(3),normals,np.cross(edges,[1,0,0]),np.cross(edges,[0,1,0]),np.cross(edges,[0,0,1])]);n=np.linalg.norm(axes,axis=1);axes=axes[n>1e-10]/n[n>1e-10,None];axes=np.unique(np.round(axes,7),axis=0);proj=flat@axes.T;radius=abs(axes)@half
 return float(np.max(np.maximum(proj.min(0)-radius,-radius-proj.max(0))))

def loadrobot():
 raw=[]
 for link in ET.parse(YAM_URDF).getroot().findall('link'):
  for c in link.findall('collision'):
   m=c.find('geometry/mesh');data=(YAM_URDF.parent/m.attrib['filename']).read_bytes();n=struct.unpack_from('<I',data,80)[0];tri=np.ndarray(n,dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]),buffer=data,offset=84)['v'].astype(float);o=c.find('origin');p=np.fromstring(o.attrib.get('xyz','0 0 0'),sep=' ');R=rpy_matrix(np.fromstring(o.attrib.get('rpy','0 0 0'),sep=' '));scale=np.fromstring(m.attrib.get('scale','1 1 1'),sep=' ');raw.append((link.attrib['name'],tri*scale@R.T+p))
 assert len(raw)==315;return raw

def world(raw,a,arm):
 q=a[arm*7:arm*7+6];f=a[arm*7+6]*-.04695;fk=forward_kinematics(YAM_URDF,{**{f'joint{i+1}':float(v)for i,v in enumerate(q)},'joint7':float(f),'joint8':float(f)})
 return[(n,t@fk[n][:3,:3].T+fk[n][:3,3]+BASES[arm])for n,t in raw]

def obstacles(source):
 obs=[('riser',np.array([.26,0,TOP+.025]),np.eye(3),np.array([.08,.08,.05])),('backing',np.array([.478,-.035,.9525]),np.eye(3),np.array([.012,.36,.36]))]
 st=Usd.Stage.Open(str(source/'stand.usda'));cache=UsdGeom.XformCache()
 for prim in st.Traverse():
  if prim.IsA(UsdGeom.Cube):
   size=float(UsdGeom.Cube(prim).GetSizeAttr().Get());M=np.array(cache.GetLocalToWorldTransform(prim)).T;scale=np.linalg.norm(M[:3,:3],axis=0);obs.append((str(prim.GetPath()),M[:3,3]+[.52,-.035,TOP],M[:3,:3]/scale,size*scale))
 return obs

def run(source):
 rows=[json.loads(l)for l in(source/'trajectory.jsonl').read_text().splitlines()];a,_=aimed_demo.load_dataset();a=a.astype(np.float32).astype(float);old,_=recorded_demo.load_dataset();raw=loadrobot();static=obstacles(source);mins={};bad=[];mutual=[]
 for i in range(531,779):
  row=rows[i+1];shift=np.array([.022,-.002,0])*ik.smoothstep((i-530)/80);capR=np.asarray(row['cap_rotation']).reshape(3,3)
  canR=np.asarray(row['can_rotation']).reshape(3,3);canp=np.asarray(row['can'])+shift
  obs=static+[('parked_cap_outer_conservative',np.asarray(row['cap']),capR,np.array([.062,.062,.036])),('held_can_body_proxy',canp+canR@np.array([0,0,-.005]),canR,np.array([.052,.052,.13])),('held_can_shoulder_proxy',canp+canR@np.array([0,0,.065]),canR,np.array([.046,.046,.01]))]
  arms=[world(raw,a[i],arm)for arm in(0,1)]
  for arm,parts in enumerate(arms):
   best=(10,None,None)
   for name,t in parts:
    g=float(t[:,:,2].min()-TOP)
    if g<best[0]:best=(g,name,'table')
    for label,p,R,size in obs:
     if label.startswith('held_can_')and name in('gripper','tip_left','tip_right'):continue
     g=gap(t,p,R,size)
     if g<best[0]:best=(g,name,label)
   if best[0]<mins.get(str(arm),(10,))[0]:mins[str(arm)]=[best[0],i,*best[1:]]
   if best[0]<0:bad.append([i,arm,*best])
  bounds=[[(t.reshape(-1,3).min(0),t.reshape(-1,3).max(0))for _,t in parts]for parts in arms];lo0,hi0=np.array(bounds[0]).transpose(1,0,2);lo1,hi1=np.array(bounds[1]).transpose(1,0,2);gaps=np.maximum(lo0[:,None]-hi1[None],lo1[None]-hi0[:,None]).max(2);j,k=np.unravel_index(gaps.argmin(),gaps.shape)
  mutual.append([float(gaps[j,k]),i,arms[0][j][0],arms[1][k][0]])
 result=dict(scope='Exact float32 transported commands: all315 corrected collision meshes per arm at all248 modified ordinary command waypoints; static table/riser/backing/compound stand and conservative parked-cap outer box; mutual AABB separation only. Predicted held-can body+shoulder conservative OBBs checked against all non-hand links; hand/held-can intended contacts excluded, preserved relative pose is checked separately. Held-can poses are source observations+offset proxy, NOT newly native-validated; deformation/dynamics unproved.',minimum_static_gap=mins,negative_static_gaps=bad,minimum_mutual_aabb_gap=min(mutual),waypoints=248,robot_piece_count_per_arm=315)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args();r=run(args.source);args.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
