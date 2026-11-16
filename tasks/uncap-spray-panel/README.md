# Uncap a spray can and coat a circular plaque

Remove and park the cap, coat the fixed80mm white plaque, then hold the can
upright and steady in the left gripper with the nozzle released and right hand
clear. The can need not be set down. Exact layout, scoring, reset and fidelity
are specified in `task.json`, `config.py`, `mechanics.py` and `scoring.py`.

**Reviewer revision in progress. The previous demo rescores0.25 under the new visible-area rule; a new full demo and completed Dream run remain pending. Media bundleM-Q4X9HF still describes the previous revision.** The historical privileged-teacher029 run scored
1.0; it is development evidence and is not submission-policy proof. The recorded policy and failed Dream attempt are documented separately.

## Setup and score

The fixed seed0 scene contains two ordinary YAM arms, a capped250g can with a
moving spring-return nozzle, blue cap pad, grey can pad/50mm riser, white80mm
plaque,360mm backing, steel stand and work mat. Coordinates are world metres;
table z=0.7475. No jitter or convenient grasp handle is added. `task.json`
lists every object, size and starting pose; the setup screenshot is included in the media bundle.

Scores are0.25 for removed/parked cap;0.50 for at least50% visibly painted plaque area with no more than7.5398cm² visibly painted backing outside it;0.75 requires90% coverage.1.00 adds the measured upright, steady left-held/nozzle-off/opposing-contact/right-clear finish spanning1.0s. Coverage and off-plaque area share the same visible-color threshold; boundary cells contribute their circle-clipped areas. See [PHOTO_SCORING.md](PHOTO_SCORING.md). The episode records a further full second at score1.0 before terminating. Invalid samples/drops or unsupported spraying invalidate all credit. The cone/paint model remains uncalibrated.

This is a household DIY plaque repainting task in the Societal relevance category (the review called this Societal relatability). For real aerosol trials, follow [AEROSOL_PRECAUTIONS.md](AEROSOL_PRECAUTIONS.md) and the actual product label/SDS.

## Run and score

