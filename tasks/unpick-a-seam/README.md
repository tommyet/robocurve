# Unpick a seam

Remove the six tacking stitches joining two canvas patches. Separate the patches
without cutting or tearing either one.

**Development package; not ready to submit.** No robot demo, Dream run, media or
task score exists. `task.draft.json` is a draft. Matched 0.2 s controls at 3,840 Hz
had no thread crossings; YAM reset stability and full manipulation are unproven.

## Setup

The selected candidate now uses an ordinary bench sewing clamp. The earlier
flat-table resets below are retained as failed development evidence; they are
not the current setup. The station table is at Z = 0.7475 m.

Two flexible 75 × 80 × 0.4 mm cotton-canvas patches overlap by 20 mm vertically.
The upper patch's middle surface is X = 0.2996 m, Z = 0.8027–0.8777 m; the lower
is X = 0.3004 m, Z = 0.7477–0.8227 m. Both span Y = −0.040–+0.040 m. Six red
0.8 mm polyester thread loops form separate tied tacking stitches at Y = −30,
−18, −6, +6, +18 and +30 mm. Each passes through two 1.6 mm square needle holes
in each patch, at Z = 0.8077 and 0.8177 m. This is a coarse hand-tacked lap seam,
not a machine lockstitch; the model does not resolve individual fabric yarns.

The selected fixture is a bench clamp with one passive moving jaw. A fixed
6 × 85 × 16 mm front jaw holds the upper patch's top 8 mm and extends 8 mm above
it. The rear jaw is 6 × 85 × 8 mm, weighs 12 g, and moves on an ideal X-axis
linear guide. Its initial 0.60 mm gap leaves 0.20 mm clearance behind the cloth.
A fixed 1,250 N/m spring target and 8 N·s/m damping close it, limited to 0.6 N.
At 0.40 mm cloth thickness the nominal seated load is 0.5 N. These are authored
mechanical parameters, not yet a measured contact-force result. The jaw can
travel from a closed gap to a 1.60 mm gap. The stand is bolted to the table.

A base, rear post and overhead bridge stay clear of the moving jaw's full
travel. Exact dimensions and positions are in `passive_clamp.py`. Every cloth
node remains dynamic; the guide constrains the metal jaw only. The lower
swatch rests its lower edge on the real table, with its middle surface
0.20 mm above the tabletop. The table supplies ordinary contact support. The
base plate sits behind the cloth. No cloth attachment, weld or runtime position
target supports either patch. The jaw has seated correctly in native probes, but both hanging mesh variants
exceeded the 5% operating domain. The table-supported reset is the current
candidate. At 960 Hz it completed a 0.2 s standalone control with less than
0.72% peak extension and no thread crossing. Its passive jaw closed to a
0.276 mm gap, leaving the cloth middle surface clear of metal but overlapping
its nominal back-side contact layer by 0.124 mm. This is finite native contact
compliance, not a calibrated textile compression model. At 3,840 Hz the same
setup exceeded 5% extension after 72.656 ms despite a correctly seated jaw.
There is no timestep-convergence claim; full robot manipulation and cutting
remain unproven. Measurements are in `evidence/native-supported-controls-041.json`.

The earlier fixed-gap clamp remains available only for a diagnostic comparison.
Its 0.30 mm gap was incompatible with the cloth's fixed 0.40 mm collision
thickness. Its YAM trial failed at a needle-hole triangle after 5.469 ms without
a thread crossing. This failure is recorded, not counted as a usable reset.

A seam ripper starts on the table at (0.200, −0.120, 0.7555) m, pointing along
+X. Its handle is 70 × 12 × 12 mm; a 1 × 0.5 × 4 mm (X/Y/Z) cutting-edge approximation is
50 mm in front of its centre, between a long point and a shorter guarded point.
Total tool mass is 19 g. The preview builds the tool as dynamic bodies joined by
a permanent fixed joint; neither hand starts attached. There are no thread/fabric
attachments.

## Local checks

From the repository root:

```bash
.venv/bin/python -m unittest discover -s tasks/unpick-a-seam -p 'test_*.py' -v
```

