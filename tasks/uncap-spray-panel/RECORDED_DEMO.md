# Historical dataset and revised early-release candidate

The original779commands remain bundled unchanged for provenance. Under the revised visible-area scorer, native030 scores0.25, not1.0. The revised aimed_demo.py reads a separate pinned779-command dataset, compiled offline by compile_aimed_demo.py from the original commands. Both TCP paths receive the same smooth22mm-forward/2mm-right offset between actions530and610 while the parked cap is clear and the can is held. Orientations, all gripper commands, the prefix through530, and the original press/release timing are preserved. The online policy reads only state_time; no teacher, geometry, contacts or state estimates are read. A direct early-release splice was rejected before native use.

NewdatasetSHA256:a355dc44db2a9a238eb23617c947650560f40444ae953efee4c17d73526feb05. MetadataSHA256:bc0ceb26ada7826af44df2ddb94e38e66c37f583361ca83cee523bf810b63e22. All779commands plus40bounded final holds fit within the revised1200-action/60-second limit. Recompiling changes the candidate and requires new native validation; do not regenerate after validating a recording.

CPU waypoint IK, exactfloat32 transport and full robot-geometry screens passed. The common translation changes the finite riser support footprint; actual can support, grasp and nozzle motion remain native-validation requirements. No new full-score claim is made here.

## Historical original playback documentation

# Clock-only recorded demo candidate

This fixed-layout, seed0 policy replays the **779 recorded commands** from
`spray-held-029`. That teacher used privileged object/contact telemetry offline.
The new policy itself reads only `Observation.state_time`; it does not import
or call the teacher, telemetry, FK, scene, native object state or a fallback.
It ignores `reset(scene)` data. Ordinary images and joints may be supplied by
the harness but are not read by this policy.

`recorded_demo_actions.jsonl` is the unchanged action log, SHA256
`18c5770b6db55699669193644402a8e3ccc033e656436fc910a9111e3ff0bd63`.
The source trajectory SHA256 is
`724856a92bb31df854fd49403fdf10c83415855133be994331406b2ab5550997`.
Initial trajectory row0 has no action; action i is held during
[i/20,(i+1)/20] and corresponds to post-step row i+1. Every recorded command is
within the pinned URDF action bounds, so original adapter clipping was identity;
the same native float32 cast applies on replay. No actions are inferred or edited.

The779 commands take38.95s. The final recorded command is then held for40 ticks
(2s), with request_stop on the last tick: at most819 applied controls/40.95s.
Duplicate clock observations return the same command without skipping a row.
Missing, nonfinite, reversed, off-grid or skipped clocks fail closed. No state
restore, object-pose write, extra force, scorer change or hardware change is used.

Fresh-reset validation command:

```sh
python run.py --policy recorded-demo --stage full --physics-hz 960 --no-video \
  --max-steps 2400 --log-dir /path/to/new-recorded-trial
```

Baseline can/button solver and20Hz control are required. The existing task limit remains
120s/2400 controls. No-video evidence remains state-only and media-ineligible.

**Fresh standard-reset playback030 reached1.0 in779 actions/38.95s.** Independent
source/geometry/paint/scoring audit and exact applied-command audit passed.
The new labelled offline video renders this same780-row native episode.
TraceSHA256:`5e471c1f9f3d183865c19e04f4f2dd39375f101185b18abc6279627f78f2353c`.
The older teacher029 remains development provenance, not the submitted proof.
