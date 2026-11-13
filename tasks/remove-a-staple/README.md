# Remove a staple without tearing the papers

**Development package; not submission-ready.** Full-size flexible 100 µm box-panel
paper now passes passive contact and a short YAM integration check. A fixed
translation of the whole station near the paper origin resolves the earlier
large-coordinate numerical failure without changing relative geometry or
material. Complete extraction and loaded robot feasibility remain unverified.
There is no demo, Dream run or media ID.

The robot removes a clinched staple without tearing either sheet and leaves the
complete staple at least10mm clear. The difficulty is engaging a remover under
the crown and unbending both legs without damaging their paper holes. No
unrelated transport or separation of the sheets is required.

## Evidence so far

The native 3 mm steel-leg coupon bends only when its diagnostic jaw touches it.
After the jaw withdraws, it retains 0.87567 rad of plastic bend. Moving the jaw
3 mm away produces no motion or plastic set. Halving the physics step from
100 to 50 microseconds changes the residual angle to 0.87322 rad, a 0.28%
difference. The three unedited reports are in `evidence/native-coupon-*.json`;
`VALIDATION.json` records their hashes. These are contact/material tests, not
paper extraction or robot demonstrations. Material parameters are approximate.

There are 55 passing CPU checks for the steel law, punctured meshes,
latched membrane/contact guards, tool approach geometry and photo-based judging.
The older CPU cohesive-opening model remains a research probe; it does not
supply tearing physics in the native scene.

An earlier surface-FEM supported-edge candidate used fixed620 ×420µm punctures in
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

## Historical surface-FEM candidate

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
the far edges overhang by 20 and 32 mm.
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

## Remaining acceptance gates (current panel candidate)

1. Verify flexible loaded contact during remover insertion and extraction;
   the full-size passive contact and short native YAM gates now pass.
2. Settle the full scene without fixtures, show contact-driven extraction and
   reject damaging or out-of-plane manipulation that exceeds model scope.
3. Implement ordinary YAM manipulation and demonstrate full score within the
   run limit, including safely releasing the extracted staple and papers.
4. Run Dream, score both recordings, verify the concise final setup and upload
   media only after the user authorizes submission.

The proposed judging uses before/after photographs, a millimetre ruler and
backlighting. It awards 0.5 for one leg entirely clear of both sheets, and 1.0
for both legs clear with every part of the intact staple at least 10 mm from
either sheet and three seconds of release. The sheets may remain stacked.
Excess damage or invalid simulation evidence overrides all credit.

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
reaches 0.411% lower-sheet membrane strain after 4.5 ms at a 100 µs step.
A separate diagnostic allowing up to 1% still stops at 4.9 ms (1.020% lower
sheet strain), so the local excursion is not yet shown to be bounded. No
wire centreline crosses intact paper, but that alone does not validate contact.
Those controls also fail: the unstapled pocket reaches 1.107% strain after
4.8 ms, and the stapled 25 µs control reaches 1.049% after 10.15 ms. The
pocket introduces an independently unstable support edge; it is not promoted.

A separate `clearance-candidate` mesh uses 0.8 × 0.6 mm initial punctures to
represent opened staple holes. This leaves 100 µm of clearance per side after
the paper collision thickness, compared with 10 µm in the earlier mesh. It
retains the full clinched-leg obstruction and passes the same mesh-quality
checks. The supported-edge trial with these holes lasts 96.2 ms before a wire crosses
a lower-sheet triangle; its matched no-staple control exceeds 1% local membrane
strain after 8.4 ms. This remains a diagnostic geometry candidate, not a
promoted reset or a change to the damage rubric.

