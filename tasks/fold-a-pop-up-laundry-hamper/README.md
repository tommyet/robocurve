# Fold a pop-up laundry hamper

Twist-fold the pop-up laundry hamper and secure it with its retaining loop.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

A pop-up hamper must be twisted into nested loops and restrained before its spring frame opens again.

## Setup and reset

An empty, ordinary 33 x 33 x 53 cm spring-steel and polyester-mesh laundry hamper, flattened into its full 33 x 53 cm rectangle but not twisted or coiled. Its attached elastic retaining loop lies loose beside it. The flat hamper lies on a 220 x 380 x 100 mm raised wooden board on the table with the 33 cm width between the arms and the 53 cm length running forward. Both hands start open. No latch or fixture holds a folded shape.

Use a full-size pop-up mesh hamper with an attached elastic retaining loop, such as the 13 x 13 x 21 inch Smart Design type. Open it, inspect the wire and seams, flatten the sides without twisting the frame, then restore the photographed rectangle and loose loop. Do not start from an already coiled frame.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if the hamper forms a packet no larger than 22 x 22 x 6 cm, its retaining loop surrounds it, and it remains within those dimensions for three seconds after both hands release. 0.5 for the same compact packet while held or unsecured; 0.25 for a packet no larger than 35 x 25 cm. Otherwise 0. A broken frame, detached loop or torn fabric scores 0. Use a ruler and the released video.

## Simulation and limits

Native elastic frame segments, flexible fabric panels, retaining loop and finger collisions. Passive joint stiffness and self-contact produce the fold; no commanded collapse, final-pose snap or gripper attachment is used. It starts flattened but uncoiled. The steel and elastic properties are uncalibrated approximations and a successful twist-fold has not yet been demonstrated.

This is explicitly the twist-fold and retaining-loop operation, not the initial flattening of an upright hamper. Size reference: https://www.shopsmartdesign.com/products/pop-up-laundry-hamper-square-13inch . The reduced four-frame model and its elastic loads still need a native physical feasibility check. The 22 cm packet target is a proposal, not a measured claim about a particular retail unit.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
OMNI_KIT_ACCEPT_EULA=YES python tasks/fold-a-pop-up-laundry-hamper/run.py --mode hold --steps 60 --out /tmp/fold-a-pop-up-laundry-hamper-hold
```

A complete robot demonstration is not authored yet. This hold command inspects the native reset only; it cannot establish task feasibility. Add and validate `make_plan.py` and `demo-plan.json` before collecting demonstration or Dream evidence.

Rescore recorded native body poses with `python tasks/fold-a-pop-up-laundry-hamper/rescore.py /tmp/fold-a-pop-up-laundry-hamper-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 1,600 control steps (80 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.

The current candidate plan only tests the twist/nest motion. Securing the retaining loop is not implemented; this is not full-score evidence.
