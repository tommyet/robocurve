# Fasten a bra’s back hooks on a torso form

Fasten both hooks in the outermost eye row and leave the band untwisted and closed on the form. The skill is holding two elastic ends under tension while engaging small ungated hooks. The garment is already on the form; putting it on and assessing comfort are outside the task.

## Setup

The fixed polymer torso is about 383 mm high, on a 240 × 300 × 10 mm base. Its main body is 160 × 260 × 310 mm, with a smaller upper section, neck and two supported fabric cups. The non-working garment and 12 mm shoulder straps are supported on the form. The two working elastic wings are free at their closure ends.

Each reinforced tape is 30 × 32 × 0.6 mm. Two 0.8 mm-wire hooks are spaced 16 mm vertically; the opposing tape has three eye rows, 9 mm apart. The outer eye bars project 6 mm beyond the fabric edge. This is simplified generic hook-and-eye geometry, not a dimensionally exact product. [BraBuilders](https://www.brabuilders.com/products/hook-and-eye-closures) and [Aimerfeel](https://aimerfeel.com/collections/best-sellers/products/a_139893) describe ordinary two-hook, three-row closures.

Coordinates are metres, with +X forward from the station and +Y to its left. The table is at Z=0.7475. The torso body centre is (0.395, 0, 0.9025); the loose tape centres are (0.270, ±0.040, 0.9025), facing backward. Each working wing has an 83.24 mm rest anchor-to-tape span. `geometry.py` defines the complete fixed layout; there is no object jitter. Both YAM arms use 40 × 6 × 1 mm precision finger extensions with a 4 N jaw limit.

## Scoring

Score the final state using the highest qualifying tier, after both open hands have been at least 55 mm clear for three seconds:

- **1.0:** both hooks remain in their outer-row eyes throughout those three seconds, with neither wing twisted.
- **0.5:** one intended hook remains engaged throughout; the wings are untwisted.
- **0:** otherwise, or if the fabric/hardware is damaged or a working wing exceeds 1.6 times its rest span at any point.

Photographs show the engaged hooks and tape orientation; video shows release and retention under the garment’s own tension. The simulated eye-in-pocket and orientation checks implement those visible conditions. Grasping or bringing the ends together earns no credit. Reset by unhooking both ends and restoring the loose starting layout; replace damaged material.

## Simulation limits

Native compliant end links approximate the working wings, with 20/100/20 N/m translational stiffness and finite rotational compliance. Intermediate ribbon shape is drawn between their endpoints: distributed cloth contact, wrinkling and self-collision are omitted. Reinforced tapes are rigid. Hooks and eyes have native collision; there is **no auto-latch or engagement joint**.

Contact-checked compliant pinch joints approximate finger friction, limited to 5 N and 0.02 Nm. They start at the measured pose, transmit reaction forces, and release on opening or slip. The same model and hardware apply to Dream and the scripted demo. Object poses are written only at reset; the demo supplies ordinary robot joint commands.

## Run and score

Use the pinned Isaac/YAM environment in `ENVIRONMENT.json`. Native physics and cameras require a CUDA GPU; frozen rescoring runs on CPU. Dream reads `DREAM_API_KEY` or the existing private Dream credential file.

```bash
python tasks/fasten-a-bra-on-a-torso-form/run.py --mode demo --out /tmp/bra-demo
python tasks/fasten-a-bra-on-a-torso-form/run.py --mode dream --out /tmp/bra-dream
python tasks/fasten-a-bra-on-a-torso-form/rescore.py /tmp/bra-demo
```

Limit: 1,800 controls, or 90 seconds at 20 Hz. The runner records every action, native pose, event and camera frame, plus a hashed source snapshot. `rescore.py` verifies and uses that snapshot; it does not rerun physics. Seed/layout: fixed, no randomisation.

## Validation

The native demo completed 580 controls with score **1.0**, retaining both hooks for 5.4 seconds with the hands clear. Frozen rescoring and independent checks against the recorded finger collision geometry pass. The matching Dream baseline completed 1,800 controls with score **0.0**; its frozen rescore also passes. One uninterrupted physical episode used 73 API requests; 36 expired-session recoveries are recorded in the transcript. Rendering took about 21 minutes for Dream on an L40S while sharing the GPU with other trials. The rear camera is the unobstructed assessment view, used for the complete uncut episode.