An unrun fallback explicitly uses heavier flexible printing paper via
`--paper-profile heavy-200gsm-candidate`: 200 g/m² and 200 µm, with matching mass,
contact thickness, sheet spacing and staple-clinch depth. Both sheets remain
native deformable surfaces. [Mondi’s printing-paper range](https://www.mondigroup.com/products-and-solutions/uncoated-printing-paper/color-copy/)
and the [manufacturer datasheet](https://store.paper.co.uk/pub/pdfs/Color-Copy-data-sheet-10-19.pdf)
support this material class. They do not calibrate the declared isotropic 2 GPa
elastic approximation. This candidate has not replaced the task setup or
passed native extraction; scoring and strain guards are unchanged.

## Flexible-facet candidate

Native surface-FEM controls still let the steel cross intact paper, including
200gsm paper and increased predictive contact margin. This is a contact failure,
not a conclusion that ordinary creasing tears paper. The task is not ready.

`facet_probe.py` tests two 24×20mm coupons made from 100µm triangular prisms.
Native bending hinges provide flexibility and native finite break forces bound
intactness. All staple contacts stay enabled; no sheet is pinned or attached.
The weak-direction 1500 N/m strength envelope is an engineering approximation
from the copy-paper tensile data cited in `MATERIAL_DOMAIN.md`, not a calibrated
puncture fracture law. This candidate has no full-size or extraction evidence.

```sh
python tasks/remove-a-staple/facet_probe.py --out OUTPUT --seconds .02 --dt .0001
python tasks/remove-a-staple/facet_probe.py --out OUTPUT_EMPTY --seconds .02 --dt .0001 --no-staple
```

Inspect native cooked-hull thickness, mass, hinge continuity and wire crossing
before interpreting either control. Authored collision dimensions alone do not
prove that native cooking preserved the 100 µm thickness.

### Latest paper candidate: native analytic panels

The earlier surface-FEM controls remained invalid because steel crossed intact
paper. Triangular rigid facets also failed: native cooking produced741–1030µm
thick tetrahedra from100µm input prisms. Setting minimum hull thickness did not
fix this, so these controls are not accepted evidence of paper behavior.

The replacement uses exact100µm native boxes joined along edges by passive
bending hinges. Paper flexural rigidity, mass and finite edge strength remain
explicit. There are no paper anchors or automatic releases. The24×20mm coupon
has152 panels per sheet and the same two physical punctures. A20ms free-fall
control matches gravity; both empty and stapled100ms contact controls pass,
with final hinge gaps below13nm and clean metal-crossing audits. These are
material/contact results, not extraction demonstrations. The full210×148mm
candidate is prepared with573/550 panels per sheet and the established support,
free staple and remover. It still needs native validation and robot extraction.

```sh
python tasks/remove-a-staple/facet_probe.py --out artifacts/paper-box-stapled --seconds .1 --dt .0001 --primitive-box-panels --external-forces-every-iteration
python tasks/remove-a-staple/facet_probe.py --out artifacts/paper-box-full --seconds .05 --dt .0001 --primitive-box-panels --full-size-candidate --external-forces-every-iteration
```

`arena_panels.py` and `task_panels.py` are separate candidate YAM modules. They
use reset-only pose writes and inspect paper continuity/crossing every substep.
They have not yet run. Paper remains a discretely flexible shell, not one rigid
sheet; anisotropy, permanent crease memory and detailed post-fracture topology
are not represented. Any broken/gaping hinge invalidates the candidate trial.

### Current box-panel candidate, 13 November

The active candidate uses `facet_paper.py`, `arena_panels.py`, `task_panels.py`
and `preview_panels.py`. The lower and upper A5 sheets have 573 and 550 free
analytic boxes, each genuinely 100 µm thick, joined by passive finite-strength
bending hinges. It is an approximately inextensible flexible sheet, not a
rigid paper prop. Explicit 0.8 × 0.6 mm holes surround the clinched wire. The
physical document plate has a 1.5 × 16 × 8 mm pocket below the folded legs.

The original full scene failed at 4.7 ms despite no initial solid overlap.
Translating the entire scene by (−0.32, 0, −0.7675) m before physics attachment
resolves that failure at the same 100 µs step. The 0.1-second native control
keeps maximum hinge gaps below 0.173 µm and all wire-crossing audits clean.
The identical coordinate change includes both robot bases, the table, fixed
cameras and hardware in the YAM bridge; wrist camera transforms remain relative
to their arms. Its two-action gate also passes, with final gaps of 0.599 and
0.643 µm. No task object is moved during control except through physics.

Increasing the TGS step to 500 µs fails by 5.5 ms; that configuration is not used. The two-action
bridge took 113.6 wall seconds including initialization. Runtime reductions
need matched mechanical checks before a full robot trial. The 236-action
pocket-support lever plan has a clean whole-arm collision screen, but has not
yet grasped the remover or extracted the staple in this model.

Run the current integration gate in the pinned environment:

```sh
python tasks/remove-a-staple/preview_panels.py --out OUTPUT --steps 2 --physics-hz 10000 --recenter-at-paper
```

The coordinate translation is a numerical choice, not an altered physical
setup. Ordinary creases are allowed. Broken or gaping hinges and intact-paper
wire crossings invalidate evidence. See
`evidence/native-panel-recenter-070-074-summary.json` for measured controls.

The intact extracted staple may remain in or on a released remover resting
on the work surface. Holding the tool with the staple still in it does not
start the three-second release interval. Judging v4 records this explicitly.

### PGS and complete motion candidate

The matched PGS control at 500 µs and 32 position iterations passes full-size
passive contact and the two-action YAM bridge. Final panel hinge gaps are
5.82 and4.35 µm with no staple crossings. Each rendered control action takes
about4.5–4.9 wall seconds. See `evidence/native-pgs-panels-080-082-summary.json`.
This is integration evidence; loaded extraction remains unverified.

A386-action candidate includes the unchanged236-action lever sequence, physical
placement and release of the remover, and3.2 seconds of hands-free observation.
Its full-frame offline hull audit has no unintended intersections; this does not
prove native grasp or extraction. The proposed600-action limit is30 simulated
seconds. The native trial records measured paper/steel geometry and all-substep
continuity/crossing checks. `assess_trace.py` supplies conservative geometric
distance/release evidence after a run; it does not fill human review fields or
certify a score. The staple may remain in the released remover, at least10mm
from both papers.
