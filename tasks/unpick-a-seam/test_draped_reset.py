import unittest
import subprocess
import sys
from pathlib import Path
import numpy as np
from draped_reset import initial_drape,cylindrical_drape,triangle_pair_distance,surface_distance
from quality_mesh import quality_patch
from geometry import STITCH_Y,stitch_loop,TABLE_TOP
from contact_audit import ThreadClothAudit
from inspection import StrainAudit,point_triangle_distance


class DrapeTests(unittest.TestCase):
    def test_contact_envelope_preserves_physical_material_and_rest_distance(self):
        from dataclasses import asdict
        from native_cloth import seam_fabric
        baseline=asdict(seam_fabric());expanded=asdict(seam_fabric(.00075))
        self.assertEqual(baseline.pop('contact_offset'),.00025)
        self.assertEqual(expanded.pop('contact_offset'),.00075)
        self.assertEqual(baseline,expanded)
        self.assertEqual(expanded['rest_offset'],.0002)
        self.assertEqual(expanded['thickness'],.0004)
        for value in (0.,.0002,.001,float('nan'),float('inf')):
            with self.assertRaises(ValueError):seam_fabric(value)

    def test_native_contact_correction_bound_is_explicit_and_fail_closed(self):
        from native_cloth import ContactRefinement
        baseline=ContactRefinement(True,4,4).attributes(64)
        bounded=ContactRefinement(True,4,4,.05).attributes(64)
        self.assertEqual(bounded.pop('physxDeformableBody:maxDepenetrationVelocity'),.05)
        self.assertEqual(bounded,baseline)
        for value in (0.,float('nan'),float('inf'),2.):
            with self.assertRaises(ValueError):ContactRefinement(max_depenetration_m_s=value).attributes(64)

    def test_scene_loads_runtime_subtraction_with_loader_only_stubs(self):
        # Exercise scene.py and the actual Cloth/Thread definitions. Only the
        # external loader shell is stubbed: no native simulator is available
        # to this CPU regression. It catches float-sensitive authoring guards.
        script='''
import sys,types,runpy
from dataclasses import dataclass
import numpy as np
@dataclass(frozen=True)
class Box:
    name:str
    pos:tuple
    size:tuple
    mass:float|None=None
    color:tuple=(.5,.5,.5)
@dataclass(frozen=True)
class ObjectState:pass
package=types.ModuleType('yam_arena');package.__path__=[]
adapter=types.ModuleType('yam_arena.scene')
adapter.task_object=lambda x:x
adapter.object_states=lambda env,names:{}
task_file=types.ModuleType('yam_arena.task_file')
task_file.Box=Box;task_file.ObjectState=ObjectState
package.scene=adapter
sys.modules.update({'yam_arena':package,'yam_arena.scene':adapter,'yam_arena.task_file':task_file})
import runtime_config
for shape in ('gaussian','cylindrical'):
    runtime_config.CONFIG=runtime_config.SeamRuntime(thread_radius_m=.0004,hole_half_m=.0008,
        quality_mesh=True,seam_lowering_m=.0024-.0004,pre_draped_seam=True,drape_shape=shape)
    result=runpy.run_path('scene.py')
    assert len(result['OBJECTS'])==10
    for mesh,initial in zip(result['MESHES'],result['INITIAL']):
        assert np.ptp(mesh.rest[:,2])==0
        assert np.ptp(initial[:,2])>.000899
        assert not np.shares_memory(mesh.rest,initial)
    assert max(abs(result['thread_nodes'](0.)[:,2].min()-(.7475+.0004)),0)<1e-12
runtime_config.CONFIG=runtime_config.SeamRuntime(thread_radius_m=.0004,hole_half_m=.0008,
    hole_mesh_spacing_m=.0004,sewing_clamp=True)
result=runpy.run_path('scene.py')
assert len(result['OBJECTS'])==17
assert len(result['FIXTURE'])==7
assert all(item.mass is None for item in result['FIXTURE'])
assert abs(result['MESHES'][1].rest[:,2].min()-(.7475+.020))<1e-12
for mesh,initial in zip(result['MESHES'],result['INITIAL']):
    assert len(mesh.rest)==4407 and len(mesh.faces)==8490
    assert np.ptp(mesh.rest[:,0])<1e-12
    np.testing.assert_array_equal(mesh.rest,initial)
runtime_config.CONFIG=runtime_config.SeamRuntime(thread_radius_m=.0004,hole_half_m=.0008,
    hole_mesh_spacing_m=.0004,sewing_clamp=True,passive_clamp=True)
result=runpy.run_path('scene.py')
assert len(result['OBJECTS'])==15 and len(result['FIXTURE'])==5
moving=[item for item in result['FIXTURE'] if item.mass is not None]
assert len(moving)==1 and moving[0].name=='clamp_moving_jaw' and moving[0].mass==.012
assert all(np.ptp(mesh.rest[:,0])<1e-12 for mesh in result['MESHES'])
runtime_config.CONFIG=runtime_config.SeamRuntime(thread_radius_m=.0004,hole_half_m=.0008,
    quality_mesh=True,sewing_clamp=True,passive_clamp=True)
result=runpy.run_path('scene.py')
assert all(len(mesh.rest)==1582 and len(mesh.faces)==2888 for mesh in result['MESHES'])
assert len(result['FIXTURE'])==5
assert abs(result['MESHES'][1].rest[:,2].min()-(.7475+.020))<1e-12
runtime_config.CONFIG=runtime_config.SeamRuntime(thread_radius_m=.0004,hole_half_m=.0008,
    quality_mesh=True,sewing_clamp=True,passive_clamp=True,supported_clamp=True)
result=runpy.run_path('scene.py')
assert abs(result['MESHES'][1].rest[:,2].min()-(.7475+.0002))<1e-12
assert len(result['FIXTURE'])==5
baseline=result
from dataclasses import replace,asdict
runtime_config.CONFIG=replace(runtime_config.CONFIG,cloth_contact_offset_m=.00075)
result=runpy.run_path('scene.py')
assert result['FABRIC'].contact_offset==.00075
assert baseline['FABRIC'].contact_offset==.00025
for before,after in zip(baseline['MESHES'],result['MESHES']):
    np.testing.assert_array_equal(before.rest,after.rest)
    np.testing.assert_array_equal(before.faces,after.faces)
assert baseline['FIXTURE']==result['FIXTURE']
np.testing.assert_array_equal(baseline['thread_nodes'](0.),result['thread_nodes'](0.))
runtime_config.CONFIG=replace(runtime_config.CONFIG,cloth_contact_offset_m=.00025,backed_clamp=True)
result=runpy.run_path('scene.py')
assert len(result['FIXTURE'])==17
assert len([box for box in result['FIXTURE'] if box.mass is not None])==1
for before,after in zip(baseline['MESHES'],result['MESHES']):
    np.testing.assert_array_equal(before.rest,after.rest)
    np.testing.assert_array_equal(before.faces,after.faces)
from repair_backing import initial_clearance,fixture_boxes
assert abs(initial_clearance(result['MESHES'],[result['thread_nodes'](y) for y in result['STITCH_Y']])-.0002)<1e-12
assert len(fixture_boxes())==12
runtime_config.CONFIG=replace(runtime_config.CONFIG,quality_mesh=False,facet_cloth=True)
result=runpy.run_path('scene.py')
assert all(len(mesh.faces)==236 for mesh in result['MESHES'])
assert len(result['FIXTURE'])==17
assert type(result['OBJECTS'][0]).__name__=='FacetCloth'
assert abs(result['MESHES'][0].audit()['surface_area_m2']-baseline['MESHES'][0].audit()['surface_area_m2'])<1e-12
station=result
import coordinate_frame
coordinate_frame.configure(True)
runtime_config.CONFIG=replace(runtime_config.CONFIG,box_panels=True,cpu_ccd=True,
    clear_thread_sampling=True,passive_thread_bending=True)
result=runpy.run_path('scene.py')
for old,mesh,initial in zip(station['MESHES'],result['MESHES'],result['INITIAL']):
    np.testing.assert_allclose(mesh.rest,old.rest+coordinate_frame.OFFSET_M,rtol=0,atol=1e-15)
    np.testing.assert_array_equal(mesh.rest,initial)
from arena_thread import initial as thread_reset
from thread_bending import planar_frames
threads=[item for item in result['OBJECTS'] if item.name.startswith('stitch_')]
assert len(threads)==6 and all(len(item.nodes)==24 for item in threads)
for item in threads:
    reset=thread_reset(item)
    np.testing.assert_allclose(reset[:,:3],(item.nodes+np.roll(item.nodes,-1,axis=0))/2,atol=1e-15)
    np.testing.assert_allclose(reset[:,3:],planar_frames(item.nodes),atol=1e-15)
    assert item.bending.rigidity_nm2==1.2e-9
assert all(abs(mesh.rest[:,0].mean())<.001 for mesh in result['MESHES'])
assert station['FIXTURE']==result['FIXTURE']  # ordinary roots shift in cfg, once
coordinate_frame.configure(False)
'''
        result=subprocess.run([sys.executable,'-c',script],cwd=Path(__file__).resolve().parent,
                              text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_triangle_features_include_edge_interiors_and_piercing(self):
        first=np.array([[[0,0,0],[1,0,0],[0,1,0]]],float)
        lifted=first+np.array([.1,.1,.25])
        self.assertAlmostEqual(triangle_pair_distance(first,lifted)[0],.25)
        piercing=np.array([[[.2,.2,-1],[.2,.2,1],[.3,.2,1]]])
        self.assertEqual(triangle_pair_distance(first,piercing)[0],0.)
        # Closest points lie inside both edges, not at any vertex.
        edge_a=np.array([[[-1,0,0],[1,0,0],[0,-1,0]]],float)
        edge_b=np.array([[[0,0,1],[0,0,2],[0,1,1]]],float)
        self.assertAlmostEqual(triangle_pair_distance(edge_a,edge_b)[0],1.)

    def test_fixed_drape_has_clearance_and_preserves_intrinsic_rest(self):
        meshes=[quality_patch(True),quality_patch(False)]
        rest=[mesh.rest.copy() for mesh in meshes]
        initial=[initial_drape(mesh,upper) for mesh,upper in zip(meshes,(True,False))]
        separation=surface_distance(initial[0],meshes[0].faces,initial[1],meshes[1].faces)
        self.assertTrue(separation['exact_minimum'])
        self.assertGreater(separation['minimum_surface_distance_m'],.0004)
        segments=[];samples=[];max_interval=0.
        for y in STITCH_Y:
            nodes=stitch_loop(y);nodes[:,2]-=.002
            for a,b in zip(nodes,np.roll(nodes,-1,axis=0)):
                segments.append((a,b))
                count=max(1,int(np.ceil(np.linalg.norm(b-a)/.0001)))
                max_interval=max(max_interval,np.linalg.norm(b-a)/count)
                samples.extend(a+(b-a)*t for t in np.linspace(0,1,count+1))
        for mesh,original,points in zip(meshes,rest,initial):
            np.testing.assert_array_equal(mesh.rest,original)
            np.testing.assert_array_equal(points[:,:2],original[:,:2])
            self.assertGreaterEqual(float(points[:,2].min()),TABLE_TOP+.0002-1e-12)
            strain=StrainAudit(original,mesh.faces);self.assertFalse(strain.update(points,0.))
            crossing=ThreadClothAudit(mesh.faces);crossing.update(points,segments,0.)
            self.assertIsNone(crossing.first_failure)
            # Continuous capsule-axis lower bound includes cloth half-thickness.
            distance=float(point_triangle_distance(samples,points,mesh.faces).min())-max_interval/2
            self.assertGreater(distance,.0004+.0002)

    def test_cylindrical_reset_is_nearly_isometric_and_preserves_holes(self):
        meshes=[quality_patch(True),quality_patch(False)]
        initial=[cylindrical_drape(m,upper) for m,upper in zip(meshes,(True,False))]
        for mesh,points in zip(meshes,initial):
            strain=StrainAudit(mesh.rest,mesh.faces);strain.update(points,0.)
            self.assertLess(strain.maximum_observed,1.00003)
            overlap=(mesh.rest[:,0]>=.290)&(mesh.rest[:,0]<=.310)
            np.testing.assert_array_equal(points[overlap,:2],mesh.rest[overlap,:2])
            np.testing.assert_array_equal(points[:,1],mesh.rest[:,1])
            self.assertLess(np.max(np.abs(points[:,0]-mesh.rest[:,0])),.000064)
        self.assertGreater(surface_distance(initial[0],meshes[0].faces,initial[1],meshes[1].faces)
                           ['minimum_surface_distance_m'],.0004)


if __name__=='__main__':unittest.main()
