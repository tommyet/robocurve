"""Measured-state spray deposition. No simulator imports or pose writes.

The plume is an explicit approximation, not a particle/fluid simulation.
Inputs are supplied by run.py, never by the policy. Surface cells represent
the first intersection with a single fixed backing plane.
"""
import math
from functools import lru_cache
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



def circle_rectangle_area(x0,x1,y0,y1,radius):
    """Analytic disk/axis-aligned rectangle intersection (triangle/sector sum).

    Each rectangle edge is split at exact circle crossings. Inside pieces
    contribute signed triangle area; outside pieces contribute circle sectors.
    No centre classification, raster sampling or overspray-specific threshold.
    """
    if not all(math.isfinite(v) for v in (x0,x1,y0,y1,radius)) or x1<=x0 or y1<=y0 or radius<=0:raise ValueError('invalid circle rectangle')
    polygon=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    total=0.
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];aa=dx*dx+dy*dy;bb=2*(a[0]*dx+a[1]*dy);cc=a[0]**2+a[1]**2-radius**2
        ts=[0.,1.];discriminant=bb*bb-4*aa*cc
        if discriminant>0:
            root=math.sqrt(discriminant)
            ts.extend(t for t in ((-bb-root)/(2*aa),(-bb+root)/(2*aa)) if 0.<t<1.)
        ts.sort()
        for lo,hi in zip(ts,ts[1:]):
            p=(a[0]+lo*dx,a[1]+lo*dy);q=(a[0]+hi*dx,a[1]+hi*dy)
            mid=(a[0]+(lo+hi)*dx/2,a[1]+(lo+hi)*dy/2)
            cross=p[0]*q[1]-p[1]*q[0]
            total+=cross/2 if mid[0]**2+mid[1]**2<radius**2 else radius**2*math.atan2(cross,p[0]*q[0]+p[1]*q[1])/2
    return min((x1-x0)*(y1-y0),max(0.,total))


@lru_cache(maxsize=1)
def cell_area_weights():
    """Fixed uniform10mm dose cells clipped at the exact circular plaque."""
    rows=[]
    for i in range(GRID):
        y0=-BOARD_HALF+i*CELL
        for j in range(GRID):
            z0=-BOARD_HALF+j*CELL
            inside=min(CELL*CELL,circle_rectangle_area(y0,y0+CELL,z0,z0+CELL,TARGET_RADIUS))
            rows.append((inside,CELL*CELL-inside))
    return tuple(rows)


