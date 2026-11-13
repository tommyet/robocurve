"""CPU/native-device equivalence check for the optional fused predicate.

This runs geometry calculations only, not Isaac physics or task demonstrations.
Use --device cuda:0 only in the orchestrator's authorized existing GPU queue.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def reference(points,faces,segments,old_points=None,old_segments=None):
    from contact_audit import _hits
    triangles=np.asarray(points)[faces]
    ns,nf=len(segments),len(faces)
    current=np.broadcast_to(triangles,(ns,nf,3,3)).reshape(-1,3,3)
    starts=np.broadcast_to(segments[:,None,0],(ns,nf,3)).reshape(-1,3)
    ends=np.broadcast_to(segments[:,None,1],(ns,nf,3)).reshape(-1,3)
    low,high=segments.min(1),segments.max(1)
    tl,th=triangles.min(1),triangles.max(1)
    static=_hits(starts,ends,current).reshape(ns,nf)
    swept=np.zeros_like(static)
    if old_points is not None:
        old_triangles=np.asarray(old_points)[faces]
        old=np.broadcast_to(old_triangles,(ns,nf,3,3)).reshape(-1,3,3)
        delta=current[:,0]-old[:,0]
        for endpoint in (0,1):
            a=np.broadcast_to(old_segments[:,None,endpoint],(ns,nf,3)).reshape(-1,3)
            b=np.broadcast_to(segments[:,None,endpoint],(ns,nf,3)).reshape(-1,3)
            swept|=(_hits(a,b-delta,old)|_hits(a+delta,b,current)).reshape(ns,nf)
        low=np.minimum(low,old_segments.min(1));high=np.maximum(high,old_segments.max(1))
        tl=np.minimum(tl,old_triangles.min(1));th=np.maximum(th,old_triangles.max(1))
    broad=np.all((high[:,None]>=tl[None]-1e-10)&(low[:,None]<=th[None]+1e-10),axis=2)
    return (static.astype(np.int32)+2*swept.astype(np.int32))*broad


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device',default='cpu');p.add_argument('--out',type=Path,required=True)
    p.add_argument('--cache',type=Path);p.add_argument('--cases',type=int,default=200)
    p.add_argument('--benchmark',action='store_true',help='Time 50 persistent-buffer passes over both full refined meshes')
    a=p.parse_args()
    if not 1<=a.cases<=1000:p.error('Use 1–1000 cases')
    import warp as wp
    if a.cache:wp.config.kernel_cache_dir=str(a.cache)
    from warp_contact import crossing_matrix
    rng=np.random.default_rng(231119)
    mismatches=[];checks=0;pair_tests=0;start=time.perf_counter()
    def check(points,faces,segments,op=None,os=None,label=''):
        nonlocal checks,pair_tests
        expected=reference(points,faces,segments,op,os)
        actual,latch=crossing_matrix(points,faces,segments,previous_points=op,previous_segments=os,device=a.device)
        checks+=1;pair_tests+=actual.size
        if not np.array_equal(actual,expected) or (latch==1)!=bool(expected.any()):
            mismatches.append({'label':label,'different_pairs':int(np.count_nonzero(actual!=expected)),
                               'latch':latch,'expected_failure':bool(expected.any())})
    for i in range(a.cases):
        scale=10**rng.uniform(-5,-2)
        points=rng.normal(size=(60,3))*scale;faces=np.arange(60).reshape(-1,3)
        segments=rng.normal(size=(28,2,3))*scale
        check(points,faces,segments,label=f'random-static-{i}')
        check(points+rng.normal(size=points.shape)*scale*.1,faces,
              segments+rng.normal(size=segments.shape)*scale*.1,points,segments,f'random-swept-{i}')
    # Grazing triangle boundaries, segment endpoints, nearly parallel paths,
    # submillimetre faces, and cloth moving through a stationary segment.
    for scale in (1e-5,2e-4,.002):
        points=np.array(((0.,0.,0.),(scale,0.,0.),(0.,scale/4,0.)))
        faces=np.array(((0,1,2),))
        for eps in (-2e-7,-1e-7,-.5e-7,0.,.5e-7,1e-7,2e-7):
            x=scale*eps
            segment=np.array((((x,scale/16,-scale),(x,scale/16,scale)),))
            check(points,faces,segment,label=f'edge-{scale}-{eps}')
            check(points,faces,segment*[-1,1,eps],label=f'parallel-{scale}-{eps}')
        edge=np.array((((scale/4,scale/16,scale/10),(scale/2,scale/16,scale/10)),))
        check(points+[0,0,scale/5],faces,edge,points,edge,f'moving-cloth-{scale}')
    report={'status':'pass' if not mismatches else 'fail','native_physics_run':False,
            'warp_version':wp.__version__,'device':a.device,'seed':231119,'checks':checks,
            'pair_tests':pair_tests,'mismatches':mismatches,'wall_seconds':time.perf_counter()-start,
            'source_sha256':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest()
                for n in ('warp_contact.py','contact_audit.py','check_warp_contact.py')},
            'scope':'Standalone predicate equivalence only; GPU runner integration and first-failure snapshots remain unvalidated.'}
    from geometry import Mesh
    from warp_contact import PersistentCrossingAudit
    triangle=np.array(((0.,0.,0.),(1.,0.,0.),(0.,1.,0.)))
    mesh=Mesh(triangle,np.array(((0,1,2),)))
    segment=np.array((((.2,.2,.1),(.3,.2,.1)),))
    persistent=PersistentCrossingAudit([mesh,mesh],1,.01,device=a.device)
    persistent.update([triangle,triangle],segment,0)
    initial_valid=all(s['valid'] for s in persistent.summaries())
    persistent.update([triangle+[0,0,.2],triangle],segment,1)
    persistent.update([triangle+[0,0,.3],triangle],segment,2)
    summaries=persistent.summaries()
    snapshot_ok=(initial_valid and not summaries[0]['valid'] and summaries[1]['valid'] and
        summaries[0]['first_failure']['native_substep']==1 and
        np.array_equal(persistent.failure_pair['previous_left'],triangle) and
        np.array_equal(persistent.failure_pair['current_left'],triangle+[0,0,.2]))
    report['persistent_first_failure_snapshot_passed']=bool(snapshot_ok)
    if not snapshot_ok:
        report['status']='fail';mismatches.append({'label':'persistent-first-failure-snapshot'})
    if a.benchmark:
        from geometry import patch,stitch_loop,STITCH_Y
        from warp_contact import crossing_kernel
        segments=np.concatenate([np.stack((stitch_loop(y),np.roll(stitch_loop(y),-1,axis=0)),axis=1) for y in STITCH_Y])
        seg=wp.array(segments,dtype=wp.vec3d,device=a.device)
        buffers=[]
        for left in (True,False):
            mesh=patch(left,hole_half=.0008,hole_mesh_spacing=.0004)
            points=wp.array(mesh.rest,dtype=wp.vec3d,device=a.device)
            faces=wp.array(mesh.faces.astype(np.int32),dtype=wp.vec3i,device=a.device)
            latch=wp.full(1,2**31-1,dtype=wp.int32,device=a.device)
            mask=wp.zeros((len(segments),len(mesh.faces)),dtype=wp.int32,device=a.device)
            args=[points,points,faces,seg,seg,1,1,latch,mask]
            buffers.append((args,mask.shape))
            wp.launch(crossing_kernel,dim=mask.shape,inputs=args,device=a.device)
        wp.synchronize_device(a.device)
        begin=time.perf_counter()
        for _ in range(50):
            for args,shape in buffers:wp.launch(crossing_kernel,dim=shape,inputs=args,device=a.device)
        wp.synchronize_device(a.device)
        report['full_mesh_benchmark']={'repeats':50,'faces_per_patch':len(mesh.faces),'segments':len(segments),
            'seconds_per_pair_step':(time.perf_counter()-begin)/50,
            'initial_scene_crossings':sum(int(np.count_nonzero(args[-1].numpy())) for args,_ in buffers),
            'scope':'Persistent-buffer kernel and launch timing only; excludes scene stepping, tensor preparation, damage and strain audits.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if mismatches:raise SystemExit(1)


if __name__=='__main__':main()
