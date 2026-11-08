# Shared working notes

Last updated: 2026-11-08 UTC. Read this before starting work; update it when an
experiment changes what we know. This is a shared operating record for both
developers and their agents, not a competition submission document.

## Agreed workflow

- The team fork's `main` is the shared development baseline. New work starts
  from current `origin/main` on a `codex/` branch. Competition submission branches
  start from fresh `upstream/main` and receive only one validated task folder.
  See the [team quickstart](README.md#team-quickstart) for agent onboarding.
- Commit and push completed work to this fork. Do not open a competition PR
  until the user explicitly asks. The user explicitly authorized media upload
  and the die-task PR on 2026-11-03, then the four brick-task submissions on
  2026-11-04. Future tasks still need explicit submission authorization. Keep each submission branch limited to its task folder.
- `submission/roll-a-die` was submitted from the fork to upstream `main` as
  [PR #44](https://github.com/robocurve/benchmark-tasks/pull/44), commit `ba4ac81`.
  Its diff contains only `tasks/roll-a-die/`. It received a final rejection on
  November 5; preserve the submitted task as evidence and do not reopen it.
  Record follow-up notes on `roll-a-die`, outside the submission branch.
- The user confirmed upload team `T-39`. The private `.env.robocurve` stores
  `ROBOCURVE_TEAM` and a single-quoted `ROBOCURVE_TOKEN`. Parse the quoted value
  without displaying it; do not mistake empty quotes for a configured token.
- Before eventual submission, rescore the final demo/Dream evidence with the
  final scorer. This is complete for the final marked v3 demo/Dream evidence. Fresh
  GPU repeats are an additional confidence check, not an explicit competition
  requirement after a scorer-only change. Earlier notes incorrectly elevated
  them into a mandatory gate; do not repeat that interpretation.
- Reuse **one Brev VM**, currently `robocurve-dice`, while working daily.
  Prepare several tasks locally and batch their GPU trials in one session.
  Initially run simulator trials consecutively, rather than starting competing
  simulator processes on the same GPU.
- Before using the shared VM, check its live state and coordinate with the other
  developer. Record the operator, task/branch, intended runs and completion in a
  dated session entry here. Git notes are not a lock or a live status service;
  do not stop a VM while someone else's trial is running.
- Do scene design, scoring tests, trajectory analysis and documentation locally
  where possible. Start the GPU when a batch is ready. Download results, push
  code and confirm the VM reaches `STOPPED` when the session is finished.
- The user permits the **Dream API key on the team VM** when useful. Transfer it
  without displaying its contents; restrict file access and keep it outside Git,
  logs and artifacts. This approval does not require another confirmation next
  session. Direct Dream access should remove the Mac/SSH bridge dependency;
  direct execution is now verified. The key was transferred on November 3
  into an owner-only credentials file outside Git and logs. The final direct
  Dream run used one session with no retries; scene/rendering also changed, so
  its timing is not an isolated transport speed comparison.
- Keep the five private reference/application PDFs, credentials, `.env*`,
  generated media and full trial artifact directories ignored. Curated anonymous
  numeric traces may be committed inside a task as review evidence after a
  content check; the die task includes five such compressed traces (two current
  v3 runs and three historical runs). See
  [.gitignore](.gitignore).
  This repository is public: do not add account tokens or private application
  content to this log. Keep task text and submitted media anonymous.

## GPU cost and persistence

Observed on 2026-11-03: L40S, 48 GB VRAM, 256 GiB allocated disk. Running rate
**$3.28/hour**, comprising $3.23 compute and $0.05 storage. These are observed
rates for this instance, not guaranteed future prices.

| Quantity | Planning value | Meaning |
|---|---:|---|
| 10 minutes running | $0.55 | Elapsed instance time, including idle gaps; excludes separate Dream API charges. |
| $2 running budget | About 37 minutes | A target, not a user-imposed hard cap. |
| Storage while stopped | $1.20/day | The whole allocated disk, shared by all tasks on this VM; not per task. |
| Clean Dream trial | $0.18 | 197.996 seconds of measured runner wall time, prorated at $3.28/hour. |
| Initial cold installation | About 40 minutes | First environment installation/warmup; excluded from per-trial numbers. |

The actual build configuration is VM mode (`environment.build.vm`, with an
`on_create_script`). Legacy API flags such as `vmOnlyMode` were misleading.
According to [Brev's launchable documentation](https://docs.nvidia.com/brev/concepts/launchables),
the VM setup script does not automatically rerun on restart. The retained
installation should therefore be reusable; boot and simulator initialization
still recur. **Restart and installation reuse were verified later on November 3.**
The environment survived and the marked-die demos each took about 44 seconds
including simulator startup. Two earlier restart attempts at 13:08 and 13:11 UTC
failed because no GPU capacity was available in the existing region. Stopped data remained inaccessible; local
backups allowed scoring work to continue. Retaining a disk does not reserve a GPU.

Stopping ends compute charges but retains storage. Deleting ends the instance's
charges and removes its data and installation. Copying files locally does not
cancel the allocated disk. See [Brev lifecycle and persistence](https://docs.nvidia.com/brev/concepts/gpu-instances).
Keep the VM between daily sessions as agreed; reconsider retention for longer
gaps. Do not delete it as a routine cleanup step.

Code, final videos, setup images and measured trajectories are already local.
The original raw camera arrays and installed simulator remain on the VM. Before
any later deletion, identify and back up anything still needed. A fresh VM needs
setup again; restoring a full archived environment has not been tested.

Billing snapshot at 12:24 UTC on 2026-11-03: $196.95 of the initial $200 remained
($3.05 posted spend). Billing may lag. Creation through confirmed shutdown at the
displayed running rate gives a conservative **$4.43 estimate**, not an invoice.
Do not add overlapping per-run estimates to this total. Dream API dollars were
not reported by the SDK and remain unknown.

## What the first task taught us

The implementation and run commands are in
[tasks/roll-a-die/README.md](tasks/roll-a-die/README.md); the candid submission
assessment is [docs/roll-a-die-review.md](docs/roll-a-die-review.md).

| Finding | Evidence | Reusable lesson |
|---|---|---|
| Full gripper closure caused vibration around the 16 mm cube. | Trial 001: score 0. | Check contact behaviour visually; reachable poses alone do not prove a grasp. |
| A gentle 15 mm target jaw gap enabled stable pickup. | Trials 002 onward. | Tune grasp pressure/closure before adding a dynamic release. |
| Rotation about the jaw-closing axis transferred little tumble. | Trial 003: 30.274 degrees, score 0.25. | The wrist rotation axis relative to the grasp matters. |
| An upward stroke, world-X rotation and delayed opening produced a roll. | Trial 004: 164.434 degrees, score 1.0 in 9.30 simulated seconds. | Use measured release and object motion, not intended actions, as evidence. |
| A second simulator startup encountered a shader-cache miss. | Trial 004 wall time 321.206 s; earlier short trials 46–73 s. | Start serially initially; measure concurrency before assuming it saves money. |
| Per-tick remote bridge traffic caused Dream session expiry. | First Dream attempt: 49 attempts, 25 sessions, 24 expiries. | A completed evaluation can still be infrastructure-confounded. Inspect sessions and retries. |
| Batching observations fixed that transport problem. | Clean baseline: 25 requests, one session, zero retries; score 0.0. | Use the clean result, preserve the failed attempt as development evidence. |

The batched bridge preserves observation order, timestamps, states, prompt and
the model's frame window. Ten bridge tests, including real HTTP transport and
comparison with the Dream client, passed. The original version also passed twenty-two scorer tests.
Tests do not establish physical realism, repeatability or acceptance.

The runner records cube position, quaternion, linear/angular velocity and
measured hand state every **50 ms**; physics runs at 240 Hz. Scores can be
replayed from `trajectory.jsonl` without a GPU. Keep the final score, rather than
the best historical score, so later violations erase credit. Record source
snapshots, versions, seed, setup image, final videos and runtime for each trial.
Use a new artifact directory for every attempt; do not overwrite evidence.

The scene uses seed 0, no object jitter and a fixed scripted demonstration.
This establishes a simulated manipulation example, not a random/fair die or a
measured repeat-success rate. The November 7 updated-simulator rerun matched the
original v3 demo numerically; this does not establish determinism across other
hardware or configurations. V3 adds 1–6 pips for tracking faces; it still does not request a particular
result or measure outcome fairness.

## Die task findings and next checks

- **V3 is current.** Six coloured pip-marked faces replace the blank cube.
  Pickup earns 0.25, visible release 0.5, and a post-release marked-face up→down
  sequence plus one second of rest earns 1.0. Exact thresholds are in the task.
  This replaces v2 acceleration/clearance predicates with pose/time checks.
- Final fresh recordings: `die-v3-demo-002` scores 1.0 after 182 actions / 9.10 s;
  `die-v3-dream-002` scores 0.0 after 1,200 actions / 60 s. All 48 tests pass. Both
  trajectories are independently rescored and committed anonymously with source
  hashes in `tasks/roll-a-die/VALIDATION.json`. Prior v2 evidence is historical.
- The review camera must be above the cube enough to see the upward face.
  A low oblique view hid cyan 5 in an otherwise passing run. The final raised
  camera shows cyan 5 up at 7.85 s and opposite red 2 up at 8.00 s, establishing
  cyan 5 down. Opposite-face evidence is valid because the marked cube is rigid
  and the face mapping is specified. Preserve the intervening frames.
- Readability needs real rendering checks, not just score telemetry. The final
  complete videos combine the 1600×1280 review view with all three policy views.
  The close-up is not a model input. Visual rulers do not add collision geometry;
  perspective prevents treating them as universal screen-space measurements.
- Direct Dream ran successfully on the VM: 25 requests / 25 attempts / 1 session.
  It returned 380 out-of-range prediction rows, including unused final-chunk rows.
  Standard execution bounds/step clamps are retained; all 1,200 executed actions
  pass bounds and step checks. Do not confuse returned predictions with executed
  actions, or evaluation status `success` with task success.
- The same frozen demo physics produced matching results twice, with only the
  review camera changed. This is not a statistical repeatability/fairness claim.
- Final media in `artifacts/roll-a-die-v3/` is uploaded as **M-PV3ZXY**:
  H.264/yuv420p, fast start, complete frame counts and below upload limits.
  The user's explicit upload-and-PR request supersedes the earlier approval
  blocker. Do not reuse the obsolete blank-cube videos.
- The refreshed live board had 128 entries (38 pending, 90 pilot) and the public
  repository had 43 prior PRs immediately before submission. No direct die-roll
  duplicate was found; this does not guarantee acceptance. The team token was
  accepted as T-39, and Robocurve received the `tommyet` PR as **TK-YBZD4Q**.

## Dated session log

### 2026-11-07–08 — overhand-knot development session (in progress)

- Operator: repository agent; branch `codex/tie-overhand-knot` from `0ac98c6`.
  User requested task implementation using review feedback and strong PRs;
  this does not authorize an upstream PR. The planned first GPU checks are
  rope stability, grasping, self-contact and knot retention before full demo
  and Dream trials. No knot feasibility or score is established yet.
- Brev CLI and filtered API checks confirmed the retained `robocurve-dice`
  VM was STOPPED at 23:52 UTC, with no running compute. Posted credit $186.16;
  observed catalog running rate $3.279064/hour, including allocated storage.
  Session evidence is ignored under `artifacts/rope-knot-development/`.
  Check current status and remote users/jobs before taking over this VM.
- Read accepted cable tasks [#8](https://github.com/robocurve/benchmark-tasks/pull/8),
  [#10](https://github.com/robocurve/benchmark-tasks/pull/10), and coordinated-latch
  [#42](https://github.com/robocurve/benchmark-tasks/pull/42). Use a specific
  functional purpose, independent negative controls, visible measurements and
  explicit approximation limits. The die's relevance rejection is a warning
  against presenting generic dexterity alone as societal value.
- Implemented a maximal-coordinate capsule rope, ordinary joint-command
  manipulation, topology checks, complete geometry capture, offline replay and
  a separate load assay. **No validated robot-tied knot or Dream run yet.**
  `tasks/tie-overhand-knot/task.draft.json` deliberately has no fabricated media
  identifier. README, JUDGING and VALIDATION all identify development status.
- Current scorer: 0.5 for a released overhand with both tails ≥4 cm; 1.0 if
  that same knot survives a 2 s seating ramp followed by 5 s at 0.981 N ±5%.
  Assessor-induced knot loss retains the pre-test half credit, but invalid
  physics erases all credit. Projected core size/slip are diagnostics only;
  they did not reliably correspond to ruler measurements. Forty-three local
  tests passed, including negative topology, corrupted evidence, force/timing
  checks, fixture clearance and runner cleanup. They do not establish robot
  feasibility.
- With body damping 0.5 linear / 2 angular and bend damping 2e-5, the straight
  cord's recorded centres did not drift over 5.05 s. The earlier low-damping
  straight chain rolled spontaneously. A preformed-knot **diagnostic** survived
  the new gradual load protocol with maximum joint gap 0.284 mm and all
  topology checks passing. It always scores zero as a task. Shareable anonymous
  traces and configuration are in the task's `evidence/` folder.
- Unassisted crossing-lift/threading probes had excess tip/standing-strand
  overlap; raising physics from 240 to 960 Hz did not fix it and made runs much
  slower. Actual USD capsule height excludes its hemispheres, matching our
  geometry check. GPU CCD should not be assumed effective merely because its
  authored flag is true. Current default remains 240 Hz, with source snapshots
  and native scene settings recorded per trial.
- An untied three-peg jig settled without invalid rope contact. Its first
  manipulation missed a pickup at 13.5 mm above the rope axis; actual fingertips
  extend only 12.842 mm beyond TCP. At +9 mm, pickup and rotation worked, but
  the working strand wrapped around an upright and slipped during lifting.
  A revised far-side support layout and reflected standing lead passed offline
  geometry/robot-clearance checks; its physical trial is in progress. The
  scorer requires the whole cord ≥1 cm clear of all jig parts before credit.
  Every revised run stores its exact fixture geometry for reproducible replay.
- VM remains running during this entry. Start request was 23:57:16 UTC on
  November 7, at $3.279064/hour. Stop and billing evidence must be recorded
  before this session is considered closed. No Dream API request or upstream
  PR/media upload has been made in this session.

### 2026-11-07 — rope and shoelace asset follow-up

- Operator: repository agent; branch `codex/rope-asset-note`, based on
  `a348579`. Read-only source review; no GPU started or physics trials run.
- NVIDIA AutoData provides a deformable `Rope.usd`, loaded using
  `DeformableObjectCfg`. Its [Franka example](https://isaac-sim.github.io/AutoData/main/pages/workflows/franka_rope_softmimicgen/index.html)
  demonstrates grasping the rope and bringing its ends together, with PhysX or
  Newton. It does **not** demonstrate knot formation or retention. The
  [asset wrapper at inspected commit](https://github.com/isaac-sim/AutoData/blob/073c393e90d4188937d916096356fba992a3906c/autodata_examples/envs/isaac_lab_arena/franka_rope/rope_asset.py)
  is a concrete integration starting point; no asset has been imported locally.
- Our pinned Arena commit also includes a procedural
  [Cable](https://github.com/isaac-sim/IsaacLab-Arena/blob/c7edf3a9d5d8276565208f72422f8f8a0806d6cf/isaaclab_arena/assets/cable.py)
  using `CableObjectCfg`/`ObjectType.CABLE`. It requires Newton, with VBD
  recommended. Its reset/export tests do not establish knotting behavior.
- Neither candidate is a drop-in object for our current task loader:
  `artifacts/simulator-update-2026-11-07/upstream/adapter-scene-pinned.py`
  lines 196–218 load library USDs as `ObjectType.RIGID`. Custom deformable scene
  integration is needed. AutoData's supported Arena pin also differs from ours.
- No named rope/shoelace was found in the inspected ordinary Arena object
  library (186 name definitions); registered PhysX deformables were cube,
  surface and teddy bear. This was not an exhaustive SimReady/cloud catalog
  search. A flat shoelace with aglets has not been identified.
- Decision: a round cord and simple overhand knot are plausible candidates for
  a small feasibility trial. First verify robot grasping, self-contact without
  passing through itself, tightening and retention after release. Dimensions,
  friction and knot reliability remain unmeasured; do not claim submission
  feasibility from the existence of a rope asset alone.

### 2026-11-07 — knot, folding, cutting and screw-cap idea review

- Read-only research around 19:54 UTC: the authenticated board returned 992
  tasks (879 pending, 18 accepted, five being revised, 90 pilots). The public
  repository returned 999 PRs across all states. Raw snapshots and filtered
  matches are ignored under `artifacts/task-ideas-2026-11-07/`. This is a dated
  search, not a reservation or guarantee of novelty; recheck before building.
  No GPU, task development, media upload or submission was started.
- **Knot tying:** no direct knot-tying task was found in this snapshot. Pilot
  `TK-MLM3G2` is “Undo a knot in a rope”; pending rope/line tasks include
  [lacing an eyelet #750](https://github.com/robocurve/benchmark-tasks/pull/750)
  and fastening maritime lines. Pilots are also relevant to the novelty check.
  [HANDLOOM](https://proceedings.mlr.press/v229/viswanath23a.html) demonstrates
  bimanual robotic knot tying, with specialized tooling; it does not validate
  stock YAM grippers. Rope self-contact, friction, tightening and regrasping are
  substantial new work for our runner. Evaluate one useful knot objective
  before planning a batch; knot names alone do not establish distinct abilities.
- **Clothes folding:** no direct clothes-folding entry or PR was found, but
  [BEHAVIOR already specifies folding clothes](https://behavior.stanford.edu/knowledgebase/tasks/folding_clothes-0.html)
  and [SoftGym](https://sites.google.com/view/softgym) includes cloth folding.
  Generic folding therefore has strong prior-art risk even without a board
  match. Cloth handling is also a larger simulation project than our bricks.
  [Isaac Sim 6.1's migration guide](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/migration_guides/isaac_sim_6_0/core_api_to_core_experimental.html)
  says the old particle-cloth wrappers have no drop-in replacement. This does
  not make cloth impossible; it means old examples cannot be assumed to work
  in our pinned Arena/YAM environment. Changing garment or fold direction is
  not a dependable novelty distinction.
- **Food chopping:** [bread slicing #699](https://github.com/robocurve/benchmark-tasks/pull/699)
  is received as `TK-N9C8DA` and pending. Vegetable chopping was not found as
  an exact board title, but [BEHAVIOR specifies slicing vegetables](https://behavior.stanford.edu/knowledgebase/tasks/slicing_vegetables-0.html).
  Our code has no validated cutting model. The hard part is separation,
  deformation and cutting resistance, beyond carrying a knife. The pending
  bread task discloses a custom rigid-slab/joint approximation; pending does
  not establish reviewer approval of that approximation. Likewise,
  [OmniGibson's slicing transition](https://behavior.stanford.edu/omnigibson/transition_rules.html)
  replaces objects under prescribed conditions rather than validating fracture
  physics. Deprioritize generic chopping for a quick submission.
- **Unscrewing a bottle:** technically the most manageable of these four, but
  clear competition overlap: [open bottle and pour #103](https://github.com/robocurve/benchmark-tasks/pull/103),
  [child-resistant medicine cap #790](https://github.com/robocurve/benchmark-tasks/pull/790)
  and [flashlight screw cap #230](https://github.com/robocurve/benchmark-tasks/pull/230)
  are all received/pending. Pilot `TK-W6YVSV` opens, loads and recloses a screw
  jar; `TK-YSCE4F` opens a medicine bottle. Ordinary screw-cap removal is not
  an obviously unclaimed objective. [BiDemoSyn](https://arxiv.org/html/2512.09297v3)
  demonstrates water-bottle unscrewing with two parallel grippers, but not our
  specific YAM setup. Thread/contact mechanics and free cap release still need
  validation; different cap sizes or thread counts alone are weak distinctions.
- Scoring directions if a distinct task survives that check: knot topology plus
  a specified gentle retention test and tail/slip limits; folds judged by marked
  corner/edge alignment and layer configuration, not compactness alone; food
  judged by complete separation and useful piece dimensions; screw caps judged
  by actual thread disengagement and intact removal, not wrist rotation.
  Dimensions and thresholds must be selected and tested for the actual objects.
  Current recommendation: only investigate a specific functional knot after a
  small rope-physics feasibility check; none of the four generic ideas is a
  low-risk acceptance candidate. These are engineering/novelty judgments, not
  organiser decisions.

### 2026-11-07 — shared main and agent handoff

- The user asked whether all work was on `main` for Eito to continue. Fresh
  remote checks found `main` at `4f8c32c`, 16 commits behind the fully pushed
  `duplo-joining-batch` branch, with no divergent commits. GitHub confirms
  `Miyamura80` has write access and `main` is the repository's default branch.
- The fork's `main` was fast-forwarded to the completed work and these handoff notes.
  All five task folders match their submitted branch versions. The handoff
  adds README setup steps and explicit development/submission branch guidance;
  no task source, submitted media or submission branch changes are needed.
- Code, CAD, curated numeric evidence and shared notes belong on `main`.
  Credentials, private PDFs and full trial artifacts remain ignored. The
  simulator is installed on the retained VM, not in Git; November 7 validation
  and the stopped VM's evidence locations are recorded below.

### 2026-11-07 — official simulator update and compatibility validation

- Operator: repository agent; working branch `duplo-joining-batch`. The user
  explicitly authorized the simulator update and checking the earlier runs.
  The retained VM was STOPPED before this session; no active login or GPU job
  was found after starting. Source snapshots, local patches and installed-package
  manifests were saved before running the official update. Setup output is
  private because the official script prints the existing desktop password.
- Official launchable advanced from `d825f0c` to `25a2963`; its asset fix changes
  Arena's library from the outdated staging bucket to the production root.
  Inspect Robots upgraded 0.60.0 → 1.0.0, YAM plugin 0.37.0 → 0.38.0, agent
  plugin 0.28.0 → 0.30.0, and NumPy 2.3.1 → 2.5.4. Other dependency changes are
  recorded in `artifacts/simulator-update-2026-11-07/postflight.json`.
  Isaac Sim 6.1, the adapter `0059d02` and Dream client 1.0.14 were retained.
  The official setup and explicit agent upgrade both completed successfully;
  YAM embodiments and Dream/scripted policies are registered.
- Independent offline replay of all ten historical final trials still gives
  demo 1.0 / Dream 0.0, with matching core and evidence hashes. The asset fix
  targets library objects; our custom task-file scenes use procedural room
  geometry, local bricks/die and bundled robot assets. The update does not
  itself explain Dream's low scores or previous session recoveries.
- All five fresh demos pass at **1.0**. Each brick demo uses 400 actions / 20
  simulated seconds; the die uses 182 actions / 9.10 seconds. Every demo's
  measured numeric trajectory and executed actions exactly match its original
  final recording, with no action-range or delta violations. Archived task
  sources match the submitted versions. This is a fixed-seed compatibility
  check, not a general repeat-success or physical-fidelity claim.
- The four brick demos took 130.5, 107.8, 110.3 and 109.4 seconds of runner wall
  time (full 2×2, single-stud, mixed and offset); the die took 44.5 seconds.
  The updated full 2×2 Dream trial completed in 262.9 seconds and scored **0.0**;
  the robot did not achieve the pickup milestone. All 1,200 executed actions /
  60 simulated seconds pass bounds and step checks. There were 25 requests,
  27 attempts, two expired-session retries and three sessions, with recoveries
  at steps 128 and 272. This is valid evidence of the observed failure, but
  session recovery could affect performance: do not present it as an
  uninterrupted measure of task difficulty. The other four historical Dream
  trials were rescored locally rather than rerun on the GPU.
- The new full 2×2 composite renders successfully and retains all 401 frames.
  Visual samples of all four updated brick demos show the expected geometry,
  suspended lower brick during the proof lift, and released final assemblies.
  No obvious missing geometry or texture was seen. Sampling does not establish
  every duration or contact condition; the numeric audits check those scores.
- Inspect 1.0 changes camera-export filenames from `*_top_cam.mp4` to
  `*~top_cam.mp4` (likewise wrist cameras). After exporting the camera videos,
  run `python tools/prepare_review_media.py RUN`, then the existing task's
  `render_review.py`. The helper adds relative aliases without overwriting or
  re-encoding files; it supports both formats and rejects ambiguous inputs.
  It was verified on actual old/new videos. No submitted task source or media
  was edited, and no submission branch or upstream PR was changed.
- Environment backups, trajectories, actions, videos, setup images and audit
  reports were downloaded to ignored `artifacts/simulator-update-2026-11-07/`.
  Raw camera arrays remain on the retained VM. See `historical-evidence-recheck.md`,
  `updated-first-demo-audit.json`, `new-demos-audit.json`,
  `new-die-demo-audit.json`, `new-dream-audit.json` and
  `visual-check-3-brick-demos/visual-audit.json`.
  These checks found no update-related reason to replace existing submissions;
  they do not resolve the competition's novelty or importance criteria.
- VM session: start requested **15:41:56 UTC**, healthy at 15:43:14; all trials
  and downloads finished before the stop request at 16:05:54. No GPU compute
  process remained. **STOPPED confirmed 16:13:47 UTC**; the existing
  `g6e.2xlarge` and 256 GiB disk were retained without resizing or deletion.
  Charging the entire 31m50.6s start-to-confirmed-stop interval at the observed
  $3.279064/hour gives a conservative **$1.74** estimate, including storage
  during that interval but excluding Dream API charges and later storage.
  Posted credit was $186.46 before and $186.44 at 16:14:14; billing lag means
  that $0.02 difference is not the session's actual cost. See `session.json`,
  `billing-final.json` and `final-session-audit.json` in the artifact directory.

### 2026-11-07 — updated launchable instructions and FAQ

- Operator: repository agent; branch `duplo-joining-batch`. Checked the live
  [walkthrough](https://tasks.robocurve.org/walkthrough#updating) and
  [FAQ](https://tasks.robocurve.org/#faq) at about 15:35 UTC. No VM start,
  environment update, rerun or submission change was made.
- The November 5 launchable update fixes outdated asset locations and upgrades
  to inspect-robots 1.0. Our retained installation predates November 5; brick
  `VALIDATION.json` records inspect-robots 0.60.0 and inspect-robots-yam 0.37.0.
  No application of this fix is recorded. Before the next GPU batch, follow
  the live update sequence below, check compatibility and record new versions.
  The walkthrough PDF predates the update. Its effect on our earlier runs,
  Dream session expiries and scores is unverified; no rerun requirement for
  existing submissions was found in the update section.

  ```bash
  cd ~/YAM-inspect-Isaac
  git pull origin main
  bash launchable/setup.sh
  ~/.local/bin/uv pip install -U inspect-robots-agent --python /data/IsaacLab-Arena/.venv/bin/python
  ```

- The FAQ says separate tasks need distinct objectives/abilities; geometry,
  layout or difficulty changes usually do not suffice. This remains a risk for
  the four pending brick tasks, not a new decision on them.
- Custom assets are allowed under the task's open-source license. Third-party
  assets must permit research use and redistribution, with licenses documented.
  One primary 0–1 score is required; optional extra scores must be described in
  both README and task.json. Bimanual parallel-gripper tasks still need Dream-1.
- One accepted task makes a team eligible for the planned paper's authorship;
  the number of authors depends on contribution. This is eligibility, not an
  acceptance guarantee. Local guide snapshots are ignored under
  `artifacts/brick-submissions/{guide,walkthrough}-2026-11-07.html`.

### 2026-11-06 UTC — brick rejections withdrawn; die finally rejected

- Operator: repository agent; working branch `duplo-joining-batch`. User asked
  for current PR status. Fresh GitHub reads at 05:49 UTC show all four brick
  PRs open and unmerged, and the die PR closed and unmerged. No submitted code,
  media or PR was changed; no GPU was used. This supersedes the previous entry.
- Organizers corrected [#365](https://github.com/robocurve/benchmark-tasks/pull/365#issuecomment-6671468200)
  at November 5, 22:43:27 UTC and [#366](https://github.com/robocurve/benchmark-tasks/pull/366#issuecomment-6671466189)
  at 22:43:20 UTC: their earlier decisions were posted in error, both tasks are
  back in the review queue, and no action is needed from us. The PRs have been
  reopened. Do not treat the withdrawn novelty decisions as established review
  findings. Novelty remains an independent concern, not a published verdict.
- [Die #44](https://github.com/robocurve/benchmark-tasks/pull/44#issuecomment-6672524315)
  received **Not accepted: final** at November 5, 23:44:38 UTC. The stated reason
  is “Task lacks strong real-world relevance.” The decision says the task fails
  the importance bar and cannot be revised; a different task may be submitted
  in a new PR. Preserve this submission and wait for user direction on new work.
- #364 and #367 still have only receipt comments. None of our five tasks is
  accepted. Keep all four pending brick submission branches unchanged.
- Evidence: `artifacts/brick-submissions/pr-status-2026-11-06.json` (ignored).
  The authenticated board at 05:50 UTC confirms all four brick tasks pending
  with no review timestamp; the die is absent, so use its GitHub decision.
  It lists 17 accepted, 582 pending, 12 rejected and 90 previous-cohort plans.
  Board evidence: `artifacts/brick-submissions/board-our-five-status-2026-11-06-05-50-06.json`.
  Reusable lesson: recheck live decisions before acting; organizers can correct
  prior reviews. Technical feasibility and a full-score demo do not establish
  the competition's real-world importance requirement.

### 2026-11-05 — two final novelty rejections; three tasks still pending

**Superseded:** the organizers withdrew both brick decisions later that day.
The historical snapshot below records what was published at the time, not the
current review outcome. See the November 6 UTC entry above.

- Operator: repository agent; working branch `duplo-joining-batch`. User asked
  for updates on all five submitted PRs. Checked GitHub status/comments at
  21:54 UTC and the authenticated board at 21:55 UTC; no task or PR was changed.
- [PR #365, two 1×1 blocks](https://github.com/robocurve/benchmark-tasks/pull/365#issuecomment-6669481752)
  (`TK-UJQEDY`) was **not accepted: final** at 21:04:16 UTC.
- [PR #366, 1×1 onto 2×2](https://github.com/robocurve/benchmark-tasks/pull/366#issuecomment-6669477142)
  (`TK-PSN375`) was **not accepted: final** at 21:04:08 UTC.
- Both organizer comments identify them as superficial variants of the full
  2×2 task (`TK-BPUQW9`): changes to brick size, stud count and allowed stud
  positions did not meet the Importance criterion. Both PRs are closed and
  unmerged. The decisions explicitly forbid revising these tasks; a different
  task may be submitted in a new PR. Do not reopen or treat them as ordinary
  48-hour revision cases. New task development/submission needs user direction.
- [Die #44](https://github.com/robocurve/benchmark-tasks/pull/44),
  [full 2×2 #364](https://github.com/robocurve/benchmark-tasks/pull/364) and
  [offset 2×2 #367](https://github.com/robocurve/benchmark-tasks/pull/367) remain
  open, unmerged and pending, with no new review feedback after their receipts.
  Keep those submitted branches unchanged. The rejected tasks' source and
  evidence remain archived for learning; submitted heads are unchanged.
- The board returns the three pending tasks with `reviewed_at: null`; the two
  finally rejected tasks are absent from its list. The GitHub comments establish
  the final decisions, not their absence from the board. No revision deadline
  was provided. Local evidence: `artifacts/brick-submissions/pr-status-2026-11-05.json`
  and `board-our-five-status-2026-11-05.json` in the same ignored directory.
- Learning for future batches: changes in part size or number of engaged studs
  do not establish a separate task here. Assess a distinct objective and skill
  before developing another variant. Successful demos and rigorous scoring
  do not establish novelty. The remaining two brick tasks have not yet received
  an acceptance decision.

### 2026-11-04 — four brick tasks submitted (November 5 UTC)

- Operator: repository agent; working branch `duplo-joining-batch`. The user
  explicitly requested a PR for each of the four tasks after reviewing the
  completed batch. This authorized the four media uploads and submissions.
- Refreshed the live guide, upstream `AGENTS.md` and authenticated board.
  Preflight showed 420 tasks (330 pending, 90 previous-cohort plans), no own
  submissions in the previous 24 hours, an open window and a 20/day cap.
  The three earlier DUPLO plans remain. New pending `TK-E4WPXK` attaches a
  tipper-bed hinge and unloads a cube; no new direct stud/socket retention
  counterpart was found in the bounded check. External benchmark overlap
  remains a novelty risk; receiving a task is not acceptance.
- Tightened setup, context, rubric and judging prose. The guide requires the
  **exact model instruction**, so it is unchanged and checked against config,
  runtime and recorded evaluation prompts. Every frozen simulation/scoring
  source hash matches. All eight final offline replays passed again: demos
  1.0, Dream 0.0, no invalid evidence. No GPU was started.
- Used the official uploader's multipart builder with curl transport, following
  the previously verified workaround for urllib's Cloudflare 403. The token
  remained in memory and out of arguments, logs and Git. Each task received
  its own Dream video, full-score demo and `setup-closeup.png`; upload hashes
  match the validated local files. No successful upload was retried.

| Task | PR | Board ID | Media ID | Submitted head |
|---|---|---|---|---|
| Join two 2×2 blocks | [#364](https://github.com/robocurve/benchmark-tasks/pull/364) | `TK-BPUQW9` | `M-FFYNCV` | `f985309` |
| Join two 1×1 blocks | [#365](https://github.com/robocurve/benchmark-tasks/pull/365) | `TK-UJQEDY` | `M-3W4V6P` | `8b2ae31` |
| Join a 1×1 block to a 2×2 block | [#366](https://github.com/robocurve/benchmark-tasks/pull/366) | `TK-PSN375` | `M-WMS6EN` | `c35d19d` |
| Join two 2×2 blocks with two studs overlapping | [#367](https://github.com/robocurve/benchmark-tasks/pull/367) | `TK-4NRFL8` | `M-NDBC5A` | `15c31bf` |

- All four were received without ingestion errors at 01:01:51–01:01:59 UTC
  on November 5 and were **waiting for review** at receipt. The board confirmed our
  ownership, matching submitted text and all three media links for each.
- Each PR is non-draft, authored by the registered `tommyet` account, against
  upstream `main`, with one commit and exactly 30 files under its one task
  folder. No shared notes, workbench files, private PDFs, credentials or die
  changes are in those diffs. PR #44 remains unchanged.
- **Freeze all four submitted branches while pending.** Do not push later
  working edits into them expecting re-ingestion. Revisions after feedback
  use the same PR; do not merge the PRs ourselves. Shared notes remain on
  `duplo-joining-batch`. Local single-task worktrees are under ignored
  `artifacts/brick-submissions/worktrees/`.
- Filtered receipts, branch heads, final replay checks, upload hashes and
  board confirmation are in ignored `artifacts/brick-submissions/`. Preparation
  commit: `c2763f7`; submitted heads above contain only their own task package.
  The GPU remains stopped; this submission needed no further simulation.

### 2026-11-04 — four construction-brick tasks, completed for review

- Operator: repository agent; branch `duplo-joining-batch`. User requested four
  separate joining tasks, complete for review, and approved custom printable
  single-stud bricks at Duplo scale. This does not authorize new uploads or PRs.
- Before startup, Brev reported `robocurve-dice` STOPPED. The CLI login had
  expired; the user's existing Safari session renewed it successfully. Start
  requested for a batch of contact probes, four robot demos and four Dream runs.
  Final results and shutdown are recorded below.
- The original Mumbai `g6e.2xlarge` failed twice with
  `CAPACITY_UNAVAILABLE`. Resizing the same stopped VM to `g6e.4xlarge`
  preserved its disk/environment and allowed startup around 23:24 UTC.
  Both have one L40S GPU; the larger machine adds CPU/RAM. The observed
  Mumbai catalog rate is $4.329588/hour compute plus approximately $0.05/hour
  disk, or $4.38/hour while running. Do not use the older $3.28 rate for this
  session. The cheaper configuration was restored after shutdown (see below).
- The four task folders contain their own complete runtime/scorer/geometry.
  `brick_workbench/` maintains shared sources and packages them; it must stay
  outside eventual single-task submission diffs. The received die task is unchanged.
- Custom geometry uses hollow compound colliders and compliant socket contact,
  with no proximity glue or attachment joint. Material coefficients are trial
  assumptions, not measured Duplo/printed-plastic calibration. The final robot
  trials below establish simulated feasibility only.
- The scorer checks geometric seating, then unsupported retention while only
  the upper brick is held, followed by released rest. All 315 collision meshes
  of each YAM arm contribute to nine conservative measured-link boxes. A TCP
  distance alone cannot exclude lower-brick support by a finger or forearm.
- Read actual rigid roots for scoring. Arena `object_states().pos` is the AABB
  centroid, which shifts upward when studs are added. Body-centred geometry
  and mixed centroid telemetry would silently corrupt seating measurements.
- CPU material probe `brick-probe-005` tests aligned insertion, a 2 mm
  lateral error and a non-contact hover for each configuration. All aligned
  joints retained for the full one-second proof; all negative controls failed
  retention. Final aligned seating gaps were 0.097–0.123 mm and maximum hard
  overlap was below 0.030 mm. The 20 N value is a descent-stop threshold,
  not a strict force cap: misaligned contacts briefly exceeded it.
- The compliant contact model is an approximation, not measured PLA bending.
  The largest transient compliant overlap was 0.461 mm at the socket transition;
  nominal radial interference is 0.1 mm. Printing tolerances, insertion force
  and pull-out force still need real calibration. Keep this limitation in
  each task's fidelity statement. Probe results are not robot demonstrations.
- Instrumented contact probes must enable contact processing and confirm
  actual reports. Isaac Lab disables it by default; zero unobserved impulses
  are not evidence of zero force. Probe004's pose checks are superseded by
  probe005 for force/contact validation. CPU tensor views require the active
  stage ID, without manually attaching the stage a second time.
- Actual robot trials revealed loaded tracking error and upward brick slip
  during insertion. Pose-only reachability cannot validate pressing. One-time
  measured grasp-offset correction aligns the scripted demo, while Dream
  retains the standard camera/robot observations. Trial-specific offsets,
  source snapshots and failed attempts are preserved in local artifacts.
- All four configurations now have a full-score robot demo. The four-stud
  trial needed a 23 mm grasp height, 1 mm nominal squeeze per side and 6 mm
  commanded press overtravel; other joins passed with 22 mm, 0.5 mm and 3 mm.
  These are controller targets, not measured plastic deformation. All motions
  use ordinary joint/gripper commands, with no brick teleport or joint creation.
- Novelty is a material submission risk. The November 4 board snapshot has
  previous-cohort DUPLO image/bridge/overhang plans; those are not accepted
  reviews, but the board asks new tasks to differ from them. The primary
  [WorkBenchMark](https://workbenchmark.github.io/) project already includes
  two-brick DUPLO assembly. Our unsupported retention proof is a useful
  distinction shared by all four tasks; four separate acceptances are not
  assured. See `docs/brick-task-review.md` before choosing submissions.
- The retained virtualenv's FFmpeg exports policy streams but lacks the
  `drawtext` filter. Compose labeled review videos locally with the verified
  bundled macOS FFmpeg; there is no need to leave the GPU running for that.

### 2026-11-04 — final brick evidence and learning points (finished November 5 UTC)

- Operator: repository agent; branch `duplo-joining-batch`. All four tasks are
  complete for user review. No media was uploaded and no competition PR was
  opened. The original die task and submission branch remain unchanged.
- Final demo / Dream run IDs, scores and measured runner wall times:

  | Variant | Demo | Dream |
  |---|---|---|
  | 2×2 | `brick-2x2-demo-004`: 1.0, 109.469 s | `brick-2x2-dream-001`: 0.0, 266.701 s |
  | 1×1 | `brick-1x1-demo-002`: 1.0, 106.703 s | `brick-1x1-dream-001`: 0.0, 241.736 s |
  | Mixed | `brick-mixed-demo-002`: 1.0, 107.380 s | `brick-mixed-dream-001`: 0.0, 264.635 s |
  | Offset | `brick-offset-demo-002`: 1.0, 107.844 s | `brick-offset-dream-001`: 0.0, 263.739 s |

- Every demo uses 400 actions / 20 simulated seconds; every Dream run uses
  1,200 actions / 60 seconds. All eight independent audits pass with matching
  frozen source hashes and replay scores, complete frame counts, and zero
  executed action range/step-limit violations. The shared scorer passes 54
  tests. One fixed-seed run per policy is not a reliability estimate.
- Dream used the standard direct client but recovered expired sessions.
  Request/attempt/retry/session counts are respectively 25/29/4/5 for 2×2,
  25/26/1/2 for 1×1 and mixed, and 25/27/2/3 for offset. The four-stud diagnostic
  identifies `DreamSessionExpired` (`DA-0001`). Recovery retries the same
  observation window without a simulation action between attempts, adopts
  the replacement session, and resets client action smoothing. Server
  continuity and performance effects are unknown. Do not label these clean,
  uninterrupted runs or attribute failure entirely to task difficulty.
- Every task now has completed `VALIDATION.json`, anonymous numeric compressed
  traces, audit reports, sampled visual review reports and the material probe.
  Preserve the distinction between original-file hashes and curated-trace
  hashes. Curating strips arbitrary text and still produces the same score.
  `brick_workbench/finalize_batch.py` fails closed on mismatched/incomplete
  evidence; do not bypass its checks to fill scores from memory.
- Video review sampled setup, seating, unsupported lift and released finish,
  with six times across each Dream run. Every-frame completeness and numeric
  scoring were audited separately. Exact submillimetre seating is established
  from geometry/telemetry, not claimed from an oblique frame. For offset, the
  known grid and visible 16 mm displacement establish two engaged studs even
  if one unused stud is hidden. Explain this in the manual judging guide.
- Final composites are H.264/yuv420p, fast start, with every original frame.
  Demos are 5.3–5.6 MB and Dream videos 14.7–19.1 MB; complete task folders
  are about 3.8 MB each. Use `setup-closeup.png` (1600×1280) for a later upload,
  rather than the smaller policy-view `setup.png`. Each task needs its own
  upload/media ID and one-folder PR after user authorization.
- All final media, measured trajectories, source snapshots and historical
  development attempts have local copies under ignored `artifacts/`. Raw
  camera arrays and the retained simulator installation remain on the VM.
  Local FFmpeg composition was slow; stop GPU compute after evidence download,
  then finish CPU-only composition, audits and documentation locally.
- Reproduction must use the recorded VM source revisions, not whatever local
  checkout is current. Physics 240 Hz is backed by the installed adapter's
  source configuration, not inferred from 20 Hz control timestamps. Recorded
  versions, revision hashes and action limits are in each validation record.

- Stop requested at 00:29:52 UTC on November 5; STOPPED confirmed at
  00:42:11 UTC. Shutdown took about 12m19s even though the CLI returned success
  earlier. Always check the actual VM lifecycle status. No GPU compute
  processes remained before stopping, and final evidence was downloaded.
- Start request at November 4 23:16:16 UTC through confirmed stop spans
  85m55s. At the observed $4.37746/hour total rate, conservatively charging
  that whole interval estimates **$6.27 total / $1.57 per task**. This includes
  failed starts, probe/demo development, idle time and shutdown; it is not an
  invoice. Do not add overlapping per-run estimates. Separate Dream charges
  and later retained storage are excluded. Last posted balance was $193.36
  at 00:00:19 UTC, before completion; billing lag makes it unsuitable as the
  complete batch cost. Filtered lifecycle/rate evidence is in ignored
  `artifacts/brick-batch-session/`. The retained 256 GiB disk is about
  $1.15/day at the catalog rate (UI rounded estimate $1.20/day), shared by
  all tasks, not charged separately per task.

- After confirmed shutdown, restored the retained VM to `g6e.2xlarge` for
  later sessions; `brev ls` confirms STOPPED at that size. No restart was
  requested. A scale operation can transiently report STOPPING and the old
  type; wait for it to settle. The private access token can expire while
  reading status: run the read-only `brev ls` to use the CLI's existing refresh
  flow before requesting a new browser login. Never print credentials.

### 2026-11-03 — final media upload and competition submission

- Operator: repository agent. User explicitly requested: "Media upload and PR.
  Submit as advised by doc." This authorizes this die-task submission.
- Uploaded the complete final v3 `dream.mp4`, `demo.mp4` and `setup.png` from
  `artifacts/roll-a-die-v3/` to Robocurve; returned media ID **M-PV3ZXY**.
  The token stayed in memory and out of command arguments/output/Git.
- The official Python uploader received Cloudflare 1010, including on a public
  unauthenticated page. Standard curl reached the same service successfully.
  Upload used curl with the official `/api/media` fields and authorization
  header passed privately through stdin. Do not repeat an upload after success.
- Independent final audit confirmed 21 task-only files, anonymous task text and
  evidence, matching core-source hashes and replay scores 1.0 / 0.0. No new
  GPU trial was necessary; the VM remained stopped.
- Opened non-draft [PR #44](https://github.com/robocurve/benchmark-tasks/pull/44)
  as `tommyet`, from `tommyet:submission/roll-a-die` to
  `robocurve/benchmark-tasks:main`, at 14:40:12 UTC. Submitted head `61268c3`;
  media and task docs were attached before creating the PR. The initial
  ingestion reported two field-length violations, corrected at `ba4ac81`
  before Robocurve received the task; simulation, scoring and media were unchanged.
- The GitHub connector could read the upstream repository but its PR-create
  call returned "Resource not accessible by integration". The existing
  authenticated `gh` CLI account successfully created the same requested PR.
- [Robocurve receipt](https://github.com/robocurve/benchmark-tasks/pull/44#issuecomment-6606759429)
  at **14:41:54 UTC**: received as **TK-YBZD4Q**, **waiting for review**.
  Final submitted commit **ba4ac81**, media **M-PV3ZXY**. Do not merge the PR
  ourselves. Acceptance is an upstream merge after organizer review.
- Newly verified text limits: `fidelity` maximum **500 characters**, `scores`
  maximum **300 characters**. Final fields are 406 / 275 characters; retain
  fuller explanations in README/JUDGING/VALIDATION. The ingestion bot accepts
  a correction pushed to the same PR before receipt, as it did here.
- The live program limits also report 20 submissions/day, 50 MB/video, 25 MB
  code and 95 MB total. Read current limits rather than relying on defaults.
- Pending submissions are frozen by the guide. Do not push task changes before
  review expecting them to be re-ingested. Keep working notes on the broader
  working branch; revisions after feedback use the same PR.

### 2026-11-03 — marked die, observable v3 rubric and fresh direct Dream runs

- Operator: repository agent; branch `roll-a-die`. User requested coloured
  faces/markings, the new rubric and fresh demo/Dream recordings. GPU startup
  succeeded around 13:58 UTC after the earlier regional capacity failures.
  The retained `/data/` installation survived; no cold installation was needed.
- Added six coloured faces and black 1–6 pips as non-colliding paint on the same
  16 mm / 5 g cube. Added a separate review camera and render-only reference rulers.
  Camera angle needed visual QA: the first low view hid the qualifying upper
  face, so it was raised and both final videos were recorded on the final setup.
- V3 uses visible pose/time criteria. The first v3 scripted release was tuned
  locally for reachable targets and speed limits, then scored 1.0 on the first
  new physics attempt. Final camera-matched demo002 also scored 1.0 after 182
  actions / 9.10 simulated seconds, wall 44.457 s. Cyan 5 up at 7.85 s → red 2 up at 8.00 s demonstrates
  the required inversion; rest is 8.10–9.10 s. Commands never move the die directly.
- Final direct Dream002 scored 0.0 with no qualifying pickup in 1,200 actions /
  60 simulated seconds; wall 184.133 s, 25 requests, 25 attempts, 1 session, no retries.
  Its 380 returned prediction rows beyond bounds include unused tail rows.
  Inspect's normal bounds clamp/per-step limiter remains enabled. Independent
  action-log checks found zero range or step-limit violations in executed actions.
- Final evidence: `artifacts/die-v3-demo-002/`, `artifacts/die-v3-dream-002/`;
  final media: `artifacts/roll-a-die-v3/`. Full videos contain 183 / 1,201 frames
  at 20 Hz, H.264/yuv420p with fast start, about 2.93 MB / 14.27 MB. The PNG is 0.67 MB.
  A separate quarter-speed turnover clip aids learning; the full videos preserve
  every original frame. Old raw artifacts and validation history remain intact.
- Final independent rescoring matches 1.0 / 0.0. All 48 tests pass: 35 scorer,
  10 bridge and 3 recording/source tests. Current core source hashes match both
  final run snapshots. Two new privacy-checked anonymous compressed traces are
  committed with `VALIDATION.json`; old evidence is in `VALIDATION-v2.json`.
- At the observed $3.28/hour rate, the final pair's 228.590 seconds of runner
  time estimates $0.208, excluding setup/idle/review iterations, shutdown,
  retained storage and Dream API charges. The complete batch includes one short
  render check, two demos, two Dream runs and elapsed preparation time. Use
  session/billing data below for the complete cost; do not add overlapping totals.
- All requested evidence was downloaded and the GPU was idle before stopping.
  Stop requested at 14:18:51 UTC; confirmed STOPPED at 14:24:57 UTC (about
  six minutes to stop). Start request 13:58:17 to confirmed stop is 26m40s;
  conservatively charging the full interval at $3.28/hour estimates **$1.46**
  for this whole batch. This is an elapsed-time estimate, not an invoice, and
  excludes later retained storage and Dream API charges. At 14:25:50 UTC posted
  credits were $196.06, versus $196.14 at 14:03:38 UTC. Billing lags, so this
  eight-cent posted change is NOT the full batch cost. Preserve the retained VM.
  Filtered lifecycle/billing evidence is local in `artifacts/die-v3-session/`.
- Dream credentials were transferred to the authorized team VM without display,
  owner-only under `~/.dreamlabs/`. No credential entered Git, logs or evidence.
  At that point, media and PR authorization were still pending. This is
  superseded by the later explicit authorization and submission entry above.

### 2026-11-03 — scoring v2 correction; GPU batch blocked by capacity

- Operator: repository agent; branch `roll-a-die`. User authorized scoring fixes
  and everything needed for readiness, while retaining the no-PR instruction.
- Shared branch fetched; VM confirmed stopped before requesting restart at
  13:07:55 UTC. Both that attempt and the 13:11 retry failed for regional GPU
  capacity. The planned two repeated demos and direct Dream run did not execute.
  VM confirmed STOPPED at 13:15:58 UTC; no key transfer or environment change.
  Posted credit was $196.16 ($3.84 total spend since the initial $200); billing
  lag/storage prevent attributing the change to these attempts.
- Scorer v2 requires a 90-degree maximum excursion from the verified release
  reference; accumulated rocking no longer earns roll credit. Historical
  trajectories were independently replayed; no evidence was overwritten.
  Results/hashes: `artifacts/die-v2-rescore-001/` and task `VALIDATION.json`.
  Three anonymous compressed trajectories are committed under the task
  `evidence/` directory so other agents/reviewers can reproduce scores offline;
  original raw media and local artifacts remain ignored.
  The demo's first v2 full-score time remains 9.30 s, matching its original
  termination, so no post-termination motion is needed for the corrected score.
- Media-token slot remains empty; user is looking for the Robocurve token.

### 2026-11-03 — first die task and operating agreement

- Code: initial validated implementation `6d38530`, branch `roll-a-die`.
- VM stopped at 12:21:26 UTC; verified stopped at 12:24 UTC. The stop request
  took about eight minutes to finish. Read the live state next session.
- Agreed to reuse one VM daily, develop locally in parallel and batch GPU work.
- User approved Dream-key transfer to the team VM when beneficial; not done yet.
- Recorded the scoring concern above; no task/scorer changes or new GPU trials
  were made during this documentation review. No competition PR is authorized.

For each new entry, record **date, operator/agent, branch/commit, question,
measured result, evidence path, cost basis, decision and remaining uncertainty**.
Update the working guidance when evidence changes it; preserve earlier dated
results and mark superseded conclusions explicitly. Pull the latest notes before
editing, merge both agents' findings, and commit/push the update with the work.
