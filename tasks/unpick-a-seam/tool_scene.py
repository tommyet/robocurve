"""Tool-only coupon: the exact seam ripper and YAM station, without fabric.

This intentionally cannot measure seam retention, damage, cutting or task score.
The ordinary scene's spawner still authors the tool and its physical colliders.
"""
from scene import SCENE,OBJECTS

OBJECTS=[obj for obj in OBJECTS if obj.name in ('ripper_handle','ripper_blade')]
SCORE_OVER='end'
def score(objects):return 0.
def success(objects):return False
