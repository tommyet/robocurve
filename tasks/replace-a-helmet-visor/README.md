# Replace a helmet visor

Development: native demo validation is still in progress. Do not submit yet.

Release a curved visor from two spaced catches, install its replacement and check that it opens and closes while retained. The shell is fixed to an ordinary display base.

## Run and score

Use the pinned NVIDIA Linux Isaac/YAM environment in `ENVIRONMENT.json`, or install with `bash bootstrap.sh`. From this folder:

```bash
python run.py --mode demo --out /absolute/path/to/demo
python run.py --mode dream --out /absolute/path/to/dream
python rescore.py /absolute/path/to/demo
```

The limit is 2,400 controls at 20 Hz (120 simulated seconds). Runtime and final scores are pending native validation. There is one fixed layout and no random seed.

Broken parts invalidate the trial. Award the highest stage reached: 0.25 for releasing the original from both catches, 0.5 for retaining the replacement at one catch, and 0.75 for both catches. Full credit additionally requires closing to within 8 degrees, reopening at least 55 degrees, placing the original on the tray and releasing both hands for 2 seconds with the replacement still retained. Catch engagement is visible through retention during the movement; no hidden force threshold is needed for physical judging.

## Setup and approximation

`task.json` gives dimensions, materials and layout. `geometry.py` supplies the entire generic assembly. It is a task proxy for a two-catch quick-release visor, not a claim of exact compatibility with a retail helmet. The inert shell is a solid ellipsoid; the unused face opening and padding are omitted. The visor centre is rigid and its two end ears have passive compliance. The original begins at 70 degrees with both native hinges engaged. The spare is unattached.

Each release trigger has 4 mm travel and 650 N/m stiffness; pressing beyond 2.8 mm releases its catch. Local insertion is approximated by enabling a hinge only when its hook is within 2.5 mm and 6 degrees of the mating base, at less than 80 mm/s. No object position is written. The hinge has two passive detents; both energy wells are equal. Ear stiffness, detent stiffness and break thresholds are engineering estimates rather than calibrated commercial-part measurements. Both policies receive identical contacts, catches and fingers.

The replacement fingers have 40 × 10 × 1 mm steel contact faces on 100 × 10 × 2 mm stems, with silicone facing, 0.7 static/0.55 dynamic friction and 6 N jaw effort. They replace the factory finger meshes. The native link masses and inertia are retained as an approximation.

## Assets

Task geometry is generated here under the included MIT licence. The runtime supplies I2RT robot meshes under its [MIT asset licence](https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/assets/yam/LICENSE.i2rt). Table, floor and camera supports are runtime primitives. Robot assets are not redistributed here.
