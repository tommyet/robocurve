# Mash cooked potato

Mash the cooked potato in the bowl until no large lumps remain. Keep the potato in the bowl.

The revised portion requires new native demo and Dream-1 evidence. Earlier 58.32 g runs are retained as development history and do not validate this 129.6 g revision.

## Setup and reset

About 130 g of peeled, cooked potato in twelve 21–23 mm cubes (120–140 g total), arranged in a 4 × 3 grid in a stainless-steel bowl (200 mm inside diameter, 75 mm deep). A 140 g wire masher has a 75 × 60 mm head and a 180 mm handle. The bowl is centred between the arms; the masher stands on its head 170 mm toward the right arm. Both hands start open.

The simulated portion is **129.6 g**: twelve clusters of 27 particles, each 0.4 g. Each cluster has a 21.4 mm axial envelope; the coarse spherical particles approximate a solid cooked cube, not hollow food. Twelve ideal 22 mm cubes occupy 127.776 mL; 129.6 g implies 1.014 g/mL, consistent in scale rather than the old 58.32 g mismatch. The bowl is 300 g, centred 340 mm forward; cube centres are 24 mm apart. The tool may be released in the bowl.

Use peeled floury potato from one batch. Cut 24 mm raw cubes, simmer for 12–15 minutes until a fork passes through, drain for 2 minutes and cool to 18–22 °C. Select twelve intact cooked cubes with each edge 21–23 mm and combined mass 120–140 g. Reject pieces or the batch if both limits cannot be met. Add no milk, butter or oil. Place them in the photographed 4 × 3 grid. Use fresh pieces and clean the equipment and food-safe gripper covers each trial.

## Scoring

Losing over 5% of the starting potato mass scores 0. Otherwise weigh retained potato and lumps larger than 9 mm. The fine-mass fraction earns 0.25 at 50%, 0.5 at 75%, and 1.0 at 95% with both hands released for 3 seconds. At 95% while still held, score 0.5; holding never increases a lower score. All other outcomes score 0. Use a 0.1 g kitchen scale and 9 mm reference grid; measure each lump’s largest dimension.

For physical judging, collect and weigh the retained food without further mashing. Gently separate the pieces larger than the grid threshold and weigh them. The fine fraction is `(retained mass − oversized-lump mass) / retained mass`. Judge the largest dimension of each lump, not its orientation on the grid. The native equivalent measures connected components and their largest particle-to-particle extent plus particle diameter. All particles have equal mass.

## Material approximation

Each of twelve chunks contains 27 cohesive 7 mm particles. Native compression during masher contact reduces cohesion. Eight overlapping local cells per chunk measure compressive strain; full local failure removes that chunk's remaining cohesion, and otherwise the bond breaking force decreases. The rule never writes particle poses. Native contacts, gravity and friction handle the fragments after separation.

The parameters are an uncalibrated cooked-tissue approximation, not a measurement of potato rheology. Released particles represent small soft lumps, not a smooth paste. Contact-gated damage, 20/s translational damping, finite cohesion and the 0.5 m/s particle speed cap are identical for the scripted and Dream runs. The demo uses observed food and tool poses to aim ordinary bounded joint actions and stops pressing when the outcome is reached; no hand attachment or success-triggered object motion is used.

SPARTA evaluates food mashing: https://arxiv.org/html/2509.24129v2 . Its overlap is an unresolved novelty risk. Tool pickup, retention scoring or changing the food name do not by themselves establish novelty, and this submission makes no contrary claim.

## Run and rescore

Use the pinned Python 3.12 / Isaac 6.1 / YAM installation in `ENVIRONMENT.json`, with the adapter installed. From the repository root:

```sh
python tasks/mash-cooked-potato/make_plan.py
OMNI_KIT_ACCEPT_EULA=YES python tasks/mash-cooked-potato/run.py --mode demo --out /tmp/potato-demo
OMNI_KIT_ACCEPT_EULA=YES python tasks/mash-cooked-potato/run.py --mode dream --out /tmp/potato-dream
python tasks/mash-cooked-potato/rescore.py /tmp/potato-demo
python tasks/mash-cooked-potato/rescore.py /tmp/potato-dream
```

The control limit is 2,400 actions (120 seconds at 20 Hz). The layout is fixed and uses no random seed. The scripted plan has a 2,380-action upper bound and can finish earlier once the measured outcome is released. Dream receives the full limit and standard three camera views plus joint observations.

The CPU rescorer verifies frozen source hashes, trace continuity, joint/rate bounds, damage progression, native break events and the outcome. It is an evidence audit, not a physics replay. Native camera videos must also be reviewed. `VALIDATION.json` records the audit and measurements. On an RTX PRO 6000 Blackwell, the demo took 390 seconds and Dream took 1627 seconds including 50 policy requests. Runtime varies with API latency.
