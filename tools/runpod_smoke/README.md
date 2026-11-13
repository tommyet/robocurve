# Runpod compatibility smoke test

This tests the pinned Isaac 6.1 / Isaac Lab / YAM environment used on Brev.
It makes **no Dream requests** and does not create or stop cloud resources.
The script is a platform diagnostic, not a full-score task demonstration.

Use a fresh Linux x86-64 **Ubuntu 24.04** container on one full RTX-capable GPU
(L40S or RTX 6000 Ada, 48 GB), with at
least 32 GB RAM, 4 vCPUs and approximately 100 GB free working storage. A minimal
`ubuntu:24.04` image is suitable if the Pod entrypoint keeps it alive and SSH or
the Runpod command API is available. Host NVIDIA driver and graphics passthrough
must already work; the bootstrap cannot install a host kernel driver. Configure
`NVIDIA_DRIVER_CAPABILITIES=all` at Pod creation. Do not nest Docker/Compose.

Before launch, arrange a separate, supervised control-plane stop deadline and
estimate hourly/storage prices. Check the returned rate immediately after
creation and stop if it exceeds the session budget. These local process timeouts do not
release the GPU and are not a spending cap. Do not rely on ending SSH or stopping
Python to end billing.

Copy the repository without secrets or old artifacts into `/workspace/robocurve`.
The commands below install into `/workspace/robocurve-sim`, then run 150 control
steps (7.5 simulated seconds). Setup is capped at 25 minutes; the simulator
subprocess is capped at 10 minutes plus 20 seconds to close.

```bash
cd /workspace/robocurve
bash tools/runpod_smoke/bootstrap.sh
/workspace/robocurve-sim/IsaacLab-Arena/.venv/bin/python \
  tools/runpod_smoke/smoke.py --out /workspace/runpod-smoke-001
```

The bootstrap uses Arena's frozen lock, exact recorded Git revisions and package
versions from `tasks/use-a-magnifying-glass/ENVIRONMENT.json`. It deliberately
reproduces the recorded NumPy 2.5.4 overlay, which differs from Arena's base lock;
a failure must be reported rather than silently changing the target environment.
Only the required Isaac Lab submodule is initialized. It does not install the
old separate Isaac 5.1 environment, desktop services, a Dream key or launchable
autostart jobs. Dream client packages are installed solely to match the recorded
environment and are never instantiated.

The diagnostic uses the existing die scene and bimanual YAM hardware. It raises
the die's initial pose by 12 cm once, observes its gravity-driven fall and table
contact, and commands a small smooth arm-yaw excursion with open grippers. All
subsequent steps use normal joint targets. Pass conditions require finite live
states, measured die drop and settled table support, actual arm movement, 20 Hz
control, and nonblank RGB from all three native 640×360 cameras. The moving
left wrist camera must change across frames; the stationary right camera is
allowed to remain still. The adapter's 224×224 policy images are checked against
native-camera resizing at the start and end. Vulkan visibility is checked before
the large simulator download.

`result.json`, `trace.jsonl`, `smoke.mp4`, six native camera screenshots and
`simulator.log` are written in a new output directory. Inspect images/video and
logs as well as numerical checks. First-run shader compilation and large package
downloads can exceed a short test budget. Stop on installation/driver/render
failure rather than retrying indefinitely. This probe does not establish cloth,
seam cutting, icing mechanics or any of the six tasks' full-score feasibility.

Download evidence and `installation.json`, then stop the Pod and independently
confirm its control-plane state and account-wide running resources. Persistent
storage still incurs charges after stopping.

## Verified run — 13 November 2026

[The recorded result](verified-2026-11-13.json) passed on an RTX 6000 Ada 48 GB
with driver 595.91.07. All pinned versions matched. The 150-step probe took
35.45 seconds after installation; it rendered all three cameras, matched YAM's
policy images, moved the arm, and measured the die falling 12 cm and settling.
This is platform evidence, not a submission demo or a cloth-physics test.

Use a current workspace-local uv: the tested base image's uv 0.9.0 did not know
Python 3.12.16, while uv 0.13.8 did. `libxt6` is needed for Isaac's MaterialX
libraries. The bootstrap includes both fixes. The API command endpoint was
restricted for the tested key; ordinary authenticated direct SSH worked.
The test Pod was confirmed stopped after evidence was downloaded. No Dream
calls or persistent volumes were used. Ephemeral installation files must be
recreated after restart.
