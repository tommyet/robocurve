"""Competition station for a static, unscored optical experiment."""
from yam_arena.task_file import Box
SCENE = "station"
# The adapter requires one registered object; this fixed marker is outside
# the left wrist's optical test area and does not assist the lens.
OBJECTS = [Box("reference_marker", pos=(.1,-.35,.753), size=(.01,.01,.01))]
