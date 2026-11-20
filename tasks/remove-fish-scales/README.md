# Remove fish scales without cutting the skin

Finish descaling the exposed side of a prepared whole fish. Hold the loose fish, scrape against the scales with the hand scaler, then release it on the board with its skin intact.

## Setup and material model

The fish lies on one side on a 250 × 300 × 8 mm wooden cutting board. Its underside has already been descaled as operator preparation. The exposed side has overlapping scales. A loose stainless hand scaler lies alongside it. The fish is approximately 260 mm long and 250 g; the tool has an ordinary handle and a serrated 56 mm-wide head. Exact geometry and the fixed starting layout are in `geometry.py`.

A rigid native fish body, including the tail, carries compliant skin patches and 26 small groups of overlapping scales. Actual tooth contact, normal load and tail-to-head travel accumulate work; sufficient work releases a scale group. Released groups remain physical objects. Excessive skin compression or a broken tissue joint invalidates the attempt. This approximates tissue and scale retention, not flesh deformation, tail tearing or individual microscopic scale mechanics. Both arms have 40 × 6 × 1 mm finger extensions with a 4 N jaw limit. Contact-checked compliant pinch joints are limited to 5 N and 0.10 Nm, release when fingers open and slip after 3 mm of material movement through the contact. The underside is prepared to avoid repeating the same scraping on a second side; it does not remove the support, force-control or directional-scraping requirement.

## Scoring

After three seconds with both hands clear, score the fraction of the initially scaled area left free of scales, provided the fish remains on the board and the skin is intact. Damage, crushing or losing the fish gives zero. Before/after photographs with a ruler allow a real assessor to compare the exposed area and check for skin tears. The simulation counts equal-area scale groups and applies the disclosed skin-damage proxy; it gives no credit for merely touching or lifting the fish.

## Run and score

Use the pinned Isaac/YAM environment in `ENVIRONMENT.json`. A CUDA GPU is required for native physics and camera rendering; the offline scorer runs on CPU.

```bash
python tasks/remove-fish-scales/run.py --mode demo --out /tmp/remove-fish-scales-demo
DREAM_API_KEY="$DREAM_API_KEY" python tasks/remove-fish-scales/run.py --mode dream --out /tmp/remove-fish-scales-dream
python tasks/remove-fish-scales/rescore.py /tmp/remove-fish-scales-demo
```

The runner saves every 20 Hz action, native object poses, measurements, camera frames, events and an immutable source snapshot. `rescore.py` verifies the recorded source hashes and recomputes scores from that snapshot. It is not a second physics run. `make_plan.py` authors ordinary robot actions; neither reach checks nor synthetic scoring controls demonstrate feasibility.

No task object follows a scripted animation. Geometry is reset once. During execution the robot supplies ordinary joint commands; native bodies, contacts and passive joints determine the outcome. Any finite pinch approximation requires opposed finger contact, starts at the measured pose, transmits reaction force, and releases or slips. The same hardware and physics apply to Dream and the demo.

## Validation status

**Development draft. No qualifying full-score demonstration or matching Dream baseline yet. Do not submit this folder in its current state.** Runtime, evidence hashes, final scores and the media ID will be recorded after native validation.
