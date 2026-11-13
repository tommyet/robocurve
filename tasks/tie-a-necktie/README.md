# Tie a necktie on a collar form

**Development draft; not ready to submit.** An adult tie reset and physical
pickup work. A complete knot, released fit, Dream run and final media are
still missing. No task score has been claimed.

Tie a simple (Oriental) knot on a collar form and leave the tie ready to wear.
This requires managing a flat strip, threading two real openings, preserving
the outward face and adjusting the finished knot.

## Run

Use the pinned Isaac Sim 6.1 / IsaacLab / YAM environment in
`ENVIRONMENT.json`. Run from the repository root:

```bash
# CPU checks do not demonstrate physical feasibility.
.venv/bin/python -m unittest discover -s tasks/tie-a-necktie -p 'test_*.py'
.venv/bin/python tasks/tie-a-necktie/run.py --check-only

# Adult physical pickup diagnostic; not a scored task demo.
python tasks/tie-a-necktie/run.py --mode motion-probe \
  --plan tasks/tie-a-necktie/adult-pickup-plan.json --steps 220 \
  --adult-collar --inside-out-reset --state-assisted-grasp \
  --judging-views --out /tmp/adult-tie-pickup

# Bring the held wide strand forward; this shorter diagnostic is validated.
python tasks/tie-a-necktie/run.py --mode motion-probe \
  --plan tasks/tie-a-necktie/adult-handoff-plan.json --steps 280 \
  --adult-collar --inside-out-reset --state-assisted-grasp \
  --state-assisted-handoff --judging-views --out /tmp/adult-tie-forward-carry
```

The station uses 240 Hz physics and 20 Hz control. Every policy receives the
same untied, source-authored gravity shape followed by five seconds of native
settling. The rest mesh remains flat. The proposed limit is 3,600 actions,
including a final five-second released hold. The seed defaults to zero.

The scripted feasibility controller explicitly reads cloth geometry to place
ordinary fingers. It cannot reposition material, add attachments or apply
extra forces. Dream will use normal camera/joint observations on the identical
scene. The runner records the actual controller inputs, executed plan, native
node states, robot links, source hashes and optional 960 × 720 judging views.

## Evidence and limits

Native batch070 completed 220 actions in 228.75 wall-clock seconds. The marked
wide-strand patch rose 318.7 mm and remained about 22 mm inside the fingers
through a one-second hold. Ten recorded robot-contact checks found no full
triangle intersection after a 0.2 mm hull contraction; the greatest sampled
node penetration was 4.8 µm. Twelve fixture checks were clear. Final maximum
edge strain was 4.71%, with 99% of edges below 1.29%. These are diagnostic
measurements, not calibrated textile accuracy or a knot score.

Batch101 completes 580 actions but misses the handoff. The receiving finger
pushes the tip aside, then lifts empty. Sampled robot, fixture and cloth
self-contact checks are clean; none establishes a grasp. Batch115 then carries the held wide strand 70 mm forward and retains it
23 mm inside the fingers, with 419 mm lift and clean sampled contact checks.
The released receiving attempt enters along the finger axis with a 10 mm
bite. Its commanded rigid checks pass; static cloth predicts a brush against
the loose narrow tip, which requires native integrity review. A broad empty-
pinch check stops the original release when the receiving hand is empty.
Batch119 retains the transfer and lifts the tip 279 mm, but the falling middle
section crosses the wide strip after release. It is not valid knot evidence.
The next attempt raises the receiving tip while both hands retain the strip,
then releases the original pinch to avoid that uncontrolled fold. Batch126
reaches native action549 before its 480-second cap. The tip remains in the
receiving fingers, but two wide-strip crossings and transient fingertip
penetration still invalidate contact integrity. Its interrupted trace was
recovered separately; the original archive remains unchanged. Earlier trials
and failed routes remain in `VALIDATION.json`; no knot is demonstrated.

The interrupted transfer used the same command above with `--steps 580`.
It remains unscored and stops before knot construction. Another run needs a
corrected material route, not merely a longer cap. Use a fresh output directory;
running requires an active, authorized compute session.

## Setup and judging

`task.draft.json` lists the complete setup: a 1.45 m, 37.55 g tapered fabric tie,
a 110 mm neck form with a physical folded collar and a rear stand. There are
no shoulders or hidden cloth constraints. The strip uses native surface FEM
for stretch, bend and self-contact; a single effective shell approximates the
sewn/interlined tie. Material coefficients are engineering estimates.

`JUDGING.md` uses the video, front/rear photographs and a ruler. Partial credit
requires a retained simple knot. Full credit also requires correct face and
tip ordering, collar fit and the proposed 400–440 mm wide-tip drop below the
neck form's lower edge. Those fit bands remain provisional until a complete
physical knot is demonstrated. The narrow tip must remain above the wide tip.

```bash
python tasks/tie-a-necktie/judge.py /path/to/judging.json \
  --evidence-dir /path/to/trial --out /path/to/reviewed-score.json
```

The judge binds measurements to evidence hashes. No completed judging record,
Dream run or submission media exists. Historical child layouts remain
available only as explicitly identified diagnostics.

Native authoring follows [NVIDIA surface deformables](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/deformables_beta/deformable_beta.html).
[TieBot](https://tiebots.github.io/) is relevant prior research; it does not
supply this YAM controller or validate this contact model.

The revised receiving approach reached action308 in batch086 before an arm
occluded an optional judging camera. The original cloth pinch remained held;
seven sampled robot/cloth checks found no deep intersections. Recording now
keeps and flags occluded review frames rather than stopping physical execution.
This historical camera interruption is superseded by batch119: the receiving
pinch retained, but strip self-crossing invalidates transfer integrity. A
complete valid handoff and knot still require native evidence.
