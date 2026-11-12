import unittest
import numpy as np
from geometry import audit_scene,patch,stitch_loop
from cutting import ThreadCutter,DamageAudit,segment_triangle_intersections
from scoring import assess


class MechanismTests(unittest.TestCase):
    def test_cloth_is_continuous_with_real_holes(self):
        r=audit_scene()
        self.assertEqual([s['boundary_loops'] for s in r['cloth']],[13,13])
        for s in r['stitches']:self.assertGreater(s['minimum_link_m'],.0004)

    def test_needle_path_passes_hole_not_material(self):
        m=patch()
        hole=segment_triangle_intersections([.295,-.030,.74],[.295,-.030,.76],m.rest,m.faces)
        cloth=segment_triangle_intersections([.300,-.030,.74],[.300,-.030,.76],m.rest,m.faces)
        self.assertEqual(len(hole),0)
        self.assertGreater(len(cloth),0)

    def test_proximity_and_wrong_force_direction_cannot_cut(self):
        c=ThreadCutter([28]*6)
        f=np.zeros((168,3))
        for _ in range(100):self.assertEqual(c.update(f,[1,0,0],1/240),[])
        f[0,0]=1.
        for _ in range(100):self.assertEqual(c.update(f,[1,0,0],1/240),[])

    def test_actual_sustained_edge_load_severs_only_contacted_thread(self):
        c=ThreadCutter([28]*6);f=np.zeros((168,3));f[33,0]=-.3
        events=[]
        for _ in range(12):events.extend(c.update(f,[1,0,0],1/240))
        self.assertEqual(events,[33]);self.assertEqual(c.severed,{33})

    def test_interrupted_contact_does_not_accumulate_as_sustained(self):
        c=ThreadCutter([28]*6);f=np.zeros((168,3));f[0,0]=-.3
        for _ in range(30):
            c.update(f,[1,0,0],.02);c.update(np.zeros_like(f),[1,0,0],.001)
        self.assertFalse(c.severed)

    def test_blade_swept_through_cloth_latches_damage(self):
        m=patch();a=DamageAudit()
        self.assertTrue(a.update([[.30,0,.75],[.301,0,.75]],[[.30,0,.76],[.301,0,.76]],
                                 [m.rest],[m.faces],.1))
        self.assertTrue(a.update([[.1,0,.8]],[[.1,0,.81]],[m.rest],[m.faces],.2))

    def test_cut_count_alone_is_not_task_completion(self):
        r=assess(released_stitches=0,minimum_patch_gap_m=0,blade_crossed_fabric=False,
                 maximum_new_tear_m=0,complete=True,thread_bridge_present=True,tools_clear=True)
        self.assertEqual(r['score'],0.)

    def test_intact_separation_and_damage_gate(self):
        kw=dict(released_stitches=6,minimum_patch_gap_m=.03,blade_crossed_fabric=False,
                maximum_new_tear_m=0,complete=True,thread_bridge_present=False,tools_clear=True)
        self.assertEqual(assess(**kw)['score'],1.)
        kw['blade_crossed_fabric']=True
        self.assertEqual(assess(**kw)['score'],0.)

    def test_invalid_judgment_types_fail_closed(self):
        base=dict(released_stitches=6,minimum_patch_gap_m=.03,blade_crossed_fabric=False,
                  maximum_new_tear_m=0,complete=True,thread_bridge_present=False,tools_clear=True)
        for field,value in [('complete','false'),('tools_clear',1),('released_stitches',True),
                            ('minimum_patch_gap_m',None),('maximum_new_tear_m',float('nan'))]:
            data=dict(base);data[field]=value
            self.assertEqual(assess(**data)['score'],0.)


if __name__=='__main__':unittest.main()
