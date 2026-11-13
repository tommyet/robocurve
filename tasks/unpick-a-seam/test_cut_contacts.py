"""Check cut/reset graph semantics without claiming native contact validation."""
import sys
import types
import unittest
from unittest.mock import patch
import numpy as np
from native_stitches import (sever_contacted_joints,restore_thread_joints,
                            restore_separated_cut_contacts,segment_distance)


class Value:
    def __init__(self,value):self.value=value
    def Set(self,value):self.value=value;return True
    def GetTargets(self):return list(self.value)
    def SetTargets(self,value):self.value=list(value);return True


class Prim:
    def __init__(self,path,neighbors=()):
        self.path=path;self.pairs=Value(list(neighbors))
        self.enabled=Value(True);self.collision=Value(False)
    def GetPath(self):return self.path
    def GetFilteredPairsRel(self):return self.pairs
    def GetJointEnabledAttr(self):return self.enabled
    def GetCollisionEnabledAttr(self):return self.collision


class Stage:
    def __init__(self):self.prims={}
    def GetPrimAtPath(self,path):return self.prims[path]


def thread(stage,name,n):
    bodies=[f'/{name}/body{i}' for i in range(n)]
    joints=[f'/{name}/joint{i}' for i in range(n)]
    for i,path in enumerate(bodies):
        stage.prims[path]=Prim(path,[bodies[(i-1)%n],bodies[(i+1)%n],'/unrelated-filter'])
    for path in joints:stage.prims[path]=Prim(path)
    return {'bodies':bodies,'joints':joints,'radius_m':.0004}


class CutContactTests(unittest.TestCase):
    def test_cut_restores_only_its_pair_and_reset_is_reversible(self):
        stage=Stage();threads=[thread(stage,'first',3),thread(stage,'second',4)]
        original={path:set(prim.pairs.value) for path,prim in stage.prims.items() if '/body' in path}
        pxr=types.SimpleNamespace(UsdPhysics=types.SimpleNamespace(FilteredPairsAPI=lambda p:p,Joint=lambda p:p))
        with patch.dict(sys.modules,{'pxr':pxr}):
            # Global joint 3 is the second loop's wraparound, not the previous loop.
            sever_contacted_joints(stage,threads,[3],defer_end_contact=False)
            a,b='/second/body3','/second/body0'
            self.assertNotIn(a,stage.prims[b].pairs.value)
            self.assertNotIn(b,stage.prims[a].pairs.value)
            self.assertFalse(stage.prims['/second/joint0'].enabled.value)
            self.assertTrue(stage.prims['/second/joint0'].collision.value)
            for path,old in original.items():
                expected=old-({b} if path==a else {a} if path==b else set())
                self.assertEqual(set(stage.prims[path].pairs.value),expected)
            # A second cut keeps the first pair open and all unrelated filters intact.
            sever_contacted_joints(stage,threads,[4],defer_end_contact=False)
            self.assertNotIn('/second/body1',stage.prims[b].pairs.value)
            self.assertNotIn(a,stage.prims[b].pairs.value)
            for item in threads:restore_thread_joints(stage,item)
            for path,old in original.items():self.assertEqual(set(stage.prims[path].pairs.value),old)
            for item in threads:
                for path in item['joints']:
                    self.assertTrue(stage.prims[path].enabled.value)
                    self.assertFalse(stage.prims[path].collision.value)

    def test_deferred_contact_waits_for_finite_capsules_then_restores_once(self):
        stage=Stage();threads=[thread(stage,'a',4)]
        pxr=types.SimpleNamespace(UsdPhysics=types.SimpleNamespace(FilteredPairsAPI=lambda p:p,Joint=lambda p:p))
        axes=np.array([[[0,0,0],[.002,0,0]],[[.002,0,0],[.002,.002,0]],
                       [[.002,.002,0],[0,.002,0]],[[0,.002,0],[0,0,0]]],float)
        original={path:set(prim.pairs.value) for path,prim in stage.prims.items() if '/body' in path}
        with patch.dict(sys.modules,{'pxr':pxr}):
            sever_contacted_joints(stage,threads,[0])
            self.assertFalse(stage.prims['/a/joint0'].enabled.value)
            self.assertFalse(stage.prims['/a/joint0'].collision.value)
            self.assertEqual(threads[0]['pending_cut_contacts'],{0})
            for path,targets in original.items():self.assertEqual(set(stage.prims[path].pairs.value),targets)
            self.assertEqual(restore_separated_cut_contacts(stage,threads,axes),[])
            # Cut endpoints are distant, but finite axes cross: still filtered.
            axes[3]=[[.001,-.002,0],[.001,.002,0]]
            self.assertEqual(restore_separated_cut_contacts(stage,threads,axes),[])
            # Axis clearance must include both finite radii and contact offsets.
            axes[3]=[[0,0,.000899],[.002,0,.000899]]
            self.assertEqual(restore_separated_cut_contacts(stage,threads,axes),[])
            axes[3,:,2]=.000901
            self.assertEqual(restore_separated_cut_contacts(stage,threads,axes),[0])
            self.assertFalse(threads[0]['pending_cut_contacts'])
            self.assertTrue(stage.prims['/a/joint0'].collision.value)
            self.assertNotIn('/a/body3',stage.prims['/a/body0'].pairs.value)
            axes[3,:,2]=0
            self.assertEqual(restore_separated_cut_contacts(stage,threads,axes),[])
            self.assertNotIn('/a/body3',stage.prims['/a/body0'].pairs.value)
            restore_thread_joints(stage,threads[0])
            for path,targets in original.items():self.assertEqual(set(stage.prims[path].pairs.value),targets)

    def test_reset_clears_pending_and_invalid_geometry_cannot_restore_contact(self):
        stage=Stage();item=thread(stage,'a',4)
        pxr=types.SimpleNamespace(UsdPhysics=types.SimpleNamespace(FilteredPairsAPI=lambda p:p,Joint=lambda p:p))
        with patch.dict(sys.modules,{'pxr':pxr}):
            sever_contacted_joints(stage,[item],[0])
            with self.assertRaises(ValueError):restore_separated_cut_contacts(stage,[item],np.zeros((3,2,3)))
            with self.assertRaises(ValueError):restore_separated_cut_contacts(stage,[item],np.full((4,2,3),np.nan))
            self.assertEqual(item['pending_cut_contacts'],{0})
            restore_thread_joints(stage,item)
            self.assertEqual(item['pending_cut_contacts'],set())
            self.assertTrue(stage.prims['/a/joint0'].enabled.value)

    def test_segment_distance_interior_parallel_and_endpoint_minima(self):
        a=np.array([[0.,0.,0.],[.002,0.,0.]])
        for b,want in [(np.array([[.001,-.002,.0003],[.001,.002,.0003]]),.0003),
                       (a+np.array([0,0,.0009]),.0009),
                       (np.array([[.003,0,0],[.004,0,0]]),.001)]:
            self.assertAlmostEqual(segment_distance(a,b),want,places=14)
            self.assertAlmostEqual(segment_distance(b,a),want,places=14)
        with self.assertRaises(ValueError):segment_distance(a,np.zeros((2,3)))


if __name__=='__main__':unittest.main()
