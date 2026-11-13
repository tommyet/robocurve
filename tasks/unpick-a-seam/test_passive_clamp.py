import unittest
import numpy as np
from geometry import patch
from clamp_layout import transform
from passive_clamp import fixture_boxes,PARAMETERS,FRONT_FACE,MOVING_NAME,MOVING_POSITION,MOVING_SIZE


class PassiveClampGeometry(unittest.TestCase):
    def test_cloth_starts_tangent_on_fixed_side_and_clear_on_moving_side(self):
        upper=transform(patch(True,hole_half=.0008).rest)
        self.assertAlmostEqual(float(upper[0,0]-.0002),FRONT_FACE,places=12)
        moving_face=MOVING_POSITION[0]-MOVING_SIZE[0]/2
        self.assertGreater(moving_face-(upper[0,0]+.0002),.000199999)

    def test_full_permitted_jaw_sweep_is_clear_of_frame(self):
        size=np.array(MOVING_SIZE);center=np.array(MOVING_POSITION)
        low=center-size/2;high=center+size/2
        low[0]-=PARAMETERS.initial_gap_m;high[0]+=PARAMETERS.opening_travel_m
        for name,other_size,position in fixture_boxes():
            if name==MOVING_NAME:continue
            lo=np.array(position)-np.array(other_size)/2
            hi=np.array(position)+np.array(other_size)/2
            self.assertFalse(np.all(np.minimum(high,hi)-np.maximum(low,lo)>1e-12),name)

    def test_nominal_force_is_bounded_and_can_support_cutting_load(self):
        # A seated jaw leaves the full 0.4 mm collision thickness, instead of
        # imposing the old 0.3 mm incompatible fixed gap.
        normal=PARAMETERS.stiffness_n_m*.0004
        self.assertLess(normal,PARAMETERS.force_limit_n)
        swatch_weight=2*patch(True,hole_half=.0008).audit()['surface_area_m2']*.0004*350*9.81
        self.assertGreater(2*.8*normal,.25+swatch_weight)
        critical=2*np.sqrt(PARAMETERS.mass_kg*PARAMETERS.stiffness_n_m)
        self.assertGreaterEqual(PARAMETERS.damping_n_s_m,critical)


if __name__=='__main__':unittest.main()
