# Pick up and roll a die — task review

Assessment: 2026-11-03. Current scorer: **roll-a-die-v3**.

The task now uses a coloured, pip-marked die and directly observable pickup,
release, turnover and rest criteria. A fresh recorded demonstration earns
**1.0 in 9.10 simulated seconds**. The final camera-matched Dream evaluation earns **0.0** after its full
60-second allowance; it does not establish a qualifying pickup. Final media is
uploaded as **M-PV3ZXY**, and [submission PR #44](https://github.com/robocurve/benchmark-tasks/pull/44)
is open. Robocurve received it as **TK-YBZD4Q** at 14:41:54 UTC and reports
**waiting for review**. This is receipt, not acceptance.

## Task and purpose

The robot picks up a die, releases it so a marked face turns from facing up to
facing down, then leaves it to settle. Category: **Societal relevance**, as one
component of helping someone participate in tabletop games. No particular
number is requested, and randomness or statistical fairness is not tested.

| Item | Specification |
|---|---|
| Robot/environment | Calibrated two-arm YAM station, Isaac Lab-Arena / Isaac Sim 6.1. |
| Die | One sharp-edged 16 × 16 × 16 mm cube, 5 g; six coloured faces with 1–6 pips; opposite faces sum to seven. |
| Initial pose | Centre (0.20, 0.16, 0.7555) m; identity orientation; white 1 up. |
| Table | 1.10 × 1.30 m, top z=.7475 m, centre x=.36 m/y=0. |
| Trial | Seed 0; no jitter; 20 Hz control/audit, 240 Hz physics; maximum 1,200 actions / 60 seconds. |
| Recording | Three original policy views plus a separate 1600 × 1280 close-up and visual rulers; the close-up is not sent to Dream. |

The six face colours and pips are render-only paint on the original collision
cube. They add no contact geometry, mass or rolling aids. Primitive friction,
sharp corners and homogeneous mass remain approximations to a physical die.
The scale guides are visual references, not physical obstacles; perspective
must be considered when comparing objects outside a ruler's plane.

## Scoring and what the demonstration shows

- **0.25:** hold the die's bottom at least 30 mm above the table for 0.20 s.
- **0.5:** after pickup, release it at least 10 mm above the table with both
  gripper tool centres at least 50 mm away.
- **1.0:** after release, one marked face points up within 30°, then the same
  face points down within 30°, followed by one continuous second of rest.

Rest uses a fixed pose: movement at most 2 mm / 5°, a face within 10° of level,
bottom within 3 mm of the table, and both tool centres at least 60 mm away.
Leaving the allowed table area or a tool returning inside 50 mm after release
erases all credit. Full details are in the [judging guide](../tasks/roll-a-die/JUDGING.md).
Pure yaw, held rotation and accumulated small rocking cannot earn turnover credit.

Final demonstration `die-v3-demo-002`: pickup at **4.60 s**, release and cyan
**5 up at 7.85 s**, then red **2 up at 8.00 s**. Since 2 is opposite 5, this is
visible evidence that 5 points down. Continuous video preserves face identity.
The die rests from **8.10–9.10 s**, ending with white 1 up. The audit reports
272.987° cumulative tilt travel, a diagnostic rather than a full-revolution
claim. The policy commands only robot joints and grippers.

The demo used **182 actions** and **44.457 seconds of VM wall time** (about
**$0.041** at the observed $3.28/hour rate). A preceding run scored identically,
but its low camera partly hid the upward face; the final raised view resolves
that presentation issue. Two matching demonstrations are useful evidence,
not a statistical reliability study.

Dream used **184.133 seconds of VM wall time** (about **$0.168**), with 25
requests in one continuous session and no retries. It returned 380 prediction
rows outside action bounds, including unused final-chunk rows. Standard execution
clamps applied; all 1,200 executed Dream actions and all 182 demo actions pass
position and per-step-limit checks. This is a model result under those shared
execution limits, not a transport failure. Dream API dollars are not reported.

All **48 tests pass** (35 scorer, 10 bridge, 3 recorded-evidence/source checks).
Both final measured trajectories independently replay to their recorded scores.
The complete H.264 videos have 183/1,201 frames at 20 Hz, browser fast start,
and sizes below 50 MB. The setup image is below 10 MB.

The complete development/recording session, including preparation and the
six-minute shutdown, spans 26m40s from start request to confirmed stop: a
conservative **$1.46 Brev estimate** at the observed running rate. The VM is
**STOPPED**. Billing is delayed; this is not an invoice and excludes later
retained storage and Dream API charges. Reusing the installation avoided the
previous cold setup.

## Readiness and acceptance

This revision substantially improves manual judging: faces are identifiable,
turnover is visible, and acceleration/angular-velocity estimates are no longer
part of the rubric. A ruler, paused frames, angle guide and timestamps can
check the specified events. The scorer still uses tool-centre distance as a
hand-clearance proxy; visual review must also reject support or contact by
other robot links. Sampling at 20 Hz can miss faster motion.

The source, numeric evidence, complete videos and setup screenshot form the
review package. [VALIDATION.json](../tasks/roll-a-die/VALIDATION.json) records
current measured results and hashes; older blank-cube evidence is explicitly
historical. The task is more reviewable than v2, but acceptance remains a
reviewer decision. Importance/novelty, physical fidelity and the strength of
the game-assistance relevance still matter. Immediately before submission,
the refreshed live board (128 entries: 38 pending and 90 pilot) and 43 public
PRs showed no direct dice-roll duplicate.

**Submission:** the user explicitly authorized media upload and the PR on
2026-11-03. Media **M-PV3ZXY** is referenced by `task.json`;
[PR #44](https://github.com/robocurve/benchmark-tasks/pull/44) contains only the
21 files under `tasks/roll-a-die/`, received at commit `ba4ac81`. Private
reference documents, credentials, local artifacts and shared team notes are
excluded. The ingestion validator's text-length findings were corrected
before receipt: fidelity is 406/500 characters and scores is 275/300. Detailed
audit information remains in the task documentation. The task is now held
unchanged while waiting for review.

Run commands: [task README](../tasks/roll-a-die/README.md). Shared operating
lessons and overall cost accounting: [TEAM_LEARNINGS.md](../TEAM_LEARNINGS.md).
Final local media: `artifacts/roll-a-die-v3/` (git-ignored).
