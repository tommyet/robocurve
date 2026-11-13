"""Cheap native surface-cloth diagnostics, not a robot task demonstration.

Run under the retained Isaac Sim interpreter. No Dream calls are made. Start
with --mode drape --seconds 3, then clamp and open-clamp. All cloth and jaw
movement comes from native physics after the initial state is authored.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import traceback
import numpy as np
from cloth_mesh import Mesh,tshirt,edge_strain
from native_cloth import Fabric


def coupon(spacing=.005):
    nx=round(.18/spacing);ny=round(.05/spacing)
    x,y=np.meshgrid(np.linspace(0,.18,nx+1),np.linspace(-.025,.025,ny+1))
    points=np.column_stack((x.ravel(),y.ravel(),np.zeros(x.size)))
    faces=[]
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i
            faces.extend(((a,a+1,a+nx+2),(a,a+nx+2,a+nx+1)))
    return Mesh(points,np.asarray(faces),{})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('drop','drape','clamp','open-clamp','line-clamp','task-layout'),default='drape')
    p.add_argument('--line-diameter-mm',type=float,choices=(3.,5.),default=3.,help='Line-clamp diagnostic only')
    p.add_argument('--coupon-spacing-mm',type=float,choices=(2.5,5.,10.),default=10.,help='Line-clamp diagnostic only')
    p.add_argument('--spring-stiffness-scale',type=float,choices=(.1,.25,1.),default=1.,help='Line-clamp force diagnostic only; task spring is unchanged')
    p.add_argument('--spring-damping',type=float,choices=(.003,.0085),default=.003,help='Line-clamp damping diagnostic in Nm s/rad; .0085 is five times the fixed-jaw critical estimate')
    p.add_argument('--seconds',type=float,default=3.)
    p.add_argument('--peg-rests',action=argparse.BooleanOptionalAction,default=None,help='Ordinary handle-access rests, selected by default for task-layout; --no-peg-rests reproduces the old table-peg control')
    p.add_argument('--line-pegs',action='store_true',help='Task-layout candidate: spare pegs physically clipped to the empty line, with no peg rests')
    p.add_argument('--board-thickness-mm',type=float,default=None,
                   help='Task-layout diagnostic override for support thickness; task default is 8 mm')
    p.add_argument('--physics-hz',type=int,choices=(240,480,960),default=480)
    p.add_argument('--contact-refinement',choices=('baseline','iterations','speculative','combined'),
                   default='baseline',help='Diagnostic native contact controls only; geometry/material/audit unchanged')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--headless',choices=('true','false'),default='true')
    p.add_argument('--no-render',action='store_true',help='Only for diagnosing renderer failures; no RGB evidence')
    args=p.parse_args()
    if not 0 < args.seconds <= 10:
        p.error('a diagnostic is limited to ten simulated seconds')
    if args.board_thickness_mm is not None and (args.mode!='task-layout' or not 8<=args.board_thickness_mm<=40):
        p.error('board thickness diagnostics require task-layout and 8–40 mm')
    if args.peg_rests is True and args.mode!='task-layout':p.error('--peg-rests requires task-layout')
    if args.spring_stiffness_scale!=1. and args.mode!='line-clamp':p.error('Spring-force diagnostic requires line-clamp')
    if args.spring_damping!=.003 and args.mode!='line-clamp':p.error('Damping diagnostic requires line-clamp')
    if args.line_pegs and args.mode!='task-layout':p.error('--line-pegs requires task-layout')
    if args.line_pegs and args.peg_rests is True:p.error('Choose line pegs or peg rests')
    args.peg_rests=args.mode=='task-layout' and args.peg_rests is not False and not args.line_pegs
    args.output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    # Application must precede all simulator imports.
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=args.headless=='true', enable_cameras=not args.no_render).app
    report={'status':'running','kind':'diagnostic_not_submission_evidence',
            'mode':args.mode,'material':asdict(Fabric()),'physics_hz':args.physics_hz,
            'seconds':args.seconds,'provenance':{},'phase':'build',
            'render_bridge':None if args.no_render else 'native PhysX Fabric'}
    for name in ('probe.py','cloth_mesh.py','native_cloth.py','scene.py','probe_capture.py','probe_runtime.py','peg_rests.py','line_pegs.py'):
        report['provenance'][name]=hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    capture=None
    world=None
    try:
        from probe_runtime import ProbeRuntime
        from pxr import Gf,UsdGeom,UsdPhysics,PhysxSchema
        import omni.physics.tensors as tensors
        from native_cloth import author_cloth,author_box,author_peg,ensure_gpu_scene
        world=ProbeRuntime(app, 1/args.physics_hz, render=not args.no_render)
        stage=world.stage
        author_box(stage,'/World/Ground',(10.,10.,.1),(0.,0.,-.05))
        ensure_gpu_scene(stage)
        cloth_path='/World/Cloth'
        if args.mode=='task-layout':
            import scene
            if args.board_thickness_mm is not None:
                scene.SUPPORT_BOARD_THICKNESS=args.board_thickness_mm/1000
            report['support_board_thickness_m']=scene.SUPPORT_BOARD_THICKNESS
            from scene import author_props,initial_layout,TABLE
            author_box(stage,'/World/Table',(1.1,1.3,.06),(.36,0.,TABLE-.03),(.58,.39,.25))
            report['peg_rests_candidate']=bool(args.peg_rests)
            report['line_pegs_candidate']=bool(args.line_pegs)
            mesh=author_props(stage,with_peg_rests=args.peg_rests,line_pegs=args.line_pegs)
            initial=initial_layout(mesh)
            cloth_path='/World/Tshirt'
        elif args.mode in ('drop','drape'):
            mesh=tshirt()
            initial=mesh.rest.copy()
            initial[:,0]+=.05
            initial[:,1]-=.15
            initial[:,2]+=.40
            if args.mode=='drape':
                # A 10 mm round rail does not pin any vertices.
                rail=UsdGeom.Cylinder.Define(stage,'/World/Rail')
                rail.CreateRadiusAttr(.005)
                rail.CreateHeightAttr(.55)
                rail.CreateAxisAttr('X')
                rail.AddTranslateOp().Set(Gf.Vec3d(.05,0.,.32))
                UsdPhysics.CollisionAPI.Apply(rail.GetPrim())
                collision=PhysxSchema.PhysxCollisionAPI.Apply(rail.GetPrim())
                collision.CreateContactOffsetAttr(.0005)
                collision.CreateRestOffsetAttr(0.)
        else:
            mesh=coupon(args.coupon_spacing_mm/1000 if args.mode=='line-clamp' else .005)
            initial=mesh.rest.copy()
            initial[:,2]+=.5004
            author_peg(stage,'/World/Peg',pos=(0.,0.,.5),fixed_lower=True,
                       spring=args.mode in ('clamp','line-clamp'),open_angle=-.35)
            if args.mode=='line-clamp':
                # Mechanism coupon only: a fixed lower jaw removes robot
                # positioning variance. The upper jaw closes by its passive
                # spring. Cloth begins clear of both jaws and the round line.
                radius=args.line_diameter_mm/2000
                center=(.030,0.,.5005+radius)
                initial[:,0]+=.020
                initial[:,2]=center[2]+radius+.0006
                rail=UsdGeom.Cylinder.Define(stage,'/World/Line')
                rail.CreateRadiusAttr(radius);rail.CreateHeightAttr(.2);rail.CreateAxisAttr('Y')
                rail.AddTranslateOp().Set(Gf.Vec3d(*center))
                UsdPhysics.CollisionAPI.Apply(rail.GetPrim())
                cp=PhysxSchema.PhysxCollisionAPI.Apply(rail.GetPrim())
                cp.CreateContactOffsetAttr(.0005);cp.CreateRestOffsetAttr(0.)
                report['line_fixture']=dict(kind='cylinder',center=center,radius=radius,height=.2,axis='Y')
                report['coupon_spacing_m']=args.coupon_spacing_mm/1000
                drive=UsdPhysics.DriveAPI(stage.GetPrimAtPath('/World/Peg/hinge'),'angular')
                drive.GetStiffnessAttr().Set(drive.GetStiffnessAttr().Get()*args.spring_stiffness_scale)
                drive.GetDampingAttr().Set(args.spring_damping*np.pi/180)
                report['spring_stiffness_scale']=args.spring_stiffness_scale
                report['spring_damping_Nm_s_per_rad']=args.spring_damping
                report['damping_basis']='Upper jaw4g, two35x10x6mm boxes with their authored offsets: hinge-axis inertia1.798e-6kgm2, critical damping2sqrt(0.4*I)=0.001696Nm s/rad.0.0085 is a diagnostic five-critical overdamped closure, not calibrated wood friction.'
            if args.mode=='open-clamp':
                # Negative diagnostic: the jaw is fixed in the declared open
                # pose. This fixture is never used in a task episode.
                UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath('/World/Peg/upper')).CreateKinematicEnabledAttr(True)
        if args.mode!='task-layout':
            author_cloth(stage,cloth_path,mesh,points=initial)
        # Native body contact options only; no global GPU-incompatible scene CCD.
        from native_cloth import _set
        contact_prim=stage.GetPrimAtPath(cloth_path)
        if args.contact_refinement in ('iterations','combined'):
            _set(contact_prim,'physxDeformableBody:collisionIterationMultiplier',4)
            _set(contact_prim,'physxDeformableBody:collisionPairUpdateFrequency',4)
        if args.contact_refinement in ('speculative','combined'):
            _set(contact_prim,'physxDeformableBody:enableSpeculativeCCD',True)
        report['contact_refinement']={'mode':args.contact_refinement,'native_attributes':{
            key:contact_prim.GetAttribute(key).Get() for key in (
                'physxDeformableBody:collisionIterationMultiplier',
                'physxDeformableBody:collisionPairUpdateFrequency',
                'physxDeformableBody:enableSpeculativeCCD')}}
        if not args.no_render:
            from probe_capture import ProbeCapture
            if args.mode in ('clamp','open-clamp','line-clamp'):
                eye,target=(.30,-.38,.72),(.045,0.,.45)
            elif args.mode=='task-layout':
                eye,target=(1.25,-1.30,1.60),(.38,0.,.92)
            else:
                eye,target=(.64,-.62,.76),(.05,0.,.25)
            capture=ProbeCapture(stage,args.output,eye,target)
        stage.GetRootLayer().Export(str(args.output/'initial.usda'))
        report['phase']='attach'
        world.start()
        report['phase']='tensor_view'
        simview=tensors.create_simulation_view('torch',stage_id=world.stage_id)
        simview.set_subspace_roots('/')
        cloth=simview.create_surface_deformable_body_view(cloth_path)
        if cloth.count != 1:
            raise RuntimeError('Native cloth view did not register exactly one body')
        peg_view=None
        peg_poses=[]
        peg_velocities=[]
        if args.mode=='task-layout':
            peg_paths=[f'/World/{side}Peg/{jaw}' for side in ('Left','Right') for jaw in ('lower','upper')]
            peg_view=simview.create_rigid_body_view(peg_paths)
            if peg_view.count!=4:raise RuntimeError('Expected four actual free peg-jaw bodies')
            report['peg_body_paths']=peg_paths
        elif args.mode=='line-clamp':
            peg_paths=['/World/Peg/lower','/World/Peg/upper']
            peg_view=simview.create_rigid_body_view(peg_paths)
            if peg_view.count!=2:raise RuntimeError('Expected two actual diagnostic peg jaws')
            report['peg_body_paths']=peg_paths
        report['phase']='simulate'
        report['initial_native_sample_time_s']=1/args.physics_hz
        report['initial_sample_note']='GPU native getters require one step; this is counted within the requested duration, not an extra warmup'
        frames=[]
        times=[]
        velocity_max=0.
        for step in range(1,round(args.seconds*args.physics_hz)+1):
            world.step(render=(capture is not None and step % max(1,args.physics_hz//60)==0))
            if capture is not None and step==1:
                # Renderer-only warmup after the first counted physics step.
                for _ in range(6):
                    world.render()
                capture.capture('initial')
            if step==1 or step % max(1,args.physics_hz//20)==0:
                times.append(step/args.physics_hz)
                points=cloth.get_simulation_nodal_positions().detach().cpu().numpy()[0,:len(mesh.rest)].copy()
                if points.shape != mesh.rest.shape or not np.isfinite(points).all():
                    raise RuntimeError('Invalid native cloth telemetry')
                frames.append(points)
                velocities=cloth.get_simulation_nodal_velocities().detach().cpu().numpy()[0,:len(mesh.rest)]
                velocity_max=max(velocity_max,float(np.linalg.norm(velocities,axis=1).max()))
                if peg_view is not None:
                    peg_poses.append(peg_view.get_transforms().detach().cpu().numpy().copy())
                    peg_velocities.append(peg_view.get_velocities().detach().cpu().numpy().copy())
            if capture is not None and step and step % max(1,args.physics_hz//capture.fps)==0:
                capture.capture('final' if step==int(args.seconds*args.physics_hz) else None)
        frames=np.asarray(frames)
        np.savez_compressed(args.output/'nodes.npz',positions=frames,faces=mesh.faces,
                            rest=mesh.rest,initial=initial,times_s=np.asarray(times))
        if peg_view is not None:
            np.savez_compressed(args.output/'pegs.npz',poses_xyzw=np.asarray(peg_poses),
                                velocities=np.asarray(peg_velocities),times_s=np.asarray(times))
            report['final_peg_poses_xyzw']=peg_poses[-1].tolist()
            late=np.asarray(peg_velocities)[np.asarray(times)>=times[-1]-.5-1e-9]
            report['last_half_second_max_peg_linear_speed_m_s']=float(np.linalg.norm(late[:,:,:3],axis=-1).max())
            report['last_half_second_max_peg_angular_speed_rad_s']=float(np.linalg.norm(late[:,:,3:],axis=-1).max())
        final=frames[-1]
        strain=edge_strain(mesh.rest,final,mesh.faces)
        # Native dynamics diagnostics only: none is a task success score.
        report.update(max_nodal_speed_m_s=velocity_max,
                      max_transient_abs_edge_strain=float(max(np.abs(edge_strain(mesh.rest,f,mesh.faces)).max() for f in frames)))
        report.update(status='complete',phase='complete',mesh=mesh.audit(),frames=len(frames),
                      max_displacement_m=float(np.linalg.norm(final-initial,axis=1).max()),
                      final_z_min_m=float(final[:,2].min()),
                      final_z_max_m=float(final[:,2].max()),
                      final_z_range_m=float(np.ptp(final[:,2])),
                      max_abs_edge_strain=float(np.max(np.abs(strain))),
                      nodes_above_45cm=int(np.sum(final[:,2]>.45)),
                      validation='Requires visual and differential interpretation; no auto-pass.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
        print(report['traceback'],flush=True)
    finally:
        if capture is not None:
            report['rendering']=capture.close()
        report['wall_seconds']=time.monotonic()-started
        (args.output/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
        if world is not None:
            world.close()
        app.close()


if __name__=='__main__':
    main()
