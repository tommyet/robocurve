"""Render all synchronized native cameras, explicitly labelled diagnostic."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path)
    args=p.parse_args()
    import cv2
    import numpy as np
    import imageio_ffmpeg
    cameras={name:sorted(args.run.glob('frames/**/*'+name+'_*.npy'))
             for name in ('top_cam','left_cam','right_cam')}
    counts={k:len(v) for k,v in cameras.items()}
    if not counts['top_cam'] or len(set(counts.values()))!=1:
        raise RuntimeError('missing or unaligned camera frames: '+str(counts))
    first=np.load(cameras['top_cam'][0]);h,w=first.shape[:2]
    output=args.run/'diagnostic-preview.mp4'
    command=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error',
             '-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24',
             '-s',f'{2*w}x{3*h+24}','-r','20','-i','-',
             '-an','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',
             '-movflags','+faststart',str(output)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    for index in range(counts['top_cam']):
        imgs={k:np.load(v[index]) for k,v in cameras.items()}
        scene=cv2.resize(imgs['top_cam'],(2*w,2*h))
        lower=np.concatenate([imgs['left_cam'],imgs['right_cam']],axis=1)
        title=np.zeros((24,2*w,3),dtype=np.uint8)
        cv2.putText(title,'PROTOTYPE DIAGNOSTIC - NOT A SPRAYING DEMO',(8,17),
                    cv2.FONT_HERSHEY_SIMPLEX,.46,(255,255,255),1)
        proc.stdin.write(np.concatenate([title,scene,lower],axis=0).tobytes())
        if index in (0,counts['top_cam']-1):
            for name,img in imgs.items():
                cv2.imwrite(str(args.run/f'{name}-{index:06d}.png'),cv2.cvtColor(img,cv2.COLOR_RGB2BGR))
    proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError('encoder failed')
    (args.run/'preview-metadata.json').write_text(json.dumps(dict(
        cameras=counts,frames=counts['top_cam'],fps=20,diagnostic=True,successful_spray_demo=False),indent=2))
    print(output)

if __name__=='__main__':main()
