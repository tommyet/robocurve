# Requested robotics batch — 14 November 2026

The user authorized continuing spray corrections and developing two additional
jobs: a crowded 4x2 Ethernet panel with genuine RJ45 latch manipulation, and
even drying of long hair while manipulating a dryer. Existing bottom-tape
carton breakdown and ordinary-roll packing work remains part of the batch.
No new competition submission is authorized.

## Delivery

One composite MP4 per task, all in:
`/Users/miyamura/Github/robocurve/artifacts/task-previews/`

That folder contains only the requested preview videos. Source, telemetry,
screenshots, failed attempts and audits live elsewhere. Do not place dummy
videos or unrelated artifacts there. Label incomplete previews honestly.

## Queue

| Task | Source branch | State |
|---|---|---|
| Uncap and spray a panel | codex/uncap-spray-object | Active physical correction; cap removal works, coating not yet passed |
| Cut bottom tape, unfold and flatten carton | codex/carton-breakdown-packing | Geometry and scorer draft; no robot rollout |
| Pack and seal with ordinary tape roll | codex/carton-breakdown-packing | Material/contact/scorer draft; flush-end peeling unproven |
| Crowded 4x2 RJ45 insertion and release | codex/ethernet-hair-batch | Novelty/mechanics research and design |
| Even drying of long hair | codex/ethernet-hair-batch | Novelty/mechanics research and design |

## Working assumptions

Ethernet: eight real-size ports in two rows of four. Six neighbouring plugs
and cables crowd the work area; one marked cable starts latched in a seventh
port and must be disconnected, then inserted into the remaining target port.
Release requires depressing its clip; the inserted plug must retain after
release. Insertion naturally deflects a normal clip against the jack; do not
invent an unnecessary manual-clip rule if the actual geometry does not need it.
Do not inflate connector pitch or add convenient handles to evade crowding.

Hair: a long-haired mannequin representing a woman's hairstyle. The robot
must expose and dry front/back/under-layer regions with a handheld dryer.
Occlusion, airflow direction/distance, moisture and overheating need measured
state and explicit fidelity notes. A rigid hair sheet with painted dry colour
cannot establish this task. Native hair dynamics and real dryer grasp/switch
operation remain major feasibility questions.

## GPU coordination

Keep the spray trial active. Use one simulator at a time on the shared GPU.
Root is operating yam-eval-launchable-72837c; do not stop it or launch another
trial until the active spray session completes. Check live jobs before a later
session; this document is a record, not a lock.

## Novelty/research check (14 November)

Refreshed all-state upstream history: 1,958 PRs. No direct title/body match for
Ethernet/RJ45 latch servicing or actual long-hair drying. #860 retrieves a
plugged-in dryer from a sink; it is a different hazard task. This is not a
novelty guarantee and the authenticated board still needs a final recheck.

DataCenterBench already includes joining an Ethernet plug and coupler. Its
published candidate list explicitly left out unplugging a network cable and
notes the latch. The new task must establish real latch retention/release and
bimanual access under cable interference; a crowded layout alone is not enough
for novelty. Source: https://robocurve.org/datacenterbench/

DYMO-Hair demonstrates simulated and real-wig hair manipulation/styling, not
this drying task. Reuse its insights only after inspecting implementation and
licence; its paper is not evidence that our native hair/airflow model works.
Source: https://arxiv.org/abs/2510.06199
