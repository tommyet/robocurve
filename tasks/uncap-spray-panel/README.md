# Uncap a spray can and repaint a household plaque

Remove and park the cap, spray a blue coat on the fixed80mm decorative plaque while protecting its backing, then finish with the can upright and steady in the left gripper, nozzle released and right hand clear. This is a familiar household DIY finishing job in the **Societal relevance** category. No set-down or unsupported suspension is required; the can may still contact the starting riser while gripped.

**Revised native demo:1.0. Completed Dream-1 evaluation:0.0.** Both use the predeclared1,200-control/60-second limit. The demo video explicitly shows an offline visualization of the same native episode. The model video contains actual native RGB; see the limitations below.

## Setup and scoring

Fixedseed0, no object jitter. The scene contains two ordinary YAM arms, a capped250g orange can with a spring-return button, blue cap pad, grey can pad/50mmriser, white80mmplaque,360mmbacking, steel stand and work mat. Exact dimensions/materials/poses are in task.json, config.py and mechanics.py. The screenshot depicts the initial native scene, rendered offline.

Coverage and paint outside the plaque use **the same visible-blue criterion**: at least50% of the clean-to-blue color change. In simulation this is dose>=0.04effective plume-centre seconds. Exact circle/cell intersection areas handle boundary cells. The fixed off-plaque allowance is **7.5398cm²**,15% of the50.2655cm² plaque area; it never depends on emitted mass. See [PHOTO_SCORING.md](PHOTO_SCORING.md) for the square-on photograph, color references and ruler protocol.

| Score | Required outcome |
|---|---|
|0.25|Cap physically detached and parked within45mm horizontally/12mm vertically of its pad target, speed<20mm/s.|
|0.50|Above, at least50%visible plaque coverage and outside paint<=7.5398cm².|
|0.75|Above, at least90%coverage.|
|1.00|Above, plus can within10°upright/speed<20mm/s, valve travel<0.5mm, rightTCP>70mm from can/cap, both opposing left fingertip contacts>=0.1N; all maintained between qualifying endpoints spanning1.0s.|

The episode retains another elapsed1.0s at score1.0 before success termination. Missing/nonfinite/nonmonotonic samples, a can/cap drop>30mm below the table or emitting outside the supported cone/backing/range geometry invalidate all credit. No scorer condition depends on controller phase names.

Real aerosol trials require the actual product's label/SDS, suitable ventilation, ignition control and protective equipment: [AEROSOL_PRECAUTIONS.md](AEROSOL_PRECAUTIONS.md). The simulation is not an aerosol safety assessment.

## Reproduce

Use the installed Isaac Lab-Arena/YAM environment pinned in RUNTIME.json: Ubuntu24.04, Python3.12.16, IsaacSim6.1, InspectRobots1.0.0, agent0.30.0 and yam-arena0059d02a1a91bc6834c1d0846022891df0c78730. Setup uses [the pinned launchable installer](https://github.com/ttpierson/YAM-inspect-Isaac/blob/25a2963d10451265dd2a6cbddea69d6a3b3b9b0d/launchable/setup.sh). Loading task.py alone does not install the native cap/nozzle mechanics; run.py registers that adapter and invokes Inspect Robots.

```sh
# Fresh native clock-only demonstration; no actor restore or feedback controller.
python tasks/uncap-spray-panel/run.py --policy aimed-demo --stage full \
  --physics-hz 960 --max-steps 1200 --no-video --log-dir /tmp/new-spray-demo
python tasks/uncap-spray-panel/audit_trial.py /tmp/new-spray-demo
python tasks/uncap-spray-panel/audit_aimed_demo.py /tmp/new-spray-demo

# Genuine Dream-1 through Inspect Robots, actual RGB/frame recording enabled.
python tasks/uncap-spray-panel/run.py --policy dream --stage full \
  --physics-hz 960 --max-steps 1200 --render-sync --log-dir /tmp/new-spray-dream

python -m unittest discover -s tasks/uncap-spray-panel -p 'test*.py'
```

Use new output directories and fresh native resets. Both policies get1,200controls/60simulatedseconds at20Hz; native physics is960Hz/48substeps per action, baseline body solver. This limit replaces the previous120-second default and was fixed before the new model outcome. The full demonstration policy is bounded to819controls/40.95s including extra hold. The tested L40S runs took approximately298s(demo) and522s(model), including startup; other hardware/runtime is unmeasured.

## New evidence and limitations

Frozen native source56854fb. Fresh demo applied799ordinary commands over39.95s and scored1.0: **97.4479%coverage,3.01736cm²outside paint**, valid opposing contacts/nozzle release and2.0s final physical hold. The last21states span an additional full second continuously at score1.0. Source, actual commands, all21body poses, nozzle geometry, paint dose/color updates and all-sample scoring independently passed audit. TraceSHA256:3db73f7c4787f393ec9d1fe4be0bf8ed5b06918705b9c4a0d4ae1e990bc8a1e9. See AIMED_DEMO_AUDIT.json and AIMED_PLAYBACK_AUDIT.json.

The demo ran camera-free to avoid earlier RTX failures. Its raw diagnostic/state-only/media_eligible=false flags remain unchanged. The40.0s/800frame demo is explicitly OFFLINE Storm rendering of the same measured native body poses and paint, with disclosed lighting normalization; it is not native RTX footage. No physical states, score samples or final frames were fabricated or frozen. The setup image is likewise offline-rendered initial geometry.

Dream completed the standard1,200-control/60s Inspect Robots evaluation with error=None and score0.0; the cap was not detached and no paint was emitted. This includes32standard observation-preroll controls and1,168model-target controls, under the normal clamp/delta guard. The60.05s/1,201frame composite contains all actual native RGB endpoints. The standardSDK recovered24server-session expirations across25requests/49attempts/25sessions. Server memory reset, and realRTX images are visibly noisy. This is a completed rollout with transport/image-quality confounds, **not an uninterrupted measure of task difficulty**. TraceSHA256:d1cb0608539186095988ab9ad6c8b1b835689bcb1a0c687963fe3c74c3355522. See MODEL_ATTEMPT.json.

The clock-only demo reads only Observation.state_time. Its offline-generated dataset translates both original TCP trajectories22mm forward/2mm right while clear, preserving jaws, orientations, press/release timing and the prefix through action530. No online scene/object/contact/teacher feedback is used. See [RECORDED_DEMO.md](RECORDED_DEMO.md). One successful fixed-seed run is not a reliability/generalization estimate.

The rigid compound can/cap/button, spring forces, finite torsional contact patch and12°cone are uncalibrated approximations.10mmuniform-tint cells approximate paint; the displayed128-sided circular boundary differs from the analytic score by<13µm radially. There is no CFD, solvent chemistry or full-room deposition. Unsupported spraying invalidates rather than silently disappearing from the area measure.

Historical030 met the old emitted-fraction rubric but rescores0.25 under the new area rule(13.895cm²outside). Historical031 failed in RTX before a completed model evaluation. These have been superseded; historical audit files remain labelled accordingly. The new surface visibility/area thresholds were fixed before rescoring or new evaluation.
