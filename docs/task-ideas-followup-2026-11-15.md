# Follow-up: wrapping, rocking, untangling and five new ideas

Latest research: [pages, paper planes, wire, eyelets and new opportunities](#17-november-pages-paper-planes-wire-eyelets-and-new-opportunities).
The earlier ribbon, hoop and garlic shortlist has since been submitted as
PRs #2459, #2456 and #2455; those receipts are not acceptances. Earlier
implementation status is historical; use current PR decisions for status.

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

## 16 November: digging and planting in a small pot

Research only, around 17:00 UTC; 641 current board records and targeted all-state
PR searches checked. No GPU, Dream, simulation or task build. **Generic seedling
planting is too occupied; actual excavation is a conditional candidate.**

| Existing task | Current evidence and implication |
|---|---|
| [Plant a seedling while holding it upright #680](https://github.com/robocurve/benchmark-tasks/pull/680) | Returned on 12 November: too little soil to backfill its hole, and clod counts did not ensure coverage around the plug. Its original hold has elapsed, but a newer task overlaps. |
| [Plant and firm a pepper seedling #2106](https://github.com/robocurve/benchmark-tasks/pull/2106) | Latest revision returned at 06:35 UTC on 16 November. The corrected height probes could still hit a shifted plug or miss its top. Its revision hold remains active until about 06:35 UTC on 18 November. Starts with a prepared hole; do not duplicate its placing/backfilling skill. |
| [Expose a buried pipe with a spade #1057](https://github.com/robocurve/benchmark-tasks/pull/1057) | Final rejection: a shallow layer of large wooden cubes did not preserve digging, and hand-sweeping bypassed the spade. |
| [Double-pot plants #854](https://github.com/robocurve/benchmark-tasks/pull/854), [plant strawberries #1048](https://github.com/robocurve/benchmark-tasks/pull/1048) | Final rejections for missing actual plants/soil/root insertion and replacing the work with placing cylinders. |

BEHAVIOR already defines [plants in pots](https://behavior.stanford.edu/knowledgebase/tasks/planting_plants-0.html)
and [seeds plus soil in a pot](https://behavior.stanford.edu/knowledgebase/tasks/planting_vegetables-0.html).
Those published goals do not require digging an initial hole, controlling its
depth or a specified burial orientation. This leaves a possible capability
distinction, not an exemption from novelty review.

The strongest narrow version is **dig a hole with a hand trowel, plant one
dormant bulb at the required depth with its shoot end upwards, and backfill**.
Start with an ordinary filled pot or small planter, not a pre-made socket.
Use actual horticultural scale; a small pot is legitimate, a miniature farm is
not the intended context. The [RHS bulb guide](https://www.rhs.org.uk/plants/types/bulbs/planting)
supports this sequence and notes that dormant bulbs are normally planted
without foliage or roots. This avoids inventing a need for complex growing
plants, watering or growth simulation. Select a species and its planting depth
before defining numeric targets.

The distinct skill would be penetrating the substrate, levering/scooping
material out and managing a hole that can slump, then replacing soil around
the bulb. A disclosed granular approximation might suffice if it preserves
these interactions and meaningful failures; large loose blocks, deleted soil
or animated excavation would not. Species substitution alone adds no novelty.

Keep scoring physical: hole/depth and bulb orientation visible before covering,
final soil cover and spill, using recorded views and a ruler. A reliable final
burial-depth check remains to be designed; do not infer it from particle counts
or uncalibrated soil mass. PR2106 also shows why measurement must remain valid
when the object moves. **Retain as a research reserve, probably Societal
relatability, not a high-confidence quick submission or promised $3 build.**

## 16 November: squeeze ketchup onto a burger

Research only, around 17:25 UTC. Targeted all-state PR searches for ketchup,
condiments, mustard, mayonnaise, sauce, burger, squeezing and dispensing, plus
the same-day 641-record board snapshot, found no exact ketchup-on-burger task.
No GPU, Dream, simulation or task implementation. **Highly relatable and
plausible, but only a conditional shortlist candidate because of overlap.**

Our pending [cake piping #1919](https://github.com/robocurve/benchmark-tasks/pull/1919)
already requires pressure-controlled viscous extrusion, stopping flow and a
clean surrounding surface. [Glue dispensing #2283](https://github.com/robocurve/benchmark-tasks/pull/2283)
is also waiting for review. A burger instead of a cake, or red material instead
of icing, is not a sufficient capability distinction. Controlled dosing may
give the ketchup version a different emphasis, but does not establish novelty
by itself. Do not claim it is clearly distinct without revisiting these tasks.

BEHAVIOR's [grill-burgers definition](https://behavior.stanford.edu/knowledgebase/tasks/grill_burgers-0.html)
requires cooking patties and putting them on buns, not dispensing ketchup.
Its [sandwich task](https://behavior.stanford.edu/knowledgebase/tasks/make_a_sandwich-0.html)
already includes coating bread with peanut butter and jelly. These comparisons
support a narrow possible distinction, not a claim that food coating is new.

The simplest credible scope is: **add a specified portion of ketchup to the
exposed burger, keep it on the food, then stop dispensing and put the bottle
down.** Start with an open, filled squeeze bottle and an accessible burger;
cap opening, cooking and decorative zigzags add little to this proposal.
The useful skill is orienting and compressing a compliant bottle while
regulating the deposited amount and ending the flow cleanly.

Preserve a finite reservoir, squeeze- and orientation-dependent flow, visible
deposition and meaningful underdosing, overdosing and spilling. A simplified
material model may suffice; dispensing cannot be a target-aware animation.
Score amount on the burger with a scale, plus placement/spill from photos
and a separate spill collector. Specify the physical measurement arrangement
and numeric tolerances before building; bottle mass loss alone also counts
spilled material. Do not require an arbitrary arm path or particular pattern.

[Instrumentation for Better Demonstrations](https://arxiv.org/abs/2504.18481)
demonstrates robotic squeeze-bottle flow control with xanthan-thickened water
on different hardware. This is evidence that the real manipulation is
credible, not proof of our simulator or actual ketchup behaviour. Reusing
parts of the cake model might reduce effort, but neither acceptance nor a
$3 build is established. **Keep for comparison with stronger novel ideas;
do not build automatically.**

## 16 November: broad creative shortlist

**First investigate the split key ring and embroidery hoop.** Freeing a trapped
zip is the next strongest everyday problem, with greater simulation risk.
The seven ideas below have credible acceptance cases, not promised acceptance.
All remain research proposals; no GPU, Dream, simulation or task implementation
was used. The user's previous approximately $3-per-task preference is not a
validated cost estimate for any of these.

### Coverage and what the reviews show

Downloaded all **2,341 upstream PR metadata records through #2342**, and an
authenticated **647-record task board** on 16 November. Screened titles and
board instructions/context for broad manipulation families and candidate
synonyms, searched relevant PR bodies, and read twelve close review histories.
This does not mean every submission's video or code was audited. The board
contains 180 accepted, 340 pending, 37 rejected/returned and 90 pilot records;
many historical rejections only appear in GitHub. Those counts are not a
submission acceptance rate. Evidence: ignored
`artifacts/creative-ideation-2026-11-16/`.

The 1,016-entry BEHAVIOR task-name index and current
[RoboDojo simulation](https://robodojo-benchmark.com/doc/sim-tasks/) and
[real-task](https://robodojo-benchmark.com/doc/real-tasks/) catalogues did not
reveal an exact match for the seven scopes. Other benchmark overviews were
consulted, but this is not an exhaustive world-literature or implementation
audit. A missing keyword match is not novelty clearance. Recheck ownership
and the closest task's actual start/goal immediately before building.

- [Ice-tray twisting #1436](https://github.com/robocurve/benchmark-tasks/pull/1436)
  was accepted with two sprung rigid halves and twist-dependent cube release.
  [Cucumber peeling #1899](https://github.com/robocurve/benchmark-tasks/pull/1899)
  uses contact-dependent skin patches without peel ribbons. A complete
  continuum-material solver is not a universal requirement.
- [O-ring fitting #1576](https://github.com/robocurve/benchmark-tasks/pull/1576)
  was accepted after its score rewarded useful progress and the final seal,
  removing arm-home rewards and irrelevant release-angle penalties. Its
  limited ring model is explicitly disclosed. Treat that as a precedent for
  preserving the task with a reduced model, not permission to script success.
- [Circlip fitting #1561](https://github.com/robocurve/benchmark-tasks/pull/1561)
  had to remove an unrealistic fixed fixture and preserve the need to steady
  the loose assembly. Convenient fixation can remove the task's difficulty.
- [Enlarged zipper #1513](https://github.com/robocurve/benchmark-tasks/pull/1513),
  [oversized floss model #1341](https://github.com/robocurve/benchmark-tasks/pull/1341)
  and [our waxing #2192](https://github.com/robocurve/benchmark-tasks/pull/2192)
  failed when the simplification removed essential scale, contact or material
  interaction. Honest wording alone did not repair that.

These ideas fit **Societal relatability** most naturally. Do not add an
unsupported jobs-impact claim to make an ordinary household skill sound larger.
Scoring below is a proposed physical approach; numerical thresholds must be
chosen against the selected real objects before submission.

### 1. Put a house key onto a split key ring

**Task:** Put the loose key onto the split ring and leave the ring closed.
Use a real key, a normal-size double-coil ring and a commercially available
ring-opening tool. Separate the overlapping coils, start the key's hole over
the exposed end, then advance it around the coil until it is fully captured.

The proposed distinction is maintaining an opening while threading a closed
hole around a spring coil. It differs from the accepted circlip, which expands
over a shaft and seats in a groove, and from [hanging key rings #2213](https://github.com/robocurve/benchmark-tasks/pull/2213).
[Rapala's split-ring pliers](https://www.rapala.com/us_en/mini-split-ring-pliers)
provide a real one-handed tool precedent, not proof that a particular model
fits a house-key ring or YAM fingers; choose compatible hardware first.

**Judge:** key fully past the split and retained after both hands/tools release;
ring returns closed and is not permanently bent. A photograph plus a small,
specified retention pull suffices. Give partial credit for an intact key
advanced onto the coil, not merely touching it. Opening force, helical contact
and gripper access are the feasibility questions. No automatic attachment or
enlarged ring gap. **Top priority; moderate expected development risk.**

### 2. Mount fabric taut in an embroidery hoop

**Task:** Secure the marked area of this cloth in the hoop, smooth and taut.
Start with loose woven cloth and the two rings of a real screw-adjusted hoop.
Align the cloth, seat the rings and adjust tension so the material remains
usable after release. No stitching is needed. A
[Prym beechwood hoop](https://de.handicraft.com/en/products/stickrahmen-buchenholz)
is a concrete reference; [Singer's hooping instructions](https://www.singer.com.tr/assets/img/uploads/product-files/3020e8588727712d5e346657212221aa_en.pdf)
describe mounting and securing fabric tension.

This tests distributed tension retained by frictional clamping, distinct from
folding clothing, pegging a shirt or ordinary rigid assembly. The cloth must
stay deformable and able to slip or wrinkle; a flat sheet that becomes fixed
when the rings approach would remove the skill.

**Judge:** the marked region is inside the usable opening, the cloth is intact,
and it stays clamped with limited deflection under a specified small weight.
Use a photo, ruler and weight; keep the cloth's weave undistorted. Partial credit
for seated/retained cloth before reaching usable tension. Define reproducible
material, loading point and tolerances. **Top priority; moderate risk from
cloth/hoop friction, with a relatively compact setup.**

### 3. Free lining caught in a zip

**Task:** Free the lining trapped in this zip and leave the zip working.
Start with a reproducible snag in an ordinary flexible garment or pouch.
Coordinate slider reversal with easing the caught material out. Confirm the
slider can then pass the snag location without catching again.

[YKK's instructions](https://ykkamericas.com/wp-content/uploads/2021/10/fastening-catalog-compressed-1.pdf)
describe moving the slider gently while extracting caught fabric. Pending
[PR2109](https://github.com/robocurve/benchmark-tasks/pull/2109) closes an already
started baby-jacket zip; it does not start with a physical cloth jam. That is
the proposed distinction, though related-task novelty still needs review.

**Judge:** lining freed and intact, zipper functional across the affected
section, no broken pull/teeth. Partial credit for freeing the fabric before
the function check. The jam must arise from cloth trapped in slider geometry;
a hidden lock released by a gesture is inadequate. Use a real-size pull or
documented real attachment: PR2109's review specifically challenged an
oversized simulated grasp block. **Strong relatable idea; higher development
risk than the first two because contact creates the snag.**

### 4. Remove a seatbelt twist through its sliding tongue

**Task:** Remove the twist in this seatbelt and leave the webbing running flat.
The relevant operation is passing a folded section of webbing through the
sliding latch plate to reverse its orientation, with the belt anchors still
attached. This is a documented
[Mopar owner-manual procedure](https://vehicleinfo.mopar.com/assets/publications/en-us/Ram/2022/2500_3500/om_html/GUID-C4A92A2D-CDC9-4902-8069-20F4A16FC582.html).

Pending [retractor tests #1866](https://github.com/robocurve/benchmark-tasks/pull/1866)
and [#2164](https://github.com/robocurve/benchmark-tasks/pull/2164) test acceleration
locking, not passage of folded webbing through a narrow slot. The rejected
[child-harness fitting #861](https://github.com/robocurve/benchmark-tasks/pull/861)
is adjacent and warns against miniature geometry and inaccessible mesh scores.

**Judge:** visible flat, untwisted webbing on both sides of the plate, intact
anchors/webbing, and free sliding over a stated test distance after release.
A contrasting edge marker can make twist visible without changing the task.
The actual slot must constrain a flexible strip that bends and folds, not a
round rope. This is a bench manipulation task, not a crash-safety certification.
**Good reserve; moderate-to-high risk from folded-webbing contact.**

### 5. Rethread a hoodie drawstring

**Task:** Put the drawstring back through the hood and leave both ends out.
Use a real hoodie and blunt drawstring threader/bodkin. Attaching the cord to
the tool can be a disclosed prepared step; the work is guiding the hidden tool
through the flexible casing, gathering and releasing fabric without losing
the trailing end. [Dritz's real tool](https://prymamericas.com/collections/sewing-notions/products/706)
is designed for this operation.

[Lamp-cord threading #2273](https://github.com/robocurve/benchmark-tasks/pull/2273)
is adjacent but uses a rigid pipe. The cloth casing's bunching and redistribution
must create the distinction; replacing it with a rigid channel would collapse
that case. Drawstring-bin closure #2134 does not install a missing cord.

**Judge:** the cord follows the existing casing, both ends extend by specified
usable lengths, and a gentle pull cinches/releases the hood without new holes
or detached seams. Partial credit for intact passage emerging at the outlet
before adjusting the tails. Use photos and a simple pull test, not inferred
path length through hidden meshes. **Strong everyday relevance; higher risk
from enclosed flexible contact and reset reproducibility.**

### 6. Patch one puncture in a bicycle inner tube

**Task:** Patch the marked puncture so the inner tube no longer leaks.
Start with the tube out of the tyre and a known puncture; omit wheel removal.
Use the selected patch system's real preparation and application steps. A
[pre-glued patch](https://www.parktool.com/assets/doc/product/GP-2_instructions.pdf)
avoids modelling glue chemistry, but still requires clean/dry rubber, light
abrasion and firm contact. Park Tool describes that product as an emergency
repair; do not claim a permanent restored tube.

The useful result is an airtight bond on compliant curved rubber, distinct
from placing a sticker. [Tyre-bead mounting #1690](https://github.com/robocurve/benchmark-tasks/pull/1690)
is occupied and is not part of this proposal. That review also demonstrates
that a proposed force check is not evidence of an actually measured capability.

**Judge:** the patch covers the puncture and survives a defined leak/pressure
check after release. Partial credit for a securely applied patch before a
passing seal test. Pressure loss/bubbles should agree with the physical
check; patch-centre alignment alone cannot imply sealing. The tube must be
supported appropriately during any physical inflation check, with a selected
manufacturer-compatible procedure. **Appealing repair, but higher risk: the
model must preserve poor adhesion, wrinkles and leakage.**

### 7. Fold a pop-up car sunshade into its pouch

**Task:** Fold the spring-framed sunshade and put it in its storage pouch.
Coordinate both hands to twist the frame into overlapping loops, keep it
compressed, and retain the bundle. This is the familiar awkward operation
described in [Tesla's folding instructions](https://www.tesla.com/sites/default/files/pdfs/modelx_sunshade_installation.pdf).
Select a commercially available size within YAM reach, not a scaled-down
version of a large shade. The cited manual establishes the operation, not
the dimensions or forces of a chosen build.

No close submission was found. It is distinct from opening an umbrella or
folding hinged furniture because the continuous elastic frame changes shape
and can spring back. **Judge:** intact shade fully retained in the specified
pouch after release; the frame still unfolds to its original usable shape.
Partial credit can cover a compact held bundle before retention. A fold
animation or preset hinged mechanism would not demonstrate the claimed skill.
**Most visually distinctive reserve; high risk from elastic buckling and
self-contact. Not the first choice for a small development budget.**

### Ideas deliberately left out

- **Tune an instrument:** [PR794](https://github.com/robocurve/benchmark-tasks/pull/794)
  already proposed plucking a string and adjusting its key using a tuner.
  It is closed/unmerged; the visible comments show daily-limit failures and no
  review decision. It may be unclaimed, but is not a newly discovered idea,
  and there is no acceptance feedback to rely on. Do not call it rejected.
- **Change a hacksaw blade:** [PR1472](https://github.com/robocurve/benchmark-tasks/pull/1472)
  failed its stated importance case and excluded valid wing-nut techniques.
  Not a strong new recommendation merely by changing the tool to a coping saw.
- **Push a tablet out of a blister:** [PR725](https://github.com/robocurve/benchmark-tasks/pull/725)
  was judged a single press with a non-robotic calendar challenge. Avoid adding
  reading or counting to manufacture difficulty.
- **Floss teeth:** [PR1341](https://github.com/robocurve/benchmark-tasks/pull/1341)
  and its appeal failed for oversized block teeth and missing real contours.
  Real-scale floss contact is too uncertain for the economical shortlist.
- **Load/draw up a sewing-machine bobbin:** no direct match found and
  [Singer documents the operation](https://euhelp.singer.com/en-US/singer-machine-faqs-594705),
  but the fine thread's actual capture/routing is central. A magical loop
  appearing after turning the handwheel would repeat the fidelity failure.
  Keep as a longer-term research idea rather than adding it to this build queue.
- **Ketchup, generic wiping, another vegetable-peeling task, another basic
  screw/plug task:** existing dispensing, cleaning, peeling and insertion
  coverage makes these weaker novelty bets. Gardening remains the earlier
  excavation research reserve, not a quick substitute for occupied planting.

**Recommended next selection: split ring, embroidery hoop, then trapped zip.**
First verify accessible real geometry and whether the minimum model can fail
in the same meaningful ways as the real task. Only after the user selects
tasks should any paid trial or implementation start. Keep the task small;
score the useful final result, include partial credit and treat later damage
as failure. Do not add prescribed paths or cosmetic precision for difficulty.

## 16 November: broken plate, pancake, nail, paper aeroplane and medicine spoon

Research only. Refreshed the board (661 records), searched current PRs in all
states and read relevant review comments. Also screened the same-day complete
PR title index, saved BEHAVIOR task names and current RoboDojo catalogues.
Absence from these searches is not novelty clearance. Feasibility and acceptance
ratings below are judgments, not measured success rates; no simulations run.

| Idea | Evidence and novelty | Minimum credible model; recommendation |
| --- | --- | --- |
| Superglue a broken plate | No exact plate repair found, but pending [mug repair #2283](https://github.com/robocurve/benchmark-tasks/pull/2283) already applies glue, aligns fracture surfaces and presses them together. Earlier [#1610](https://github.com/robocurve/benchmark-tasks/pull/1610) needs revision for glue application and bond realism. | Technically plausible with two rigid ceramic fragments and a disclosed contact/coverage/hold-time bond model. Require actual dispensing, contacting fracture faces, product-appropriate hold time and retained attachment; no proximity-triggered snap. A different ceramic object alone adds little. **Low acceptance prospect as stated; park.** More fragments add cost without guaranteeing a distinct skill. |
| Flip a pancake | [#1435](https://github.com/robocurve/benchmark-tasks/pull/1435) was finally rejected explicitly as a duplicate of earlier steak flipping. Egg flipping TK-84YE4P is already a board pilot. Utensil-free pan tossing is also proposed in pending [#2310](https://github.com/robocurve/benchmark-tasks/pull/2310). | A spatula/contact model is feasible; a pan toss needs inertial launch, rotation and catching. Gripper-turning must not bypass tool use. **Very low for a spatula flip; low for a pan toss given current overlap. Skip.** |
| Knock in a nail | Pending [#2206](https://github.com/robocurve/benchmark-tasks/pull/2206) starts a loose nail with one hand while the other taps, then drives it home. Earlier [#142](https://github.com/robocurve/benchmark-tasks/pull/142) failed novelty against [DexJoCo Hammer Nail](https://github.com/brave-eai/dexjoco/blob/main/configs/multi_task/hammer_nail.yaml). | Straightforward reduced impact/resistance model in principle, but slow pressing must not substitute for impacts and unsupported nails must fall. **Very low novelty/acceptance prospect. Skip.** |
| Make a paper aeroplane | No direct Robocurve match found. However the [IROS 2026 Robotic Origami Challenge](https://robotic-origami-challenge.github.io/) already benchmarks a six-fold plane, and [PaperBot](https://paperbot.cs.columbia.edu/) folds and throws planes on real robots. Our gift-wrap [#2197](https://github.com/robocurve/benchmark-tasks/pull/2197) is pending and tests pre-creased wrapping/taping, not forming a plane from an uncreased sheet. | Needs thin-sheet manipulation, forming and pressing lasting creases, and layered self-contact. Rigid panels with preinstalled hinges omit crease creation; a pre-creased version must be named honestly and has a weaker capability claim. Score measured alignment/symmetry and retained structure after release; flight would add aerodynamic validation and is unnecessary for a folding-only task. **Low-to-moderate, uncertain; substantial modelling cost. Research reserve, not an inexpensive build.** |
| Administer medicine via a spoon | No exact match found, but [spoon feeding #713](https://github.com/robocurve/benchmark-tasks/pull/713) was finally rejected for a rectangular mouth pit, glass beads and no unsafe face-contact penalty. [Dosing #355](https://github.com/robocurve/benchmark-tasks/pull/355) failed for an unrecognizable solid dosing cup. Accepted [eye-drop #1981](https://github.com/robocurve/benchmark-tasks/pull/1981) shows a care-training manikin can be valid. | Conditional scope: deliver a specified quantity of inert test liquid with a proper medicine spoon to a representative training mouth, with measurable delivered volume, spillage and safe interface contact. Model contact and fluid transfer rather than teleporting liquid or deleting beads; do not claim to validate swallowing. A narrow physical delivery task is more defensible than complete clinical administration. **Low-to-moderate if built credibly; low for a cheap simplified version. Research reserve.** |

A proper medicine spoon is a legitimate device; this is distinct from a kitchen
teaspoon used as a measuring tool. [NHS England](https://www.england.nhs.uk/patient-safety/patient-safety-insight/patient-safety-alerts/enduring-standards/standards-that-remain-valid/medication-safety/)
allows a medicine spoon or graduated measure where appropriate. This does not
establish that a particular robot delivery protocol is clinically safe.

None is an obvious next inexpensive submission. Plate, pancake and nail have
strong overlap. Paper folding and spoon delivery retain interesting skills but
need material/interface work and a stronger novelty case before paid testing.


## 17 November: shortlist against live review prompt v24

Research only; no GPU, Dream, new task build or submission. Checked the live
622-record board, targeted all-state PR title/body searches, the saved
1,016-entry BEHAVIOR name index, current RoboDojo catalogues and primary
research sources. Evidence is ignored under
`artifacts/medicine-revision-2026-11-17/`. These are candidates, not novelty
clearance or demonstrated feasibility. Recheck ownership immediately before a build.

The current [review prompt](https://tasks.robocurve.org/review-prompt) permits
explained material-response rules if the robot still performs the physical
work. A successful-looking animation, proximity trigger or helper that does
that work is insufficient. Prioritize a recognizable physical outcome and
simple judging, with one clear difficulty per task.

### Recommended candidates, in order for small feasibility trials

| Activity | Minimal useful task and judging | Distinction and main risk |
| --- | --- | --- |
| Curl gift ribbon | Hold ordinary curling ribbon under tension and draw it across a real curling edge, then release an intact, visibly curled length. Score retained coils/curled length with a photo and ruler; no reward for a prescribed number of strokes. | Permanent bending under controlled tension and edge contact, distinct from our gift's paper enclosure/tape closure. No direct board/PR match found. The response rule must depend on actual loaded sliding contact; curling cannot be an animation triggered by a waypoint. Familiar result, compact setup; promising first trial. |
| Mount fabric taut in an embroidery hoop | Start with loose woven fabric and both rings of an ordinary screw hoop. Seat the fabric, distribute tension and secure it. Score intact, retained fabric and deflection under a small specified weight, using a ruler/photo. | Distributed tension and frictional retention, different from the shirt's discrete spring pegs or folding. No direct board/PR match found. The fabric must wrinkle and slip under poor handling. Main review risk is whether hoop preparation is familiar enough under Societal relatability; do not invent a large jobs-impact claim. |
| Peel a garlic clove with a silicone rolling peeler | Load a normal unpeeled clove, compress and roll the flexible tube, then recover the intact peeled clove. Score visible skin removal and retained flesh; use a photo and scale where needed. | Friction inside a deformable tool removes papery skin, unlike accepted cucumber blade-peeling #1899. No direct board/PR match found. Skin detachment must result from contact/shear, with incomplete peeling and crushing able to fail. Specify a consistent garlic size/type/condition and protect the rig. No cutting knife or invented peeling gadget needed. |

These are relative priorities, not probabilities or a guaranteed $3 budget.
Material/contact feasibility remains untested. All fit Societal relatability
more naturally than a broad employment-number justification.

Primary references:

- [PNAS ribbon-curling experiments and model](https://pmc.ncbi.nlm.nih.gov/articles/PMC4763768/)
  establish the real edge/tension mechanism and show that the response is not
  simply proportional to pulling harder. They do not validate our simulator.
- [Prym's ordinary beechwood hoop](https://de.handicraft.com/en/products/stickrahmen-buchenholz)
  uses an adjustment screw to retain fabric tension. A robotics product demo of
  hooping exists; no matching open evaluation task was found in this search, so
  do not claim hooping has never been demonstrated by a robot.
- [OXO's silicone garlic peeler](https://www.oxo.com/garlic-peeler.html)
  specifies downward pressure and rolling on the counter, with detached skin
  retained in the tool. This is a real existing method, not a simulation aid.
- BEHAVIOR's [garlic mushrooms](https://behavior.stanford.edu/knowledgebase/tasks/make_garlic_mushrooms-0.html)
  and [garlic prawns](https://behavior.stanford.edu/knowledgebase/tasks/make_king_prawns_with_garlic-0.html)
  definitions were read in full: their garlic goals concern dicing/cooking,
  with no papery-skin removal condition. This supports a distinction from those
  two recipes; it is not an exhaustive novelty guarantee.
- [RoboDojo task catalogue](https://robodojo-benchmark.com/doc/sim-tasks/)
  contains adjacent folding and pouring, not a direct match for these scopes.

### Screened out or deferred

- **Split key ring:** now occupied by [#2426](https://github.com/robocurve/benchmark-tasks/pull/2426),
  board TK-L3WWW2 pending. This supersedes our earlier recommendation.
- **Pencil sharpening:** [#1845](https://github.com/robocurve/benchmark-tasks/pull/1845)
  already exists; not a fresh candidate.
- **Towel wringing:** explicitly present in the [T-DOM dataset](https://sites.google.com/view/t-dom).
- **Turn clothing right-side out:** [Right-Side-Out](https://right-side-out.github.io/)
  already evaluates garment reversal. A sleeve-only variant still has substantial
  overlap and difficult self-contact; do not recommend it as a low-risk novelty.
- **Thread a needle:** directly covered by the
  [IROS forceps challenge](https://medcvr.github.io/Forceps-Manipulation-Challenge/)
  and multiple published robotic needle-threading evaluations.
- **Plunge a sink:** [#2092](https://github.com/robocurve/benchmark-tasks/pull/2092)
  and [#1251](https://github.com/robocurve/benchmark-tasks/pull/1251) already exist.
- **Roll sushi:** [#1331](https://github.com/robocurve/benchmark-tasks/pull/1331)
  already covers bamboo-mat maki rolling.
- **Separate a yolk / peel a boiled egg / sew on a button:** no direct competition
  match found in targeted searches, but these need substantially more material,
  membrane or fine-thread work. Keep as research reserves; they are not the
  economical next recommendations. A text-to-video yolk-separation benchmark is
  not itself evidence of an equivalent robot manipulation benchmark.

## 17 November: flour, screen protector and catching

Research only; no paid compute, implementation or submission. Refreshed the
626-record board and live review prompt (still v24), searched PRs in all states,
read relevant decisions/revision receipts and checked primary benchmark sources.
Evidence: `artifacts/flour-screen-catch-2026-11-17/` (ignored).
Ratings are judgments about the proposed scopes, not acceptance probabilities.

| Idea | Current overlap | Viability and recommendation |
| --- | --- | --- |
| Measure out flour | Accepted [powdered-formula #1668](https://github.com/robocurve/benchmark-tasks/pull/1668) already requires scooping, leveling and transferring powder. Accepted [analytical-balance #621](https://github.com/robocurve/benchmark-tasks/pull/621) doses loose material to a scale reading. Both are confirmed merged and accepted on the board. | Plausible with a disclosed bulk-powder model preserving scoop loading, leveling, tilt-dependent flow, spills and retained mass. A kitchen scale makes judging straightforward. Weighing flour or leveling a flour cup mainly changes the ingredient/container; neither establishes a new ability. **Low acceptance prospect; do not prioritize.** No need for individual flour-grain simulation, but proximity-triggered filling would remove the skill. |
| Apply an iPhone screen protector | [#2162](https://github.com/robocurve/benchmark-tasks/pull/2162) already uses an iPhone 16 and a Spigen glass protector/alignment tray. Revision **TK-68HCRS** received 16 November 22:43 UTC is pending; its original review only requested practical adhesion judging and clarification of kit steps. | Tray installation is plausible and directly occupied. Freehand installation of flexible film would add handling and progressive adhesion, but removing a tray does not by itself establish novelty. A credible version needs misalignment, poor adhesion/bubbles and premature sticking to remain possible, judged with an ordinary photo/inspection. **Very low as stated; park.** Do not copy the superseded 0.3 mm real-world corner-lift criterion: reviewers explicitly rejected it as impractical. |
| Catch an object | [Ramp-ball #1213](https://github.com/robocurve/benchmark-tasks/pull/1213#issuecomment-6819080096) was finally rejected because the demo prepositioned a basket before a predictable release. [Tunnel-part #1033](https://github.com/robocurve/benchmark-tasks/pull/1033#issuecomment-6817312640) merely unloaded a stopped carrier and did not enforce the claimed emergence condition. [Bi-DexHands](https://github.com/PKU-MARL/DexterousHands#tasks) already includes underarm/abreast airborne throwing-and-catching tasks; [RoboDyna](https://robodyna.github.io/robodyna/) includes Catch Ramp Ball, Catch Valley Ball and further interception scenes. | Rigid-body flight/contact is tractable in principle; achieving a real moving catch and reliable retention is the harder controller problem. A proper scope would require interception after release, retained possession, and no table/ground rescue or magnetic attachment. Use video and retained catches to judge it; check robot reach/speed and real control timing before claiming feasibility. **Low for a generic catch, uncertain for a materially different practical skill.** Changing the object, throw speed, or number of catches alone does not establish novelty. |

**Decision:** none is currently a strong low-cost submission candidate. Catching
is interesting robotics, but that is separate from competition novelty. Keep
all three out of the paid build queue unless a substantially different ability
and credible real setup are identified. A task's absence from exact-title
searches is not clearance, and pilot board ideas are leads, not accepted tasks.

## 17 November: pages, paper planes, wire, eyelets and new opportunities

Research only: refreshed 639 task-board records, all 2,463 upstream PR titles
and states, relevant public review comments, and the live review prompt (v24).
Checked the saved 1,016-entry BEHAVIOR catalogue, relevant live definitions,
primary robotics research and product instructions. No simulation, paid GPU,
Dream call, task implementation or upstream change. Private evidence is under
`artifacts/ideation-2026-11-17-pages-plane-wire-eyelet/`.

These ratings are comparative judgments, not calibrated probabilities. They
assume a reproducible setup, honest contact-driven model, full-score demo and
practical scoring. No match found is a limited search result, not clearance.

### Four proposed ideas

| Idea | Evidence and viability | Acceptance outlook |
| --- | --- | --- |
| Turn pages in a book | [#2222](https://github.com/robocurve/benchmark-tasks/pull/2222#issuecomment-6930309035) was finally rejected: overlap with dexhand Book Page Turn, rigid 1.8 mm leaf, reinforced grasp tab, and mismatched scoring. [T-Rex](https://tactile-reactive-dexterous.github.io/) also evaluates actual page flipping. Thin-page separation from a stack is more faithful but difficult with YAM fingers; no tabs, rigid leaves or automatic page selection. | **Low.** Turning several pages or requesting a page number alone does not resolve the underlying overlap. A real single-sheet separation task would still face established evaluation work. Park. |
| Paper aeroplane with pre-folds | Our uncreased draft was never submitted: the centre fold failed locally, with excessive stretch. Pre-creases may reduce that difficulty but have not been tested. No direct competition PR found; the [IROS 2026 Origami Challenge](https://robotic-origami-challenge.github.io/) already benchmarks a six-fold paper plane. | **Low.** Ordinary pre-creases are not categorically forbidden, but a fully prepared hinge network removes crease creation and weakens the novelty claim. A single centre crease preserves more work than pre-folding all wings/nose, yet remains close to an existing task. Do not resume solely because implementation would become easier. The user's current permission to consider pre-folds supersedes the earlier strict-uncreased preference for this research. |
| Bend wire into a paperclip | No direct paperclip-manufacturing PR found. Accepted [tube bending #991](https://github.com/robocurve/benchmark-tasks/pull/991) already tests permanent bending and springback. [Cotter-pin #994](https://github.com/robocurve/benchmark-tasks/pull/994#issuecomment-6819957596) was returned for physically implausible steel bending resistance. Ordinary wire, real pliers and repeated supported bends are plausible in principle; soft craft wire need not make a useful spring clip. | **Low.** Familiar paperclips do not make hand-manufacturing them an everyday activity. A shape trace alone is insufficient: the result must grip and retain paper after release. Tool leverage, yielding and springback need credible forces. Weak importance case, plus overlap with existing bending and our ribbon task. |
| Put an eyelet in a curtain | No direct curtain-eyelet PR found. [Prym's click eyelets](https://www.prym.com/it/occhielli-per-tende-click-in-diversi-colori) are two plastic parts fitted around a cut hole; [metal eyelets](https://www.prym.com/en/happiness-is-handmade/non-sew-range) use a setting tool. These are materially different tasks. | **Low for a pre-cut snap-in eyelet; conditional for setting a metal eyelet.** The former risks being another covered snap-fit. The latter preserves loose-fabric alignment and permanent crimping, but tool force/access and specialist-work importance are unresolved. [Hand rivet #1468](https://github.com/robocurve/benchmark-tasks/pull/1468#issuecomment-6929581215) was finally rejected partly because its specific work did not establish the jobs threshold. Do not claim all sewing/maintenance workers do curtain eyelets. |

The current [review prompt](https://tasks.robocurve.org/review-prompt) allows
material-response rules when actual grasp, contact, motion and approximate
force do the work. It rejects preparations that remove the defining difficulty.
Judging an accepted simplification from an older task does not establish a
blanket exemption under the current prompt.

### New shortlist, ranked for further investigation

No direct title/instruction match was found for these five scopes in the fresh
board/PR search. Their distinctions below must survive implementation; several
have neighbouring abilities already covered. These are proposals, not validated
tasks or guaranteed low-cost builds.

1. **Strip the leafy part from a kale stalk and collect it for cooking.**
   Hold the stalk and strip the leaf using an opposing pinch/pull, leaving the
   tough stalk out of the bowl. Selective separation along a flexible stem is
   different from blade peeling or cutting off a branch. Score recovered edible
   leaf and residual leaf on the stalk, with stem contamination reducing credit;
   use photos and a kitchen scale, not prescribed stroke counts. A coarse leaf
   with contact/load-driven tearing could suffice, but leaves must not disappear
   on proximity. Specify cultivar, size, freshness and reset. **Promising,
   moderate modelling risk.** [OXO's recipe](https://www.oxo.com/blog/cooking-and-baking/back-pocket-recipe-chicken-caesar-salad-from-oxo-engineer-mack)
   documents the actual preparation. BEHAVIOR's [cook_kale](https://behavior.stanford.edu/knowledgebase/tasks/cook_kale-0.html)
   definition does not require removing a stalk; the distinction is the physical
   separation, not the ingredient. Use societal relatability unless a specific
   jobs claim can be supported.

2. **Secure a loose trouser hem with a safety pin.**
   Fold the loose section to the existing hemline, pass an ordinary safety pin
   through the intended fabric layers and close it with its point protected.
   The distinct work is controlling two limp layers while puncturing and
   capturing the sprung point, rather than clipping a rigid part. Score hem
   retention and alignment, captured layers and the safely enclosed point;
   reject tearing beyond intended punctures. A photo and gentle specified pull
   test suffice in principle. **Promising, moderate-to-high implementation risk:**
   fine tool access and two-arm grasp changes must be checked. No pre-punched
   holes or enlarged artificial handles. The failure of our seam-unpicking task
   is a reminder to demonstrate the actual everyday clothing repair and real
   puncture resistance, not label an abstract swatch a garment.

3. **Apply a water-transfer temporary tattoo to a practice forearm.**
   Position a normal transfer, hold it still while wetting its backing with a
   cloth, then remove the backing leaving the picture intact. The proposed skill
   is transferring a fragile image between carriers while maintaining contact
   on a curved surface. Score final registration, missing image and distortion
   with a reference photo. This must differ physically from merely sticking on
   a label: insufficient wetting, sliding and early removal must lose parts of
   the image. **Conditional, potentially economical.** First establish that the
   selected transfer actually adheres to the chosen practice-skin material;
   silicone compatibility is not proven. [Manufacturer instructions](https://www.ohmytat.com/products/fake-wall-e-temporary-tattoo-sticker)
   specify wetting and peeling after 30 seconds. Do not infer substrate
   compatibility or clinical use from those instructions.

4. **Twist-fold a pop-up mesh laundry hamper and secure its folded loops.**
   Start with a normal open spring-frame hamper; flatten, twist and nest its
   loops, then secure its own retaining strap. This is elastic buckling and
   control of stored spring energy, unlike rotating rigid crate panels. Score
   compact retained size, release stability and whether the frame reopens
   without damage. **Strong novelty candidate, high modelling/controller risk.**
   A preprogrammed collapse or rigid hinge surrogate would remove the central
   work. [Smart Design's ordinary hamper](https://www.shopsmartdesign.com/products/pop-up-laundry-hamper-square-13inch)
   is 13 by 13 by 21 inches, so workspace clearance needs checking before a
   build; do not miniaturize it to fit. Product-label folding instructions are
   transcribed [here](https://www.directionsforme.org/product/140668).

5. **Peel a silicone baking cup away from a muffin without breaking it.**
   Work the flexible cup down and away while supporting the baked muffin, then
   leave it intact on a plate. Score full release and retained intact food;
   partial credit can reflect released area with damage penalties. **Conditional,
   moderate-to-high modelling risk.** Distinguish progressive cup inversion from
   accepted ice-tray twisting and build-plate flexing: it cannot be one angle
   threshold releasing a rigid block. [Ordinary OXO cups](https://www.oxo.com/oxo-gg-silicone-baking-cups-blister.html)
   are flexible and can be inverted. BEHAVIOR's [make_muffins](https://behavior.stanford.edu/knowledgebase/tasks/make_muffins-0.html)
   goal creates cooked muffins on a cookie sheet, with no silicone-cup removal.
   Real cup/muffin adhesion must require manipulation: if tipping alone releases
   the product, do not artificially forbid that solution or invent stickiness.

**Priority:** investigate kale stripping and safety-pin hem repair first.
Temporary transfer is a useful lower-mechanics backup after substrate checking.
Hamper folding has a clearer distinctive capability but should receive a strict
early feasibility gate rather than an open-ended physics project. Muffin
demoulding is a reserve because easy release can erase the proposed challenge.

Other screened directions: ponytail fastening with an elastic has no direct
match found but hair/finger access and entanglement make it a costly reserve;
flossing [#1341](https://github.com/robocurve/benchmark-tasks/pull/1341) and sterile
pouch opening [#1278](https://github.com/robocurve/benchmark-tasks/pull/1278) already
exist and were finally rejected for unrealistic simplifications. They are
rebuild opportunities, not fresh discoveries. Dumpling folding/pinching is
already evaluated in [DP3](https://www.roboticsproceedings.org/rss20/p067.pdf) and
[RoboCook](https://hshi74.github.io/robocook/), so exclude it from this shortlist.

## 17 November: avocado stones and reception adjustment

Research only, using a fresh 641-record task board, targeted all-state PR
searches, review prompt v24 and primary physical/benchmark references. No GPU,
Dream calls, simulation, task implementation or submission. These are qualitative
acceptance judgments, not measured probabilities or claims of hardware success.

### Remove the stone from an avocado half — shortlist, moderate prospects

Proposed instruction: **Remove the stone from this avocado half without crushing
the flesh, and leave the stone in the waste dish.** Start with a freshly halved
ordinary avocado, its stone still firmly attached and the tool lying separately.
Use an ordinary hand pitter; engage the stone, support the fruit, twist and lift,
then release the stone. The [OXO hand tool](https://www.oxo.com/3-in-1-avocado-slicer-901.html)
provides a real twist-removal reference. No knife strike or powered pitting rig
is needed for this proposed scope.

No direct pitting task was found in the current board/PR searches. The nearby
[PSAG avocado task](https://arxiv.org/html/2408.12674v1#S4.SS1) evaluates cutting
around the core without cutting into it; its published success criterion does
not include extracting the stone. BEHAVIOR's
[buy_a_good_avocado](https://behavior.stanford.edu/knowledgebase/tasks/buy_a_good_avocado-0.html)
requires checkout placement, not pitting. This supports a plausible distinction,
not an exhaustive novelty guarantee.

The new capability must be gaining purchase on an embedded irregular object
while preserving soft surrounding food. Generic hold-and-turn is already covered
by the review prompt. A loose sphere in a rigid cup, a proximity-triggered tool
attachment or a turn-angle unlock would erase the case for this task. A reduced
contact/detachment model may be adequate if it preserves slipping, resistance,
fruit damage and genuine tool engagement; that has not been tested. Physical
reset must control cultivar, size, ripeness and cut preparation. Judge actual
stone removal and intact usable flesh with photos and, if needed, a kitchen
scale. No mandatory trajectory or hidden simulated force threshold in scoring.

Avocado is the preferred fruit for this idea because the target is larger and
the activity recognizable. No direct cherry/olive pitting match was found, but
a lever pitter risks reducing the skill to generic fixture loading and pressing.
Do not turn fruit substitutions into multiple near-duplicate submissions.

### Adjust a TV aerial for stable reception — reserve, conditional prospects

Basic preparation is occupied: pending
[PR #2419](https://github.com/robocurve/benchmark-tasks/pull/2419), TK-Z3KXZH,
asks for extending a pocket radio aerial and standing it upright without moving
or tipping its 190 g radio. Received 17 November at 04:33 UTC; not accepted as of
this check. Do not duplicate it with another radio or TV aerial.

A potentially distinct instruction is: **Adjust the indoor TV aerial until the
selected channel has stable reception, then let go.** Begin with a connected,
powered receiver already on a weak channel and its signal-quality display open.
The work is observing reception while changing aerial orientation/position,
then leaving a useful setting. Prefer visible receiver feedback for an RGB
policy. [Philips support](https://www.usa.philips.com/c-t/XC000011301/my-philips-tv-is-not-adding-some-local-channels-after-some-automatic-installation)
documents antenna adjustment to optimize reception of a weak channel.
BEHAVIOR's [turning_on_radio](https://behavior.stanford.edu/knowledgebase/tasks/turning_on_radio-0.html)
only requires the radio's on state. No direct reception-optimization match was
found in the searched submissions; generic feedback tuning remains an overlap
risk even if the exact household device is new.

A particularly relevant warning is finally rejected
[PR #301](https://github.com/robocurve/benchmark-tasks/pull/301#issuecomment-6814707528):
its two-knob programmed meter stood in for claimed antenna/mirror calibration.
Reviewers rejected the abstract mathematical response and the mismatch between
visible meter and scorer. Therefore do not make reception a synthetic green bar
that rises near a chosen target pose. Any proposed reduced RF model needs a
physical basis and evidence for the chosen device/environment, or measured
reception data. A full electromagnetic solver is not inherently required, but
acceptance of a reduced approach is unproven.

Score useful receiver output and sustained reception after both hands withdraw,
with partial credit from observable reception quality; do not score angular
error to a privileged optimum. A repeatable source/environment and realistic
receiver response matter because uncontrolled broadcasts and surroundings make
reset inconsistent. This is mechanically plausible but the reception model and
physical reproducibility may cost more effort than the manipulation. Shortlist
avocado first; keep reception adjustment as a reserve until that evidence exists.

## 17 November: mashing food and poaching an egg

Research only: fresh 642-record board, all-state PR search, related reviews and
primary research. No direct mashing/guacamole/poaching submission found; absence
from search is not a novelty guarantee. No GPU, Dream, simulation or task build.

**Mashing potato or avocado: technically plausible, with substantial but
unresolved external-benchmark novelty risk.** [SPARTA, ICRA 2026](https://arxiv.org/html/2509.24129v2#S5)
evaluates mashing food into a puree-like consistency and explicitly uses avocado
and banana as examples; potato mashing is discussed in its introduction. It
uses tool presses and visual progress toward transformed food. Clay proxies are
used during training for easier resets; this does not erase the underlying
skill overlap. Merely changing the ingredient, adding a bowl-steadying second
arm or calling the result guacamole is unlikely to establish a new capability.
This judgment is an inference under the review prompt, not an organizer ruling
on our unbuilt proposal. Potato and avocado should not be separate submissions.

If pursued despite novelty risk, start with cooked peeled potato or prepared
avocado and an ordinary masher/fork. Food must actually yield and break down
under effective contact; hovering, press counts or tool travel cannot count as
mashing. [Mortar PR1591](https://github.com/robocurve/benchmark-tasks/pull/1591#issuecomment-6822406353)
was sent for revision because travel above the floor could score while
peppercorns remained whole. Score remaining lumps and retained food, using a
reproducible photo/sample procedure, not hidden cumulative stroke distance.
[PR2046](https://github.com/robocurve/benchmark-tasks/pull/2046#issuecomment-6927012837)
was finally rejected for insufficient relatability, so kitchen relevance alone
does not guarantee acceptance. Keep mashing as a conditional candidate rather
than excluding it solely because of a paper; avocado pitting currently has a
clearer distinction.

Clarification after checking the current review prompt: external benchmarks do
count, including suites outside the named examples, but a matching verb or an
existing research paper is not an automatic exclusion. The rule requires the
same ability and equivalent success condition. SPARTA is meaningful overlap
evidence, but we have not established that it is indexed in the review corpus
or found an organizer decision excluding our proposed mashing task. Its
position-selection policy uses a built-in pressing primitive, so a fair
comparison must distinguish that setup from a proposed full manipulation task;
the extra work must itself be meaningful, not just additional routine steps.

**Poaching an egg: potentially distinct, but high implementation risk and low
confidence as a quick submission.** The meaningful activity is gently releasing
a raw egg into hot water, allowing the white to set around the yolk, then
lifting and draining the fragile result. [BDA instructions](https://www.bda.uk.com/resource/perfect-poached-eggs.html)
and [Good Food's method](https://www.bbcgoodfood.com/recipes/poached-eggs)
provide real preparation references. A whirlpool is one technique, not a
mandatory scoring condition. A pre-cracked egg in a cup and already heated water
would isolate the poaching skill honestly; egg cracking itself is already in
[PR1269](https://github.com/robocurve/benchmark-tasks/pull/1269).

The simulator would need useful approximations of white spreading/cohesion,
yolk integrity, temperature/time-dependent setting and delicate spoon contact.
A full biochemical model is unnecessary, but those effects must respond to the
robot and allow meaningful failure. A rigid egg becoming cooked on a timer
would remove the reason this is an interesting task. Reviewers finally rejected
[egg-beating PR447](https://github.com/robocurve/benchmark-tasks/pull/447#issuecomment-6816395810)
for both existing whisking overlap and bead physics omitting rupture and mixing;
that is relevant fidelity evidence, not proof poaching itself is duplicated.

Judge the served egg: retained cohesive white, intact yolk before a standardized
cut, and the specified doneness, with partial credit for usable retained food.
A cut/photo and scale are plausible simple checks; exact thresholds and repeatable
freshness/temperature/reset conditions would still need development. Do not
claim food safety or success merely from elapsed simulated time. Keep as a
future reserve; do not start a substantial thermal/fluid project for this batch.

## 17 November: cut the cap from a cigar

**Conditional reserve: plausible mechanics; no exact duplicate found; low-to-
moderate overall acceptance confidence because of relatability and related
cutting skills.** Research only. Checked live all-state PR search, the recent
642-record board snapshot, the PR title index, BEHAVIOR names and external
research searches. No direct cigar-cutting robotics task found. This is not an
exhaustive novelty guarantee. Human image/activity datasets are not evidence
that a robot manipulation task has already been evaluated. No paid compute.

Proposed instruction: **Cut the cap cleanly from the cigar without splitting or
unwrapping it.** Start with an ordinary unlit cigar and a normal handheld
open-backed double-blade cutter lying separately. The work is locating the
natural cap boundary, controlling insertion depth and alignment, and operating
the cutter while supporting a crushable object. A closed-back depth-stop cutter
would remove much of the proposed depth-selection skill; do not claim that
skill if using one. [XIKAR's physical guide](https://xikar.com/blogs/news/the-art-and-science-of-cigar-cutting)
explains why cutting beyond the cap can unravel the wrapper, and its
[tool instructions](https://xikar.com/pages/xikar-how-to) describe independently
moving blades and squeeze operation. These support task design, not a measured
force model or proof of robot feasibility.

Related tasks include accepted
[cable-tie cutting #1441](https://github.com/robocurve/benchmark-tasks/pull/1441),
plus [fingernail #2346](https://github.com/robocurve/benchmark-tasks/pull/2346)
and [dog-claw #2378](https://github.com/robocurve/benchmark-tasks/pull/2378), both
currently requiring revision. Cigar cutting is not automatically a duplicate
of these different settings, but it needs more than a new object/tool name.
Its strongest distinction is cap-depth control while preserving the wrapper.

Mechanically this seems more tractable than thermal/fluid cooking, but no demo
has been attempted. Use actual blade/cigar contact, enough travel to sever the
cap and approximately real cutting resistance. A disclosed reduced cut rule is
reasonable in principle; there is no need to simulate every tobacco leaf.
Grip/crush and cut-too-deep failures must remain possible. PR2346 specifically
requires cutting resistance in addition to the clipper's spring; PR2378 asks
for verified grip span and force compatibility. Check those on the chosen
ordinary cutter before investing in a demo. Avoid invented force values or
claiming compatibility from shape alone.

Score the resulting open head, full cap separation and retained wrapper/body,
using close photos and a ruler/calipers. Define partial opening and damage
thresholds after selecting a real cigar; do not reward mere approach or impose
a universal millimetre cut depth across cigar shapes. Specify size, cap shape,
conditioning and replacement between trials. No lighting or smoking is part of
the task. Scoring must inspect actual damage, not require one prescribed path.

The principal acceptance concern is category fit. Societal relatability is the
plausible category, but the current prompt explicitly disfavors a familiar
object in a hobbyist/specialist setting. Cigar preparation may fall on that side
of the line; recognizability in films alone does not establish its stated
up-close familiarity criterion. Do not invent a 500k-worker job claim. Keep as
a reserve, behind clearer everyday candidates; this is our judgment, not an
organizer rejection or a ban on the topic.


## 19 November — sun cream, twin pet bowl and tap washer

Fresh screen:749 current board records plus all-state GitHub keyword searches. No paid simulation for these ideas. The new v24 review prompt compares underlying ability with public benchmarks and treats component swaps or chains of simple operations as insufficient novelty.

| Idea | Viability and evidence | Decision |
| --- | --- | --- |
| Apply sun cream | Technically plausible with contact-driven spreading and measurable coverage on a practice arm. ARIO's [Agilex data-collection task9](https://imaei.github.io/project_pages/ario/static/agilex%20cobot-magic%20data%20collection%20tasks.pdf) already specifies spreading ointment evenly on skin. This is a documented task protocol, not proof that it is in the organisers' indexed comparison set. Changing ointment to sunscreen would nevertheless preserve essentially the same skill. | Low novelty confidence as stated; do not build or submit on the present evidence. A claim of UV protection would additionally require more than cosmetic colour coverage. |
| Cat food and water in a twin bowl | [BEHAVIOR-1K](https://behavior.stanford.edu/knowledgebase/tasks/index.html) explicitly lists putting_out_cat_food and putting_out_dog_food. Adding ordinary water pouring or an adjacent bowl does not create a new hardest skill. Feasible, but not a good acceptance bet under the current rules. | Do not build or PR. |
| Change a tap washer | A real compression-tap washer replacement is mechanically feasible, with unscrewing, removing the old washer, installing a replacement and reassembly. [PR2382](https://github.com/robocurve/benchmark-tasks/pull/2382), TK-AH9VBW, was accepted and merged on 20 November at 00:52 UTC; it replaces and verifies a faucet cartridge. The components and retention method differ, but another valve insert replacement has substantial variant risk. | Do not spend compute or PR without a materially distinct skill; a washer/cartridge rename is insufficient. |

No direct gel-nail-extension or wet-hair-blotting title match was found in the fresh GitHub searches. That is a bounded screen, not proof of worldwide novelty. Their previously noted physical preparation, contact and measurable-outcome requirements still apply.
