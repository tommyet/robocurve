# Isolated postcut NORTH/LEFT outer-flap scoop — CPU candidate only

This never changes production source, native physics/material/scoring parameters
or object poses after the existing one-time diagnostic restore. Source179s
cut011 state has allcuts/cutterparked; coupon restores exact panel/cutter/arm
poses ONCE, zeroesvelocities, then ordinary14Dcommands/quietcheck. It seeds no
cut coverage or scorer; all output is synthetic/unsealed/unscored/mediafalse.

Route: hold right arm/cutter parked; prepare6mm totalaperture over2s; raise
LEFT atits heldcommandXY/R toTCPZ.910; translate/reorientaboveaperture; fixedR
descendstaging→inside; insertunderedge; acquirecontactwith≤.8mmuplift; measured
supportedarc to−30deg ONLY. Start firstprepared14D exactly, thenCartesian
references are limitedcontinuously frompreviousissuedFK. No fixedclockjump
can skip actualtracking/geometry/contact/angle gates. Arm/fingerjointlimits and
existing.04rad/.05gripperpersample slewremain. Diagnostic paths use20mm/s
free,5mm/sinside/arc,1mm/sacquire and.35rad/s rotations. No integral/forceboost
or mechanicalgainchange is introduced.

Runtimefreshactual315pieces/current12panels/cutter/table/actualotherarm are
checked EACHcommand, including afterquietrestore; candidateboundedcommandFK is
also checked beforeissue. Non-targetgap/otherarmpositiveAABBseparation mustbe
≥.2mm. ONLYtip_right↔north_bottom is intended incontactacquire/arc; palm/spare
finger remain obstacles. Intendedtargetgap is TELEMETRY, notzerooverlapproof.
Actualforcebounds are1N target/.1N otherhand-panels; supportpresence≥.02N.
Commandlead≤1.8deg, abortifmeasuredlead≥2deg. Arcstall5s (timerRESETatacquire→arc),
pathstall8s,cuttershift>2mm and malformedreadings abort. Terminal5frames mustbe
consecutive. No blanketclearanceclaim for servoerror/continuoussweep/dynamics.

CPUgeometry: originalAstra75desiredposes certifiedGRIPPERONLY. New321samples
check ALL315correctedcollisionpiecesperarm withcontinuous-seedPINNEDIK;
non-targetmin.3601mm,otherarm110.776mm. ContactIKtol1e−6 (sameDLS/limits)
reduces intendednumericaloverlapfrom66.96um to.624um, belowunchanged10um
certificatecriterion. Baselineandnewreports/scripts remain separatelyfrozen.
None ofthis is a nativecontact/friction/actualopening proof.

89CPUtests pass;8focusedcontrollerregressions cover bounds/waypoints/exactentry,
freshunsafegeometryabort, handofftimer/consecutiveterminalcounter, lead/force
abort andno pose/wrench/score setters. Compilepasses. Physics/sourcefiles from
cut011 are byte-identical; onlycouponfactory/harness/controller/safety/tests
were added/changed. Dependencies remain pinnedYAMassets/NumPy/nativeIsaac.

`north-scoop-route.json` is now reviewed:true afterAstraPASS21:01:16UTC/root
authorization forONEboundedunscoredrestored diagnostic. Original reviewed:false
route/manifest hashes are preserved underreview/preapproval-*.json. Controller
and mechanics are unchanged. No GPUjob is launched by this packaging step;
root/operatoralone mayrun the authorized boundeddiagnostic:

```
python task/open_run.py --snapshot start/snapshot.json \
 --route north-scoop-route.json --seconds 110 --out /new/diagnostic/output
```

The prescribedspeedlimits need~60s before settling, so old50s harnesscap could
truncatea legitimatearc. CLI accepts5..120diagnosticseconds; controllercaps100s
plusquietprefix. This changes NOproductiontaskbudget. Existingrawnormal/friction
reader records actualsubstepbuffers (notCOP); no newbenchforces are applied.
Routecompletion means only measuredpartialpresentation, neverfulltaskscore.
