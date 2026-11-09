# Magnifier development handoff

Checkpoint: 2026-11-09 UTC, through `pickup-005`. This is a development
workbench, not a submission-ready task. Real optical enlargement is demonstrated;
the robot can pick up, centre and retain the tool. The current demo lasts
26.5 seconds and demonstrates a continuous three-second optical benefit.
The user authorized development, **not an upstream PR for this task**.

## Evidence

Records, frozen source, images and video are under the ignored directory
`artifacts/magnifier-optical-session/`. Preserve these alongside the code when
handing over; they are not included in Git. The working source may advance beyond
these runs.

| Run | Result |
| --- | --- |
| `optical-001` | Startup failed because Kit's EULA was not accepted. No optical result. The runners now set `OMNI_KIT_ACCEPT_EULA=YES` before importing Isaac Lab. |
| `optical-002` | RT2 completed all six static cases. The 100 mm curvature lens produced **1.911× native RGB enlargement and 1.908× in actual policy RGB**. Both line orientations gained resolved detail under the experimental metric. |
| `optical-003` | PathTracing reference: **1.905× native and 1.907× policy enlargement**, agreeing with RT2 within 0.4%. Five cases were saved; the process reached its external time budget before the baseline repeat. This was not a complete six-case run. |
| `pickup-001` | Failed with `KeyError: 'tool_root_path'`: the spawn wrapper had not reached the copied rigid-object configuration. The fix wraps both `spawner_cfg.func` and `object_cfg.spawn.func` before scene creation. |
| `pickup-002` | Completed, but the loose grip let the tool roll. |
| `pickup-003` | Completed 370 actions at 20 Hz (18.5 simulated seconds). Closing the right gripper to zero normalized opening retained the tool using ordinary contact. Centering is insufficient; the saved optical comparison **does not pass** the experimental gate. |
| `pickup-004` | Completed 490 actions / 24.5 seconds with measured-tool feedback through normal right-arm joint commands. Both five-bar groups are readable; all 13 saved hold samples show at least 1.872× enlargement. The full photo score remains **0** because the frame hides the outer registration marks. This prompted a chart-layout correction, not a scoring-threshold change. |
| `pickup-005` | Completed 530 actions / 26.5 seconds with the corrected outer marks and a five-second hold. All 61 frames in the final three seconds show both readable groups and at least **1.8797×** enlargement. Final reference registration shifts by only 0.083 pixel. The V1 per-frame detector intermittently loses a tiny mark under different illumination; its original failed audit is preserved. |

The corrected **V2 registration detector passes the strict hold check on all
61 frames**, with photo-hold score 1.0 and maximum outer-mark displacement
0.150 pixel against the unchanged 1-pixel limit. It compares each mark with its
local background, instead of using central swatches under different lighting.
It retains contrast, expected-size and shape checks. The four edge-gain and
bar-count rules are unchanged. Both an independent audit and the root agent's
offline rerun agree. This is a certified **optical hold**, not yet a complete
competition score or Dream result.

The optical audit files are `optical-002/independent-image-audit.json` and
`optical-003/independent-image-audit.json`. They verify saved native/policy arrays,
control cases, and unchanged physics/joints. Lens-free and IOR 1 controls stay
near 1×; the tilted lens fails the gate. The stronger 75 mm curvature candidate
has distorted registration and fails the full gate: its larger apparent gain
is not a validated improvement.

The original chart/scorer remain exploratory. Some fiducials occupy only one policy
pixel, the affine map approximates nonlinear distortion, and normalized fitted
modulation is **not Michelson contrast**. These numbers establish feasibility,
not a competition score or calibrated real-world resolving power.

`inspection_target.py` and `inspection_measure.py` provide the simpler judging
chart: two groups of five whole bars, and outer marks that verify the camera
stayed in place. The metric counts existing image pixels; it does not use a
fitted grating or enlarged image to claim visible detail. Its photo score alone
does not certify pickup or the continuous hold. Version 2 moves the outer marks
beyond the opaque frame. Preserve version 1's failure evidence.

The final physical audit reconstructs 531 measured poses with no tested
conservative-box overlaps. In the last three seconds, lens movement spans only
0.059 mm and its axis stays within 0.164 degrees of vertical. The camera is
unchanged. The first 491 measured states exactly repeat pickup-004. These are
sampled FK checks, not a complete self-collision or continuous-time proof.

Both Brev sessions are confirmed stopped. Their combined conservative elapsed
cost is **$2.12**, including startup and shutdown; there were **zero Dream calls**.
This is an estimate, not an invoice, and excludes later retained storage.
Numeric evidence and costs are in `evidence/`; the ignored final preview is
`artifacts/magnifier-optical-session/pickup-005/preview.mp4`. Its wrist inset is
the actual 224×224 stream displayed at 2× for viewing; scoring uses original pixels.

## Scene and fidelity

