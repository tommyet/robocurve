# Remove a staple without tearing the papers

**Development package; not submission-ready.** The native steel coupon works.
Paper contact, complete extraction and robot feasibility remain unproven. There
is no demo, Dream run or media ID.

The robot removes a clinched staple, then separates two flexible office-paper
sheets. The central difficulty is engaging a remover under the crown and
unbending the legs without damaging the thin paper around their holes.

## Evidence so far

The native 3 mm steel-leg coupon bends only when its diagnostic jaw touches it.
After the jaw withdraws, it retains 0.87567 rad of plastic bend. Moving the jaw
3 mm away produces no motion or plastic set. Halving the physics step from
100 to 50 microseconds changes the residual angle to 0.87322 rad, a 0.28%
difference. The three unedited reports are in `evidence/native-coupon-*.json`;
`VALIDATION.json` records their hashes. These are contact/material tests, not
paper extraction or robot demonstrations. Material parameters are approximate.

There are 38 passing CPU checks for the steel law, punctured meshes,
latched membrane/contact guards, tool approach geometry and photo-based judging.
The older CPU cohesive-opening model remains a research probe; it does not
supply tearing physics in the native scene.

The current supported-edge candidate uses fixed 620 × 420 µm punctures in
coarser, better-conditioned local meshes. An unstapled pair completes 0.1 s at
10,000 Hz with peak membrane strain of 0.272% and 0.283%. The full stapled
control still exceeds the conservative 0.3% membrane boundary at 5.6 ms
(0.368% lower, 0.173% upper); wire-crossing audits remain clean. These controls
are recorded in `evidence/native-coarse-paper-030-031-summary.json`.

Local bending warnings are no longer classified as tears. The native model
still approximates bending elastically and does not retain permanent creases.
Membrane excursions, degenerate geometry and wire crossing remain latched
validity failures. See `MATERIAL_DOMAIN.md` for the distinction and evidence.
Earlier unsuccessful contact controls are preserved in `VALIDATION.json`.

## Reproduce the checks

From the repository root, with NumPy installed:

```sh
python -m unittest discover -s tasks/remove-a-staple -p 'test_*.py' -v
```

In the pinned Isaac 6.1 environment:

```sh
python tasks/remove-a-staple/native_probe.py --out artifacts/staple-positive --dt .0001 --seconds 1
python tasks/remove-a-staple/native_probe.py --out artifacts/staple-negative --dt .0001 --seconds 1 --no-contact
python tasks/remove-a-staple/native_probe.py --out artifacts/staple-half-dt --dt .00005 --seconds 1
python tasks/remove-a-staple/paper_probe.py --out artifacts/paper-free --mode free --seconds .2 --physics-hz 2000
python tasks/remove-a-staple/paper_probe.py --out artifacts/paper-separated --mode free-separated --seconds .2 --physics-hz 2000
python tasks/remove-a-staple/paper_probe.py --out artifacts/paper-stapled --mode stapled --seconds .2 --physics-hz 2000 --sheet-gap-um 120 --crown-gap-um 20
python tasks/remove-a-staple/full_probe.py --out artifacts/staple-full --seconds .1 --physics-hz 10000 --reset-profile supported-edge-candidate --mesh-profile coarse --refined-contact-diagnostic --max-depenetration-m-s .05 --observe-bending-diagnostic
```

Each output directory must be new. Read the JSON result: Isaac shutdown may
leave a zero process exit status after a reported error. The three steel runs
took about 7, 8 and 12 seconds respectively, excluding installation. Full trial
runtime and cost are not established. All setups are deterministic; no seeds.

## Proposed native task

`paper.py` creates genuine 0.1 mm, 80 gsm sheets with explicit puncture holes.
`native_paper.py` supplies surface-FEM paper and independently simulated steel
segments joined by measured-angle plastic hinges. Contact, rather than an
attachment or release trigger, retains the sheets on the staple.

`paper_probe.py` first tests 30 × 24 mm coupons. A fixed crown is an explicit
diagnostic fixture: the free sheets should fall, while the clinched fixture
should support them without crossing intact triangles or exceeding the elastic
validity bounds. Passing that test does not establish extraction.

`full_scene.py` authors two 210 × 148 mm sheets, a **free** staple, a forked lever
remover and a 20 mm-high document support. The upper sheet is offset by 12 mm;
the far edges overhang by 20 and 32 mm to make later separation accessible.
The candidate support is190 ×128mm, with the staple8mm beyond its left edge
and the remover fulcrum on the board. This scene runs but has
not passed its material/contact validity gate;
`setup.json` and `task.draft.json` are provisional until the geometry is tested.
The YAM bridge in `arena_paper.py`, `arena_hardware.py` and `task.py` is authored
but unrun. It exposes measured geometry to an assessor, writes poses only on
reset and fails closed when the material/contact validity guard trips.
`preview_yam.py` is an unrun camera/integration recorder using ordinary ready
joint targets. It audits both FEM sheets and all 61 free hardware bodies. Run
it only after the native contact gates; it cannot certify task success.

The steel currently bends in its original plane. The paper model is isotropic
and uses a conservative, provisional 0.3% membrane-strain boundary. A breach
irreversibly invalidates the trial, even if the paper later looks flat. Bending
is reported separately; harmless creases are allowed by the task. No post-fracture topology or visible tear is simulated. A separate
wire/triangle crossing audit also fails closed. These limits need contact and
adversarial checks before any score can be claimed. See `PAPER_SOLVER_PLAN.md`.

## Remaining acceptance gates

1. Show that real-scale flexible paper contacts and retains the clinched wire;
   test a free-sheet control and smaller time steps.
2. Settle the full scene without fixtures, show contact-driven extraction and
   reject damaging or out-of-plane manipulation that exceeds model scope.
3. Implement ordinary YAM manipulation and demonstrate full score within the
   run limit, including releasing and separating the sheets.
4. Run Dream, score both recordings, verify the concise final setup and upload
   media only after the user authorizes submission.

The proposed judging uses before/after photographs, a millimetre ruler and
backlighting. It awards 0.5 for one leg entirely clear of both sheets, and 1.0
for both legs clear plus30mm additional relative sheet-corner displacement
from their initial12mm stagger, and release for three seconds. Excess damage or invalid simulation evidence overrides all credit.

Accepted [cord cutting](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/cut-taut-cord)
and [steel filing](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/file-a-steel-block-flat-down-to-a-scribed-line)
informed the causal material-hook structure. Neither validates this paper
model. Native [joint and drive documentation](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/rigid_bodies_articulations/joints.html)
explains the PhysX coupling used here.

The subsequent capped-wire, fixed-crown and four-velocity-iteration controls
still exceed 1% membrane strain within 5–7 ms. Native wire masses match their
steel volumes; no mass clamp explains this. A separate pocket-support candidate
uses a 1.5 × 16 × 8 mm recess below the clinched legs. Its five solid plate pieces
leave the whole intended 6 mm planar leg sweep clear while supporting the paper
near the punctures. It adds no attachment or collision filter. This candidate
has geometry checks only and is not yet a validated task reset.
