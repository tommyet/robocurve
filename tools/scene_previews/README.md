# Native draft layout videos

These are **unscored scene previews**, not task demos. All task geometry is
fixed, the YAM arms hold READY, and there is no latch, hair/airflow, cutting,
adhesion, or task-success simulation in this recorder. No state is animated to
look like successful manipulation. The preview geometry is kept separate from
engineering task folders to avoid confusing a visual layout with implemented
mechanics. Connector dimensions and hair bundles are illustrative proxies.

On the pinned Isaac/YAM VM:

```bash
for kind in ethernet hair carton-breakdown carton-packing; do
  timeout 420 /data/IsaacLab-Arena/.venv/bin/python run.py "$kind" \
    --out "/home/ubuntu/yam-eval/preview-$kind-001"
done
```

Each trial captures 160 actual native camera frames at 20 Hz, composites the
three synchronized views, and burns the limitation into every frame. Output is
one H.264/yuv420p `preview.mp4`, plus `setup.png`, source layout and result JSON.
Only the MP4 belongs in the user's preview folder. Inspect geometry visibility
and video integrity before delivery. A success score must never be inferred
from these videos. Actual task mechanics/controller implementation remains in
the corresponding task's `VALIDATION.json`.