The closed biconvex lens is 60 mm in diameter, with 100 mm curvature radii,
1 mm edge thickness and approximately 10.21 mm center thickness. OmniGlass uses
IOR 1.5, zero roughness and `thin_walled=false`. The 100 mm value is a curvature
radius; effective focal length is approximately 102 mm. See
[OmniGlass documentation](https://docs.omniverse.nvidia.com/materials-and-rendering/latest/templates/OmniGlass.html).

`tool.py` adds the glass and 32 convex rim sectors to one dynamic handle body.
The handle is 80 × 20 × 18 mm; the rim has 30/34 mm inner/outer radii and is
18 mm thick. Total tool mass is 120 g. Friction 0.7, restitution 0,
0.2 mm contact offset and zero rest offset are modeling assumptions, not measured
hardware properties. Glass is unbreakable. No attachment joint, magnet, imposed
object motion or grasp helper is used.

The pickup scene has a fixed 120 × 100 × 7.5 mm target plate, top at z=0.755 m;
its print is at `(0.35, 0.05, 0.7551)` m. The table top is z=0.7475 m.
The static optical test instead fixes visual lens/target geometry relative to
the camera; it does not demonstrate pickup.

Evidence uses the existing wrist camera: fixed calibrated pinhole/OpenCV
intrinsics, 640 × 360 native RGB and the wrapper's actual 224 × 224 RGB resize.
No camera zoom or image enlargement is substituted for refraction. Autofocus,
physical camera blur/MTF, coatings and glass imperfections have not been
validated. After pickup, the lens-hidden comparison freezes physics at the
same final camera/target pose; these evaluation images are not policy inputs
during control.

## Reproduce and continue

Run CPU checks and generate a chart from the repository root:

```bash
.venv/bin/python -m unittest magnifier_workbench.test_lens
.venv/bin/python magnifier_workbench/measure.py --self-test
.venv/bin/python magnifier_workbench/inspection_measure.py --self-test
.venv/bin/python magnifier_workbench/score_hold.py --self-test
.venv/bin/python magnifier_workbench/target.py \
  --output-dir artifacts/magnifier-next/target
.venv/bin/python magnifier_workbench/inspection_target.py \
  --output-dir artifacts/magnifier-next/inspection-target
```

GPU commands below assume this checkout and the installed YAM/Isaac environment
on an already coordinated GPU host. The development VM already has the adapter;
do not reinstall it. A fresh machine needs the pinned environment described in
the team setup notes. The committed motion plan is sufficient for replay.
Use a fresh output directory for each run; both runners reject existing ones.

```bash
ISAAC_PY=/data/IsaacLab-Arena/.venv/bin/python

"$ISAAC_PY" magnifier_workbench/probe.py \
  --out artifacts/magnifier-next/optical-rt2 \
  --target-dir artifacts/magnifier-next/target \
  --mode RealTimePathTracing --renders 32 \
  --target-distance 0.200 --lens-distance 0.125

# Current physical prototype: firm grip, bounded centring, five-second hold.
"$ISAAC_PY" magnifier_workbench/pickup.py \
  --out artifacts/magnifier-next/pickup-replay \
  --target-dir artifacts/magnifier-next/inspection-target \
  --plan magnifier_workbench/motion-plan.json --align-steps 60
```

For a PathTracing reference, use a separate output with `--mode PathTracing
--renders 64` and an explicit external time budget. The original 241-second
budget expired before the final control. Historical runs require their frozen
source and target; current commands can produce later revisions. The current
planner defaults to the firmer zero-opening target at the unchanged 50 N actuator
limit. Nominal IK/collision checks do not prove physical retention.

`probe.json` records installed versions: **isaaclab 17.0.2, isaacsim 6.1.0.0,
inspect-robots-yam 0.38.0**. Preserve this environment and source hashes. The
runners explicitly configure `IsaacRtxRendererCfg.global_settings` with ambient
light 0, `antialiasing_mode=None`, and `enable_dlssg=False`. They disable
`/isaaclab/render/deterministic`: that helper otherwise forces RT2 and can
silently replace a requested PathTracing mode. This is not a claim of bitwise
deterministic rendering. A named antialiasing mode can also reset the renderer.

The requested mode is `/rtx/rendermode`; RT2 uses `/rtx/rtpt/maxBounces=6` and
`/rtx/rtpt/maxSpecularAndTransmissionBounces=6`. PathTracing uses the equivalent
`/rtx/pathtracing/` keys, also 6. Legacy translucency is enabled with 6 refraction
bounces. Check the **actual** recorded mode after camera initialization. The
static probe calls `sim.render()` and forces camera recomputation while asserting
unchanged physics steps and joints, then checks raw RGB against the wrapper's
actual image. See [Isaac Sim rendering modes](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/reference_material/rendering_modes.html).

## Remaining work

1. Finalize the combined optical/physical score and the real-trial reference
   protocol. A fixed camera and fixed target must be established, not assumed
   merely because the arm received stationary commands.
2. Keep the original V1 failure and its source alongside the passing V2 audit.
   Twelve synthetic photo checks cover illumination gradients, antialiasing,
   shadows, missing/occluded marks, camera motion, digital zoom and blurred detail.
3. Freeze a concise, numeric rubric combining physical pickup/hold, optical gain
   and resolved detail. Reviewers must be able to check it with simple image
   measurements; movement closer to the target must not substitute for a lens.
   The current native row/column bar-count implementation also needs camera-roll
   invariance checks: a rotated but readable target must not lose credit solely
   because a complete horizontal or vertical scanline no longer fits its patch.
4. Record and rescore the final full-score demo and a matching Dream run; write
   the task setup, fidelity, reset and run instructions, then review every
   competition criterion. No Dream run or submission package is established by
   the evidence above. Request submission authorization only once reviewable.
