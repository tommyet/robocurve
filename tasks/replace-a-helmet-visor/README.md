# Fit a replacement helmet visor

Development: native demo validation is still in progress. Do not submit yet.

Fit a curved replacement visor to two spaced catches and check that it opens and closes while retained. The old visor has already been removed. The shell is fixed to an ordinary display base.

## Run and score

Use the pinned NVIDIA Linux Isaac/YAM environment in `ENVIRONMENT.json`, or install with `bash bootstrap.sh`. From this folder:

```bash
python run.py --mode demo --out /absolute/path/to/demo
python run.py --mode dream --out /absolute/path/to/dream
python rescore.py /absolute/path/to/demo
```

The limit is 1,600 controls at 20 Hz (80 simulated seconds). Runtime and final scores are pending native validation. There is one fixed layout and no random seed.

Broken parts score zero. Otherwise award the highest applicable score: 0.25 for one engaged catch; 0.5 for both; 0.75 for closing the attached visor to within 8° of shut. Full score also requires reopening it by at least 55° and releasing both hands for two seconds with both catches still engaged. Other outcomes score zero. Check retention and travel in the video using a simple angle template.

## Setup and approximation

`task.json` gives dimensions, materials and layout. `geometry.py` supplies the entire generic assembly. It is a task proxy for a two-catch quick-release visor, not a claim of exact compatibility with a retail helmet. The inert shell is a solid ellipsoid; the unused face opening and padding are omitted. The visor centre is rigid and its two end ears have passive compliance. The helmet begins bare and the replacement is unattached. Both hinge constraints start disabled. Their assembled rest frames agree at the 70-degree open position, independently of the loose visor’s starting pose.

Each release trigger has 4 mm travel and 650 N/m stiffness; pressing beyond 2.8 mm releases its catch. Local insertion is approximated by enabling a hinge only when its hook is within 2.5 mm and 6 degrees of the mating base, at less than 80 mm/s. No object position is written. The hinge has two passive detents; both energy wells are equal. Ear stiffness, detent stiffness and break thresholds are engineering estimates rather than calibrated commercial-part measurements. Both policies receive identical contacts, catches and fingers.

The replacement fingers have 40 × 10 × 1 mm steel contact faces on 100 × 10 × 2 mm stems, with silicone facing, 0.7 static/0.55 dynamic friction and 6 N jaw effort. They replace the factory finger meshes. The native link masses and inertia are retained as an approximation.

## Assets

Task geometry is generated here under the included MIT licence. The runtime supplies I2RT robot meshes under its [MIT asset licence](https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/assets/yam/LICENSE.i2rt). Table, floor and camera supports are runtime primitives. Robot assets are not redistributed here.
