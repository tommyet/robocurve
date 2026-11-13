# Unpick a seam

Remove the six tacking stitches joining two canvas patches without cutting or
tearing either patch, then put the seam ripper down. Patch relocation is not
required. See `JUDGING.md` for the final inspection and safe-release criteria.

**Development package; not ready to submit.** No robot demo, Dream run, media or
task score exists. `task.draft.json` is a draft. The current flexible-panel and
passive-thread candidate retained every stitch for2s. Its CPU/YAM reset and
two-action bridge pass. The robot then physically picked up the ripper and
reached the first tack in265actions. No thread was cut or removed; an uncut
thread joint became physically disjoint under tool loading. Full task
feasibility remains unproven. Short contact replays now confirm gross thread
penetration into the tool guard; neither slower motion nor finer stepping
provides a physically valid cutting result.

The 960 Hz replay reproduces joint disconnection after 52 ms. At 3,840 Hz it
completes 100 ms without tripping the existing cloth/joint guards, but a separate
finite-solid audit finds 0.894 mm overlap between the thread and long guard,
whose combined radii are 0.900 mm. That is a contact failure, not a successful
trial. Quarter-speed motion still disconnects an uncut joint. These are
reconstructed, unscored diagnostics, never alternative task resets. See
`evidence/native-contact-replay-120-123.json`. Actual native guard contact must
be verified and corrected before another full robot attempt.

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

Seventy-eight tests pass: connected cloth with real needle holes, needle-path clearance,
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
The same source with `--max-depenetration-m-s .05` also failed before pickup,
at0.08125 s. Peak extensions were0.773%/0.437%; the cap did not preserve
thread/cloth contact. See `evidence/native-capped-contact-047.json`.


### Physical repair backing candidate

`--backed-clamp` adds an ordinary rigid rear board and two front guide rails
to the supported spring-clamp layout. A26 mm high front window exposes both
needle-hole rows and the seam ripper approach. The65 mm rear board leaves
7.5 mm of fabric exposed at each side. The lower sheet remains free to slide;
no cloth attachment, vertex target or changed material is used. The fixture
has a foot, posts and standoffs connected to the existing bolted stand.

Initial geometry has at least0.20 mm clearance from every added solid. The
same294-action first-cut plan clears the complete arm/tool box geometry at
commanded20 Hz poses. This is a CPU screening result; native tracking, thread
contact, cutting and later side extraction remain unvalidated. The candidate
returns to baseline0.25 mm contact offset and unlimited correction velocity,
with every existing crossing, junction, strain and blade-damage guard intact.

```bash
python tasks/unpick-a-seam/preview_yam.py --sewing-clamp --passive-clamp --supported-clamp --backed-clamp --coarse-thread --quality-mesh --contact-refinement combined --physics-hz 960 --plan tasks/unpick-a-seam/evidence/clamp-cut-plan.json --steps 294 --maximum-stretch 1.05 --audit-junctions --crossing-backend warp --profile-steps --out artifacts/seam-backed-first-cut
```


### Native force-integration comparison

The supported standalone041 scene leaves TGS external-force iteration at the
installed schema default, false. YAM047 explicitly authors it true. The wheel
control found unforced angular momentum with true and removed it with false;
that finding motivates a seam comparison but does not prove the seam cause.
`--external-forces-once` sets the option before scene construction and checks
the composed native flag. It changes no material, geometry, action or guard.
The preview also records measured gripper/tool relative poses so an actual
cutting miss can be attributed to tracking or grasp geometry. These measured
poses never feed the frozen policy. See `evidence/external-force-mode-cpu.json`.


### Finite articulated cloth candidate

FEM contact remains invalid after the backing and once-per-step comparison.
The new opt-in `--facet-cloth` route replaces each patch with236 dynamic thin
triangular prisms and passive revolute hinges along their shared edges. The
physical area, needle openings,0.4 mm thickness and total mass are unchanged.
Finite bending springs use D = E_bend t³ / [12(1−ν²)] and the hinge edge length
over the adjacent centroid spacing. The membrane is approximately inextensible;
this is a discrete flexible shell, not FEM or a single rigid cloth proxy.
No fabric facet is attached to the world. The same ordinary clamp/backing
provides support. Neighbouring material facets sharing a vertex have collision
exclusions; thread-to-fabric and distant self-contact remain enabled.

