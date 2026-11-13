"""Score physical staple-removal observations; missing evidence fails closed."""
import argparse
import json
import math
from pathlib import Path

CHECKS = ("correct_start", "both_sheet_faces_inspected", "staple_intact",
          "sheets_not_modified", "ordinary_contact_only", "evidence_reviewed")


def score(record):
    result = {"score": 0., "record_valid": False, "submission_certified": False, "reasons": []}
    try:
        if record.get("schema") != "staple-judging-v2":
            raise ValueError("Unsupported judging record")
        checks = record["checks"]
        if any(type(checks.get(k)) is not bool for k in CHECKS):
            raise ValueError("All observable checks must be reviewed as true or false")
        legs = record["legs_clear_of_both_sheets"]
        if type(legs) is not int or legs not in (0, 1, 2):
            raise ValueError("Number of entirely withdrawn legs must be 0, 1 or 2")
        measures = {k: record[k] for k in ("maximum_new_tear_mm", "release_seconds")}
        if any(type(v) not in (int,float) or not math.isfinite(v) or v < 0 for v in measures.values()):
            raise ValueError("Finite nonnegative measurements required")
        offsets={key:record[key] for key in ('initial_relative_corner_offset_mm','final_relative_corner_offset_mm')}
        if any(not isinstance(v,(list,tuple)) or len(v)!=2 or any(type(x) not in (int,float) or not math.isfinite(x) for x in v) for v in offsets.values()):
            raise ValueError('Two finite signed tabletop coordinates required for each relative corner offset')
        initial=offsets['initial_relative_corner_offset_mm'];final=offsets['final_relative_corner_offset_mm']
        if math.hypot(initial[0],initial[1]-12.)>1.:
            raise ValueError('Initial corresponding-corner offset must match the fixed12mm stagger within1mm')
        independent_slide=math.hypot(final[0]-initial[0],final[1]-initial[1])
        result['relative_displacement_change_mm']=independent_slide
        if type(record.get("any_new_damage_away_from_holes")) is not bool:
            raise ValueError("Inspect both full sheets for new damage away from original holes")
        result["record_valid"] = True
        result["reasons"] = [k for k in CHECKS if not checks[k]]
        if measures["maximum_new_tear_mm"] > 2.:
            result["reasons"].append("A tear extends over 2 mm beyond an original hole")
        if record["any_new_damage_away_from_holes"]:
            result["reasons"].append("New tear, cut or puncture away from the original holes")
        if result["reasons"]:
            return result
        if legs == 2 and independent_slide >= 30. and measures["release_seconds"] >= 3.:
            result["score"] = 1.
        elif legs >= 1:
            result["score"] = .5
    except (KeyError, TypeError, ValueError) as error:
        result["reasons"].append(str(error))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("record", type=Path)
    args = p.parse_args()
    print(json.dumps(score(json.loads(args.record.read_text())), indent=2))
