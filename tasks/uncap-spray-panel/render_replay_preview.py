"""Combine all three exact-frame offline USD views into one labelled preview."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture',type=Path)
    parser.add_argument('replay',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    import cv2
    import numpy as np
    capture=args.capture;replay=args.replay
    manifest=json.loads((replay/'replay-output-manifest.json').read_text())
    data=(capture/'trajectory.jsonl').read_bytes()
    rows=[json.loads(line) for line in data.splitlines()]
    audit=json.loads((capture/'audit.json').read_text())
    summary=json.loads((capture/'score-summary.json').read_text())
    if (manifest['diagnostic'] or manifest['native_rtx_capture'] or
        manifest['trace_sha256']!=hashlib.sha256(data).hexdigest() or
        summary['score']!=1 or rows[-1]['metrics']['score']!=1 or
        not audit.get('passed') or audit.get('score')!=1 or audit.get('trace_sha256')!=manifest['trace_sha256'] or
        audit.get('samples')!=len(rows) or manifest['frames']!=len(rows)):
        raise ValueError('preview requires a complete, audited, matching offline physics replay')
    names=('top_cam','left_cam','right_cam')
    cameras={name:sorted((replay/'frames'/name).glob('frame-*.png')) for name in names}
    for name,files in cameras.items():
        if len(files)!=len(rows) or any(int(path.stem.rsplit('-',1)[1])!=i for i,path in enumerate(files)):
            raise ValueError('missing, extra or misaligned rendered frames: '+name)
    width,height=320,176
    output=args.output or replay/'complete-physics-replay.mp4'
    command=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo',
             '-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{2*width}x{3*height+72}',
             '-r','20','-i','-','-an','-c:v','libx264','-crf','20',
             '-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for i,row in enumerate(rows):
            images={}
            for name in names:
                image=cv2.imread(str(cameras[name][i]),cv2.IMREAD_COLOR)
                if image is None:raise ValueError('unreadable frame: '+str(cameras[name][i]))
                images[name]=cv2.cvtColor(cv2.resize(image,(width,height)),cv2.COLOR_BGR2RGB)
            scene=cv2.resize(images['top_cam'],(2*width,2*height))
            wrists=np.concatenate([images['left_cam'],images['right_cam']],axis=1)
            title=np.zeros((48,2*width,3),dtype=np.uint8)
            cv2.putText(title,'SCRIPTED PHYSICS REPLAY - MEASURED FULL SCORE',(8,18),
                        cv2.FONT_HERSHEY_SIMPLEX,.45,(255,255,255),1)
            cv2.putText(title,'Recorded native poses; offline USD rendering, normalized lighting',(8,38),
                        cv2.FONT_HERSHEY_SIMPLEX,.36,(220,220,220),1)
            footer=np.zeros((24,2*width,3),dtype=np.uint8);m=row['metrics']
            text=f"{row['time']:.2f}s  score {m['score']:.2f}  coverage {m['coverage']:.0%}  overspray {m['overspray']:.1%}"
            cv2.putText(footer,text,(8,17),cv2.FONT_HERSHEY_SIMPLEX,.44,(255,255,255),1)
            process.stdin.write(np.concatenate([title,scene,wrists,footer],axis=0).tobytes())
        process.stdin.close()
        if process.wait()!=0:raise RuntimeError('composite encoding failed')
    except BaseException:
        process.kill();process.wait();raise
    metadata=dict(frames=len(rows),fps=20,measured_score=summary['score'],
                  offline_physics_replay=True,native_rtx_capture=False,
                  trace_sha256=manifest['trace_sha256'],source_views=list(names),
                  appearance=manifest['appearance'],preview_light_scale=manifest['preview_light_scale'])
    (replay/'preview-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(output)


if __name__=='__main__':main()
