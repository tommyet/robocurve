"""Same-row native readback grouping; no physics/FK mocked as success."""
import unittest
from types import SimpleNamespace
import numpy as np
from native_capture import read_poststep_snapshot,native_body_world_poses

class Tensor:
 def __init__(self,value,counter):self.value=np.asarray(value);self.counter=counter
 @property
 def shape(self):return self.value.shape
 def reshape(self,*shape):return Tensor(self.value.reshape(*shape),self.counter)
 def detach(self):return self
 def cpu(self):self.counter['copies']+=1;return self
 def numpy(self):return self.value

def fixture(owners,owner_poses):
 count={'copies':0,'articulation_reads':{},'object_reads':{}}
 entities={};objects={}
 for path,o in owners.items():
  if o['kind'] in ('robot','articulation'):
   group=entities.setdefault(o['entity'],{})
   group[o['body_index']]=(o['body_name'],owner_poses[path])
  else:objects[o['entity']]=np.array(owner_poses[path],dtype=float)[None,:]
 scene={}
 class Data:
  def __init__(self,name,value):self.name,self.value=name,value
  @property
  def body_link_pose_w(self):
   name=self.name;count['articulation_reads'][name]=count['articulation_reads'].get(name,0)+1
   return Tensor(self.value,count)
 for name,group in entities.items():
  names,poses=zip(*(group[i]for i in range(len(group))))
  scene[name]=SimpleNamespace(body_names=list(names),data=Data(name,np.array(poses,dtype=float)[None,:]))
 class World:
  def get_pose_w(self,name):
   count['object_reads'][name]=count['object_reads'].get(name,0)+1
   return Tensor(objects[name],count)
 def cat(values,dim):return Tensor(np.concatenate([v.value for v in values],axis=dim),count)
 return scene,World(),cat,count,objects

class SnapshotTests(unittest.TestCase):
 def test_full262_owners_same_native_values_one_copy_no_cross_step_cache(self):
  owners={};poses={}
  for entity,n in [('left_robot',9),('right_robot',9),('hair_model',241)]:
   for j in range(n):
    path=f'/Env/{entity}/body{j}';owners[path]={'entity':entity,'kind':'articulation','body_index':j,'body_name':f'body{j}'}
    poses[path]=[.001*j,0,1,0,0,0,1]
  for name in ('dryer','switch','scalp_collision'):
   owners['/Env/'+name]={'entity':name,'kind':'object'};poses['/Env/'+name]=[0,0,1,0,0,0,1]
  scene,world,cat,count,objects=fixture(owners,poses)
  out=read_poststep_snapshot(scene,owners,world,cat=cat)
  self.assertEqual(out['owner_poses'],poses);self.assertEqual(count['copies'],1)
  self.assertEqual(count['articulation_reads'],{'left_robot':1,'right_robot':1,'hair_model':1})
  self.assertEqual(count['object_reads'],{'dryer':1,'switch':1,'scalp_collision':1})
  objects['dryer'][0,0]=.25
  new=read_poststep_snapshot(scene,owners,world,cat=cat)
  self.assertEqual(new['owner_poses']['/Env/dryer'][0],.25)
  self.assertEqual(out['owner_poses']['/Env/dryer'][0],0.)
 def test_missing_body_order_and_nonfinite_fail_closed(self):
  owners={'/x':{'entity':'hair_model','kind':'articulation','body_index':0,'body_name':'head'}}
  poses={'/x':[0,0,1,0,0,0,1]};scene,world,cat,count,_=fixture(owners,poses)
  scene['hair_model'].body_names=['other']
  with self.assertRaisesRegex(ValueError,'ordering'):read_poststep_snapshot(scene,owners,world,cat=cat)
  scene['hair_model'].body_names=['head'];scene['hair_model'].data.value[0,0,0]=np.nan
  with self.assertRaisesRegex(ValueError,'invalid actual'):read_poststep_snapshot(scene,owners,world,cat=cat)


class DetentHostTimingTests(unittest.TestCase):
 def test_timed_binding_preserves_callback_reads_and_well_targets(self):
  import sys,types
  from unittest.mock import patch
  try:from pxr import Usd,UsdPhysics
  except ImportError:self.skipTest('OpenUSD unavailable')
  from switch_detent import NativeDetentBinding
  from config import SWITCH_DETENT_STIFFNESS,SWITCH_DETENT_DAMPING
  stage=Usd.Stage.CreateInMemory();joint=UsdPhysics.PrismaticJoint.Define(stage,'/dryer/power_slider')
  drive=UsdPhysics.DriveAPI.Apply(joint.GetPrim(),'linear');drive.CreateStiffnessAttr(SWITCH_DETENT_STIFFNESS);drive.CreateDampingAttr(SWITCH_DETENT_DAMPING);drive.CreateTargetPositionAttr(0.)
  sample={'q':0.};calls={'get_transforms':0,'get_velocities':0}
  class View:
   def __init__(self,switch):self.switch=switch
   def get_transforms(self):
    calls['get_transforms']+=1
    return Tensor(np.array([[-.037,0,-.045+sample['q'],0,0,0,1.]])if self.switch else np.array([[0,0,0,0,0,0,1.]]),{'copies':0})
   def get_velocities(self):calls['get_velocities']+=1;return Tensor(np.zeros((1,6)),{'copies':0})
  class Manager:
   def register_callback(self,callback,event,**kw):self.callback=callback;return 1
   def deregister_callback(self,handle):pass
  # Explicit mock backend only checks output instrumentation, not native physics.
  manager=Manager();base=SimpleNamespace(sim=SimpleNamespace(physics_manager=manager,cfg=SimpleNamespace(dt=1/480)),scene={'dryer':SimpleNamespace(root_view=View(False)),'switch':SimpleNamespace(root_view=View(True))})
  class Scene(dict):pass
  scene=Scene(base.scene);scene.stage=stage;base.scene=scene
  module=types.ModuleType('isaaclab_physx.physics.physx_manager');module.IsaacEvents=SimpleNamespace(PRE_PHYSICS_STEP='pre')
  with patch.dict(sys.modules,{'isaaclab_physx.physics.physx_manager':module}):
   binding=NativeDetentBinding(base)
   for q in [0.]*8+[.003]*8+[.001]*8:
    sample['q']=q;manager.callback(1/480)
    self.assertAlmostEqual(drive.GetTargetPositionAttr().Get(),0. if q<.002 else .004,places=8)
   timing=binding.host_timing();self.assertEqual(timing['callback_calls'],24);self.assertEqual(timing['native_sample_calls'],24);self.assertEqual(timing['native_api_copy_calls'],96)
   self.assertEqual(calls,{'get_transforms':48,'get_velocities':48})
   self.assertGreaterEqual(timing['callback_wall_s'],timing['native_api_and_copy_wall_s']);binding.close()

if __name__=='__main__':unittest.main()
