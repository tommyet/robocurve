import math
import unittest
from scene import layout,rotate_z,rotate_x,add


class GeometryTests(unittest.TestCase):
    def test_inventory_is_four_walls_and_eight_flaps(self):
        parts,joints=layout()
        self.assertEqual(len(parts),12);self.assertEqual(len(joints),12)
        self.assertEqual(sum(h['sealed'] for h in joints),2)
        self.assertEqual(len({p['name'] for p in parts}),12)

    def test_hinge_anchors_coincide_in_initial_configuration(self):
        parts,joints=layout();lookup={p['name']:p for p in parts}
        def transform(p,v):
            w,x,y,z=p['quat']
            # Unit quaternion vector rotation.
            cross=(y*v[2]-z*v[1],z*v[0]-x*v[2],x*v[1]-y*v[0])
            second=(y*cross[2]-z*cross[1],z*cross[0]-x*cross[2],x*cross[1]-y*cross[0])
            return tuple(a+b+2*w*c+2*d for a,b,c,d in zip(p['pos'],v,cross,second))
        for h in joints:
            a=transform(lookup[h['a']],h['anchor_a']);b=transform(lookup[h['b']],h['anchor_b'])
            self.assertLess(math.dist(a,b),1e-9,h['name'])

if __name__=='__main__':unittest.main()
