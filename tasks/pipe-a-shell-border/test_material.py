"""Mechanism regressions, including negative controls. No robot trial claims."""
import unittest
import numpy as np
from material import Icing
from scoring import assess
from native import Coupling

DOWN=np.diag((1.,-1.,-1.))


class MaterialTests(unittest.TestCase):
    def model(self):
        return Icing(dx=.002)

    def advance(self,m,q,steps=120,pos=(.235,0.,.8055)):
        for _ in range(steps):
            m.step(1/240,piston_m=q,nozzle_pos=pos,nozzle_rotation=DOWN)

    def test_motion_without_pressure_cannot_paint(self):
        m=self.model()
        for y in np.linspace(-.045,.045,60):
            self.advance(m,0,steps=1,pos=(.235,y,.8055))
        self.assertEqual(m.emitted_m3,0.)
        self.assertEqual(float(m.volume.sum()),0.)

    def test_pressure_produces_real_material_and_reaction(self):
        m=self.model()
        reaction=m.step(1/240,piston_m=.01,nozzle_pos=(.235,0.,.8055),nozzle_rotation=DOWN)
        self.assertGreater(reaction,0.)
        self.assertGreater(m.air_volume.sum(),0.)
        self.advance(m,.01)
        self.assertGreater(m.volume.sum(),0.)
        self.assertLess(abs(m.balance()["error_m3"]),1e-15)

    def test_retraction_does_not_refill(self):
        m=self.model()
        self.advance(m,.01)
        emitted=m.emitted_m3
        self.advance(m,0,steps=10)
        self.assertEqual(m.emitted_m3,emitted)
        self.assertEqual(m.last_flow_m3_s,0.)
        self.assertLessEqual(m.emitted_m3,m.p.initial_volume_m3)

    def test_off_cake_flow_is_not_credited_as_a_border(self):
        m=self.model()
        self.advance(m,.01,pos=(.4,.09,.8055))
        self.advance(m,0,steps=100,pos=(.4,.09,.8055))
        r=assess(m.x,m.y,m.volume,dx=m.dx,emitted_m3=m.emitted_m3,lost_m3=m.lost_m3)
        self.assertEqual(r["score"],0.)
        self.assertGreater(r["spill_area_mm2"],20.)

    def test_volume_conserved_through_slumping(self):
        m=self.model()
        m.volume[60,60]=.5e-6
        m.emitted_m3=.5e-6
        maximum=m.height.max()
        for _ in range(100):m._relax(1/480)
        self.assertLess(m.height.max(),maximum)
        self.assertLess(abs(m.balance()["error_m3"]),1e-18)
        self.assertTrue(np.all(m.volume>=0))

    def test_cake_collision_is_irreversible_damage(self):
        m=self.model()
        reaction=m.tool_contact([[.235,0.,m.cake_top-.002]],[[0.,0.,-.01]],1/240)
        self.assertGreater(reaction[0,2],0.)
        self.assertAlmostEqual(m.cake_damage_depth_m,.002)
        r=assess(m.x,m.y,m.volume,dx=m.dx,emitted_m3=0,damage_depth_m=m.cake_damage_depth_m)
        self.assertEqual(r["score"],0.)

    def test_force_ceases_below_yield(self):
        m=self.model()
        self.advance(m,.0001,steps=10)
        self.assertEqual(m.emitted_m3,0.)

    def test_fixed_volume_slope_is_resolution_sensitive_and_reported(self):
        # A sanity bound only. This does not certify convergence or calibration.
        a,b=Icing(dx=.002),Icing(dx=.001)
        for m in (a,b):
            self.advance(m,.008,steps=60)
        self.assertAlmostEqual(a.emitted_m3,b.emitted_m3,places=15)
        self.assertLess(abs(a.balance()["error_m3"]),1e-15)
        self.assertLess(abs(b.balance()["error_m3"]),1e-15)

    def test_nan_telemetry_cannot_score(self):
        m=self.model()
        m.volume[0,0]=float("nan")
        self.assertEqual(assess(m.x,m.y,m.volume,dx=m.dx,emitted_m3=0)["score"],0.)

    def test_native_coupling_actually_uses_metal_lip_contact(self):
        c=Coupling(self.model())
        pose=np.array((.235,-.080,c.material.cake_top+.001,0.,0.,0.,1.))
        piston=pose.copy();piston[1]-=.060
        barrel_force,piston_force=c.advance(pose,np.zeros(6),piston,1/240)
        self.assertGreater(barrel_force[2],0.)
        self.assertGreater(c.material.cake_damage_depth_m,.001)
        self.assertEqual(c.material.emitted_m3,0.)

    def test_smooth_line_is_not_a_shell_border(self):
        m=self.model();X,Y=m.X,m.Y
        m.volume[(abs(X-.235)<.005)&(abs(Y)<.045)]=.004*m.dx**2
        r=assess(m.x,m.y,m.volume,dx=m.dx,emitted_m3=float(m.volume.sum()),completed=True,tools_clear=True)
        self.assertEqual(r['score'],0.)

    def test_perfect_looking_material_without_execution_proof_scores_zero(self):
        m=self.model()
        m.volume[abs(m.X-.235)<.004]=.006*m.dx**2
        r=assess(m.x,m.y,m.volume,dx=m.dx,emitted_m3=float(m.volume.sum()))
        self.assertEqual(r['score'],0.)

    def test_invalid_grid_and_judgment_types_fail_closed(self):
        m=self.model();base=dict(dx=m.dx,emitted_m3=0.,completed=True,tools_clear=True)
        for field,value in [('completed','false'),('tools_clear',1),('damage_depth_m',-.1),('dx',None)]:
            kw=dict(base);kw[field]=value
            self.assertEqual(assess(m.x,m.y,m.volume,**kw)['score'],0.)
        for x,y,v in [(m.x+1,m.y,m.volume),([],[],np.empty((0,0))),(m.x,m.y*2,m.volume)]:
            self.assertEqual(assess(x,y,v,**base)['score'],0.)

    def test_mirrored_material_gets_the_same_score(self):
        m=Icing(dx=.0005)
        # Synthetic asymmetric shapes exercise rubric direction invariance;
        # these samples are never presented as simulated icing or demo evidence.
        for start in (-.045,-.030,-.015,0.,.015,.030):
            s=(m.Y-start)/.015
            width=np.where(s<.2,.002+.05*np.maximum(s,0),.012-.012*(s-.2))
            height=np.where(s<.2,.001+.02*np.maximum(s,0),.005-.005*(s-.2))
            mask=(s>=0)&(s<=1)&(abs(m.X-.235)<width/2)
            m.volume[mask]=np.maximum(m.volume[mask],height[mask]*m.dx**2)
        kw=dict(dx=m.dx,emitted_m3=float(m.volume.sum()),completed=True,tools_clear=True)
        a=assess(m.x,m.y,m.volume,**kw)
        b=assess(m.x,-m.y[::-1],m.volume[:,::-1],**kw)
        self.assertEqual(a['score'],b['score'])
        self.assertGreater(a['valid_shells'],0)


if __name__=="__main__":unittest.main()
