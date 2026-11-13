# Historical tabbed-box evidence — superseded scene

These runs scored 1.0 for commit `bbc3a68`, which had added flap grasp tabs and
only top-seam tape. They are not full-score evidence for the handle-free revision.

To reproduce their score using the historical scorer and geometry constants:

```bash
mkdir -p /tmp/unbox-tabbed-v1
for file in config.py scoring.py replay.py; do
  git show bbc3a68:tasks/unbox-delivery/$file > /tmp/unbox-tabbed-v1/$file
done
gzip -dc evidence/tabbed-v1/full-demo.jsonl.gz > /tmp/unbox-tabbed-v1/trajectory.jsonl
python3 /tmp/unbox-tabbed-v1/replay.py /tmp/unbox-tabbed-v1/trajectory.jsonl
```

The stored audits' source hashes refer to that historical runtime. Original,
curated and compressed trace hashes are preserved in this folder's validation
record. No historical score should be reused for the revised task.
