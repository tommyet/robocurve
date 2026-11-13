# Peg a T-shirt onto a clothesline

**Development package; not ready to submit.** No robot demo, Dream run, measured
score or uploaded media exists yet. The native cloth and spring-peg code has not
yet completed GPU validation. Do not turn this draft into `task.json` until the gates
in `VALIDATION.json` pass.

The task is ordinary laundry fastening: hang a small cotton T-shirt using two
spring pegs and leave it supported only by the line and pegs. The shirt is an
original two-layer sewn surface mesh with open neck, cuffs and bottom hem. It
is not a rigid outline. `scene.py` authors the proposed full prop layout;
`arena_cloth.py` implements the native cloth bridge for the pinned YAM adapter.
`arena_props.py` registers both dynamic peg jaws and resets their actual poses
and velocities. `task.py` assembles the complete station scene; `run.py` records
a bounded no-op robot smoke run. Standalone native drape physics and rendering
now run; the robot bridge and a successful controller remain to be demonstrated.

On 13 November, the three-second standalone drape rendered 31 nonblank frames.
The one-second contact audit found no triangle intersections with the rail,
but the cloth was still moving. Clamp and robot probes stopped at a peg
quaternion authoring error; its precision is corrected and awaits rerun.
This is mechanism evidence, not task success.

## Local checks

From the repository root:

```bash
.venv/bin/python -m unittest discover -s tasks/peg-out-a-tshirt -p test_local.py -v
.venv/bin/python tasks/peg-out-a-tshirt/run.py --check-only
```

These check mesh topology, the unstrained starting pose and adversarial cases
in the provisional rubric. They do not simulate cloth or demonstrate success.

## First GPU checks

Use the retained Isaac Sim 6.1 interpreter, with the pinned IsaacLab/Arena
environment already activated. No additional installation is required by these
scripts. Do not call Dream until native contact has passed.

```bash
python tasks/peg-out-a-tshirt/probe.py --mode drape --seconds 3 --output /tmp/tshirt-drape
python tasks/peg-out-a-tshirt/probe.py --mode clamp --seconds 3 --output /tmp/tshirt-clamp
python tasks/peg-out-a-tshirt/probe.py --mode open-clamp --seconds 3 --output /tmp/tshirt-open-clamp
python tasks/peg-out-a-tshirt/probe.py --mode task-layout --seconds 3 --output /tmp/tshirt-layout
python tasks/peg-out-a-tshirt/run.py --mode smoke --steps 60 --out /tmp/tshirt-yam-smoke
```

Each process records source hashes, actual runtime and native node trajectories.
By default it also records native-rendered diagnostic video and initial/final
PNGs. Use `--no-render` only to isolate a physics-startup failure. Native
physics advances through an explicit cached-stage attachment and fixed steps;
the deprecated `World.reset()` path failed to attach a PhysX stage under the
verified Isaac Sim 6.1 installation. Maximum transient edge strain and nodal speed are
recorded alongside the final shape.
Inspect the drape for sag/folding and no penetrations. Compare the closed and
open jaw fixtures: only actual spring pressure and friction may retain the free
cloth coupon. A valid result needs visual review as well as the numeric report.
The diagnostic peg's lower jaw is fixed to its test stand; both jaws are free in
the actual task, and the robot must pick up and operate the peg physically.

The YAM runner holds the ordinary ready joint targets. It checks that the shirt
is a native self-contact deformable, that each peg has two non-kinematic jaws
and one free hinge, and that no attachment appears in the scene. It records
policy camera video, joints, native cloth nodes, actual jaw poses/velocities,
source files and runtime. Geometry is assessor-only data and never feeds back
into the constant policy. A completed smoke run always has `score: null`.
The runner explicitly resets the raw environment once before its first
snapshot and records the reset's physics step counts, without an extra settling
loop; this exercises the native cloth and peg reset events.

Run at 240 Hz first. Increase to 480 or 960 only if contact convergence justifies
it. Do not run ten full robot attempts to diagnose a failed three-second cloth
probe. Runtime and the approximately $3 task budget cannot be confirmed before
the first measured GPU process.

