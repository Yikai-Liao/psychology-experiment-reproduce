"""
Geometry helpers for mapping between visual angles, pixels, and Manim coordinates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, Tuple

from manim import BLUE, GREEN, RED, WHITE, YELLOW, BLACK, config
from manim.utils.color import rgb_to_color


@dataclass
class Screen:
    """
    Physical screen parameters used for stimulus conversion.

    Defaults mirror the paper: 17-inch CRT, 1024x768, 50 cm viewing distance, white background.
    Coordinates are centered: (0, 0) is the screen center.
    """

    size_inch: float = 17.0
    resolution_px: Tuple[int, int] = (1024, 768)
    viewing_distance_cm: float = 50.0
    background_rgb: Tuple[int, int, int] = (255, 255, 255)

    @property
    def ppi(self) -> float:
        px_w, px_h = self.resolution_px
        diag_px = math.hypot(px_w, px_h)
        return diag_px / self.size_inch


def visual_angle_to_cm(angle_deg: float, distance_cm: float) -> float:
    """Convert a visual angle (deg) to physical size on screen (cm)."""
    return 2 * distance_cm * math.tan(math.radians(angle_deg) / 2)


def cm_to_pixels(size_cm: float, spec: Screen) -> float:
    """Convert a physical size (cm) to pixels for the given display."""
    return size_cm * spec.ppi / 2.54


def visual_angle_to_pixels(angle_deg: float, spec: Screen) -> float:
    """Directly convert visual angle to pixels using display geometry."""
    return cm_to_pixels(visual_angle_to_cm(angle_deg, spec.viewing_distance_cm), spec)


def pixel_to_manim(point_px: Sequence[float], spec: Screen) -> Tuple[float, float, float]:
    """
    Map pixel coordinates (centered) to Manim coordinates.

    Manim's frame_width/height define how many logical units span the screen.
    """
    px_w, px_h = spec.resolution_px
    x_scale = px_w / config.frame_width
    y_scale = px_h / config.frame_height
    x = point_px[0] / x_scale
    y = point_px[1] / y_scale
    return (x, y, 0)


def polar_deg_to_manim(radius_deg: float, angle_deg: float, spec: Screen) -> Tuple[float, float, float]:
    """
    Convert a polar position (radius in visual degrees, angle in degrees) to Manim coords.
    Angle 0 points to the right, increasing counterclockwise.
    """
    radius_px = visual_angle_to_pixels(radius_deg, spec)
    rad = math.radians(angle_deg)
    x_px = radius_px * math.cos(rad)
    y_px = radius_px * math.sin(rad)
    return pixel_to_manim((x_px, y_px), spec)


def manim_color_from_rgb255(rgb: Sequence[int]):
    """Convert 0-255 RGB tuple to a Manim color."""
    r, g, b = rgb
    return rgb_to_color((r / 255, g / 255, b / 255))


# Convenience color map for common palette seen in example paper.
NAMED_COLORS = {
    "red": RED,
    "green": GREEN,
    "blue": BLUE,
    "yellow": YELLOW,
    "white": WHITE,
    'black': BLACK
}


__all__ = [
    "Screen",
    "DisplaySpec",
    "visual_angle_to_cm",
    "cm_to_pixels",
    "visual_angle_to_pixels",
    "pixel_to_manim",
    "polar_deg_to_manim",
    "manim_color_from_rgb255",
    "NAMED_COLORS",
]

# Backward compatibility export
DisplaySpec = Screen
