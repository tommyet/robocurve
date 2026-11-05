"""Render the actual printable STL assemblies as a static review illustration.

Run: .venv/bin/python -m brick_workbench.cad.render_targets
The image illustrates target poses; it is not evidence of simulator success.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/robocurve-matplotlib")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import trimesh

from brick_workbench.geometry import BODY_HEIGHT
from brick_workbench.variants import VARIANTS


BLUE = np.array([.16, .40, .90])
RED = np.array([.94, .27, .15])
LABELS = (
    ("2×2 + 2×2 · full overlap", "All four lower studs engaged"),
    ("1×1 + 1×1 · full overlap", "The single lower stud engaged"),
    ("1×1 on 2×2 · corner", "One lower stud engaged; three exposed"),
    ("2×2 + 2×2 · offset", "Two lower studs engaged; two exposed"),
)


def _triangles(shape, translation, color):
    cad = Path(__file__).resolve().parent
    name = f"brick_{shape[0]}x{shape[1]}.stl"
    mesh = trimesh.load(cad / name, file_type="stl", force="mesh", process=True)
    if not mesh.is_watertight:
        raise ValueError(f"invalid input STL: {name}")
    light = np.array([-.5, -.65, 1.])
    light /= np.linalg.norm(light)
    brightness = .73 + .27 * np.maximum(mesh.face_normals @ light, 0)
    colors = brightness[:, None] * color
    return mesh.triangles + np.asarray(translation), colors


def _render_surface(faces: np.ndarray, colors: np.ndarray) -> np.ndarray:
    """Orthographic CPU triangle rasterizer with a real per-pixel depth buffer.

    A depth buffer is needed because the STL has hollow sockets; sorting entire
    triangles by average depth can incorrectly show internal faces through walls.
    Units remain millimetres and every panel uses the same pixels/mm scale.
    """
    width, height, scale = 1000, 650, 10.5
    elevation, azimuth = np.radians((28, -135))
    toward_eye = np.array([np.cos(elevation) * np.cos(azimuth),
                           np.cos(elevation) * np.sin(azimuth), np.sin(elevation)])
    right = np.array([-toward_eye[1], toward_eye[0], 0.])
    right /= np.linalg.norm(right)
    up = np.cross(toward_eye, right)
    camera = faces @ np.column_stack((right, up, toward_eye))
    bounds = camera.reshape(-1, 3)
    centre = (bounds.min(axis=0) + bounds.max(axis=0)) / 2
    screen = camera.copy()
    screen[:, :, 0] = (camera[:, :, 0] - centre[0]) * scale + width / 2
    screen[:, :, 1] = -(camera[:, :, 1] - centre[1]) * scale + height / 2
    pixels = np.full((height, width, 3), 255, dtype=np.uint8)
    depths = np.full((height, width), -np.inf)
    normals = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    for triangle, color, normal in zip(screen, colors, normals):
        if normal @ toward_eye <= 1e-12:
            continue
        xmin = max(0, int(np.floor(triangle[:, 0].min())))
        xmax = min(width - 1, int(np.ceil(triangle[:, 0].max())))
        ymin = max(0, int(np.floor(triangle[:, 1].min())))
        ymax = min(height - 1, int(np.ceil(triangle[:, 1].max())))
        if xmin > xmax or ymin > ymax:
            continue
        x0, y0, z0 = triangle[0]
        x1, y1, z1 = triangle[1]
        x2, y2, z2 = triangle[2]
        denominator = (y1-y2)*(x0-x2) + (x2-x1)*(y0-y2)
        if abs(denominator) < 1e-12:
            continue
        yy, xx = np.mgrid[ymin:ymax+1, xmin:xmax+1]
        xx, yy = xx+.5, yy+.5
        a = ((y1-y2)*(xx-x2) + (x2-x1)*(yy-y2)) / denominator
        b = ((y2-y0)*(xx-x2) + (x0-x2)*(yy-y2)) / denominator
        c = 1-a-b
        z = a*z0 + b*z1 + c*z2
        region = depths[ymin:ymax+1, xmin:xmax+1]
        visible = (a >= -1e-10) & (b >= -1e-10) & (c >= -1e-10) & (z > region)
        region[visible] = z[visible]
        pixels[ymin:ymax+1, xmin:xmax+1][visible] = np.round(color*255).astype(np.uint8)
    return pixels


def render(output: Path) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13})
    fig = plt.figure(figsize=(14, 10), dpi=180, facecolor="white")
    fig.text(.055, .948, "Four assembly targets", fontsize=26, weight="bold", color="#142234")
    fig.text(.055, .910, "CAD targets — not simulator results", fontsize=15, color="#4c5b6d")
    for x, color, text in ((.695, BLUE, "Lower brick"), (.838, RED, "Upper brick")):
        fig.add_artist(Rectangle((x, .923), .015, .015, transform=fig.transFigure, color=color, lw=0))
        fig.text(x + .022, .923, text, fontsize=11, va="bottom", color="#344256")

    positions = ((.04, .47), (.525, .47), (.04, .075), (.525, .075))
    for (variant, (title, subtitle), (left, bottom)) in zip(VARIANTS.values(), LABELS, positions):
        fig.text(left + .018, bottom + .365, title, fontsize=16, weight="bold", color="#17263a")
        fig.text(left + .018, bottom + .335, subtitle, fontsize=11, color="#526174")
        ax = fig.add_axes((left, bottom, .435, .325), facecolor="white")
        height = BODY_HEIGHT * 1000
        offset = np.array(variant["target_offset"]) * 1000
        lower, lower_colors = _triangles(variant["lower_shape"], (0, 0, height / 2), BLUE)
        upper, upper_colors = _triangles(variant["upper_shape"], (*offset, 1.5 * height), RED)
        faces = np.concatenate([lower, upper])
        colors = np.concatenate([lower_colors, upper_colors])
        ax.imshow(_render_surface(faces, colors), interpolation="lanczos")
        ax.set_axis_off()
    fig.text(.055, .035,
             "Actual printable STL geometry  ·  16 mm stud pitch  ·  Seated poses before the lift-and-release test",
             fontsize=11, color="#526174")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/brick-targets.png"))
    args = parser.parse_args()
    render(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
