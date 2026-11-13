"""Recording integrity checks; no simulation or grasp-success claims."""
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
import numpy as np
from trace_data import DenseClothTrace, cloth_array


@dataclass
class State:
    nodes: np.ndarray
    velocities: np.ndarray


class Recording(unittest.TestCase):
    def test_native_float32_bits_survive_recording_and_readback(self):
        with TemporaryDirectory() as folder:
            nodes=np.array(((.123456789, -.000000371, 1.23456789),
                            (-2.3456789, .000000001, -.0)),dtype=np.float32)
            velocity=-nodes
            specs={'tie':SimpleNamespace(mesh=SimpleNamespace(rest=nodes))}
            writer=DenseClothTrace(folder,specs,2)
            encoded=writer.record({'tie':State(nodes,velocity)},1,lambda x:x)
            writer.flush()
            row={'step':1,'objects':encoded}
            for field,expected in [('nodes',nodes),('velocities',velocity)]:
                actual=cloth_array(folder,row,'tie',field)
                self.assertEqual(actual.dtype,np.float32)
                self.assertEqual(actual.tobytes(),expected.tobytes())
            row['step']=0
            with self.assertRaises(ValueError):cloth_array(folder,row,'tie')

    def test_recording_rejects_precision_loss(self):
        with TemporaryDirectory() as folder:
            points=np.zeros((2,3),dtype=np.float64)
            writer=DenseClothTrace(folder,{'tie':SimpleNamespace(mesh=SimpleNamespace(rest=points))},1)
            with self.assertRaises(ValueError):
                writer.record({'tie':State(points,points)},0,lambda x:x)

    def test_legacy_trace_and_external_reference(self):
        row={'step':0,'objects':{'tie':{'nodes':[[1.,2.,3.]]}}}
        np.testing.assert_array_equal(cloth_array('.',row,'tie'),[[1.,2.,3.]])
        row={'step':0,'objects':{'tie':{'dense_cloth_arrays':{
            'nodes':{'file':'../outside.npy','frame':0}}}}}
        with self.assertRaises(ValueError):cloth_array(Path('/tmp/inside'),row,'tie')


if __name__=='__main__':unittest.main()
