# Wheel manipulation plan

This is a development plan, not a successful demo. The frozen commands use the
published setup and robot URDF. They do not read live object poses, spoke
tension, contact flags or the score.

**Only the pickup segment is a current candidate. The full-turn plan is
blocked:** its nominal robot hulls intersect the hub and spokes by up to 15.4 mm.
Reachability did not establish safe access; the grip/layout is being replanned.

The pickup candidate starts the wheel 50° around its axle, with square nipple flats
phased by 45°. The 195 mm slot-to-grip wrench and a shorter front axle clear 38 sampled
engagement poses. A complete approach and turn plan remains to be validated. The left hand approaches the continuous rim from above at a 45°
tilt and steadies it, after narrowing its opening to clear the stand. These are explicit reset settings; the native source
defaults remain unchanged until the candidate is checked.

1. Approach and grip the free wrench handle while the other hand grips the rim.
2. Lift the wrench 80 mm and hold it for inspection.
3. Approach nipple 0, insert the open slot, tighten clockwise by a quarter turn,
   withdraw through the mouth, reset the tool angle and repeat twice.
4. Repeat the three quarter turns at nipple 2, then withdraw and release.

The pickup segment has 82 actions (4.1 seconds at 20 Hz). The current turn
segment has 499 actions (24.95 seconds). The offline IK and velocity checks
pass with the recorded URDF. They establish reachability only. The robot still
needs to demonstrate pickup, collision-safe motion, actual nipple rotation and
a complete released revolution for judging. There is no task score yet.

Compile from the pinned YAM Python environment:

```sh
python tasks/true-a-bicycle-wheel/motion_plan.py --out tasks/true-a-bicycle-wheel/pickup-plan.json
```

The preview checks the plan's source and URDF hashes before running. Begin
with two actions to verify integration, then expand only after inspecting the
native report:

```sh
python tasks/true-a-bicycle-wheel/preview_yam.py --out NEW --steps 2 --physics-hz 20000 --plan tasks/true-a-bicycle-wheel/pickup-plan.json
```

`audit_robot_plan.py` screens sampled commanded poses against the actual URDF
hulls and nominal scene geometry. It assumes a fixed grasp only to examine
clearance, and labels intended finger contacts separately. It cannot prove
grip, continuous-time collision safety or native task success.

The latest 82 sampled pickup poses have no unintended intersections with the
extended wrench, shortened front axle and far-side stand. The corrected straight-slot wrench also
transmits 32.90° of a 45° fixture command through contact, with all 16,000 rim
checks passing. That fixture clamps the hub explicitly for diagnosis; it is not
used by the task or offered as a successful robot demo.
