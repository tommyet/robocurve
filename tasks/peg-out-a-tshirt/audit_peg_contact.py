"""Offline full-triangle cloth/jaw overlap check, not a fastening classifier.

Uses recorded dynamic jaw poses and the frozen authoring geometry. Contact,
retention and line capture still require the native videos and released hold.
"""
import argparse,ast,gzip,hashlib,json
from pathlib import Path
import numpy as np
from interpret_motion import rotation_xyzw
from fixture_clearance import fixture_intersections


def verify_jaw_source(path):
    tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='author_peg_jaw')
    calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='author_box']
    sizes=[ast.literal_eval(c.args[2]) for c in calls]
    if sizes!=[(.035,.010,.006),(.035,.010,.006)]:raise ValueError('Frozen jaw shapes differ from this diagnostic')
    positions=[ast.unparse(c.args[3]) for c in calls]
    if positions!=['(0.0175, 0.0, sign * 0.0035)','(-0.0175, 0.0, sign * 0.008)']:
        raise ValueError('Frozen jaw offsets differ from this diagnostic: '+repr(positions))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trial',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--every',type=int,default=100);p.add_argument('--shrink',type=float,default=.0002)
    args=p.parse_args();source=args.trial/'task-source/native_cloth.py';verify_jaw_source(source)
    meshes=json.loads((args.trial/'meshes.json').read_text());faces=np.asarray(meshes['tshirt']['faces'])
    plan=json.loads((args.trial/'task-source/fixed-motion.json').read_text());frames=plan['frames']
    endpoints={i+1 for i,f in enumerate(frames) if i==len(frames)-1 or f['stage']!=frames[i+1]['stage']};samples=[]
    with gzip.open(args.trial/'trace.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line);step=row['step']
            if step%args.every and step not in endpoints:continue
            from trace_data import cloth_array
            nodes=cloth_array(args.trial,row,'tshirt');hits={}
            for side in ('left_peg','right_peg'):
                poses=np.asarray(row['objects'][side]['body_poses'])
                for index,label in enumerate(('lower','upper')):
                    sign=-1 if index==0 else 1;pose=poses[index];r=rotation_xyzw(pose[3:]);local=(nodes-pose[:3])@r
                    shapes={side+':'+label+':jaw':dict(kind='box',size=(.035,.010,.006),center=(.0175,0.,sign*.0035)),
                            side+':'+label+':handle':dict(kind='box',size=(.035,.010,.006),center=(-.0175,0.,sign*.008))}
                    hits.update(fixture_intersections(local,faces,shapes,margin=-args.shrink))
            samples.append(dict(step=step,intersecting_faces_by_shape={k:v for k,v in hits.items() if v}))
    out=dict(kind='offline_native_cloth_jaw_integrity_check',shrink_m=args.shrink,samples=samples,score=None,
        trace_sha256=hashlib.sha256((args.trial/'trace.jsonl.gz').read_bytes()).hexdigest(),jaw_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        limitation='Discrete recorded states only, not a contact, grasp, fastening, damage or task-success classifier.')
    args.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(samples=len(samples),overlap_samples=sum(bool(s['intersecting_faces_by_shape']) for s in samples)),indent=2))


if __name__=='__main__':main()