## First robot contact probe

After the native drape/clamp checks and settled reset are verified, the frozen
`grasp-plan.json` runs a 21-second bimanual approach, pinch, lift and release.
`fixed_motion.py` generates it from the declared support coordinates and YAM
URDF kinematics without loading a simulator. It reads no cloth state. The
maximum offline IK residual is 3.55 mm and 1.87 degrees. The sampled official
YAM collision-hull vertices stay outside the table, laundry support and
opposite arm. This
is a useful clearance check, not a continuous collision proof or successful
cloth retention; both require the recorded robot trial.

```bash
python tasks/peg-out-a-tshirt/run.py --mode motion-probe \
  --plan tasks/peg-out-a-tshirt/grasp-plan.json --out /tmp/tshirt-grasp
```

The same runner still records assessor-only nodes, jaw poses and ordinary
camera images. Motion-probe is explicitly unscored and cannot be submitted as
a full task demo. Its current waypoint positions remain provisional until the
measured settled drape is checked. Do not spend Dream calls on this diagnostic.

## Model and judging limits

Native surface FEM handles stretch, bending, gravity and self-contact. A
constant revolute spring closes each peg; no controller changes the drive,
attaches cloth, suppresses collisions or writes cloth positions. The initial
front/back gap is 1.6 mm; each surface's contact/rest offsets are 0.8/0.3 mm and
must be checked for artificial inflation in the clamp probe.

Mass is set from 180 g/m² fabric and mesh area, giving approximately 33.9 g.
The 400 mm sleeve span, 280 mm body width and 300 mm length describe a small
child's garment. Material stiffness, friction and peg torque are engineering
starting values, not calibrated cotton/wood measurements. The isotropic model
does not reproduce yarns, wet fabric, seam failure or tearing. Edge strain is a
diagnostic, not a tear detector. Visible damage, unphysical penetration or
unreviewed integrity prevents certifying a score.

`JUDGING.md` defines simple photo/video/ruler assessment. `scoring.py` applies
that rubric to a complete reviewed record; it does not invent capture from
closeness. Numeric thresholds are provisional until a feasible full-score run
and physical prop checks exist.

## Sources and overlap

Native authoring follows [NVIDIA surface deformables](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/deformables_beta/deformable_beta.html)
and [the installed IsaacLab runtime](https://github.com/isaac-sim/IsaacLab/blob/91a0906f93802eb859192dcb0bca879f891e92d6/source/isaaclab_physx/isaaclab_physx/assets/deformable_object/deformable_object.py).
The native rigid/deformable solver supports dynamic friction; no claim of
separate static friction is made.

The earlier [sock-pegging submission](https://github.com/robocurve/benchmark-tasks/pull/760)
failed for rigid cloth, automatic clip operation and proximity-based scoring.
A fixed low plastic laundry board gives the starting hem a real 65 mm overhang;
the robot still has to lift the flexible garment and operate both pegs. Its
200 x 440 mm top is 100 mm above the table. The current diagnostic starts the
shirt flat above that support so gravity can establish the drape. A successful
settling probe must supply the final reset; no pose is changed during control.

This implementation addresses those physical omissions, but claim ownership
and novelty still require organizer review. [BEHAVIOR clothesline hanging](https://behavior.stanford.edu/knowledgebase/tasks/hanging_clothes_on_clothesline-0.html)
uses draping, without a peg. This comparison is not advance acceptance.

## Reproduce a reviewed score

Complete the measurements and visual decisions in a judging JSON record after
reviewing the specified views. Include `evidence_files` and matching
`evidence_sha256` maps for the required photographs and released video, with
paths relative to the evidence directory. Then run:

```bash
python tasks/peg-out-a-tshirt/judge.py /path/to/judging.json \
  --evidence-dir /path/to/trial --out /path/to/reviewed-score.json
```

This checks every evidence file's digest before applying the rubric. Missing
measurements, unknown integrity or changed media produce an error, not an
invented score. No completed judging record exists yet.
