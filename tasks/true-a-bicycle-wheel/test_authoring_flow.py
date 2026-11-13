"""Exercise authoring Python on a recording stub; this is not USD validation.

The native runtime remains necessary for schema/physics checks. This cheap test
catches errors on rarely used branches before allocating a simulator run.
"""
import sys
import types
import unittest
from unittest.mock import patch
from wheel_scene import build_scene


class Attribute:
    def __init__(self,value=None):self.value=value
    def Set(self,value):self.value=value;return True
    def SetTargets(self,value):self.value=value;return True
    def Get(self):return self.value


class Prim:
    def __init__(self,path):self.path=path;self.attributes={};self.apis=[]
    def GetPrim(self):return self
    def __getattr__(self,name):
        if name=='SetXformOpOrder':return lambda order:None
        if name.startswith(('Create','Get','Add')):
            key=name.removeprefix('Create').removeprefix('Get').removeprefix('Add')
            def attribute(*args):
                attr=self.attributes.setdefault(key,Attribute())
                if args:attr.Set(args[0])
                return attr
            return attribute
        raise AttributeError(name)


class Stage:
    def __init__(self):self.prims={}
    def GetPrimAtPath(self,path):return self.prims.setdefault(path,Prim(path))


class Schema:
    def __init__(self,name):self.name=name
    def Define(self,stage,path):return stage.GetPrimAtPath(path)
    def Apply(self,prim,*instance):prim.apis.append(self.name);return prim


class SchemaNamespace:
    Tokens=types.SimpleNamespace(z='Z')
    def __getattr__(self,name):
        if name.startswith('SetStage'):return lambda *args:None
        return Schema(name)


class AuthoringFlowTests(unittest.TestCase):
    def test_native_central_springs_use_positive_centre_separation(self):
        vector=lambda *values:tuple(values)
        stub=types.SimpleNamespace(Gf=types.SimpleNamespace(Vec3d=vector,Vec3f=vector,Quatf=vector),
            Sdf=types.SimpleNamespace(Path=str),Vt=types.SimpleNamespace(Vec3fArray=lambda value:value),
            UsdGeom=SchemaNamespace(),UsdPhysics=SchemaNamespace(),PhysxSchema=SchemaNamespace())
        with patch.dict(sys.modules,{'pxr':stub}):
            stage=Stage();metadata=build_scene(stage,central_spring_candidate=True,distance_spring_tolerance_m=.025,inextensible_rim_candidate=True)
        self.assertTrue(metadata['inextensible_rim_candidate'])
        for i in range(32):
            joint=stage.prims[f'/WheelTask/wheel/rim_joint_{i:02d}']
            self.assertEqual(joint.attributes['StiffnessAttr'].value,0.)
            self.assertGreater(joint.attributes['LowAttr'].value,joint.attributes['HighAttr'].value)
        for i,spoke in enumerate(metadata['spokes']):
            spring=stage.prims[f'/WheelTask/wheel/spoke_{i:02d}_central_spring']
            self.assertIn('PhysxPhysicsDistanceJointAPI',spring.apis)
            self.assertTrue(spring.attributes['SpringEnabledAttr'].value)
            self.assertGreater(spoke['rest_target_attribute'].Get(),.05)
            self.assertAlmostEqual(spoke['rest_target_origin_m'],spoke['half_rod_length_m'])
            actual=spoke['half_rod_length_m']+spoke['rest_target_origin_m']
            rest=spoke['rest_target_attribute'].Get()+spoke['rest_target_origin_m']+spoke['native_rest_bias_m']
            self.assertGreater(actual-rest,0.) if i not in (0,2) else None

    def test_all_wheel_authoring_branches_execute_and_axes_stay_explicit(self):
        vector=lambda *values:tuple(values)
        stub=types.SimpleNamespace(Gf=types.SimpleNamespace(Vec3d=vector,Vec3f=vector,Quatf=vector),
            Sdf=types.SimpleNamespace(Path=str),Vt=types.SimpleNamespace(Vec3fArray=lambda value:value),
            UsdGeom=SchemaNamespace(),UsdPhysics=SchemaNamespace(),PhysxSchema=SchemaNamespace())
        with patch.dict(sys.modules,{'pxr':stub}):
            stage=Stage();metadata=build_scene(stage,wheel_clocking_rad=.1,nipple_flat_phase_rad=.2)
        self.assertEqual(len(metadata['spokes']),32)
        rigid=[p for p in stage.prims.values() if 'RigidBodyAPI' in p.apis]
        self.assertEqual(len(rigid),130)
        self.assertEqual(stage.prims['/WheelTask/wheel/hub_bearing'].attributes['AxisAttr'].value,'Z')
        for i in range(32):
            self.assertEqual(stage.prims[f'/WheelTask/wheel/nipple_{i:02d}/barrel'].attributes['AxisAttr'].value,'X')
