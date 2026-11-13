# Tie a necktie on a collar form

**Development only; not ready to submit.** Native cloth reset, grasp and a retained handoff work. A complete four-in-hand knot, Dream run,
final score and uploaded media are still missing.

Tie a child-sized necktie on a collar form and leave it ready to wear. The task
requires a broad fabric strip to face correctly, wrap and thread through its
front loop, tighten and retain a wearable fit. A centreline knot invariant
alone does not establish success.

## Run

Use the pinned Isaac Sim 6.1 / IsaacLab / YAM environment in `ENVIRONMENT.json`.
From the repository root:

```bash
# CPU checks; these do not prove simulation or task success.
.venv/bin/python -m unittest discover -s tasks/tie-a-necktie -p test_local.py
.venv/bin/python tasks/tie-a-necktie/run.py --check-only

# Native drape and contact diagnostics.
python tasks/tie-a-necktie/probe.py --mode collar-drape --seconds 3 --output /tmp/tie-drape
python tasks/tie-a-necktie/probe.py --mode free-fall --seconds 3 --output /tmp/tie-fall
python tasks/tie-a-necktie/run.py --mode motion-probe \
  --plan tasks/tie-a-necktie/handoff-plan.json --judging-views --out /tmp/tie-handoff
```

The station runs at 240 Hz physics and 20 Hz control. `reset_scene.py` resets
once and advances exactly 100 ready-position control steps (5 seconds) before
the first policy observation. The initial uncrossed half-wrap settles through
gravity and collar contact, with no attachment. Every policy must use this
same reset. The proposed task limit is 3,600 actions, including the final
five-second released hold; settling is recorded separately. The seed defaults
to zero.

The runner saves ordinary camera images, optional native 960×720 judging
views, source hashes, runtime and assessor telemetry. Frozen plans contain
ordinary joint commands only; no object or mesh readings feed the policy.
Native self-contact and the absence of attachments are checked. All current
diagnostic scores are null; interrupted runs are recorded as interrupted.

## What has been demonstrated

A bare neck form let the untied fabric fall. Ordinary rigid shoulders support
the selected reset through contact. Initial and settled full-triangle audits
clear the neck, shoulders, collar points, post and base.

Batch015 physically raised the grasped wide-strand patch by 197 mm, retained
it through a two-second hold and dropped it when the fingers opened. The held
patch stayed within 3 mm of the actual gripper centre; eleven sampled
triangle/fixture audits were clear. Batch020's receiving hand pushed the
fabric sideways and missed, so that handoff failed. The revised 640-action
approach aligns insertion with the receiving finger gap and passes sampled
robot hull checks. Batch022 then transferred the tip, lifted it 167 mm and held it for two
seconds. Fabric still snags or rests on the hand during its later open-finger
withdrawal. Nine actual robot-hull audits found no triangle intersection after
a 0.2 mm hull contraction; the deepest sampled node penetration was 0.119 mm.
Clean release remains unproven. The 900-action front-crossing trial retained
both ends but produced 22% local strain and up to 1.46 mm finger penetration.
It is not valid knot evidence. Batch030's 980-action free-tail attempt kept
the wide end in the hand but swept the narrow tail aside, so the wrap unwound.
Ninety-nine sampled states had no transverse nonadjacent triangle crossing;
one fingertip contact reached 0.210 mm triangle penetration. This is still
not knot evidence. Batch032 then pinched the narrow tail, but the rear pass
loaded the wide strip against the shoulder and the narrow grip slipped.
The shoulder penetration reached 0.713 mm and sampled local strain reached
32.7%; that attempt is blocked. `front-space-wrap-plan.json` instead grasps
lower on the narrow tail and brings it forward before wrapping in the space
ahead of the shoulder. Batch035 completes the clear route: 60 sampled fixture and self-crossing
audits pass. The narrow tip nevertheless slips out during crossing and the
wrap unwinds. Batch039 also loses the deeper 40 mm bite during the rear pass.
The wide strip retains considerable slack: its held-to-collar segment has
about 497 mm arc length but only 183 mm endpoint separation as the grip fails.
The narrow strand is swept around the wrapping hand. Whole-arm screening rejects a sideways continuation too. A further physical
wide-tip handoff is being checked so the first arm can leave the crossing
before the opposite arm carries the tip through. No knot or partial score
is claimed. A simpler under/over knot route is CPU-only and
has passed its 1,200-pose hull screen. Its explicit `--inside-out-reset` option
reverses the initial material face before the same physical settling; the
default task remains unchanged. No native simple-knot trial has run.

