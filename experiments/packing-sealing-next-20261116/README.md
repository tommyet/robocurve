# Packing/sealing next — CPU diagnosis, 2026-11-16

Native closure002 has203 rows/10.15 simulated seconds, score0 and no meaningful
flap motion. Trace SHA256:6618b2634fbbc13fd3b6342685c534bf905475bc4ee27d7cd97cf5266faffd13.
The process was interrupted by wall timeout, not a reported controller exception.

`replay_stall.py` reconstructs the planner using the earlier LOGGED guard results
and actual native joint/object states. This is not independent validation of all
203 earlier guards. It then independently recomputes the final pre-action state
at10.10s with real IK and every315 URDF collider piece. Maximum reconstructed
command difference from the applied native float32 trace is1.55µrad. The compact
fixture/report records exact measured prestate and reconstructed planner state.
`test_stall_fixture.py` independently rebuilds that final prestate and has TWO
passing tests: numeric guard rejection/transaction rollback and preserved
engagement deadline. No geometry or IK is mocked in these final-state tests.

The causal obstruction is the intended LEFT fingertip/east_top ISSUED proxy
depth bound−1mm, not collision with another flap:

- Measured intended gap≈−0.0215mm; measured geometry is safe.
- Previous issued intended proxy gap−0.965899mm, almost at the limit.
- Full next proposal gap−2.096854mm; fractions0.5/0.25/0.125/0.0625 give
  −1.531477/−1.248713/−1.107312/−1.036607mm. Every candidate violates−1mm.
- Unrelated geometry stays≥1.398888mm; opposite arm separation≈298.6mm.
- Therefore the controller holds its previous target, rolls back proposed PI and
  command-angle changes, and returns advance0 while actual hinge stays≈−174.96°.
- Rejection does not extend the original3s measured-engagement deadline.

This identifies a positional/contact command bottleneck; geometric depth is not
contact force and does not demonstrate motor insufficiency. No physics, gains,
scoring, tape form factor or initial open-flap/preloaded layout was changed.
Astra recommends screening an ordinary broad-face push with a real mesh support
witness across the entire hinge arc before implementing a new runtime strategy.
No GPU/start/SSH was used. Task source is unchanged.

CPU commands (with pinned YAM source accessible):

    PYTHONPATH=/private/tmp/spray-yam-source /private/tmp/robocurve-usd-env/bin/python experiments/packing-sealing-next-20261116/replay_stall.py --source /path/to/continue-packing-closure-002 --out experiments/packing-sealing-next-20261116/closure002-fixture-report.json
    PYTHONPATH=/private/tmp/spray-yam-source /private/tmp/robocurve-usd-env/bin/python -m unittest discover -s experiments/packing-sealing-next-20261116 -p test_stall_fixture.py -v

## Central-width broad-face CPU search (negative result)

A normal-oriented family (yaw0/90/180/270°, tilt0/±30/±45/±60°,
radius45/55/65mm, both arms for inner flaps and near arm for outer flaps)
ran504 initial candidates: no initial IK solution from the READY seed.
`face-push-normal-family.json` preserves this result. This is a finite sampled
family/local-IK result, not an exhaustive impossibility proof.

The expanded side-pad family adds tilt±75/±90° and independent toolroll
0/90/180/270°, with READY plus actual native arm seeds. Across1152 candidates,
none passed initial full315 geometry. Valid IK but rejected actual mesh guards:
112 east,32 west,16 north,16 south; remaining candidates failed IK or the5mm
finite face-edge margin. `face-push-side-family.json` preserves all outcomes.
The exact toolZ-parallel-hinge sidepad orientations are reachable but the real
outer sidepad support is47.05mm away from TCP; placing this support on the centre
of the underside lowers the TCP and causes forearm/link3 overlap with the
north/south neighbouring flap (about35mm). Several support witnesses consist
of85–170 real mesh vertices and retain20mm or more face-edge margin: this is a
credible contact patch with an independently unsafe unrelated-link path.

No candidate reached a safe complete contact arc, so no ready/approach/retract
route or runtime was authored, and no native attempt is justified by this
search. The script retains all315 robot pieces and all tape/roll/products/
cutter/finite-thickness flap geometry. Prior flaps are hypothetically closed
in inner-before-outer order, only for CPU planning; no actor was moved.

Potential further work requires reviewed geometry: a lateral near-rim distal-tip
contact with wider finger portions outside the finite face, or a different
force-backed rim strategy. The global sidepad support plane used here must not
be silently replaced by a tip point while overlooking the rest of the finger.

## Reviewed face-push candidate checkpoint

All four sampled push/withdrawal/fall/park routes have been checked locally.
North/south use above-box standoff, unrelieved high/side hover, a separate2mm
normal relief, free lateral entry, then normal approach. Both active-flap
endpoints−175/−174.5deg and unrelated-open-neighbor endpoints pass. Previously
closed flaps are modeled exactly0deg; runtime keeps fresh actual-scene guards.
These are finite CPU samples, not continuous clearance or native success.

Root packing suite:93tests PASS; separate mesh/replay experiments:5tests PASS.
Astra approved one bounded EAST-only diagnostic after runtime review. No native
closure or sealing is demonstrated by these CPU results. The ordinary tape roll
still needs acquisition, payout, adhesive application, cutting and retention.

The full positive/negative numeric reports are preserved compactly in
`cpu-reports.tar.gz`; extract them here before rerunning route scripts:

    tar -xzf cpu-reports.tar.gz

Raw JSON stays ignored except the compact replay fixture and benchmark summaries.
All experiment code and team notes stay outside any future task-only submission.
