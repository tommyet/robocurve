# Change the fuse in an unplugged UK plug

Replace the fuse in the unplugged plug with the spare of the same rating, and refit its fuse carrier securely.

## Run and score

Use the Python 3.12 / Isaac Sim 6.1 / YAM runtime pinned in `ENVIRONMENT.json`.
An NVIDIA GPU is needed for native rendering. From the repository root:

```sh
OMNI_KIT_ACCEPT_EULA=YES python tasks/change-a-plug-fuse/run.py --mode demo --out /tmp/change-a-plug-fuse-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/change-a-plug-fuse/run.py --mode dream --out /tmp/change-a-plug-fuse-dream
python tasks/change-a-plug-fuse/rescore.py /tmp/change-a-plug-fuse-demo
```

Dream receives the ordinary RGB cameras and joint state through Inspect Robots.
The SDK resolves its credential privately. Use one episode per key at a time.
The fixed layout has no random jitter or seed. The limit is 3,000
controls at 20 Hz. Demo and Dream use identical physics and hardware; the demo
commands only the robot joints and grippers.

Each run saves its source, complete state trace, camera recordings and report.
Rescoring checks source hashes and recomputes outcomes from the recorded native
states on CPU; it is not a new physics simulation. Camera strides above 1 are
for diagnostics and are excluded from submission evidence.

## Setup and reset

Use the disconnected moulded UK plug, two matching 3 A cartridge fuses,
screwdriver and parts dish specified in `task.json`. This is a mechanical
replacement task: the plug is never connected to electricity. The original
fuse starts seated, with the carrier closed; the spare is separate.

The plug centre is (280, 80, 761.5) mm, rotated 90 degrees clockwise so its
access notch faces the right arm. The spare starts at (400, -105, 763.5) mm
on an 18 x 18 x 12 mm wooden rest. The screwdriver pickup centre is
(280, -140, 775.5) mm. Its handle and shaft rest on secured wooden blocks,
30 x 20 x 19 mm and 20 x 20 x 26 mm. The plastic parts dish is centred at
(290, -160) mm and has 16 mm sides. X points forward and Y left; table height
is 747.5 mm. Match the setup image. The plug, carrier, fuses, driver and dish
are free to move. Restore intact clips and the original seated fuse each time.

The left fingers have 45 x 20 x 3 mm padded extensions. The right extensions
are 45 x 4 mm steel, with 3 mm backing and 2 x 2 mm distal 12 mm sections.
The finger actuator limits are 40 N.

## Scoring and material model

Inspect the released result with a ruler and the video. Full credit requires
the old fuse at least 40 mm outside its seat, both replacement ferrules inside
the clips, the carrier flush, and three seconds of retention after release.
Removing the old fuse and seating the replacement earns 0.5; removing only
the old fuse earns 0.25. Broken clips or housing, or parts falling off the
table, score zero. No electrical continuity or diagnostic claim is made.

Rigid-body contacts and passive spring leaves supply extraction and insertion
resistance. Clip stiffness and break loads approximate the small metal and
plastic parts. Only the screwdriver has an auxiliary grip: a compliant native
constraint forms between closing fingers, releases on opening or 8 mm slip,
and breaks at 18 N or 0.18 Nm. All other parts are moved by ordinary contacts.
Grip reaction loads on the robot are omitted. No part is positioned by task
logic during a trial.

## Assets

All task geometry is original procedural work under the included MIT license.
The robot, table and runtime come from the pinned YAM / Isaac environment.
No third-party task meshes, scans or textures are used.

## Validation status

Not submission-ready. The latest native diagnostic (`fuse-full-039`) stopped
at control 825 after a terminal was damaged during cartridge pickup. The
previous shallower pickup stayed intact but lost the cartridge after 6.4 mm
of lift. A full replacement demo and completed Dream baseline remain required.
