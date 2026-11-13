# Anonymous numeric validation evidence

`full-demo.jsonl.gz` contains the scorer inputs from `unbox-feedback-full-002`:
measured blade/cutter/item state, flap angles, release flag and timestamps. It
contains no stored score, team identity, credentials, instruction or file paths.
Run the task's `replay.py` on its decompressed contents to reproduce score 1.0.

`full-002-audit.json` and `full-003-audit.json` record the two successful full-task
runs: source hashes, independent replay, executed command checks, final states,
and complete camera frame counts. Video files and raw trial artifacts remain
outside Git. The source hashes refer to the eight runtime/replay files listed in
the reports, not documentation or the audit helper itself.

See `../VALIDATION.json` for original, curated and compressed trace hashes,
runtime versions, historical failures and limitations. Both scored trials begin
sealed; the separately identified pre-cut diagnostic earns zero task credit.
