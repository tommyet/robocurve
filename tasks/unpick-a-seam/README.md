# Unpick a seam

Remove the six tacking stitches joining two canvas patches. Separate the patches
without cutting or tearing either one.

**Development package; not ready to submit.** No robot demo, Dream run, media or
task score exists. `task.draft.json` is a draft. Native probes are being checked;
contact stability at this scale remains unresolved.

## Setup

The station table is at Z = 0.7475 m. Two 75 × 80 × 0.4 mm cotton-canvas patches
overlap by 20 mm. The left patch spans X = 0.235–0.310 m and the right spans
X = 0.290–0.365 m; both span Y = −0.040–+0.040 m. Initial middle-surface heights
are 4.0 and 3.2 mm above the table, allowing the thread to settle underneath.

Six red 0.4 mm threads form separate tied tacking stitches at Y = −30, −18, −6,
+6, +18 and +30 mm. Each goes through the same two 1.2 mm needle holes in both
patches, at X = 0.295 and 0.305 m. This is a coarse hand-tacked lap seam, not a
machine lockstitch. The model uses 1.2 mm square openings rather than resolving
yarns; its material parameters describe an approximate coarse canvas prop.

A seam ripper starts on the table at (0.200, −0.120, 0.7555) m, pointing along
+X. Its handle is 70 × 12 × 12 mm; a 1 × 4 × 0.5 mm cutting-edge approximation is
50 mm in front of its centre, between a long point and a shorter guarded point.
Total tool mass is 19 g. The preview builds the tool as dynamic bodies joined by
a permanent fixed joint; neither hand starts attached. There are no clamps or
thread/fabric attachments in the intended task scene.

## Local checks

From the repository root:

```bash
.venv/bin/python -m unittest discover -s tasks/unpick-a-seam -p 'test_*.py' -v
```

Twenty-four tests pass: connected cloth with real needle holes, needle-path clearance,
force direction and sustained contact for cutting, interrupted-contact rejection,
blade damage latching, whole-thread clearance, rigid-motion-invariant strain
inspection, moving-cloth/thread tunnelling detection, and final-state scoring. These are CPU geometry/rule
checks, not proof that cloth or thread dynamics work.

## Next native probes

Use the pinned team Isaac Sim environment:

```bash
python tasks/unpick-a-seam/probe_native.py --mode intact --seconds 3 --out artifacts/seam-intact
python tasks/unpick-a-seam/probe_native.py --mode open --seconds 3 --out artifacts/seam-open
python tasks/unpick-a-seam/preview_yam.py --steps 60 --out artifacts/seam-yam-preview
```

The retention probes rotate the sewn pair vertically and grip only the top edge
between declared physical clamp jaws. Compare retained intact stitches with
deliberately pre-cut loops; the latter are a negative control, never a demo.
All cloth vertices remain dynamic. The YAM preview uses the horizontal task
layout, an ordinary ready robot pose and native blade/thread contact forces.
It stays unscored. No probe uses Dream, object-motion animation or pose feedback
to a policy. The initial 0.4 mm thread failed the crossing audit after 19–20 ms.
A 0.8 mm thread / 1.6 mm hole diagnostic retained the hanging patch for 0.1 s
with a 2.47 mm drop and maximum principal extension below 0.7%; this short
result does not certify sustained retention. Its 96 substeps took 7.74 s
including startup. Repeated coarse-thread runs then failed the strict crossing
audit at 67.708 ms (intact) and 28.125 ms (open). Offline inspection places those
centreline intersections 17.3 nm and 21.2 µm inside the nearest genuine cloth
boundary, respectively; both lie inside the intersected triangle. The first
distance is near the precision scale of native coordinates, but it remains a
failure. These distances are geometric diagnostics, not tear measurements or
permission to ignore a crossing. See `evidence/native-crossings-009.json`.
Initial layout is fixed,
with no random jitter; intended task seed is 0 and limit is 2,400 actions at 20 Hz.

A contact-settings diagnostic also failed: combined deformable speculative CCD
and four collision subiterations produced crossings at 48.958 ms (intact) and
28.125 ms (open). The intact failure crossed a 1.601 mm hole edge between vertices
0.866 and 0.677 mm from the thread axis. That edge is underresolved relative to
the 0.8 mm thread; the native implementation's exact edge handling is not
established. Contact settings alone did not solve the problem.

The next bounded diagnostic refines the actual FEM/collision mesh locally:

```bash
python tasks/unpick-a-seam/probe_native.py --mode intact --coarse-thread --contact-refinement combined --hole-mesh-spacing .0004 --physics-hz 960 --seconds .2 --out artifacts/seam-hole-mesh-refined
```

`--contact-refinement iterations` sets the native deformable collision multiplier
and pair update frequency to 4; `speculative` enables only deformable speculative
CCD; `combined` enables both. `baseline` preserves their native defaults. All
options preserve geometry, fabric properties and strict audit tolerances. The
report records the authored settings. These controls are documented in the
[native deformable schema](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/deformables_beta/physx_deformable_schema.html)
and were checked against installed PhysxSchemaAddition 110.3.2. Deformable
speculative CCD is separate from unsupported rigid-body CCD in this GPU mode.
Pair updates concern surface-to-surface contact; schema support alone does not
establish an improvement in rigid-thread contact. `--hole-mesh-spacing .0004`
uses conforming midpoint refinement near the same hole boundaries. It creates
4,407 vertices / 8,490 triangles per patch, with hole edges at most 0.4 mm,
unchanged 0.00596928 m² area and all thirteen boundary loops. There are no added
colliders, attachments or enlarged openings. This refinement is unrun; a
successful short probe would still need a longer intact/open comparison. See
`evidence/native-contact-refinement-013.json` for the measured failure and CPU
geometry checks.

## Mechanics and limitations

Each patch is a native PhysX surface FEM mesh: 1,346 vertices, 2,492 triangles and
twelve genuine holes. Six separate 28-link capsule chains pass through those
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

Native FEM cannot change cloth topology at runtime. `DamageAudit` therefore
conservatively invalidates blade crossings rather than claiming intact fabric
survived cutting. It does not simulate tear propagation. `StrainAudit` also
latches any triangle exceeding 2% principal extension as outside the intended
low-strain simulation envelope. That engineering cutoff is not a calibrated
canvas tear strain. [Cotton tensile measurements](https://www.mdpi.com/2673-7248/5/4/67)
show substantial fabric and warp/weft dependence; they do not validate one
universal failure threshold. Both audits are wired to the preview, with native
validation pending.

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
