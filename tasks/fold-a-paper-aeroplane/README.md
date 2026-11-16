# Fold a paper aeroplane — blocked development draft

**Not submission-ready. No PR or media upload.** The starting sheet must be
strictly uncreased. The user rejected pre-creased stock as a fallback.

The current model can retain the two nose folds in a CPU preview. Later folds
still slide, twist or stretch the sheet excessively. The checked-in
`demo-plan.json` is only that 1,280-action prefix. It is not a complete plane,
not a native demonstration and not scored success. The scorer returns zero.
`VALIDATION.json` records the outstanding gates and failed experiments.

## Current approximation

A uniform triangular sheet starts flat with zero rest angles. Geometric stretch
constraints, signed-dihedral bending, local plastic bend retention and layer
contact approximate paper. A finite strip can be pinched within the finger
pad; it follows measured robot poses. The material receives no planned crease,
stage label or desired final shape. Initial stiffness is uniform, including
along the future nose, centre and wing folds.

This approximation is not sufficiently faithful for submission: the best
corner preview has up to 7.1% transient numerical edge stretching. Centre-fold
attempts had larger errors or moved the entire sheet instead of forming a
crease. A private straightedge experiment also failed. Passing the numerical
unit checks does not establish physical fidelity or task feasibility.

The draft sheet is 210 × 154 mm with 31 × 23 vertices. Its front is pale blue
and its back is white, with no fold markings. A fixed 100 × 15 × 2 mm ruler
outside the working area is only a judging reference; it is not the failed
movable-straightedge experiment. The latter is not part of this task's scene.
Paper stock, complete setup, judging and scoring remain to be validated.

## Continue locally

Local CPU dependencies used here: Python 3.12, NumPy 2.3.5, SciPy, Numba 0.64.0
and llvmlite 0.46.0. Trajectory authoring also needs the team's `yam_arena`
adapter. The native Isaac/YAM target in `ENVIRONMENT.json` has **not** been
verified with this task or these added dependencies.

```sh
python tasks/fold-a-paper-aeroplane/test_paper.py
python tasks/fold-a-paper-aeroplane/make_plan.py /tmp/nose-prefix.json --nose-only
```

The generator uses predicted material states offline to choose grasp positions.
Its output contains ordinary joint targets and no runtime material feedback.
Without `--nose-only`, it also attempts the unsuccessful bimanual centre fold.
An optional `--resume /path/to/output.nose2.pkl` resumes a trusted local
checkpoint only when the material and solver hashes match.

The unit checks cover the bending gradient against finite differences and the
flat sheet staying flat without contact. Private experiments and their source
snapshots are under `artifacts/plane-spoon-cake-2026-11-16/` in the authoring
workspace. They are CPU development evidence, not uploaded submission media.

Before further submission work, recheck current task-board novelty, including
the separate [IROS origami challenge](https://robotic-origami-challenge.github.io/)
which also includes paper-plane folding. No claim of universal novelty is made.
