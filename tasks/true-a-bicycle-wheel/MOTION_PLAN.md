# Wheel manipulation plan

This is a development plan. Native112 turns one nipple90.54° during tightening,
but entry loosens it and withdrawal stays engaged. The clearer122 approach
overshoots before insertion, then stops on an unreachable re-aligned wrist
target. No full-score demonstration or complete repair cycle exists.

The fixed service route uses the published 55° wheel layout and robot URDF.
The left hand steadies the rim while the right picks up the free wrench,
services nipple 0, indexes the wheel−22.5° by physically moving the held rim,
and services nipple 2. Three quarter turns per nipple restore nominal thread
length. A separate finale returns/releases the wrench, spins/releases the rim
and observes a whole revolution. The scorer judges geometry and tension, not
these planned nipple angles.

The scripted controller uses native tool pose to estimate the physical grasp.
It latches a measured square-nipple orientation before each quarter turn,
choosing the equivalent orientation closest to the nominal wrist workspace.
The target does not chase nipple rotation during tightening. Measured nipple
translation follows rim deflection. All outputs are ordinary position-, speed-
and effort-limited robot joint targets; no object state, material, attachments
or actuator efforts are modified. Dream does not receive this feedback.
During the clear approach's settling hold, one re-alignment is allowed after
five successive20Hz orientations remain within0.01rad. This avoids chasing
the brief nipple wobble seen in096 while preventing a stale approach frame.
Insertion and tightening retain a fixed orientation target for that quarter.
Native104 exposed a stage-boundary bug: first insertion relatched the nipple
after early mouth contact, requesting an unreachable handle pose. The approach
and first insertion now share one engagement latch. Replaying the measured
190th-frame grasp through all190 remaining commands passes IK and the sampled
hull screen. This correction still needs a native retry.

The joint tracker adds bounded integral compensation, at most 0.12 rad, using
only robot joint observations. Native 091 showed why the old 0.9 s turn was too
fast: arm tracking error reached 0.50 rad and jaw-centre lag reached 112.8 mm.
Insertion initially loosened the nipple, then the wrench lost engagement.
The first 203 native poses have no unexpected sampled hull intersections.

`slow_contact_plan.py` keeps the first 160 commands unchanged and adds 1.5 s
approach/insertion settling,1.5 s insertion, a 4 s turn,1 s final settling and slower
withdrawal. It has 380 actions/19 s. Its 220 new commands solve and pass the hull
screen using measured 091step 160 grasp/wheel geometry. This is a counterfactual
planning check; future physical slip and deformation still need native evidence.

Only the clear approach may accept a bounded IK residual fitting the 5 mm mouth.
The jaw-point error bound is at most 0.75 mm versus 0.885 mm mouth half-clearance.
Tight insertion/turning retains the stricter command-quality check. Native
contact, not IK accuracy, must prove engagement and torque transfer.
Native096 stops at177 before insertion on0.002086rad versus the old0.002rad
angular limit, although its0.7462mm jaw-point bound fits the reserved0.750mm.
The approach angular cap is now0.01rad only inside that unchanged jaw bound.
The revised controller passes all recorded096 approach observations and the
203 remaining commands with the measured177 grasp; their hull screens have
no unexpected intersections. This is local evidence, not a completed retry.

Compile and run commands are in `README.md`. Plans carry source and URDF hashes.
`audit_robot_plan.py` screens nominal targets; `audit_native_trace.py` checks
measured states. Both use real robot hulls, but neither certifies continuous-time
clearance or task success. The old1073-action fast candidate is superseded.
The slower1630-action service plus391-action released-spin finale would require
2021 actions; the proposed2400-action/120s limit leaves time for the complete
task. All1630 nominal service poses pass the hull screen, but no full service
or released revolution has been demonstrated.

Native112 physically turns the first nipple90.54° during its intended stroke,
but the10mm lead-in touches the square early and withdrawal never clears the
jaws. The clearer448-action diagnostic uses a14mm lead-in,16mm withdrawal and
a settling hold. Its state-assisted controller checks the full measured square
is beyond the jaw ends before crossing the wheel plane. Approximate IK is
allowed only while the solved square remains clearly outside the mouth; the
seated turn retains its stricter bound. These are controller safeguards, not
task scoring conditions or object-state interventions.

Native122 stops at174/448 actions before intended insertion. Its14mm nominal
lead-in does not prevent dynamic overshoot: actual whole-square clearance falls
from12.49mm at160 to−1.72mm at168. The nipple rotates over6° from early contact.
The settled re-alignment shifts the long-handle wrist target outside reach;
three local seeds and four damping values cannot solve it. An endpoint-only relocation was insufficient: one candidate still hit a wrist
limit during the transition, and a lower candidate intersected the table.

The explicit `forward10-right50-lower10` diagnostic now moves the fixture
10 mm forward and 50 mm toward the right arm, and shortens its upright 10 mm.
The base remains on the tabletop. Its 652-action route slows the last approach,
pauses before insertion, and blends measured alignment only while clear of the
wheel. All 652 nominal frames and both 570-frame measured-state routes pass
IK and unintended-hull screens. Native physics has not run on this layout;
actual grip, contact, withdrawal and the rest of the repair remain unproved.
See `RELOCATION_DIAGNOSTIC.md` for exact geometry, evidence and future gates.
