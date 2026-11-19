# Secure a ponytail with a plain hair elastic

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

Place the roots on a 72 mm-wide rear scalp patch. In the head frame, root lateral coordinates are `(s − 5.5) × 6.5 mm` for `s = 0..11`; their heights are `35 + 15 cos(s) mm` above the head centre. A ruler-marked paper template makes these positions reproducible within 2 mm. The front-to-back coordinate follows the scalp surface. Brush the twelve locks straight and lay them separately in their photographed loose arrangement; **do not tie, braid or join them**. Weigh/prepare before fixing roots, so no trial requires extracting hair from a commercial rooted head.

The head faces away from the robot. Its centre is (390, 0, 1052.5) mm; the elastic starts at (270, 0, 810.5) mm on two secured wooden rests. X points forward, Y left, and the table is 747.5 mm high. Restore the loose hair and separate band each trial. The synthetic locks and contact envelopes are a coarse grouped-fibre model, not individual hair strands.

The finger extensions have 40 mm working length, 24 mm width and 3 mm thickness.
Both arms use their ordinary mounting height and 40 N finger actuator limits.

## Scoring and material model

After the robot releases, wait three seconds, then pull the elastic gently towards the hair ends with a spring scale: ramp to **1 N over 0.5 seconds**, hold **3 seconds**, then unload over **0.5 seconds**. Hook the scale through the elastic without catching hair; the evaluator must not support the band. Film the scale and band beside a ruler. The band may move **at most 10 mm** from its starting position throughout this test. A loose ring that slips down the hair fails, even if it previously rested in place.

All credit requires passing this retention test, intact roots/band, and the band centre at least 55 mm behind and 25–160 mm below the head centre. Count locks remaining through the band after unloading: eleven or twelve earn 1.0, nine or ten 0.5, six to eight 0.25, fewer zero. Full credit also limits the band's maximum width to 50 mm. Other outcomes score zero. The load check is a repeatable gentle-tug criterion, not a claim about every hairstyle or elastic product.

The simulator applies the same downward load, divided over native band contact patches, after three seconds with clear hands and after the band leaves its starting rest. It ramps/holds/unloads without writing material positions. Touching again resets the test. The evaluator force stands in for the scale; the test is recorded in the ordinary native trial and CPU-audited from its state history.

Articulated 5 mm contact envelopes group fine hair fibres into flexible locks.
A native elastic surface models the band; its stiffness is approximate. A
geometry-gated native contact patch represents a centred finger pinch and
releases on opening, 8 mm slip or estimated 6 N local tension. This force
estimate is uncalibrated, not a measured native force limit. Local contacts at
a held patch are filtered to avoid conflicting constraints. No hair or band
pose is assigned during a trial.

The auxiliary pinch is selected within the central 8 mm of the 24 mm face.
It also holds adjacent elastic vertices already enclosed by that same real
face, representing friction over a finite contact patch. It does not attach
material outside the fingers. The estimated 6 N and 8 mm slip guards remain.

The tension guard estimates load at the exposed ends of the held patch,
using the current cord extension. It is checked at every control step.

The CPU audit wrapper restores the native float32 surface coordinates after
JSON loading, then runs the unchanged frozen scorer and tolerances. Without
that dtype restoration, the nearly circular band produces up to 0.000043 mm
of SVD measurement drift in the Dream trace. No score changes. The complete
recorded traces and original sources are preserved.

## Assets

All task geometry is original procedural work under the included MIT license.
The robot, table and runtime come from the pinned YAM / Isaac environment.
No third-party task meshes, scans or textures are used.

## Revision validation

New native recordings must include the retention test. Previous 1.0/0.0 recordings lacked that test and are development history only. Revised validation remains pending.
