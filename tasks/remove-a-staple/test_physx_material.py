"""Check native-precision caching preserves the full plastic target history."""
import math
import struct
import unittest
import numpy as np
from materials import PlasticHinge,SteelSpec
from physx_material import PhysxPlasticHinge


class Attribute:
    def __init__(self):self.values=[]
    def Set(self,value):self.values.append(value)


class NativeTargetTests(unittest.TestCase):
    def test_cache_matches_uncached_float32_targets_and_material_history(self):
        spec=SteelSpec();actual=PhysxPlasticHinge.__new__(PhysxPlasticHinge)
        actual.hinge=PlasticHinge(spec);actual.target_position=Attribute();actual._native_target=0.
        reference=PlasticHinge(spec);expected=[];last=0.
        for angle in np.r_[np.zeros(100),np.linspace(0.,1.2,100),np.linspace(1.2,0.,100),np.zeros(100)]:
            result=actual.update_from_measured_angle(float(angle));control=reference.advance(float(angle))
            self.assertEqual(result,control)
            target=struct.unpack('f',struct.pack('f',math.degrees(reference.plastic_angle_rad)))[0]
            if target!=last:expected.append(target);last=target
            self.assertEqual(actual._native_target,target)
        self.assertEqual(actual.target_position.values,expected)
        self.assertLessEqual(len(expected),200)
        self.assertGreater(len(expected),0)
        actual.reset()
        self.assertEqual(actual._native_target,0.)
        self.assertEqual(actual.target_position.values[-1],0.)
        self.assertEqual(actual.hinge.plastic_angle_rad,0.)


if __name__=='__main__':unittest.main()
