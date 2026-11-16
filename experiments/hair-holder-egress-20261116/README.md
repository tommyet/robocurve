# Read-only holder obstruction audit, 2026-11-16

Internal development evidence; exclude this folder and shared notes from any single-task competition PR. These reports are geometric diagnostics, not contact-force telemetry or feasibility proof. They do not run a GPU simulation.

Input: the source/pose-bound native capture `hair-opposite-sweep-002`, trace SHA13fa63aa7e0b893a45e043decf2ad84e1e66777bcd5b5f9838b5712c6418ddb9, archived locally in revision-completed-before-roll.tgz (SHAad986c070977a23ac77ff476d33cfd4d62b8048819c4748ae4742f3017bf8599). Original helper snapshots retain their local recovery paths; unpack that verified capture under the documented path or adapt those constants before running with the pinned YAM package and NumPy. They load collision geometry from the captured source, not an unrelated current task.

Measured: first signed SAT overlap34.00s, tip_left carrier piece57 versus positive-Y cradle_1; minimum-0.422mm. An independent actual-mesh-vertex-inside-box witness occurs34.70s (piece47), so this is more than a conservative broadphase overlap. Geometry does not measure the contact force.

The15mm-up/Y-90mm/up85mm candidate collides. The X-90mm withdrawal alternative clears the holder but reaches a joint limit; it is not native-ready with payload compensation. No production controller was changed and no additional native trial is recommended from these reports alone.

A subsequent bounded static/front-grasp screen finds one candidate: handle-local Z=-65 mm, tool Z=world +X, closing X=world -Y. The complete 100 mm hand STL translation has minimum 0.618 mm holder clearance;21 nominal IK samples stay below0.1 micrometre error and the minimum joint margin after payload compensation is7.06 degrees. This is UNACQUIRED: release/retract/reorientation/regrasp transitions, whole-arm/other-arm/head clearance and actual opposed handle contacts remain unproved. It is not native-ready or a full task demo. No production code or physics was changed. The original snapshot helper keeps its local capture paths, as above.
