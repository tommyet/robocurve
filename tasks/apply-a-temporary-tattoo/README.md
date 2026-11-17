# Apply a water-transfer temporary tattoo

Apply the water-transfer tattoo inside the marked area on the practice forearm. Remove the backing and leave the image intact.

**Development draft. No native success, Dream score, media upload or submission readiness is claimed.**

A water-transfer tattoo needs even wetting and careful backing removal to leave the picture intact on a curved surface.

## Setup and reset

A fixed 200 mm long, 64 mm diameter practice forearm with a smooth PVC surface; one 50 x 40 mm water-transfer paper carrying a red heart; a pre-wetted 40 x 40 x 20 mm cellulose sponge in a shallow dish. A 30 x 20 x 10 mm rest supports the paper with its edges overhanging. The tattoo is separate, image-side down, with only its protective film removed. A 40 x 35 mm target is marked on the form. Both hands start open; removable waterproof pad covers protect the rig.

Clean and dry the PVC. Use a fresh water-transfer tattoo and a sponge wetted with 5 ml clean water, squeezed until it no longer drips. Qualify the chosen tattoo/PVC pair by one hand application before trials; replace the PVC cover if removal leaves residue. Do not use semi-permanent or dry-rub transfers.

`geometry.py` records every simulated part, dimension, mass, fixed coordinate and passive joint. The starting photograph must be captured from the final native reset before submission.

## Judging

1.0 if at least 95% of the image transfers inside the target, the backing is fully removed, and both hands have released for three seconds. 0.5 for at least 75% transferred inside the target with the backing removed; 0.25 for at least 50%. Otherwise 0. A torn backing scores 0. Compare a close photograph with the supplied full image and centimetre scale.

## Simulation and limits

Native flexible paper, sponge parts and robot contacts. Sponge compression supplies reaction force; local wetting requires loaded contact against paper on the curved form. After 30 seconds of wetting, native peeling releases the backing and a reduced transfer rule leaves ink on the form. Dry or early peeling loses that image region. Adhesion and water transport are approximated. Native feasibility has not yet been validated.

The manufacturer describes application to non-skin objects as well as skin: https://www.temporarytattoos.com/blogs/news/how-to-apply-a-temporary-tattoo . That supports a practice surface, but it is not a test of this particular PVC/tattoo combination. A physical qualification is specified, not claimed as completed. Target markings, the drawing and the native full-score peel still need validation.

No manipulated object is attached to a hand. Native contact, friction and ordinary joint actions handle grasping. A scripted controller may use privileged state for a feasibility demo; Dream must use only the standard three cameras and joint observations. The geometry and material laws must be identical in both runs.

## Run

Use the Python 3.12 / Isaac 6.1 / YAM environment targeted in `ENVIRONMENT.json`. New-task verification is still pending. From the repository root:

```sh
python tasks/apply-a-temporary-tattoo/make_plan.py
OMNI_KIT_ACCEPT_EULA=YES python tasks/apply-a-temporary-tattoo/run.py --mode demo --out /tmp/apply-a-temporary-tattoo-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/apply-a-temporary-tattoo/run.py --mode dream --out /tmp/apply-a-temporary-tattoo-dream
```

Rescore recorded native body poses with `python tasks/apply-a-temporary-tattoo/rescore.py /tmp/apply-a-temporary-tattoo-demo`. The scorer checks frozen source hashes, trace continuity, bounded joint actions, native break events, and the outcome. This supports, and does not replace, visual inspection of the contact and material behaviour.

Fixed layout; no random seed. Limit: 1,400 control steps (70 seconds at 20 Hz). Actual runtime per trial, complete native evidence and independent scoring will be recorded after successful validation. Do not upload a CPU plot or a kinematic reach check as a successful demo.
