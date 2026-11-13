"""State-assisted peg alignment through ordinary bounded robot commands.

Free-jaw observations center their mouth on the line before handle release.
This controller writes no body poses, cloth nodes, forces or physics settings.
It is a disclosed scripted demo, never a Dream policy observation or action.
"""
import numpy as np
from interpret_motion import rotation_xyzw


class PegMouthServo:
    def __init__(self,start=820,end=880,target=(.52,.115,1.09)):
        self.start=start;self.end=end;self.target=np.asarray(target,float)
        self.offset=np.zeros(6);self.records=[];self.last_error=None
        self.desired_tcp=None;self.desired_q=None

    def action(self,step,reference,observed,body_poses):
        from yam_arena import ik,station
        a=np.asarray(reference,float).copy();observed=np.asarray(observed,float).reshape(-1)
        if self.start<step<=self.end:
            poses=np.asarray(body_poses,float)
            if poses.shape!=(2,7) or not np.isfinite(poses).all():raise ValueError('Invalid free peg observations')
            inner=[p[:3]+rotation_xyzw(p[3:])@np.array((.030,0.,sign*.0005)) for p,sign in zip(poses,(-1.,1.))]
            mouth=np.mean(inner,0);error=self.target-mouth;distance=float(np.linalg.norm(error))
            gap=float(np.linalg.norm(inner[1]-inner[0]))
            if distance>.065 or gap<.006 or gap>.012:raise RuntimeError('Peg alignment lost its held open-jaw geometry')
            if self.desired_tcp is None:
                self.desired_tcp,_=ik.tcp_pose(a[7:13],station.BASES['right'])
                self.desired_q=a[7:13].copy()
            _,nominal_rotation=ik.tcp_pose(a[7:13],station.BASES['right'])
            increment=error*min(.15,.00075/max(distance,1e-12))
            self.desired_tcp=self.desired_tcp+increment
            q,pe,re=ik.solve(self.desired_tcp,ik.matrix_to_quat_xyzw(nominal_rotation),self.desired_q,base_pos=station.BASES['right'],iters=100)
            if pe>.002 or re>.025:raise RuntimeError('Peg-mouth servo could not produce a normal reachable action')
            self.desired_q=q.copy()
            a[7:13]=q;self.offset=q-reference[7:13];self.last_error=distance
            self.records.append(dict(step=step,mouth_m=mouth.tolist(),error_m=error.tolist(),gap_m=gap,commanded_tcp_increment_m=increment.tolist(),desired_tcp_m=self.desired_tcp.tolist()))
        elif self.end<step<=self.end+140:
            if self.last_error is None or self.last_error>.0015:
                raise RuntimeError('Peg mouth did not reach1.5mm alignment; closure withheld')
            blend=1. if step<=self.end+60 else max(0.,1-(step-(self.end+60))/80)
            a[7:13]+=blend*self.offset
        return a