Forty-six tests pass: connected cloth with real needle holes, needle-path clearance,
force direction and sustained contact for cutting, interrupted-contact rejection,
blade damage latching, whole-thread clearance, rigid-motion-invariant strain
inspection, moving-cloth/thread tunnelling detection, and final-state scoring. These are CPU geometry/rule
checks, not proof that cloth or thread dynamics work.

## Native validation status

The coupon probe rotates the sewn pair vertically and holds only the top edge
between physical clamp jaws. All cloth vertices stay dynamic. Intact and
pre-cut loops are matched controls; neither is a robot demonstration.

| Evidence | Settings | Result |
|---|---|---|
| Original thread | 0.4 mm thread, 1.2 mm holes | Crossed intact fabric after 19–20 ms. |
| Batch 009 | 0.8 mm thread, 1.6 mm holes | Intact crossed at 67.708 ms; open at 28.125 ms. |
| Batch 013 | Same geometry, combined native contact refinement | Intact crossed at 48.958 ms; open at 28.125 ms. |
| Batch 015 | Same geometry, 0.4 mm local mesh, 960 Hz | Intact completed 0.2 s without crossing or strain excursion; hanging patch dropped 2.373 mm. Open crossed at 42.708 ms. |
| Batch 018 | Same refined mesh, open control, 3,840 Hz | No crossing through 16.406 ms. Stopped on 2.096% local principal extension near a needle hole, exceeding the 2% engineering domain. This was a strain stop, not a contact failure. |
| Batch 020 | Matched intact/open controls, same refined mesh, 3,840 Hz | Both completed 0.2 s without a crossing. Original 2% strain invalidity stayed latched: maximum extensions 2.624% intact and 4.429% open. Physical fragment extraction remains unproven. |
| Batch 021 | First YAM two-action smoke | Stopped before stepping on a contact-setting assertion; no robot physics result. The installed official sensor setup is now applied after simulation creation. |
| Batch 022 | Standalone CUDA audit | 445 cases / 224,045 segment–face pairs matched CPU. Two-patch kernel benchmark: 0.359 ms per substep. This excludes native physics and other audits. |
| Batch 024 | Persistent CUDA check and native CPU shadow | Snapshot retention passed. All 88 reset/substep checks agreed before a 2.086% right-patch strain stop at 22.656 ms; no crossing or blade damage. Contact configuration now works. |
| Batch 025 | Same layout, Warp, 5% domain | Stopped at 26.042 ms on 5.146% right-patch extension; no crossing or blade damage. Both patches had fallen about 2.4 mm toward the table. |
| Batch 026 | Graded mesh, upright intact/open controls | Both stopped at strict centreline crossings near a hole edge: intact 127.604 ms / 2.29 µm inside, open 122.656 ms / 11.46 µm inside. Finite-radius overlap is present; duration and permanent escape were not measured. |
| Batch 027 | Rectilinear mesh, resting reset, Warp, 5% domain | Stopped at 12.5 ms on 6.329% right-patch extension; no crossing or blade damage. The failure triangle has a 50 µm edge. Native stepping took 1.965 of 2.712 control wall seconds. |
| Batch 028 | Graded mesh and resting reset, same guards | Stopped at 9.896 ms on 5.103% right-patch extension; left peaked at 1.504%. No crossing or blade damage. Native stepping took 1.875 of 2.345 control wall seconds. |
| Batch 029 | Same reset, strain continuation only | Thread crossed the right patch at 13.542 ms, 0.440 mm inside the mesh boundary. By the first action boundary, peak extension reached 36.4% left / 48.6% right. This reset fails substantially; it is not a usable settled state. |
| Batch 029 | Separate tool-only coupon, 240 Hz | All 220 actions completed: 77.6 mm lift, retained grasp, then 79.6 mm drop after opening. No cloth, cut or task score. |
| Batch 034 | Sewing clamp, rectilinear mesh, 3,840 Hz, 5% domain | Stopped after 21 substeps / 5.469 ms at 6.491% upper-patch extension near a needle hole. Zero completed actions; no crossing, cut or blade damage. |
| Batch 041 | Passive jaw, graded mesh, supported lower edge, 960 Hz / 3,840 Hz | 960 Hz completed 0.2 s with 0.711% / 0.425% peak extension and no crossings; nominal jaw contact-layer overlap is 0.124 mm. The 3,840 Hz comparison exceeded 5% strain at 72.656 ms. No robot action or cut. |

