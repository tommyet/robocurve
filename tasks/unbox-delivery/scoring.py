"""Measured-state tape sweep and ordered unboxing milestones, without simulator imports."""
import math
from config import SEAM, LID_Z, DESTINATION, CUTTER_START, TOP

class UnboxScorer:
    def __init__(self):
        self.cut = [False]*21
        self.previous_tip = None
        self.previous_valid = False
        self.value = 0.
        self.opened = False
        self.rest_since = None
        self.invalid = False
        self.reason = None

    def update(self,s):
        t=s['time']; tip=s['tip']; c=s['cutter']; item=s['item']
        values=[t,*tip,*c['pos'],c['speed'],*item['pos'],item['speed'],
                s['blade_down'],*s['flap_angles']]
        if not all(math.isfinite(v) for v in values):
            self.invalid=True; self.reason='nonfinite telemetry'
        if item['pos'][2]<TOP-.02 or c['pos'][2]<TOP-.03:
            self.invalid=True; self.reason='item or cutter dropped off table'
        # A guarded blade must be held, aligned down, at tape height. Sweeps faster
        # than 0.25 m/s are excluded to prevent teleport-like segments earning cuts.
        valid=(s['held'] and s['blade_down']>.9 and abs(tip[1])<=.006
               and LID_Z-.004<=tip[2]<=LID_Z+.004)
        if valid and self.previous_valid and self.previous_tip is not None:
            a=self.previous_tip; dt=t-self.previous_time
            dist=math.dist(a,tip)
            if 0<dt<=.1 and .002*dt<=dist<=.25*dt:
                lo,hi=sorted((a[0],tip[0]))
                for i in range(21):
                    x0=SEAM[0]+i*.01; x1=x0+.01
                    # Track each 1 mm slice of the segment's length, not just a
                    # waypoint/tip proximity. Multiple short passes accumulate.
                    for j in range(10):
                        x=x0+(j+.5)*.001
                        if lo<=x<=hi: self.covered.add(i*10+j)
                    self.cut[i]=all(i*10+j in self.covered for j in range(10))
        self.previous_tip=tip; self.previous_valid=valid; self.previous_time=t
        sealed=not all(self.cut)
        angles=s['flap_angles']
        if sealed and max(abs(a) for a in angles)>12:
            self.invalid=True; self.reason='flap forced open before tape was cut'
        if not sealed and min(angles)>=80: self.opened=True
        returned=(math.dist(c['pos'][:2],CUTTER_START[:2])<=.045
                  and abs(c['pos'][2]-CUTTER_START[2])<.025 and c['speed']<.02
                  and not s['held'])
        placed=(abs(item['pos'][0]-DESTINATION[0])<=.025
                and abs(item['pos'][1]-DESTINATION[1])<=.025
                and abs(item['pos'][2]-(TOP+.022))<=.008
                and item['speed']<.01 and s['item_released'])
        ready=self.opened and min(angles)>=70 and returned and placed
        self.rest_since=t if ready and self.rest_since is None else self.rest_since if ready else None
        self.value=0. if sealed else .25
        if self.opened: self.value=.5
        if self.rest_since is not None and t-self.rest_since>=1.-1e-8: self.value=1.
        if self.invalid: self.value=0.
        return self.result()

    @property
    def covered(self):
        if not hasattr(self,'_covered'): self._covered=set()
        return self._covered

    def result(self):
        return dict(score=self.value,cut_segments=sum(self.cut),total_segments=21,
                    opened=self.opened,invalid=self.invalid,reason=self.reason)
