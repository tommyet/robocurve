# Unbox a taped delivery parcel — development prototype

Use the orange guarded cutter to sever the parcel's top seam, return the tool,
open both flaps, and place the blue item on the green pad. This targets receiving
and unpacking deliveries with tool use followed by access and retrieval.

## Status

Development prototype, not a competition submission. No full-score robot demo or
Dream result has been established. The scripted plan is experimental. The final prototype trial (`unbox-demo-006`)
scored **0.25**: all tape cut and cutter returned, but the flaps were not fully
opened and the item remained inside. It used 1,153 steps / 57.65 simulated seconds
and 169.56 seconds of runner wall time. Independent replay matches 0.25, and all
six core source hashes match the recorded snapshot. The left flap reached 53.86°
and the right 11.55°; neither met the 80° milestone. All three exported camera
videos have 1,154 frames each. Current
validation and remaining gaps are recorded in `VALIDATION.json`. The authenticated
task board was inaccessible, but the public PR history identifies a closely
related pending carton-cutting/opening task, [PR #1856](https://github.com/robocurve/benchmark-tasks/pull/1856),
received as TK-V7P9X9 on November 13. Ordinary carton unboxing is therefore
not an obviously unclaimed competition objective. Do not interpret this folder as submission-ready.

## Setup

Fixed seed 0, no jitter, standard bimanual YAM station and three policy cameras.
World x points away from the robot bases, y left, z up; tabletop z=0.7475 m.
`config.py` and `task.py` specify every initial pose, size, colour and mass.

- Plain cardboard parcel, 220 × 180 × 75 mm, 3 mm walls/bottom, fixed in a
  packing fixture. The five static panels form an actual hollow enclosure.
- Two 18 g top flaps, each 220 × 88 × 3 mm, hinged along the long outer edges;
  each has a 35 × 14 × 9 mm thickened paper pull tab. The end walls extend to
  the lid; there are no separate inner minor flaps in this simplified carton.
- Brown tape along the 210 mm top seam; 21 simulated 10 mm segments. Each
  segment must have every 1 mm slice traversed by the blade before it is cut.
- Orange 55 g guarded package cutter: 110 × 25 × 25 mm handle, 25 × 30 × 20 mm
  guard, and a 14 × 3 × 8 mm metal cutting tooth. Initial root (0.13, 0.19, 0.7695).
- Blue item, 40 mm cube, 60 g, inside the parcel at (0.27, 0, 0.7705).
- Orange cutter pad, 170 × 70 × 2 mm, with an 80 × 40 × 7.5 mm
  handle cradle; green receiving pad, 100 × 100 × 2 mm.

The carton fixture is part of this task's setup. It makes no claim to evaluate
holding an unconstrained delivery box with the other arm.

## Run

In the installed Arena virtual environment, from this folder:

```bash
python run.py --policy demo --max-steps 1800 --log-dir ~/yam-eval/unbox-demo-001
python run.py --policy dream --max-steps 2400 --log-dir ~/yam-eval/unbox-dream-001
```

Use a **new directory for each attempt**. `run.py` is required to install the
compound cutter, physical flap joints, tape mechanics and measured-state audit.
The stock one-file command deliberately fails rather than run an unsealed box.
The prototype uses 20 Hz control and existing standard action guardrails. It
accepts 1–2400 steps; 2400 steps is 120 simulated seconds. The partial scripted trial took 169.56 seconds of wall time; runtime for a
full-score trial is not yet established. Do not claim the current 1800-step demo reaches 1.0.

Export each finalized Inspect log with `inspect-robots video RUN/adhoc_ID.json`.
The runner also writes `setup.png`, `trajectory.jsonl`, `score-summary.json`,
source snapshots and SHA-256 hashes. Reset is a fresh process with intact tape,
closed flaps, and every object restored to its fixed starting pose.

## Scoring and mechanics

Final-state scoring with ordered milestones:

- **0:** top seam not completely cut, or an invalid outcome.
- **0.25:** all 21 tape segments cut by a measured, held cutter sweep.
- **0.5:** after cutting, both flaps have reached at least 80° open.
- **1:** after opening, both flaps remain at least 70° open, the item is placed
  within 25 mm in x and y of the receiving-pad centre, its centre is within 8 mm
  of its resting height, and its speed is below 10 mm/s for one second. Both
  TCPs must be over 65 mm from the item. The cutter must be within 45 mm of
  its pad centre and 25 mm of its initial height, move slower than 20 mm/s,
  and no longer be held.

Tape cuts require the measured blade tip within 6 mm laterally and 4 mm
vertically of the seam, blade axis within acos(0.9) of down, and cutter handle
within 35 mm of a measured TCP with 8–38% jaw opening. Successive valid samples
must be at most 100 ms apart, and blade speed 2–250 mm/s. Short passes accumulate
coverage; lifting or leaving the seam cannot bridge an uncut region.

Forcing a flap more than 12° while tape remains, dropping the item centre more
than 20 mm below the table, dropping the cutter centre more than 30 mm below
the table, or nonfinite telemetry invalidates all credit, permanently.

The tape latch physically locks both revolute hinges until all segments are cut.
Cutting releases their angular limits; robot contacts must then move the flaps.
The runner does not teleport the cutter, item or flaps or attach them to a hand.
Darkened tape segments visualize the measured cuts.

## Fidelity and limitations

This is rigid cardboard with ideal hinges and an ideal fixture. Tape is a
geometric blade-sweep fracture approximation releasing a hinge latch, not a
calibrated adhesive, fracture-force or flexible-strip simulation. Grip proximity
and jaw opening are a grasp proxy, not contact-force confirmation. Cutting depth,
cardboard tearing, tool/item damage and real material friction are not validated.
The cutter is a small guarded package-opening tool, not an unrestricted knife.
Real cardboard and tape need calibration before claiming physical fidelity.
Visual/physics validation, robot full-score feasibility and novelty review remain
required. The initial scripted flap-grasp paths may need substantial revision.

## Local tests

```bash
python3 -m unittest -v test_scoring
```

These tests establish scorer logic, not physics realism or robot feasibility.