The refined mesh has 4,407 vertices / 8,490 triangles per patch, hole boundary
edges at most 0.4 mm, the same 0.00596928 m² area, and thirteen boundary loops.
It adds no colliders, attachments or enlarged openings. Earlier crossing
locations and later mesh/timestep evidence are recorded in
`evidence/native-crossings-009.json`, `evidence/native-contact-refinement-013.json`
`evidence/native-mesh-timestep-015-018.json` and
`evidence/native-controls-020-022.json`. Full release is still unproven.

The following commands reproduce the strain-continuation contact controls.
They retain invalid-model status above 2% and stop at the first crossing:

```bash
python tasks/unpick-a-seam/probe_native.py --mode intact --coarse-thread --contact-refinement combined --hole-mesh-spacing .0004 --physics-hz 3840 --seconds .2 --continue-after-strain --out artifacts/seam-intact-contact-control
python tasks/unpick-a-seam/probe_native.py --mode open --coarse-thread --contact-refinement combined --hole-mesh-spacing .0004 --physics-hz 3840 --seconds .2 --continue-after-strain --out artifacts/seam-open-contact-control
```

These are diagnostic commands for the pinned Isaac Sim environment. They do
not authorize a score, weaken a crossing predicate, or certify a new material
limit. Reports include both failure types, every-step displacement maxima and
source hashes; first-invalid and first-contact snapshots retain both sides of
the relevant native physics step. No probe uses Dream or animated object motion.

`--contact-refinement iterations` sets the native deformable collision multiplier
and pair update frequency to 4; `speculative` enables only deformable speculative
CCD; `combined` enables both. `baseline` preserves native defaults. These
controls were checked against installed PhysxSchemaAddition 110.3.2 and its
[native deformable schema](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/deformables_beta/physx_deformable_schema.html).
Deformable speculative CCD is separate from unsupported rigid-body CCD in this
GPU mode. Pair updates concern surface-to-surface contact; schema support alone
does not prove an improvement in rigid-thread contact.

The supported 960 Hz full cloth scene completed eight actions before a
near-hole contact guard stopped the trial at 0.410417 s. The axis crossed
45.79 µm inside the hole boundary; a neighbouring vertex lay 243.59 µm inside
the nominal capsule radius. At the retained 0.45 s terminal state, static
intersections were absent and each uncut tack retained its original links
through both patches. This is evidence of transient edge penetration with
recovery, not a successful trial or permanent unthreading. The original
invalidity stays latched. See `evidence/native-reset-first-cut-041.json`.
A separate tool-only coupon demonstrates pickup, retention and release; no
thread cut or full manipulation has been demonstrated.
`preview_yam.py` records ordinary robot actions, every-substep audits, native
blade/thread force events, video and cloth/thread traces. It stays unscored.
The draft setup remains fixed, with no random jitter, seed 0 and a limit of
2,400 actions at 20 Hz. The coarse thread is the current candidate, with final
native validation still outstanding.

## Audit performance check

The opt-in `warp-shadow` backend evaluates the same double-precision crossing
predicates on both CPU and CUDA at every native physics substep. It checks
agreement and preserves the first failing states before polling at each 20 Hz
action boundary. No physics step is skipped. `warp` omits the duplicate CPU
crossing calculation after equivalence is established; strain and blade-damage
audits remain active every substep. The CPU backend remains the default.

```bash
python tasks/unpick-a-seam/check_warp_contact.py --device cuda:0 --benchmark --out artifacts/seam-warp-check.json
python tasks/unpick-a-seam/preview_yam.py --coarse-thread --hole-mesh-spacing .0004 --contact-refinement combined --physics-hz 3840 --steps 2 --crossing-backend warp-shadow --out artifacts/seam-yam-shadow
```

