"""Score a completed physical judging record. Thresholds are provisional.

This does not read simulator hidden state or grant a submission certificate.
Measurements must come from the whole-wheel released check in JUDGING.md.
"""
import argparse
import json
import math
from pathlib import Path

CHECKS = ("correct_start", "whole_revolution_visible", "hands_and_tools_clear",
          "wheel_and_stand_intact", "nipples_only_adjusted", "load_test_complete",
          "spoke_load_test_complete", "evidence_reviewed")


def score(record):
    result = {"score": 0., "record_valid": False, "submission_certified": False,
              "thresholds_calibrated": False, "reasons": []}
    try:
        if record.get("schema") != "wheel-judging-v1":
            raise ValueError("Unsupported judging record")
        checks = record["checks"]
        if any(type(checks.get(k)) is not bool for k in CHECKS):
            raise ValueError("All observable checks must be reviewed as true or false")
        names = ("lateral_runout_mm", "radial_runout_mm", "dish_offset_mm",
                 "maximum_loaded_deflection_mm", "maximum_residual_deflection_mm")
        values = {k: record[k] for k in names}
        if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in values.values()):
            raise ValueError("All measurements must be finite nonnegative millimetres")
        deflections = record["spoke_midspan_deflections_mm"]
        if not isinstance(deflections, list) or len(deflections) != 32 or any(
                type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in deflections):
            raise ValueError("All 32 spoke midspan deflections must be measured")
        result["record_valid"] = True
        failures = [k for k in CHECKS if not checks[k]]
        if values["radial_runout_mm"] > 1.: failures.append("radial runout exceeds 1.0 mm")
        if values["dish_offset_mm"] > .5: failures.append("dish offset exceeds 0.5 mm")
        if values["maximum_loaded_deflection_mm"] > 2.: failures.append("rim fails provisional proof-load deflection")
        if values["maximum_residual_deflection_mm"] > .2: failures.append("rim does not recover after load")
        if min(deflections) < .15 or max(deflections) > 1.2:
            failures.append("spoke load deflection outside provisional 0.15 to 1.2 mm service envelope")
        result["reasons"] = failures
        if not failures:
            r = values["lateral_runout_mm"]
            result["score"] = 1. if r <= .5 else .5 if r <= 1.5 else 0.
    except (KeyError, TypeError, ValueError) as e:
        result["reasons"].append(str(e))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("record", type=Path)
    args = p.parse_args()
    print(json.dumps(score(json.loads(args.record.read_text())), indent=2))
