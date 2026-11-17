# Mash cooked potato

Mash the cooked potato in the bowl until no large lumps remain. Keep the potato in the bowl.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

Mashing cooked potato requires loaded pressing across the bowl, breaking down the pieces while keeping the food contained.

## Setup and reset

About 60 g of peeled cooked potato in twelve 21–22 mm pieces; a 200 mm inside-diameter, 75 mm deep bowl; and an ordinary wire masher with a 75 x 60 mm head and a 180 mm handle. The bowl is centred between the arms; the masher stands on its head 170 mm toward the right arm. Both hands start open. Use removable food-safe pad covers and a washable tray beneath the bowl.

Use peeled floury potato from one batch, cut into 21–22 mm pieces, boiled until a fork passes through easily, then drained and cooled to 18–22 °C. Weigh 60 ± 5 g per trial. Add no milk, butter or oil. Use fresh cooked pieces and clean the tool, bowl, tray and covers between trials.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if at least 95% of the retained potato has no lumps larger than 9 mm, at least 95% of the starting mass stays in the bowl, and both hands have released for three seconds. 0.5 for at least 75% reduced to that size; 0.25 for at least 50%. Otherwise 0. Losing over 5% of the potato scores 0. Weigh the retained food and inspect it spread on a 9 mm reference grid.

## Simulation and limits

Native wire masher, bowl, robot contacts and cohesive potato clusters. Force-limited internal bonds break under real tool loading; released particles remain physical objects. The score measures remaining connected lump size and retained mass, not press count or tool travel. This approximates breakup rather than smooth potato rheology. Native feasibility has not yet been validated.

The primary novelty risk is SPARTA food mashing (https://arxiv.org/html/2509.24129v2). This proposal includes native tool pickup, loaded three-dimensional pressing and retained-lump judging, but that does not guarantee an originality pass. No novelty or acceptance claim is made from a changed food name alone. Physical preparation and the proposed 9 mm texture criterion need to agree with the native demonstration.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
python tasks/mash-cooked-potato/make_plan.py
OMNI_KIT_ACCEPT_EULA=YES python tasks/mash-cooked-potato/run.py --mode demo --out /tmp/mash-cooked-potato-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/mash-cooked-potato/run.py --mode dream --out /tmp/mash-cooked-potato-dream
```

Rescore recorded native body poses with `python tasks/mash-cooked-potato/rescore.py /tmp/mash-cooked-potato-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 2,400 control steps (120 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.
