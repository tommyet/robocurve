"""Single authorized conditional continuation: SOUTHbottom185, no native edit."""
import sys
sys.dont_write_bytecode = True
import json
import math
import time
import hashlib
import itertools
import copy
from pathlib import Path
import numpy as np
from planner import Planner, Exhausted, ROOT, READY
from geometry import BASES, GAP
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import axis_angle_matrix
from scene import layout
from config import TOP

PRIOR = Path('/private/tmp/carton-adaptive-opening/planner-report.json')


def box_gap(a, b):
    p, R, size = a
    q, S, other = b
    axes = np.concatenate([R.T, S.T, np.cross(R.T[:, None], S.T[None, :]).reshape(-1, 3)])
    norm = np.linalg.norm(axes, axis=1)
    axes = axes[norm > 1e-10]/norm[norm > 1e-10, None]
    return float(np.max(abs(axes@(q-p)) - abs(axes@R)@(np.array(size)/2)
                        - abs(axes@S)@(np.array(other)/2)))


class Conditional185(Planner):
    def __init__(self):
        super().__init__()
        self.original = json.loads(PRIOR.read_text())
        self.original_south = self.rotated['south_bottom']
        hinge = next(h for h in layout()[1] if h['b'] == 'south_bottom')
        fp, fr, size = self.original_south
        pivot = fp+fr@hinge['anchor_b']
        R = axis_angle_matrix(self.rotated['south'][1][:, 0], np.radians(
            185-self.row['angles_deg']['south_bottom_hinge']))@fr
        self.rotated['south_bottom'] = (pivot-R@hinge['anchor_b'], R, size)
        self.conditional_south = self.rotated['south_bottom']
        self.model.contact_cache = {float(k): v for k, v in
            self.original['contact_heading_certificates'].items()}
        self.left_by_angle = {}
        self.prefix_validation = []
        self.panel_checks = []

    def budget(self, kind=None):
        if time.monotonic()-self.started >= 180:
            raise Exhausted('180s CPU-wall budget')
        if kind == 'ik':
            if self.ik_count >= 2000:
                raise Exhausted('2000 IK attempts')
            self.ik_count += 1
        if kind == 'full':
            if self.full_count >= 600:
                raise Exhausted('600 full315 geometry certificates')
            self.full_count += 1

    def panels(self, angle):
        _, _, _, obs = self.state(angle, 0)
        results = []
        vertices = np.array(list(itertools.product([-1., 1.], repeat=3)))
        for name, connected in [('south_bottom', 'south'), ('north_bottom', 'north')]:
            p, R, size = obs[name]
            minz = float((p+(vertices*np.array(size)/2)@R.T)[:, 2].min())
            results.append(dict(pair=[name, 'table'], gap_m=minz-TOP))
            for other in obs:
                if other == name or other == connected:
                    continue
                results.append(dict(pair=[name, other], gap_m=box_gap(obs[name], obs[other])))
        worst = min(results, key=lambda r:r['gap_m'])
        return dict(angle_deg=float(angle), safe=bool(worst['gap_m'] >= -1e-5),
                    worst=worst, pairs=results,
                    scope='S185 andN againstallotheractualpanels+cutter/table; onlydirecthingewall pair excluded; no0.2mm blanketpanel-margin claim')

    def left_at_angle(self, angle):
        if angle in self.left_by_angle:
            return self.left_by_angle[angle]
        _, _, _, obs = self.state(angle, 0)
        parked = self.model.parts('right', self.native['right']['joints'],
                                  self.native['right']['finger_joints'])
        g = self.full('left', READY, [FINGER_OPEN]*2, obs, parked)
        self.left_by_angle[angle] = g
        return g

    def evaluate(self, angle, heading, parent, seed_label):
        self.budget()
        panels = self.panels(angle)
        self.panel_checks.append(panels)
        if not panels['safe']:
            return dict(valid=False, angle_deg=float(angle), heading_deg=heading,
                        reason='conditional_panel_table_collision', geometry=panels)
        left = self.left_at_angle(angle)
        if not left['safe']:
            return dict(valid=False, angle_deg=float(angle), heading_deg=heading,
                        reason='idle_left_collision_with_current_world', geometry=left)
        return super().evaluate(angle, heading, parent, seed_label)

    def validate_prefixes(self):
        self.records = copy.deepcopy(self.original['retained_nodes'])
        for index, node in enumerate(self.records):
            self.budget()
            angle = node['angle_deg']
            panels = self.panels(angle)
            _, _, _, obs = self.state(angle, node['heading_deg'])
            checks = []
            if panels['safe']:
                left = self.left_at_angle(angle)
                for fingers in ([-.003]*2, [-node['contact']['common_opening_m']]*2):
                    checks.append(self.full('right', node['q'], fingers, obs,
                                            self.left, intended=True))
                p, R = ik.tcp_pose(node['q'], BASES['right'])
                pe = float(np.linalg.norm(p-np.array(node['tcp'])))
                re = float(np.linalg.norm(ik._rot_error(np.array(node['R']), R)))
                passed = bool(left['safe'] and pe <= 2e-6 and re <= .002
                              and all(g['safe'] and g['target_gap_m'] >= -1e-5 for g in checks))
            else:
                passed, left, pe, re = False, None, None, None
            node['valid'] = passed
            node['open_and_loaded_geometry'] = checks
            node['conditional185_prefix_valid'] = passed
            self.prefix_validation.append(dict(index=index, passed=passed,
                angle_deg=angle, heading_deg=node['heading_deg'], panels=panels,
                idle_left=left, right_open_loaded=checks, pinned_pe_m=pe, pinned_re_rad=re))
        # Reject a descendant if any source-prefix node became invalid.
        for node in self.records:
            node['valid'] = bool(node['valid'] and all(
                self.records[i]['conditional185_prefix_valid'] for i in node['path']))
        return sorted([n for n in self.records if n['valid'] and n['angle_deg'] == -45.],
                      key=self.rank, reverse=True)[:4]

    def continue_arc(self, beam):
        self.best = beam[0]['path']
        failures = []
        for angle in np.arange(-40., 185.001, 5.):
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
                return 'CONDITIONAL_NEXT_ANGLE_BLOCKED', failures
            beam = sorted(survivors, key=self.rank, reverse=True)[:4]
            self.best = beam[0]['path']
            print('CONDITIONAL_BEAM', angle, [n['heading_deg'] for n in beam],
                  'IK', self.ik_count, 'FULL', self.full_count, flush=True)
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
                node = self.evaluate(angle, heading, dense[-1], end['seed_branch'])
                if not node['valid']:
                    return 'CONDITIONAL_DENSIFICATION_FAILED', [node]
                if np.max(abs(np.array(node['q'])-dense[-1]['q'])) > .02+1e-12:
                    return 'CONDITIONAL_DENSIFICATION_JOINT_STEP_FAILED', [node]
                dense.append(node)
        self.dense = dense
        return 'CONDITIONAL_SAMPLED185_ARC_ONLY', []

    def run_conditional(self):
        status, failures = 'INCOMPLETE', []
        try:
            if not self.park():
                status = 'LEFT_PARK_NOT_CERTIFIED_UNDER_CONDITION'
            else:
                beam = self.validate_prefixes()
                if not beam:
                    status = 'NO_REVALIDATED_MINUS45_PREFIX'
                else:
                    status, failures = self.continue_arc(beam)
        except Exhausted as error:
            status, failures = 'INCOMPLETE_BUDGET', [str(error)]
        files = [Path(__file__), ROOT/'planner.py', ROOT/'geometry.py', PRIOR,
                 Path('/private/tmp/carton-adaptive-opening/dependency-strategy.json')]
        out = dict(status=status, elapsed_execution_wall_s=time.monotonic()-self.started,
            ik_attempts=self.ik_count, full315_certificates=self.full_count,
            caps=dict(wall_s=180, ik=2000, full315=600),
            condition='SOUTHbottom185 assumedONLY inCPU; SOUTHtop/allotherpanels unchanged; nophysicalSopening/retention/LEFTbodybrace/boxroll proved',
            conditional_south_pose={'position':self.conditional_south[0].tolist(),
                                    'R':self.conditional_south[1].tolist()},
            prefix_revalidation=self.prefix_validation, left_park=self.park_trials,
            idle_left_by_angle=self.left_by_angle, panel_checks=self.panel_checks,
            best_prefix=[self.records[i] for i in self.best], retained_nodes=self.records,
            densified_arc=getattr(self,'dense',None), terminal_failures=failures,
            source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},
            physical_twist_unproved=True, native_authorized=False,
            scope='FINITE_CONDITIONAL_CPU_ONLY; originalfrozenreportnotmodified; nofamilyexpansion')
        (ROOT/'conditional-report.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
        print('DONE',status,'IK',self.ik_count,'FULL',self.full_count,
              'wall',out['elapsed_execution_wall_s'],flush=True)
        return out


if __name__ == '__main__':
    Conditional185().run_conditional()
