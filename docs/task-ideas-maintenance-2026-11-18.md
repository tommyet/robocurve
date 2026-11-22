# Maintenance ideas and a fresh shortlist — 18 November 2026

Research only. No GPU rental, Dream call, simulation, task build or competition
submission. Ratings are comparative judgments, conditional on a faithful
full-score demo and a fresh novelty check; they are not calibrated probabilities.
None of the new mechanisms below is validated in our simulator.

## Evidence and scope

- Fresh authenticated [board](https://tasks.robocurve.org/board), 14:49 UTC: 792 records
  (239 accepted, 385 pending, 78 rejected/revisable, 90 pilot). This is the current
  visible catalogue, not the lifetime submission/decision totals.
- All-state upstream index, 14:51 UTC: 2,666 PRs. Searched titles, then current board
  instructions, keywords and relevant setup/context; read the closest public
  review histories. Final rejections can be absent from the current board.
- Live [review prompt](https://tasks.robocurve.org/review-prompt): v24, in use
  since 18 November 07:30:27 UTC. The review compares external suites and our own
  earlier tasks as well as other teams. The recognisability test for Societal
  relatability is stricter than merely using a familiar object.
- Checked the saved 1,016-name BEHAVIOR catalogue and targeted primary robotics
  papers/manufacturer guidance. This is not an exhaustive audit of every task in
  all roughly 35 suites available to the review agent. “No direct match found”
  must not be restated as “never done”.
- Raw snapshots and selected comments remain git-ignored under
  `artifacts/maintenance-ideation-2026-11-18/` in the main local workspace.

Accepted [rotary can opening #1851](https://github.com/robocurve/benchmark-tasks/pull/1851)
is useful evidence of the fidelity standard: it approximates cutting but retains
rim engagement, sustained handle squeeze and cranking. Approximation is allowed;
removing the mechanism that makes the operation difficult is not.

## The seven requested ideas

| Idea | Novelty and acceptance judgment | Viable scope and main risk |
|---|---|---|
| Thread a needle | **Low–medium; not a first build.** No direct board/PR match found, but actual flexible-thread threading has prior robotic evaluations. | Ordinary sewing/darning needle and flexible thread; no rigid aglet, enlarged toy eye or automatic capture. Tail finding, submillimetre access and thin-object collision make this unusually risky for YAM. Score actual passage and a useful free tail visible in a close-up. |
| Open a tin with a tin opener | **Very low: direct accepted duplicate.** [#1851](https://github.com/robocurve/benchmark-tasks/pull/1851), TK-XJDMXF, already tests hand-held rotary opening. | Feasible, demonstrated by the accepted task, but another brand, can size or handle arrangement would not establish novelty. |
| Adjust bicycle seat height | **Very low: earlier pending task.** [#2502](https://github.com/robocurve/benchmark-tasks/pull/2502), TK-VCAYTT, opens a quick release, raises and straightens the loose post, and closes it. | Mechanically straightforward. Changing the height, adult/child bike or clamp tool is a weak distinction. |
| Adjust bicycle-chain tension | **Medium; strongest of these seven.** No direct match found. Distinct from wheel truing and puncture repair. | Use a real-size single-speed bicycle with horizontal dropouts: reposition and centre the rear wheel, secure it, and leave appropriate chain slack through a crank revolution. Axle torque, wheel access and chain dynamics are the feasibility gates. A knob that simply changes a displayed tension value is insufficient. |
| Oil a hinge | **Low–medium.** No direct domestic-hinge-oiling match found. Pending [grease-gun task #1243](https://github.com/robocurve/benchmark-tasks/pull/1243), TK-BYRCR3, and BEHAVIOR bicycle-chain lubrication are neighbours. | Target the real hinge interfaces with controlled application, work the joint and leave it usable without excessive spill. A free-moving hinge with a pose-triggered “lubricated” flag would not measure maintenance. Application alone may be too ordinary to clear the physical difficulty bar; demonstrating reduced friction adds modelling/reset burden. |
| Change a fuse in a plug | **Low–medium, conditional.** The exact domestic idea was [finally rejected in #763](https://github.com/robocurve/benchmark-tasks/pull/763#issuecomment-6816890746) for abstract carriers/rails, not because real plug-fuse handling is inherently unimportant. However real fuse extraction/retention is already being revised in [#1628](https://github.com/robocurve/benchmark-tasks/pull/1628), TK-9363AK. | An unplugged ordinary UK plug, real-size cartridge, actual spring clips and securely restored cover. Keep wire access and tool purchase realistic. Do not claim novelty merely from replacing an industrial holder with a UK plug, or from reading a different fuse rating. |
| Reset a domestic consumer-unit trip | **Very low; skip.** [#2336](https://github.com/robocurve/benchmark-tasks/pull/2336#issuecomment-6930830592) and [#2436](https://github.com/robocurve/benchmark-tasks/pull/2436#issuecomment-6972343861) were finally rejected for insufficient robotic difficulty. | Mechanically easy to simulate, but identifying a breaker and moving it off/on is mostly recognition and sequencing. Adding unplugging or a cover did not rescue the existing ideas. A real fault-diagnosis/safety task would be a different proposal, not an easy reframing. |

### Important distinctions

**Needle threading.** MimicGen/SkillGen's “Threading” inserts a rigid needle into
a tripod hole ([SkillGen task definitions](https://raw.githubusercontent.com/mlresearch/v270/main/assets/garrett25a/garrett25a.pdf));
that is not the same skill as putting flexible sewing thread through an eye.
However [T-NT](https://arxiv.org/abs/2311.02396) actually studies tail finding and
flexible-thread insertion, with simulation and real-robot experiments. Therefore
the idea is not unexplored robotics territory. That paper is a novelty warning,
not proof that this particular task is in Robocurve's comparison library. An
ordinary needle threader is a legitimate possible tool, but would change the
skill and require its own scope/novelty assessment.

**Chain tension.** Specify the drivetrain. On a single-speed bike, changing rear
axle position changes slack and wheel alignment; do not describe an ordinary
derailleur bike as having the same adjustment. [Park Tool's procedure](https://www.parktool.com/en-int/blog/repair-help/chain-replacement-single-speed-bikes)
checks slack, centring, tight spots and axle security. Its example axle torque is
about 25 N·m, so we must check actual tool leverage and robot grip, not reduce the
torque to make a demo succeed. Score physical slack with a ruler under a defined
simple check, alignment and retained wheel position; choose the tolerances from
the selected bicycle. The related conveyor-chain joining [#1882](https://github.com/robocurve/benchmark-tasks/pull/1882)
was rejected for its guided applicator and unsupported jobs-impact claim; it is
not a direct chain-tension duplicate.

**Oil and fuses.** A controlled application can use a disclosed simplified
material model, but no magical success-state switch. The grease-gun reviews show
the need for repeatable ordinary parts and protected gripper pads. For a plug
fuse, [Electrical Safety First](https://www.electricalsafetyfirst.org.uk/safety-advice/home-and-people/house-maintenance/plugs-and-fuses/)
specifies removal from the socket before opening, the correct replacement rating,
secure clip retention and a secure cover. Real trials should be unplugged;
energising mains is unnecessary to evaluate the manipulation. The domestic
recognition case is better than claiming every electrician regularly changes a
particular industrial fuse: that unsupported workforce argument failed in
[#2271](https://github.com/robocurve/benchmark-tasks/pull/2271).

## New shortlist

The first four are the strongest remaining concepts from this pass. The fifth is
an ambitious reserve. All have no direct match in the current board/PR search;
the neighbouring tasks and unresolved risks below still matter. These are
directions to choose for later feasibility work, not permission to rent GPUs.

1. **Put a dropped bicycle chain back on the front chainring and leave it running
   freely.** My first mechanical choice. Start with the connected chain genuinely
   off the front chainring and still on the rear drivetrain. Guide the slack
   links onto the teeth while controlling the crank. Finish with several complete
   revolutions without dropping or jamming the chain. This tests link/tooth
   engagement and coordinated feeding, rather than axle tightening or our wheel
   truing/patching. **Promising acceptance case; medium implementation risk.**
   Preserve tooth engagement, chain slack and real-size access. Do not snap the
   entire chain onto a target path. Compare to accepted gear-meshing tasks before
   building; a flexible derailment recovery is the proposed difference.

2. **Put a silicone swimming cap on a headform, with its rim seated and the face
   clear.** Immediately recognisable bimanual dressing. The robot stretches the
   opening, draws it over the crown, releases and corrects the rim. Score coverage,
   face clearance, intact material and retention after release. **Promising
   acceptance case; high material-model risk.** It needs a real flexible elastic
   shell, not a rigid dome with a snap flag. A bare headform is enough for the
   narrow cap-fitting claim; no hair simulation is needed. [Speedo's guidance](https://speedo.com/en-us/blogs/news/how-to-protect-your-hair-when-swimming)
   establishes the familiar activity. Existing headband/earmuff fitting and our
   embroidery hoop are neighbours; deforming a closed cap around a head must be
   the substantive distinction.

3. **Lift trapped hair out of a hairbrush with a pin-tail comb, leaving the brush
   intact.** One hand steadies the brush; the comb slides under the trapped hair
   and lifts it through the bristle field. Score residual trapped hair, collection
   in a dish and intact pins. **Promising but conditional; medium-to-high modelling
   risk.** [Denman](https://denmanbrush.com/blogs/news/d3-original-styler-7-row-brush-of-the-month)
   and [Tangle Teezer](https://us.tangleteezer.com/blogs/inspiration/how-to-clean-your-tangle-teezer-products)
   describe this real technique. Standard wig fibres and a reproducible starting
   pattern could avoid variable used hair, but any grouped-fibre approximation
   must retain real snagging, sliding and release. A rigid removable “hair mat”
   would erase the challenge. Distinguish this from our genuine-knot removal and
   from generic hair combing; do not claim that merely changing a cable to hair
   establishes novelty.

4. **Compress and fit a foam earplug into a practice ear, then release it once
   retained.** The distinctive skill is preparing the soft plug and inserting it
   before it re-expands, with the ear positioned appropriately. [NIOSH](https://www.cdc.gov/niosh/mining/tools/earplugs.html)
   describes rolling, pulling the ear and holding while the plug expands.
   **Medium acceptance case; medium-to-high implementation risk.** Pending
   [earmuff fitting #2472](https://github.com/robocurve/benchmark-tasks/pull/2472)
   and accepted [ear thermometry #1912](https://github.com/robocurve/benchmark-tasks/pull/1912)
   are close context neighbours. The foam preparation/recovery must make this
   physically different from inserting another rigid probe. Use a compliant
   trainer; score observable mechanical fit and retention, not a simulated claim
   of hearing protection or an unmeasurable internal contact pressure.

5. **Secure a ponytail with a plain hair elastic on a styling head.** Gather the
   loose hair, stretch and twist the elastic, pass the hair through again and
   leave it retained. **Promising recognisability, but an ambitious reserve with
   high simulation and demo risk.** Keep the elastic closed and the hair genuinely
   movable, allowing escape and failed retention. No pre-wrapped loops, glued
   bundle or rigid hair rod. Existing [MOE-Hair](https://moehair.github.io/)
   evaluates patting, finger combing and grasping, rather than fastening a free
   elastic. Pending rope plaiting #2296 and our knot tasks are neighbours, so the
   elastic-loop manipulation and retained hairstyle must be the actual skill.
   This is not the first choice for a small fixed development budget.

## Ideas screened out or held back

- Nail pulling: now directly pending [#2595](https://github.com/robocurve/benchmark-tasks/pull/2595).
- Circlip fitting: already accepted [#1561](https://github.com/robocurve/benchmark-tasks/pull/1561).
- Turning socks inside out: prior [Physical Intelligence evaluation](https://www.pi.website/blog/olympics), even without a direct current Robocurve PR.
- Dumpling folding: existing [DexDeform](https://openreview.net/references/pdf?id=dRysTSDTpE)
  and [RoboCook](https://hshi74.github.io/robocook/) substantially reduce novelty.
- Watch spring-bar fitting: no direct match found, but accepted spring-spindle
  insertion #1847 is a close physical ability; small size alone is not novelty.
- Shoehorn-assisted dressing: new pending [shoe fitting #2666](https://github.com/robocurve/benchmark-tasks/pull/2666)
  makes this a riskier family to enter, even though its clog mechanism differs.
- Loading 35 mm film: no direct match found, but a niche/hobbyist-recognition
  risk under v24 plus custom camera/film mechanics. Accepted LP handling #1921
  is encouraging context, not evidence this other activity will pass.
- Hand planing wood: no direct PR found, but prior robotic planing evaluations
  and difficult cutting-force fidelity make it less attractive than it first
  appears. Do not present it as wholly new or cheaply validated.
- Screen-mesh spline rolling: no direct exact match found, but overlap with our
  tension-and-secure embroidery hoop makes it less attractive as another team
  submission without a clear different ability.

Recommendation: consider dropped-chain recovery first, then cap fitting or
hairbrush clearing if the user prefers a deformable-material task. Keep chain
tension as the best of the original seven, subject to a realistic torque/reach
check. No $3 development-cost promise is justified without a mechanism test.


## 22 November update: eleven further ideas

Read-only research against live review prompt v24 (page timestamp 09:51:44 GMT),
29 all-state public PR keyword searches, and individual review histories. This
was not a fresh authenticated task-board or exhaustive external-suite audit.
No GPU, Dream calls or task development. Ratings below are judgment, not measured
acceptance probabilities. Rejected precedent is evidence of risk, not a permanent
ownership claim; pending/revising submissions can still reserve their ideas.

| Idea | Evidence | Recommendation and validity requirements |
|---|---|---|
| Crush recycling | [Can crusher #2705](https://github.com/robocurve/benchmark-tasks/pull/2705) finally rejected for insufficient relatability; [carton flattening #1858](https://github.com/robocurve/benchmark-tasks/pull/1858) rejected as oversimplified. | Low priority. Specify the actual material and method; preserve realistic irreversible deformation and force. A different recyclable alone does not establish a new skill. |
| Punch a belt | No exact belt-punch hit; [card punching #2146](https://github.com/robocurve/benchmark-tasks/pull/2146) accepted. | Tentative only, with substantial overlap risk. Align a real flexible belt inside a handheld rotary punch and fully cut a functional hole without edge damage. Check achievable handle force; do not reduce material resistance merely to make it work. Hole position/completeness and prong passage can be checked simply. Different material/tool alone is insufficient. |
| Crack walnuts | [Hand nutcracker #1423](https://github.com/robocurve/benchmark-tasks/pull/1423) finally rejected for hardware feasibility; [figure nutcracker #2247](https://github.com/robocurve/benchmark-tasks/pull/2247) for relatability. | Low. #1423 explicitly disclosed a much weaker simulated shell. A practical higher-leverage tool might address force, but still needs real-tool evidence and preserved cracking/control difficulty. |
| Sharpen a knife | [Whetstone #1421](https://github.com/robocurve/benchmark-tasks/pull/1421) requires physical calibration; [honing #3600](https://github.com/robocurve/benchmark-tasks/pull/3600) revised and pending. [Pull-through #3715](https://github.com/robocurve/benchmark-tasks/pull/3715) finally rejected as a duplicate of the honing ability. | Do not pursue another tool variant. Valid scoring needs evidence of sharpening work, not just a visually plausible pass count. |
| Rack pool balls | [#1992](https://github.com/robocurve/benchmark-tasks/pull/1992) accepted/merged. | Exact requested activity already accepted, including tightening the rack and removing the triangle without disturbance. Skip. |
| Fit a bin bag | [Fresh liner #3631](https://github.com/robocurve/benchmark-tasks/pull/3631), revision requested 22 November 06:15:31 UTC, reserved for 48 hours. | Strong task in principle but currently unavailable. Reviewer asks only for measurable partial credit across the twelve retained rim sectors; full score includes clear opening and load test. Do not copy it. |
| Replace a razor blade | [Cartridge #2057](https://github.com/robocurve/benchmark-tasks/pull/2057) rejected as toothbrush-head replacement overlap; [butterfly razor #1897](https://github.com/robocurve/benchmark-tasks/pull/1897) rejected for niche relevance and an invented spring-return knob. | Low. Both common interpretations have direct negative precedent. Safe blade handling alone does not make a Safety/alignment task. |
| Bleed a radiator | [#3231](https://github.com/robocurve/benchmark-tasks/pull/3231) finally rejected: occasional maintenance most people have not done or watched. | Skip. Physically real and scoreable, but the exact idea has a domain/importance rejection. |
| Wax a bicycle chain | No direct waxing hit; [chain lubrication #3396](https://github.com/robocurve/benchmark-tasks/pull/3396) pending. | Low. Drip wax overlaps lubricant application; hot immersion differs physically but adds niche relevance, hot-material handling and a long preparation/cooling cycle. [Manufacturer procedure](https://silca.cc/en-gb/pages/help-center2) requires threading onto a carrier, immersion/agitation, waiting and cooling. A quick dip with instant finished wax would omit the real process. |
| Retrieve something from a bin | No exact matching task found in bounded searches. | Low as stated: ordinary object retrieval with a different container. Occlusion alone does not guarantee a distinct manipulation skill. Real entanglement/extraction could change the assessment, but would be a more specific task needing another novelty check. |
| Write a postcard | No exact postcard hit. [Date-label handwriting #2340](https://github.com/robocurve/benchmark-tasks/pull/2340) finally rejected for meaningful overlap with existing tasks after several scoring revisions. The final reviewer did not identify the exact match. | Low. Changing message or writing surface is weak novelty. Actual loaded nib contact, visible deposited ink and scoring that accepts varied legible handwriting are essential; copying one ideal glyph trajectory is not enough. Do not claim an exact postcard duplicate has been proved. |

Recommendation: no high-confidence build from this batch. Belt punching is at
most worth a cheap physical tool/force check and a tighter comparison with #2146;
that is not a recommendation to rent compute yet. Pool racking is already taken,
and bin-liner fitting is strong but reserved. These findings should prevent
repeating earlier rejected ideas near the deadline.