These checks use the unchanged 2% default. The standalone checker also verifies
that later updates cannot overwrite the first-failure snapshot. Native shadow
integration agreed through 87 substeps (`evidence/native-warp-shadow-024.json`).
`--profile-steps` optionally records CPU call timings to locate remaining cost.
Runtime reports separate control wall time from
readback, strain, crossing, damage and cutting costs.

## Next geometry and setup diagnostics

`--quality-mesh` selects a graded triangulation of the same coarse-thread patch
surface and twelve 1.6 mm square holes. It requires `--coarse-thread` and omitting
`--hole-mesh-spacing`. It uses 2,888 faces rather than 8,490 per patch, keeps all
hole-boundary edges at 0.4 mm, and raises the smallest edge from 25 to 400 µm and
the smallest triangle angle from 3.81° to 17.34°. Area, connectedness, boundary
positions and winding are checked during generation. Material and contacts are
unchanged. Its upright native controls failed near-boundary contact in batch
026, so this mesh is not validated. The combined graded-mesh/resting-reset YAM
comparison also stopped on the 5% strain guard in batch 028. Bounded settling
forensics in batch 029 showed growing deformation and a substantial crossing,
not a harmless short settling excursion.

`--resting-seam` is a separate preview option: lower the complete sewn assembly
until its bottom thread surface is tangent to the tabletop. For the coarse thread
this removes a 2 mm initial air gap. All relative geometry and intrinsic fabric
rest shapes remain unchanged. This addresses the initial table impact seen in
batch 025; it is an explicit fixed-layout change, recorded in each trial, and
failed the 5% strain guard with the original rectilinear mesh in batch 027.
It never moves objects after reset. Neither option
changes a scoring or damage threshold.

For failure investigation only, `probe_native.py --continue-after-invalid
--record-contact-history` records static and swept occupancy at every native
step while the original guard stays latched. Reports include boundary distance,
signed endpoint distances to the intersected face plane, and sampled recovery
intervals. This distinguishes a brief contact from persistent intersection; it
does not certify unthreading or make an invalid trial valid. The YAM preview's
separate `--continue-after-strain` option is restricted to four ready-hold
actions (0.2 s), with no policy. Crossings and blade damage still stop the run,
and exceeding the strain limit retains invalid-model status. Diagnostic evidence
from batches 025–028 is summarized in `evidence/native-controls-025-028.json`;
batch 029 is in `evidence/native-controls-029.json`.

The separate tool-only coupon uses the same tool spawner and robot station but
omits cloth, so it cannot establish seam retention, cutting, fabric integrity or
task score. Its frozen pickup can be followed by a fixed opening/release control:

```bash
python tasks/unpick-a-seam/probe_tool.py --steps 140 --physics-hz 240 --release-control --out artifacts/seam-tool-pickup
```

This records 220 actions (11 simulated seconds), tool and gripper poses, video,
and height changes across the hold/opening sequence. Batch 029 completed it in
38.9 wall seconds. The held TCP was 10.021 mm above the handle in its local frame;
this fixed calibration can inform later plans, but it is not live object feedback.
The coupon's lower physics rate is not a validated rate for the cloth scene.


`--pre-draped-seam` is an opt-in fixed reset for the coarse thread and graded
mesh. It starts the cloth gently draped over the bottom thread runs, preserving
the flat intrinsic rest meshes, material, holes and all dynamic degrees of
freedom. No pose is prescribed after reset. CPU checks measure 1.812% maximum
initial extension, 0.463 mm minimum cloth-to-cloth distance, and conservative
thread-axis distances of 0.755 / 0.637 mm against a 0.600 mm required envelope.
Full triangle faces and edges are checked, not only vertices. Batch 030 stopped
before physics on an exact floating-point equality in the layout guard. That
authoring bug is fixed and covered by a scene-loading CPU regression. Native
stability failed in batch 031: the 2% limit was exceeded on the first substep,
and the 5% run reached 8.29% extension after 2.083 ms. There were no crossings
through that early stop. First-step speeds of 0.804 / 0.622 m/s were mostly
in-plane at hole-boundary nodes. `evidence/pre-drape-cpu.json` records the initial
geometry; `evidence/native-controls-030-031.json` records the failed native gates.

