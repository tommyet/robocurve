# Seal a laboratory sample plate with adhesive film

Cover the prepared plate with the loose film, press around the wells using the roller, and leave every well individually sealed. This is a common manual sample-storage procedure; an apparently covered plate can still leak through wrinkles between wells.

## Setup and material model

Use a 96-well polypropylene plate with a 127.76 × 85.48 mm footprint, 9 mm well pitch and 34 mm height; 130 × 80 × 0.1 mm adhesive PET storage film; a clean release liner and raised tray; and a padded hand roller with a 50 mm-wide wheel in an open 76 × 42 × 50 mm bench rest. The tool is not attached to the rest. The loose plate remains upright on the table. Operator preparation fills the wells and removes the backing before placing the film adhesive-side down on its non-stick liner. Peeling backing is not part of the task. Alternating coloured and clear water supports later leakage inspection.

The film uses 216 passive connected sectors, with bending and native collision. The roller wheel rotates freely and its native padding compression supplies the pressing load. Adhesion requires actual rim proximity, roller load and dwell. Bonds start at the measured position and can break. The model does not simulate liquid flow or adhesive chemistry. A connectivity calculation estimates whether each well has a path to another well or the outside; it does not certify molecular sealing or long-term storage.

The physical design follows an ordinary storage-film and roller procedure, not heat-sealed PCR foil. Relevant manufacturer references: [Azenta roller applicator](https://www.azenta.com/products/adhesive-seal-roller-applicator), [seal selector](https://www.azenta.com/seal-selector). Coloured-water testing follows the principle in [Eppendorf Application Note 239](https://www.eppendorf.com/product-media/doc/en/159628_Application/Eppendorf_Consumables_Application-Note_239_Deepwell-Plates_Microplates_Eppendorf-Deepwell-Plates-Microplates-Investigations-sealing-methods.pdf); the final reproducible test protocol still needs to be fixed for this chosen setup.

## Scoring

After three seconds clear of the plate and tools, score the fraction of 96 wells individually covered and isolated from neighbours and the outside. A missing cover, wrinkle channel or lifted region can lose credit even if most film adheres. Torn film, broken objects or spilling invalidates credit. Real assessment uses photographs and a specified coloured-water leak check; the simulator's interface proxy must be disclosed alongside those criteria.

## Run and score

Use the pinned Isaac/YAM environment in `ENVIRONMENT.json`. A CUDA GPU is required for native physics and camera rendering; the offline scorer runs on CPU.

```bash
python tasks/seal-a-laboratory-sample-plate/run.py --mode demo --out /tmp/seal-a-laboratory-sample-plate-demo
DREAM_API_KEY="$DREAM_API_KEY" python tasks/seal-a-laboratory-sample-plate/run.py --mode dream --out /tmp/seal-a-laboratory-sample-plate-dream
python tasks/seal-a-laboratory-sample-plate/rescore.py /tmp/seal-a-laboratory-sample-plate-demo
```

The runner saves every 20 Hz action, native object poses, measurements, camera frames, events and an immutable source snapshot. `rescore.py` verifies the recorded source hashes and recomputes scores from that snapshot. It is not a second physics run. `make_plan.py` authors ordinary robot actions; neither reach checks nor synthetic scoring controls demonstrate feasibility.

No task object follows a scripted animation. Geometry is reset once. During execution the robot supplies ordinary joint commands; native bodies, contacts and passive joints determine the outcome. Any finite pinch approximation requires opposed finger contact, starts at the measured pose, transmits reaction force, and releases or slips. The same hardware and physics apply to Dream and the demo.

## Validation status

**Development draft. No qualifying full-score demonstration or matching Dream baseline yet. Do not submit this folder in its current state.** Runtime, evidence hashes, final scores and the media ID will be recorded after native validation.
