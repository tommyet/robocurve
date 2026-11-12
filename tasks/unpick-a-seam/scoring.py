"""Draft final-state rubric. Cut events alone are not released stitches."""
import math


def assess(*,released_stitches,minimum_patch_gap_m,blade_crossed_fabric,
           maximum_new_tear_m,complete,thread_bridge_present,tools_clear):
    vals=[minimum_patch_gap_m,maximum_new_tear_m]
    if (type(released_stitches) is not int or not 0<=released_stitches<=6
            or not all(type(v) in (float,int) and math.isfinite(v) and v>=0 for v in vals)
            or not all(type(v) is bool for v in (blade_crossed_fabric,complete,thread_bridge_present,tools_clear))):
        return {'score':0.,'reason':'invalid measurements'}
    if not complete or blade_crossed_fabric or maximum_new_tear_m>.002:
        return {'score':0.,'reason':'incomplete evidence or fabric damage'}
    if released_stitches==6 and minimum_patch_gap_m>=.030 and not thread_bridge_present and tools_clear:
        return {'score':1.,'reason':'both intact patches separated by at least 30 mm'}
    score=.75 if released_stitches==6 else .5 if released_stitches>=4 else .25 if released_stitches>=2 else 0.
    return {'score':score,'reason':'released stitches confirmed in final inspection'}
