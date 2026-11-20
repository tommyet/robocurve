# Fasten a bra’s back hooks on a torso form

Fasten both hooks in the outermost eye row and leave the band untwisted and closed on the form. This isolates holding two elastic ends under tension while aligning and engaging ungated hooks.

## Setup and material model

A fixed torso form wears a prepared two-hook bra with 32 mm reinforced closure tapes and three adjustment rows. The front cups and form are fixed; the non-working garment and straps are supported on the form; the rear elastic wing endpoints and closure tapes are passive physical parts. The ends start unfastened. Dimensions and positions are defined in `geometry.py`; the setup screenshot must show the settled starting layout.

The working wings use passive three-dimensional elastic end links. Intermediate ribbon shape is drawn from their native endpoints; distributed cloth contact, wrinkling and self-collision are not simulated. This reduced model preserves elastic resistance, tape orientation and hook retention, but is not a full garment simulation. The reinforced tapes are rigid, and the metal hooks and eyes have collision geometry. There is no auto-latch or engagement joint. Finger friction is approximated by contact-checked compliant joints limited to 5 N and 0.02 Nm. Both arms have 40 × 6 × 1 mm precision finger extensions and a 4 N jaw limit. This models fastening, not comfort, fit or the complete process of putting on a bra.

## Scoring

Damage or failure to release the closure for three seconds gives zero. One hook retained in its intended eye gives 0.5. Both hooks in the outermost row, with aligned untwisted tapes and three seconds of released retention, give 1.0. An assessor can count engaged hooks in close photographs and observe the released fastening; simulated pocket coordinates and orientation checks operationalise those visible conditions. Grasping or merely bringing the ends together earns nothing.

## Run and score

Use the pinned Isaac/YAM environment in `ENVIRONMENT.json`. A CUDA GPU is required for native physics and camera rendering; the offline scorer runs on CPU.

```bash
python tasks/fasten-a-bra-on-a-torso-form/run.py --mode demo --out /tmp/fasten-a-bra-on-a-torso-form-demo
DREAM_API_KEY="$DREAM_API_KEY" python tasks/fasten-a-bra-on-a-torso-form/run.py --mode dream --out /tmp/fasten-a-bra-on-a-torso-form-dream
python tasks/fasten-a-bra-on-a-torso-form/rescore.py /tmp/fasten-a-bra-on-a-torso-form-demo
```

The runner saves every 20 Hz action, native object poses, measurements, camera frames, events and an immutable source snapshot. `rescore.py` verifies the recorded source hashes and recomputes scores from that snapshot. It is not a second physics run. `make_plan.py` authors ordinary robot actions; neither reach checks nor synthetic scoring controls demonstrate feasibility.

No task object follows a scripted animation. Geometry is reset once. During execution the robot supplies ordinary joint commands; native bodies, contacts and passive joints determine the outcome. Any finite pinch approximation requires opposed finger contact, starts at the measured pose, transmits reaction force, and releases or slips. The same hardware and physics apply to Dream and the demo.

## Validation status

**Development draft. No qualifying full-score demonstration or matching Dream baseline yet. Do not submit this folder in its current state.** Runtime, evidence hashes, final scores and the media ID will be recorded after native validation.
