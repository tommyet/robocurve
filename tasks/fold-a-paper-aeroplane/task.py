"""Flat, uncreased sheet on a YAM station; ruler is a fixed judging reference."""
from yam_arena.task_file import Box
SCENE="station"
OBJECTS=[Box("ruler",pos=(.30,-.20,.7485),size=(.100,.015,.002),color=(.35,.40,.42))]
def success(objects):return False
