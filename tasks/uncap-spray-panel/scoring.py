"""Measured-state spray deposition. No simulator imports or pose writes.

The plume is an explicit approximation, not a particle/fluid simulation.
Inputs are supplied by run.py, never by the policy. Surface cells represent
the first intersection with a single fixed backing plane.
"""
import math
from config import *


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def blocked(origin, endpoint, spheres):
    """Conservative cap/hand occlusion, not a full scene ray query."""
    ray=[b-a for a,b in zip(origin,endpoint)]
    length2=dot(ray,ray)
    for center,radius in spheres:
        offset=[b-a for a,b in zip(origin,center)]
        t=max(0.,min(1.,dot(offset,ray)/length2))
        closest=[a+t*b for a,b in zip(origin,ray)]
        if distance(closest,center) < radius:return True
    return False


def opposing_left_can_contacts(sample):
    """Policy-independent opposing contact presence, not a grip-force calibration."""
    try:
        names=sample['left_contact_bodies'];matrix=sample['left_can_contact_matrix']
        if names.count('tip_left')!=1 or names.count('tip_right')!=1 or len(matrix)!=len(names):return False
        if any(len(row)!=1 or len(row[0])!=3 for row in matrix):return False
        if not all(math.isfinite(v) for row in matrix for v in row[0]):return False
        left=matrix[names.index('tip_left')][0];right=matrix[names.index('tip_right')][0]
        a=math.sqrt(dot(left,left));b=math.sqrt(dot(right,right))
        return a>=.1 and b>=.1 and dot(left,right)<=-.5*a*b
    except (KeyError,TypeError,ValueError,IndexError,AttributeError):return False


def right_tcp_clear(sample):
    try:
        tcp=sample['hands'][1]['tcp']
        return len(tcp)==3 and all(math.isfinite(v) for v in tcp) and all(distance(tcp,sample[name])>.070 for name in ('can','cap'))
    except (KeyError,TypeError,ValueError,IndexError):return False


