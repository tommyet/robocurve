"""Check cut/reset graph semantics without claiming native contact validation."""
import sys
import types
import unittest
from unittest.mock import patch
from native_stitches import sever_contacted_joints,restore_thread_joints


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
    return {'bodies':bodies,'joints':joints}


class CutContactTests(unittest.TestCase):
    def test_cut_restores_only_its_pair_and_reset_is_reversible(self):
        stage=Stage();threads=[thread(stage,'first',3),thread(stage,'second',4)]
        original={path:set(prim.pairs.value) for path,prim in stage.prims.items() if '/body' in path}
        pxr=types.SimpleNamespace(UsdPhysics=types.SimpleNamespace(FilteredPairsAPI=lambda p:p,Joint=lambda p:p))
        with patch.dict(sys.modules,{'pxr':pxr}):
            # Global joint 3 is the second loop's wraparound, not the previous loop.
            sever_contacted_joints(stage,threads,[3])
            a,b='/second/body3','/second/body0'
            self.assertNotIn(a,stage.prims[b].pairs.value)
            self.assertNotIn(b,stage.prims[a].pairs.value)
            self.assertFalse(stage.prims['/second/joint0'].enabled.value)
            self.assertTrue(stage.prims['/second/joint0'].collision.value)
            for path,old in original.items():
                expected=old-({b} if path==a else {a} if path==b else set())
                self.assertEqual(set(stage.prims[path].pairs.value),expected)
            # A second cut keeps the first pair open and all unrelated filters intact.
            sever_contacted_joints(stage,threads,[4])
            self.assertNotIn('/second/body1',stage.prims[b].pairs.value)
            self.assertNotIn(a,stage.prims[b].pairs.value)
            for item in threads:restore_thread_joints(stage,item)
            for path,old in original.items():self.assertEqual(set(stage.prims[path].pairs.value),old)
            for item in threads:
                for path in item['joints']:
                    self.assertTrue(stage.prims[path].enabled.value)
                    self.assertFalse(stage.prims[path].collision.value)


if __name__=='__main__':unittest.main()
