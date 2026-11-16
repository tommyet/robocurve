"""Ordinary open-jaw inner-pad targets; no object-state or physics writes."""
import numpy as np
from yam_arena import ik
from yam_arena.constants import READY,SHOULDER,WRIST
from closure_geometry import rx
from config import BOARD

# E/W acquisition, pushpastvertical, movingflap exit, gravity andpark have CPU
# full315 certificates. N/S use reviewed above-box standoff and 2mm relieved insertion.
ROUTES={
 'east':dict(side='left',radius=.075,offset=-.073,yaw=90.,polarity=180.,rock=0.,hover=.025,high=.060,enabled=True,seed=[-0.10443747268800183, 2.5329217908590147, 1.651480825431047, 0.8814431278444186, 1.466361720774014, -1.4835329659372343]),
 'west':dict(side='right',radius=.075,offset=-.073,yaw=90.,polarity=180.,rock=3.,hover=.040,high=.060,enabled=True,seed=[0.4336194244940853, 1.6333445250925618, 0.026915266569081293, 1.4820795801084745, -1.13878519229623, -1.5964355185372279]),
 'north':dict(side='left',radius=.075,offset=-.087,yaw=90.,polarity=180.,rock=3.,hover=.040,high=.060,enabled=True,seed=[-1.144290754222204, 1.606668150917362, 0.0491041054539689, 1.4312491453394678, -1.1458296228296654, -1.5985976822414143]),
 'south':dict(side='right',radius=.075,offset=.087,yaw=270.,polarity=0.,rock=-3.,hover=.040,high=.060,enabled=True,seed=[1.1442881390356, 1.6066601531896676, 0.04913650357459782, 1.4311878557925557, 1.1458537710279806, 1.5986243285393253])}
for _name in('east','west'):ROUTES[_name].update(relief=0.,standoff=None)
for _name in('north','south'):ROUTES[_name].update(relief=.002,standoff=[.35,.22 if ROUTES[_name]['side']=='left'else-.22,1.0675])
FINGER=-.010
OPENING=FINGER/-.04695
NORMAL_PRELOAD=.00065
LOOKAHEAD_DEG=.1
RELEASE_ANGLE=-70.

def clip(poly,axis,bound,greater):
 if not len(poly):return np.empty((0,3))
 out=[];a=poly[-1];va=(a[axis]-bound)*(1 if greater else -1)
 for b in poly:
  vb=(b[axis]-bound)*(1 if greater else -1)
  if(va>=0)!=(vb>=0):out.append(a+(b-a)*va/(va-vb))
  if vb>=0:out.append(b)
  a,va=b,vb
 return np.asarray(out).reshape(-1,3)

