# Peel a baking cup off a muffin

Peel the silicone baking cup off the muffin without breaking it. Leave the muffin and cup separate on the tray.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

Removing a reusable baking cup requires peeling the flexible cup while supporting a fragile muffin.

## Setup and reset

One cooled plain muffin, about 65 mm across and 60 mm high, still inside a 52 mm base-diameter, 40 mm high silicone baking cup; a 320 x 280 mm tray. The cup is fully seated and has not been loosened. Both hands start open. Use clean removable food-safe pad covers.

Use plain muffins from one batch, cooled to 18–22 °C in the same washed and dried cup model. Use a fresh muffin each trial and do not pre-peel or oil the cup. Inspect the cup for tears and wash the tray and removable covers between trials.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if the cup is completely off and the intact muffin and cup rest separately on the tray after three seconds with both hands clear. 0.5 if at least three quarters of the cup wall is peeled away; 0.25 for at least half. Otherwise 0. A torn cup, split muffin or detached muffin piece larger than 5 mm scores 0. Judge from close views and a ruler.

## Simulation and limits

Native muffin, flexible jointed cup walls and robot contacts. Adhesion joints resist removal and break through physical peeling loads. The muffin has damageable crust pieces; the cup can tear. There are no pose-following objects or proximity grasps. Silicone, crumb strength and adhesion are coarse uncalibrated approximations. Native feasibility has not yet been validated.

Ordinary reusable silicone baking cups provide the physical target, for example https://www.oxo.com/oxo-gg-silicone-baking-cups-blister.html . The simulation resolves passive folding and peeling resistance rather than releasing the muffin when a hand reaches a particular angle. Native grading and all final dimensions must be checked against the demonstrated trial.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
python tasks/peel-a-silicone-baking-cup/make_plan.py
OMNI_KIT_ACCEPT_EULA=YES python tasks/peel-a-silicone-baking-cup/run.py --mode demo --out /tmp/peel-a-silicone-baking-cup-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/peel-a-silicone-baking-cup/run.py --mode dream --out /tmp/peel-a-silicone-baking-cup-dream
```

Rescore recorded native body poses with `python tasks/peel-a-silicone-baking-cup/rescore.py /tmp/peel-a-silicone-baking-cup-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 1,000 control steps (50 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.
