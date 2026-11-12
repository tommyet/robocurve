# Remove a staple without tearing the papers

**Development package — not ready to submit.** A contact/material probe exists;
a complete deformable paper/staple scene and successful robot trial do not. No
simulator or Dream run has occurred, and a $3 completion cost is not established.

The task is to remove a clinched staple from two sheets, keeping both sheets
usable. The robot must support thin paper, engage a remover under the fastener,
unbend its legs and withdraw them through the existing holes.

## Implemented and checked locally

- Rectangular steel wire bending with irreversible plastic set and hardening.
- A unilateral jaw-contact probe: a moving diagnostic jaw bends one 3 mm
  clinched leg. A jaw passing outside the leg has no effect; withdrawing the
  jaw leaves a permanent bend. Doubling wire thickness increases resistance.
- An irreversible paper cohesive-opening law whose force/opening integral
  equals its specified fracture energy. Closing a torn bond does not heal it.
- An installed staple centreline with a 12.8 mm crown and two inward-bent ends.
- A lazy native PhysX angular-drive material hook. It uses measured joint angle
  to update the plastic rest angle; it has not been exercised in Isaac.
- A native diagnostic scene with the 3 mm wire leg, physical hinge and a
  contacting jaw; it is authored but not yet run.
- A photo/ruler judging procedure and fail-closed scorer.

These are **separate, uncalibrated probes**, not a coupled extraction simulation.
The jaw probe fixes its root instead of modelling the paper hole. It cannot
show whether paper survives, whether a whole staple is removed, or whether a
robot can do it. Its 5.865 N peak jaw force and residual 0.928 rad bend are outputs
of the chosen numerical parameters, not measured properties of a real staple.

## Reproduce the CPU checks

```sh
.venv/bin/python -m unittest discover -s tasks/remove-a-staple -p 'test_*.py' -v
.venv/bin/python tasks/remove-a-staple/probe.py --out tasks/remove-a-staple/evidence/material-probe.json
.venv/bin/python tasks/remove-a-staple/contact_probe.py --out tasks/remove-a-staple/evidence/contact-probe.json
```

The NumPy-only checks take under one second on the development machine, use no
GPU/API/network and contain no randomness. Full trial runtime is unknown.

On the funded existing Isaac environment, from the repository root:

```sh
python tasks/remove-a-staple/native_probe.py --out artifacts/staple-native-001 --dt 0.0001 --seconds 2
```

This native coupon has no paper. A kinematic diagnostic jaw contacts a dynamic
steel leg; only contact can move it. The measured joint angle updates a plastic
rest angle after yield. Compare the recovered angle at half the time step
before trusting the material coupling. Kinematic jaw motion is a diagnostic
test fixture, not a robot demo. No full-task success is claimed by this entry
point. Native [stepping](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/simulation_control/simulation_control.html)
and [drive units](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/rigid_bodies_articulations/joints.html)
follow NVIDIA's documentation; compatibility with the retained installation
still needs an actual run.

## Blocking work before a robot or Dream trial

The defining interaction needs a coupled 3D solver with thin deformable sheets,
four original puncture holes, steel-wire plasticity, jaw leverage, self-contact
and irreversible crack growth around those holes. Rigid paper plates or a
staple that detaches when a remover is nearby would omit the task.

The existing native PhysX chain pattern can represent a bending wire, but does
not by itself provide tearable 100 µm paper. A coarse panel sheet risks leaving
gaps larger than the staple, and ordinary millimetre-scale collision offsets
are larger than the entire two-sheet stack. This contact-scale issue must be
resolved without enlarging paper thickness or replacing paper by rigid cards.
The plastic drive hook also needs time-step convergence checks and contact
force/energy checks before use.

`PAPER_SOLVER_PLAN.md` specifies the remaining thin-shell, puncture-contact and
irreversible crack-propagation work, including contact resolution and destructive
control cases. The nominal reset starts the flat stapled stack 0.5 mm above the
table, keeping the clinch clear, then requires physical settling before control.
No rigid-paper replacement or interpenetrating tabletop reset is acceptable.

The deterministic proposed geometry and layout are in `setup.json`. Select and
measure matching actual staple/remover and paper; calibrate wire yield,
paper bending, tear propagation and friction. Then establish a matching reset,
robot reach, a camera/joint-feedback or open-loop successful demo, and an
ordinary Dream baseline. Final scoring must inspect both faces of both sheets.

Accepted [cord cutting](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/cut-taut-cord)
uses measured blade/cord contact force to drive material failure. Accepted
[filing](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/file-a-steel-block-flat-down-to-a-scribed-line)
uses a before-substep material model. Their causal contact structure informed
this package; neither establishes that our uncalibrated paper model is valid.
