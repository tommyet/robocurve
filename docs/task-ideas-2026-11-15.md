# New task ideas: novelty and viability

Implementation update, 16 November: the user selected bracelet fastening,
present wrapping, pram rocking, knot removal and wax-strip technique for
building and submission. Current results and PRs are in the
[five-task record](five-household-task-batch.md). The research below records
the earlier screening; it is not the current development status. Waxing is
scoped to applying, smoothing and peeling a strip on a practice form, without
a hair-removal claim.

Checked 15 November 2026, after the necktie submission and GPU shutdown.
No simulation, GPU or Dream work was performed for these ideas.

This screen searched the titles of 2,167 upstream PRs, the titles/instructions
and relevant descriptions of 542 current board records, and the matching PRs'
review histories. It also checked the 1,016-entry BEHAVIOR catalogue, RoboCasa,
RoboDojo and relevant primary research. A missing match is not a guarantee of
novelty. Recheck the live board and ownership immediately before development.
The feasibility assessments below are engineering judgments, not test results.

## Shortlisted for later

- **Help fasten a bracelet — selected by the user on 15 November.** Keep this
  on the development shortlist; this selection is not authorization to build
  or spend compute yet. Fit and fasten a functional, real-size clasp on a
  flexible bracelet around a wrist form, then release it.
- **Wrap a present — stronger conditional candidate after the follow-up.**
  The user's intended task is folding paper around a box, holding the folds
  and taping them closed. BEHAVIOR's published goal does not require those
  closure mechanics. See the [follow-up comparison](task-ideas-followup-2026-11-15.md).
- **Genuine charging-cable knot removal — research reserve.** More promising
  than necklace untangling for the current grippers, but not a new research
  problem and not yet demonstrated in our simulator.
- **Rock a pram — conditional backup.** Keep the physical dynamics realistic;
  extra repetitions or arbitrary timing constraints do not establish novelty.

The follow-up also screens waxing, trap setting, suitcase packing, tattooing
and cocktail shaking. None has been authorized for implementation by this
research request. The recommendations below record the earlier screen;
the recommended order has been updated using the follow-up findings.

## Findings

