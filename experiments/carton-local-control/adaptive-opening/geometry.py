"""Role-explicit full-arm guard and finite contact polygons for CPU planning."""
import sys
sys.dont_write_bytecode = True
sys.path[:0] = ['/private/tmp/spray-yam-source',
                '/private/tmp/carton-open-coupon/task',
                '/private/tmp/carton-scoop-guard-profile']
import numpy as np
from yam_arena import ik
from scoop_safety import convex_box_gap
from fast_safety import ScoopSafety

BASES = {'left': np.array([0., .305, .75]),
         'right': np.array([0., -.305, .75])}
GAP = .0002


def unique_axes(v):
    n = np.linalg.norm(v, axis=1)
    return np.unique(np.round(v[n > 1e-10] / n[n > 1e-10, None], 8), axis=0)


def convex_pair(a, b):
    """Same facet/edge SAT as Astra's existing exact mutual refinement."""
    ea = unique_axes(np.concatenate([a[:, 1]-a[:, 0], a[:, 2]-a[:, 1], a[:, 0]-a[:, 2]]))
    eb = unique_axes(np.concatenate([b[:, 1]-b[:, 0], b[:, 2]-b[:, 1], b[:, 0]-b[:, 2]]))
    axes = unique_axes(np.concatenate([
        np.cross(a[:, 1]-a[:, 0], a[:, 2]-a[:, 0]),
        np.cross(b[:, 1]-b[:, 0], b[:, 2]-b[:, 0]),
        np.cross(ea[:, None], eb[None, :]).reshape(-1, 3)]))
    best = -100.
    for start in range(0, len(axes), 256):
        ax = axes[start:start+256]
        pa, pb = a.reshape(-1, 3) @ ax.T, b.reshape(-1, 3) @ ax.T
        best = max(best, float(np.maximum(pa.min(0)-pb.max(0), pb.min(0)-pa.max(0)).max()))
        if best >= GAP:
            return best
    return best


def clip_polygon(poly, axis, bound, keep_less):
    if not len(poly):
        return np.empty((0, 3))
    output = []
    previous = poly[-1]
    pv = previous[axis]-bound
    inside = lambda value: value <= 1e-14 if keep_less else value >= -1e-14
    for point in poly:
        value = point[axis]-bound
        if inside(value) != inside(pv):
            output.append(previous + (point-previous) * (-pv)/(value-pv))
        if inside(value):
            output.append(point)
        previous, pv = point, value
    return np.asarray(output).reshape(-1, 3)


def union_area_in_rectangle(polygons, rect):
    """Exact piecewise-linear scanline union; vertices/edge crossings split x.

    Handles overlapping convex decomposition facets without adding their areas
    or filling holes by a convex hull. Boundary-only gaps have zero area.
    """
    xmin, xmax, ymin, ymax = rect
    polys, edges, xs = [], [], [xmin, xmax]
    for poly in polygons:
        p = np.column_stack([np.asarray(poly)[:, :2], np.zeros(len(poly))])
        for axis, value, less in [(0, xmin, False), (0, xmax, True),
                                  (1, ymin, False), (1, ymax, True)]:
            p = clip_polygon(p, axis, value, less)
        if len(p) < 3:
            continue
        polys.append(p[:, :2])
        xs.extend(p[:, 0])
        for a, b in zip(p, np.roll(p, -1, axis=0)):
            if abs(b[0]-a[0]) > 1e-14:
                slope = (b[1]-a[1])/(b[0]-a[0])
                edges.append((min(a[0], b[0]), max(a[0], b[0]), slope, a[1]-slope*a[0]))
    for i, (lo, hi, m, c) in enumerate(edges):
        for lo2, hi2, m2, c2 in edges[i+1:]:
            if abs(m-m2) > 1e-14:
                x = (c2-c)/(m-m2)
                if max(lo, lo2) < x < min(hi, hi2):
                    xs.append(x)
    xs = np.unique(xs)
    area = 0.
    for a, b in zip(xs[:-1], xs[1:]):
        x = (a+b)/2
        intervals = []
        for poly in polys:
            y = []
            for p, q in zip(poly, np.roll(poly, -1, axis=0)):
                if min(p[0], q[0]) < x < max(p[0], q[0]):
                    y.append(p[1]+(q[1]-p[1])*(x-p[0])/(q[0]-p[0]))
            if len(y) >= 2:
                intervals.append((min(y), max(y)))
        end, length = -np.inf, 0.
        for lo, hi in sorted(intervals):
            length += max(0., hi-max(lo, end))
            end = max(end, hi)
        area += (b-a)*length
    return float(area)


