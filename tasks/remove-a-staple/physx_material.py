"""Native PhysX plastic-hinge hook; one-leg coupon controls passed.

Call from the same before-substep hook used by accepted cordkit/filekit tasks.
The scene must supply the MEASURED joint angle, radians relative to its authored
rest/clinch pose. The hook changes plastic rest angle only after material yield;
it never sets body poses, installs a grasp, removes the staple or awards credit.
Native drive gains are per degree, whereas materials.py uses SI radians.
"""
import math
from materials import PlasticHinge, SteelSpec


class PhysxPlasticHinge:
    def __init__(self, joint_prim, steel=None):
        from pxr import UsdPhysics
        self.hinge = PlasticHinge(steel or SteelSpec())
        self.drive = UsdPhysics.DriveAPI.Apply(joint_prim, "angular")
        self.drive.CreateTypeAttr("force")
        self.drive.CreateStiffnessAttr(self.hinge.spec.stiffness_nm_per_rad*math.pi/180.)
        self.drive.CreateDampingAttr(0.)
        self.drive.CreateTargetPositionAttr(0.)
        self.drive.CreateTargetVelocityAttr(0.)

    def update_from_measured_angle(self, measured_angle_rad):
        result = self.hinge.advance(measured_angle_rad)
        self.drive.GetTargetPositionAttr().Set(math.degrees(self.hinge.plastic_angle_rad))
        return result

    def reset(self):
        self.hinge = PlasticHinge(self.hinge.spec)
        self.drive.GetTargetPositionAttr().Set(0.)
