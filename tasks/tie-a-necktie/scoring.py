"""Evidence-bound dressing rubric. A knot invariant alone is insufficient."""
import math


def score(j):
    required=('evidence_sha256','integrity_checked','intact','four_in_hand_verified',
              'released_hold_s','wide_face_out','narrow_end_hidden','knot_zone_offset_mm',
              'neckband_gap_mm','wide_tip_below_collar_mm','narrow_tip_above_wide_tip_mm')
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
    for field in ('released_hold_s','knot_zone_offset_mm','neckband_gap_mm','wide_tip_below_collar_mm','narrow_tip_above_wide_tip_mm'):
        value=j[field]
        if type(value) not in (int,float) or not math.isfinite(value) or (value < 0 and field!='narrow_tip_above_wide_tip_mm'):
            raise ValueError('invalid measurement: '+field)
    for field in ('intact','four_in_hand_verified','wide_face_out','narrow_end_hidden'):
        if type(j[field]) is not bool:
            raise ValueError('visual assessment must be known: '+field)
    if j['intact'] is not True or j['four_in_hand_verified'] is not True or j['released_hold_s'] < 5.:
        return 0.
    fitted=(0 <= j['neckband_gap_mm'] <= 10. and 0 <= j['knot_zone_offset_mm'] <= 15.
            and 280. <= j['wide_tip_below_collar_mm'] <= 320.
            and j['narrow_tip_above_wide_tip_mm'] >= 10.)
    dressed=j['wide_face_out'] is True and j['narrow_end_hidden'] is True
    return 1. if fitted and dressed else .5
