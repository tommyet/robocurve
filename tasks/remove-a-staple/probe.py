"""CPU material probes only. Does not demonstrate staple removal."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
from materials import SteelSpec, PlasticHinge, PaperSpec, PaperBond, clinched_staple_centerline


def probe():
    steel, paper = SteelSpec(), PaperSpec()
    hinge = PlasticHinge(steel)
    loading = [dict(angle_rad=float(a), **hinge.advance(float(a))) for a in np.linspace(0., .8, 161)]
    # Zero moment occurs at the residual plastic angle; do not force it to zero.
    unloaded = hinge.advance(hinge.plastic_angle_rad)
    bond = PaperBond(paper)
    openings = np.linspace(0., paper.final_opening_m, 1001)
    forces = [bond.advance(float(d))["force_n"] for d in openings]
    measured_energy = float(np.trapezoid(forces, openings))
    return {
        "schema": "staple-material-probe-v1", "calibrated": False,
        "evidence_type": "CPU material-law and geometry probe, not extraction or a robot trial",
        "steel_spec": asdict(steel), "paper_spec": asdict(paper),
        "hinge_stiffness_nm_per_rad": steel.stiffness_nm_per_rad,
        "initial_yield_moment_nm": steel.initial_yield_moment_nm,
        "plastic_bending": loading, "unloaded_at_residual_angle": unloaded,
        "paper_complete_fracture_work_j": measured_energy,
        "paper_expected_fracture_work_j": paper.fracture_energy_j_per_m2*paper.area_m2,
        "paper_reclosure": bond.advance(0.),
        "paper_reopening": bond.advance(paper.opening_at_peak_m),
        "initial_staple_centerline_m": clinched_staple_centerline().tolist(),
        "unimplemented": ["Coupled 3D contact and paper-hole geometry", "Contact-driven jaw leverage", "Paper bending and mixed-mode crack propagation", "Isaac/YAM integration", "Robot policy", "Physical calibration"],
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    data = probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2)+"\n")
    print(json.dumps({k: data[k] for k in ("evidence_type", "hinge_stiffness_nm_per_rad", "initial_yield_moment_nm", "unloaded_at_residual_angle", "paper_complete_fracture_work_j", "paper_expected_fracture_work_j", "unimplemented")}, indent=2))
