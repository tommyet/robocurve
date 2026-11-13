# Remove a staple without tearing the papers

**Development package; not submission-ready.** The flexible-paper reset and
short YAM integration pass. A one-handed lever attempt is prepared; complete
removal, a full-score demo, a Dream run and media are still missing.

The robot uses a forked remover to release a clinched staple while preserving
the thin paper around its holes. This is a document-preparation task. The
complete staple must finish at least 10 mm clear of both sheets and remain
released for three seconds. It may rest on the released remover.

## Current model

Two free 210×148×0.1 mm,80 gsm sheets lie on a 210×128×20 mm support. The upper
sheet starts 12 mm forward. A 1.5×16×8 mm pocket clears the clinched staple legs.
The staple has a 12.8 mm crown,6 mm legs and 500×300 µm steel section, passing
through existing 0.8×0.6 mm punctures. A 45 g forked steel/ABS lever remover rests
beside the sheets. `setup.json` defines the fixed dimensions and coordinates.

Each sheet consists of native 100 µm box panels joined by passive bending
hinges with finite breaking strength. The sheets are flexible, have no pins
or attachments, and move through native gravity and contact. Analytic boxes
avoid the collision cooker's minimum thickness for thin triangular meshes.
The free staple uses contact-driven plastic steel hinges. No grasp latch or
scripted extraction moves the objects.

The panel approximation is internally inextensible and isotropic; its elastic
bending does not retain permanent creases. Steel bending is planar. Every
physics substep checks steel continuity and wire crossings through intact
paper, alongside the selected paper-continuity diagnostic. `MATERIAL_DOMAIN.md`
explains the approximations and distinguishes numerical residuals from tears.
The whole station receives one fixed coordinate translation before construction
to avoid single-precision errors near the tabletop; relative geometry is unchanged.

## Measured progress

- The contact-driven steel coupon retains 0.87567 rad of bend. A no-contact
  control retains 0; halving the step changes the positive result by 0.28%.
  This validates that small mechanism, not a completed removal.
- Full-size passive panel contact and a short CPU/YAM control pass with PGS
  at 500µs. The active loaded candidate uses 128 position and 4 velocity iterations.
- Native bracing reaches 46 actions. The largest raw paper endpoint mismatch
  includes compression and slip. Across all shared edges, the recorded state
  has 120.69 µm maximum positive opening, no empty normal gap and finite overlap.
  Steel crossing checks remain clean. This does not establish a tear or success.
- A slower brace still stops at 89 actions with 171.59 µm positive aperture,
  no native hinge-break events and clean wire crossings. The next candidate
  keeps the spare arm at READY and uses the remover's physical heel to oppose
  the lift. All 386 commanded hull frames pass the offline rejection screen.

`VALIDATION.json` and `evidence/` preserve the measured reports and hashes.
Historical FEM and triangular-prism attempts are clearly separated from the
active panel model. There are 69 passing CPU checks.

## Reproduce

The pinned environment and versions are in `ENVIRONMENT.json`. From the
repository root:

```sh
python -m unittest discover -s tasks/remove-a-staple -p 'test_*.py'
python tasks/remove-a-staple/preview_panels.py \
  --out NEW_OUTPUT --steps 2 --physics-hz 2000 --solver-type PGS \
  --position-iterations 128 --recenter-at-paper --judging-views
```

The next bounded 386-action extraction diagnostic adds:

```sh
--plan ONE_HAND_PLAN.json --joint-tracking --geometry-aware-continuity --tool-pose-servo
```

`one_hand_plan.py` compiles that plan from the existing complete extraction
and release plan. The scripted controller may compensate the measured remover
grasp through normal bounded robot joint targets after pickup. It never changes
object state or forces, and Dream cannot use it.

The geometric mode requires positive empty
aperture no greater than 150 µm and finite overlap of every shared edge. It keeps
raw endpoint errors and separately records native joint breaks. It is explicitly
diagnostic-only; the assessor will not certify a score from that mode. The
150 µm value screens contact gaps relative to the 300 µm wire and does not replace
the visible tear rubric.

Each output directory must be new. Read the JSON result rather than trusting
process exit status: simulator shutdown can return zero after a reported error.
The recent 89-action brace diagnostic took 387 seconds excluding installation.
Full runtime is not yet measured. Layouts are fixed; no random seeds are used.

## Judging and remaining work

Use before/after photos of both sides, a millimetre ruler and backlighting.
`JUDGING.md` and `scoring.py` define the numeric conditions and review inputs.
One whole leg clear of both sheets earns 0.5 if preservation checks pass. The
intact staple at least 10 mm clear, both legs out and three seconds of release
earns 1.0. New tears over 2 mm beyond an original hole, any new cut or puncture
elsewhere, broken or altered hardware, or invalid evidence give zero. Creases
alone do not count as tears. Moving the sheets apart is unnecessary.

Before submission, demonstrate valid contact through complete extraction,
independently inspect preservation and final clearance, then run Dream and
score both recordings. Record the final setup and upload media only within
the user's submission authorization. This folder deliberately has
`task.draft.json`, not submission metadata.
