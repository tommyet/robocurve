# Untie a loose overhand knot

Untie the overhand knot in the cord. Leave the cord on the table without any crossings, then let go.

Removing a real knot from a flexible cord requires finding and feeding an end back through the loop. Simply moving crossed strands apart is not enough.

## Run and score

Use Python 3.12 and the Isaac 6.1 / YAM environment pinned in `ENVIRONMENT.json`,
including its public asset-root patch. An NVIDIA GPU renders the cameras.
From the repository root:

```sh
OMNI_KIT_ACCEPT_EULA=YES python tasks/unknot-a-cable/run.py --mode demo --out /tmp/unknot-a-cable-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/unknot-a-cable/run.py --mode dream --out /tmp/unknot-a-cable-dream
python tasks/unknot-a-cable/rescore.py /tmp/unknot-a-cable-demo
```

The layout is fixed; no random seed is used. The reset node geometry settles
under native gravity for one second before step 0 and the initial knot check. Each action is an ordinary bounded
14-element joint/gripper command at 20 Hz. The scripted demo follows a saved
joint plan and reads only the robot's joint positions for tracking. It never
reads the task state or scorer. Dream receives the normal three camera views
and robot joint observations. Its key comes from its private credential store
or `DREAM_API_KEY`; run one Dream session per key at a time.

The cord moves through native contact forces; its measured state supplies the score. `run.json` gives the score and wall runtime. Outputs also
include complete measured traces, source hashes, three judging videos, a policy
camera video and initial/final photographs. `rescore.py` verifies frozen source
hashes and recomputes topology from the measured native cord to check the recorded result. Always
inspect the videos as well. This task requires native PhysX; `--cpu-preview` cannot run its cord physics.

## Setup and judging

One 1.075 m long, 10 mm diameter blue polyester cord, mass 80 g, lies on a wooden table in a loose overhand knot. Its two tips are marked yellow and red. The knot is centred about 28 cm in front of the robot; both free tips point towards the left-hand side of the table. Both grippers start open. The setup photograph and initial-nodes.json specify this single reproducible layout. No clamps, pins or hidden anchors hold the cord.

1.0 if the original overhand has been removed, the intact cord has no crossings in an overhead view, its surface is no more than 2.5 cm above the table, and both hands have released it for three seconds. 0.5 if the knot has been removed and the cord released for three seconds but it still has loose crossings or is not laid down. Otherwise 0. A broken cord or an invalid initial knot scores 0. Judge the knot and crossings from overhead and side video with a ruler; topology analysis supplies an additional simulation check.

Reset: Retie the same loose overhand and restore the photographed layout, or reset the scene. Nothing is consumed.

## Model limits

The cord is a native PhysX chain of 86 rounded capsules with bending constraints, gravity, friction, gripper contact and non-neighbour self-collision, simulated at 240 Hz. It is freely movable; no ideal grasp attachments, object teleports or scripted untying forces are used. A coarse link chain approximates bending, torsion and compression rather than individual fibres. Static open-curve topology uses several closures and can be ambiguous; the final uncrossed, released cord and video remain the primary physical judging criteria.

Final native run counts, scores, timings and media are recorded in
`VALIDATION.json` once validation is complete.
