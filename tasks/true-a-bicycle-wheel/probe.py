"""Run the CPU mechanical probe; never starts a simulator or a paid service."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
from mechanics import WheelModel, starting_turn_errors


def compact(state):
    return {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in state.items()}


def probe():
    model = WheelModel()
    turns = starting_turn_errors(model.spec)
    one = np.zeros(model.spec.spokes)
    one[0] = .25
    forces = np.zeros((model.spec.spokes, 3))
    forces[0, 2] = .5*9.80665
    return {
        "schema": "wheel-mechanics-probe-v1",
        "evidence_type": "CPU constitutive/equilibrium probe; not a robot trial",
        "calibrated": False,
        "spec": asdict(model.spec),
        "balanced": compact(model.equilibrium(np.zeros(model.spec.spokes))),
        "starting_imbalance": compact(model.equilibrium(turns)),
        "one_quarter_turn": compact(model.equilibrium(one)),
        "reversed_adjustment": compact(model.equilibrium(-one)),
        "uniform_loosen_four_turns": compact(model.equilibrium(np.full(model.spec.spokes, -4.))),
        "known_reset_restored": compact(model.equilibrium(turns-turns)),
        "half_kg_axial_assessor_load": compact(model.equilibrium(np.zeros(model.spec.spokes), external_forces_n=forces)),
        "scope": "The last case algebraically restores the reference rest lengths. It is not an autonomous truing policy or demonstration.",
        "slack_load_warning": "The geometric prestress tangent is frozen at the reference state. Once any spoke becomes slack, load/stability predictions are out of scope; the slack case is only an adversarial warning, not a faithful loose-wheel load model.",
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    data = probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2)+"\n")
    print(json.dumps({name: {k: v for k, v in data[name].items() if k in ("lateral_peak_to_peak_m", "dish_offset_m", "radial_peak_to_peak_m", "maximum_force_residual_n", "slack_spokes")} for name in ("balanced", "starting_imbalance", "one_quarter_turn", "uniform_loosen_four_turns")}, indent=2))
