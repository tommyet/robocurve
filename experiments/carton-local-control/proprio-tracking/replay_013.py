"""Observational joint-only PI replay, with separate read-only geometry audit.

The recorded actual state does not respond to these hypothetical commands;
this is not a closed-loop test, new native attempt, or convergence proof.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib
import json
import numpy as np
from joint_position_pi import JointPositionPI

ROOT = Path(__file__).parent
GUARD = Path('/private/tmp/carton-scoop-guard-profile')
YAM = Path('/private/tmp/spray-yam-source')
SOURCE = Path('/private/tmp/carton-open013-approved-source')
sys.path[:0] = [str(GUARD), str(YAM)]
from fast_safety import ScoopSafety
from workload import SAMPLES, inputs
from yam_arena import ik, YAM_URDF


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    rows = [json.loads(line) for line in (SOURCE / 'recent100-raw.jsonl').read_text().splitlines()]
    pi = JointPositionPI(ik.LOWER, ik.UPPER)
    pi.begin(rows[0]['action_14d'][:6], rows[0]['time'])
    guard = ScoopSafety()
    results = []
    for row in rows:
        left = next(h for h in row['native_hands'] if h['side'] == 'left')
        right = next(h for h in row['native_hands'] if h['side'] == 'right')
        # The frozen013 controller has no augmentation, so issued q is its
        # unbiased nominal target. POSTSTEP measured q is explicitly identified.
        proposal = pi.propose(row['action_14d'][:6], left['joints'], row['time'])
        args = dict(fingers=np.array(left['finger_joints']),
                    poses={n: np.array(v) for n, v in row['poses'].items()},
                    cutter=np.array(row['cutter_pose']),
                    right_q=np.array(right['joints']),
                    right_fingers=np.array(right['finger_joints']), contact=False)
        actual = guard.check(q=np.array(left['joints']), **args)
        candidate = guard.check(q=np.array(proposal.command), **args)
        safe = bool(actual['safe'] and candidate['safe'])
        receipt = pi.resolve(proposal, guard_safe=safe)
        results.append(dict(time_s=row['time'], nominal_q=row['action_14d'][:6],
                            actual_q_poststep=left['joints'],
                            proposal=proposal.__dict__, resolution=receipt.__dict__,
                            actual_geometry=actual, augmented_geometry=candidate))

    # Deliberately test a BLIND transfer of this offset. This is not a proposed
    # trajectory: actual future configuration/response and bias will differ.
    # Each pose gets the native URDF limit clamp; no hidden geometry exceptions.
    transfer = []
    for index in range(len(SAMPLES)):
        args = inputs(index)
        nominal = args['q'].copy()
        args['q'] = np.clip(nominal + pi.bias, ik.LOWER, ik.UPPER)
        result = guard.check(**args)
        transfer.append(dict(index=index, phase=SAMPLES[index]['phase'],
                             nominal_q=nominal.tolist(), augmented_q=args['q'].tolist(),
                             **result))
    bad = [row for row in transfer if not row['safe']]
    report = dict(
        scope='CPU_OBSERVATIONAL_REPLAY_NOT_NATIVE_OR_CLOSED_LOOP',
        original013='cancelled_by_coordinator_before_contact; not a completed controller failure',
        measured_state_timing='nominal=original PRESTEP issued action; actual=POSTSTEP own q; hypothetical next command uses that measured state',
        bounds=dict(ki_per_s=pi.ki, bias_cap_rad=pi.bias_cap,
                    bias_rate_rad_per_s=pi.bias_rate,
                    command_step_rad=pi.command_step),
        samples=len(results),
        window_s=[rows[0]['time'], rows[-1]['time']],
        accepted=sum(r['resolution']['accepted'] for r in results),
        rejected=sum(not r['resolution']['accepted'] for r in results),
        final_observational_bias_rad=pi.bias.tolist(),
        minimum_augmented_hard_gap_m=min(r['augmented_geometry']['hard_gap_m'] for r in results),
        minimum_augmented_other_arm_gap_m=min(r['augmented_geometry']['other_arm_aabb_gap_m'] for r in results),
        final_bias_near_contact_scope_probe=dict(
            cases=len(transfer), unsafe_cases=len(bad),
            worst=min(transfer, key=lambda r:r['hard_gap_m']),
            first_unsafe=bad[0] if bad else None,
            limitation='Frozen observational replay accumulates I without plant response. Blind offset transfer is intentionally tested to show why fresh augmented-command safety must remain; this is not a candidate full-route controller.'),
        source_sha256={str(p):digest(p) for p in (
            SOURCE/'recent100-raw.jsonl', SOURCE/'recent100-diagnosis.json',
            SOURCE/'recent100-estimate.json', GUARD/'fast_safety.py',
            GUARD/'baseline_safety.py', GUARD/'route321.json',
            GUARD/'snapshot-row.json', Path(YAM_URDF), ROOT/'joint_position_pi.py')},
        native_effect='NONE; no scene, object, force, drive, controller, scorer or remote edits',
        records=results)
    (ROOT/'replay-013-report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('records','source_sha256')}, indent=2))


if __name__ == '__main__':
    run()
