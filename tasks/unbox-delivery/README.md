# Unbox a taped delivery parcel — development prototype

Use the orange guarded cutter to sever the parcel's top seam, return the tool,
open both flaps, and place the blue item on the green pad. This targets receiving
and unpacking deliveries with tool use followed by access and retrieval.

## Status

The feedback scripted controller completed **two full-score trials**, each with
**1.0** after 1,596 actions / 79.8 simulated seconds. Runner wall times were
222.86 and 220.43 seconds. Both start with sealed tape and closed flaps, cut all
21 segments, return the cutter, open both flaps to about 110°, and release the
item on the receiving pad. Independent replay and action/source/video audits
pass for both. Each camera video contains all 1,597 frames at 20 Hz.

Sixteen scorer/controller tests pass. The original prototype scored 0.25, and an
intermediate feedback trial scored 0.5 after dropping the item. These are
historical development results; `VALIDATION.json` records the current evidence
and limitations. The two fixed-layout successes establish feasibility for this
setup. Dream has not been evaluated on this task.

This remains a competition draft. The public PR history identifies a closely
related carton-cutting/opening task, [PR #1856](https://github.com/robocurve/benchmark-tasks/pull/1856),
received as TK-V7P9X9 on November 13. Novelty needs resolution before submission;
no media has been uploaded and no upstream PR has been opened for this task.

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
python run.py --policy demo --max-steps 2400 --log-dir ~/yam-eval/unbox-demo-001
python run.py --policy dream --max-steps 2400 --log-dir ~/yam-eval/unbox-dream-001
```

Use a **new directory for each attempt**. `run.py` is required to install the
compound cutter, physical flap joints, tape mechanics and measured-state audit.
The stock one-file command deliberately fails rather than run an unsealed box.
The prototype uses 20 Hz control and existing standard action guardrails. It
accepts 1–2400 steps; 2400 steps is 120 simulated seconds. The validated scripted trials took about 221–223 seconds of runner wall time.
The 120-second limit refers to simulated time, not wall time.

Export each finalized Inspect log with `inspect-robots video RUN/adhoc_ID.json`.
The runner also writes `setup.png`, `trajectory.jsonl`, `score-summary.json`,
source snapshots, controller events and SHA-256 hashes. Reset is a fresh process with intact tape,
closed flaps, and every object restored to its fixed starting pose.

## Feedback controller and isolated opening test

`demo_policy.py` uses privileged measured flap, item and hand poses for the
scripted feasibility demonstration. It commands ordinary joint/gripper targets.
Dream receives the standard three camera images, joint state and instruction.
The controller does not move object roots, create grasp constraints or change
material properties or scorer thresholds.

The script grasps each tab high enough to keep finger tips off the cardboard,
then moves and rotates the hand about the physical fold. Wrist tilt is capped
at 80° to keep the arm within reach while the TCP completes the opening arc.
Flap progress controls advancement; a stalled/lost tab causes a bounded retry.
The controller checks that each flap remains open after release before retrieving
the item, and parks the arm with a smooth joint-space move to avoid an IK branch
problem during retreat.

The pickup and transport phases preserve the commanded jaw gap, including its
contact preload. Restarting each segment at the wider measured jaw opening had
removed that preload and caused the intermediate trial's drop. Measured item
slip now triggers a bounded pickup retry. Pickup verification and grasp-offset
measurement set the subsequent placement target.

For an opening-only diagnostic, with tape explicitly assumed pre-cut:

```bash
python run.py --policy demo --stage opening --max-steps 1400 --log-dir ~/yam-eval/unbox-open-001
```

This mode cannot earn task credit: task success is disabled, the reported score
is zero, and both its mode file and every trace row are marked diagnostic.
`unbox-open-003` opened and released both flaps at 110°; its maximum planned IK
position residual was 0.083 mm. This is an IK residual, not a measured tracking
accuracy claim. Both full-score trials use the default **full** stage and begin
sealed.

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
The full-score trials establish simulated feasibility in the fixed setup.
Material calibration, broader variation testing and novelty resolution remain
open; the scripted controller has privileged telemetry.

## Tests and reproducible evidence

Pure scorer tests run with standard Python:

```bash
python3 -m unittest -v test_scoring
```

In the installed Arena environment, all 16 tests also cover incomplete-cut and
unreturned-tool gates, bounded stall recovery, diagnostic credit isolation,
reachable wrist motion and preservation of grasp preload:

```bash
python -m unittest -v test_scoring test_controller
```

Replay the committed anonymous full-demo trace without Isaac or NumPy:

```bash
gzip -dc evidence/full-demo.jsonl.gz > /tmp/unbox-demo.jsonl
python3 replay.py /tmp/unbox-demo.jsonl
```

Expected score: **1.0**. `evidence/` also contains both complete-run audit reports.
The curated trace contains scorer inputs and omits stored scores; its hashes and
the original trace hash are distinguished in `VALIDATION.json`.

For a new full run, export its three videos, then capture the installed robot
limits on the VM:

```bash
python audit_trial.py ~/yam-eval/unbox-demo-001 --capture-limits-only
```

On a machine with `ffprobe`, audit the downloaded run directory (preserve its
`actions/` directory, finalized Inspect log, trajectory, limits, controller events,
source hashes and three MP4s):

```bash
python3 audit_trial.py /path/to/downloaded/run --output /path/to/downloaded/run/audit.json
```

The audit checks independent score replay, current runtime source hashes, trace
and action counts, control timestamps, final released placement, executed joint
bounds and command rates against configured actuator velocities, and complete
videos. Inspect's stock action semantics have no per-step maximum configured;
the motion-rate test is an independent audit of the actual executed commands.
Tests and these fixed-layout trials do not calibrate real cardboard or adhesive.
