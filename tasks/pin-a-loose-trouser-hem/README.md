# Secure a loose trouser hem

Secure the loose trouser hem with the safety pin, with its point safely enclosed.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

A safety pin can hold a loose turned trouser hem until it can be sewn properly.

## Setup and reset

An inside-out cotton trouser cuff, 180 mm across and 240 mm long, rests over a 140 x 190 x 60 mm wooden sewing support inserted between its faces. The 20 mm turned front hem overhangs the support by 46 mm toward the left arm; its middle 60 mm of stitching is loose. The back stays below the support. An ordinary 50 mm steel safety pin lies open toward the right arm. Both hands start open.

Use a cotton-twill trouser cuff with a 20 mm factory crease; unpick the securing thread from a 60 mm front section and remove loose thread. Replace punctured fabric after each trial. Restore the photographed fold, inspect the pin and protective pad covers, and leave the pin open.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if the pin passes through both front and hem layers, returns through them to the surface, and closes with its point inside the shield; the hem remains secured after a three-second release. 0.5 if both layers are threaded but the pin is still open or held; 0.25 for a partial threading through a correct layer. Otherwise 0. Pinning the back of the leg, more than four punctures, or a tear over 5 mm scores 0.

## Simulation and limits

Native cloth panels, sprung pin arm, shield and finger contacts. A reduced puncture rule requires measured compression of a force-resisting needle point before creating a sliding hole constraint. Closing must overcome the native spring and align the point with its shield. No hand attachment is used. Cloth, puncture and spring properties are uncalibrated. Native feasibility has not yet been validated.

The starting hem is turned but unsecured. The task retains the actual in-and-out threading and sprung closure, not just pressing an already threaded pin shut. The native score checks two punctures in each layer and verifies that those holes still surround the shaft. A full native threading/closure demo is still required.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
OMNI_KIT_ACCEPT_EULA=YES python tasks/pin-a-loose-trouser-hem/run.py --mode hold --steps 60 --out /tmp/pin-a-loose-trouser-hem-hold
```

The candidate controller in `make_plan.py` and `demo_control.py` is still being validated. The hold command checks reset only. Use `--mode demo` for the candidate trajectory; it is not yet full-score evidence.

Rescore recorded native body poses with `python tasks/pin-a-loose-trouser-hem/rescore.py /tmp/pin-a-loose-trouser-hem-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 1,400 control steps (70 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.
