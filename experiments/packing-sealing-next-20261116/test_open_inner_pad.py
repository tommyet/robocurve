"""Actual finite inner-pad geometry; oppositefinger is never collision-masked."""
import json,unittest
from pathlib import Path
import numpy as np
from screen_open_straddle_push import OpenStraddleSearch,ik,BASES,READY
from screen_distal_face_push import clip
from config import BOARD
P=Path(__file__).parent
class InnerPadTests(unittest.TestCase):
 def test_physical_opening_witness_and_opposite_finger_clearance(self):
  s=OpenStraddleSearch();tcp,R,w=s.point('east',-175.,.075,90.,-.073,roll=180.);fp,fr=s.pose('east',-175.)
  self.assertEqual(w['selected_inner_pad'],'tip_left');self.assertEqual(w['physical_jaw_opening_m'],.020);self.assertGreater(w['largest_single_real_triangle_contact_patch_area_m2'],1e-6);self.assertGreater(w['patch_outward_normal_alignment'],.95)
  other=np.concatenate([poly for n,poly in s.distal if n=='tip_right']);local=(other@R.T+tcp-fp)@fr
  self.assertLess(local[:,2].max(),-BOARD/2-.015)
 def test_all_four_recorded_push_routes_keep_all315_pieces_and_real_patch(self):
  routes=[]
  for source in('face-push-gravity-release.json','face-push-rocked-gravity-release.json'):
   routes.extend(r for r in json.loads((P/source).read_text())['results']if r.get('success')and r['withdrawal']['safe'])
  self.assertEqual({r['flap']for r in routes},{'east','west','north','south'})
  for r in routes:
   s=OpenStraddleSearch();s.rock_deg=r.get('rock_deg',0.);self.assertEqual(len(s.g.raw),315)
   for angle in(-175.,-160.,-90.,-70.):
    tcp,R,w=s.point(r['flap'],angle,r['radius_m'],r['approach_yaw_deg'],r['lateral_offset_m'],roll=r['polarity']);self.assertGreaterEqual(w['support_face_edge_margin_m'],.002-1e-12);self.assertGreaterEqual(w['largest_single_real_triangle_contact_patch_area_m2'],1e-6);self.assertGreater(w['patch_outward_normal_alignment'],.95)
 def test_distal_clip_preserves_positive_real_triangle_area(self):
  triangle=np.array([[0,0,-.02],[1,0,0],[0,1,0]],float);p=clip(triangle,2,-.015,True)
  self.assertEqual(p.shape,(4,3));self.assertTrue(np.all(p[:,2]>=-.015-1e-12));self.assertGreater(abs(np.cross(p[1]-p[0],p[2]-p[0])[2]),0)
if __name__=='__main__':unittest.main()