| Idea | Existing coverage | Viability and decision |
|---|---|---|
| IKEA assembly | [Cam-lock shelf assembly #1520](https://github.com/robocurve/benchmark-tasks/pull/1520) is pending after revisions. [Dowel joining #2003](https://github.com/robocurve/benchmark-tasks/pull/2003) needs revision. [FurnitureBench](https://clvrai.github.io/furniture-bench/) already covers furniture assembly. | Mechanically feasible with real connector dimensions and functional engagement, but generic assembly is crowded. Do not build another shelf/cam-lock task. A genuinely different repair or misassembly diagnosis would need a separate novelty check. |
| Move a mouse and click | [Mouse drag-and-drop #1840](https://github.com/robocurve/benchmark-tasks/pull/1840) is accepted. | Straightforward to simulate, but moving and clicking is already contained in that accepted task. Drop. |
| Wrap a present | No close Robocurve submission found. BEHAVIOR's [Christmas gift box](https://behavior.stanford.edu/knowledgebase/tasks/make_a_christmas_gift_box-0.html) explicitly requires wrapping paper over a box, although the paper asset is marked planned. | Conditional. Real creasing, end-flap folding and tape that retains the wrap after release could add a meaningful skill beyond an overlay predicate. Flexible paper plus adhesion makes this a less predictable cheap build. Do not claim the broad idea is new. |
| Retrieve stuck toast | [Low toast retrieval with wooden tongs #1457](https://github.com/robocurve/benchmark-tasks/pull/1457) is pending, with the extra-lift lever and unplugging represented. | Feasible, but almost exactly the proposed household problem. Starting unplugged does not distinguish it. Drop unless the objective becomes a genuinely different mechanical repair. |
| Peel a potato | [Peel the cucumber #1899](https://github.com/robocurve/benchmark-tasks/pull/1899) is accepted. Its model uses contact-qualified skin patches rather than peel ribbons. | A useful modelling precedent, but changing the vegetable is unlikely to justify another peeling task. Drop as proposed. |
| Rock a pram | No close Robocurve task found in the searches; no match in the checked BEHAVIOR/RoboDojo task catalogues. | Technically one of the simpler options: a full-size wheeled pram, restrained weighted dummy, bounded reciprocal travel and a controlled stop. Keep as a backup. Repeated pushing may fail the complexity bar, and mechanical rocking must not be presented as evidence of soothing an infant. |
| Scrub a pan with a tough oil stain | BEHAVIOR lists [clean a grill pan](https://behavior.stanford.edu/knowledgebase/tasks/clean_a_grill_pan-0.html) and other pan-cleaning tasks. [Scrape charred food from a griddle #2019](https://github.com/robocurve/benchmark-tasks/pull/2019) is pending. | Contact-dependent dirt removal is feasible, but a tougher stain alone is weak novelty. Drop the generic version. A distinct cleaning mechanism would need its own comparison. |
| Spray and wipe a surface | Robocurve includes pilot wiping tasks TK-8VAYXV and TK-Y9E26E. [RoboCasa](https://robocasa.ai/docs/build/html/tasks/composite_tasks.html) includes WipeTable and ScrubCuttingBoard. [Window squeegeeing #1978](https://github.com/robocurve/benchmark-tasks/pull/1978) was rejected for existing benchmark overlap. | Easy to approximate; weak novelty. Adding a spray step to ordinary wiping is unlikely to be enough. Drop. |
| Untangle cable / wire / jewellery | [Uncross two cables #13](https://github.com/robocurve/benchmark-tasks/pull/13) was rejected as too close to the cable-identification family. [The revised cable-identification task #12](https://github.com/robocurve/benchmark-tasks/pull/12) was accepted. Published [cable-untangling benchmarks](https://yuhao-zhou.com/5_dof_gripper/index.html) also exist. | Conditional, high risk. Removing a genuine knot or freeing an entangled chain is different from lifting a simple crossing, but requires a strong distinction from existing work. Self-contact must prevent strands passing through one another; cutting, disconnecting or breaking the object must not count. Jewellery is harder than a thicker cable. |
| Help put on a bracelet | No close Robocurve match found; no bracelet-fitting entry in the checked BEHAVIOR/RoboDojo catalogues. | Best lead. Fit a real-size bracelet around a wrist form and fasten a working clasp, then release it. A documented fold-over or box clasp may be more practical than a tiny lobster clasp. Preserve the flexible band and actual latch operation; avoid an oversized toy clasp or automatic proximity attachment. |
| Prune a plant | [Trim hedge shoots while sparing flowers #1059](https://github.com/robocurve/benchmark-tasks/pull/1059) is accepted. [Prune a rose above its bud #1298](https://github.com/robocurve/benchmark-tasks/pull/1298) is pending after revisions. | Feasible, but directly occupied. Drop ordinary pruning. Changing plant species or cut count is insufficient. |
| Operate a fire extinguisher | [PASS task #1928](https://github.com/robocurve/benchmark-tasks/pull/1928) and [bin-fire task #1016](https://github.com/robocurve/benchmark-tasks/pull/1016) were finally rejected for unrealistic scale, loads and working distance. [Inspection #1242](https://github.com/robocurve/benchmark-tasks/pull/1242) also replaced the mechanism and used hidden fault information. | Conditional, not a cheap first choice. A real-size training unit with functional pin, seal, lever and hose, credible operating loads and working distance is required. A tabletop miniature would repeat the rejected designs. Training-target coverage can be measured; it must not be sold as validated fire-suppression physics. |

## Recommended order

1. **Bracelet fitting and fastening:** strongest combination of familiar value,
   a clear end state and an apparent gap. Before spending, choose a real clasp
   whose working surfaces are accessible to YAM fingers. Score closure and
   retention on the wrist form after release, with an intact band and clasp.
2. **Gift wrapping:** a stronger conditional candidate after comparing the
   actual BEHAVIOR goal. Focus on folding and securing a loose sheet around
   a box, with the wrapper retained after release. Existing carton taping is
   adjacent accepted work, so tape alone is not the distinction.
3. **Pram rocking:** reserve option with simpler mechanics. Establish why the
   controlled motion is a worthwhile task, using observable travel, timing,
   upright retention and stopping criteria. No claim about infant response.

Real knot removal and full-size extinguisher operation can remain longer-term
possibilities. Neither is a sensible automatic next build on a small budget.
The other ideas should be parked in their current form.

## Lessons from the reviews

- Familiar household work fits societal relatability. The toaster revision
  changed category because explicitly prescribed precautions did not establish
  independent safety judgment.
- Scale and functional geometry matter. The cam-lock reviews checked whether
  bolt heads actually fit the holes and reach the cams; the extinguisher reviews
  rejected smaller, lighter, easier hardware and a shortened operating range.
- Score the achieved outcome. The accepted hedge task removed prescribed blade
  angles from physical judging and instead judged whether the correct shoots
  were severed. Those angles remained a disclosed simulation approximation.
- Later damage must invalidate success. Rose pruning was sent back because a
  good first cut retained full credit even after another cut removed the bud.
- Generic wiping is already covered. Changing a stain model or adding a step
  does not automatically establish a new core skill.

Further primary references: [RoboDojo simulation catalogue](https://robodojo-benchmark.com/doc/sim-tasks/),
[real-task catalogue](https://robodojo-benchmark.com/doc/real-tasks/),
[robotic paper wrapping](https://arxiv.org/abs/2411.08389), and
[cooperative paper wrapping](https://arxiv.org/abs/2511.03181).
These demonstrate prior research or catalogue coverage, not acceptance by Robocurve.

Local snapshots and full relevant review comments are retained in ignored
`artifacts/new-ideas-2026-11-15/`. No assets or task implementations were built.
