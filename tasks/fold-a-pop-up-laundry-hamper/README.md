# Fold a pop-up laundry hamper

Development draft: the current native demo is still being validated. A full-score fold, matching Dream run and uploaded media are required before submission.

Twist the flattened spring-frame hamper into nested loops, flatten the packet and secure it with its attached elastic retaining loop. Leave it intact and restrained after both hands release.

## Setup and reset

Use one ordinary 33 × 33 × 53 cm spring-steel and polyester-mesh hamper, such as the 13 × 13 × 21 inch Smart Design type. Use the same model for every trial. Flatten its sides into the full 33 × 53 cm rectangle, without twisting or coiling its frame. Its attached silicone retaining loop has a 300 mm circumference and a 5 × 1 mm section, sewn through a 12 mm textile tab. Leave the loop loose beside the frame.

The table is 747.5 mm high. X points forward and Y toward the left arm. The flattened frame is centred at (390, 0, 865.5) mm, with its 530 mm length between the arms. Four 20 × 20 × 100 mm wooden rests support its short ends: their centres are X = 325 or 455 mm, Y = ±265 mm, Z = 797.5 mm. The table beneath the centre is clear for folding.

Both arms stand on 120 × 120 × 50 mm risers. Each gripper has 100 × 26 mm steel extensions with silicone faces: a 60 mm, 4 mm-thick backing and a 40 mm, 2 mm-thick distal section. The working offset is 215 mm and the finger actuator limit is 40 N.

The operator places the fingers around the two opposite bound ends and closes them before the timer starts. Native opposing-pad contact, an intact untwisted frame and zero score are checked at reset. No twist, coil or retaining-loop placement is supplied. The first 140 entries in the saved trajectory describe this robot reset and are excluded from the timed trial. Restore the setup photograph and replace any damaged frame, fabric, tab or loop between trials.

## Run and score

Use the pinned Python 3.12 / Isaac Sim 6.1 / YAM environment in `ENVIRONMENT.json`, an NVIDIA GPU and a new output folder:

```sh
python tasks/fold-a-pop-up-laundry-hamper/run.py --mode demo --out /tmp/hamper-demo
python tasks/fold-a-pop-up-laundry-hamper/run.py --mode dream --out /tmp/hamper-dream
python tasks/fold-a-pop-up-laundry-hamper/rescore.py /tmp/hamper-demo
```

The layout is fixed, without random jitter or a seed. The limit is 2,600 actions at 20 Hz. The current scripted trajectory uses 2,100 timed actions. Dream receives the standard camera and joint observations through Inspect Robots; use one episode per API key at a time. Both runs share the same reset, material model and hardware. The demo sends bounded robot joint commands and never sets a task object's pose.

Measure the packet with a ruler, allowing it to be turned for inspection. A packet within 350 × 250 mm earns 0.25. Within 220 × 220 × 60 mm earns 0.5. Full credit also requires the attached loop around the packet and those dimensions maintained for three seconds after both hands release. A broken frame, torn fabric or detached loop scores zero. The scorer includes the fabric and bound frame in the measured packet.

Each run saves its exact source, native state trace, videos and report. Rescoring checks hashes, action limits and recorded outcomes; it does not rerun physics. `--capture-every` values above 1 are diagnostic only and cannot be submitted. No wall runtime or successful score is claimed until validation finishes.

## Material model

Native elastic surfaces represent the spring frame, sewn mesh, textile tab and retaining loop. The four flattened frames share one strip with their combined mass and stiffness; inter-layer slip is omitted. The spring strip weighs 41 g, its binding 38 g, the mesh 60 g and the retaining loop 4 g. Rest shapes never change during a trial.

A finite frame pinch starts only when a bound segment is between closing finger faces. It releases when the fingers open or physical pad contact is lost, and breaks at 30 N or 0.36 Nm. Its native gripper attachment approximates unresolved friction and transmits reaction loads at each physics step. Initial capture allows a 1 mm contact margin; the 2 mm holding margin matches the native pad collision margin. The retainer uses a native vertex pinch that releases on opening, 8 mm slip or an estimated 6 N tension. Only incident contact triangles are filtered while held.

These are uncalibrated material and grip approximations. The frame and fabric still bend, slip and collide, and the band must be stretched around the packet. Nothing prescribes a folded or retained shape. All geometry is original procedural work under the included MIT license; YAM and Isaac retain their own licences.

Frame pinches connect directly to the robot gripper rather than a world anchor updated at20Hz. This removes control-interval lag while retaining the same30N/0.36Nm limits and continuous pad-contact checks.

Frame-grip capture is restricted to the central12mm of each26mm pad and at least10mm behind its tip. This conservative contact approximation leaves room for compliance during folding; it does not enlarge the physical pad or increase grip strength. Holding still checks the full real pad faces.

The steel face extends from 88 mm behind the TCP to 12 mm ahead. Holding checks use that actual 100 mm contact span; capture remains central. The earlier 22 mm holding window incorrectly released contacts still on the physical finger.
