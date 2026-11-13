import unittest
import numpy as np
from geometry import stitch_loop


def segment_distance(a,b,c,d):
    # Independent finite-line minimization, including all four boundary minima.
    u=b-a;v=d-c;w=a-c;A=u@u;B=u@v;C=v@v;D=u@w;E=v@w
    determinant=A*C-B*B;values=[]
    if determinant>1e-25:
        s=(B*E-C*D)/determinant;t=(A*E-B*D)/determinant
        if 0<=s<=1 and 0<=t<=1:values.append(np.linalg.norm(a+s*u-c-t*v))
    for p in (a,b):values.append(np.linalg.norm(p-c-np.clip((p-c)@v/C,0,1)*v))
    for p in (c,d):values.append(np.linalg.norm(p-a-np.clip((p-a)@u/A,0,1)*u))
    return min(values)


class ThreadDiscretizationTests(unittest.TestCase):
    def test_same_physical_loop_and_mass_without_non_neighbour_tangency(self):
        old=stitch_loop(.006);new=stitch_loop(.006,clear_capsules=True)
        self.assertEqual(len(old),28);self.assertEqual(len(new),24)
        np.testing.assert_allclose(new.min(0),old.min(0),rtol=0,atol=1e-15)
        np.testing.assert_allclose(new.max(0),old.max(0),rtol=0,atol=1e-15)
        self.assertAlmostEqual(np.linalg.norm(np.roll(old,-1,axis=0)-old,axis=1).sum(),
                               np.linalg.norm(np.roll(new,-1,axis=0)-new,axis=1).sum(),places=14)
        minimum=[]
        for points in (old,new):
            n=len(points);distances=[]
            for i in range(n):
                for j in range(i+1,n):
                    if (j-i)%n in (1,n-1):continue
                    distances.append(segment_distance(points[i],points[(i+1)%n],points[j],points[(j+1)%n])-.0008)
            minimum.append(min(distances))
        self.assertAlmostEqual(minimum[0],0.,places=14)
        self.assertGreater(minimum[1],.000199999999)


if __name__=='__main__':unittest.main()
