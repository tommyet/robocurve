# Joint-position PI candidate: CPU only

`joint_position_pi.py` is a reusable outer-loop correction for ordinary six-joint
targets. It is not installed in the frozen opening coupon, SDK, or production
policy. No GPU, force, object pose, scorer, collision threshold, mechanical gain,
or active source was changed.

The helper consumes only an **unbiased nominal joint target**, measured joints
of that same arm, a monotonic control clock, previous issued command, and supplied
joint limits. It imports only NumPy, dataclasses and math. Simulator geometry and
object data are used only by the separate observational replay/audit script.

## Command contract

Defaults: Ki = 0.5/s; integral offset capped at +/-0.02 rad per joint; offset
increment capped at 0.005 rad/s (0.25 mrad per 50 ms); command change capped at
the original 0.04 rad per tick. Nominal and emitted commands respect the caller's
URDF joint limits. Measured physical joints may overshoot a limit; they must be
finite, while all emitted targets remain bounded. This changes outer target
selection, not a native articulation drive's stiffness, damping or force limit.

```python
pi = JointPositionPI(urdf_lower, urdf_upper)
pi.begin(last_issued_14d[:6], time_s)

# On each 20 Hz call: nominal_q comes from the UNBIASED path/IK reference.
proposal = pi.propose(nominal_q, own_measured_q, time_s)
candidate14 = last_issued_14d.copy()
candidate14[:6] = proposal.command

# Check the EXACT candidate after every applicable limit/clamp, together with
# fresh actual geometry. If any downstream operation alters these six targets,
# reject rather than committing a command that was not actually issued.
safe = bool(actual_315_piece_guard() and augmented_315_piece_guard(candidate14))
receipt = pi.resolve(proposal, guard_safe=safe)
issued14 = last_issued_14d.copy()
issued14[:6] = receipt.command

# This is eligibility, not permission to bypass existing tracking/progress gates.
if existing_tracking_and_progress_gates:
    accepted_path_clock += receipt.path_dt_s
```

The helper preserves the first six issued joints **exactly**, even when the new
nominal target differs. First handoff, duplicate clocks, invalid state, rejected
geometry, and slew-clipped commands contribute zero path time. No other arm or
finger entry is changed by this six-joint helper. A caller must preserve the rest
of the 14D action itself.

Proposals and resolutions contain immutable tuples. Only the exact outstanding
proposal may resolve. Guard rejection commits neither bias nor issued targets.
The observed wall clock still advances, so rejected intervals never accumulate
as catch-up integration on a later accepted tick. Invalid state latches a held
command failure until explicit `begin`; the caller should halt its motion path.

The integral uses **nominal - actual**, never issued/augmented - actual. Conditional
anti-windup discards an outward increment when its command would exceed a joint
or per-tick action limit; inward unwinding remains possible. The bias is added
once. Do not derive a new nominal pose from augmented-command FK and then add
the same offset again. Phase continuity, reference ownership, bias transfer and
reset points still need review when integrating with a real controller.
In particular, `begin` sets bias to zero: it preserves the old command on the
first tick, not an arbitrary pre-existing loaded bias on all later targets.
Start the new nominal trajectory continuously from that issued q, or review an
explicit inherited-bias handoff before supplying a different unbiased reference.
If fresh actual or candidate safety fails, the caller must halt/abort its path;
retaining a previous command is not itself proof of a safe physical hold.
Runner integration must check a controller failure immediately after `command`
and **before** `env.step`. Frozen `open_run.py` currently checks at loop bottom,
after stepping once; that ordering must be repaired in a separately reviewed
candidate before using this abort contract. The frozen runner is unchanged.

## Evidence and limits

Nine focused unit tests pass. They exercise a biased lagged plant including the
observed 8.35 mrad joint-six load offset, convergence within 5 microradians after
20 synthetic seconds, command/offset bounds, joint-limit and slew anti-windup,
rejection/clock recovery, exact loaded first command, duplicate clocks, stale
transactions, invalid-state holds, and zero integration when nominal error is
zero despite a nonzero augmented target. A linear lag plant is not a native
stiction or contact-stability proof. Ki, offset slew and any velocity damping
need an agreed native diagnostic before production use.
Astra independently passed the nine tests and reviewed the pure helper at
source hash `50e463323228bec1387ad6204761af12d88f23ac5af0732552e9c6bc15e26422`.
This is a helper-only review, not controller integration, route or GPU approval.

`replay_013.py` is an **observational** replay of the latest 100 recorded 013 rows
(23.00–27.95 s). The original 013 run was deliberately cancelled before contact;
it is not relabeled as a completed controller failure. Original issued q is the
unbiased nominal input because that frozen controller had no PI. POSTSTEP own
joint q is the measured input to a hypothetical next command. These recorded
measurements cannot respond to hypothetical commands, so this replay cannot
establish convergence or stability: joint-six I reaches its -20 mrad cap.

All 100 replay candidates pass fresh actual and augmented-command 315-piece
checks in those recorded **free-space** scenes, with at least 1.3989 mm hard
clearance and 222.6 mm other-arm AABB separation. No precontact target exception
was added. These are sampled command geometry checks, not swept/substep proof.

Blindly applying the final observational offset to all 321 old route poses
produces **three unsafe underedge-insert poses**; the worst tip_right/north_bottom
overlap is 3.533 mm, with the flap still a hard obstacle. This deliberate scope
probe is not a proposed path or native prediction. It shows why the actual and
exact augmented-command guards must remain and why the old coupon contact route
cannot be assumed valid with compensation. This helper makes no full-opening
feasibility claim.

## Reproduce

The pure helper/tests need Python 3.10+ and NumPy:

```sh
cd /private/tmp/carton-proprio-tracking
/private/tmp/robocurve-media-env/bin/python -m unittest -v test_joint_position_pi.py
```

The separate replay additionally reads the pinned local YAM and guard candidates:

```sh
/private/tmp/robocurve-media-env/bin/python replay_013.py
```

`PROVENANCE.json` pins external inputs, URDF, guard and unchanged frozen source.
`MANIFEST.json` binds this candidate's files. All work remains an isolated scratch
candidate with helper-only review; no task branch or native runner uses it.
