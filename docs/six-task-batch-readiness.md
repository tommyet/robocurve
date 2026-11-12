# Six task development batch

Requested 12 November 2026. Develop the six tasks below for review before submission, aiming for about **$3 per task / $18 for the batch**. No upstream PR is authorized yet. A task is ready only after a credible full-score robot demonstration, a Dream baseline, independent rescoring and matching anonymous media exist.

## Current status

All six are in local development. None is submission-ready. Draft metadata deliberately omits claimed run scores and media IDs until actual trials exist.

Each folder now has a proposed setup, concise task description, scoring and judging notes, a licence, a target environment manifest and an explicit `VALIDATION.json`. Native simulator code is authored but unexecuted. The environment manifests describe the retained installation previously verified for another task; they do not claim these six have run there.

| Package | Local implementation | Main remaining engineering work |
| --- | --- | --- |
| [Wheel](../tasks/true-a-bicycle-wheel/README.md) | Coupled elastic rim/spoke model, nipple adjustment probes, released-wheel and individual-spoke judging | Validate native wheel, wrench/nipple contact and torque, physical response, reach and robot controller |
| [T-shirt](../tasks/peg-out-a-tshirt/README.md) | Two-layer surface cloth with real garment openings; two dynamic spring pegs; YAM scene and bounded smoke recorder | Validate cloth/line capture and released retention; establish reachable reset and robot controller |
| [Staple](../tasks/remove-a-staple/README.md) | Irreversible steel bending and paper damage laws; unilateral jaw-contact tests; native wire coupon | Implement and validate the coupled thin-paper, puncture-hole and full-staple extraction scene |
| [Seam](../tasks/unpick-a-seam/README.md) | Two cloth meshes with real needle holes; six contact-held thread loops; force-qualified cutting; YAM preview and blade-crossing audit | Validate thin contacts, tensile damage, released-stitch inspection and robot controller |
| [Cake](../tasks/pipe-a-shell-border/README.md) | Passive dispenser and pressure reaction; finite icing reservoir; gravity, slumping, metal-lip contact; YAM preview | Demonstrate shell ridges, complete robot/material contact, tune the controller and compare scoring with photos |
| [Necktie](../tasks/tie-a-necktie/README.md) | Broad surface cloth, collar form, visible edge markings; YAM scene and bounded smoke recorder | Validate settled reset, self-contact, physical threading/tightening, wearable retention and robot controller |

The remaining work includes implementation as well as GPU verification. Funding alone would not make these packages ready. Material behaviour and judging tolerances need credible reference checks before final evidence. No new media has been uploaded and no upstream PR has been opened.

Local review passed **76 CPU tests**: wheel 19, T-shirt 7, staple 17, seam 9, cake 14 and tie 10. These cover geometry, material laws and adverse scoring cases; they are not successful robot trials. The shirt and tie definitions also load through the pinned YAM task-file loader. Their smoke runners explicitly reset the environment and record assessor state separately from the constant ready-pose action. The tie's 4,464 initial triangles pass a 1 mm fixture-clearance check; gravity settling is still untested.

| Task | Defining interaction | Evidence needed before full runs |
| --- | --- | --- |
| True a bicycle wheel | Turning spoke nipples changes spoke tension and elastic rim shape | Contact-driven wrench rotation, stable elastic response, released runout measurement, rejection of a slack-wheel shortcut |
| Peg out a T-shirt | Real spring pegs retain flexible fabric on a line | Native cloth draping and self-contact, physical jaw opening, cloth/line capture and unsupported retention |
| Remove a staple | A remover unbends and withdraws clinched steel through paper | Plastic bending, paper-hole contact, irreversible tearing under misuse, complete released extraction |
| Unpick a seam | A seam ripper cuts joining thread while preserving both cloth pieces | Stitches physically join flexible layers, blade contact causes cutting, misuse can damage fabric |
| Pipe a shell border | Squeezing a dispenser deposits icing with controlled starts, stops and shape | Finite reservoir, force/flow coupling, material deposition and slump, observable shell shapes without target-aware spawning |
| Tie a necktie | Flat fabric wraps, passes through itself and retains a wearable knot | Surface cloth self-contact, grasp and slip, collar fit, functional knot retention after release |

