"""Replay only three EXISTING failed nodes, conditional SOUTH185, no search."""
import sys,json,hashlib,itertools,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import numpy as np
from planner import Planner,READY
from geometry import BASES
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import axis_angle_matrix
from scene import layout
from config import TOP
P=Planner();prior=json.loads((Path(__file__).parent/'planner-report.json').read_text());parent=prior['best_prefix'][-1];P.left=P.model.parts('left',READY,[FINGER_OPEN]*2);P.model.contact_cache={float(k):v for k,v in prior['contact_heading_certificates'].items()}if isinstance(prior['contact_heading_certificates'],dict)else{};h=next(v for v in layout()[1]if v['b']=='south_bottom');a=P.row['angles_deg']['south_bottom_hinge'];fp,fr,sz=P.rotated['south_bottom'];wr=P.rotated['south'][1];pivot=fp+fr@h['anchor_b'];newR=axis_angle_matrix(wr[:,0],np.radians(185-a))@fr;newP=pivot-newR@h['anchor_b'];conditional=dict(P.rotated);conditional['south_bottom']=(newP,newR,sz);corn=np.array(list(itertools.product([-1.,1.],repeat=3)));vertices=newP+(corn*np.array(sz)/2)@newR.T;checks=[]
for heading in [30,35,40]:
 tcp,R,patch,original=P.state(-40,heading);altered=dict(original);altered['south_bottom']=(newP,newR,sz);contact=P.model.contact(heading,P.size);opening=contact.get('common_opening_m');result=dict(angle_deg=-40,heading_deg=heading,contact_valid=contact['valid'],original_cheap=P.model.cheap_hand(tcp,R,original),conditional_cheap=P.model.cheap_hand(tcp,R,altered))
 if contact['valid']:
  q,pe,re=ik.solve(tcp,ik.matrix_to_quat_xyzw(R),np.array(parent['q']),base_pos=BASES['right'],iters=500,tol=1e-6);result.update(q=q.tolist(),pe_m=pe,re_rad=re)
  if pe<2e-6 and re<.002:
   result['original_full']=P.model.guard('right',q,[-opening]*2,original,P.left,intended=True);result['conditional_full']=P.model.guard('right',q,[-opening]*2,altered,P.left,intended=True)
 checks.append(result);print(heading,result.get('pe_m'),result['conditional_cheap'],result.get('conditional_full'),flush=True)
# Box-only collisions of the hypothetically moved flap are explicit, not erased.
_,_,_,obs=P.state(-40,35);obs['south_bottom']=(newP,newR,sz);panel=[]
for name,(p,r,size)in obs.items():
 if name in ['south_bottom','south']or name.startswith('cutter'):continue
 axes=np.concatenate([newR.T,r.T,np.cross(newR.T[:,None,:],r.T[None,:,:]).reshape(-1,3)]);n=np.linalg.norm(axes,axis=1);axes=axes[n>1e-10]/n[n>1e-10,None];gap=float(np.max(abs(axes@(p-newP))-abs(axes@newR)@(np.array(sz)/2)-abs(axes@r)@(np.array(size)/2)));panel.append(dict(other=name,gap_m=gap))
out=dict(scope='Threealreadyfailed−40nodes headings30/35/40 replayedfrombest−45prefix, identicalIKseed/contact/otherarm. ConditionalSOUTHbottom185 is NOT controllerachievement and mayneedbodyreposition; no newbeam/grid. Allotherpanelsfixedactualrotated011.',original_report_sha256=hashlib.sha256((Path(__file__).parent/'planner-report.json').read_bytes()).hexdigest(),conditional_south={'from_angle_deg':a,'to_angle_deg':185,'position':newP.tolist(),'rotation':newR.tolist(),'lowest_vertex_z_m':float(vertices[:,2].min()),'table_penetration_m':max(0.,TOP-float(vertices[:,2].min())),'panel_pair_checks':panel},replayed_nodes=checks,conclusion='Seeexactfullguardresults; aconditionalclear-node provesonlydependency, notopeningorderfeasibility orwholearc.',native_authorized=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());path=Path(__file__).parent/'dependency-review185.json';path.write_text(json.dumps(out,indent=2)+'\n');print('saved',path,'south minZ',vertices[:,2].min(),'panelpenetrations',[x for x in panel if x['gap_m']<-1e-5])
