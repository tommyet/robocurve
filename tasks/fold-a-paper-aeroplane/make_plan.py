"""Offline trajectory prototype using predicted material states.

Exported trajectories contain ordinary joint targets only. No successful
complete aeroplane has been demonstrated by this generator.
"""
from pathlib import Path
import numpy as np,json,sys,pickle,hashlib,argparse
from planner import Plan
from common import down,TABLE

if __name__=='__main__':
 from model import Model
 from yam_arena import ik,station
 class PredictedPlan(Plan):
  def __init__(self):super().__init__();self.predicted=Model()
  def add(self,*args,**kwargs):
   start=len(self.frames);before=self.predicted.paper.max_strain;super().add(*args,**kwargs)
   for row in self.frames[start:]:
    q=np.asarray(row['action14']);hands={}
    for side,o in [('left',0),('right',7)]:
     point,R=ik.tcp_pose(q[o:o+6],station.BASES[side]);hands[side]=dict(tcp=point,rotation=R,opening=q[o+6])
    self.predicted.update(hands)
   if self.predicted.paper.max_strain>before+.02:print('Strain diagnostic',args[1],self.predicted.paper.max_strain,flush=True)
   return self
 p=PredictedPlan();D=down(-90);z=TABLE+.0003
 paper_source_hash=hashlib.sha256(Path(__file__).with_name("paper.py").read_bytes()).hexdigest()
 parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
 parser.add_argument('--resume',type=Path);parser.add_argument('--nose-only',action='store_true')
 args=parser.parse_args();output=args.output
 resumed=False
 if args.resume:
  with args.resume.open('rb') as f:data=pickle.load(f)
  assert data['paper_sha256']==paper_source_hash,'Material changed; regenerate the prefix.'
  assert str(args.resume).endswith('.nose2.pkl'),'Only a complete two-corner prefix may be resumed.'
  assert data['solver_sha256']==hashlib.sha256(Path(__file__).with_name('paper_solver.py').read_bytes()).hexdigest(),'Solver changed; regenerate the prefix.'
  p.frames=data['frames'];p.a=data['a'];p.audit=data['audit'];p.predicted=data['predicted'];resumed=True
 def checkpoint(label):
  data=dict(frames=p.frames,a=p.a,audit=p.audit,predicted=p.predicted,paper_sha256=paper_source_hash,solver_sha256=hashlib.sha256(Path(__file__).with_name("paper_solver.py").read_bytes()).hexdigest())
  with output.with_suffix('.'+label+'.pkl').open('wb') as f:pickle.dump(data,f)

 def vertex(i,j):return p.predicted.paper.p[i*23+j].copy()
 def target(point,opening=.08,press=False):return (np.asarray(point)+[0,0,.0132 if press else .0115],D,opening)
 def move(side,point,opening=.08,t=1.,label='move',mode='cartesian',press=False):p.add(t,label,{side:target(point,opening,press)},mode)
 def fold(side,corner,pivot,axis,counter,crease_end,label):
  global D
  other='right' if side=='left' else 'left';corner=np.asarray(corner);pivot=np.asarray(pivot);axis=np.asarray(axis,float);axis/=np.linalg.norm(axis);counter=np.asarray(counter)
  angle=np.degrees(np.arctan2(axis[0],-axis[1]));D=down(angle%180-180)
  move(side,corner+[0,0,.08],.8,3.,label+' approach',mode='joint')
  move(other,counter+[0,0,.08],.8,3.,label+' counterhold approach',mode='joint')
  move(side,corner,.8,1.5,label+' lower to corner')
  move(other,counter,.8,1.5,label+' lower counterhold')
  p.add(1.,label+' pinch',{side:target(corner),other:target(counter)})
  v=corner-pivot
  for a in np.linspace(0,np.pi,21)[1:]:
   q=pivot+v*np.cos(a)+np.cross(axis,v)*np.sin(a)+axis*np.dot(axis,v)*(1-np.cos(a))
   q[2]+=.001*a/np.pi
   move(side,q,t=.4,label=label+' turn flap')
  move(other,counter,.8,.5,label+' release counterhold')
  move(other,counter+[0,0,.08],.8,1.,label+' lift pressing hand')
  move(other,pivot+[0,0,.06],.08,2.,label+' prepare pressing fingers')
  move(other,pivot,.08,1.,label+' contact crease',press=True)
  move(other,crease_end,.08,6.,label+' press crease',press=True)
  move(other,np.asarray(crease_end)+[0,0,.08],.08,1.,label+' lift pressing hand')
  move(side,q,.8,.5,label+' release flap')
  move(side,q+[0,0,.08],.8,1.,label+' clear flap')
  p.add(1.,label+' settle',{})
 def centre_pair():
  global D
  D=down(-90)
  corners={'left':vertex(4,22),'right':vertex(17,0)}
  pivot=vertex(0,11);axis=vertex(30,11)-pivot;axis/=np.linalg.norm(axis)
  p.add(3.,'centre approach with both hands',{side:target(q+[0,0,.08],.8) for side,q in corners.items()},'joint')
  p.add(2.,'centre lower both hands',{side:target(q,.8) for side,q in corners.items()})
  p.add(1.,'centre pinch both ends of the edge',{side:target(q) for side,q in corners.items()})
  for angle in np.linspace(0,np.radians(80),31)[1:]:
   goals={}
   for side,corner in corners.items():
    v=corner-pivot;a=angle if side=='left' else -angle
    q=pivot+v*np.cos(a)+np.cross(axis,v)*np.sin(a)+axis*np.dot(axis,v)*(1-np.cos(a))
    goals[side]=target(q)
   p.add(.4,'centre turn entire edge',goals)
  p.add(1.,'centre hold the closed fold',{})
  checkpoint('centre-held')
  p.add(.5,'centre release both hands',{side:(q[0],q[1],.8) for side,q in goals.items()})
  p.add(1.,'centre clear both hands',{side:(q[0]+[0,0,.08],q[1],.8) for side,q in goals.items()})
  p.add(1.,'centre settle',{})
 if not resumed:
  fold('left',vertex(30,22),vertex(30,11),[1,-1,0],vertex(18,9),vertex(19,22),'first nose fold')
  print('First fold',p.predicted.measure(),flush=True);checkpoint('nose1')
  fold('right',vertex(30,0),vertex(30,11),vertex(19,0)-vertex(30,11),vertex(10,16),vertex(19,0),'second nose fold')
  print('Second fold',p.predicted.measure(),flush=True);checkpoint('nose2')
 if not args.nose_only:
  centre_pair()
  print('Centre fold',p.predicted.measure(),flush=True);checkpoint('centre')
 np.savez_compressed(output.with_suffix('.npz'),**p.predicted.state())
 result=p.save(output)
 saved=json.loads(output.read_text());saved.update(development_only=True,complete_plane=False,predicted_measurements=p.predicted.measure());output.write_text(json.dumps(saved,separators=(',',':'))+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!="audit"}))