Accepted examples are references for useful approximations and submission structure, not proof that a new model is valid. The accepted [cord-cutting task](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/cut-taut-cord) uses measured blade contact force before a cut; [panel painting](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/finish-painting-panel) uses geometric contact-driven coverage. The defining interaction still has to cause the result.

## Compute plan and blocker

At 12:01 UTC on November 12, Brev's billing profile reported **−$2.28 remaining**. A second read confirmed it. The usage breakdown total was $189.74 compute plus $12.5482 storage. Both team VMs were stopped. These are organization totals, not costs incurred by this batch or proof of which teammate incurred a charge.

The retained `robocurve-dice` rate remains $2.729872/hour including its catalog storage rate while running. Its previous installation is preserved. No VM start, simulator trial or Dream prediction has been made for this batch. GPU validation is waiting for funded access; local development continues. The guide says program credits cannot be topped up, so another available account or an arrangement with the organizers may be necessary. No organizer has been contacted.

Provisional allocation, to refine using the first measured runtimes:

- $2.25 per task for active GPU runs, about 49 minutes at the current rate.
- $0.50 per task reserved for Dream requests; this is an allowance, not a verified charge forecast.
- $1.50 shared allowance for startup, shutdown, transfer and idle overhead.
- Total: $18.00. Do not count posted balance changes as the batch cost when billing lags. Track lifecycle elapsed time, run times and model charges separately.

This is a spending target, not a demonstrated completion cost. In particular, thin paper damage and broad-cloth knotting remain substantial technical risks. Test their defining interactions briefly before spending on a full robot trial.

Prepare and test locally. Batch short material diagnostics first, then approximately 200-action robot smoke tests. Only spend on final-length demo and Dream runs after the relevant mechanics work. Use one shared VM, run trials sequentially, verify no teammate is active, download/hash-check evidence and confirm shutdown. Do not consume the whole task allowance repeating a failed physical model without resolving the cause.

The first funded session should check the shared native cloth API once before trying all three fabric tasks. Then compare the shirt's closed/open clamp controls, the seam's intact/open stitches and the dispenser's zero/applied-force controls. Run the wheel's isolated ring before its complete native scene, and the staple's wire coupon before developing a full extraction trial. A failed prerequisite stops that task's longer runs; it does not justify spending on Dream to diagnose physics.

## Final readiness checks

1. Refresh board and all-state PR history; inspect any similar task's review and claim status. Clothes pegging has a previous finally rejected attempt, [#760](https://github.com/robocurve/benchmark-tasks/pull/760#issuecomment-6817178720). Its appeal window is still open; do not assume the idea is free merely because the PR is closed.
2. Complete the real-prop setup: dimensions, materials, initial layout, reset and any calibration assumptions. Use goal-only instructions and concise context.
3. Verify that robot contact causes the result, and that ordinary misuse/failure can occur. No proximity-triggered grasping, automatic pegs, decorative fabric, preset shells or animated knots.
4. Use the same scene, action limits and physical model for demo and Dream. New review feedback rejects privileged object-state corrections; feedback in the submitted demo must use policy-available observations.
5. Score all possible final outcomes with ordinary observable measurements, partial credit and damage gates. A numerical solver unit test is not a successful robot trial.
6. Produce a complete full-score demo and Dream run, save source hashes and traces, independently rescore, inspect the videos, and make the matching setup screenshot.
7. Finish each self-contained task folder with run/scoring commands, actual wall time, versions, seeds, license, fidelity limitations and validation evidence. Upload media and open one isolated PR per task only after the user authorizes submission.

Private source snapshots, detailed financial observations and experimental outputs are under the ignored `artifacts/six-task-batch-2026-11-12/` directory. Task-local evidence must identify CPU diagnostics as diagnostics and must not claim an unrun demo score.
