"""Visual-servo equivalent for the scripted demo, using privileged native poses.

Only ordinary arm joint targets are returned. The material model is untouched.
"""
import numpy as np
from scipy.spatial.transform import Rotation
class DemoControl:
 def __init__(self):self.grasp=None
 def action(self,k,wanted,model,hands,current):
  if k<260 or k>440:return wanted
  from yam_arena import ik,station
  if self.grasp is None:
   R=model.orientation('cutter');self.grasp=(R.T@(hands['right']['tcp']-model.p('cutter')),R.T@hands['right']['rotation'])
  # The cap position comes from the intact cigar, so a detached cap is not chased.
  head=model.p('cigar',[0,0,.068]);axis=-model.orientation('cigar')[:,2]
  nominal=Rotation.from_euler('z',-20,degrees=True).as_matrix()@Rotation.from_euler('x',-45,degrees=True).as_matrix()
  turn=Rotation.align_vectors([axis],[nominal[:,2]])[0].as_matrix();R=turn@nominal
  u=np.clip((k-260)/60,0,1);u=u*u*(3-2*u)
  center=head-R[:,2]*(.055*(1-u));point=center+R@self.grasp[0];handR=R@self.grasp[1]
  q,pe,re=ik.solve(point,ik.matrix_to_quat_xyzw(handR),current[7:13],base_pos=station.BASES['right'],iters=60)
  result=wanted.copy();result[7:13]=q
  return result
