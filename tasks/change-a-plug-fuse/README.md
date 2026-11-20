# Replace a fuse in an open, unplugged UK plug

Replace the exposed cartridge with the matching spare, then refit the removed carrier securely. The carrier is already removed at the start; opening it is outside this task.

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
The fixed layout has no random jitter or seed. The limit is 2,400
controls at 20 Hz. Demo and Dream use identical physics and hardware; the demo
commands only the robot joints and grippers.

Each run saves its source, complete state trace, camera recordings and report.
Rescoring checks source hashes and recomputes outcomes from the recorded native
states on CPU; it is not a new physics simulation. Camera strides above 1 are
for diagnostics and are excluded from submission evidence.

## Setup and reset

Use the disconnected full-size UK plug and two matching3A cartridges. The original fuse starts seated in its spring terminals. The removed carrier starts upright in the raised tray; the spare is separate. No part has been replaced during reset, and the plug is never connected to electricity.

The plug centre is(280,80,761.5)mm, rotated90degrees clockwise. The spare starts at(400,-105,763.5)mm on an18×18×12mm wooden rest. The carrier starts at(318,-16,780.25)mm in a90×70mm tray with a25mm base and4mm rim. The85×70mm parts dish is centred at(290,-160)mm and has16mm sides. X points forward,Y left; table height is747.5mm. The plug, carrier and cartridges are free to move. Match the setup photograph, restore intact clips and detents, and seat the original cartridge before each trial.

The left fingers use55×20×3mm padded extensions. The right fingers use55mm steel extensions, with3mm backing and0.8×2mm distal22mm sections. Both jaw actuators have40N limits. The thin tips fit between the cartridge and the ordinary cover detents.

## Scoring and material model

Full credit requires the old fuse at least40mm outside its seat, the replacement within3mm of its seat and aligned within18degrees, and the carrier flush within2.5mm and aligned within18degrees, with3seconds retained after both hands release. Both replacement ferrules must be in their spring clips. Removing the old fuse and seating the replacement earns0.5; removing only the old fuse earns0.25. Broken parts or parts falling off the table score0. The rigid housing itself has no fracture model; clip and detent failure are simulated. Inspect the video and released result with a ruler. No electrical continuity claim is made.

Cartridges and the carrier use native contacts and spring joints. A contact-gated native pinch approximates friction while a part is between closing finger faces. It starts at the measured pose, transmits reaction to the hand, releases on opening, and slips at 8 mm or breaks at 12 N / 0.060 Nm. These limits are approximate. Spring response and break loads approximate small metal/plastic parts. Ordinary moulded cavity ends limit axial cartridge movement. The robot moves only through its joints; no task-object pose is written. The supporting hand moves the plug aside during carrier pickup, then brings it back for refitting.

## Assets

All task geometry is original procedural work under the included MIT license.
The robot, table and runtime come from the pinned YAM / Isaac environment.
No third-party task meshes, scans or textures are used.

## Validation status

This revised open-plug setup is not submission-ready. The prior closed-plug diagnostic removed the old cartridge and seated the replacement, but failed to pick up the overturned carrier. A complete demo, paired Dream baseline, independent rescoring and media review remain required for the current setup.
