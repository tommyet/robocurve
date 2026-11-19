# Put a silicone swimming cap onto a headform

Stretch the swimming cap over the headform. Cover the crown, leave the face clear, and release it without tearing the cap.

## Run and score

Use the Python 3.12 / Isaac Sim 6.1 / YAM runtime pinned in `ENVIRONMENT.json`.
An NVIDIA GPU is needed for native rendering. From the repository root:

```sh
OMNI_KIT_ACCEPT_EULA=YES python tasks/fit-a-silicone-swimming-cap/run.py --mode demo --out /tmp/fit-a-silicone-swimming-cap-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/fit-a-silicone-swimming-cap/run.py --mode dream --out /tmp/fit-a-silicone-swimming-cap-dream
python tasks/fit-a-silicone-swimming-cap/rescore.py /tmp/fit-a-silicone-swimming-cap-demo
```

Dream receives the ordinary RGB cameras and joint state through Inspect Robots.
The SDK resolves its credential privately. Use one episode per key at a time.
The fixed layout has no random jitter or seed. The limit is 1,800
controls at 20 Hz. Demo and Dream use identical physics and hardware; the demo
commands only the robot joints and grippers.

Each run saves its source, complete state trace, camera recordings and report.
Rescoring checks source hashes and recomputes outcomes from the recorded native
states on CPU; it is not a new physics simulation. Camera strides above 1 are
for diagnostics and are excluded from submission evidence.

## Setup and reset

Use the adult headform, thin silicone cap and upturned polypropylene tumbler
specified in `task.json`. Secure the headform base and tumbler to the table.
The cap is separate from the head, resting opening-down on the tumbler.
The head centre is (460, 0, 872.5) mm and faces the right arm; the cap's initial
rim centre is (260, 0, 838.5) mm. X points forward, Y left, and the table is
747.5 mm high. Match the setup image and restore the cap without stretching
or tearing it. The ordinary arm bases have no additional risers.

The open grippers start beside opposite rim arcs with a 27 mm face gap.
`initial-action.json` records their fixed reset joint positions. This applies
identically to demo and Dream. The robot still has to close on the rim,
stretch the cap, fit it and release it; no material pose is set during a trial.

Both grippers have 40 x 24 x 3 mm silicone-faced finger extensions, with
40 N finger actuator limits. No fixture holds the cap on the head.

## Scoring and material model

Use the video and a ruler to check the rim around the head, the clear face,
the crown gap and three seconds of retention after release. The numerical
bands and partial credit are in `task.json`. A cap resting beside the head,
or crumpled on its crown without an encircling rim, cannot receive full credit.

The cap is a 0.8 mm native elastic shell with self-contact and a 3 mm rolled
rim. Young's modulus is 1 MPa; this uncalibrated value approximates silicone.
The head is rigid. A compliant native pinch forms only when a rim element is
between closing finger faces. It releases on opening or 8 mm slip, and breaks
at 18 N or 0.08 Nm. Grip reaction loads on the robot are omitted. The robot
must stretch, position and release the material; no fitted shape is assigned.

## Assets

All task geometry is original procedural work under the included MIT license.
The robot, table and runtime come from the pinned YAM / Isaac environment.
No third-party task meshes, scans or textures are used.

## Validation status

Not submission-ready. The latest native diagnostic (`cap-full-061`) completed
640 controls with score 0.0. Sequential hand withdrawal still pulled the cap
off the head. A released full-score fitting and completed Dream baseline
remain required.
