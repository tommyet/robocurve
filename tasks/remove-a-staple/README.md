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

There are 31 passing CPU checks for the steel law, punctured sheet meshes,
irreversible validity guards, contact auditing and photo-based judging.
The older CPU cohesive-opening model remains a research probe; it does not
supply tearing physics in the proposed native scene.

The latest paper tests still fail the provisional elastic-domain guard. With
cleaned meshes and the documented shell bend coefficient, the touching free
sheets gain about 0.8 mm of separation; one exceeds 0.3% local bending after
0.129 seconds. The stapled coupon exceeds that boundary after 0.010 seconds.
Wire-crossing audits stay clean. These are failed contact/validity tests, not
evidence of a tear or successful retention. The separated-sheet control now
passes 0.2 seconds with zero bending and a 9.9986 mm final gap from 10 mm;
this implicates contact. The 120 µm midplane-gap control also passes with zero
bending and 119.85 µm final separation. The stapled coupon with that gap and
20 µm of crown clearance still crosses the bending-domain boundary after
0.007 seconds. The actual supported A5 scene also runs, but its original mesh
crosses the bending boundary after 0.009 seconds and the membrane boundary
after 0.011 seconds. The worst stretched triangle is far from the staple; its
52:1 aspect ratio magnifies micron-scale motion into local strain.

The replacement A5 meshes refine only the puncture regions. Frozen assets
preserve the exact 620 × 420 µm holes, sheet outline, area and mass. Minimum
triangle angles are 15.08° and 15.85°, with edge ratios below 3.57. Geometry,
wire-hole alignment and rigid-motion checks pass. At the original 0.5 ms step,
the refined native scene still reaches 0.429% membrane strain after 0.011 seconds,
now beside a staple leg. The next comparison uses the wire coupon's validated
0.1 ms step. Material parameters and validity thresholds have not changed. The task loads
NumPy assets; SciPy is only required to regenerate them with
`generate_meshes.py`. `assets/mesh-manifest.json` records hashes and quality.

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
python tasks/remove-a-staple/full_probe.py --out artifacts/staple-full --seconds .1 --physics-hz 2000
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
The staple and remover fulcrum are over the support. This scene runs but has
not passed its material/contact validity gate;
`setup.json` and `task.draft.json` are provisional until the geometry is tested.
The YAM bridge in `arena_paper.py`, `arena_hardware.py` and `task.py` is authored
but unrun. It exposes measured geometry to an assessor, writes poses only on
reset and fails closed when the material/contact validity guard trips.
`preview_yam.py` is an unrun camera/integration recorder using ordinary ready
joint targets. It audits both FEM sheets and all 61 free hardware bodies. Run
it only after the native contact gates; it cannot certify task success.

The steel currently bends in its original plane. The paper model is isotropic
and uses a conservative, provisional 0.3% membrane/surface-bending strain
boundary. A breach irreversibly invalidates the trial, even if the paper later
looks flat. No post-fracture topology or visible tear is simulated. A separate
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
for both legs clear plus sheets separated by 30 mm and released for three
seconds. Excess damage or invalid simulation evidence overrides all credit.

Accepted [cord cutting](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/cut-taut-cord)
and [steel filing](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/file-a-steel-block-flat-down-to-a-scribed-line)
informed the causal material-hook structure. Neither validates this paper
model. Native [joint and drive documentation](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/rigid_bodies_articulations/joints.html)
explains the PhysX coupling used here.
