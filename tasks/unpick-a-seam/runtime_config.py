"""Explicit numerical/geometry choices for development previews.

The default remains the draft setup. A diagnostic runner may select the coarse
thread and refined mesh before scene construction and must record these values.
No setting is changed after native simulation begins.
"""
from dataclasses import dataclass
from native_cloth import ContactRefinement


@dataclass(frozen=True)
class SeamRuntime:
    thread_radius_m: float = .0002
    hole_half_m: float = .0006
    hole_mesh_spacing_m: float | None = None
    physics_hz: int = 960
    contact_refinement: ContactRefinement = ContactRefinement()
    maximum_stretch: float = 1.02
    quality_mesh: bool = False
    seam_lowering_m: float = 0.
    pre_draped_seam: bool = False
    drape_shape: str = 'gaussian'
    sewing_clamp: bool = False
    passive_clamp: bool = False


CONFIG=SeamRuntime()