The measured shared-vertex mesh feeds the existing crossing and damage checks.
Every native substep also measures physical hinge-endpoint gaps. The current
0.1 mm stop is a conservative engineering warning, not a competition criterion
or proof that a 0.8 mm thread can escape. Exact solid geometry and persistence
must distinguish contact error from loss of retention; averaging alone cannot
establish either. The first native pair (056) stopped on first-step hinge gaps. Its hull cooking
left the PhysX minimum thickness at1mm, exceeding the actual0.4mm shell and
clamp gap. Explicitly reducing that cooking minimum in057 produced exactly
the same measured states, so it did not establish the cause. The supported
PhysX collision-representation query now measures cooked geometry directly;
contact-free and velocity-iteration controls distinguish fixture contact from
solver/joint bias. Geometry and guards stay unchanged. Native cantilever
bending, retained/open thread contact and full manipulation still require
validation. See `evidence/native-facet-control-056.json` and `evidence/native-facet-control-057.json`. Defaults remain FEM. The
scripted runner is integrated so a successful mechanism gate can proceed
without another scene rewrite. See `evidence/facet-shell-cpu.json`.

```bash
python tasks/unpick-a-seam/probe_facets.py --mode bend --physics-hz 240 --seconds .5 --out artifacts/seam-facet-bend
python tasks/unpick-a-seam/probe_facets.py --mode intact --physics-hz 960 --seconds .5 --out artifacts/seam-facet-intact
python tasks/unpick-a-seam/probe_facets.py --mode open --physics-hz 960 --seconds .5 --out artifacts/seam-facet-open
# Only after the physical gates and visual review:
python tasks/unpick-a-seam/preview_yam.py --facet-cloth --external-forces-once --sewing-clamp --passive-clamp --supported-clamp --backed-clamp --coarse-thread --physics-hz 960 --plan tasks/unpick-a-seam/evidence/clamp-cut-plan.json --steps 294 --maximum-stretch 1.05 --audit-junctions --crossing-backend warp --profile-steps --out artifacts/seam-facet-first-cut
```


### Native primitive panel and pose-assisted entry candidates

The061 freefall pair keeps hinge gaps below0.3µm at both32 and1 velocity
iterations, but its queried collision hulls are1.076–1.099mm thick instead of
0.4mm. The opt-in `--box-panels` candidate merges each rectangular triangle
pair into a native box:118 dynamic panels and189 bending hinges per patch,
with the same physical area, thickness, mass and needle openings. This avoids
convex cooking. The results below supersede the initially pending gates; see
`evidence/native-facet-freefall-061.json` and `evidence/box-panels-cpu.json`.

`--pose-assisted-entry` is a disclosed scripted-demo option. It preserves the
first140 pickup actions, then converts the fixed blade path using measured
tool-in-gripper poses filtered with alpha0.1. It commands only bounded robot
joint targets. No tool or cloth pose is written, and large grasp slip stops
the diagnostic. Native entry remains unvalidated. Dream would keep its normal
camera/joint observations. See `evidence/tool-entry-cpu.json`.

The native box bending coupon (063) completed 0.5 s with a 52.37 mm mean
free-tip drop and only 5.72 µm peak hinge disagreement. This demonstrates
flexibility, not a static material calibration. With one velocity iteration,
all hinge gaps stayed below 34.36 µm, but a zero-thickness crossing warning
appeared beside a needle hole. Exact native-box analysis of the corrected
067 recording confirms three transient thread passages that subsequently
reseated. All 24 initial thread/hole links are restored after 0.4354 s. At
0.5 s there are no box-midplane intersections and the largest remaining
capsule overlaps are 1.06 and 1.25 µm in the two patches. A longer stability
interval is still required before starting a trial from a passively settled
reset. No task score or successful cut is claimed.

