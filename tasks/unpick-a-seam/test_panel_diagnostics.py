import unittest
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.spatial.transform import Rotation
from panel_diagnostics import segment_box_distances,linking_number,boundary_loops,solid_contacts
from facet_cloth import shell_mesh,mechanics


class PanelDiagnosticTests(unittest.TestCase):
    def test_exact_segment_box_distance_against_independent_convex_minimum(self):
        rng=np.random.default_rng(69);segments=rng.normal(size=(500,2,3));half=rng.uniform(.01,.8,size=(500,3))
        distance,parameter,points=segment_box_distances(segments,half)
        for i,(segment,h) in enumerate(zip(segments,half)):
            objective=lambda t:np.linalg.norm(np.maximum(np.abs(segment[0]+t*(segment[1]-segment[0]))-h,0.))
            result=minimize_scalar(objective,bounds=(0,1),method='bounded',options={'xatol':1e-14})
            reference=min(objective(0),objective(1),result.fun)
            self.assertAlmostEqual(distance[i],reference,places=7)
        np.testing.assert_allclose(points,segments[:,0]+parameter[:,None]*(segments[:,1]-segments[:,0]),atol=1e-14)

    def test_linking_detects_retained_reversed_and_unlinked_loops(self):
        t=np.linspace(0,2*np.pi,80,endpoint=False)
        a=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
        b=np.c_[1+.5*np.cos(t),np.zeros_like(t),.5*np.sin(t)]
        self.assertEqual(abs(linking_number(a,b)['value']),1)
        self.assertEqual(linking_number(a[::-1],b)['value'],-linking_number(a,b)['value'])
        self.assertEqual(linking_number(a,b+[3,0,0])['value'],0)
        self.assertEqual(linking_number(a*1e-3,b*1e-3)['value'],linking_number(a,b)['value'])
        rotation=Rotation.from_euler('xyz',[.4,.2,.7]);shift=np.array([.3,-.2,.8])
        self.assertEqual(linking_number(rotation.apply(a)+shift,rotation.apply(b)+shift)['value'],linking_number(a,b)['value'])

    def test_box_contacts_use_native_faces_and_finite_radius(self):
        mesh=shell_mesh();model=mechanics(mesh,primitive_boxes=True)
        poses=np.column_stack((model['centres'],np.tile([0,0,0,1],(len(model['centres']),1))))
        c=model['centres'][0];segments=np.array([[c+[0,0,-.001],c+[0,0,.001]]])
        contact=solid_contacts(model,poses,segments)
        self.assertTrue(contact['native_midplane_intersections'])
        self.assertEqual(contact['maximum_capsule_overlap_lower_bound_m'],.0004)
        away=solid_contacts(model,poses,segments+[0,0,1])
        self.assertEqual(away['maximum_capsule_overlap_lower_bound_m'],0.)
        self.assertEqual(len([x for x in boundary_loops(mesh.faces) if len(x)==4]),12)


if __name__=='__main__':unittest.main()
