"""Collect exactly one verified composite MP4 per requested robotics task.

Manifest is a JSON map from task slug to existing composite-video path.
No files are copied until every required preview exists and ffprobe validates
it. The destination contains videos only; logs and manifests stay elsewhere.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

TASKS=('spray-panel','carton-breakdown','carton-packing','ethernet-latch','hair-drying')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def collect(manifest,out,dry_run=False):
    sources=json.loads(manifest.read_text())
    if set(sources)!=set(TASKS):
        raise ValueError('manifest must contain exactly: '+', '.join(TASKS))
    plan=[];pending=[]
    for task in TASKS:
        source=Path(sources[task]).expanduser()
        if source.suffix.lower()!='.mp4' or not source.is_file():
            pending.append(task);continue
        response=subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=codec_name,pix_fmt,nb_frames:format=duration',
            '-of','json',str(source)],check=True,capture_output=True,text=True)
        info=json.loads(response.stdout)
        if not info['streams'] or float(info['format']['duration'])<=0:
            raise ValueError('empty or unplayable preview: '+task)
        stream=info['streams'][0]
        if stream['codec_name']!='h264' or stream.get('pix_fmt')!='yuv420p':
            raise ValueError('preview must be H.264/yuv420p: '+task)
        plan.append((task,source.resolve(),digest(source)))
    if pending:raise ValueError('previews not ready; no files copied: '+', '.join(pending))
    names={task+'.mp4' for task in TASKS}
    if out.exists() and any(p.name not in names for p in out.iterdir()):
        raise ValueError('destination has unrelated artifacts; choose a video-only folder')
    if not dry_run:
        out.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.preview-package-',dir=out.parent) as temp:
            stage=Path(temp)
            for task,source,expected in plan:
                dest=stage/(task+'.mp4');shutil.copy2(source,dest)
                if digest(dest)!=expected:raise ValueError('copy verification failed: '+task)
            out.mkdir(exist_ok=True)
            for task,_,_ in plan:(stage/(task+'.mp4')).replace(out/(task+'.mp4'))
    return dict(dry_run=dry_run,folder=str(out.resolve()),videos=[t+'.mp4' for t,_,_ in plan])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    try:print(json.dumps(collect(a.manifest,a.out,a.dry_run),indent=2))
    except (ValueError,OSError,subprocess.SubprocessError) as e:p.exit(1,str(e)+'\n')
