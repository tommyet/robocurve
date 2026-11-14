# Dry long hair evenly with a handheld dryer

Native mechanics and controller under development; no complete drying demo yet.

Use a long-haired mannequin representing a woman's hairstyle. Pick up and
operate the dryer, expose hair sections as needed, and dry the full length,
both exposed sides and under-layers. Leave no persistently wet region. The
second arm can separate or lift locks; a rigid painted sheet cannot count as
successful hair manipulation.

Candidate native representation: multiple articulated flexible locks with
self-contact and scalp-root attachment. Fine fibre geometry can be rendered
around the physical bundles. Coarse bundles, bending/contact forces, airflow
and moisture/temperature models must be documented and calibrated; they are
not interchangeable with individual-strand fluid simulation.

Drying must depend on measured dryer position/direction, switch state,
airflow attenuation/occlusion, distance, exposure and local moisture. Merely
sweeping a target trajectory cannot flip hair regions to dry. Test front-only
exposure, hidden inner layers, near/far operation, no airflow, manipulation,
and released stable hair. Exact moisture/heat thresholds and task allowance
remain unset until the model and native reach/access probes are established.

Native geometry, thermal/occlusion kernels and incomplete robot probes now exist. No complete drying score, demo or submission readiness is claimed.
DYMO-Hair is relevant prior work on hair dynamics/manipulation, not proof that
this implementation can model or complete drying. See the batch record.

## Current implementation and probes

The mannequin has a passive swivel neck bearing and separate articulated locks;
robot contact must turn its head. The bearing has no policy-driven angle or
motor. A normal open U-shaped dryer holder supports the barrel with its handle
accessible below; no extra grasp handles are added. The real handle slider
sets power from measured travel. The robot braces the handle, pushes the
slider using measured phase gates, confirms retained power after horizontal
retraction, and verifies actual dryer lift. It then holds the powered dryer;
full drying motion remains unimplemented.

`airflow.py` traces from the measured nozzle to four surface quadrants on every
hair segment. The scalp and other measured capsule locks can occlude airflow.
Local heat/moisture loss is energy limited; power-off and hidden patches do
not dry. Candidate pressure drag is capped at 0.25 N total with equal/opposite
dryer recoil. The dryer uses an ordinary **45 °C low-heat setting**; the scoring limit
remains 50 °C. This candidate source temperature is not an empirical
calibration. Heat, moisture, drag and bearing values remain uncalibrated.
The hair model is a coarse bundle approximation, not individual-fibre CFD.

```bash
/data/IsaacLab-Arena/.venv/bin/python run.py --mode dynamics --out /path/to/new-probe
/data/IsaacLab-Arena/.venv/bin/python run.py --mode power-probe --out /path/to/new-attempt
```

The first separate-body hair probe passed its passive test, but moving-head
robot trials exposed excessive joint error. A reduced-coordinate tree is now
being validated for both integrity and speed. Current slider/pickup attempts
are incomplete. Full inner-layer manipulation, all-surface drying, switch-off,
released parking and native scoring integration are still required. Do not
infer successful drying from a planned arm sweep or a warm-coloured render.

The switch probe clips the unmodified finger collision triangles to the actual
slider footprint and starts 1 mm below its lower face. Alignment and insertion
require five measured settled frames (TCP <1 mm, orientation <1 degree,
dryer drift <1 mm); upward pushing occurs only afterwards at 1 mm/s. It logs
measured support height and finger joints, and aborts on missing slider motion,
tracking timeout, brace disturbance or failed pickup. Up to 1,600 control
steps / 80 seconds are allowed for this engineering probe, not a complete task.
The trace includes local patch water, temperature, exposure and occluder IDs,
and the measured minimum scalp-to-capsule clearance every frame. Connected
root capsules now collide with the scalp; adjacent lock segments remain
filtered. Native clearance and controller success still require GPU validation.

The left grasp is 25 mm below the handle midpoint to clear the second hand.
An elevated approach avoids a low-pose IK limit. Before insertion the probe
uses actual loaded jaw joints and TCP pose to certify at least 1 mm between
both hands throughout the full insertion/stroke/retraction translation volume.
The nominal CPU certificate covers loaded jaw positions from −12 to −20 mm
and gives at least 5.24 mm separation; native frictional pickup still needs
validation. Neither the finger geometry nor the grip force target is altered.

Native collision repair (hair-skin012): the backend filtered the root
articulation-link/scalp pair even with joint collision enabled. The650g head
is now split into a600g head and50g invisible spherical collision skin joined
by a passive fixed joint excluded from the articulation. Its rendered head and
physical radius are unchanged; it is an anatomical rigid attachment, not a
robot grasp constraint. Native maximum attachment gap0.645micrometres, strand
anchor gap0.242micrometres; sphere/capsule contact check passed throughout the
9-second force diagnostic. This is not a drying-completion demonstration.
