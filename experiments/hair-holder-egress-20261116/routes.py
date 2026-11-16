from audit import *
from yam_arena import ik
from yam_arena.constants import TCP_OFFSET
rows=[json.loads(l) for l in (CAP/'trajectory.jsonl').open()];idx=next(i for i,r in enumerate(rows) if r['phase']=='lift_dryer');start=rows[idx-1];first=rows[idx];owners=start['native_owner_poses'];gpose=np.array(next(v for p,v in owners.items() if '/LeftArm/' in p and p.endswith('/gripper')));R=quat_xyzw_to_matrix(gpose[3:]);P=gpose[:3]+R@np.array(TCP_OFFSET);seed=np.array(first['robot_control']['arms'][0]['arm_joints']);hand=worldpieces(start)

def cylinder(center,radius,length):
 count=96;rr=radius/math.cos(math.pi/count);a=np.arange(count)*2*math.pi/count
 vertices=np.array([[center[0]+sign*length/2,center[1]+rr*math.cos(t),center[2]+rr*math.sin(t)] for sign in [-1,1] for t in a]);faces=[]
 for k in range(count):
  j=(k+1)%count;faces += [(k,j,count+j),(k,count+j,count+k),(0,j,k),(count,count+k,count+j)]
 return vertices[np.array(faces)]

def box(center,size):
 v=np.array([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)])*np.array(size)/2+center
 return v[np.array([(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),(2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)])]
import math
dp=np.array(start['dryer_pose']);dR=quat_xyzw_to_matrix(dp[3:]);sp=np.array(start['switch_pose']);sR=quat_xyzw_to_matrix(sp[3:])
tool=[('barrel',cylinder((0,0,0),.029,.09)),('nozzle',cylinder((.065,0,0),.018,.045)),('handle',box((-.019,0,-.065),(.030,.026,.085)))]
tool=[(n,t@dR.T+dp[:3]) for n,t in tool]+[('switch',box((0,0,0),(.006,.013,.014))@sR.T+sp[:3])]

def minimum(pieces,offset):
 best=(10.,None,None)
 for n,t in pieces:
  t=t+offset
  for label,p,size in holders:
   broad=np.maximum(t.min((0,1))-p-size/2,p-size/2-t.max((0,1))).max()
   if broad>best[0] and broad>.002:continue
   g=boxgap(t,p,size)
   if g<best[0]:best=(g,n,label)
 return best
out=[]
for name,waypoints in [('up15_yminus90_up85',[(0,0,0),(0,0,.015),(0,-.09,.015),(0,-.09,.10)]),('up15_xminus90_up85',[(0,0,0),(0,0,.015),(-.09,0,.015),(-.09,0,.10)])]:
 record=[];q=seed.copy()
 for leg,(a,b) in enumerate(zip(waypoints,waypoints[1:])):
  for s in np.linspace(0,1,17):
   offset=np.array(a)+(np.array(b)-a)*s;h=minimum(hand,offset);t=minimum(tool,offset)
   q,pe,re=ik.solve(P+offset,ik.matrix_to_quat_xyzw(R),q,base_pos=(0,.305,.75),iters=220,tol=1e-6)
   record.append({'leg':leg,'fraction':float(s),'offset':offset.tolist(),'hand_gap_m':h[0],'hand_pair':h[1:],'tool_gap_m':t[0],'tool_pair':t[1:],'IK_position_error_m':pe,'IK_rotation_error_rad':re})
 result={'name':name,'physical_start_native_time_s':start['time'],'hand_min':min(record,key=lambda x:x['hand_gap_m']),'tool_min':min(record,key=lambda x:x['tool_gap_m']),'max_IK_error_m':max(x['IK_position_error_m'] for x in record),'max_IK_rotation_rad':max(x['IK_rotation_error_rad'] for x in record),'rows':record};out.append(result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)
Path('/private/tmp/hair-holder-egress-cpu/routes.json').write_text(json.dumps({'scope':'Nominal translated achieved physical grasp at fixed achieved R; signed SAT; cylinder is conservative96-sided circumscribed bound. NO native validation/full arm clearance/swept dynamics proof.','start_tcp':P.tolist(),'start_R':R.tolist(),'routes':out},indent=2)+'\n')
