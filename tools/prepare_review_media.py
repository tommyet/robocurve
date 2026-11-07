"""Make Inspect camera exports readable by the frozen task video renderer.

After exporting all three policy views at 20 fps, run:
  python tools/prepare_review_media.py RUN --dry-run
  python tools/prepare_review_media.py --run-dir RUN
  python tasks/TASK/render_review.py RUN --output RUN/complete.mp4

Old *_top_cam.mp4 names are already compatible. For Inspect 1.0 exports named
*~top_cam.mp4 (and left_cam/right_cam), create relative *_top_cam.mp4 symlinks
in RUN/media. All cameras must be unambiguous before any links are created.
Existing files are never overwritten; rerunning is safe. This checks names and
file targets only, without decoding, copying or re-encoding video.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CAMERAS = ('top_cam', 'left_cam', 'right_cam')


def plan_aliases(run_dir):
    media = (Path(run_dir)/'media').resolve(strict=True)
    if not media.is_dir():
        raise ValueError('RUN/media must be a directory')
    plan = []
    for camera in CAMERAS:
        old = sorted(media.glob(f'*_{camera}.mp4'))
        new = sorted(media.glob(f'*~{camera}.mp4'))
        if len(old) > 1 or len(new) > 1 or not (old or new):
            raise ValueError(f'{camera}: expected one unambiguous export; found {len(old)} old and {len(new)} new names')
        for candidate in old+new:
            if not candidate.is_file() or candidate.resolve().parent != media:
                raise ValueError(f'{camera}: export must resolve to a file within RUN/media')
        if old:
            if new and not old[0].samefile(new[0]):
                raise ValueError(f'{camera}: old and new names identify different files')
            plan.append((camera, old[0], None))
        else:
            source = new[0]
            alias = media/(source.name[:-len(f'~{camera}.mp4')]+f'_{camera}.mp4')
            if alias.exists() or alias.is_symlink():
                raise FileExistsError(f'{camera}: alias path is already occupied')
            plan.append((camera, alias, source))
    return plan


def prepare(run_dir, *, dry_run=False):
    plan = plan_aliases(run_dir)
    created = []
    try:
        if not dry_run:
            for _, alias, source in plan:
                if source is not None:
                    alias.symlink_to(source.name)  # Relative, same-directory target; creation is exclusive.
                    created.append((alias, source.name))
            plan_aliases(run_dir)  # Catch a concurrent export or changed target.
    except Exception:
        for alias, target in reversed(created):
            if alias.is_symlink() and alias.readlink() == Path(target):
                alias.unlink()
        raise
    return {'dry_run': dry_run, 'cameras': {
        camera: {'file': alias.name, 'source': source.name if source else alias.name,
                 'action': ('would_create' if dry_run else 'created') if source else 'ready'}
        for camera, alias, source in plan}}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('run_dir', nargs='?', type=Path)
    parser.add_argument('--run-dir', dest='named_run_dir', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if (args.run_dir is None) == (args.named_run_dir is None):
        parser.error('provide a run directory either positionally or with --run-dir')
    try:
        result = prepare(args.run_dir or args.named_run_dir, dry_run=args.dry_run)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Cannot prepare review media: {exc}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
