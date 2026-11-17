# Remove an avocado stone

Remove the stone from the avocado half without crushing the flesh, and put the stone in the waste dish.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

Removing a stubborn avocado stone calls for a firm grip on the stone while protecting the soft flesh.

## Setup and reset

One firm-ripe Hass avocado half, about 100 x 65 x 35 mm, cut-side up with its 35–40 mm stone still attached; a 300 x 240 x 18 mm wooden chopping board; and a 110 mm diameter, 24 mm deep waste dish. The fruit is centred on the board, with its narrow end toward the left arm. The dish is 180 mm toward the right arm. Both hands start open. Use clean removable food-safe pad covers.

Use a fresh firm-ripe Hass half at 18–22 °C, cut immediately before a trial. Reject visibly overripe, split or already loose-stoned halves. Use a single grocery batch and record size/ripeness. Clean the board, dish and removable covers between trials.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if the stone is fully removed and rests in the waste dish, the avocado remains intact on the board, and both hands have released for three seconds. 0.5 if the intact stone is fully clear of the fruit but not yet released in the dish. Otherwise 0. A torn skin or crushed/torn flesh patch larger than 1 cm² scores 0. Use the final video and a ruler beside the fruit.

## Simulation and limits

Native colliding fruit, stone, dish and robot fingers. Passive bonds resist stone extraction and allow the flesh to break under excessive load; no object is attached to a hand. The fruit is a coarse assembly rather than a deformable tissue model. Its 7 N extraction and 12 N flesh-bond thresholds are engineering estimates, not measurements. Native feasibility has not yet been validated.

The fixed scene coordinates and mass/contact parameters are in geometry.py. The pit bond can break through actual force or torque; a loose decorative sphere is not substituted. Physical photographs should show the skin and flesh before and after extraction. Native scoring must still be reconciled with the stated flesh-damage area before submission.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
python tasks/remove-an-avocado-stone/make_plan.py
OMNI_KIT_ACCEPT_EULA=YES python tasks/remove-an-avocado-stone/run.py --mode demo --out /tmp/remove-an-avocado-stone-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/remove-an-avocado-stone/run.py --mode dream --out /tmp/remove-an-avocado-stone-dream
```

Rescore recorded native body poses with `python tasks/remove-an-avocado-stone/rescore.py /tmp/remove-an-avocado-stone-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 800 control steps (40 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.
