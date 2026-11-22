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

`task.json` gives dimensions, materials and layout. `geometry.py` supplies the entire generic assembly. It is a task proxy for a two-catch quick-release visor, not a claim of exact compatibility with a retail helmet. The inert shell is a solid ellipsoid with a dark face-opening mark; the unused face cavity and padding are omitted. The visor centre is rigid and its two end ears have passive compliance. The helmet begins bare and the replacement is unattached. Both hinge constraints start disabled. Their assembled rest frames agree at the 70-degree open position, independently of the loose visor’s starting pose.

Small snap-latch flex and insertion resistance are omitted. Local seating is approximated by enabling a finite-break-force hinge only when its hook is within 2.5 mm and 6 degrees of the mating base, at less than 80 mm/s. No object position is written. Seated plastic latches have finite translational/tilt compliance (4,000 N/m; 2 Nm/rad), bounded by 3 mm and 6 degrees. This prevents an instantaneous rigid-lock impulse at engagement; the original 80 N/1 Nm break limits remain. These are engineering estimates. The hinge has two passive detents; both energy wells are equal. Ear stiffness, detent stiffness and break thresholds are engineering estimates rather than calibrated commercial-part measurements. Both policies receive identical contacts, catches and fingers.

The replacement fingers have 40 × 10 × 1 mm steel contact faces on 100 × 10 × 2 mm stems, with silicone facing, 0.7 static/0.55 dynamic friction and 6 N jaw effort. They replace the factory finger meshes. The native link masses and inertia are retained as an approximation.

The [Nolan N87 manufacturer instructions](https://cdn6.louis.de/manual/ANL_21656300-Nolan-N87-Bedienungsanleitung.pdf), page 14, describe fitting the two sides and checking retention by opening and closing. This task uses that maintenance activity, but its generic hardware is not an exact N87 model. Removal of the old visor is outside the episode.

## Assets

Task geometry is generated here under the included MIT licence. The runtime supplies I2RT robot meshes under its [MIT asset licence](https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/assets/yam/LICENSE.i2rt). Table, floor and camera supports are runtime primitives. Robot assets are not redistributed here.
