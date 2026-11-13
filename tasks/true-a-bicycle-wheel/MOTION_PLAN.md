# Wheel manipulation plan

This is a development plan. Native 091 reaches the first wrench turn but loses
engagement:90° commanded produces 22.86° net tightening. The wheel remains
within its integrity limits. No full-score demonstration exists.

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
clearance or task success. The 1073-action complete candidate has a screened
released-spin finale, but its fast service prefix remains superseded until the
slower physical turn succeeds. The final run limit must cover a validated full
sequence; the proposed 60 s limit is not yet final.
