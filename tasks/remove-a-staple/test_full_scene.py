"""Geometry safeguards for the actual A5 sheets, independent of Isaac."""
import hashlib
import json
from pathlib import Path
import unittest
import numpy as np
from contact_guard import PaperWireCrossingGuard
from full_scene import paper_mesh,SHEET_CENTRES,PAPER_CENTRE_HEIGHTS,STAPLE_XY,PAPER_TOP,scene_layout,SUPPORT_TOP,support_parts
from generate_meshes import quality
from materials import clinched_staple_centerline
from paper import ElasticDomainGuard,PaperMesh


class FullPaperTests(unittest.TestCase):
    def test_frozen_assets_match_manifest_and_keep_real_boundaries(self):
        assets=Path(__file__).with_name('assets')
        manifest=json.loads((assets/'mesh-manifest.json').read_text())
        for i,entry in enumerate(manifest['meshes']):
            self.assertEqual(hashlib.sha256((assets/entry['file']).read_bytes()).hexdigest(),entry['sha256'])
            metrics=quality(paper_mesh(i),(.21,.148))
            self.assertGreaterEqual(metrics['minimum_triangle_angle_deg'],15.)
            self.assertLessEqual(metrics['maximum_edge_length_ratio'],4.)
            self.assertAlmostEqual(metrics['surface_area_m2'],.21*.148-2*.00062*.00042,places=12)

    def test_authored_staple_passes_only_through_existing_holes(self):
        points=clinched_staple_centerline()
        rotation=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
        points=np.asarray(points)@rotation.T+[*STAPLE_XY,PAPER_TOP]
        wire=np.stack((points[:-1],points[1:]),axis=1)
        for i,xy in enumerate(SHEET_CENTRES):
            mesh=paper_mesh(i)
            world=mesh.rest+[*xy,PAPER_CENTRE_HEIGHTS[i]]
            self.assertTrue(PaperWireCrossingGuard(mesh.faces).update(world,wire)['valid'])
            # Translating the staple 2 mm sideways puts its legs through intact paper.
            self.assertFalse(PaperWireCrossingGuard(mesh.faces).update(world,wire+[.002,0.,0.])['valid'])

    def test_supported_reset_starts_on_board_with_clinched_legs_clear(self):
        layout=scene_layout('supported-edge-candidate')
        self.assertAlmostEqual(layout['paper_centres_z'][0]-.00005,SUPPORT_TOP)
        left=layout['support_center'][0]-layout['support_size'][0]/2
        self.assertGreater(left-STAPLE_XY[0],.007)
        self.assertLess(left-(SHEET_CENTRES[0][0]-.105),.021)
        self.assertAlmostEqual(layout['paper_centres_z'][1]-layout['paper_centres_z'][0],.00012)
        points=clinched_staple_centerline()
        rotation=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
        points=np.asarray(points)@rotation.T+[*STAPLE_XY,layout['crown_underside_z']]
        self.assertTrue(np.all(points[:,0]+.00025<left))
        wire=np.stack((points[:-1],points[1:]),axis=1)
        for i,xy in enumerate(SHEET_CENTRES):
            mesh=paper_mesh(i);world=mesh.rest+[*xy,layout['paper_centres_z'][i]]
            self.assertTrue(PaperWireCrossingGuard(mesh.faces).update(world,wire)['valid'])
        with self.assertRaises(ValueError):scene_layout('unknown')

    def test_full_mesh_rigid_motion_is_not_strain(self):
        angle=.61;c=np.cos(angle);s=np.sin(angle)
        rotation=np.array([[c,0.,s],[0.,1.,0.],[-s,0.,c]])
        for i in range(2):
            mesh=paper_mesh(i)
            result=ElasticDomainGuard(mesh).update(mesh.rest@rotation.T+[.3,-.2,.7])
            self.assertTrue(result['valid'])

    def test_pocket_support_leaves_the_entire_planar_leg_sweep_free(self):
        layout=scene_layout('pocket-support-candidate');parts=support_parts(layout)
        pocket=layout['clinch_clearance_pocket'];center=np.array(pocket['center_m']);size=np.array(pocket['size_m'])
        self.assertAlmostEqual(sum(np.prod(s) for _,_,s in parts),np.prod(layout['support_size'])-np.prod(size))
        # Conservative envelope: a whole 6mm leg rotates from inward flat to
        # vertical under either puncture. Its finite wire section fits too.
        for side in (-1,1):
            for angle in np.linspace(0,np.pi/2,91):
                for length in np.linspace(0,.006,13):
                    point=np.array((STAPLE_XY[0],STAPLE_XY[1]+side*(.0064-length*np.cos(angle)),
                                    SUPPORT_TOP-.0002-length*np.sin(angle)))
                    self.assertGreaterEqual(point[2]-.00015,center[2]-size[2]/2)
                    self.assertLessEqual(abs(point[0]-center[0])+.00025,size[0]/2)
                    self.assertLessEqual(abs(point[1]-center[1])+.00015,size[1]/2)
        self.assertAlmostEqual(layout['paper_centres_z'][0]-.00005,SUPPORT_TOP)

    def test_missing_triangle_cannot_pass_boundary_or_area_audit(self):
        mesh=paper_mesh(0)
        damaged=PaperMesh(mesh.rest,mesh.faces[1:],mesh.holes)
        with self.assertRaises(ValueError):quality(damaged,(.21,.148))


if __name__=='__main__':unittest.main()
