# Follow-up: wrapping, rocking, untangling and five new ideas

Latest research: the [16 November creative shortlist](#16-november-broad-creative-shortlist)
below supersedes the earlier research priorities. It proposes seven new scopes;
none has been built or selected for development. Earlier implementation status
is historical; use the linked batch record and current PR decisions for status.

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
