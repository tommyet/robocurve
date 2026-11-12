# Tie a necktie on a collar form

**Development package; not ready to submit.** The flat-fabric model, native
cloth bridge and collar diagnostic are implemented. A reproducible settled
starting layout, functional robot knot, final scoring evidence and Dream run
are still missing. There is no task score or media ID.

The proposed task is to tie a four-in-hand necktie on a fixed collar form and
leave it ready to wear. The defining differences from a round rope knot are
the broad fabric's face orientation, folding, front-loop threading and final
fit. A centreline knot invariant alone cannot establish success.

## Local checks

From the repository root:

```bash
.venv/bin/python -m unittest discover -s tasks/tie-a-necktie -p test_local.py -v
.venv/bin/python tasks/tie-a-necktie/run.py --check-only
```

The original 1.40 m mesh is a tapered two-dimensional strip, 35–70 mm wide with
pointed ends. It has 2,513 vertices and 4,464 triangles. These tests verify
topology and that the diagnostic reset distorts edge lengths by less than
0.03%. A full triangle/solid audit also checks at least 1 mm initial clearance
from the neck, mounting post, base and collar points; its regression detects
the former rear-post intersection. These checks do not test knot tying or
retention.

Pale and gold markings run along opposite material edges. With its wide tip
down, a front-facing tie has pale on the viewer's left and gold on the right.
This makes face orientation visible despite a two-sided cloth renderer.

## First GPU checks

Activate the retained Isaac Sim 6.1 / pinned IsaacLab environment:

```bash
python tasks/tie-a-necktie/probe.py --mode collar-drape --seconds 3 --output /tmp/tie-drape
python tasks/tie-a-necktie/probe.py --mode free-fall --seconds 3 --output /tmp/tie-free-fall
python tasks/tie-a-necktie/run.py --mode smoke --steps 60 --out /tmp/tie-yam-smoke
```

The diagnostic begins with an untied half-wrap around the back of the collar
and two uncrossed, initially horizontal free ends. Gravity must form the hanging
shape. This is a physics diagnostic, **not the final task setup**; the final
reset must be a photographed, physically reproducible settled drape, within
both arms' reach. Never replace this with an animated or preset knot path.

The YAM smoke recorder uses the full `task.py` station and collar scene, holds
the ordinary ready joint targets, and saves policy camera video plus native
nodes and robot-link geometry. Those assessor readings never control the arms.
It explicitly resets the raw environment once before the first snapshot and
records the reset's physics step counts, without an extra settling loop.
It rejects a rigid substitute or software attachment and always leaves the
task score null. Its floating-end start remains explicitly diagnostic.

The probe logs native node positions, material parameters, source hashes and
actual runtime. Start at 240 Hz. Inspect fabric/neck contact, self-contact and
whether the tie remains accessible on the table. Passing a drape probe is only
the first gate. Next prove finger friction, threading, knot tightening and
retention, then build a controller using camera observations and robot state.
Do not spend Dream calls on an unvalidated scene. Runtime and an approximately
$3 total task cost are not yet established.

## Physics and fit

The native surface FEM mesh has stretch, bend and self-contact. It represents
the sewn/interlined tie as one effective fabric shell, not every textile layer.
The nominal 1.2 mm thickness and 500 kg/m³ effective density give approximately
36.3 g. Friction, bending and elasticity remain uncalibrated. Native deformables
use dynamic friction; independent static friction is not supported. No vertex
targets, runtime rest-shape edits, attachments or artificial tightening occur.

`layout.py` defines a 110 mm diameter, 65 mm high collar/neck form with fixed
collar points and a 25 mm square post centred beneath the neck at x=0.50,y=0.
The post rises from the 0.7475 m tabletop to z=1.12 m; the 180 x 160 x 12 mm
base is centred at x=0.50,y=0,z=0.7535 m. This keeps the support clear of the
tie's rear half-wrap. `arena_cloth.py` implements the cloth bridge for
YAM, and `arena_props.py` registers the fixed collar geometry. A guarded smoke
runner exists; the observation-based demonstration and final scored runner
remain to be completed after the native checks. Only reset events may restore
nodal state.

`JUDGING.md` requires a retained four-in-hand, correctly facing ends and measured
collar/length fit. No unseen simulator flag proves that a tie is ready to wear.

## Sources and overlap

[NVIDIA surface deformables](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/deformables_beta/deformable_beta.html)
and [the pinned native runtime](https://github.com/isaac-sim/IsaacLab/blob/91a0906f93802eb859192dcb0bca879f891e92d6/source/isaaclab_physx/isaaclab_physx/assets/deformable_object/deformable_object.py)
establish the supported API, not the validity of our material parameters.
[TieBot](https://tiebots.github.io/) is direct prior robotics research. The
wearable fit and flat-fabric distinctions may matter to review, but novelty
relative to existing knot tasks is not guaranteed.
