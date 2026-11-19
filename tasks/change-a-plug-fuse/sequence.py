"""Robot motions after levering; no changes to object state."""
import numpy as np
from scipy.spatial.transform import Rotation as Rot
from geometry import PLUG,PLUG_ROT,CARRIER_OFFSET,FC,TOOL,SPARE,CATCH_TRAY,CARRIER_RESET
from common import TABLE,down
DISH=np.array([.29,-.16,TABLE+.010])
PHASES=[]
def add(n,label,obj,kind,grip,*,point=(0,0,0),delta=(0,0,0),position=None,rotation=None,relative=None):
 PHASES.append(dict(n=n,label=label,obj=obj,kind=kind,grip=grip,point=np.array(point),delta=np.array(delta),position=None if position is None else np.array(position),rotation=rotation,relative=relative))
Rplug=PLUG_ROT.as_matrix();Rcover=Rplug@down(90);Rfuse=Rplug@down(90)
add(40,'withdraw screwdriver','screwdriver','move',0,position=TOOL+[0,0,.10],rotation=np.eye(3))
add(40,'park screwdriver','screwdriver','move',0,position=TOOL,rotation=np.eye(3))
add(20,'release screwdriver','screwdriver','release',.55)
add(40,'clear tool rest','screwdriver','withdraw',.55,delta=[0,0,.09])
add(60,'approach old fuse','old_fuse','pick',.134,point=[0,0,-.003],delta=[0,0,.04],rotation=Rfuse)
add(20,'settle above the cartridge','old_fuse','pick',.134,point=[0,0,-.003],delta=[0,0,.04],rotation=Rfuse)
add(80,'place tips around cartridge','old_fuse','pick',.134,point=[0,0,-.003],rotation=Rfuse)
add(30,'grip old fuse','old_fuse','pick',.10,point=[0,0,-.003],rotation=Rfuse)
add(60,'pull old fuse out of clips','old_fuse','lift',.10,delta=[0,0,.04])
add(60,'carry old fuse to dish','old_fuse','move',.10,position=DISH+[-.025,0,.06])
add(40,'lower old fuse into dish','old_fuse','move',.10,position=DISH+[-.025,0,.015])
add(20,'release old fuse','old_fuse','release',.55)
add(60,'clear the removed fuse','old_fuse','withdraw',.55,delta=[0,0,.09])
add(60,'approach the matching spare','spare_fuse','pick',.35,point=[0,0,.009],delta=[0,0,.05],rotation=down(-90))
add(40,'place tips around the spare','spare_fuse','pick',.25,point=[0,0,.009],rotation=down(-90))
add(30,'grip the replacement fuse','spare_fuse','pick',.10,point=[0,0,.009],rotation=down(-90))
add(60,'lift the spare','spare_fuse','lift',.10,delta=[0,0,.07])
add(80,'align the replacement over both clips','spare_fuse','move',.10,position=FC+[0,0,.035],rotation=Rot.from_euler('z',180,degrees=True).as_matrix(),relative='plug')
add(80,'press the replacement into its clips','spare_fuse','move',.10,position=FC,rotation=Rot.from_euler('z',180,degrees=True).as_matrix(),relative='plug')
add(20,'release the seated fuse','spare_fuse','release',.4)
add(40,'withdraw above the replacement','spare_fuse','withdraw',.4,delta=[0,0,.03])
add(40,'align closed tips above seated cartridge','spare_fuse','push',.06,position=FC+[0,0,.035],rotation=down(90),relative='plug')
add(60,'push cartridge fully into clips','spare_fuse','push',.06,position=FC+[0,0,.011],rotation=down(90),relative='plug')
add(40,'lift clear of the seated cartridge','spare_fuse','push',.06,position=FC+[0,0,.040],rotation=down(90),relative='plug')
add(60,'approach the removed carrier','carrier','pick',.4,point=[.010,0,.004],delta=[0,0,.04],rotation=Rcover)
add(40,'grasp the carrier for refitting','carrier','pick',.25,point=[.010,0,.004],rotation=Rcover)
add(30,'close on the carrier','carrier','pick',.06,point=[.010,0,.004],rotation=Rcover)
add(40,'lift the carrier from the dish','carrier','lift',.06,delta=[0,0,.035])
add(70,'align the carrier above the plug','carrier','move',.06,position=CARRIER_OFFSET+[0,0,.035],rotation=np.eye(3),relative='plug')
add(80,'press the carrier flush','carrier','move',.06,position=CARRIER_OFFSET,rotation=np.eye(3),relative='plug')
add(20,'release the refitted carrier','carrier','release',.5)
add(30,'clear the carrier before pressing','carrier','withdraw',.5,delta=[0,0,.035])
add(30,'align closed tips above the carrier','carrier','push',.06,position=CARRIER_OFFSET+[0,0,.035],rotation=down(90),relative='plug')
add(80,'press the released carrier into its detents','carrier','push',.06,position=CARRIER_OFFSET+[0,0,.0075],rotation=down(90),relative='plug')
add(50,'withdraw from the carrier','carrier','withdraw',.5,delta=[-.04,-.04,.05])
add(40,'inspect the refitted plug','carrier','hold',.5)

# Opening the carrier is outside this task's disclosed starting setup.
PHASES=PHASES[4:]

def append_plan(p,left_return=None):
 from geometry import Q
 objects={'screwdriver':(TOOL+[0,0,.08],np.eye(3)), 'carrier':(CARRIER_RESET,Rplug), 'old_fuse':(PLUG+[0,-.08,.075]+Rplug@FC,Rplug), 'spare_fuse':(SPARE,np.eye(3))}
 last=None;grasp={}
 for phase in PHASES:
  obj=phase['obj'];pos,Robj=objects[obj];kind=phase['kind']
  if kind=='pick':
   R=phase['rotation'];target=pos+Robj@phase['point']+phase['delta'];grasp[obj]=(R.T@(pos-target),R.T@Robj)
  elif kind=='push':
   R=Rplug@phase['rotation'];target=PLUG+[0,-.08,.075]+Rplug@phase['position']
  elif kind in ['move','lift']:
   tr,rr=grasp.get(obj,(np.zeros(3),down(180).T))
   goal=pos+phase['delta'] if kind=='lift' else phase['position'];goalR=phase['rotation'] if phase['rotation'] is not None else Robj
   if phase['relative']=='plug':goal=PLUG+[0,-.08,.075]+Rplug@goal;goalR=Rplug@goalR
   R=goalR@rr.T;target=goal-R@tr;objects[obj]=(goal,goalR)
  elif kind=='withdraw':target=last[0]+phase['delta'];R=last[1]
  else:target,R=last
  targets={'right':(target,R,phase['grip'])}
  if left_return is not None and phase['label']=='approach the removed carrier':
   targets['left']=(np.asarray(left_return[0])+[0,.10,.02],left_return[1],left_return[2])
  if left_return is not None and phase['label']=='align the carrier above the plug':targets['left']=left_return
  p.add(phase['n']/20,phase['label'],targets);last=(target,R)
