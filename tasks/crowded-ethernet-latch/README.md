# Service a crowded 4x2 Ethernet panel

Native mechanics and robot controller under development; no completed task demo yet.

Unlatch the marked RJ45 plug from its current port without breaking the tab,
then insert it into the marked empty port and leave its latch engaged. Six
other connected cables crowd the eight-port, two-row/four-column panel. Their
plugs must remain seated. A second arm may move a flexible neighbouring cable
aside to reach the clip; no added handles or enlarged port pitch.

Native geometry must reproduce a plug shell, flexible spring-return latch,
retention hook and jack ledge. Pulling an engaged plug must physically resist;
pressing the tab must clear that ledge. Insertion must deflect and re-engage a
normal latch through contact, rather than toggle a boolean when a plug crosses
a distance threshold. Actual plug/cable orientation and clipping clearance must
come from a selected connector drawing before the dimensions are frozen.

Proposed checks: source-port clip depression before withdrawal; target plug
alignment and seating; clip re-extension into the target retention recess;
released retention, neighbouring connections undisturbed, tab intact, cable
not severed or overstrained. All measures need native pose/contact readback.
The controller attempts clip release and transfer, but current trials score 0.0: the plug has not been successfully disconnected and retained in the target. No successful demo or media ID is claimed.

DataCenterBench already joins an Ethernet plug and coupler and its discarded
candidate list mentions network-cable latch release. Real release/retention
mechanics and bimanual cable obstruction are the intended distinctions, not
merely eight connectors instead of one. See the batch record for sources.

## Current native tests

`run.py` builds actual open sockets, passive spring clips with retaining hooks,
and jointed cable chains. Connector geometry is explicitly approximate and
needs calibration against a selected product; it is not licensed vendor CAD.
The switch is fixed on a stand; plugs and cables have real rigid-body dynamics.

```bash
/data/IsaacLab-Arena/.venv/bin/python run.py --mode retention-probe --out /path/to/new-run
/data/IsaacLab-Arena/.venv/bin/python run.py --mode release-probe --out /path/to/new-attempt
```

Retention probes apply external bench forces and cannot receive task credit.
Release attempts use bounded normal robot joint/gripper commands and privileged
native telemetry, never object pose writes or software latch-release toggles.
Actual source release, target alignment, clip return, six neighbours and a
2-second released retention hold determine scoring. Controller phase names do
not establish success. A failed physical precondition stops the attempt.

Every output freezes its Python sources and contact-point JSON. Require a real
`result.json` and no `error.json`; Kit shutdown can swallow an exception and
return exit code 0. Videos and traces are diagnostics unless final scoring and
visual review establish full completion. See `VALIDATION.json` for evidence.

### Physical-layout reference correction

The early 28 mm prototype pitch was only a mechanics scaffold and is superseded.
Horizontal pitch is now 16.26 mm, with a 65.91 x 27.30 mm 2x4 housing envelope
referenced to the public Amphenol RJE7K drawing. Vertical pitch remains a
13.72 mm procedural approximation pending visual drawing verification. The
retaining ledge, flexible clip and unbooted plug details are original approximate
geometry, not vendor CAD or a standards certification. The source/target are
the lower/upper ports of the outside column; six other cables remain connected.
Source: https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/p-rje7k-888-1xx0.pdf