class Geometry:
    def __init__(self):
        self.model = ScoopSafety()
        self.names = self.model.names
        p, R = ik.tcp_pose(np.zeros(6))
        world = self.model.world(np.zeros(6), [-.003, -.003], np.zeros(3))
        self.hand = [(i, n, (tri-p) @ R) for i, (n, tri) in enumerate(world)
                     if n in ('gripper', 'tip_left', 'tip_right')]
        self.contact_cache = {}

    def parts(self, side, q, fingers):
        return self.model.world(q, fingers, BASES[side])

    def guard(self, side, q, fingers, obstacles, other, *, intended=False):
        """All315 pieces, all supplied OBBs/table; opposite arm never deleted."""
        pieces = self.parts(side, q, fingers)
        vertices = np.concatenate([t.reshape(-1, 3) for _, t in pieces])
        obs = [(n, p, R, size) for n, (p, R, size) in obstacles.items()]
        gaps = self.model._pair_gaps(pieces, vertices, obs)
        mask = np.zeros_like(gaps, dtype=bool)
        if intended:
            column = next(i+1 for i, (n, _, _, _) in enumerate(obs) if n == 'north_bottom')
            mask[:, column] = [n in ('tip_left', 'tip_right') for n in self.names]
        hard = self.model._minimum(gaps, ~mask, pieces, obs)
        target = self.model._minimum(gaps, mask, pieces, obs) if intended else (10., None, None)
        a = np.minimum.reduceat(vertices, self.model.starts, axis=0)
        b = np.maximum.reduceat(vertices, self.model.starts, axis=0)
        ov = np.concatenate([t.reshape(-1, 3) for _, t in other])
        c = np.minimum.reduceat(ov, self.model.starts, axis=0)
        d = np.maximum.reduceat(ov, self.model.starts, axis=0)
        pairs = np.max(np.maximum(a[:, None]-d[None], c[None]-b[:, None]), axis=2)
        i, j = np.unravel_index(pairs.argmin(), pairs.shape)
        mutual = float(pairs[i, j])
        pair_id = [int(i), int(j), pieces[i][0], other[j][0]]
        refinements = []
        for i, j in sorted(np.argwhere(pairs < GAP), key=lambda ij: pairs[tuple(ij)]):
            g = convex_pair(pieces[i][1], other[j][1])
            refinements.append([int(i), int(j), pieces[i][0], other[j][0], g])
            if g < GAP:
                mutual, pair_id = g, [int(i), int(j), pieces[i][0], other[j][0]]
                break
        else:
            if refinements:
                mutual = min(GAP, min(x[-1] for x in refinements))
                pair_id = ['all_unseparated_AABB_pairs_refined', len(refinements)]
        return dict(safe=bool(hard[0] >= GAP and mutual >= GAP),
                    hard_gap_m=float(hard[0]), hard_pair=list(hard[1:]),
                    target_gap_m=float(target[0]), target_pair=list(target[1:]),
                    other_arm_gap_m=mutual, other_arm_pair=pair_id,
                    exact_mutual_refinements=refinements)

    def local_hand(self, openings):
        result = []
        for i, n, tri in self.hand:
            t = tri.copy()
            if n == 'tip_left':
                t[:, :, 0] += .003-openings[0]
            elif n == 'tip_right':
                t[:, :, 0] -= .003-openings[1]
            result.append((i, n, t))
        return result

    def cheap_hand(self, tcp, R, obstacles, openings=(.003, .003)):
        from config import TOP
        hard = (10., None, None)
        targets = {'tip_left': 10., 'tip_right': 10.}
        for i, n, tri in self.local_hand(openings):
            t = tri @ R.T+tcp
            g = float(t[:, :, 2].min()-TOP)
            if g < hard[0]:
                hard = (g, n, 'table')
            for name, (p, rot, size) in obstacles.items():
                g = convex_box_gap(t, p, rot, size)
                if name == 'north_bottom' and n in targets:
                    targets[n] = min(targets[n], g)
                elif g < hard[0]:
                    hard = (g, n, name)
        return dict(safe=bool(hard[0] >= GAP and min(targets.values()) >= -1e-5),
                    hard_gap=list(hard), finger_target_gaps=targets)

    def contact(self, heading, board_size):
        """Angle-invariant contact certificate in the actual flap frame."""
        if heading in self.contact_cache:
            return self.contact_cache[heading]
        h = np.radians(heading)
        R = np.column_stack([[-0., -0., -1.],
                             [-np.cos(h), np.sin(h), 0.],
                             [np.sin(h), np.cos(h), 0.]])
        patch = np.array([.055, -board_size[1]/2+.0025, 0.])
        tcp = patch-R @ np.array([0., 0., .0105])
        targets = {}
        for jaw in ('tip_left', 'tip_right'):
            def gap(opening):
                return min(convex_box_gap(t @ R.T+tcp, np.zeros(3), np.eye(3), board_size)
                           for _, n, t in self.local_hand((opening, opening)) if n == jaw)
            lo, hi = 0., .003
            if gap(hi) < -1e-5 or gap(lo) > 1e-6:
                targets[jaw] = dict(valid=False, reason='no_open_to_closed_first_contact')
                continue
            for _ in range(19):
                mid = (lo+hi)/2
                if gap(mid) < 0:
                    lo = mid
                else:
                    hi = mid
            targets[jaw] = dict(valid=True, first_contact_opening_m=hi)
        if not all(v['valid'] for v in targets.values()):
            result = dict(valid=False, jaws=targets)
            self.contact_cache[heading] = result
            return result
        common = np.mean([v['first_contact_opening_m'] for v in targets.values()])
        valid = True
        for jaw in targets:
            polys, signed, ids = [], [], []
            for index, name, raw in self.local_hand((common, common)):
                if name != jaw:
                    continue
                world = raw @ R.T+tcp
                normal = np.cross(world[:, 1]-world[:, 0], world[:, 2]-world[:, 0])
                lengths = np.linalg.norm(normal, axis=1)
                for k, tri in enumerate(world):
                    if lengths[k] < 1e-14 or raw[k, :, 2].min() < .008:
                        continue  # No back of finger or foretip-edge contacts.
                    sign = 1. if tri[:, 2].mean() > 0 else -1.
                    if normal[k, 2]/lengths[k]*(-sign) < .995:
                        continue
                    p = tri.copy()
                    face = sign*board_size[2]/2
                    for axis, bound, less in [(2, face-1e-5, False), (2, face+1e-5, True),
                            (0, -board_size[0]/2, False), (0, board_size[0]/2, True),
                            (1, -board_size[1]/2, False), (1, board_size[1]/2, True)]:
                        p = clip_polygon(p, axis, bound, less)
                    if len(p) >= 3:
                        polys.append(p)
                        signed.extend((sign*(p[:, 2]-face)).tolist())
                        ids.append([index, k])
            # Astra clarified2mm is the setback from the board's freeedge,
            # not2mm depth of the loaded contact polygon. Preserve the real
            # finite union, including its holes/disconnected components.
            setback_polys = [clip_polygon(p, 1, -board_size[1]/2+.002, False)
                             for p in polys]
            setback_polys = [p for p in setback_polys if len(p) >= 3]
            rect = [-board_size[0]/2, board_size[0]/2,
                    -board_size[1]/2+.002, board_size[1]/2]
            area = union_area_in_rectangle(setback_polys, rect)
            points = np.concatenate(setback_polys) if setback_polys else np.empty((0, 3))
            span = float(np.ptp(points[:, 0])) if len(points) else 0.
            depth = float(np.ptp(points[:, 1])) if len(points) else 0.
            target_gap = min(convex_box_gap(t @ R.T+tcp, np.zeros(3), np.eye(3), board_size)
                             for _, n, t in self.local_hand((common, common)) if n == jaw)
            okay = bool(area > 1e-12 and span >= .005 and target_gap >= -1e-5
                        and target_gap <= 1e-5)
            targets[jaw].update(common_opening_m=float(common), finite_patch_valid=okay,
                board_setback_m=.002, contact_union_area_m2=area,
                contact_tangential_span_m=span, actual_contact_inboard_depth_m=depth,
                signed_face_gap_min_m=min(signed) if signed else None,
                signed_face_gap_max_m=max(signed) if signed else None,
                target_gap_m=float(target_gap), raw_piece_triangle_ids=ids,
                contact_polygons_flap_local_m=[p.tolist() for p in setback_polys])
            valid = valid and okay
        result = dict(valid=valid, heading_deg=heading, jaws=targets,
                      common_opening_m=float(common), ordinary_single_grip_scalar=True,
                      purchase_definition='Real finite inward-pad polygons at least2mm inboard fromfreeedge, spanning5mm tangentially; real depth/area reported, no2mm-deep rectangle requirement. Astra clarified wording.',
                      force_or_friction_proved=False)
        self.contact_cache[heading] = result
        return result
