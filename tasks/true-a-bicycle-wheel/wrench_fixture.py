"""Finite-load bench fixture for contact diagnosis, never a robot controller.

The fixture applies a bounded force and moment at the proposed physical handle
grasp. It cannot prescribe the wrench pose, nipple angle or spoke tension.
"""
import numpy as np


def rotation_vector(R):
    R=np.asarray(R,float)
    angle=float(np.arccos(np.clip((np.trace(R)-1)/2,-1.,1.)))
    skew=np.array((R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]))
    if angle<1e-7:return skew/2
    if np.pi-angle<1e-5:raise ValueError('Fixture target must not jump by pi radians')
    return skew*angle/(2*np.sin(angle))


def bounded(vector,limit):
    vector=np.asarray(vector,float)
    if not np.isfinite(vector).all() or not np.isfinite(limit) or limit<=0:
        raise ValueError('Finite fixture loads and positive limit required')
    return vector*min(1.,limit/max(float(np.linalg.norm(vector)),1e-30))


class HandleFixture:
    """Conservative declared bench loads, not an equivalence claim to YAM.

    10 N resultant force and 0.35 N m moment at the handle are below the
    pinned YAM's 50 N finger actuator and 7 N m wrist actuator limits. These
    actuator limits do not guarantee that a particular robot grasp can transmit
    the fixture loads; the real grasp still needs its own native demonstration.
    """
    def __init__(self,mass_kg,tcp_local,force_limit_n=10.,moment_limit_nm=.35):
        self.mass=float(mass_kg);self.tcp=np.asarray(tcp_local,float)
        self.force_limit=float(force_limit_n);self.moment_limit=float(moment_limit_nm)
        self.previous=None

    def command(self,center,R,com_local,velocity,target_center,target_R,dt):
        center,R,com_local,velocity,target_center,target_R=map(np.asarray,
            (center,R,com_local,velocity,target_center,target_R))
        grip=center+R@self.tcp;com=center+R@com_local
        target=target_center+target_R@self.tcp
        if self.previous is None:target_v=np.zeros(3);target_w=np.zeros(3)
        else:
            target_v=(target-self.previous[0])/dt
            target_w=rotation_vector(target_R@self.previous[1].T)/dt
        self.previous=(target.copy(),target_R.copy())
        grip_v=velocity[:3]+np.cross(velocity[3:],grip-com)
        force=bounded(1000.*(target-grip)+20.*(target_v-grip_v)+
                      np.array((0.,0.,self.mass*9.80665)),self.force_limit)
        moment=bounded(4.*rotation_vector(target_R@R.T)+.10*(target_w-velocity[3:]),self.moment_limit)
        return dict(position_m=grip,force_n=force,moment_nm=moment,
                    position_error_m=float(np.linalg.norm(target-grip)),
                    orientation_error_rad=float(np.linalg.norm(rotation_vector(target_R@R.T))))
