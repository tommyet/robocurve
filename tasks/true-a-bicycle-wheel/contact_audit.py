"""Read-only contact diagnostics against the fixed bench and wheel stand.

The old tensor API's net force can omit friction. Detailed filtered normal and
friction patches are both used; the bearing constraint itself is not a contact.
"""
import numpy as np


def _array(value):
    return value.detach().cpu().numpy()


class FixedContactAudit:
    def __init__(self, simulation_view, stage, metadata):
        from pxr import UsdPhysics
        from thread_coupling import body_paths
        root=metadata['hub_path'].rsplit('/wheel/',1)[0]
        sensors=[p for p in body_paths(metadata) if p!=metadata['wrench_path']]
        # Exact collider paths avoid ambiguous nesting matches. Sensors exclude
        # the free wrench. Robots are intentionally outside this fixed-fixture
        # diagnostic; their contacts must be assessed separately.
        filters=[]
        for prim in stage.Traverse():
            path=str(prim.GetPath())
            if prim.HasAPI(UsdPhysics.CollisionAPI) and (path.startswith(root+'/stand/') or '/table/' in path or path=='/Bench'):
                filters.append(path)
        if not filters:raise RuntimeError('No fixed bench/stand contact filters found')
        self.view=simulation_view.create_rigid_contact_view(sensors,[filters]*len(sensors),max_contact_data_count=16384)
        self.sensors=list(self.view.sensor_paths);self.filters=list(self.view.filter_paths)
        self.capacity=int(self.view.max_contact_data_count)
        if self.view.sensor_count!=len(sensors) or not self.view.filter_count:
            raise RuntimeError('Incomplete fixed-fixture contact view')

    def measure(self, dt, axle):
        force,point,normal,separation,count,start=map(_array,self.view.get_contact_data(dt))
        friction,friction_point,friction_count,friction_start=map(_array,self.view.get_friction_data(dt))
        force=force.reshape(-1);point=point.reshape(-1,3);normal=normal.reshape(-1,3)
        separation=separation.reshape(-1);friction=friction.reshape(-1,3);friction_point=friction_point.reshape(-1,3)
        count=count.reshape(self.view.sensor_count,self.view.filter_count);start=start.reshape(count.shape)
        friction_count=friction_count.reshape(count.shape);friction_start=friction_start.reshape(count.shape)
        if int(count.sum())>=self.capacity or int(friction_count.sum())>=self.capacity:
            raise RuntimeError('Fixed-fixture contact audit buffer exhausted')
        total_force=np.zeros(3);total_torque=np.zeros(3);pairs=[]
        for i,j in np.argwhere((count>0)|(friction_count>0)):
            k=int(start[i,j]);n=int(count[i,j]);f=force[k:k+n,None]*normal[k:k+n]
            q=point[k:k+n];t=np.cross(q-axle,f).sum(0)
            kf=int(friction_start[i,j]);nf=int(friction_count[i,j]);ff=friction[kf:kf+nf]
            t+=np.cross(friction_point[kf:kf+nf]-axle,ff).sum(0);net=f.sum(0)+ff.sum(0)
            total_force+=net;total_torque+=t
            pairs.append(dict(sensor=self.sensors[i],filter_index=int(j),normal_patch_count=n,friction_patch_count=nf,
                              force_n=net.tolist(),torque_about_axle_nm=t.tolist(),
                              minimum_separation_m=float(separation[k:k+n].min()) if n else None))
        return dict(fixed_contact_force_n=total_force.tolist(),fixed_contact_torque_about_axle_nm=total_torque.tolist(),
                    pairs=pairs,note='Bench/stand contacts only; excludes robot contacts and native bearing constraint reactions.')
