# CPU spray aiming experiment — 2026-11-16

Selected candidate: `tasks/uncap-spray-panel/aimed_demo.py`, generated ordinary
14-dimensional joint targets in `aimed_demo_actions.jsonl`, and pinned metadata.
All 779 original action times and 40 final hold actions remain. Actions 0–530
and every gripper command are unchanged. Offline seeded IK translates both TCPs
by WORLD (+22, −2, 0) mm, smoothstep-ramped over actions 530–610, then constant.
Online policy observes only `Observation.state_time`; it never reads scene,
contacts, poses, geometry or scoring. Original recorded policy/data are intact.

`compile_aimed.py` creates the new dataset, pins its hashes in the policy, and
checks all modified FK poses, original bounds and unchanged hardware joint speed
limits. `test_aimed_demo.py` has six passing CPU tests, independently rerun by
Astra. `aimed-compile-report.json` records all248 modified targets.

`check_aimed_geometry.py --source /path/to/original030 --out report.json` checks
all315 corrected URDF collider pieces per arm at all248 modified waypoints using
EXACT float32 transported commands. It includes the table, riser, backing,
compound stand, parked-cap conservative outer box, and predicted held-can
body/shoulder conservative OBBs against all non-hand links. Intended hand/can
contacts are excluded explicitly; paired command geometry is preserved to IK
residual. Minimum unrelated static separation1.398888mm; minimum inter-arm AABB
separation14.093064mm. These are target/proxy checks, not native trajectory proof.

The initial conservative can-body OBB/static check flagged up to0.271mm
body/riser overlap. This was retained in `aimed-object-proxy-report.json`, not
silently discarded. More faithful finite-riser SAT with a conservative
circumscribed128-sided cylinder (`check_riser_support.py`) finds the SAME minimum
support overlap11.4245µm for source and shifted pose, with ZERO additional
penetration from the translation. Ramp support clearance≥3.055641mm. Later the
can partly rests on the riser; its footprint shifts and its stability remains
unproved until a new native run. Some projected COMs are outside the riser Yedge,
as in the source trajectory; the robot holds the can. This is not an unsupported
stability claim or an object/support collision-free claim.

Float32 transport changes TCP positions≤64.49nm and orientation≤0.175µrad.
Relative paired TCP command change≤7.8nm. During source ramp rows530–610 the can
has two LEFT contacts in all81 rows, RIGHT contact force0, button travel≤14.23µm,
and cap speed≤0.05042mm/s. These are historical source observations, not new
measurements. Root's separate full-dose counterfactual sensitivity screen is a
hypothesis only; fresh native valve/grasp/aim/scorer replay is required.

Earlier `screen_schedule.py` / `report.json` describes a REJECTED shorter-spray
splice. The apparent counterfactual dose pass was pose-selection dependent and
compressed press-loading motion; DO NOT run that splice or interpret it as a
valid demonstration. The selected aimed candidate retains original timing.

CPU environment used:
`PYTHONPATH=/private/tmp/spray-yam-source /private/tmp/robocurve-usd-env/bin/python`.
Experiment scripts that use the historical local fixture path are evidence
helpers; that external trace and assets must be provided to reproduce them.
No GPU, native run, actor-pose write, rubric adjustment or full-score claim was
made by this experiment.
