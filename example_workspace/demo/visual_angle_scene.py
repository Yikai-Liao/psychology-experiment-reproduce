"""
Batchable Manim renders driven by dataclass specs (visual angle → pixels → Manim units).

Design philosophy:
- Every scene is parameterized by a Screen dataclass so figures always honor the paper apparatus.
- StimulusFrameSpec encapsulates *all* render inputs (background, fixation, geometry) so a single list
  can act as both configuration and test fixture; there is no implicit global state.
- item-level StimulusItem keeps raw specs close to the paper vocabulary (shape, size in visual degrees,
  and polar/pixel coordinates) which avoids leaking Manim-specific units into data ingestion.
- render_batch applies per-frame Manim config overrides via a temporary context; this keeps the main
  settings file untouched and allows multiple PNGs to be produced in one call, matching the workflow
  where the agent must output a series of images into example_workspace/demo/media.
- The entire pipeline intentionally mirrors the data path in the paper: raw parameters are supplied
  as visual angles, converted to pixels using apparatus metadata, and finally mapped to Manim units.
  This makes the render reproducible and minimizes the human error that would otherwise occur if
  authors guessed Manim coordinates manually.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Sequence
import sys

from manim import Circle, Line, Scene, Square, VGroup, config

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


@dataclass
class StimulusItem:
    shape: Literal["circle", "square"]
    size_deg: float  # diameter for circle; side length for square
    color_rgb: Sequence[int]
    # Provide either polar coordinates (radius_deg, angle_deg) or explicit pixels (x, y)
    polar_deg: Sequence[float] | None = None
    position_px: Sequence[float] | None = None


@dataclass
class StimulusFrameSpec:
    name: str
    screen: Screen
    background_rgb: Sequence[int] | None
    items: list[StimulusItem]
    add_fixation: bool = True
    fixation_size_px: float = 12.0
    fixation_color_rgb: Sequence[int] = (0, 0, 0)
    frame_width: float = 14.0  # logical manim units across width; keeps scaling consistent


def px_len_to_manim(length_px: float, spec: StimulusFrameSpec) -> float:
    return length_px / (spec.screen.resolution_px[0] / spec.frame_width)


class StimulusScene(Scene):
    def __init__(self, spec: StimulusFrameSpec):
        self.spec = spec
        super().__init__()

    def construct(self):
        for item in self.spec.items:
            self.add(self._build_item(item))
        if self.spec.add_fixation:
            self.add(self._build_fixation())

    def _build_item(self, item: StimulusItem):
        size_px = visual_angle_to_pixels(item.size_deg, self.spec.screen)
        size_manim = px_len_to_manim(size_px, self.spec)
        color = manim_color_from_rgb255(item.color_rgb)
        pos = self._item_position(item)

        if item.shape == "circle":
            node = Circle(radius=size_manim / 2, color=color, fill_opacity=1, stroke_width=0)
        else:
            node = Square(side_length=size_manim, color=color, fill_opacity=1, stroke_width=0)
        node.move_to(pos)
        return node

    def _item_position(self, item: StimulusItem):
        if item.position_px is not None:
            return pixel_to_manim(item.position_px, self.spec.screen)
        if item.polar_deg is not None:
            radius_deg, angle_deg = item.polar_deg
            return polar_deg_to_manim(radius_deg, angle_deg, self.spec.screen)
        return (0, 0, 0)

    def _build_fixation(self):
        half_len = px_len_to_manim(self.spec.fixation_size_px / 2, self.spec)
        color = manim_color_from_rgb255(self.spec.fixation_color_rgb)
        horiz = Line((-half_len, 0, 0), (half_len, 0, 0), color=color, stroke_width=2)
        vert = Line((0, -half_len, 0), (0, half_len, 0), color=color, stroke_width=2)
        return VGroup(horiz, vert)


def render_batch(specs: Iterable[StimulusFrameSpec], output_dir: Path = MEDIA_DIR) -> list[Path]:
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
            StimulusScene(spec).render()
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


# Example specs derived from paper text (Experiment 1)
PAPER_SCREEN = Screen()

SAMPLE_SPECS: list[StimulusFrameSpec] = [
    StimulusFrameSpec(
        name="search_display",
        screen=PAPER_SCREEN,
        background_rgb=PAPER_SCREEN.background_rgb,
        items=[
            StimulusItem(shape="circle", size_deg=2.94, color_rgb=(255, 0, 0), polar_deg=(7.59, 0)),
            StimulusItem(shape="circle", size_deg=2.94, color_rgb=(0, 255, 0), polar_deg=(7.59, 45)),
            StimulusItem(shape="circle", size_deg=2.94, color_rgb=(0, 0, 255), polar_deg=(7.59, 90)),
            StimulusItem(shape="circle", size_deg=2.94, color_rgb=(255, 255, 0), polar_deg=(7.59, 135)),
            StimulusItem(shape="circle", size_deg=2.94, color_rgb=(255, 0, 0), polar_deg=(7.59, 180)),
            StimulusItem(shape="circle", size_deg=2.94, color_rgb=(0, 255, 0), polar_deg=(7.59, 225)),
            StimulusItem(shape="circle", size_deg=2.94, color_rgb=(0, 0, 255), polar_deg=(7.59, 270)),
            StimulusItem(shape="circle", size_deg=2.94, color_rgb=(255, 255, 0), polar_deg=(7.59, 315)),
        ],
    ),
    StimulusFrameSpec(
        name="memory_display_integrated_vs_separate",
        screen=PAPER_SCREEN,
        background_rgb=PAPER_SCREEN.background_rgb,
        items=[
            # Integrated colored shape at center (4.2° square)
            StimulusItem(shape="square", size_deg=4.2, color_rgb=(255, 0, 0), position_px=(0, 0)),
            # Separate objects at corners of 8.4° virtual square
            StimulusItem(shape="square", size_deg=4.2, color_rgb=(0, 0, 0), position_px=(-visual_angle_to_pixels(4.2, PAPER_SCREEN), visual_angle_to_pixels(4.2, PAPER_SCREEN))),
            StimulusItem(shape="circle", size_deg=4.2, color_rgb=(255, 0, 0), position_px=(visual_angle_to_pixels(4.2, PAPER_SCREEN), -visual_angle_to_pixels(4.2, PAPER_SCREEN))),
        ],
    ),
]


if __name__ == "__main__":
    render_batch(SAMPLE_SPECS)
