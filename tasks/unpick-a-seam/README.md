# Unpick a seam

Remove the six tacking stitches joining two canvas patches. Separate the patches
without cutting or tearing either one.

**Development package; not ready to submit.** No robot demo, Dream run, media or
task score exists. `task.draft.json` is a draft. Native probes are being checked;
short native contact controls now pass at 3,840 Hz, but full manipulation is unproven.

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

Twenty-seven tests pass: connected cloth with real needle holes, needle-path clearance,
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

The YAM integration completed 87 native substeps before the unchanged 2% strain
stop; no complete action or pickup is demonstrated. The frozen pickup/approach
plan remains unrun.
`preview_yam.py` records ordinary robot actions, every-substep audits, native
blade/thread force events, video and cloth/thread traces. It stays unscored.
The draft setup remains fixed, with no random jitter, seed 0 and a limit of
2,400 actions at 20 Hz. The larger diagnostic thread has not been adopted as
the final task specification.

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
