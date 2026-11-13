"""Bounded real-scale paper/staple native contact diagnostic, never task evidence.

Two 100 µm surface-FEM sheets with explicit original punctures settle onto a
clinched staple held by a diagnostic crown fixture. Free sheets provide the
negative control. Test support, strain and contact before attempting extraction.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback
import numpy as np
from paper import perforated_sheet, ElasticDomainGuard, PaperMaterial
from contact_guard import PaperWireCrossingGuard


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('stapled','free','free-separated'),default='stapled')
    p.add_argument('--seconds',type=float,default=.5)
    p.add_argument('--physics-hz',type=int,choices=(1000,2000,5000,10000),default=2000)
    p.add_argument('--sheet-gap-um','--free-gap-um',dest='sheet_gap_um',type=float,default=100.,help='Diagnostic initial midplane gap; free-separated fixes10mm')
    p.add_argument('--crown-gap-um',type=float,default=0.,help='Initial clearance below the crown, stapled mode only')
    a=p.parse_args()
    if not 0<a.seconds<=2:p.error('Diagnostic limited to two seconds')
    if not 100.<=a.sheet_gap_um<=10000.:p.error('Diagnostic midplane gap must be100–10000µm')
    if a.mode=='free-separated' and a.sheet_gap_um!=100.:p.error('free-separated fixes a10mm gap')
    if not 0.<=a.crown_gap_um<=100. or (a.mode!='stapled' and a.crown_gap_um!=0.):p.error('Crown gap must be0–100µm and is only for stapled mode')
    if a.mode=='stapled' and a.sheet_gap_um>200.:p.error('Stapled layout gap must fit the clinched staple')
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    mesh=perforated_sheet();guards=[ElasticDomainGuard(mesh),ElasticDomainGuard(mesh)]
    crossing=[PaperWireCrossingGuard(mesh.faces),PaperWireCrossingGuard(mesh.faces)]
    material=PaperMaterial()
    report={'kind':'coupled_paper_staple_coupon','status':'running','mode':a.mode,'score':None,'robot_demo':False,
            'mesh':mesh.audit(),'thickness_m':.0001,'physics_hz':a.physics_hz,'seconds':a.seconds,
            'collision_offsets_m':{'contact':material.contact_offset_m,'rest':material.rest_offset_m},
            'limitations':['uncalibrated isotropic paper','planar steel hinge model','crown fixed for diagnostic only'],
            'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ('paper.py','native_paper.py','paper_probe.py','materials.py','physx_material.py','contact_guard.py')}}
    app=None;attached=False;stage=None;cache=None;sim=None
    report["phase"]="launch"
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=False).app
        from pxr import Gf,Usd,UsdGeom,UsdPhysics,PhysxSchema,UsdUtils
        import omni.physics.tensors as tensors
        import carb
        carb.settings.get_settings().set_bool("/physics/suppressReadback",True)
        carb.settings.get_settings().set_int("/physics/cudaDevice",0)
        from omni.physx import get_physx_interface,get_physx_simulation_interface
        from native_paper import author_paper,author_staple,update_staple,measured_wire_segments
        report['phase']='build'
        cache=UsdUtils.StageCache.Get();stage=Usd.Stage.CreateInMemory();cache.Insert(stage)
        stage_id=cache.GetId(stage).ToLongInt()
        UsdGeom.SetStageMetersPerUnit(stage,1.);UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        scene=UsdPhysics.Scene.Define(stage,'/physicsScene')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.));scene.CreateGravityMagnitudeAttr(9.80665)
        sx=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
        sx.CreateEnableGPUDynamicsAttr(True);sx.CreateBroadphaseTypeAttr('GPU')
        sx.CreateSolverTypeAttr('TGS');sx.CreateEnableCCDAttr(False)
        # Explicit diagnostic control: identical sheets, 10 mm of air between
        # their midplanes, so inter-sheet contact cannot explain deformation.
        gap=.01 if a.mode=='free-separated' else a.sheet_gap_um*1e-6
        if a.mode=='stapled':
            top_midplane=.39995-a.crown_gap_um*1e-6
            origins=[(0.,0.,top_midplane-gap),(0.,0.,top_midplane)]
            report['initial_crown_clearance_m']=a.crown_gap_um*1e-6
        else:origins=[(0.,0.,.39985),(0.,0.,.39985+gap)]
        report['initial_midplane_gap_m']=origins[1][2]-origins[0][2]
        for i,origin in enumerate(origins):author_paper(stage,f'/World/Paper_{i}',mesh,origin)
        staple=author_staple(stage,'/World/Staple',origin=(0.,0.,.4),fixed_crown=True) if a.mode=='stapled' else None
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        report['phase']='attach'
        sim=get_physx_simulation_interface();sim.attach_stage(stage_id);attached=True
        simulation=tensors.create_simulation_view('torch',stage_id);simulation.set_subspace_roots('/')
        views=[simulation.create_surface_deformable_body_view(f'/World/Paper_{i}') for i in range(2)]
        if any(v.count!=1 for v in views):raise RuntimeError('Native paper surface body missing')
        frames=[[],[]];snapshots=[]
        # Direct GPU tensor mode cannot rely on the CPU rigid transform cache.
        # Read the actual native steel bodies from the same GPU tensor view.
        wire_view=simulation.create_rigid_body_view('/World/Staple/wire_*') if staple else None
        class TensorPhysics:
            def refresh(self):
                self.transforms={} if wire_view is None else dict(zip(wire_view.prim_paths,wire_view.get_transforms().detach().cpu().numpy()))
            def get_rigidbody_transformation(self,path):
                row=self.transforms.get(path)
                return {'ret_val':False} if row is None else {'ret_val':True,'position':row[:3],'rotation':row[3:]}
        physics=TensorPhysics()
        def positions(view):
            values=view.get_simulation_nodal_positions()
            return values.detach().cpu().numpy()[0,:len(mesh.rest)].copy()
        report['phase']='simulate'
        initial=[];final=[]
        # The GPU tensor backend is populated by the first physics step.
        # Initial strain/contact reference comes from the authored geometry;
        # the first observed frame is explicitly t=1/hz, not hidden settling.
        initial=[mesh.rest.mean(0)+np.asarray(origin) for origin in origins]
        for step in range(1,round(a.seconds*a.physics_hz)+1):
            if step>1 and staple:update_staple(physics,staple)
            sim.simulate(1/a.physics_hz,(step-1)/a.physics_hz);sim.fetch_results()
            physics.refresh()
            measurements=[];step_points=[]
            wire=measured_wire_segments(physics,staple) if staple else None
            for i,view in enumerate(views):
                points=positions(view)
                step_points.append(points)
                result=guards[i].update(points)
                result['centroid_m']=points.astype(np.float64).mean(0).tolist()
                result['z_span_m']=float(np.ptp(points[:,2]))
                if wire is not None:
                    result['contact_audit']=crossing[i].update(points,wire)
                    result['valid']=result['valid'] and result['contact_audit']['valid']
                if step==1 or step%max(1,a.physics_hz//20)==0:frames[i].append(points)
                measurements.append(result)
            if step==1 or step%max(1,a.physics_hz//20)==0:snapshots.append({'step':step,'time_s':step/a.physics_hz,'paper':measurements})
            if any(not result['valid'] for result in measurements):
                report.update(status='invalid_model_domain',first_invalid_step=step,first_invalid_measurements=measurements)
                np.savez_compressed(a.out/'first-invalid-state.npz',paper0=step_points[0],paper1=step_points[1],faces=mesh.faces,rest=mesh.rest)
                break
        for i,view in enumerate(views):final.append(positions(view).astype(np.float64).mean(0))
        np.savez_compressed(a.out/'state.npz',paper0=np.asarray(frames[0]),paper1=np.asarray(frames[1]),faces=mesh.faces,rest=mesh.rest)
        report.update(completed_steps=step,centroid_drop_m=[float(x[2]-y[2]) for x,y in zip(initial,final)],
                      final_centroid_gap_m=float(final[1][2]-final[0][2]),
                      paper=[g.summary() for g in guards],contact_audit=[g.summary() for g in crossing] if staple else None,samples=snapshots,
                      note='A supported coupon must retain sheets with intact elastic-domain checks; free control must fall. Neither proves extraction or robot feasibility.')
        if report['status']=='running':report['status']='complete'
    except BaseException as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc());raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (a.out/'paper-probe.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        if attached:sim.detach_stage()
        if stage and cache:cache.Erase(stage)
        if app:app.close()


if __name__=='__main__':main()
