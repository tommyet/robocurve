import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from prepare_contact_replay import pose_velocity


class ContactReplayTests(unittest.TestCase):
    def test_unsmoothed_pose_velocity_is_world_frame_and_rotation_invariant(self):
        rng=np.random.default_rng(110)
        previous=np.column_stack((rng.uniform(-.1,.1,(20,3)),Rotation.random(20,random_state=rng).as_quat()))
        v=rng.normal(size=(20,3))*.1;w=rng.normal(size=(20,3))*.3;dt=.05
        current=np.column_stack((previous[:,:3]+v*dt,
            (Rotation.from_rotvec(w*dt)*Rotation.from_quat(previous[:,3:])).as_quat()))
        np.testing.assert_allclose(pose_velocity(previous,current,dt),np.column_stack((v,w)),atol=2e-14)
        rotation=Rotation.random(random_state=rng);translation=rng.normal(size=3)
        shifted=lambda poses:np.column_stack((rotation.apply(poses[:,:3])+translation,
            (rotation*Rotation.from_quat(poses[:,3:])).as_quat()))
        np.testing.assert_allclose(pose_velocity(shifted(previous),shifted(current),dt),
                                  np.column_stack((rotation.apply(v),rotation.apply(w))),atol=2e-14)

    def test_single_body_and_invalid_interval(self):
        pose=np.array([0.,0.,0.,0.,0.,0.,1.])
        np.testing.assert_array_equal(pose_velocity(pose,pose,.05),np.zeros(6))
        with self.assertRaises(ValueError):pose_velocity(pose,pose,0.)


if __name__=='__main__':unittest.main()
