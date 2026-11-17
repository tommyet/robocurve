# Secure a loose trouser hem

Secure the loose trouser hem with the safety pin, with its point safely enclosed.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

A safety pin can hold a loose turned trouser hem until it can be sewn properly.

## Setup and reset

A 180 mm wide, 240 mm long cotton-twill trouser cuff section, with its existing 20 mm turned hem loose at the front; one open 50 mm steel safety pin beside it; and a dry work surface. Both fabric faces and the turned hem are flexible. The pin is not threaded into anything. Use replaceable puncture-resistant covers over the gripper pads.

Use a cotton-twill trouser cuff with a 20 mm factory crease; unpick the securing thread from a 60 mm front section and remove loose thread. Replace punctured fabric after each trial. Restore the photographed fold, inspect the pin and protective pad covers, and leave the pin open.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if the pin passes through both front and hem layers, returns through them to the surface, and closes with its point inside the shield; the hem remains secured after a gentle lift and three-second release. 0.5 if both layers are threaded but the pin is still open or held; 0.25 for a partial threading through a correct layer. Otherwise 0. Pinning the back of the leg, more than four punctures, or a tear over 5 mm scores 0.

## Simulation and limits

Native cloth panels, sprung pin arm, shield and finger contacts. A reduced puncture rule requires measured compression of a force-resisting needle point before creating a sliding hole constraint. Closing must overcome the native spring and align the point with its shield. No hand attachment is used. Cloth, puncture and spring properties are uncalibrated. Native feasibility has not yet been validated.

The starting hem is turned but unsecured. The task retains the actual in-and-out threading and sprung closure, not just pressing an already threaded pin shut. The draft native score counts four punctured patches; verifying the real retention check and reproducing the cuff drape remain required before submission.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
OMNI_KIT_ACCEPT_EULA=YES python tasks/pin-a-loose-trouser-hem/run.py --mode hold --steps 60 --out /tmp/pin-a-loose-trouser-hem-hold
```

A complete robot demonstration is not authored yet. This hold command inspects the native reset only; it cannot establish task feasibility. Add and validate `make_plan.py` and `demo-plan.json` before collecting demonstration or Dream evidence.

Rescore recorded native body poses with `python tasks/pin-a-loose-trouser-hem/rescore.py /tmp/pin-a-loose-trouser-hem-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 1,400 control steps (70 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.
