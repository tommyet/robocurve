"""Evidence-bound dressing rubric. A knot invariant alone is insufficient."""
import math


def score(j):
    required=('evidence_sha256','integrity_checked','intact','simple_knot_verified',
              'released_hold_s')
    if any(k not in j for k in required):
        raise ValueError('incomplete judging record')
    evidence=j['evidence_sha256']
    if not isinstance(evidence,dict) or not {'released_video','front_photo','rear_photo'} <= set(evidence):
        raise ValueError('released video plus front and rear photographs required')
    if any(not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v)
           for v in evidence.values()):
        raise ValueError('invalid evidence digest')
    if j['integrity_checked'] is not True:
        raise ValueError('cloth self-contact and integrity require review')
    hold=j['released_hold_s']
    if type(hold) not in (int,float) or not math.isfinite(hold) or hold<0:
        raise ValueError('invalid released hold measurement')
    for field in ('intact','simple_knot_verified'):
        if type(j[field]) is not bool:
            raise ValueError('visual assessment must be known: '+field)
    if not j['intact'] or not j['simple_knot_verified'] or hold<5.:
        return 0.
    # Dressing measurements are meaningful only after a real retained knot.
    fit_fields=('wide_end_untwisted','narrow_end_hidden','knot_zone_offset_mm',
                'neckband_gap_mm','wide_tip_below_collar_mm','narrow_tip_above_wide_tip_mm')
    if any(k not in j for k in fit_fields):raise ValueError('retained knot needs dressing assessment')
    for field in fit_fields[2:]:
        value=j[field]
        if type(value) not in (int,float) or not math.isfinite(value) or (value<0 and field!='narrow_tip_above_wide_tip_mm'):
            raise ValueError('invalid measurement: '+field)
    for field in fit_fields[:2]:
        if type(j[field]) is not bool:raise ValueError('visual assessment must be known: '+field)
    fitted=(0 <= j['neckband_gap_mm'] <= 15. and 0 <= j['knot_zone_offset_mm'] <= 20.
            and 350. <= j['wide_tip_below_collar_mm'] <= 440.
            and j['narrow_tip_above_wide_tip_mm'] >= 10.)
    dressed=j['wide_end_untwisted'] is True and j['narrow_end_hidden'] is True
    return 1. if fitted and dressed else .5
