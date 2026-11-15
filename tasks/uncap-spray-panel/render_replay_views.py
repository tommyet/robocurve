"""Render the three recorded cameras with Apple's local USD Storm renderer."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('replay', type=Path)
    parser.add_argument('--renderer', default='/usr/bin/usdrecord')
    args = parser.parse_args()
    folder = args.replay.resolve()
    manifest = json.loads((folder / 'replay-output-manifest.json').read_text())
    scene = folder / manifest['usd_file']
    if hashlib.sha256(scene.read_bytes()).hexdigest() != manifest['usd_sha256']:
        raise ValueError('replay scene changed after manifest was written')
    if manifest['native_rtx_capture'] or manifest['diagnostic']:
        raise ValueError('completed preview requires the audited, non-diagnostic replay')
    if manifest['first_frame'] != 0 or manifest['frames'] != manifest['last_frame'] + 1:
        raise ValueError('invalid recorded frame range')
    for name in ('top_cam', 'left_cam', 'right_cam'):
        output = folder / 'frames' / name
        output.mkdir(parents=True, exist_ok=False)
        # Apple USD's fractional placeholder avoids scientific notation for
        # integer frame numbers >=1000. Only exact integer samples are rendered.
        command = [args.renderer, '--renderer', 'Storm', '--frames',
                   f"0:{manifest['last_frame']}", '--imageWidth', '320',
                   '--camera', manifest['cameras'][name], str(scene),
                   str(output / 'frame-####.#########.png')]
        with (folder / f'render-{name}.log').open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        files = sorted(output.glob('frame-*.png'))
        if len(files) != manifest['frames'] or any(
                int(path.stem.rsplit('-', 1)[1]) != i for i, path in enumerate(files)):
            raise ValueError('rendered frame sequence is incomplete: ' + name)
        print(f'{name}: {len(files)} exact recorded frames', flush=True)


if __name__ == '__main__':
    main()