The older 063 sparse `thread` snapshot field accidentally contained panel
poses; runtime crossing checks were unaffected. The recorder now asserts
thread body count and saves previous/current raw poses at the first warning.
`--record-every-step --continue-after-audit-warning` is an explicitly unscored
forensic option that preserves the original warning while observing its
persistence. `panel_diagnostics.py` reads these traces to measure actual
capsule/box overlap and hole/thread linking without changing physics or scores.
See `evidence/native-box-panels-063-067.json`.

The longer 068 test **did not settle into a valid retained seam**. One intact
stitch passed through both patches and lost all four hole links by 1.9021 s;
only 20 of the initial 24 links remained. This supersedes the apparent
short-term recovery in 067. Actual thread endpoint motion at the first
permanent escape was 0.409 mm per step, comparable to the 0.4 mm cloth thickness.
The GPU scene has no working continuous collision detection. The new
`--cpu-ccd` coupon option keeps the same geometry and material while selecting
CPU PhysX, sweep CCD and speculative CCD on every dynamic body. Its native
scene/body flags and tensor device are checked explicitly. The CPU results
below are failures, not a feasibility claim. See `evidence/native-box-retention-068.json`
and NVIDIA's [CCD documentation](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/rigid_bodies.html).


The 070/072/075 CPU controls lose uncut thread continuity within 3.125 ms.
Moving the whole scene near the origin lowers initial panel coordinate error
to 1.5 nm, but does not cure the failure. Both hybrid and sweep-only CCD fail.
This precedes loss of the 24 hole/thread links, so the next diagnostic isolates
one free loop with no cloth, table or fixture. It records native mass, inertia,
initial closure and every body pose. An equivalent translation-locked D6
connector follows the working knot rope's implementation; all angular motion
remains free. Disabling self-contact is available only for causal diagnosis
and is not a task setting. See `evidence/native-cpu-chain-070-075.json`.

```bash
python tasks/unpick-a-seam/probe_thread.py --joint-kind spherical --ccd sweep --seconds .05 --out artifacts/seam-loop-spherical
python tasks/unpick-a-seam/probe_thread.py --joint-kind d6 --ccd sweep --seconds .05 --out artifacts/seam-loop-d6
```

The isolated 080 spherical and D6 loops fail identically. In 081, removing
self-contact makes the loop stable, while turning CCD off alone does not.
The original sampling has six exactly tangent non-neighbour capsule pairs.
The opt-in `--clear-thread-sampling` keeps the same centreline, diameter and
mass but uses 24 links, leaving 0.2 mm between non-neighbours at reset. All
ordinary self-contact stays enabled. This is a discretization correction,
not a validated physical fix; the free-loop gate must pass before the intact
seam is tested. See `evidence/native-self-contact-081.json`.

The 24-link free loop passes 48 native steps, but the intact scene still develops
rotational self-contact and loses an uncut joint after 166.7 ms with sweep CCD.
Hybrid CCD fails earlier, after 35.4 ms, with a 1.040 mm uncut joint gap. In both
traces all 24 needle-hole links remain and no actual box midplane passage occurs
before the chain becomes disjoint. This is an unstable contact/constraint
response, not a successful unpicking. See `evidence/native-clear-thread-083.json`
and `evidence/native-hybrid-thread-085.json`.

A matched native PGS control is prepared with the same 24-link geometry, mass,
material, all self-contact and sweep CCD. It changes the contact solver only,
retains every-step evidence and stops on a disjoint uncut joint. No PGS result
or valid manipulation reset is claimed yet.

The PGS comparison also opens an uncut joint at36.5ms, with all24 hole links
retained and no actual box-midplane passage. PGS alone is not a remedy
(`evidence/native-pgs-thread-088.json`). The next material candidate adds
passive thread bending, described in `thread_bending.py` and
`evidence/thread-bending-cpu.json`. Its native D6 swing springs have fixed
straight rest, free axial twist and no angular limits or task-aware forces.
Two free-loop controls test circular equilibrium and rectangular relaxation
before any full seam attempt. These controls are prepared, not validated.

