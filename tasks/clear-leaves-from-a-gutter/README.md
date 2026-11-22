# Clear dry leaves from a gutter

Development: the native demo is still being validated. Do not submit yet.

Remove loose leaves from a full-size roof-edge section and collect them in a bucket. The overhang, curved channel and cross-bracket constrain tool access. Working at height is outside this task.

## Run and score

Use the pinned Linux NVIDIA Isaac/YAM runtime in `ENVIRONMENT.json`, or install it with `bash bootstrap.sh`. From this folder:

```bash
python run.py --mode demo --out /absolute/path/to/demo
python run.py --mode dream --out /absolute/path/to/dream
python rescore.py /absolute/path/to/demo
```

The allowance is 1,600 controls at 20 Hz (80 simulated seconds). The scripted plan uses 1,060 controls. Wall time and actual scores must be recorded after validation. There is one fixed layout and no random seed.

Count whole leaves inside the bucket after both hands release for one second. Divide by twelve. Partial leaves and leaves outside the bucket earn nothing. The bucket must remain within 40 mm of its starting centre and 18.2 degrees of upright. A leaf falling off the table or broken equipment invalidates the trial. A photo, ruler and count suffice; no force measurement is needed.

## Setup and approximation

Dimensions, materials and table-frame coordinates are in `task.json`; `geometry.py` supplies every starting pose. Secure the full-size PVC gutter/fascia section on the bench. Use twelve loose dry leaves approximately 60 × 26 mm and 0.3 g each, with a shallow curl raising the tips about 8 mm above the centre. Avoid wet, sticky or crumbling leaves. Replace torn leaves and restore the picture between trials.

Each simulated leaf has four passive articulated panels with finite bending stiffness, gravity and contact. This approximates dry flexible leaf handling; fine veins, tearing, moisture and brittle fragments are omitted. The scoop has a hollow raised handle and a thin curved mouth. All collection and tipping use native contact; there is no attachment of leaves to the scoop or bucket. Material stiffness and friction are engineering estimates, not measurements of a particular leaf species.

## Assets

Task geometry is generated here under the included MIT licence. The runtime supplies the I2RT robot meshes under its [MIT asset licence](https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/assets/yam/LICENSE.i2rt). Table, floor and camera supports are runtime primitives. Robot assets are not redistributed here.