```bash
python tasks/unpick-a-seam/preview_yam.py --coarse-thread --quality-mesh --pre-draped-seam --contact-refinement combined --physics-hz 3840 --steps 2 --maximum-stretch 1.02 --crossing-backend warp --out artifacts/seam-pre-drape
```


A separate frozen first-tack candidate is in `evidence/first-cut-plan.json`.
It preserves the pickup/hover prefix, physically presses the left patch with
closed fingertips, feeds the vertical blade through the first tack at 2° pitch,
then lifts the tool and releases the press. It has 540 actions / 27 seconds.
Its ordinary joint rates stay below 42.5% of the allowed maximum; nominal complete
hand bounds have no inter-hand or tool/left-hand overlap. The pressing fingertips
approach to 0.358 mm above the table, giving about 0.042 mm nominal compression
of the 0.4 mm sheet. This replaces an unrun 0.058 mm gap that would overconstrain
the cloth between the hand and table. Actual force and strain remain unmeasured.
`evidence/first-cut-clearance-cpu.json` records these geometry checks.
This is unrun: native pressing, cutting, fabric integrity, removal and stable
cloth contact all remain gates. Do not execute it before reset validation.

The opt-in `--audit-junctions` also checks the short centreline segments between
native capsule endpoints at every substep. It invalidates physically disjoint
end caps at an uncut joint. A force-qualified cut removes only its connector
from both current and previous audit state, preserving other motion histories.
The first-cut candidate requires this option. CPU tests cover the cut transition;
native integration remains unvalidated.

A force-qualified cut now also removes that adjacent capsule pair's collision
exclusion in both directions and enables the disabled joint's collision flag.
Other pair filters remain unchanged; reset restores the original joined pairs.
CPU tests check this graph change, including wraparound joints and repeated
cuts. Native pair rebuilding and separation of the formerly overlapping end
caps remain unvalidated, so this is not yet evidence of physical extraction.


`--max-depenetration-m-s .05` is a separate native numerical diagnostic. It
bounds only the solver velocity used to resolve contact penetration; it does
not clamp actual object velocity, alter material parameters, or relax an audit.
The default leaves the native value unchanged. Each preview now records actual
contact/rest offsets, self-collision filter distance and correction controls.
This follows the [PhysX deformable schema](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/deformables_beta/physx_deformable_schema.html).
In 032 the capped Gaussian reset still failed at 2.083 ms, with 5.150% right-patch
extension. Its first-substep strain was unchanged, consistent with the cap not
addressing the initial elastic relaxation.


`--drape-shape cylindrical` selects a separate pre-drape comparison. It keeps the
overlap and needle openings flat at 1.65 / 1.10 mm above the table, then bends
only the outer 20 mm ramps. Integrating the horizontal arc coordinate preserves
the original material length; outer edges shift by at most 63.3 µm. Initial
maximum extension is 0.00214%, full cloth separation is 0.543 mm, and conservative
thread-axis distances are 0.755 / 0.655 mm. Intrinsic rest meshes and material
parameters stay unchanged. `evidence/cylindrical-drape-cpu.json` records the CPU
checks. The 032 native comparison stayed below the 2% warning until 6.771 ms,
then failed at 7.552 ms with 5.646% right-patch extension. The failing triangle
beside a needle hole fell 0.60–0.65 mm, versus about 0.28 mm gravitational free
fall over that interval. This supports a further contact-correction comparison,
but does not isolate its cause. Neither 032 reset completed an action; no thread
crossing or blade damage was detected before the stops. See
`evidence/native-controls-032.json`. The cylindrical reset with the correction
cap then failed in 033 at 8.854 ms, with 6.396% left extension
and peak cloth speeds of 1.747 / 2.542 m/s. No complete action or score exists.
`evidence/native-control-033.json` records the result. Table-reset tuning is
stopped. The fixed-gap clamp below was the next diagnostic; the passive jaw
described at the top now replaces it.