The passive-thread candidate passed both native free-loop controls in090. The
circular loop changes shape by less than3micrometres over50ms; the rectangular
loop relaxes from90-degree maximum bends to19.4degrees over0.2s, with declining
mechanical-energy proxy and no disjoint joint. The complete intact seam then
retained all24 hole links for2s, with no actual box-midplane passage and peak
reconstructed extension below0.29%. Last-second finite contact penetration
peaked at10.6micrometres. This is a usable passive-control result, not robot
feasibility. See `evidence/native-passive-thread-090.json`.

The opt-in CPU/YAM bridge now carries the same geometry, bending and CCD
settings, consistently translating all world roots and fixed cameras near the
seam. Its ordinary reset is unvalidated. A separate zero-bending free-loop cut
checks whether restoring collision between overlapping cut endcaps injects
energy; it is diagnostic only and never qualifies as the task's blade cut.

The093 zero-load cut exposed artificial contact-correction energy when the
formerly adjoining, overlapping capsule endcaps were enabled immediately. An
uncut joint subsequently opened1.24mm. The prepared correction breaks the cut
connection immediately and restores only that pair's contact after the complete
finite capsules separate by their radii plus the native contact margins. All
cloth, tool and other thread contacts remain active. The native zero-load and
elastic-relaxation comparisons must pass before this is used for removal.

The093 YAM attempt stopped before stepping because its tensor view omitted the
attached USD stage ID. Inspection also found unshifted generic Box reset events;
the corrected bridge translates those poses with the world roots and checks the
native tensor device.65 CPU tests pass; native validation remains pending. See
`evidence/native-cut-bridge-093.json`.

The094 deferred cut control removes the zero-load contact impulse: peak
relative kinetic energy stays below1.3e-16J over0.2s. With passive bending,
the ends separate and their ordinary contact returns after2.08ms; all remaining
thread joints stay connected. A later three-step self-contact has at most
0.269mm capsule overlap before clearing. PhysX endpoint velocities briefly
spike, while the unsmoothed pose-difference motion remains bounded; these are
recorded separately rather than turned into an invented energy scoring gate.
See `evidence/native-cut-transition-094.json`. The YAM retry exposed a reset
dtype mismatch, corrected by preserving Python float values in Arena Pose
configuration. Neither free-loop control is a robot cutting demonstration.

The097 CPU/YAM bridge passes two ready-hold actions with96 physics substeps
audited. The ordinary reset restores cloth positions within1.5nm and zero
velocities. Peak extension is0.173%, all thread/cloth and closed-junction checks
pass, and no blade damage is detected. This establishes integration only; the
294-action first-cut candidate remains to be tested. Native overview images are
clean but too wide to inspect individual stitches. Optional `--judging-views`
adds fixed native close-up views for recording only; camera framing has not yet
been validated. See `evidence/native-yam-bridge-097.json`.


## Native first-tack entry 097 and geometric panel audit

The same candidate completed 251 robot actions (12.55 s) with physical pickup
and at most 0.160 mm grasp-position drift. All 12,071 reset/substep thread/fabric
and closed-junction checks passed. Peak cloth stretch stayed below 1%; no
blade-damage event occurred. There was no cutting force, cut or removed stitch.
The run stopped during entry on an upper-sheet Euclidean hinge residual of
110.02 µm against the former 100 µm numerical cutoff. That residual alone does
not identify a tear: it can include compression and tangential sliding. The
recorded averaged mesh cannot reconstruct the missing individual panel poses.
Measurements are in `evidence/native-first-cut-097.json`.

The explicit `--geometric-panel-audit` comparison retains that raw residual
as telemetry and measures actual native shared-edge geometry each substep.
It stops if positive empty aperture exceeds 0.20 mm or the shared edge loses
finite overlap. Normal separation includes both physical half-thicknesses;
compression and tangential slip are reported separately. The limit is half
the 0.4 mm panel thickness and one quarter of the 0.8 mm thread diameter. This
is a conservative numerical continuity diagnostic, not a calibrated tear
threshold. All existing thread/cloth, blade, strain and closed-junction checks
remain active. Native panel poses are saved in each action trace and in the
first-failure and terminal snapshots. A native joint-break observer is also
installed, but the panel hinges have no calibrated finite fracture load;
absence of a notification cannot certify intact real fabric.

