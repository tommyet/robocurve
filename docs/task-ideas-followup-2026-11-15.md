# Follow-up: wrapping, rocking, untangling and five new ideas

Implementation update, 16 November: the user selected bracelet fastening,
present wrapping, pram rocking, knot removal and wax-strip technique for
building and submission. Current results and PRs are in the
[five-task record](five-household-task-batch.md). The research below records
the earlier screening; it is not the current development status. Waxing is
scoped to applying, smoothing and peeling a strip on a practice form, without
a hair-removal claim.

Research only, 15 November 2026, with board/PR snapshots around 21:09 UTC. No GPU,
Dream inference, simulation, task build or upstream submission was performed.

Refreshed 2,172 upstream PR titles and 548 task-board records, searched
titles/instructions/context for close matches and read relevant review histories.
Also checked the previously saved 1,016-entry BEHAVIOR catalogue and primary
benchmark/research sources below. Raw board/PR snapshots are ignored under
`artifacts/idea-followup-2026-11-15/`. No match means none found in this search,
not a guarantee of novelty. All proposed simulation designs remain untested.

## User's later shortlist

**Help fasten a bracelet is explicitly saved for later** in the
[central idea list](task-ideas-2026-11-15.md#shortlisted-for-later).
Use a flexible, real-size bracelet and an actual working clasp on a wrist form.
No close bracelet-fastening task was found. Before implementation, check the
specific clasp against YAM finger access and against the then-current board.

## Wrap a present: a defensible difference

BEHAVIOR inclusion is a novelty concern, not a blanket ban on every activity
with the same name. The competition asks for a meaningfully different skill.
That distinction must be in the physical work and achieved outcome.

BEHAVIOR's [Christmas gift-box definition](https://behavior.stanford.edu/knowledgebase/tasks/make_a_christmas_gift_box-0.html)
requires a bell inside a box and paper `overlaid` on it. The paper asset is
listed as planned. Its [Overlaid state](https://behavior.stanford.edu/omnigibson/object_states.html)
checks covering geometry; it is not a test of tucked end folds or adhesive
closure. The published task has no tape object or taped-closure goal.
The planned asset does not, by itself, exempt us from novelty review.

The user's proposed task is stronger: **fold paper around a rectangular present,
hold the folds and secure them with tape so it stays wrapped after release.**
This involves managing a flexible sheet around three-dimensional corners,
maintaining overlapping folds while another hand places tape, and producing
a retained enclosure. That is a credible difference from paper covering a box.
No close Robocurve gift-wrapping entry was found in this search.

There is adjacent accepted work: [carton sealing #1893](https://github.com/robocurve/benchmark-tasks/pull/1893)
already tests closing flaps and applying tape. Our distinction must therefore
come from shaping the loose wrapping sheet around the object, not merely
adding tape. That accepted task uses contact-qualified tape cells and simplified
flap locking, so a full adhesive-material solver is not a prerequisite.

The economical scope would start with one box on a correctly sized, flat,
pre-cut sheet and accessible pre-cut tape strips. No cutting, bows or decorative
extras. Preserve bending, contact and the need to hold unsecured folds; tape
must bridge the intended layers and retain them. A disclosed reduced model
is reasonable if wrong placement and premature release can actually fail.
Do not animate predetermined folds or award closure merely for hand proximity.

Judge visible coverage, secured overlaps and end folds, and retention after
release and a simple lift/turn check. Partial credit can follow completed
closures, with damage or unwrapping invalidating the affected credit. Exact
tolerances should be chosen with the physical paper and box, not invented now.

Real robots have already performed [paper-and-tape wrapping](https://arxiv.org/abs/2411.08389),
so feasibility is credible in principle, but that does not establish feasibility
or cost in our simulator. **Recommendation: move this above pram rocking.**

## Rock a pram: possible, but the importance case remains uncertain

No close pram-rocking task was found. The best version would be: **keep a
full-size pram moving smoothly back and forth in a small floor area, then stop
and leave it stationary**, using a restrained weighted infant doll.

The actual skill should be controlling rolling inertia, caster drift and
reversals through the handle. Leave wheels and steering functional; a cart
constrained to a rail with a programmed rocking hinge would remove much of
that skill. Choose an actual pram geometry and mass accessible to the robot;
do not shrink it into a toy to fit the workstation. Natural stopping/parking
can be included if its controls are physically accessible, but attaching a
separate unrelated challenge just to make the task longer would be weak.

A marked floor and video can assess travel range, repeated smooth reversals,
sideways drift, wheel contact and the final stationary state. A defined motion
reference would be needed before specifying acceleration or timing limits;
do not present arbitrary limits as infant-safety or soothing thresholds.
The simulated result measures controlled motion, not a child's response.

There is real demand for this motion: the [Rockit manufacturer](https://rockitrocker.com/product/the-rockit-rocker-rechargeable-version/)
describes a device reproducing manual pram rocking. That establishes a familiar
use, not that robotic rocking meets Robocurve's capability bar. Accepted
[infant-manikin measurement #1318](https://github.com/robocurve/benchmark-tasks/pull/1318)
is a care-domain precedent, but involves different manipulation.
**Recommendation: keep as a backup; no strong acceptance claim yet.**

## Genuine knot removal

Yes: a real knot is a stronger manipulation task than simply lifting one cable
over another. Start with **one unplugged charging cable with intact connectors
and a reproducible loose overhand knot**. It should require opening a loop,
managing slack and passing an end through, then leaving the cable usable.
Do not begin with an arbitrary pile: it is hard to reset and may contain no
actual knot. A necklace is a later target because of its much smaller grasp
surfaces and more demanding chain-link contact.

[Uncross two cables #13](https://github.com/robocurve/benchmark-tasks/pull/13)
was finally rejected as too close to the cable-identification family.
The accepted revision of [#12](https://github.com/robocurve/benchmark-tasks/pull/12)
routes the correct plugs of cables hidden under a cover. Neither establishes
that genuine knot removal has already been accepted here. However, genuine
untangling is established robotics research: [SGTM](https://arxiv.org/abs/2207.07813)
evaluates overhand/figure-eight and more complex cable tangles, and
[this tactile-gripper benchmark](https://yuhao-zhou.com/5_dof_gripper/index.html)
also includes cable untangling. Do not claim the idea is new to robotics.
Our own accepted [overhand-knot task #1153](https://github.com/robocurve/benchmark-tasks/pull/1153)
is another relevant comparison: opening an existing knot and recovering a
usable cable must justify a distinct capability, rather than simply reversing
the tying demo. Novelty remains a review risk despite the lack of a direct match.

The simulator must allow changing the knot's topology through manipulation,
while self-contact prevents strands or connectors passing through each other.
A fixed-topology shortcut like the prepared necktie model is unsuitable.
Connectors must fit through a genuinely opened loop; removing a connector,
breaking the cable or cutting it cannot count. A coarse flexible cord model
may be enough if it preserves those constraints, friction and slack.

Judge the intact cable, absence of the specified knot, and usable extension
after release with a simple physical inspection. A low-force extension check
may support judging, but extension alone cannot prove absence of a small knot;
use visual inspection as well. A single-view crossing count is not adequate.
**Recommendation: retain as a technically demanding candidate, starting with
a cable rather than jewellery.**

## Five new ideas

| Idea | Findings | Decision and credible scope |
|---|---|---|
| Waxing a leg | No close Robocurve or checked BEHAVIOR task found. [Veet's instructions](https://www.veet.co.uk/blogs/tips/leg-hair-removal-with-veet/) identify skin tension and wax/hair adhesion as parts of the real process. [Protective-film peeling #769](https://github.com/robocurve/benchmark-tasks/pull/769) was rejected after replacing a continuously adhered film with intermittently taped paper strips. | Novel-looking but high modelling risk. The smallest credible version is one cold-wax strip on one patch, preserving skin support, flexible peeling and hair removal. A rigid leg with hairs disappearing when a strip moves would not establish waxing. Score actual removal and surface damage, not prescribed gestures. A physically reproducible surrogate is still unresolved; keep for research, not a cheap immediate build. |
| Set then place a mousetrap | [#1355](https://github.com/robocurve/benchmark-tasks/pull/1355) was finally rejected because it omitted arming/baiting and was ordinary placement. But [#1444](https://github.com/robocurve/benchmark-tasks/pull/1444), TK-T9Q5HL, now tests actually setting a spring rat trap and is pending. Pilot TK-TKFWP3 already moves a set mousetrap without triggering it. BEHAVIOR's [setting-mousetraps definition](https://behavior.stanford.edu/knowledgebase/tasks/setting_mousetraps-0.html) is placement-only. | Actual spring restraint and latch engagement would be a real capability; this is already held by the pending rat-trap task. Combining its arming skill with the pilot's transport skill is unlikely to be a sufficient distinction. Park this version. |
| Pack a suitcase | BEHAVIOR's [packing task](https://behavior.stanford.edu/knowledgebase/tasks/packing_bags_or_suitcase-0.html) places clothes/toiletries into a backpack. [RoboDojo](https://robodojo-benchmark.com/) includes packing objects into a backpack. [Compress and zip an overfull case #707](https://github.com/robocurve/benchmark-tasks/pull/707) was finally rejected for a separate slider/software lock replacing a functional zipper. | Generic packing is crowded. A distinct version would compress soft contents and align/join the loaded case edges with an actual zipper; it must not reduce to pulling a handle on a fixed track. That repair of #707's core failure is technically possible in principle, but flexible contents plus zipper interaction make it a reserve, not a quick cheap build. |
| Tattoo artist | No close tattoo submission found. [Skin-Screen](https://achapiro.github.io/pio23/pio23.pdf) demonstrates controlled tattoo deposition on synthetic practice substrates. [Drawing along a held ruler #755](https://github.com/robocurve/benchmark-tasks/pull/755) was rejected as duplicating straightedge marking. | Potentially distinct if narrowed to tattooing a small outlined shape on compliant practice skin over a curved form. Preserve skin support/tension, needle engagement and retained ink; score the cleaned mark, missing/excess ink and tearing or through-punctures. Drawing a texture on a rigid surface would lose the distinction. A real training substrate provides a reproducible physical target, but contact/deposition calibration and the specialist-activity importance case remain unresolved. Research reserve. |
| Cocktail shaking | [#520](https://github.com/robocurve/benchmark-tasks/pull/520) already seals, shakes and opens a Boston shaker; latest revision review was 15 November 09:31 UTC. It needs correction because the stated tins cannot form the claimed press fit. [Shaker opening #1956](https://github.com/robocurve/benchmark-tasks/pull/1956) also remains in revision, reviewed 15 November 01:59 UTC. Both are inside their 48-hour revision windows at this check. | Direct overlap; do not build. These are repairable submissions, not abandoned unclaimed ideas. Their reviews also show why an unsealed cap with beads, invented sealing geometry or shaking-count proxies alone cannot establish the claimed drink-making result. |

## Current recommendation

Keep **bracelet fastening** as the user-selected later task and **paper gift
wrapping** as the strongest additional candidate from this follow-up. Keep
genuine cable knot removal for a focused feasibility decision, with pram rocking
as a lower-confidence backup. Waxing, practice-skin tattooing and a functional
loaded-suitcase zipper need more groundwork. Trap setting and cocktail shaking
are too directly occupied to recommend now.

No candidate above is promised acceptance or a $3 development cost. Recheck
ownership and current feedback immediately before any authorized build.