def supported_spray_domain(nozzle,axis):
    """Geometric emission validity, separate from visible painted AREA scoring.

    The full authored cone must hit the finite backing within the deposition
    model's supported range. This prevents unmodelled off-board/backward paint
    from silently becoming zero measured overspray. No mass ratio is scored.
    """
    if len(nozzle)!=3 or len(axis)!=3 or not all(math.isfinite(v) for v in (*nozzle,*axis)):return {'valid':False,'reason':'nonfinite spray-domain geometry'}
    length=math.sqrt(dot(axis,axis))
    if abs(length-1.)>.001:return {'valid':False,'reason':'non-unit spray axis'}
    a=[v/length for v in axis];theta=math.radians(SPRAY_HALF_ANGLE);sine=math.sin(theta);ax=a[0];D=TARGET_X-nozzle[0]
    if D<=0 or ax<=sine:return {'valid':False,'reason':'emitting cone does not fully face the backing plane'}
    denominator=ax*ax-sine*sine;bounds=[]
    for coordinate in (1,2):
        centre=nozzle[coordinate]+D*ax*a[coordinate]/denominator
        half=D*sine*math.sqrt(max(0.,ax*ax+a[coordinate]**2-sine*sine))/denominator
        bounds.append((centre-half,centre+half))
    beta=math.acos(max(-1.,min(1.,ax)))
    range_min=D/math.cos(max(0.,beta-theta));range_max=D/math.cos(beta+theta)
    report={'valid':True,'reason':None,'footprint_yz_bounds_m':bounds,'ray_range_bounds_m':[range_min,range_max]}
    for (low,high),centre in zip(bounds,TARGET_CENTER):
        if low<centre-BOARD_HALF-SPRAY_DOMAIN_TOLERANCE_M or high>centre+BOARD_HALF+SPRAY_DOMAIN_TOLERANCE_M:report.update(valid=False,reason='emitting cone footprint leaves finite backing');return report
    if range_min<MIN_RANGE-SPRAY_DOMAIN_TOLERANCE_M or range_max>MAX_RANGE+SPRAY_DOMAIN_TOLERANCE_M:report.update(valid=False,reason='emitting cone leaves supported deposition range')
    return report


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
        self.finish_previous = False
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
            if dt_spray>0:
                domain=supported_spray_domain(s['nozzle'],s['axis'])
                if not domain['valid']:self.invalid=domain['reason']
            # Legacy emitted-flux diagnostics are normalized to seconds; they
            # do not enter the area rubric. Unsupported off-board/backward
            # emission is separately invalidated above. Paint credit requires
            # visible deposition, not merely aiming or touching the panel.
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
        area=self.area_metrics();coverage=area['coverage']
        overspray_area=area['off_plaque_painted_area_m2']
        cap_parked = (distance(s['cap'][:2], CAP_PAD[:2]) <= .045 and
                      abs(s['cap'][2]-(TOP+.017)) <= .012 and s['cap_speed'] < .02)
        self.held_contact=opposing_left_can_contacts(s);self.right_clear=right_tcp_clear(s)
        finished = (self.cap_removed and coverage >= .90 and overspray_area <= MAX_OFF_PLAQUE_AREA_M2 and cap_parked and
                    self.held_contact and self.right_clear and s['upright']>=math.cos(math.radians(10)) and
                    s['can_speed']<.02 and s['button_travel']<.0005)
        self.finish_hold = self.finish_hold+dt if finished and self.finish_previous else 0.
        self.finish_previous = bool(finished and not self.invalid)
        if self.invalid:
            self.value = 0.
        elif self.finish_hold >= 1.-1e-9:
            self.value = 1.
        elif self.cap_removed and cap_parked and coverage >= .90 and overspray_area <= MAX_OFF_PLAQUE_AREA_M2:
            self.value = .75
        elif self.cap_removed and cap_parked and coverage >= .50 and overspray_area <= MAX_OFF_PLAQUE_AREA_M2:
            self.value = .5
        elif self.cap_removed and cap_parked:
            self.value = .25
        else:
            self.value = 0.
        return self.result()

    def area_metrics(self):
        weights=cell_area_weights()
        painted=sum(inside for dose,(inside,outside) in zip(self.dose,weights) if dose>=VISIBLE_DOSE)
        outside=sum(outside for dose,(inside,outside) in zip(self.dose,weights) if dose>=VISIBLE_DOSE)
        painted=min(PLAQUE_AREA_M2,painted)  # roundoff at the analytic full-disk bound
        return dict(coverage=painted/PLAQUE_AREA_M2,visible_plaque_area_m2=painted,
                    off_plaque_painted_area_m2=outside,off_plaque_painted_area_cm2=outside*1e4,
                    off_plaque_area_fraction=outside/PLAQUE_AREA_M2)

    def result(self):
        area=self.area_metrics()
        return dict(score=self.value, invalid=self.invalid, cap_removed=self.cap_removed,**area,
                    overspray=area['off_plaque_area_fraction'],
                    overspray_metric='visible off-plaque painted area / fixed plaque area; not emitted mass',
                    visible_dose_threshold=VISIBLE_DOSE,visible_display_blend_fraction=VISIBLE_COAT_FRACTION,
                    max_off_plaque_painted_area_cm2=MAX_OFF_PLAQUE_AREA_M2*1e4,
                    emitted_mass_seconds_diagnostic=self.emitted,
                    off_target_mass_fraction_diagnostic=self.off_target/self.emitted if self.emitted else 0.,
                    spray_seconds=self.spray_seconds, finish_hold=self.finish_hold,
                    opposing_left_can_contacts=self.held_contact,right_tcp_clear=self.right_clear)
