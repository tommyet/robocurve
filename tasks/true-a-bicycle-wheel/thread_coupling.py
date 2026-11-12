"""Measured-angle screw material coupling for the authored native wheel.

Only measured nipple rotation changes spoke rest length. The energy-conjugate
lead torque is applied equally/oppositely to nipple and hub. Native capped
angular damping supplies an approximate thread-friction law; no pose writes,
proximity grasps or score triggers occur here. Not runtime validated.
"""
from dataclasses import dataclass
import math
import numpy as np


class ThreadTravelOutOfScope(RuntimeError):
    pass


@dataclass(frozen=True)
class ThreadSpec:
    pitch_m_per_turn: float = .000454
    friction_coefficient: float = .15
    thread_mean_radius_m: float = .001
    viscous_friction_nm_s_per_rad: float = 1000.
    minimum_turns: float = -3.
    maximum_turns: float = 3.


def response(length_m, nominal_rest_m, turns, stiffness_n_per_m, spec=None):
    s = spec or ThreadSpec()
    if not all(math.isfinite(v) for v in (length_m,nominal_rest_m,turns,stiffness_n_per_m)):
        raise ValueError("Thread state must be finite")
    if not s.minimum_turns <= turns <= s.maximum_turns:
        raise ThreadTravelOutOfScope("Nipple exceeded the uncalibrated +/-3-turn thread model domain; invalidate the trial, never clamp the angle")
    if length_m <= 0 or nominal_rest_m <= 0 or stiffness_n_per_m <= 0:
        raise ValueError("Positive lengths/stiffness required")
    rest = nominal_rest_m-turns*s.pitch_m_per_turn
    if rest <= 0:
        raise ThreadTravelOutOfScope("Nonpositive spoke rest length")
    extension = max(length_m-rest,0.)
    tension = stiffness_n_per_m*extension
    return {"rest_length_m":rest,"tension_n":tension,
            "energy_j":.5*stiffness_n_per_m*extension**2,
            "lead_torque_nm":-tension*s.pitch_m_per_turn/(2*math.pi),
            "friction_limit_nm":s.friction_coefficient*tension*s.thread_mean_radius_m}


def rotation(q):
    q = np.asarray(q,dtype=float)
    if q.shape != (4,) or not np.isfinite(q).all() or np.linalg.norm(q) < 1e-12:
        raise ValueError("Invalid measured xyzw rotation")
    x,y,z,w=q/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


class NativeThreadCoupler:
    """Call before EVERY native physics substep after stage attachment.

    `metadata` comes from wheel_scene.build_scene. Missing live transforms or
    excess thread travel raises and invalidates the trial. The caller must
    record that error and must not resume with a saturated/clamped state.
    """
    def __init__(self, stage_id, metadata, spec=None):
        from omni.physx import get_physx_interface, get_physx_simulation_interface
        from pxr import PhysicsSchemaTools, Sdf
        self.physics=get_physx_interface()
        self.sim=get_physx_simulation_interface()
        self.stage_id=stage_id
        self.meta=metadata
        self.spec=spec or ThreadSpec()
        self.ids={path:PhysicsSchemaTools.sdfPathToInt(Sdf.Path(path)) for path in
                  [metadata["hub_path"]]+[s["nipple_path"] for s in metadata["spokes"]]}
        self.previous=np.zeros(len(metadata["spokes"]))
        self.unwrapped=np.zeros(len(metadata["spokes"]))
        self.last=[]

    def frame(self,path):
        tr=self.physics.get_rigidbody_transformation(path)
        if not tr.get("ret_val"):
            raise RuntimeError("Live PhysX transform unavailable: "+path)
        return np.asarray(tr["position"],dtype=float),rotation(tr["rotation"])

    def before_step(self):
        import carb
        hp,hR=self.frame(self.meta["hub_path"])
        hub_torque=np.zeros(3)
        self.last=[]
        for i,s in enumerate(self.meta["spokes"]):
            rp,rR=self.frame(s["rim_path"])
            _,nR=self.frame(s["nipple_path"])
            relative=np.asarray(s["reference_nipple_in_rim_rotation"]).T @ rR.T @ nR
            wrapped=math.atan2(relative[2,1],relative[1,1])
            delta=(wrapped-self.previous[i]+math.pi)%(2*math.pi)-math.pi
            self.unwrapped[i]+=delta
            self.previous[i]=wrapped
            turns=s["initial_turn_offset"]+self.unwrapped[i]/(2*math.pi)
            anchor=hp+hR@np.asarray(s["hub_anchor_local_m"])
            endpoint=rp+rR@np.asarray(s["rim_anchor_local_m"])
            length=float(np.linalg.norm(endpoint-anchor))
            state=response(length,s["nominal_rest_m"],turns,s["stiffness_n_per_m"],self.spec)
            s["rest_target_attribute"].Set(state["rest_length_m"]-s["rest_target_origin_m"])
            s["friction_drive"].GetMaxForceAttr().Set(state["friction_limit_nm"])
            torque=nR[:,0]*state["lead_torque_nm"]
            self.sim.apply_torque(self.stage_id,self.ids[s["nipple_path"]],carb.Float3(*map(float,torque)))
            hub_torque-=torque
            self.last.append({"spoke":i,"turns":turns,"length_m":length,**state})
        self.sim.apply_torque(self.stage_id,self.ids[self.meta["hub_path"]],carb.Float3(*map(float,hub_torque)))

    def observation_for_assessor(self):
        """Material telemetry only; never feed this into a robot policy/demo."""
        return self.last
