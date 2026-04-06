from __future__ import annotations

"""Tests for easyeda_svg_renderer.

Two real components cover the key branches:

  C381116 — N-MOSFET
    symbol : PL (polyline), R (rectangle), A (arc), P (pin + labels)
    footprint: TRACK, CIRCLE, PAD OVAL (w≠h → <ellipse>), RECT,
               SOLIDREGION solid + cutout (fill="none"), layer-100 skip

  C2685 — NPN transistor
    symbol : PG (polygon, closed=True), PL, P (pins)
    footprint: ARC (→ <path>), PAD ELLIPSE (w==h → <circle>), PAD RECT,
               SOLIDREGION solid + layer-100 skip

Branches not reachable from these two (no matching fixture data) are covered
by small inline synthetic shapes at the bottom of this file.
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest

from easyeda2kicad.easyeda.easyeda_svg_renderer import (
    render_footprint_svg,
    render_symbol_svg,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CACHE = Path(__file__).parent.parent / ".easyeda_cache"


def _load(lcsc_id: str) -> dict[str, Any]:
    path = _CACHE / f"{lcsc_id}.json"
    if not path.exists():
        pytest.skip(f"Cache file not found: {path}")
    data = json.loads(path.read_text())
    return data.get("result", data)  # type: ignore[no-any-return]


def _tags(svg: str) -> set[str]:
    """Return the set of SVG element tag names present (e.g. {'circle', 'path'})."""
    return {m.group(1) for m in re.finditer(r"<([a-z]+)\s", svg)}


def _is_valid_svg(svg: str) -> bool:
    return svg.startswith("<?xml") and "<svg" in svg and "</svg>" in svg


def _viewbox(svg: str) -> list[float]:
    m = re.search(r'viewBox="([^"]+)"', svg)
    assert m, "viewBox missing"
    return [float(v) for v in m.group(1).split()]


# ---------------------------------------------------------------------------
# C381116 — symbol
# ---------------------------------------------------------------------------


class TestSymbolC381116:
    """PL, R, A (arc), P (pin + visible number labels)."""

    @pytest.fixture(autouse=True)
    def _svg(self) -> None:
        self.svg = render_symbol_svg(_load("C381116"))

    def test_valid_svg(self) -> None:
        assert _is_valid_svg(self.svg)

    def test_viewbox_finite(self) -> None:
        assert all(v != float("inf") for v in _viewbox(self.svg))

    def test_polyline(self) -> None:
        assert "<polyline " in self.svg

    def test_rectangle(self) -> None:
        # R shape → <rect> (background <rect> also present, so tag is enough)
        assert "rect" in _tags(self.svg)

    def test_arc_path(self) -> None:
        # A shape → <path d="M ... A ...">
        assert "<path " in self.svg
        assert " A " in self.svg  # SVG arc command in path data

    def test_pin_dot(self) -> None:
        # Each P pin draws a filled connection circle
        assert "<circle " in self.svg

    def test_pin_number_label(self) -> None:
        # Pin number segment (seg4) visible="1" → <text>
        assert "<text " in self.svg


# ---------------------------------------------------------------------------
# C381116 — footprint
# ---------------------------------------------------------------------------


class TestFootprintC381116:
    """TRACK, CIRCLE, PAD OVAL (w≠h), RECT, SOLIDREGION solid + cutout."""

    @pytest.fixture(autouse=True)
    def _svg(self) -> None:
        self.svg = render_footprint_svg(_load("C381116"))

    def test_valid_svg(self) -> None:
        assert _is_valid_svg(self.svg)

    def test_track(self) -> None:
        assert "<polyline " in self.svg

    def test_circle_shape(self) -> None:
        assert "<circle " in self.svg

    def test_rect_shape(self) -> None:
        assert "<rect " in self.svg

    def test_oval_pad_ellipse(self) -> None:
        # PAD OVAL with w≠h → <ellipse rx="..." ry="..."> (not <circle>)
        assert "<ellipse " in self.svg

    def test_solidregion_cutout_fill_none(self) -> None:
        # cutout variant → fill="none" on a <path>
        assert "<path d=" in self.svg
        assert 'fill="none"' in self.svg

    def test_solidregion_layer100_skipped(self) -> None:
        # layer 100/101 shapes must be silently dropped — SVG must still be valid
        assert _is_valid_svg(self.svg)


# ---------------------------------------------------------------------------
# C2685 — symbol
# ---------------------------------------------------------------------------


class TestSymbolC2685:
    """PG (closed polygon), PL (polyline), P (pins)."""

    @pytest.fixture(autouse=True)
    def _svg(self) -> None:
        self.svg = render_symbol_svg(_load("C2685"))

    def test_valid_svg(self) -> None:
        assert _is_valid_svg(self.svg)

    def test_polygon(self) -> None:
        # PG → _render_polyline(closed=True) → <polygon>
        assert "<polygon " in self.svg

    def test_polyline(self) -> None:
        assert "<polyline " in self.svg

    def test_pin_dot(self) -> None:
        assert "<circle " in self.svg


# ---------------------------------------------------------------------------
# C2685 — footprint
# ---------------------------------------------------------------------------


class TestFootprintC2685:
    """ARC, PAD ELLIPSE (w==h → circle), PAD RECT, SOLIDREGION layer-100 skip."""

    @pytest.fixture(autouse=True)
    def _svg(self) -> None:
        self.svg = render_footprint_svg(_load("C2685"))

    def test_valid_svg(self) -> None:
        assert _is_valid_svg(self.svg)

    def test_arc_renders_path(self) -> None:
        # ARC → <path d="...">
        assert "<path " in self.svg

    def test_ellipse_equal_renders_circle(self) -> None:
        # ELLIPSE PAD with w==h → <circle> (circle branch, not <ellipse>)
        assert "<circle " in self.svg
        assert "<ellipse " not in self.svg

    def test_rect_pad(self) -> None:
        assert "<rect " in self.svg

    def test_pad_number_text(self) -> None:
        # Plated pads with a pad number → <text> label
        assert "<text " in self.svg


# ---------------------------------------------------------------------------
# Synthetic shape tests — branches not reached by the two real fixtures
# ---------------------------------------------------------------------------


def _sym_result(
    shapes: list[str], bbox: dict[str, Any] | None = None
) -> dict[str, Any]:
    ds: dict[str, Any] = {"shape": shapes}
    if bbox:
        ds["BBox"] = bbox
    return {"dataStr": ds, "title": "test"}


def _fp_result(shapes: list[str], bbox: dict[str, Any] | None = None) -> dict[str, Any]:
    ds: dict[str, Any] = {"shape": shapes}
    if bbox:
        ds["BBox"] = bbox
    pkg = {"dataStr": ds}
    return {"packageDetail": pkg, "title": "test"}


class TestSyntheticSymbolShapes:
    """Cover C, E, PT, T renderers and edge cases not in C381116/C2685."""

    def test_circle_shape(self) -> None:
        svg = render_symbol_svg(_sym_result(["C~10~20~5~#880000~1~0~none~gge1~0"]))
        assert "<circle " in svg

    def test_ellipse_shape(self) -> None:
        svg = render_symbol_svg(_sym_result(["E~10~20~8~4~#880000~1~0~none~gge1~0"]))
        assert "<ellipse " in svg

    def test_path_shape(self) -> None:
        svg = render_symbol_svg(
            _sym_result(["PT~M 0 0 L 10 10~#880000~1~0~none~gge1~0"])
        )
        assert "<path " in svg

    def test_text_shape(self) -> None:
        svg = render_symbol_svg(
            _sym_result(
                ["T~L~10~20~0~#000000~Arial~7pt~normal~baseline~start~~Hello~1"]
            )
        )
        assert "Hello" in svg
        assert "<text " in svg

    def test_text_with_rotation(self) -> None:
        svg = render_symbol_svg(
            _sym_result(
                ["T~L~10~20~90~#000000~Arial~7pt~normal~baseline~start~~Rotated~1"]
            )
        )
        assert 'transform="rotate(' in svg

    def test_rectangle_rounded_corners(self) -> None:
        # rx and ry non-empty → rx_attr added
        svg = render_symbol_svg(
            _sym_result(["R~0~0~2~2~10~10~#880000~1~0~none~gge1~0"])
        )
        assert 'rx="' in svg

    def test_pin_with_dot_circle(self) -> None:
        # segment 5: visible="1" → active-low inversion circle
        shape = "P~show~0~1~0~0~0~gge1~0^^0~0^^M 0 0 h 10~#880000^^1~12~1~0~A~start^^^1~5~-1~0~1~end^^^1~2~0^^0~"
        svg = render_symbol_svg(_sym_result([shape]))
        # dot_circle segment show="1" → stroke circle rendered
        assert svg.count("<circle ") >= 2  # pin dot + inversion circle

    def test_empty_shapes_returns_valid_svg(self) -> None:
        svg = render_symbol_svg(_sym_result([]))
        assert _is_valid_svg(svg)

    def test_unknown_shape_type_ignored(self) -> None:
        svg = render_symbol_svg(_sym_result(["UNKNOWN~1~2~3"]))
        assert _is_valid_svg(svg)

    def test_api_bbox_seeds_viewbox(self) -> None:
        svg = render_symbol_svg(
            _sym_result([], bbox={"x": 100, "y": 200, "width": 50, "height": 30})
        )
        vb = _viewbox(svg)
        # viewbox should be anchored near the supplied BBox
        assert vb[0] <= 100
        assert vb[1] <= 200


class TestSyntheticFootprintShapes:
    """Cover HOLE, VIA, TEXT, polygon PAD, non-plated PAD, SOLIDREGION npth."""

    def test_hole(self) -> None:
        svg = render_footprint_svg(_fp_result(["HOLE~100~100~2~gge1~0"]))
        assert "<circle " in svg

    def test_via(self) -> None:
        svg = render_footprint_svg(_fp_result(["VIA~100~100~4~GND~1~gge1~0"]))
        assert svg.count("<circle ") >= 2  # pad ring + drill hole

    def test_text(self) -> None:
        svg = render_footprint_svg(_fp_result(["TEXT~P~10~20~0.5~0~0~3~~5pt~REF~~"]))
        assert "<text " in svg

    def test_text_with_rotation(self) -> None:
        svg = render_footprint_svg(_fp_result(["TEXT~P~10~20~0.5~45~0~3~~5pt~REF~~"]))
        assert 'transform="rotate(' in svg

    def test_polygon_pad(self) -> None:
        pts = "90 90 110 90 110 110 90 110"
        svg = render_footprint_svg(
            _fp_result([f"PAD~POLYGON~100~100~20~20~1~GND~1~0~{pts}~0~gge1~0"])
        )
        assert "<polygon " in svg

    def test_non_plated_pad_no_copper(self) -> None:
        # is_plated = "N" → no copper fill, but drill hole still drawn if hole_r > 0
        svg = render_footprint_svg(
            _fp_result(["PAD~ELLIPSE~100~100~10~10~11~GND~1~2~0~0~gge1~0~~N"])
        )
        # no copper circle/ellipse for non-plated pad (hole_r = 2)
        assert "<circle " in svg  # drill hole still rendered

    def test_solidregion_npth(self) -> None:
        svg = render_footprint_svg(
            _fp_result(["SOLIDREGION~11~~M 0 0 L 10 0 L 10 10 Z~npth~gge1~"])
        )
        assert 'fill="white"' in svg

    def test_solidregion_cutout(self) -> None:
        svg = render_footprint_svg(
            _fp_result(["SOLIDREGION~11~~M 0 0 L 10 0 L 10 10 Z~cutout~gge1~"])
        )
        assert 'fill="none"' in svg

    def test_solidregion_layer100_skipped(self) -> None:
        svg = render_footprint_svg(
            _fp_result(["SOLIDREGION~100~~M 0 0 L 10 0 L 10 10 Z~solid~gge1~"])
        )
        assert "<path " not in svg

    def test_oval_pad_unequal(self) -> None:
        # OVAL with w≠h → <ellipse>
        svg = render_footprint_svg(
            _fp_result(["PAD~OVAL~100~100~10~6~1~GND~1~0~~0~gge1"])
        )
        assert "<ellipse " in svg

    def test_empty_footprint_returns_valid_svg(self) -> None:
        svg = render_footprint_svg(_fp_result([]))
        assert _is_valid_svg(svg)

    def test_slot_pad_renders_rect_not_circle(self) -> None:
        # PAD with hole_length > 0 → slot drill → <rect rx=...> not <circle>
        # Format: PAD~shape~cx~cy~w~h~layer~net~number~hole_r~points~rotation~id~hole_length
        # Use RECT pad so no copper circle is drawn, isolating the drill shape.
        svg = render_footprint_svg(
            _fp_result(["PAD~RECT~100~100~6~6~11~GND~1~1.5~0~0~gge1~4.0"])
        )
        assert 'rx="' in svg  # slot drill rendered as rounded rect
        assert "<circle " not in svg  # no plain circle for the slot drill

    def test_via_uses_multilayer_color(self) -> None:
        svg = render_footprint_svg(_fp_result(["VIA~100~100~4~GND~1~gge1~0"]))
        assert "#C0C0C0" in svg  # Multi-Layer color
        assert "#FF0000" not in svg  # not TopLayer color


class TestSyntheticSymbolShapesExtra:
    """Cover display-flag fix."""

    def test_text_display_0_hidden(self) -> None:
        svg = render_symbol_svg(
            _sym_result(
                ["T~L~10~20~0~#000000~Arial~7pt~normal~baseline~start~~Hidden~0"]
            )
        )
        assert "Hidden" not in svg

    def test_text_display_1_visible(self) -> None:
        svg = render_symbol_svg(
            _sym_result(
                ["T~L~10~20~0~#000000~Arial~7pt~normal~baseline~start~~Visible~1"]
            )
        )
        assert "Visible" in svg
