# Strip a kale leaf from its stalk

Strip the kale leaf from its tough stalk. Leave the usable leaf on the board and the stalk separate.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

Preparing kale means separating edible leaf tissue from its fibrous stalk without throwing the leaf away with it.

## Setup and reset

One fresh kale leaf, about 270 mm long and 80 mm wide, with a 5–6 mm stalk and 45 mm of bare stalk at its base; a 320 x 340 x 20 mm wooden chopping board. The leaf lies flat, stalk base toward the left arm, tip toward the right. Both hands start open. Use washable food-safe pad covers.

Choose fresh mature curly kale from one batch, 250–290 mm long, with an intact stalk and no missing leaf patches. Trim the bare stalk to 45 mm; wash and pat dry. Photograph it on the grid, then restore the fixed layout. Use a fresh leaf each trial.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if at least 90% of the leaf area has been stripped and retained on the board, the intact stalk is at least 2 cm clear of the leaf, and both hands have released for three seconds. 0.5 for at least 75% stripped and retained; 0.25 for at least 50% stripped and retained on the board. Otherwise 0. A broken stalk mixed into the leaf scores 0. Compare before/after photographs on a centimetre grid.

## Simulation and limits

Native contact grips a jointed stalk and flexible leaf panels. Weaker leaf-to-stalk bonds break under load; the leaf remains physical matter and falls or stays in the grippers. Stronger stalk and leaf seams can also fail. Geometry, stiffness and tear loads are coarse uncalibrated approximations. Native feasibility has not yet been validated.

Partial credit measures the result rather than the distance a hand moved. The native draft weights patches by their original area. For real judging, spread detached pieces beside the starting photograph and count occupied grid squares. All leaf pieces, including scraps, remain in the scene.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
python tasks/strip-a-kale-leaf/make_plan.py
OMNI_KIT_ACCEPT_EULA=YES python tasks/strip-a-kale-leaf/run.py --mode demo --out /tmp/strip-a-kale-leaf-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/strip-a-kale-leaf/run.py --mode dream --out /tmp/strip-a-kale-leaf-dream
```

Rescore recorded native body poses with `python tasks/strip-a-kale-leaf/rescore.py /tmp/strip-a-kale-leaf-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 800 control steps (40 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.
