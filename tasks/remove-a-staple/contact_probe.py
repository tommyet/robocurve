"""Quasistatic jaw/clinched-leg contact probe, with a permanently fixed root.

This deliberately isolates one unclinching mechanism. A flat diagnostic jaw
presses a 3 mm steel leg upward through unilateral tip contact. The root stands
in for a supported paper hole and is NOT a complete sheet/staple scene. No
extraction, paper survival or robot success is inferred from this probe.
"""
from dataclasses import asdict
import argparse
import copy
import json
from pathlib import Path
import math
import numpy as np
from materials import PlasticHinge, SteelSpec


def run_probe(*, steel=None, jaw_path_m=None, leg_length_m=.003,
              jaw_contact_stiffness_n_per_m=100_000., jaw_x_range_m=(0., .004)):
    steel = steel or SteelSpec()
    hinge = PlasticHinge(steel)
    if leg_length_m <= 0 or jaw_contact_stiffness_n_per_m <= 0:
        raise ValueError("Positive length and stiffness required")
    jaw_path = np.r_[np.linspace(-.0005, .0025, 121), np.linspace(.0025, -.0005, 121)[1:]] if jaw_path_m is None else np.asarray(jaw_path_m, dtype=float)
    if not np.isfinite(jaw_path).all():
        raise ValueError("Finite jaw positions required")
    result = []
    for jaw_z in jaw_path:
        def candidate(angle):
            material = copy.copy(hinge)
            response = material.advance(angle)
            x, z = leg_length_m*math.cos(angle), leg_length_m*math.sin(angle)
            overlap = max(0., float(jaw_z)-z) if jaw_x_range_m[0] <= x <= jaw_x_range_m[1] else 0.
            normal = jaw_contact_stiffness_n_per_m*overlap
            residual = response["moment_nm"]-normal*x
            return residual, material, response, normal, x, z
        # This probe's angle interval excludes folding back over the root.
        lo, hi = 0., math.pi/2
        a, b = candidate(lo), candidate(hi)
        if a[0] > 1e-10 or b[0] < -1e-10:
            raise RuntimeError("Contact equilibrium is outside this bounded probe")
        for _ in range(70):
            mid = (lo+hi)/2
            if candidate(mid)[0] < 0:
                lo = mid
            else:
                hi = mid
        angle = (lo+hi)/2
        residual, hinge, response, force, x, z = candidate(angle)
        result.append({"jaw_z_m": float(jaw_z), "angle_rad": angle, "tip_x_m": x,
                       "tip_z_m": z, "jaw_contact_force_n": force,
                       "moment_residual_nm": residual, **response})
    return {
        "schema": "staple-jaw-contact-probe-v1", "calibrated": False,
        "evidence_type": "CPU one-leg contact probe with fixed root; not a robot trial or staple extraction",
        "steel_spec": asdict(steel), "leg_length_m": leg_length_m,
        "jaw_contact_stiffness_n_per_m": jaw_contact_stiffness_n_per_m,
        "samples": result,
        "maximum_jaw_force_n": max(r["jaw_contact_force_n"] for r in result),
        "residual_leg_angle_rad": result[-1]["angle_rad"],
        "permanent_material_angle_rad": result[-1]["plastic_angle_rad"],
        "maximum_moment_residual_nm": max(abs(r["moment_residual_nm"]) for r in result),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: v for k,v in result.items() if k != "samples"}, indent=2))