The next 294-action comparison uses the unchanged first-tack path, geometry,
materials and physics with `--geometric-panel-audit --judging-views`. The extra
native cameras only record close-ups and are excluded from policy inputs.
This diagnostic is unscored and is not evidence of task completion.


## Native first contact 102 and passage diagnostic

The unchanged entry reached 262 actions before the lower sheet's positive
shared-edge aperture exceeded the explicit 0.20 mm diagnostic limit. The
248.87 µm opening was at an outer edge about 10 mm from the first tack. There
was no empty normal clearance, loss of shared-edge overlap, thread passage or
lost needle-hole link. All 24 links remained, the largest closed-thread joint
gap was 46.24 µm, and peak reconstructed stretch stayed below 1.75%. The native
panel poses show at most 15.27 µm finite thread/panel overlap at the stop. These
measurements do not establish a fabric tear.

The blade had just reached the first strand: its measured contact overlap was
0.248 µm and peak cutting-edge force was 0.248 mN, well below the 0.25 N sustained
cut threshold. Neither guard overlapped either panel solid at the sampled entry
poses. No stitch was cut, and the task remains unscored. Native close-up cameras
now show the seam and tool. See `evidence/native-first-contact-102.json`.

A separately selected `--panel-passage-diagnostic` keeps the 0.20 mm aperture
warning and uses 0.40 mm as the maximum positive empty shared-edge aperture.
This is half the 0.80 mm thread diameter: a geometric passage bound, not a
calibrated fracture threshold or a claim of perfectly rigid joints. Finite
shared-edge overlap is still required. The option also checks each actual
native box's middle plane against every capsule axis at every physics substep,
using unaveraged panel poses. It retains the existing swept thread/fabric,
closed-thread-junction, strain and blade-damage checks. Warning and failure
snapshots preserve raw panel, tool and thread poses. Any real crossing or
model-domain failure still stops the diagnostic; no score is produced.

The conservative broad phase for that exact native-box audit matches all 526
recorded patch states and 300 randomized states with zero numerical differences.
Measured CPU time for both patches fell from 9.20 to 1.60 ms per substep; no
physical setting or audit predicate changed. See
`evidence/solid-broadphase-equivalence.json`. The pending 294-action trial uses
this option with the same path, geometry and material as102. All six actual
stitches must still be fully removed before task completion can be claimed.

A tool-release continuation may declare `pose_assisted_entry_until_step` in its
frozen plan. Live grasp compensation ends after that closed-grasp action, before
the fingers intentionally open; ordinary joint and rate limits continue. Existing
294-action entry plans keep compensation through their final action. The prepared
six-stitch continuation is unrun and remains conditional on actual first-stitch
cutting and removal.


## Native loaded contact 110

The294-action passage diagnostic stopped after265actions at an actually
disjoint uncut thread joint:1.342mm endpoint separation versus0.8mm strand
diameter. Cloth aperture, actual native-box, swept crossing and blade-damage
guards passed throughout; the maximum cloth extension was3.18%. Peak blade
force was47.1mN, below the unchanged0.25N sustained-cut threshold. No stitch
was cut or removed. Exact tool geometry shows the thread folded into the long
guard at the failure, following a valid action265 sample with368µm clearance.
This is a contact/constraint failure, not a legitimate cut or a fabric tear.
See `evidence/native-first-contact-110.json`.

A short standalone contact replay is prepared to compare timestep and tool
speed economically. It initializes the measured action265 poses once before
physics, uses unsmoothed264→265 pose differences because native velocities were
not recorded, and lacks the original solver warm-start history. The held handle
follows the same aligned path through native kinematic targets, while the blade
stays dynamic on its ordinary mount. Robots and cameras are omitted only in
this diagnostic. Geometry, material, cutting law and all physical validity
guards remain unchanged. A baseline must reproduce the fault before comparisons
can establish a remedy. This initialization must never be used as a task reset
or a robot demonstration.
