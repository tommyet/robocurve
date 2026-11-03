# Pick up and roll a die — task review

Assessment date: 2026-11-03. Evaluated implementation: `6d38530`.

**Verdict:** a useful, well-instrumented first task with a successful simulated
demonstration and a clean model baseline. I would **hold submission for a scoring
revision and a simple-tool scoring check**. It is a credible candidate, but the
current evidence does not justify confidence that reviewers will accept it.
No competition PR has been opened or authorized; media upload is also pending.

## What we built

The robot must pick up a small blue cube, release it so it tumbles like a die,
and leave it untouched until it stops. The intended application is assisting
with tabletop games; category: **Societal relevance**.

| Item | Specification |
|---|---|
| Robot and simulator | Calibrated two-arm YAM station; Isaac Sim 6.1 / Isaac Lab-Arena. |
| Die surrogate | One blue, unmarked, sharp-edged 16 × 16 × 16 mm cube; mass 5 g. |
| Table | 1.10 × 1.30 m; surface z = 0.7475 m, centre x = 0.36 m, y = 0. |
| Initial cube pose | Centre (0.20, 0.16, 0.7555) m; identity orientation. |
| Trial settings | Fixed layout, seed 0, no object jitter; 20 Hz actions/audit, 240 Hz physics. |
| Allowance | 1,200 actions / 60 simulated seconds per episode. |
| Fidelity | Primitive collision/friction defaults; no rounded edges, pips, numbered outcome or calibrated physical-die friction. |

The scorer awards **0.25** for a verified pickup held at least 30 mm above the
table for 0.20 s; **0.5** for verified release and at least 90 degrees accumulated
tumble; **1.0** for that roll followed by one second of stable rest on a face.
Falls outside the table bounds or renewed hand proximity after release erase
credit. Pure vertical-axis spin and rotation while held earn no roll credit.
Exact speed, clearance and rest predicates are in
[scoring.py](../tasks/roll-a-die/scoring.py) and
[task.json](../tasks/roll-a-die/task.json).

## What actually happened

| Evaluation | Result | Simulated time | Runner wall time |
|---|---|---:|---:|
| Scripted demo, trial 004 | **1.0**; pickup at 4.60 s, release at 8.00 s, 164.434 degrees tumble and 1.00 s rest. | 9.30 s | 321.206 s, including shader compilation. |
| Dream-1 clean baseline | **0.0**; no verified pickup; 25 requests in one session, no retries. | 60.00 s | 197.996 s |

The demonstration commands only robot joints/gripper; it does not teleport the
cube. Replay matches both recorded scores, joint speeds stayed within the
published limits, and the videos were visually reviewed. All 32 scorer/bridge
tests passed. The earlier Dream run suffered repeated session expiry and is
excluded as the baseline. Development attempts changed the demonstration;
there is only **one successful run of the final version**, not a measured success
rate or a real-robot demonstration.

At the observed Brev rate, the clean Dream run estimates $0.18 and the final
demo $0.29, excluding separate Dream API charges. Initial setup and debugging
are additional; the complete first session had $3.05 posted spend at the last
billing check and a conservative $4.43 elapsed-time estimate. These are not
settled billing figures. See [shared cost notes](../TEAM_LEARNINGS.md).

## Is it a roll, and is it random?

**Yes, it demonstrates the simulated robot picking up, freely tumbling and
settling a die-shaped object.** The 164.434 degrees is accumulated tumble, not a
complete revolution; net orientation change relative to vertical from release
to rest was 103.204 degrees. An earlier attempt managed only 30.274 degrees.

**Randomness is not tested or deliberately introduced.** With the same initial
state and scripted motion, we expect similar results, but have not tested exact
repeatability. Numerical physics differences may occur. The cube has no face
labels, and no evidence establishes varying outcomes, equal face probabilities
or fairness. Those would require a separately designed repeated-trial study.

## Acceptance assessment

The competition requires importance, construct validity, simple unambiguous
scoring, reproducibility and feasibility; see [AGENTS.md](../AGENTS.md).

| Criterion | Current assessment |
|---|---|
| Importance / novelty | Plausible tabletop-assistance relevance. Prior November 3 checks found no direct duplicate; coverage was limited and must be refreshed. A generic small-object toss may be judged insufficiently distinctive. |
| Construct validity | The recorded motion supports a tumbling release. The claim must remain physical manipulation, without implying random/fair dice play. Physical friction and grip realism remain uncalibrated. |
| Scoring | **Main concern:** cumulative tilt can reward small rocking. An offline trace alternating ±10-degree tilts reaches 120 degrees accumulated rotation and full score after rest without a large turnover. This is a synthetic counterexample, not a demonstrated physical exploit. |
| Reproducibility / clarity | Fixed dimensions, pose, seed, versions, source snapshots and numeric logs are strong. Telemetry-based acceleration and jaw-clearance checks need an ordinary-camera scoring equivalent, especially for a blank symmetric cube. |
| Feasibility | One full-score simulated demo supports feasibility within the allowance. Repeated success, sensitivity and physical-robot performance remain untested. |

Before recommending submission: add a meaningful turnover condition and its
regression test; check that a person can apply the rubric from ordinary video;
then repeat the demo and Dream evaluation under any revised scorer. Refresh the
novelty check and upload the prepared media. Preserve existing results as
versioned evidence. **Even after those checks, acceptance remains the reviewers'
decision; do not submit without the user's explicit instruction.**

Run commands and full implementation details:
[task README](../tasks/roll-a-die/README.md). Local, git-ignored evidence:
`artifacts/die-debug-004/`, `artifacts/die-dream-002/` and final media in
`artifacts/roll-a-die/`. These files are not downloaded with a Git clone.
