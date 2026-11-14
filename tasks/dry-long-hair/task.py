"""Dry every side and inner layer of the long-haired mannequin with the dryer.

Operate the real slider, expose wet regions by moving locks, avoid excessive
heating, then switch off and put the dryer down. Use run.py for articulated
locks, geometry-dependent heating, actual switch telemetry and scoring.
"""
from yam_arena.task_file import Box
from config import *
SCENE='station';SUCCESS_HOLD_S=0.;SCORE_OVER='end'
OBJECTS=[Box('head',pos=HEAD,size=(.13,.13,.13)),
 Box('dryer',pos=DRYER_START,size=(.12,.06,.14),mass=.48),
 Box('switch',pos=SWITCH_START,size=(.014,.010,.006),mass=.003),
 Box('dryer_pad',pos=(.23,-.16,TOP+.001),size=(.18,.14,.002),color=(.75,.2,.35)),
 Box('mat',pos=(.32,0,TOP+.001),size=(.58,.60,.002),color=(.24,.27,.30))]
for k in range(LOCKS):
 for j in range(SEGMENTS):OBJECTS.append(Box(f'hair_{k}_{j}',pos=segment(k,j),size=(.008,.008,LENGTH),mass=DRY_MASS_PER_SEGMENT+PATCHES_PER_SEGMENT*WATER_PER_PATCH))
_tracker=None
_diagnostic=True
def score(objects):return 0. if _diagnostic or _tracker is None else _tracker.value
def success(objects):return score(objects)==1.
