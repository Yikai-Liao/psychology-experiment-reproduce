"""
Compound shape Manim demo

Design rationale:
- Visual assets in this project must be reproducible from structured prompts, so geometry is
  represented via dataclasses (PrimitiveShape, CompoundStimulus, CompoundFrameSpec). Each layer is
  serializable and could be produced by an LLM in the future.
- PrimitiveShape handles single elements expressed in paper-friendly units (visual degrees). Complex
  entities such as notched circles are modeled as dedicated Manim nodes (NotchedCircle) so authors can
  reason in terms of semantic parameters (ratio, rotation) instead of raw boolean ops.
- CompoundStimulus groups primitives around an anchor (pixel or polar) enabling object-level placement
  without repeating conversions.
- CompoundFrameSpec captures all per-frame global state (screen, background, fixation) to make batch
  rendering deterministic, mirroring how screenshots should be generated for multiple experiments.
- The inputs follow the same data flow as the paper: everything begins in visual degrees, converts to
  pixels via Screen geometry, and then becomes Manim coordinates. By preventing manual placement, we
  reduce the chance of drift between the recreated figure and the original experimental design.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Literal, Sequence
import math

from manim import Circle, Line, Rectangle, Square, VGroup, Scene, config
from manim.mobject.geometry.boolean_ops import Difference
import numpy as np

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from example_workspace.util.vision import (
    Screen,
    manim_color_from_rgb255,
    pixel_to_manim,
    polar_deg_to_manim,
    visual_angle_to_pixels,
)


MEDIA_DIR = Path(__file__).parent / "media"


class NotchedCircle(VGroup):
    """
    Circle with a rectangular notch removed.

    Keeping this as a first-class Manim object instead of yet another PrimitiveShape type
    makes it easy to enforce visual-angle constraints while exposing semantic parameters:
    - notch ratios are relative to the parent radius so authors can specify "half width" etc.
    - rotation is applied to the entire notched disk to avoid recomputing offsets.
    """

    def __init__(
        self,
        radius: float,
        color_rgb: Sequence[int],
        notch_width_ratio: float = 0.8,
        notch_height_ratio: float = 0.4,
        notch_offset_ratio: float = 0.9,
        rotation_deg: float = 0.0,
    ):
        circle = Circle(radius=radius)
        notch_width = 2 * radius * notch_width_ratio
        notch_height = 2 * radius * notch_height_ratio
        notch = Rectangle(width=notch_width, height=notch_height)
        notch.shift(np.array([0, notch_offset_ratio * radius, 0]))
        notched = Difference(circle, notch)
        notched.set_fill(manim_color_from_rgb255(color_rgb), opacity=1)
        notched.set_stroke(width=0)
        if rotation_deg:
            notched.rotate(math.radians(rotation_deg))
        super().__init__(notched)


@dataclass
class PrimitiveShape:
    kind: Literal["circle", "square", "rect", "notched_circle"]
    size_deg: float | tuple[float, float]  # diameter or side; rectangles use (width, height)
    color_rgb: Sequence[int]
    offset_deg: tuple[float, float] = (0.0, 0.0)
    z_index: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompoundStimulus:
    primitives: list[PrimitiveShape]
    anchor_px: tuple[float, float] | None = None
    anchor_polar_deg: tuple[float, float] | None = None


@dataclass
class CompoundFrameSpec:
    name: str
    screen: Screen
    background_rgb: Sequence[int] | None
    compounds: list[CompoundStimulus]
    add_fixation: bool = True
    fixation_size_px: float = 12.0
    fixation_color_rgb: Sequence[int] = (0, 0, 0)
    frame_width: float = 14.0


def px_len_to_manim(length_px: float, spec: CompoundFrameSpec) -> float:
    return length_px / (spec.screen.resolution_px[0] / spec.frame_width)


class CompoundScene(Scene):
    def __init__(self, spec: CompoundFrameSpec):
        self.spec = spec
        super().__init__()

    def construct(self):
        for comp in self.spec.compounds:
            self.add(self._build_compound(comp))
        if self.spec.add_fixation:
            self.add(self._build_fixation())

    def _build_compound(self, comp: CompoundStimulus):

        if comp.anchor_px is not None:
            anchor = pixel_to_manim(comp.anchor_px, self.spec.screen)
        elif comp.anchor_polar_deg is not None:
            anchor = polar_deg_to_manim(*comp.anchor_polar_deg, self.spec.screen)
        else:
            anchor = (0, 0, 0)

        group = VGroup()
        for primitive in sorted(comp.primitives, key=lambda p: p.z_index):
            mobj = self._build_primitive(primitive)
            offset_px = (
                visual_angle_to_pixels(primitive.offset_deg[0], self.spec.screen),
                visual_angle_to_pixels(primitive.offset_deg[1], self.spec.screen),
            )
            mobj.move_to(
                (
                    anchor[0] + px_len_to_manim(offset_px[0], self.spec),
                    anchor[1] + px_len_to_manim(offset_px[1], self.spec),
                    0,
                )
            )
            group.add(mobj)
        return group

    def _build_primitive(self, primitive: PrimitiveShape):
        color = manim_color_from_rgb255(primitive.color_rgb)
        if primitive.kind == "circle":
            size_px = visual_angle_to_pixels(float(primitive.size_deg), self.spec.screen)
            size_manim = px_len_to_manim(size_px, self.spec)
            return Circle(radius=size_manim / 2, color=color, fill_opacity=1, stroke_width=0)
        if primitive.kind == "square":
            size_px = visual_angle_to_pixels(float(primitive.size_deg), self.spec.screen)
            size_manim = px_len_to_manim(size_px, self.spec)
            return Square(side_length=size_manim, color=color, fill_opacity=1, stroke_width=0)
        if primitive.kind == "rect":
            width_deg, height_deg = primitive.size_deg  # type: ignore[misc]
            width_px = visual_angle_to_pixels(float(width_deg), self.spec.screen)
            height_px = visual_angle_to_pixels(float(height_deg), self.spec.screen)
            rect = Rectangle(
                width=px_len_to_manim(width_px, self.spec),
                height=px_len_to_manim(height_px, self.spec),
            )
            rect.set_fill(color, opacity=1)
            rect.set_stroke(width=0)
            return rect
        if primitive.kind == "notched_circle":
            radius_px = visual_angle_to_pixels(float(primitive.size_deg) / 2, self.spec.screen)
            radius_manim = px_len_to_manim(radius_px, self.spec)
            return NotchedCircle(
                radius=radius_manim,
                color_rgb=primitive.color_rgb,
                notch_width_ratio=primitive.extra.get("notch_width_ratio", 0.8),
                notch_height_ratio=primitive.extra.get("notch_height_ratio", 0.4),
                notch_offset_ratio=primitive.extra.get("notch_offset_ratio", 0.9),
                rotation_deg=primitive.extra.get("rotation_deg", 0.0),
            )
        raise ValueError(f"Unsupported primitive kind: {primitive.kind}")

    def _build_fixation(self):
        half_len = px_len_to_manim(self.spec.fixation_size_px / 2, self.spec)
        color = manim_color_from_rgb255(self.spec.fixation_color_rgb)
        horiz = Line((-half_len, 0, 0), (half_len, 0, 0), color=color, stroke_width=2)
        vert = Line((0, -half_len, 0), (0, half_len, 0), color=color, stroke_width=2)
        return VGroup(horiz, vert)


def render_batch(specs: Iterable[CompoundFrameSpec], output_dir: Path = MEDIA_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for spec in specs:
        cfg = {
            "pixel_width": spec.screen.resolution_px[0],
            "pixel_height": spec.screen.resolution_px[1],
            "frame_width": spec.frame_width,
            "frame_height": spec.frame_width * spec.screen.resolution_px[1] / spec.screen.resolution_px[0],
            "background_color": manim_color_from_rgb255(spec.background_rgb or spec.screen.background_rgb),
            "media_dir": str(output_dir),
            "images_dir": str(output_dir),
            "video_dir": str(output_dir),
            "format": "png",
            "save_last_frame": True,
            "disable_caching": True,
            "write_to_movie": False,
            "output_file": spec.name,
        }
        with _temporary_config(cfg):
            CompoundScene(spec).render()
            outputs.append(output_dir / f"{spec.name}.png")
    return outputs


@contextmanager
def _temporary_config(updates: dict):
    previous = {key: getattr(config, key) for key in updates}
    try:
        for key, value in updates.items():
            setattr(config, key, value)
        yield
    finally:
        for key, value in previous.items():
            setattr(config, key, value)


PAPER_SCREEN = Screen()

left_anchor = (-visual_angle_to_pixels(5.5, PAPER_SCREEN), 0)
right_anchor = (visual_angle_to_pixels(5.5, PAPER_SCREEN), 0)

NOTCH_UP = {
    "notch_width_ratio": 0.5,
    "notch_height_ratio": 0.6,
    "notch_offset_ratio": 0.75,
    "rotation_deg": 0.0,
}
NOTCH_DOWN = {
    "notch_width_ratio": 0.5,
    "notch_height_ratio": 0.6,
    "notch_offset_ratio": 0.75,
    "rotation_deg": 180.0,
}

# Example configuration replicating the shapes in Fig. 15.
COMPOUND_SPECS: list[CompoundFrameSpec] = [
    CompoundFrameSpec(
        name="exp3_compound_memory",
        screen=PAPER_SCREEN,
        background_rgb=PAPER_SCREEN.background_rgb,
        compounds=[
            CompoundStimulus(
                anchor_px=left_anchor,
                primitives=[
                    PrimitiveShape("notched_circle", 4.2, (255, 215, 0), z_index=0, extra=NOTCH_UP),
                    PrimitiveShape("square", 4.2 * NOTCH_UP["notch_width_ratio"], (220, 0, 0), offset_deg=(0, 2.2), z_index=1),
                ],
            ),
            CompoundStimulus(
                anchor_px=right_anchor,
                primitives=[
                    PrimitiveShape("notched_circle", 4.2, (255, 215, 0), z_index=0, extra=NOTCH_DOWN),
                    PrimitiveShape("square", 4.2 * NOTCH_DOWN["notch_width_ratio"], (220, 0, 0), offset_deg=(0, -2.2), z_index=1),
                ],
            ),
        ],
    ),
    CompoundFrameSpec(
        name="exp3_compound_separate",
        screen=PAPER_SCREEN,
        background_rgb=PAPER_SCREEN.background_rgb,
        compounds=[
            CompoundStimulus(
                anchor_px=left_anchor,
                primitives=[
                    PrimitiveShape("notched_circle", 4.2, (255, 215, 0), extra=NOTCH_UP),
                    PrimitiveShape("square", 4.2 * NOTCH_UP["notch_width_ratio"], (0, 0, 0), offset_deg=(-3.0, 2.8)),
                    PrimitiveShape("square", 4.2 * NOTCH_UP["notch_width_ratio"], (220, 0, 0), offset_deg=(3.0, -2.8)),
                ],
            ),
            CompoundStimulus(
                anchor_px=right_anchor,
                primitives=[
                    PrimitiveShape("notched_circle", 4.2, (255, 215, 0), extra=NOTCH_DOWN),
                    PrimitiveShape("square", 4.2 * NOTCH_DOWN["notch_width_ratio"], (0, 0, 0), offset_deg=(-3.0, -2.8)),
                    PrimitiveShape("square", 4.2 * NOTCH_DOWN["notch_width_ratio"], (220, 0, 0), offset_deg=(3.0, 2.8)),
                ],
            ),
        ],
    ),
]


if __name__ == "__main__":
    render_batch(COMPOUND_SPECS)
