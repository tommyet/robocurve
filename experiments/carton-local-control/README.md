# Local carton controller experiments

CPU-reviewed helpers, not integrated into a native task or competition submission.

- `proprio-tracking`: transactional, bounded correction of ordinary joint targets using only the arm's own joint positions. Nine tests and Astra code review passed. Geometry rejection must abort before advancing native physics; holding a previously issued command is not a new safety certificate.
- `geometry-guard`: exact batching of all existing315-piece/15-box checks. All321 route and12 negative cases matched the baseline, with6 focused tests. Measured warm CPU workload improves2.855x, not a native simulation speedup claim.

Dependencies: NumPy; geometry code additionally needs the pinned YAM adapter/assets described in the included provenance. Captured replay inputs and geometric hypotheses are development evidence only. No object poses, native drive gains, task scores, collision thresholds or production policies were changed. The original post-cut013 diagnostic was cancelled before contact because its100s controller allowance would be exhausted by actuator tracking lag; its data does not demonstrate opening.

The adaptive opening search and physical carton reorientation remain separate, unproved work. GPU remains stopped until there is a viable test.
