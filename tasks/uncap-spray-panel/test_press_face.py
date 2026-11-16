"""Check the tool frame against an actual independent collision-mesh triangle."""
import json
from pathlib import Path
import unittest


class ContactFrameTests(unittest.TestCase):
    def test_real_collision_face_is_horizontal_in_press_pose(self):
        face=json.loads(Path(__file__).with_name('press_face.json').read_text())
        r=face['rotation_can_from_tcp'];p=face['point_tcp'];tri=face['triangle_tcp']
        self.assertLess(max(abs(sum(v[i] for v in tri)/3-p[i]) for i in range(3)),1e-12)
        rotated=[[sum(row[i]*v[i] for i in range(3)) for row in r] for v in tri]
        self.assertLess(max(v[2] for v in rotated)-min(v[2] for v in rotated),1e-8)

    def test_frame_is_a_rigid_rotation(self):
        r=json.loads(Path(__file__).with_name('press_face.json').read_text())['rotation_can_from_tcp']
        for i in range(3):
            for j in range(3):self.assertAlmostEqual(sum(r[i][k]*r[j][k] for k in range(3)),float(i==j),places=10)

if __name__=='__main__':unittest.main()
