"""Finite, explicitly sampled adaptive-heading access planner; CPU only."""
import sys
sys.dont_write_bytecode = True
import json
import math
import time
import hashlib
from pathlib import Path
import numpy as np
from geometry import Geometry, BASES, GAP
from yam_arena import ik, YAM_URDF
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import quat_xyzw_to_matrix, axis_angle_matrix
from scene import layout

ROOT = Path(__file__).parent
INPUT = Path('/private/tmp/carton-grasp-topology-audit')
SNAPSHOT = Path('/private/tmp/carton-open-coupon/start/source-row.json')
READY = np.array([0., 1., 1., -.6, 0., 0.])


class Exhausted(RuntimeError):
    pass


class Planner:
    def __init__(self):
        self.started = time.monotonic()
        self.ik_count = 0
        self.full_count = 0
        self.spec = json.loads((INPUT/'adaptive-heading-plan.json').read_text())
        self.row = json.loads(SNAPSHOT.read_text())
        self.prior = json.loads((INPUT/'shallow-side-arc.json').read_text())
        self.model = Geometry()
        self.defs = {x['name']: x for x in layout()[0]}
        self.hinge = next(x for x in layout()[1] if x['b'] == 'north_bottom')
        self.native = {h['side']: h for h in self.row['native_hands']}
        self.actual = {n: (np.array(v[:3]), quat_xyzw_to_matrix(v[3:]), self.defs[n]['size'])
                       for n, v in self.row['poses'].items()}
        trans = next(t for t in self.prior['transforms'] if t['roll_worldY_deg'] == 90)
        self.transform = trans
        A, shift = np.array(trans['rotation']), np.array(trans['translation'])
        self.rotated = {n: (A@p+shift, A@R, size) for n, (p, R, size) in self.actual.items()}
        cp = np.array(self.row['cutter_pose'][:3])
        cr = quat_xyzw_to_matrix(self.row['cutter_pose'][3:])
        for obs in (self.actual, self.rotated):
            for n, size, offset in [('cutter_handle', (.1, .025, .025), (0, 0, 0)),
                    ('cutter_guard', (.02, .03, .02), (.052, 0, .002)),
                    ('cutter_blade', (.014, .0005, .008), (.062, 0, -.016))]:
                obs[n] = (cp+cr@offset, cr, size)
        self.a0 = float(self.row['angles_deg']['north_bottom_hinge'])
        self.fp0, self.fr0, self.size = self.rotated['north_bottom']
        self.axis = self.rotated['north'][1][:, 0]
        self.pivot = self.fp0+self.fr0@self.hinge['anchor_b']
        self.records = []
        self.park_trials = []
        self.left = None
        self.best = []
        self.cache = {}

    def budget(self, kind=None):
        if time.monotonic()-self.started >= 180:
            raise Exhausted('180s CPU-wall budget')
        if kind == 'ik':
            if self.ik_count >= 2000:
                raise Exhausted('2000 IK attempts')
            self.ik_count += 1
        if kind == 'full':
            if self.full_count >= 300:
                raise Exhausted('300 full315 geometry certificates')
            self.full_count += 1

    def solve(self, p, R, seed, side):
        self.budget('ik')
        q, pe, re = ik.solve(p, ik.matrix_to_quat_xyzw(R), seed,
                            base_pos=BASES[side], iters=500, tol=1e-6)
        return q, float(pe), float(re)

    def full(self, side, q, fingers, obs, other, intended=False):
        self.budget('full')
        return self.model.guard(side, q, fingers, obs, other, intended=intended)

    def state(self, angle, heading):
        fr = axis_angle_matrix(self.axis, math.radians(angle-self.a0)) @ self.fr0
        fp = self.pivot-fr@self.hinge['anchor_b']
        patch = fp+.055*fr[:, 0]+(-self.size[1]/2+.0025)*fr[:, 1]
        x = -fr[:, 2]
        z = math.cos(math.radians(heading))*fr[:, 1]+math.sin(math.radians(heading))*fr[:, 0]
        R = np.column_stack([x, np.cross(z, x), z])
        tcp = patch-R@np.array([0., 0., .0105])
        obs = dict(self.rotated)
        obs['north_bottom'] = (fp, fr, self.size)
        return tcp, R, patch, obs

    def park(self):
        native = self.native['left']
        q0 = np.array(native['joints'])
        f0 = np.array(native['finger_joints'])
        right = self.model.parts('right', self.native['right']['joints'],
                                 self.native['right']['finger_joints'])
        p, R = ik.tcp_pose(q0, BASES['left'])
        targets = [('READY', READY)]
        for name, q in targets + [('raised_sameXY_plus60mm_sameR', None)]:
            trial = dict(name=name, samples=[], accepted=False)
            if q is None:
                q, pe, re = self.solve(p+[0, 0, .060], R, q0, 'left')
                trial['IK'] = dict(pe_m=pe, re_rad=re)
                if pe > 2e-6 or re > .002:
                    trial['failure'] = 'left_target_IK'
                    self.park_trials.append(trial)
                    continue
            count = max(1, math.ceil(float(np.max(abs(q-q0))) / math.radians(1.)))
            failed = None
            for t in np.linspace(0, 1, count+1):
                current = q0+t*(q-q0)
                fingers = f0+t*(FINGER_OPEN-f0)
                g = self.full('left', current, fingers, self.actual, right)
                trial['samples'].append(dict(fraction=float(t), q=current.tolist(),
                                              fingers=fingers.tolist(), geometry=g))
                if not g['safe']:
                    failed = 'actual_unrotated_relocation_collision'
                    break
            if failed is None:
                g = self.full('left', q, [FINGER_OPEN]*2, self.rotated, right)
                trial['reoriented_endpoint_geometry'] = g
                if not g['safe']:
                    failed = 'reoriented_world_endpoint_collision'
            trial['failure'] = failed
            trial['accepted'] = failed is None
            self.park_trials.append(trial)
            if failed is None:
                self.left = self.model.parts('left', q, [FINGER_OPEN]*2)
                return True
        return False

    def evaluate(self, angle, heading, parent, seed_label):
        self.budget()
        contact = self.model.contact(heading, self.size)
        self.budget()
        if not contact['valid']:
            return dict(valid=False, angle_deg=angle, heading_deg=heading,
                        reason='opposed_pad_patch_or_common_jaw_geometry', contact=contact)
        tcp, R, patch, obs = self.state(angle, heading)
        opening = contact['common_opening_m']
        for openings in ((.003, .003), (opening, opening)):
            cheap = self.model.cheap_hand(tcp, R, obs, openings)
            self.budget()
            if not cheap['safe']:
                return dict(valid=False, angle_deg=angle, heading_deg=heading,
                            reason='cheap_full_gripper_geometry', geometry=cheap)
        q, pe, re = self.solve(tcp, R, parent['q'], 'right')
        if pe > 2e-6 or re > .002:
            return dict(valid=False, angle_deg=angle, heading_deg=heading, reason='IK',
                        pe_m=pe, re_rad=re, q=q.tolist())
        states = []
        for openings in ((.003, .003), (opening, opening)):
            g = self.full('right', q, -np.array(openings), obs, self.left, intended=True)
            states.append(g)
            if not g['safe'] or g['target_gap_m'] < -1e-5:
                return dict(valid=False, angle_deg=angle, heading_deg=heading,
                            reason='full315_geometry', geometry=states)
        # Full arm check above covers actual returned FK. Pinned FK is retained
        # explicitly instead of treating a desired Cartesian pose as achieved.
        actual_p, actual_R = ik.tcp_pose(q, BASES['right'])
        margin = float(np.minimum(q-ik.LOWER, ik.UPPER-q).min())
        path = parent.get('path', [])
        node = dict(valid=True, angle_deg=float(angle), heading_deg=int(heading),
                    q=q.tolist(), tcp=tcp.tolist(), R=R.tolist(), physical_patch=patch.tolist(),
                    pinned_FK_tcp=actual_p.tolist(), pinned_FK_R=actual_R.tolist(),
                    pe_m=pe, re_rad=re, joint_limit_margin_rad=margin,
                    contact=contact, open_and_loaded_geometry=states,
                    seed_branch=seed_label,
                    heading_variation_deg=parent.get('heading_variation_deg', 0)+abs(heading-parent.get('heading_deg', 0)),
                    joint_travel_rad=parent.get('joint_travel_rad', 0)+float(np.linalg.norm(q-parent['q'])))
        # Prefix references use integer record indices, not a recursive JSON tree.
        index = len(self.records)
        node['path'] = path+[index]
        self.records.append(node)
        return node

    @staticmethod
    def rank(node):
        clearance = min(min(x['hard_gap_m'], x['other_arm_gap_m'])
                        for x in node['open_and_loaded_geometry'])
        return (node['joint_limit_margin_rad'], clearance,
                -node['heading_variation_deg'], -node['joint_travel_rad'])

    def search(self):
        c31 = self.prior['candidates'][31]
        seeds = [('prior_actual_connected_branch', c31['seed_trials'][0]['samples'][0]['q']),
                 ('READY', READY)]
        beam = []
        failures = []
        for label, seed in seeds:
            n = self.evaluate(self.a0, 0, dict(q=np.array(seed)), label)
            if n['valid']:
                if not any(np.max(abs(np.array(n['q'])-b['q'])) < 1e-3 for b in beam):
                    beam.append(n)
            else:
                failures.append(n)
        if not beam:
            return 'NO_VALID_INITIAL_PINCH', failures
        self.best = max(beam, key=self.rank)['path']
        for angle in np.arange(-75., 185.001, 5.):
            survivors, failures = [], []
            for parent in sorted(beam, key=self.rank, reverse=True):
                for change in (0, -5, 5, -10, 10):
                    heading = parent['heading_deg']+change
                    if not -60 <= heading <= 60:
                        continue
                    key = (float(angle), heading, parent['seed_branch'])
                    if key in self.cache:
                        continue
                    self.cache[key] = True
                    n = self.evaluate(float(angle), heading, parent, parent['seed_branch'])
                    if n['valid']:
                        survivors.append(n)
                    else:
                        failures.append(n)
            if not survivors:
                return 'NO_CONTINUOUS_PREFIX_IN_FINITE_FAMILY', failures
            beam = sorted(survivors, key=self.rank, reverse=True)[:4]
            self.best = beam[0]['path']
            print('BEAM', angle, [n['heading_deg'] for n in beam],
                  'IK', self.ik_count, 'FULL', self.full_count, flush=True)
        # No selected full arc may be advertised until every connecting edge is
        # resampled and the actual resulting q increments meet the tighter bound.
        coarse = [self.records[i] for i in self.best]
        dense = [coarse[0]]
        for end in coarse[1:]:
            start = dense[-1]
            count = max(1, math.ceil(abs(end['angle_deg']-start['angle_deg'])/2),
                        math.ceil(abs(end['heading_deg']-start['heading_deg'])/2),
                        math.ceil(np.max(abs(np.array(end['q'])-start['q']))/.02))
            for f in np.linspace(0, 1, count+1)[1:]:
                angle = start['angle_deg']+f*(end['angle_deg']-start['angle_deg'])
                heading = start['heading_deg']+f*(end['heading_deg']-start['heading_deg'])
                n = self.evaluate(angle, heading, dense[-1], end['seed_branch'])
                if not n['valid']:
                    return 'DENSIFICATION_FAILED', [n]
                if np.max(abs(np.array(n['q'])-dense[-1]['q'])) > .02+1e-12:
                    return 'DENSIFICATION_JOINT_INCREMENT_FAILED', [n]
                dense.append(n)
        self.dense = dense
        return 'SAMPLED_KINEMATIC_FULLARC_ONLY', []

    def run(self):
        status, failures = 'INCOMPLETE', []
        try:
            if not self.park():
                status = 'NEITHER_ALLOWED_LEFT_PARK_CERTIFIED'
            else:
                status, failures = self.search()
        except Exhausted as error:
            status, failures = 'INCOMPLETE_BUDGET', [str(error)]
        report = dict(status=status, elapsed_wall_s=time.monotonic()-self.started,
            ik_attempts=self.ik_count, full_geometry_certificates=self.full_count,
            limits=dict(ik=2000, full_geometry=300, wall_s=180),
            spec=json.loads((INPUT/'adaptive-heading-plan.json').read_text()),
            rigid_box_transform=self.transform,
            left_relocation_trials=self.park_trials,
            retained_nodes=self.records, best_prefix=[self.records[i] for i in self.best],
            contact_heading_certificates=self.model.contact_cache,
            densified_selected_arc=getattr(self, 'dense', None), terminal_failures=failures,
            physical_twist_caveat='Heading changes require pad slip/torsional friction or measured loosen/regrasp; no rigid no-slip grasp/native proof. Box roll is separate unproved motion.',
            scope='CPU_ONLY_EXPLICITLY_SAMPLED; all315 pieces role-explicit; all12actual panels transformed together, only north_bottom rotated about hinge; actual parked knife; LEFT never deleted; no scene/native/production edits',
            native_authorized=False,
            source_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [Path(__file__), ROOT/'geometry.py', INPUT/'adaptive-heading-plan.json',
                 INPUT/'shallow-side-arc.json', SNAPSHOT, Path(YAM_URDF),
                 Path('/private/tmp/carton-scoop-guard-profile/fast_safety.py'),
                 Path('/private/tmp/carton-open-coupon/task/scoop_safety.py')]})
        (ROOT/'planner-report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        print('DONE', status, 'IK', self.ik_count, 'FULL', self.full_count,
              'wall', report['elapsed_wall_s'], flush=True)
        return report


if __name__ == '__main__':
    Planner().run()
