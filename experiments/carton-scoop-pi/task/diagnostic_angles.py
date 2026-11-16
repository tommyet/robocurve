"""Restored engineering baseline ONLY; cannot furnish fresh-task score evidence."""
import numpy as np
from angle_tracking import ContinuousBottomAngles


class DiagnosticBottomAngles(ContinuousBottomAngles):
    def initialize(self,counter,time_s,poses,velocities):
        if self.failure:return False
        if self.initialized:return self.invalidate('unexpected diagnostic reseed')
        try:
            if type(counter) is not int or counter!=0 or time_s!=0.:
                raise ValueError('diagnostic requires post-restoration prephysics origin')
            matrices,raw,radius=self._read(poses,velocities)
            # In this narrow interval the alternate raw+360 branch exceeds
            # the unchanged274.9degree hinge stop. Overshoot seeds fail closed.
            if np.min(raw)<-84.9 or np.max(raw)>12. or np.min(radius)<1.-1e-5:
                raise ValueError('restored hinge branch not uniquely certified')
            if any(np.max(np.abs(v))>1e-7 for v in velocities.values()):
                raise ValueError('diagnostic restoration must explicitly zero velocities')
        except (ValueError,TypeError) as e:return self.invalidate(e)
        self.initialized=True;self.counter=counter;self.time=float(time_s)
        self.previous=matrices;self.raw=raw;self.radius=radius;self.angles=raw.copy()
        return True

    def evidence(self,control_index,substeps):
        e=super().evidence(control_index,substeps)
        e['initialized_from_authored_zero']=False
        e['scope']='UNSCORED_RESTORED_DIAGNOSTIC_ONLY'
        return e
