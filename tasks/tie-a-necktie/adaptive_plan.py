"""Keep future, unplanned actions continuous after a measured plan update."""
from copy import deepcopy


def hold_suffix(frames, planned_through):
    if not 1 <= planned_through <= len(frames):
        raise ValueError('A nonempty planned prefix is required')
    endpoint = deepcopy(frames[planned_through - 1])
    endpoint['stage'] = 'hold while awaiting measured continuation'
    for index in range(planned_through, len(frames)):
        frames[index] = deepcopy(endpoint)
