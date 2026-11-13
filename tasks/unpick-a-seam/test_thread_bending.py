import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from geometry import stitch_loop
from thread_bending import ThreadBending,planar_frames,circular_loop,elastic_diagnostics


class PassiveThreadTests(unittest.TestCase):
    def setUp(self):
        self.nodes=stitch_loop(0.,clear_capsules=True)
        self.lengths=np.linalg.norm(np.roll(self.nodes,-1,axis=0)-self.nodes,axis=1)

    def test_same_lengths_in_cyclic_control_and_physical_frames(self):
        nodes=circular_loop(self.lengths)
        direction=np.roll(nodes,-1,axis=0)-nodes
        np.testing.assert_allclose(np.linalg.norm(direction,axis=1),self.lengths,rtol=0,atol=1e-13)
        r=Rotation.from_quat(planar_frames(nodes)).as_matrix()
        np.testing.assert_allclose(r[:,:,0],direction/self.lengths[:,None],atol=1e-12)
        np.testing.assert_allclose(np.linalg.det(r),1.,atol=1e-12)
        np.testing.assert_allclose(r[:,:,2],np.tile(r[0,:,2],(len(r),1)),atol=1e-12)

    def test_flexural_energy_scales_with_dual_length(self):
        b=ThreadBending();k,c=b.gains(self.lengths,.0004,1400.)
        np.testing.assert_allclose(k*(self.lengths+np.roll(self.lengths,1))/2,b.rigidity_nm2)
        self.assertTrue(np.all(c>0))
        zero=ThreadBending(0.);zk,zc=zero.gains(self.lengths,.0004,1400.)
        np.testing.assert_array_equal(zk,0);np.testing.assert_array_equal(zc,0)
        with self.assertRaises(ValueError):ThreadBending(-1.).gains(self.lengths,.0004,1400.)

    def test_energy_is_rigid_motion_invariant_and_circle_is_lower(self):
        def pose(nodes):return np.column_stack(((nodes+np.roll(nodes,-1,axis=0))/2,planar_frames(nodes)))
        poses=pose(self.nodes);mass=np.ones(24)*1e-6;inertia=np.tile(np.eye(3)*1e-13,(24,1,1))
        velocity=np.tile((1.,2.,3.,0.,0.,0.),(24,1))
        b=ThreadBending().rigidity_nm2
        result=elastic_diagnostics(poses,velocity,mass,inertia,self.lengths,b)
        self.assertLess(result['relative_kinetic_energy_j'],1e-30)
        circle=elastic_diagnostics(pose(circular_loop(self.lengths)),velocity,mass,inertia,self.lengths,b)
        self.assertLess(circle['bending_energy_proxy_j'],result['bending_energy_proxy_j'])
        r=Rotation.from_rotvec((.4,-.7,.1));moved=poses.copy()
        moved[:,:3]=r.apply(poses[:,:3])+(.2,.3,.4)
        moved[:,3:]=(r*Rotation.from_quat(poses[:,3:])).as_quat()
        changed=elastic_diagnostics(moved,velocity,mass,inertia,self.lengths,b)
        self.assertAlmostEqual(changed['bending_energy_proxy_j'],result['bending_energy_proxy_j'],places=15)


if __name__=='__main__':unittest.main()