`MOTION_PLAN.md` describes the remaining wrap, neck-loop passage, front-loop
threading and tightening. No in-progress knot may be carried across resets.

## Setup, physics and scoring

`task.draft.json` and `layout.py` specify every prop and fixed position. The
1.10 m tie is a tapered 35–70 mm strip, represented by 1,973 nodes and 3,504
triangles. Its nominal 1.2 mm thickness and 500 kg/m³ effective density give
28.5 g mass. Pale and gold edge markings make face orientation visible.

Surface FEM models stretch, bend, gravity and self-contact. The strip is an
effective shell, not every sewn textile layer. Friction, bending and elasticity
remain uncalibrated. The collar and shoulders are rigid and do not form any
part of the knot. There are no vertex targets, cloth attachments, runtime
rest-shape edits or artificial tightening forces.

The child-sized tie matches the short form: a roughly 346 mm neckband and
200 mm of extra knot take-up leave about 554 mm for both ends. This length
budget is planning, not proof. Full credit requires a retained four-in-hand,
correct front face, measured collar fit, a 280–320 mm wide-end drop and a
narrow tip at least 10 mm above the wide tip. `JUDGING.md` specifies the photo,
video and ruler checks; simulator geometry alone cannot certify a wearable tie.

```bash
python tasks/tie-a-necktie/judge.py /path/to/judging.json \
  --evidence-dir /path/to/trial --out /path/to/reviewed-score.json
```

The judge verifies evidence-file digests before applying the rubric. Missing
measurements or unknown integrity produce an error. No completed judging
record exists yet.

Native authoring follows [NVIDIA surface deformables](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/deformables_beta/deformable_beta.html).
[TieBot](https://tiebots.github.io/) is relevant prior robotics research. Its
results do not supply a YAM controller or validate this model; novelty relative
to existing knot tasks remains a review question.

An isolated adult-layout candidate is available with `probe.py --adult-collar`
and the matching explicit YAM runner option. It uses a1.45m,37.55g strip and a
raised standalone collar on a rear stand. A162mm lower rim and a physical
folded rear collar retain the neckband; there are no cloth attachments. The
broad shoulder block is removed. Initial triangles clear all fixtures by1mm.

The folded collar retained the adult tie in054. Refinement removed its small
triangle/fixture crossing, but056/057 showed about40% local edge stretch at
the leading flap. The128-iteration058 control reduced maximum edge stretch to9.42%
(p99=2.56%) with no final triangle/fixture intersections. These effective
textile parameters remain uncalibrated. The200-action state-assisted adult
pickup is a separate diagnostic: actual reset cloth selects ordinary pinch
targets, with full commanded-hull checks before movement. Dream receives no
material state. No adult knot or full-score demo has been demonstrated.

Batch061 failed before any action: dropping the initially horizontal adult
strip into the YAM scene produced an out-of-workspace pinch. The next explicit
adult reset uses the recorded untied gravity shape from058 and the same flat
rest mesh. All triangles clear both ready robots by1mm. Each policy still
receives five seconds of ordinary physical settling; this is a shared starting
layout, never a controller write. The new reset and pickup are not yet native
validated. `adult-settled-reset.json` records provenance and hashes.