`--sewing-clamp` without `--passive-clamp` retains the historical fixed-gap setup:
the swatches hang vertically in a small bench clamp, whose base is fixed to the
table. Its 6 × 85 × 8 mm jaws have a 0.30 mm gap and hold the upper patch's top
8 mm. A post, arm and two side bridges connect the jaws to the base; the side
bridges stay outside the fabric. Both cloth meshes and all thread capsules
remain dynamic, with no attachments. The upper edge is 150 mm above the table
and the lower swatch's bottom begins 20 mm above it.

This rigidly relocates the exact refined mesh, jaw and thread layout of the
020 vertical controls. Those earlier 0.2-second controls had no centreline
crossings but exceeded their original 2% operating cutoff. They do not establish
stability of this YAM setup: batches 034 and 035 failed within 6 ms. The fixed clamp uses the original
0.8 friction, 0.5 mm contact offset and zero rest offset. Its first ready-hold
gate retains the explicit 5% domain and all ordinary crossing/damage checks.
`evidence/sewing-clamp-cpu.json` records the authored dimensions. Existing table
cutting plans cannot be run in this layout.

```bash
python tasks/unpick-a-seam/preview_yam.py --sewing-clamp --coarse-thread --hole-mesh-spacing .0004 --contact-refinement combined --physics-hz 3840 --steps 8 --maximum-stretch 1.05 --crossing-backend warp --profile-steps --out artifacts/seam-sewing-clamp
```

## Mechanics and limitations

Each selected graded patch is a native PhysX surface FEM mesh with 1,582
vertices, 2,888 triangles and twelve genuine holes. Six separate 28-link capsule chains pass through those
holes. Native spherical joints make each thread continuous; the closed joint
approximates a hand-tied tack. Contacts with the cloth, table, tool and other
nonadjacent thread links remain active. There are no hidden stitch welds to cut.

