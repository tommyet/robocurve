import sys
import types
import unittest
from unittest.mock import patch
import numpy as np
from fixture_layout import REFERENCE,RELOCATED,RIGHT_WORKSPACE,offset,axle_position,stand_parts
from wheel_scene import build_scene
from plan_turns import nominal_nipple
from test_authoring_flow import Stage,SchemaNamespace


class FixtureLayoutTests(unittest.TestCase):
    def test_relocation_rejects_source_geometry_that_does_not_match_its_targets(self):
        from relocated_plan import validate_source
        valid=dict(wheel_clocking_deg=55.,nipple_flat_phase_deg=45.,reset_profile='two-defect-candidate')
        validate_source(valid)
        for field,value in [('fixture_layout',RELOCATED),('wheel_clocking_deg',50.),
                            ('nipple_flat_phase_deg',0.),('reset_profile','nominal-corrected-control')]:
            with self.assertRaises(ValueError):validate_source(dict(valid,**{field:value}))

    def test_shorter_stand_keeps_base_and_upright_on_the_same_support(self):
        reference={name:(np.array(p),np.array(s)) for name,p,s in stand_parts(REFERENCE)}
        moved={name:(np.array(p),np.array(s)) for name,p,s in stand_parts(RELOCATED)}
        for name in ('base','upright'):
            self.assertAlmostEqual(moved[name][0][2]-moved[name][1][2]/2,
                                   reference[name][0][2]-reference[name][1][2]/2)
        self.assertAlmostEqual(moved['upright'][1][2],.2275)
        np.testing.assert_allclose(moved['axle_arm'][0]-reference['axle_arm'][0],offset(RELOCATED))

    def test_nominal_nipple_positions_follow_fixture_without_changing_orientation(self):
        for i in range(32):
            p,R=nominal_nipple(i,.3,.4)
            shifted,Q=nominal_nipple(i,.3,.4,fixture_layout=RELOCATED)
            np.testing.assert_allclose(shifted-p,offset(RELOCATED),atol=1e-15)
            np.testing.assert_array_equal(R,Q)
        with self.assertRaises(ValueError):offset('arbitrary-layout')

    def test_authored_world_bearing_matches_wheel_and_spring_parameters_stay_identical(self):
        vector=lambda *values:tuple(values)
        stub=types.SimpleNamespace(Gf=types.SimpleNamespace(Vec3d=vector,Vec3f=vector,Quatf=vector),
            Sdf=types.SimpleNamespace(Path=str),Vt=types.SimpleNamespace(Vec3fArray=lambda value:value),
            UsdGeom=SchemaNamespace(),UsdPhysics=SchemaNamespace(),PhysxSchema=SchemaNamespace())
        states=[]
        with patch.dict(sys.modules,{'pxr':stub}):
            for layout in (REFERENCE,RELOCATED,RIGHT_WORKSPACE):
                stage=Stage()
                meta=build_scene(stage,fixture_layout=layout,central_spring_candidate=True,distance_spring_tolerance_m=.025)
                np.testing.assert_allclose(stage.prims['/WheelTask/wheel'].attributes['TranslateOp'].value,axle_position(layout))
                np.testing.assert_allclose(stage.prims['/WheelTask/wheel/hub_bearing'].attributes['LocalPos0Attr'].value,axle_position(layout))
                states.append((stage,meta))
        for old,new in zip(states[0][1]['spokes'],states[1][1]['spokes']):
            self.assertEqual(old['rest_target_attribute'].Get(),new['rest_target_attribute'].Get())
            self.assertEqual(old['stiffness_n_per_m'],new['stiffness_n_per_m'])
        self.assertEqual(states[0][0].prims['/WheelTask/wrench'].attributes['TranslateOp'].value,
                         states[1][0].prims['/WheelTask/wrench'].attributes['TranslateOp'].value)
        for layout in (RELOCATED,RIGHT_WORKSPACE):
            parts={name:(np.array(p),np.array(s)) for name,p,s in stand_parts(layout)}
            self.assertAlmostEqual(parts['base'][0][2]-parts['base'][1][2]/2,.7475)
            self.assertAlmostEqual(parts['upright'][0][2]-parts['upright'][1][2]/2,.7675)
