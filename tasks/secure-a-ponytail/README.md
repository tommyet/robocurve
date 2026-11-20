# Secure a ponytail with a plain hair elastic

**Validation withdrawn:** the previous USD proof-force command failed a native control test. New force application and paired evidence are required; do not submit the old result.

Gather the synthetic hair on the practice head into a ponytail and secure it with the plain elastic. Leave it held after both hands let go.

## Run and score

Use the Python 3.12 / Isaac Sim 6.1 / YAM runtime pinned in `ENVIRONMENT.json`.
An NVIDIA GPU is needed for native rendering. From the repository root:

```sh
OMNI_KIT_ACCEPT_EULA=YES python tasks/secure-a-ponytail/run.py --mode demo --out /tmp/secure-a-ponytail-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/secure-a-ponytail/run.py --mode dream --out /tmp/secure-a-ponytail-dream
python tasks/secure-a-ponytail/rescore_native_precision.py /tmp/secure-a-ponytail-demo
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

Use a rigid adult practice head approximately 180 × 156 × 230 mm. An inexpensive [Marianna polystyrene head with a face](https://www.sallybeauty.com/salon-supplies/other-professional-supplies/beauty-student-supplies/styrofoam-head-with-face/SBS-200201.html) is a suitable starting form; measure it and pad the scalp with firm foam if needed to match each dimension within 10 mm. Clamp its mounting base firmly to the table. The simulator uses a rigid approximation of this supported head.

Prepare the hair once from an ordinary pack of straight synthetic braiding hair. Weigh twelve **3.0 ± 0.1 g** bundles on a 0.1 g scale and trim their free length to **245 ± 5 mm**. Bind only the uppermost 10 mm of each bundle with thread and adhesive; do not join the free lengths. Fix these twelve roots individually to a thin flexible scalp backing, then bond that backing flush to the rear of the head. No backing, glue or thread may extend into the free hair. A root must withstand a 2 N pull before use; replace any loose root.

Place the roots on a 61 mm-wide rear scalp patch. In the head frame, root lateral coordinates are `(s − 5.5) × 5.5 mm` for `s = 0..11`; their heights are `35 + 15 cos(s) mm` above the head centre. A ruler-marked paper template makes these positions reproducible within 2 mm. Root coordinates in millimetres (left/right offset, height above centre): (-30.2, 50.0), (-24.8, 43.1), (-19.2, 28.8), (-13.8, 20.2), (-8.2, 25.2), (-2.8, 39.3), (2.8, 49.4), (8.2, 46.3), (13.8, 32.8), (19.2, 21.3), (24.8, 22.4), (30.2, 35.1). The front-to-back coordinate follows the scalp surface. Brush the twelve locks straight and lay them separately in their photographed loose arrangement; **do not tie, braid or join them**. Weigh/prepare before fixing roots, so no trial requires extracting hair from a commercial rooted head.

The head faces away from the robot. Its centre is (390, 0, 1052.5) mm; the elastic starts at (270, 0, 810.5) mm on two secured wooden rests. X points forward, Y left, and the table is 747.5 mm high. Restore the loose hair and separate band each trial. The synthetic locks and contact envelopes are a coarse grouped-fibre model, not individual hair strands.

The finger extensions have 40 mm working length, 12 mm width and 3 mm thickness.
Both arms use their ordinary mounting height and 40 N finger actuator limits.

## Scoring and material model

After the robot releases, wait three seconds, then pull the elastic gently towards the hair ends with a spring scale: ramp to **1 N over 0.5 seconds**, hold **3 seconds**, then unload over **0.5 seconds**. Hook the scale through the elastic without catching hair; the evaluator must not support the band. Film the scale and band beside a ruler. The band may move **at most 10 mm** from its starting position throughout this test. A loose ring that slips down the hair fails, even if it previously rested in place.

All credit requires passing this retention test, intact roots/band, and the band centre at least 55 mm behind and 25–160 mm below the head centre. Count locks remaining through the band after unloading: eleven or twelve earn 1.0, nine or ten 0.5, six to eight 0.25, fewer zero. Full credit also limits the band's maximum width to 50 mm. Other outcomes score zero. The load check is a repeatable gentle-tug criterion, not a claim about every hairstyle or elastic product.

The simulator applies the same downward load, divided over native band contact patches, after three seconds with clear hands and after the band leaves its starting rest. It ramps/holds/unloads without writing material positions. Touching again resets the test. The evaluator force stands in for the scale; the test is recorded in the ordinary native trial and CPU-audited from its state history.

Articulated 5 mm contact envelopes group fine hair fibres into flexible locks.
A native elastic surface models a 20 mm inside-diameter, 3 mm cord silicone band;
its stiffness is approximate. The starting rests are 23 mm apart. These dimensions
are part of the trial setup, not a measured retail-product calibration.

A geometry-gated native vertex attachment represents finger friction only after
closing pad faces enclose a band patch. It holds only material already inside the
central 8 mm of the 12 mm-wide face, follows the real gripper link, and releases on opening, 8 mm slip
or estimated local cord tension above 18 N. This tension estimate is uncalibrated;
it is not a measured native force limit. Local held-patch contacts are filtered
while the attachment acts, to avoid conflicting constraints. Native hair contacts,
root failures and band over-stretch remain active. No hair or band pose is assigned
during a trial; the approximation supplies no automatic gathering or fitting.

The CPU audit verifies source hashes and every action, then independently
reconstructs release time, the pull-force schedule, maximum band movement,
retained-lock count and final score from the frozen state trace. Surface nodes
are restored at their native float32 precision. Complete traces and sources
are preserved; the audit does not rerun or alter the physics.

## Assets

All task geometry is original procedural work under the included MIT license.
The robot, table and runtime come from the pinned YAM / Isaac environment.
No third-party task meshes, scans or textures are used.

## Validation

The old submitted demo and baseline are withdrawn because the USD proof force did not reach the native solver. Corrected control tests verify native force application; new successful task evidence is still required.

The working point is168mm from the gripper origin,4mm behind the extension ends. This keeps the opposed fingers clear of one another when picking up the small elastic; capture is restricted to the actual−36…+4mm working span.

The approximate local tension limit is18N, below the native40N jaw effort. It represents silicone-pad friction, not measured force feedback. The1N released retention test,8mm grip-slip limit and material integrity checks are unchanged.

The silicone modulus is an uncalibrated0.6MPa. During threading, the demo follows the observed hair centre at the current height; it does not keep the lower hair ends' X coordinate while moving toward the curved scalp.

The 12 mm-wide pads capture only vertices within their actual 6 mm half-width. The 18 N estimated slip guard is below the 40 N jaw effort; it is an explicitly uncalibrated friction approximation. The released 1 N proof is unchanged.

Every cord segment has a native contact capsule, giving the elastic a continuous collision envelope. The demo withdraws along the finger axes after opening, without sweeping backwards through the gathered hair.