`ThreadCutter` accepts only the measured blade-versus-thread contact-force matrix.
Force into the cutting edge must exceed 0.25 N continuously for 40 ms before one
thread joint is disabled. This is an uncalibrated constitutive rule, informed by
the contact/force approach in accepted [cord cutting #218](https://github.com/robocurve/benchmark-tasks/pull/218).
Fragments remain dynamic and must actually leave the seam. Cut count alone earns
no score. `ThreadClothAudit` independently rejects a thread centreline crossing
an intact cloth triangle, including a cloth surface moving through the thread.
Only the authored holes permit passage. Fine thread masses and deformable-hole contact may prove unstable;
the intact/open differential probe must resolve that before robot development.

The ripper's long point starts below its vertical cutting edge. Its square
12 mm handle supports that orientation on the table, and a continuous ordinary
metal shank joins handle and fork. Only the blade body's contact forces can cut;
the shaft and guards cannot. The frozen pickup plan keeps the hand downward,
then turns the shaft across the tack with a 5° pitch and remains above the fabric.
Nominal complete-hand collision bounds clear the table by at least 3.16 mm, but
this remains a CPU approach check. Native grasp/release is demonstrated by the
separate coupon; approach and cutting remain unvalidated.

Native FEM cannot change cloth topology at runtime. `DamageAudit` therefore
conservatively invalidates blade crossings rather than claiming intact fabric
survived cutting. It does not simulate tear propagation. `StrainAudit` records
a warning above 2% local principal extension and latches failure above the
declared operating limit. The preview defaults to 2%; `--maximum-stretch 1.05`
selects an explicit 5% approximate operating domain while retaining 2% telemetry.
Neither cutoff is a calibrated canvas tear strain. [Cotton tensile measurements](https://www.mdpi.com/2673-7248/5/4/67)
show substantial fabric and warp/weft dependence; they do not validate one
universal failure threshold. The cited pure-cotton fabrics reached 7.1–19.3% mean elongation at maximum
force; those values are not reversible elastic limits. A 2.096% local excursion
alone therefore does not demonstrate damage. The matched continuation controls
peaked below 4.43%, then relaxed below 1.7% at their last samples. This supports
testing a modest 5% operating domain; it does not prove undamaged real cotton.
Blade crossings and excursions above the declared limit still invalidate the
trial, and eventual judging must also show intact fabric in ordinary images.
Both audits are wired to the preview, with native validation pending. The blade audit uses conservative
bounds to avoid testing distant triangles; 200 randomized moving-mesh cases
matched the prior exhaustive audit (`evidence/damage-broad-phase-cpu.json`).

`inspection.py` checks actual thread-capsule clearance from both measured cloth
surfaces. It includes segment interiors and subtracts a sampling-error bound;
cut-joint counts never certify removal. This sufficient geometric test requires
all six red threads to clear both patches by at least 1 mm. The real counterpart
is inspecting both sides of the separated patches for remaining red thread.

Remaining work: native contact and cut probes; validate the wired damage audit;
validate released-stitch inspection against final images; validate the native cloth/thread reset adapters;
implement a demo using only normal policy observations or a frozen action plan;
then record demo/Dream, compare photo judgments, and rescore final evidence.
Fresh native scenes are required for current previews; repeated reset behavior
is not certified. The task preview deliberately always reports score zero.

Accepted source structure and rejected [rigid-fabric sewing #678](https://github.com/robocurve/benchmark-tasks/pull/678)
informed the design. They do not establish acceptance of this implementation.
Geometry and code are original team work; the native cloth helper is shared team
code copied into this folder so a future single-task PR can be self-contained.

### Clamp integration comparison

`preview_yam.py` now records composed native scene settings, fixture bounds and
material bindings, and native tensors before and after the explicit reset. This
is diagnostic readback; it changes no body, material or score. Batch 035 confirms
the intended jaw bounds, offsets and material. Initialization leaves 5.09 mm/s
downward velocity, but the explicit reset zeros it and restores float32 poses
within 32 nm. Upper-hole strain still fails at 5.990 ms. The evidence is in
`evidence/native-reset-snapshot-035.json`.

The corresponding standalone comparison preserves the YAM candidate rigid
transform, seven fixture parts, table bounds, cloth and thread. It omits the
robot and YAM initialization/reset, retaining GPU PhysX, TGS and every-substep
strain/crossing checks:

```bash
python tasks/unpick-a-seam/probe_native.py --mode intact --sewing-clamp --coarse-thread --hole-mesh-spacing .0004 --contact-refinement combined --physics-hz 3840 --seconds .2 --maximum-stretch 1.05 --out artifacts/seam-clamp-standalone
```

The unrun `evidence/clamp-cut-plan.json` contains 294 frozen actions: the proven
7 s tool pickup followed by a single forward tack cut. CPU IK and commanded-pose
hand/tool/fixture clearance pass (`evidence/clamp-cut-clearance-cpu.json`); those
checks do not establish native contact, continuous trajectory clearance or a
successful cut. Do not run the full plan before reset stability is demonstrated.

### Passive-jaw control

The passive jaw removes the incompatible fixed-gap contact constraint. It has
no active control or cloth attachment. A bounded standalone check is:

```bash
python tasks/unpick-a-seam/probe_native.py --mode intact --sewing-clamp --passive-clamp --coarse-thread --hole-mesh-spacing .0004 --contact-refinement combined --physics-hz 3840 --seconds .2 --maximum-stretch 1.05 --out artifacts/seam-passive-jaw
```

The probe records jaw poses/velocities alongside cloth and thread. Its reported
spring force is inferred from the fixed spring law and measured jaw state; it
is not a measured cloth contact force. The same `--passive-clamp` flag selects
the fixture in `preview_yam.py`. Use its normal `env.reset()` episode lifecycle.
The historical `--keep-constructor-state` experiment failed before stepping
because Gym requires reset before step; it is now rejected before simulator
startup. That API failure says nothing about physical task feasibility.
Constructor-internal steps remain explicitly reported as unobserved; every
subsequent control substep is audited. See `evidence/native-first-cut-api-041.json`.

Batch 037 confirms the passive jaw seats without forcing a sub-thickness gap.
It does not establish cloth stability: the upper patch reaches 5.232% local
extension after 37.760 ms, while no thread centreline has crossed cloth. See
`evidence/native-passive-clamp-037.json`. The existing graded mesh can now be
combined with the same clamp by replacing `--hole-mesh-spacing .0004` with
`--quality-mesh`. This retains every hole and the material surface, replacing
25 µm minimum edges / 3.8° minimum angles with 0.4 mm / 17.3°. No failure limit
is relaxed.

### Table-supported starting layout

The graded hanging control 038 still stops at 22.917 ms on 5.181% local extension
after the lower patch falls 2.323 mm into the stitches. Its correctly seated jaw
does not solve that impact. The selected reset now adds `--supported-clamp`: it
lowers the cloth and upper fixture by 19.8 mm, putting the lower edge at table top
plus the 0.2 mm cloth rest offset. The base moves behind the fabric so it cannot
intersect the newly lowered bottom. Every vertex remains free and the real
table supplies support. Material and all guards remain unchanged.

```bash
python tasks/unpick-a-seam/probe_native.py --mode intact --sewing-clamp --passive-clamp --supported-clamp --coarse-thread --quality-mesh --contact-refinement combined --physics-hz 3840 --seconds .2 --maximum-stretch 1.05 --out artifacts/seam-supported-clamp
```

Source geometry and the updated first-cut plan pass 45 CPU checks and complete
arm/fixture/nominal-cloth screening. This is not a native stability or cut result.
The plan requires this supported layout and cannot run accidentally against the
earlier hanging fixture. See `evidence/supported-clamp-cpu.json` and
`evidence/clamp-cut-full-arm-clearance-cpu.json`.

### Bounded contact forensics

The supported reset's first YAM trial had a temporary needle-hole-edge
intersection and recovered its original tack-to-hole linking by the final
retained snapshot. To measure the event rather than assume harmlessness,
`--contact-forensics` records static/swept intersections and boundary-vertex
capsule overlap at every native substep. It permits at most one second of
ordinary ready-hold actions, rejects a controller plan and strain continuation,
and requires the closed-junction audit. Cutting is disabled. Original crossing
invalidity stays latched; strain, blade damage or disjoint uncut joints still
stop the diagnostic. This does not change the ordinary preview's validity
thresholds or provide a task score. Native045 stopped at0.525 s: early1–3 ms upper-edge contacts recovered, but a
later lower-patch axis crossing reached0.878 mm inside intact cloth. That is a
substantial contact failure, so these measurements do not justify accepting
all near-hole penetrations. See `evidence/native-contact-forensics-045.json`.

```bash
python tasks/unpick-a-seam/preview_yam.py --sewing-clamp --passive-clamp --supported-clamp --coarse-thread --quality-mesh --contact-refinement combined --physics-hz 960 --steps 20 --maximum-stretch 1.05 --audit-junctions --crossing-backend warp --contact-forensics --profile-steps --out artifacts/seam-supported-contact-forensics
```

### Contact-generation correction

`--cloth-contact-offset .00075` is an opt-in numerical correction for both the
standalone probe and YAM preview. It changes only native contact generation:
cloth rest offset stays0.20 mm, material thickness stays0.40 mm, and geometry,
material, thread parameters and every validity guard remain unchanged. The
combined contact-to-rest discovery margin becomes0.60 mm instead of0.10 mm.
In the recorded041 failure, the capsule endpoint moved0.317 mm relative to the
adjacent triangle in one native step, beyond the previous margin.

NVIDIA describes contact offset as the distance for predictive contact creation,
while rest offset controls the resting separation, and recommends a larger
contact envelope for fast or thin objects. Larger envelopes may add contacts
and artifacts, so this remains a measured candidate rather than a claim of
physical accuracy. [Official contact-offset documentation](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/110.0/dev_guide/rigid_bodies_articulations/collision.html).

The guarded first-cut candidate uses this option with the unchanged frozen
294-action plan and normal episode reset. Native047 failed before pickup at
0.167708 s on an upper-hole axis intersection. Peak extension stayed below1%,
but normal-to-cloth velocity reached0.700/0.560 m/s with unlimited native
depenetration velocity. The larger generation envelope alone does not fix
contact stability. See `evidence/native-predictive-contact-047.json`.
The next bounded candidate adds the existing `--max-depenetration-m-s .05`
option, keeping every geometric and material guard unchanged.
