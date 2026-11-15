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

Candidate command (requires a later authorized genuine fresh reset):

```sh
python run.py --policy recorded-demo --stage full --physics-hz 960 --no-video \
  --max-steps 2400 --log-dir /path/to/new-recorded-trial
```

Baseline can/button solver and20Hz control are required. The existing task limit remains
120s/2400 controls. No-video evidence remains state-only and media-ineligible.

**Fresh native playback has not run and has no demonstrated score.** The older
teacher's1.0 capture/video does not establish this clock-only policy's feasibility
or repair any observation-contract eligibility of the teacher.
