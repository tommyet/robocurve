# Fold a pop-up laundry hamper

Twist-fold the pop-up laundry hamper and secure it with its retaining loop.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

A pop-up hamper must be twisted into nested loops and restrained before its spring frame opens again.

## Setup and reset

An empty, ordinary 33 x 33 x 53 cm spring-steel and polyester-mesh laundry hamper, flattened into its full 33 x 53 cm rectangle but not twisted or coiled. Its attached elastic retaining loop lies loose beside it. The flat hamper lies on a 220 x 380 x 100 mm raised wooden board on the table with the 53 cm length between the arms and the 33 cm width running forward. Both hands start open. No latch or fixture holds a folded shape.

Use a full-size pop-up mesh hamper with an attached elastic retaining loop, such as the 13 x 13 x 21 inch Smart Design type. Open it, inspect the wire and seams, flatten the sides without twisting the frame, then restore the photographed rectangle and loose loop. Do not start from an already coiled frame.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if the hamper forms a packet no larger than 22 x 22 x 6 cm, its retaining loop surrounds it, and it remains within those dimensions for three seconds after both hands release. 0.5 for the same compact packet while held or unsecured; 0.25 for a packet no larger than 35 x 25 cm. Otherwise 0. A broken frame, detached loop or torn fabric scores 0. Use a ruler and the released video.

## Simulation and limits

Native elastic frame segments, a flexible cloth net, retaining loop and finger collisions. Passive joint stiffness and self-contact produce the fold; no commanded collapse, final-pose snap or gripper attachment is used. It starts flattened but uncoiled. The steel and elastic properties are uncalibrated approximations and a successful twist-fold has not yet been demonstrated.

This is explicitly the twist-fold and retaining-loop operation, not the initial flattening of an upright hamper. Size reference: https://www.shopsmartdesign.com/products/pop-up-laundry-hamper-square-13inch . The flattened frame layers are represented by one strip of 12 spring-linked rods with their summed mass and rotational stiffness. This omits relative slip between the frame layers. A flexible bar-and-node net represents the flattened cloth layers with their combined mass. Freely rotating nodes permit folding and shear; mesh shear resistance and inter-layer slip are omitted. Cloth collision is sampled at the nodes and links, rather than over the complete fabric surface. The rendered mesh follows only those measured physical nodes. Twisting, bending, spring-back, self-contact and retainer placement remain physical requirements. These uncalibrated material approximations still need a native feasibility check. The 22 cm packet target is a proposal, not a measured claim about a particular retail unit.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
OMNI_KIT_ACCEPT_EULA=YES python tasks/fold-a-pop-up-laundry-hamper/run.py --mode hold --steps 60 --out /tmp/fold-a-pop-up-laundry-hamper-hold
```

The existing candidate tests pickup and twisting. It has not produced a compact coil, and retaining-loop placement is not implemented. The hold command checks reset only; it cannot establish task feasibility.

Rescore recorded native body poses with `python tasks/fold-a-pop-up-laundry-hamper/rescore.py /tmp/fold-a-pop-up-laundry-hamper-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 1,600 control steps (80 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.

The current candidate plan only tests the twist/nest motion. Securing the retaining loop is not implemented; this is not full-score evidence.

Native gripping contact uses a small torsional friction patch to approximate soft protective pad covers (1.5 mm minimum radius). This supplies frictional grip torque under contact load; it is not a hand attachment. The parameters are uncalibrated. [PhysX contact-patch documentation](https://nvidia-omniverse.github.io/PhysX/physx/5.8.0/_api_build/classPxShape.html) describes this mechanism.

Each finger has a 2 x 18 x 24 mm silicone cover over its inner pad, centred 1 mm ahead of the TCP. The cover geometry uses finite friction and a rigid collision approximation. Thin contacts are integrated at 480 Hz. Their physical closing stop leaves a 4 mm nominal jaw gap, where the two 2 mm covers meet. The original 5,000 N/m gripper gain and a 40 N/finger force ceiling apply to both demo and Dream. The covers have no attachment to task objects and do not enforce a folded shape. Thin-frame contacts use angular collision detection and additional solver iterations. These contact approximations still need a complete native demonstration.

Development runs may use `--capture-every 4` to reduce camera work while preserving every physics-state record. Such runs are explicitly marked unsuitable for submission evidence. Final videos must use the default camera capture on every action.