Requires the pinned YAM/Inspect Robots Isaac environment, NumPy, renderer and
model-service access for Dream-1. The package retains the custom native runner;
loading `task.py` alone does not install its passive mechanics/scorer adapter.
The tested runtime is pinned in `RUNTIME.json`: Ubuntu24.04, Python3.12.16,
IsaacSim6.1.0.0, InspectRobots1.0.0/agent0.30.0, and yam-arena revision
`0059d02a1a91bc6834c1d0846022891df0c78730`. The YAM launchable source is
`https://github.com/ttpierson/YAM-inspect-Isaac` at
`25a2963d10451265dd2a6cbddea69d6a3b3b9b0d`; Arena is
`https://github.com/isaac-sim/IsaacLab-Arena` at
`c7edf3a9d5d8276565208f72422f8f8a0806d6cf`. Native physics960Hz uses the
baseline body solver. The demo was tested on one L40S; runtime on other hardware
is unmeasured. Run `bash launchable/setup.sh` in the launchable repository checked out at that
revision before running these commands. The exact installer is
[launchable/setup.sh](https://github.com/ttpierson/YAM-inspect-Isaac/blob/25a2963d10451265dd2a6cbddea69d6a3b3b9b0d/launchable/setup.sh);
this task reuses its installed Arena environment rather than a separate Python
virtualenv. Full package version pins are in `RUNTIME.json`. Use a NEW log directory and fresh native reset:

```sh
# Revised candidate: common held-can aim translation; fresh validation pending.
python tasks/uncap-spray-panel/run.py --policy aimed-demo --stage full \
  --physics-hz 960 --max-steps 1200 --log-dir /tmp/spray-recorded-demo

# Dream-1 attempt. The recorded attempt failed in RTX; no completed score is claimed.
python tasks/uncap-spray-panel/run.py --policy dream --stage full \
  --physics-hz 960 --max-steps 1200 --log-dir /tmp/spray-dream

# CPU checks (NumPy and the pinned yam_arena import path required).
python -m unittest discover -s tasks/uncap-spray-panel -p 'test*.py'
```

Seed0 and object_jitter0 are fixed by the runner. Control is20Hz; physics960Hz;
limit1200 applied14D joint/gripper commands/60 simulated seconds. The replay
has779 unchanged recorded actions plus at most40 final-hold actions:819 actions/
40.95s maximum. Measured scores are emitted by the native runner/registered
`task_score` scorer, using actual state/contact/dose telemetry. Missing samples
invalidate the trial. Preserve sources, run log, mode, result, trace and media.

Under the HISTORICAL emitted-fraction rubric, standard-reset playback030 reached1.0 in779 actions/38.95 simulated seconds,
with100% coverage and5.24152% overspray. Independent geometry/dose/scoring audit
passed; all779 actual14D commands exactly match the frozen action dataset.
Launch was20:41:11UTC; the completed score-summary file was written20:46:19.24UTC,
308.24s later including startup. This is not a precise simulation-loop benchmark. Tested versions/revisions are
in `RUNTIME.json`. Demo video contains all780 captured states at20fps/39s.

## Demo provenance and observation contract

`recorded_demo.py` reads only `Observation.state_time`; its reset ignores scene
state. It imports no teacher/telemetry/FK/native-object interface and has no
feedback fallback. Dataset779 ordinary bounded14D commands came from the
privileged029 teacher offline, unchanged:
SHA256`18c5770b6db55699669193644402a8e3ccc033e656436fc910a9111e3ff0bd63`.
This is fixed-layout playback, not an autonomous generalization claim. See
`RECORDED_DEMO.md` and the bundled dataset/metadata for alignment and hashes.
The separate `--policy demo` is the privileged development teacher and is NOT
submitted as the observation-limited demonstration. Under the HISTORICAL rubric, fresh initial-state
playback030 reached1.0 within the declared limit; that does not establish the revised area score. TraceSHA256:
`5e471c1f9f3d183865c19e04f4f2dd39375f101185b18abc6279627f78f2353c`.

## Evidence and media limits

Historical teacher029 has an audited1.0/100% coverage/5.24152% overspray result,
with an explicitly labelled offline exact-physics replay. It stopped before its
auxiliary20mm finger-face cleanup; no can parking/cleanup completion is claimed.
Those historical details remain in `VALIDATION.json`, clearly distinct from
the fresh clock-demo proof and failed model-attempt evidence.

`--no-video` is an engineering-only option: the runner marks it diagnostic,
state-only and media_eligible=false. Its pose/paint replay is OFFLINE animation
of recorded physics, not native RGB footage or model camera observations.
The clearly labelled faithful offline Storm render depicts the SAME fresh
clock-only native episode after full source/geometry/paint/score audit; raw
diagnostic flags remain unchanged. Public rules do not expressly ban
such demo rendering, but reviewer acceptance is uncertain. Dream still requires
actual camera observations and genuine model video. The780-frame same-episode demo and first-frame setup screenshot are prepared.
The genuine Dream attempt failed before any recorded action. Its2.4s video
contains48 actual native RGB arrays per camera; it is initialization footage,
not a completed model trial. No model score is claimed. The exact renderer error
was `VkResult: ERROR_DEVICE_LOST`, followed by `submitToQueueCommon failed.` and
`A GPU crash occurred. Exiting the application...`; process exited139.
The SDK entered its inference call, but there is no action or provider-response
record; whether the HTTP request reached the provider is unknown. Source and error evidence are retained. The uploaded media bundle is `M-Q4X9HF`.

## Revision evidence status

The fixed area allowance and shared visibility threshold were chosen before rescoring030. Independent CPU replay of its unchanged measured states gives99.681%painted plaque area and13.895cm² painted backing: revised score0.25, not1.0. Historical audit files describe the earlier rubric. A shorter ordinary-command spraying candidate is being prepared; counterfactual dose calculations are not fresh native evidence. The reviewer-required completed Dream run remains outstanding.

A common-translation clock-only candidate is in preparation: move both TCP paths22mm forward and2mm right while clear, then preserve the original press/release timing. A direct action-skipping candidate was rejected by press-face geometry checks before native execution.

The revision predeclares a shared60-second/1200-action limit for both Dream and the scripted demo, replacing the previous120-second default. The complete planned demo is at most40.95seconds including the physical final hold. This task-design change was fixed before obtaining any new model outcome; a wall-time interruption is not a completed model result.
