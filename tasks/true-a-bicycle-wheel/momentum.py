"""Read-only native angular-momentum diagnostic; not a task success signal."""
import numpy as np
from thread_coupling import rotation_batch


class MomentumAudit:
    def __init__(self, view, excluded_wrench_path):
        self.view = view
        self.paths = list(view.prim_paths)
        self.keep = np.array([path != excluded_wrench_path for path in self.paths])
        self.mass = view.get_masses().detach().cpu().numpy().reshape(-1).astype(float)
        self.inertia = view.get_inertias().detach().cpu().numpy().reshape(-1,3,3).astype(float)
        self.com = view.get_coms().detach().cpu().numpy()[:,:3].astype(float)
        if not np.isfinite(self.mass).all() or np.any(self.mass <= 0):
            raise RuntimeError('Invalid native wheel mass properties')

    def properties(self):
        return [dict(path=p, mass_kg=float(m), com_in_body_m=c.tolist(),
                     inertia_in_body_kg_m2=I.tolist())
                for p,m,c,I in zip(self.paths,self.mass,self.com,self.inertia)]

    def measure(self, transforms, axle):
        R = rotation_batch(np.asarray(transforms)[:,3:])
        positions = np.asarray(transforms)[:,:3] + np.einsum('nij,nj->ni',R,self.com)
        velocity = self.view.get_velocities().detach().cpu().numpy().astype(float)
        world_I = R @ self.inertia @ R.transpose(0,2,1)
        orbital = np.cross(positions-axle,self.mass[:,None]*velocity[:,:3])
        spin = np.einsum('nij,nj->ni',world_I,velocity[:,3:])
        gravity = np.zeros_like(positions);gravity[:,2]=-9.80665*self.mass
        return dict(angular_momentum_kg_m2_s=(orbital+spin)[self.keep].sum(0).tolist(),
                    gravity_torque_about_axle_nm=np.cross(positions-axle,gravity)[self.keep].sum(0).tolist(),
                    maximum_angular_speed_rad_s=float(np.linalg.norm(velocity[self.keep,3:],axis=1).max()),
                    note='Excludes wrench. Compare changes against external contact/bearing torque; no score is inferred.')
