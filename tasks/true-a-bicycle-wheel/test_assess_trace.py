import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from assess_trace import rim_geometry
from mechanics import WheelSpec
from wheel_scene import x_frame,wheel_world_frame


class RimMeasurementTests(unittest.TestCase):
    def setup_ring(self):
        spec=WheelSpec();a=np.arange(32)*2*np.pi/32
        vertices=np.c_[spec.rim_radius_m*np.cos(a),spec.rim_radius_m*np.sin(a),np.zeros(32)]
        hub=np.array((.35,0.,1.005));W=wheel_world_frame(.7);poses=[]
        for i in range(32):
            p=(vertices[i]+vertices[(i+1)%32])/2
            R=W@x_frame(vertices[(i+1)%32]-vertices[i])
            poses.append(np.r_[hub+W@p,Rotation.from_matrix(R).as_quat()])
        return np.array(poses),hub

    def test_exact_ring_is_true_except_known_chord_error(self):
        poses,hub=self.setup_ring();r=rim_geometry(poses,hub)
        self.assertLess(r['lateral_runout_m'],1e-12)
        self.assertLess(r['dish_offset_m'],1e-12)
        self.assertAlmostEqual(r['radial_runout_upper_bound_m'],r['radial_chord_error_bound_m'],12)

    def test_lateral_damage_and_dish_do_not_disappear_under_average(self):
        poses,hub=self.setup_ring();poses[0,0]+=.002
        self.assertAlmostEqual(rim_geometry(poses,hub)['lateral_runout_m'],.002,12)
        poses,hub=self.setup_ring();poses[:,0]+=.001
        self.assertAlmostEqual(rim_geometry(poses,hub)['dish_offset_m'],.001,12)


if __name__=='__main__':unittest.main()
