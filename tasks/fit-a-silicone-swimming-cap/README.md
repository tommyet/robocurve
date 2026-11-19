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

Use a rigid adult headform, 190 × 160 × 240 mm, fixed to its 140 × 130 mm base. The separate silicone cap has a 150 × 140 mm unstretched opening, a 90 mm dome, a 0.8 mm wall and a 3 mm rolled rim. Match one cap model and size across trials.

The head centre is (360, 0, 872.5) mm, with its nose facing positive Y. X points forward, Y left, and the table is 747.5 mm high. Each arm stands on a fixed 160 × 160 × 100 mm steel riser. Both grippers have 40 × 24 × 3 mm silicone-faced extensions and 40 N finger actuator limits.

Both hands initially hold the cap's front and back rim above the head. The initial rim centre is (360, 0, 1047.5) mm, centred 55 mm above the crown, with a 3 mm pad gap. Reset verifies actual contact before frame zero and lets the material settle under gravity; demo and Dream share this reset. The robot must stretch, draw down and release the cap. No fixture holds it on the head and no material pose is assigned during a trial. Restore the photographed layout without pre-fitting or damaging the cap.

## Scoring and material model

Use the video and a ruler to check the rim around the head, the clear face,
the crown gap and three seconds of retention after release. The numerical
bands and partial credit are in `task.json`. A cap resting beside the head,
or crumpled on its crown without an encircling rim, earns no credit. Partial credit requires an encircling rim lowered below the 100 mm height band; the full-fit band remains 75 mm.

The cap is a 0.8 mm native elastic shell with self-contact and a 3 mm rolled
rim. Young's modulus is 1 MPa; this uncalibrated value approximates silicone.
The head is rigid. A compliant native pinch forms only when a rim element is
between closing finger faces. It releases on opening or 8 mm slip, and breaks
at 40 N or 0.08 Nm. Its uncalibrated translational stiffness is 40,000 N/m;
the force cap and 8 mm slip limit remain active. The finite grip connects to the native gripper and transmits reaction loads. The robot
must stretch, position and release the material; no fitted shape is assigned.

## Assets

All task geometry is original procedural work under the included MIT license.
The robot, table and runtime come from the pinned YAM / Isaac environment.
No third-party task meshes, scans or textures are used.

## Validation status

Not submission-ready. The rotated headform layout is being tested with a firmer commanded pinch. A full-score released fitting, native penetration check and paired Dream baseline remain required.

The 0.8 mm shell uses a 0.4 mm rest-contact offset and 3 mm speculative contact margin, with exact fixed-head triangle collisions. Grip friction is an uncalibrated approximation; the force, pad-contact, slip and material-integrity checks remain active.

The finite rim pinch uses 40,000 N/m translational stiffness and 4 N·s/m damping, with the same 40 N/0.08 Nm break limits and continuous opposed-pad contact check. The 0.5 mm finger contact offset is smaller than the 1 mm capture/holding margin. These parameters approximate an unresolved frictional grip and are not measured silicone properties.

The rolled-rim proxy may overlap a pad under compression. Holding requires it to continue spanning both pad faces within the1mm air-gap margin; compression itself is not treated as lost contact. Initial capture still requires both surfaces within1mm. The native joint connects to the actual gripper body at every physics substep and transmits reaction forces.
