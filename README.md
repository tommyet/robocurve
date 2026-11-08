# Robocurve Benchmarking Program: tasks

This is our team development fork, [tommyet/robocurve](https://github.com/tommyet/robocurve).
`main` contains our task code, reusable tools and shared notes. Competition submissions go to
[robocurve/benchmark-tasks](https://github.com/robocurve/benchmark-tasks), one task per pull request.
Program details, the review checklist and the simulation walkthrough are at https://tasks.robocurve.org.

**Using a coding agent?** Open it in your fork: [AGENTS.md](AGENTS.md) tells it how to build, upload and submit
tasks, and most agents read it automatically (Claude Code reads it through [CLAUDE.md](CLAUDE.md)).

## Team quickstart

Clone the team fork and make a development branch from its current `main`:

```bash
git clone https://github.com/tommyet/robocurve.git
cd robocurve
git switch -c codex/my-new-task
```

For an existing clean checkout, fetch `origin`, switch to `main` and run
`git pull --ff-only origin main` before creating the development branch.

Ask your agent to read [AGENTS.md](AGENTS.md) and [TEAM_LEARNINGS.md](TEAM_LEARNINGS.md)
first. The shared notes cover the current simulator, GPU costs, submission status and known
limitations. Check the live task board before choosing a new objective.

- Start with [the 2×2 task](tasks/join-two-2x2-blocks/README.md) for the scene, runner,
  scorer and evidence format. [The batch review](docs/brick-batch-review.md) records design tradeoffs;
  use the dated shared notes for current review status.
- [The table-method overhand knot](tasks/tie-overhand-knot/README.md) includes a
  full-score bimanual demo, capsule-cord model and independent geometry audits.
  It uses no fixtures or external tightening forces. Read its fidelity limits
  before reusing the rope model. [PR #1153](https://github.com/robocurve/benchmark-tasks/pull/1153)
  was received as **TK-VWRHTS** and is waiting for review.
- `brick_workbench/` contains reusable brick geometry, scoring and CAD code. Its
  `build_tasks.py` regenerates all four existing brick tasks and preserves their previous scores
  and media IDs. Create a new task folder deliberately; do not use that builder as a generic
  initializer or reuse another task's validation claims.
- Local scoring needs Python and NumPy, with no GPU or API key:

  ```bash
  python3 -m venv .venv
  .venv/bin/python -m pip install numpy
  .venv/bin/python tasks/join-two-2x2-blocks/replay.py tasks/join-two-2x2-blocks/evidence/demo.jsonl.gz
  ```

  The included demo scores 1.0. Simulator runs require the competition environment;
  on the shared VM, source `/data/IsaacLab-Arena/yam.env` and follow the task's run commands.
  Coordinate VM use, use fresh artifact directories and batch GPU trials.
- The retained VM was updated and validated on November 7. For the brick/die tasks
  with Inspect 1.0, run `python tools/prepare_review_media.py RUN` after exporting
  camera videos and before the task's `render_review.py`. The rope runner records
  its own review camera; follow its README. See the shared notes for version details.
- Credentials, private reference PDFs, full videos and raw trial artifacts are intentionally
  ignored. A clone includes code, CAD and curated numeric evidence. Arrange Brev access and
  credentials privately; full recordings are backed up on Tom's machine and the retained VM.

Development branches start from this fork's `main`. **Competition submission branches start
from `upstream/main` and contain only one `tasks/<name>/` folder.** Keep team notes and other
tasks out of those PRs. Opening an upstream PR requires explicit user approval.

## Submitting a task

1. **Upload your videos and screenshot** with the script in this repository. It uploads them to the task
   board and writes the media ID into your `task.json`:

       export ROBOCURVE_TEAM=T-39 ROBOCURVE_TOKEN=...    # use the private team token; never commit it
       python tools/upload_media.py tasks/lamp-task --video model_run.mp4 --demo demo.mp4 --screenshot setup.png

   Videos must be H.264 MP4 (`ffmpeg -i in.mp4 -c:v libx264 -pix_fmt yuv420p -movflags +faststart out.mp4`),
   up to 50 MB each. The demo is required when the Dream-1 run doesn't reach full score.

2. **Add one task folder on your development branch** (upload into it, as above):

       tasks/<task-name>/
         task.json     the task's details, including your media ID
         README.md     the commands to run and score a trial, the runtime per trial, and any seeds
         ...           your scene and scoring code

3. **After explicit submission approval, create an isolated worktree** from the competition's
   `main`. First commit the validated task, including its uploaded media ID, on your development
   branch. This example assumes that work has reached the team fork's `main`; substitute its
   development branch if needed. Add the `upstream` remote once if it is not already configured.
   Replace the example task and branch names with your new task:

       git remote add upstream https://github.com/robocurve/benchmark-tasks.git
       git fetch upstream
       git worktree add -b codex/submit-lamp-task ../robocurve-submit-lamp-task upstream/main
       cd ../robocurve-submit-lamp-task
       git restore --source=main -- tasks/lamp-task
       git add tasks/lamp-task && git commit -m "Add lamp task"
       git diff --stat upstream/main...HEAD

   Verify that the diff contains only the intended task folder, then push and open its PR:

       git push -u origin codex/submit-lamp-task
       gh pr create --repo robocurve/benchmark-tasks --base main --head tommyet:codex/submit-lamp-task --fill

Within a minute or two, a comment on your pull request says either that the task was received (with its
ID) and is waiting for review, or what to fix. Push to the same branch to try again.

## task.json

    {
      "title": "Extend a telescoping lamp",
      "category": "Societal relevance",
      "keywords": ["bimanual", "telescoping"],
      "instruction": "Extend the lamp to its full height.",
      "context": "Optional: 1-2 lines on why the task matters, beyond the instruction.",
      "setup": "Every object with type, size and material, in one fixed starting layout matching the screenshot.",
      "scoring": "0.25 at 2 cm of extension; 0.5 at 4 cm; 1.0 at 6 cm or more with the base flat.",
      "run_limit": "2,400 steps (2 minutes at 20 Hz)",
      "reset_notes": "Optional: anything consumed or hard to restore between trials.",
      "fidelity": "How faithful or approximate the simulation is, and what's simplified.",
      "scores": "Dream-1 run: 0.0; demo: 1.0",
      "media": "M-7K2Q9F"
    }

(`media` is filled in by the upload script. If it's missing, the task board uses your team's latest upload
tagged with the task's folder name.)

- **Required:** title, category, instruction, setup, scoring, run_limit, fidelity, scores and media.
- **category:** `Impact on jobs`, `Impact on AI timelines`, `Safety and alignment`, `Societal relevance` or `Other`.
- **run_limit:** the most actions a model gets: control steps for action policies like Dream-1 (20 a second),
  or model calls for language-model agents. Choose what the task reasonably needs.
- **scores:** the score each video reached, as your scorer reported it.

## Rules

- **One task per pull request,** one folder under `tasks/`. Up to 20 submissions in any 24 hours.
- **Accepted:** we merge your pull request. **Not accepted:** you get feedback and the pull request stays
  open, labeled "Not accepted"; push your changes to it to submit a revision; don't open a new
  pull request.
- **The first team to submit a task owns it** while it's pending, and, if it isn't accepted, for 48 hours
  after the review while the team revises it (shown on the board as "Being revised"), unless the review
  finds it was a low-effort placeholder. If no revision arrives within 48 hours, the hold lapses and
  another team can claim the idea. Near-duplicates from other teams aren't accepted while a team holds
  an idea.
- **A task waiting for review doesn't change:** pushes made before the review aren't picked up. To change
  it before then, close the pull request (which withdraws it) and open a new one.
- **Repeated low-quality submissions may result in disqualification.**
- **Review is blind:** the task's text, screenshot and videos must not identify your team. Your code may.
- Pull requests are matched to teams by their author, so open them from a GitHub account your team gave us.
