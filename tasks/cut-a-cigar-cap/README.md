# Cut a cigar cap cleanly

Cut the cap cleanly from the unlit cigar without splitting or unwrapping it.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

Preparing a cigar calls for placing the cut at its cap and closing the cutter without crushing or loosening the wrapper.

## Setup and reset

One unlit, capped corona-size cigar, 138 mm long and about 18.5 mm diameter; an open ordinary double-guillotine cutter with a 24 mm aperture; a 320 x 340 x 20 mm wooden board; and a small waste dish. The cigar and cutter start separate on the board. Both hands start open. Use replaceable protective covers so failed cuts cannot reach the original gripper pads.

Use intact capped cigars of one size and batch, kept in their packaging with a 69% humidity pack at 18–22 °C. Use a new cigar for each trial. Inspect the cutter edge, wrapper and protective covers; restore the open cutter and fixed layout. No lighting or smoking is part of the task.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if the cap is fully separated in one clean cut, the wrapper has no visible split or loose flap over 2 mm, and the cigar is released intact on the board for three seconds. 0.5 for the same clean separation while the cigar is still held. Otherwise 0. Inspect the cut face and wrapper in close photographs with a ruler; cutting work alone earns no credit.

## Simulation and limits

Native cutter, sliding blades, cigar, wrapper sectors and finger contacts. An analytic blade-cap material contact applies opposing forces and equal reactions in PhysX; both blades must travel through the cap under load before it separates. The rest retains native collisions. Wrapper compression can fail the trial. Cutting resistance and wrapper strength are uncalibrated. Native feasibility has not yet been validated.

A conventional cutter is the target: https://colibri.com/collections/all-products/products/cut-color-blades . The geometry is a generic straight double-guillotine approximation, not a dimensional scan of that product. The real mechanism, required cutting load and protective covers must be checked before submission. Societal relatability is a material acceptance risk because cigar preparation is a niche activity.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
python tasks/cut-a-cigar-cap/make_plan.py
OMNI_KIT_ACCEPT_EULA=YES python tasks/cut-a-cigar-cap/run.py --mode demo --out /tmp/cut-a-cigar-cap-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/cut-a-cigar-cap/run.py --mode dream --out /tmp/cut-a-cigar-cap-dream
```

Rescore recorded native body poses with `python tasks/cut-a-cigar-cap/rescore.py /tmp/cut-a-cigar-cap-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 1,000 control steps (50 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.