class SprayScorer:
    def __init__(self):
        self.dose = [0.] * (GRID*GRID)
        self.time = None
        self.spray_seconds = 0.
        self.emitted = self.off_target = 0.
        self.invalid = None
        self.cap_removed = False
        self.finish_hold = 0.
        self.value = 0.
        self.held_contact=False;self.right_clear=False

    @staticmethod
    def cells():
        for i in range(GRID):
            y = TARGET_CENTER[0] - BOARD_HALF + (i+.5)*CELL
            for j in range(GRID):
                z = TARGET_CENTER[1] - BOARD_HALF + (j+.5)*CELL
                target = ((y-TARGET_CENTER[0])**2+(z-TARGET_CENTER[1])**2 <= TARGET_RADIUS**2)
                yield i*GRID+j, (TARGET_X, y, z), target

    def update(self, s):
        """Exactly one sample per 20 Hz control step; gaps fail closed."""
        numbers = [s['time'], s['button_travel'], *s['nozzle'], *s['axis'],
                   *s['can'], *s['cap'], s['can_speed'], s['cap_speed'], s['upright']]
        if not all(math.isfinite(x) for x in numbers):
            self.invalid = 'nonfinite state'
            self.value = 0.
            return self.result()
        dt = 0. if self.time is None else s['time']-self.time
        self.time = s['time']
        if dt < 0 or dt > .051:
            self.invalid = 'nonmonotonic time or missing control samples'
        if min(s['can'][2], s['cap'][2]) < TOP-.03:
            self.invalid = 'can or cap dropped below table'
        # Compare against the actual seated location, not the can centre:
        # the latter is already 87 mm away even when the cap is closed.
        seated=[p+.087*u for p,u in zip(s['can'],s.get('can_axis',(0.,0.,1.)))]
        if s['cap_detached'] and distance(s['cap'], seated) > .06:
            self.cap_removed = True
        spray = (self.cap_removed and s['button_travel'] >= PRESS_TRAVEL)
        if spray and not self.invalid:
            remaining = max(0., MAX_SPRAY_SECONDS-self.spray_seconds)
            dt_spray = min(dt, remaining)
            self.spray_seconds += dt_spray
            # Emitted mass is normalized to seconds. Rays that miss the target,
            # including those outside the backing board or wrong-facing, count
            # as overspray. No credit from merely aiming or touching the panel.
            axis_len = math.sqrt(dot(s['axis'], s['axis']))
            if abs(axis_len-1.) > .001:
                self.invalid = 'non-unit spray axis'
            weights = []
            occluders=[(s['cap'], .035)] + [(p,.010) for p in s.get('hand_tcp',[])]
            for index, point, target in self.cells():
                ray = [p-n for p,n in zip(point, s['nozzle'])]
                along = dot(ray, s['axis'])
                r = math.sqrt(dot(ray, ray))
                if not MIN_RANGE <= r <= MAX_RANGE or along <= 0 or s['axis'][0] <= 0:
                    continue
                cosine = max(-1., min(1., along/r))
                theta = math.acos(cosine)
                if theta > math.radians(SPRAY_HALF_ANGLE):
                    continue
                if blocked(s['nozzle'],point,occluders):continue
                # Solid-angle quadrature: cos(incidence)*area/r². Uniform
                # conical flux with centre-weighting, calibrated analytically.
                weight = math.exp(-2*(theta/math.radians(SPRAY_HALF_ANGLE))**2)
                solid = ray[0]/r * CELL*CELL/(r*r)
                weights.append((index, target, weight, solid))
            cone_integral = math.pi * math.radians(SPRAY_HALF_ANGLE)**2 * (1-math.exp(-2))/2
            on_fraction = 0.
            for index, target, weight, solid in weights:
                self.dose[index] += dt_spray * weight
                if target:
                    on_fraction += weight*solid/cone_integral
            self.emitted += dt_spray
            self.off_target += dt_spray * (1-min(1., on_fraction))
        target_doses = [self.dose[i] for i,_,target in self.cells() if target]
        coverage = sum(d >= COAT_DOSE for d in target_doses)/len(target_doses)
        overspray = self.off_target/self.emitted if self.emitted else 0.
        cap_parked = (distance(s['cap'][:2], CAP_PAD[:2]) <= .045 and
                      abs(s['cap'][2]-(TOP+.017)) <= .012 and s['cap_speed'] < .02)
        self.held_contact=opposing_left_can_contacts(s);self.right_clear=right_tcp_clear(s)
        finished = (self.cap_removed and coverage >= .90 and overspray <= .15 and cap_parked and
                    self.held_contact and self.right_clear and s['upright']>=math.cos(math.radians(10)) and
                    s['can_speed']<.02 and s['button_travel']<.0005)
        self.finish_hold = self.finish_hold+dt if finished else 0.
        if self.invalid:
            self.value = 0.
        elif self.finish_hold >= 1.:
            self.value = 1.
        elif self.cap_removed and cap_parked and coverage >= .90 and overspray <= .15:
            self.value = .75
        elif self.cap_removed and cap_parked and coverage >= .50 and overspray <= .15:
            self.value = .5
        elif self.cap_removed and cap_parked:
            self.value = .25
        else:
            self.value = 0.
        return self.result()

    def result(self):
        target_doses = [self.dose[i] for i,_,target in self.cells() if target]
        return dict(score=self.value, invalid=self.invalid, cap_removed=self.cap_removed,
                    coverage=sum(d >= COAT_DOSE for d in target_doses)/len(target_doses),
                    overspray=self.off_target/self.emitted if self.emitted else 0.,
                    spray_seconds=self.spray_seconds, finish_hold=self.finish_hold,
                    opposing_left_can_contacts=self.held_contact,right_tcp_clear=self.right_clear)