class FaceTargets:
 def __init__(self,geometry,parts,hinges,pose):
  self.geometry=geometry;self.parts=parts;self.hinges=hinges;self.pose=pose;self.pads={}
  p,R=ik.tcp_pose(READY,[0,.305,.75])
  for name,triangles in geometry.pieces('left',READY,[FINGER]*2):
   if name not in('tip_left','tip_right'):continue
   for triangle in(triangles-p)@R:
    polygon=clip(triangle,2,-.015,True)
    if len(polygon):self.pads.setdefault(name,[]).append(polygon)
 def flap_pose(self,name,angle):
  wp,wr=self.pose(name);h=self.hinges[name];fr=wr@rx(angle);hp=wp+wr@np.asarray(h['anchor_a']);return hp-fr@np.asarray(h['anchor_b']),fr
 def target(self,name,angle,preload=0.):
  if not 0<=preload<=NORMAL_PRELOAD:raise ValueError('normal preload outside reviewed bound')
  d=ROUTES[name];fp,fr=self.flap_pose(name,angle);z=fr[:,0]if d['yaw']==90 else-fr[:,0];x=fr[:,2]*(1 if d['polarity']==0 else-1);y=np.cross(z,x);hand=np.column_stack((x,y,z));a=np.radians(d['rock']*np.cos(np.radians(angle)));c,s=np.cos(a),np.sin(a);hand=hand@np.array([[c,0,s],[0,1,0],[-s,0,c]]);push=-fr[:,2];body='tip_right'if d['polarity']==0 else'tip_left';polys=self.pads[body];maximum=max(float((p@hand.T@push).max())for p in polys);support=np.concatenate([p[(p@hand.T@push)>=maximum-1e-7]for p in polys]);witness=support.mean(0);local=np.array([d['offset'],self.hinges[name]['anchor_b'][1]-d['radius'],BOARD/2]);surface=fp+fr@local;tcp=surface-hand@witness;points=(support@hand.T+tcp-fp)@fr;size=np.asarray(self.parts[name+'_top']['size']);margin=float(np.min(size[:2]/2-abs(points[:,:2])));area=0.;alignment=0.
  for poly in polys:
   if len(poly)<3:continue
   normal=np.cross(poly[1]-poly[0],poly[2]-poly[0]);length=np.linalg.norm(normal)
   if length<1e-12:continue
   agree=float(hand@(normal/length)@push)
   if agree<.25:continue
   clipped=(poly@hand.T+tcp-fp)@fr
   for axis,bound,greater in[(0,-size[0]/2+.002,True),(0,size[0]/2-.002,False),(1,-size[1]/2+.002,True),(1,size[1]/2-.002,False),(2,BOARD/2-.0002,True),(2,BOARD/2+.0002,False)]:clipped=clip(clipped,axis,bound,greater)
   if len(clipped)>=3:
    xy=clipped[:,:2];value=abs(float(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1))/2))
    if value>area:area=value;alignment=agree
  if margin<.002-1e-10 or area<1e-6:raise ValueError('finite inner-pad face witness unavailable')
  return tcp+push*preload,hand,dict(body=body,side=d['side'],push_world=push.tolist(),face_normal_world=fr[:,2].tolist(),support_tcp=witness.tolist(),edge_margin_m=margin,largest_real_triangle_contact_patch_m2=area,normal_alignment=alignment,preload_m=preload,contact_is_geometric_only=True)
 def measured_gap(self,name,side,q,fingers,body):
  """Actual selected distal pad versus finite measured face, not force estimate."""
  fp,fr=self.pose(name+'_top');size=np.asarray(self.parts[name+'_top']['size']);gap=10.
  for n,triangles in self.geometry.pieces(side,q,fingers):
   if n!=body:continue
   for tri in triangles:
    poly=(tri-fp)@fr
    for axis,bound,greater in[(0,-size[0]/2+.002,True),(0,size[0]/2-.002,False),(1,-size[1]/2+.002,True),(1,size[1]/2-.002,False)]:poly=clip(poly,axis,bound,greater)
    if len(poly):gap=min(gap,float(poly[:,2].min()-BOARD/2))
  return gap

 def normal_reference(self,name,angle,q,base,witness,signed_force):
  """Linearizedactuator planning, NOT calibratedforce/effortproof.

  Requiredtorque includes authored degree-basedhingedamping/spring andactual
  gravitylever. J uses metre/radian; actuatorKP are Nm/radian. No gainwrites.
  """
  q=np.asarray(q,float);p,R=ik.tcp_pose(q,base);offset=np.asarray(witness['support_tcp']);point=p+R@offset;push=np.asarray(witness['push_world']);J=np.empty((3,6))
  for j in range(6):
   perturbed=q.copy();perturbed[j]+=1e-6;pp,rr=ik.tcp_pose(perturbed,base);J[:,j]=(pp+rr@offset-point)/1e-6
  K=np.array([SHOULDER['stiffness']]*3+[WRIST['stiffness']]*3);compliance=float(np.sum((push@J)**2/K))
  if not np.isfinite(compliance)or not .0001<compliance<.05:raise ValueError('invalid normalactuatorcompliance')
  wp,wr=self.pose(name);fp,fr=self.pose(name+'_top');h=self.hinges[name];hinge=wp+wr@np.asarray(h['anchor_a']);axis=wr[:,0];mass=self.parts[name+'_top']['mass'];gravity=float(np.cross(fp-hinge,[0,0,-mass*9.81])@axis);spring=float(h['spring']*(h['target']-angle));lever=float(np.cross(point-hinge,push)@axis)
  if not .02<lever<.15:raise ValueError('unusable selectedpad hingelever')
  required=max(0.,(.001*5.-gravity-spring)/lever);requested=float(np.clip(required+.1*(required-signed_force),0.,.2));depth=min(NORMAL_PRELOAD,compliance*requested)
  return dict(normal_compliance_m_per_N=compliance,gravity_torque_Nm=gravity,spring_torque_Nm=spring,contact_lever_m=lever,reference_speed_deg_s=5.,required_normal_force_N=required,requested_normal_force_N=requested,total_normal_depth_reference_m=depth,force_reference_is_model_not_calibration=True)
