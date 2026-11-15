"""Circle appearance partition and fixed layout; no simulator startup."""
import math
import unittest
from config import *
from surface_geometry import circle_cell_parts
from scoring import SprayScorer


def area(poly):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2


class SurfaceGeometryTests(unittest.TestCase):
    def test_every_cell_partition_covers_square_without_changing_dose_grid(self):
        white_area=0.;partial=0
        for _,p,_ in SprayScorer.cells():
            parts=circle_cell_parts(p[1],p[2],CELL*.49,TARGET_CENTER,TARGET_RADIUS)
            self.assertAlmostEqual(sum(area(poly) for poly,_ in parts),(CELL*.98)**2,places=13)
            flags={target for _,target in parts};partial+=len(flags)>1
            for poly,target in parts:
                self.assertGreaterEqual(len(poly),3)
                self.assertTrue(all(math.isfinite(v) for point in poly for v in point))
                if target:
                    white_area+=area(poly)
                    self.assertTrue(all((y-TARGET_CENTER[0])**2+(z-TARGET_CENTER[1])**2<=TARGET_RADIUS**2+1e-14 for y,z in poly))
        self.assertGreater(partial,0);self.assertGreater(white_area,.0047);self.assertLess(white_area,math.pi*TARGET_RADIUS**2)
        self.assertLess(TARGET_RADIUS*(1-math.cos(math.pi/128)),.000013)

    def test_white_target_and_backing_stand_centres_match(self):
        import task
        objects={obj.name:obj for obj in task.OBJECTS}
        self.assertEqual(TARGET_CENTER,(-.035,.9525))
        self.assertAlmostEqual(objects['panel'].pos[0]-.001,TARGET_X)
        self.assertEqual(objects['panel'].pos[1:],TARGET_CENTER)
        self.assertEqual(objects['panel'].size,(.002,.08,.08))
        self.assertEqual(objects['backing'].pos[1:],TARGET_CENTER)
        self.assertEqual(objects['stand'].pos[1],TARGET_CENTER[0])
        self.assertEqual(SPRAY_TRANSIT_CAN,(.26,0.,.9105));self.assertEqual(SPRAY_HELD_CAN,(.26,-.035,.8755))


if __name__=='__main__':unittest.main()
