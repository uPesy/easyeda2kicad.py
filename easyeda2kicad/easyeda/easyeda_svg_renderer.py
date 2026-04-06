"""Render raw EasyEDA API shape data as SVG.

Converts the ``dataStr.shape`` strings from the EasyEDA component API
directly into SVG without any KiCad conversion step.  Useful for
debugging: compare what EasyEDA delivers versus what gets imported.

Supported shape types (symbol):
    P   – Pin (line + connection dot + name/number labels)
    PL  – Polyline
    PG  – Polygon
    E   – Ellipse
    C   – Circle
    R   – Rectangle (both plain and rounded-corner variants)
    A   – Arc  (SVG path string passed through as-is)
    PT  – Path (SVG path string passed through as-is)
    T   – Text

Supported shape types (footprint):
    TRACK, PAD, CIRCLE, ARC, RECT, SOLIDREGION, HOLE, VIA
    SVGNODE is silently skipped (3D metadata, no 2D representation)

Public API:
    render_symbol_svg(api_result)     -> str  (SVG markup)
    render_footprint_svg(api_result)  -> str  (SVG markup)
"""

from __future__ import annotations

import html
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_PADDING = 1  # minimal margin so strokes at the bbox edge are not clipped (= max stroke-width / 2)

# EasyEDA layer IDs → display colours
_LAYER_COLORS: dict[str, str] = {
    "1": "#FF0000",  # TopLayer
    "2": "#0000FF",  # BottomLayer
    "3": "#FFCC00",  # TopSilkLayer
    "4": "#66CC33",  # BottomSilkLayer
    "5": "#808080",  # TopPasteMaskLayer
    "6": "#800000",  # BottomPasteMaskLayer
    "7": "#800080",  # TopSolderMaskLayer
    "8": "#AA00FF",  # BottomSolderMaskLayer
    "10": "#FF00FF",  # BoardOutLine
    "11": "#C0C0C0",  # Multi-Layer
    "12": "#FFFFFF",  # Document
    "13": "#33CC99",  # TopAssembly
    "14": "#5555FF",  # BottomAssembly
    "15": "#F022F0",  # Mechanical
    "19": "#66CCFF",  # 3DModel
    "99": "#00CCCC0F",  # ComponentShapeLayer (LIBBODY)
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _color(value: str, default: str = "#000000") -> str:
    if value and value.startswith("#"):
        return value
    return default


def _fill(value: str) -> str:
    if not value or value.lower() == "none":
        return "none"
    if value.startswith("#"):
        return value
    return "none"


def _stroke_w(value: str, default: float = 1.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _parse_points(pts: str) -> list[tuple[float, float]]:
    """Parse EasyEDA space-separated point string 'x1 y1 x2 y2 ...'"""
    nums = pts.split()
    result = []
    for i in range(0, len(nums), 2):
        if i + 1 < len(nums):
            result.append((_f(nums[i]), _f(nums[i + 1])))
    return result


# ---------------------------------------------------------------------------
# Bounding-box helpers
# ---------------------------------------------------------------------------


class _BBox:
    def __init__(self) -> None:
        self.min_x = self.min_y = float("inf")
        self.max_x = self.max_y = float("-inf")

    def add(self, x: float, y: float) -> None:
        if x < self.min_x:
            self.min_x = x
        if x > self.max_x:
            self.max_x = x
        if y < self.min_y:
            self.min_y = y
        if y > self.max_y:
            self.max_y = y

    def add_pts(self, pts: list[tuple[float, float]]) -> None:
        for x, y in pts:
            self.add(x, y)

    def is_valid(self) -> bool:
        return self.min_x != float("inf")

    def width(self, padding: float = _PADDING) -> float:
        return (self.max_x - self.min_x) + 2 * padding

    def height(self, padding: float = _PADDING) -> float:
        return (self.max_y - self.min_y) + 2 * padding

    def viewbox(self, padding: float = _PADDING) -> str:
        vx = self.min_x - padding
        vy = self.min_y - padding
        return f"{vx} {vy} {self.width(padding)} {self.height(padding)}"


def _bbox_from_path(path_d: str, bbox: _BBox) -> None:
    """Approximate bounding box from an SVG path by extracting consecutive numeric pairs.

    Inherently imprecise: arc commands (A) have 7 parameters per segment (rx, ry,
    rotation, large-arc-flag, sweep-flag, x, y), H/V commands have only one
    coordinate, and Bezier control points extend beyond the rendered curve.
    Acceptable only for simple M/L paths; for arc-heavy paths the API BBox is
    authoritative.
    """
    nums = re.findall(r"[-+]?\d*\.?\d+", path_d)
    for i in range(0, len(nums) - 1, 2):
        try:
            bbox.add(float(nums[i]), float(nums[i + 1]))
        except (ValueError, IndexError):
            pass


def _seed_bbox_from_api(data_str: dict[str, Any], bbox: _BBox) -> None:
    """Seed bbox from the API-provided BBox field to anchor the viewBox even
    when individual shape parsers miss some extents (e.g. arc endpoints)."""
    api_bbox = data_str.get("BBox", {})
    if not api_bbox:
        return
    bx = _f(api_bbox.get("x", 0))
    by = _f(api_bbox.get("y", 0))
    bw = _f(api_bbox.get("width", 0))
    bh = _f(api_bbox.get("height", 0))
    if bw > 0 and bh > 0:
        bbox.add(bx, by)
        bbox.add(bx + bw, by + bh)


def _build_svg(elements: list[str], bbox: _BBox, title: str, bg_color: str) -> str:
    if not bbox.is_valid():
        bbox.add(0, 0)
        bbox.add(100, 100)
    viewbox = bbox.viewbox()
    vw = bbox.width()
    vh = bbox.height()
    vx = bbox.min_x - _PADDING
    vy = bbox.min_y - _PADDING
    inner = "\n  ".join(elements)
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{vw}" height="{vh}" viewBox="{viewbox}" '
        f'stroke-linecap="round" stroke-linejoin="round">\n'
        f'  <rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="{bg_color}"/>\n'
        f"  <title>{html.escape(title)}</title>\n"
        f"  {inner}\n"
        f"</svg>"
    )


# ---------------------------------------------------------------------------
# Symbol shape renderers
# ---------------------------------------------------------------------------


def _render_pin(shape: str, bbox: _BBox) -> str:
    """P~visibility~type~spice_pin_number~x~y~rotation~id~is_locked^^dot_x~dot_y^^path~color^^name_data^^number_data^^dot_data^^clock_data"""
    segments = shape.split("^^")
    parts = segments[0].split("~")
    if len(parts) < 6:
        return ""

    elems: list[str] = []

    # Segment 0: visibility~type~spice_pin_number~x~y~rotation~id~is_locked
    px, py = _f(parts[4]), _f(parts[5])
    bbox.add(px, py)

    # Segment 1: dot_x~dot_y (connection-point anchor — bbox only)
    if len(segments) > 1:
        seg1 = segments[1].split("~")
        if len(seg1) >= 2:
            bbox.add(_f(seg1[0]), _f(seg1[1]))

    # Segment 2: path~color (pin line)
    if len(segments) > 2:
        path_segs = segments[2].split("~")
        path_d = path_segs[0] if path_segs else ""
        stroke = _color(path_segs[1] if len(path_segs) > 1 else "", "#880000")
        if path_d:
            _bbox_from_path(path_d, bbox)
            elems.append(
                f'<path d="{path_d}" stroke="{stroke}" stroke-width="1" fill="none"/>'
            )

    # Connection dot at pin endpoint (drawn after path so it sits on top)
    elems.append(f'<circle cx="{px}" cy="{py}" r="1.5" fill="#880000"/>')

    # Segments 3 + 4: name label and number label — show~x~y~rotation~text~anchor~font~font_size~color
    for seg_idx in (3, 4):
        if len(segments) <= seg_idx:
            break
        seg_parts = segments[seg_idx].split("~")
        if len(seg_parts) < 5 or not seg_parts[4] or seg_parts[0] in ("0", ""):
            continue
        tx, ty = _f(seg_parts[1]), _f(seg_parts[2])
        trot = _f(seg_parts[3])
        anchor = (
            seg_parts[5]
            if len(seg_parts) > 5 and seg_parts[5] in ("start", "middle", "end")
            else "start"
        )
        raw_fs = seg_parts[7] if len(seg_parts) > 7 and seg_parts[7] else "7pt"
        try:
            fs = float(raw_fs.replace("pt", ""))
        except ValueError:
            fs = 7.0
        color = _color(seg_parts[8] if len(seg_parts) > 8 else "", "#000000")
        bbox.add(tx, ty)
        transform = f' transform="rotate({trot},{tx},{ty})"' if trot else ""
        elems.append(
            f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" '
            f'font-size="{fs}" fill="{color}"{transform}>{html.escape(seg_parts[4])}</text>'
        )

    # Segment 5: dot_circle — show~cx~cy (active-low inversion indicator)
    if len(segments) > 5:
        dot_parts = segments[5].split("~")
        if dot_parts[0] not in ("0", "") and len(dot_parts) >= 3:
            dcx, dcy = _f(dot_parts[1]), _f(dot_parts[2])
            bbox.add(dcx, dcy)
            elems.append(
                f'<circle cx="{dcx}" cy="{dcy}" r="2" stroke="#880000" stroke-width="1" fill="none"/>'
            )

    # Segment 6: clock_symbol — show~path
    if len(segments) > 6:
        clk_parts = segments[6].split("~")
        if clk_parts[0] not in ("0", "") and len(clk_parts) >= 2 and clk_parts[1]:
            _bbox_from_path(clk_parts[1], bbox)
            elems.append(
                f'<path d="{clk_parts[1]}" stroke="#880000" stroke-width="1" fill="none"/>'
            )

    return "\n".join(elems)


def _render_polyline(shape: str, bbox: _BBox, closed: bool = False) -> str:
    """PL/PG~points~stroke_color~stroke_width~stroke_style~fill_color~id~locked"""
    parts = shape.split("~")
    if len(parts) < 2:
        return ""
    pts = _parse_points(parts[1])
    if not pts:
        return ""
    bbox.add_pts(pts)
    stroke = _color(parts[2] if len(parts) > 2 else "", "#000000")
    width = _stroke_w(parts[3] if len(parts) > 3 else "")
    fill = _fill(parts[5] if len(parts) > 5 else "none")
    pts_attr = " ".join(f"{x},{y}" for x, y in pts)
    tag = "polygon" if closed else "polyline"
    return f'<{tag} points="{pts_attr}" stroke="{stroke}" stroke-width="{width}" fill="{fill}"/>'


def _render_ellipse(shape: str, bbox: _BBox) -> str:
    """E~center_x~center_y~radius_x~radius_y~stroke_color~stroke_width~stroke_style~fill_color~id~locked"""
    parts = shape.split("~")
    if len(parts) < 5:
        return ""
    cx, cy, rx, ry = _f(parts[1]), _f(parts[2]), _f(parts[3]), _f(parts[4])
    bbox.add(cx - rx, cy - ry)
    bbox.add(cx + rx, cy + ry)
    stroke = _color(parts[5] if len(parts) > 5 else "", "#000000")
    width = _stroke_w(parts[6] if len(parts) > 6 else "")
    fill = _fill(parts[8] if len(parts) > 8 else "none")
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" stroke="{stroke}" stroke-width="{width}" fill="{fill}"/>'


def _render_circle(shape: str, bbox: _BBox) -> str:
    """C~center_x~center_y~radius~stroke_color~stroke_width~stroke_style~fill_color~id~locked"""
    parts = shape.split("~")
    if len(parts) < 4:
        return ""
    cx, cy, r = _f(parts[1]), _f(parts[2]), _f(parts[3])
    bbox.add(cx - r, cy - r)
    bbox.add(cx + r, cy + r)
    stroke = _color(parts[4] if len(parts) > 4 else "", "#000000")
    width = _stroke_w(parts[5] if len(parts) > 5 else "")
    fill = _fill(parts[7] if len(parts) > 7 else "none")
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{stroke}" stroke-width="{width}" fill="{fill}"/>'


def _render_rectangle(shape: str, bbox: _BBox) -> str:
    """R~x~y~[rx~ry]~width~height~stroke_color~stroke_width~stroke_style~fill_color~id~locked

    EasyEDA uses two variants: empty strings at positions 3+4 mean no rounded
    corners; numeric values mean rounded corners with those radii.  In both
    cases width/height live at positions 5+6 and color/stroke/fill at 7+.
    """
    parts = shape.split("~")
    if len(parts) < 7:
        return ""
    x, y = _f(parts[1]), _f(parts[2])
    rx_val = _f(parts[3]) if parts[3] != "" else 0.0
    ry_val = _f(parts[4]) if parts[4] != "" else 0.0
    w, h = _f(parts[5]), _f(parts[6])
    bbox.add(x, y)
    bbox.add(x + w, y + h)
    stroke = _color(parts[7] if len(parts) > 7 else "", "#000000")
    width = _stroke_w(parts[8] if len(parts) > 8 else "")
    fill = _fill(parts[10] if len(parts) > 10 else "none")
    rx_attr = f' rx="{rx_val}" ry="{ry_val}"' if rx_val or ry_val else ""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}"{rx_attr} '
        f'stroke="{stroke}" stroke-width="{width}" fill="{fill}"/>'
    )


def _render_arc(shape: str, _bbox: _BBox) -> str:
    """A~path~helper_dots~stroke_color~stroke_width~stroke_style~fill_color~id~locked

    bbox is intentionally unused: SVG arc flags (0/1) are misread as coordinates
    by _bbox_from_path, producing bogus (0,0) points. API BBox is authoritative.
    """
    parts = shape.split("~")
    if len(parts) < 2:
        return ""
    path_d = parts[1]
    stroke = _color(parts[3] if len(parts) > 3 else "", "#000000")
    width = _stroke_w(parts[4] if len(parts) > 4 else "")
    fill = _fill(parts[6] if len(parts) > 6 else "none")
    return (
        f'<path d="{path_d}" stroke="{stroke}" stroke-width="{width}" fill="{fill}"/>'
    )


def _render_path(shape: str, bbox: _BBox) -> str:
    """PT~path~stroke_color~stroke_width~stroke_style~fill_color~id~locked"""
    parts = shape.split("~")
    if len(parts) < 2:
        return ""
    path_d = parts[1]
    stroke = _color(parts[2] if len(parts) > 2 else "", "#000000")
    width = _stroke_w(parts[3] if len(parts) > 3 else "")
    fill = _fill(parts[5] if len(parts) > 5 else "none")
    _bbox_from_path(path_d, bbox)
    return (
        f'<path d="{path_d}" stroke="{stroke}" stroke-width="{width}" fill="{fill}"/>'
    )


def _render_text(shape: str, bbox: _BBox) -> str:
    """T~type~x~y~rotation~color~font~font_size~stroke_width~baseline~text_anchor~role~text~display~..."""
    parts = shape.split("~")
    if len(parts) < 13 or not parts[12]:
        return ""
    if len(parts) > 13 and parts[13] == "0":
        return ""
    x, y = _f(parts[2]), _f(parts[3])
    rotation = _f(parts[4])
    color = _color(parts[5] if len(parts) > 5 else "", "#000000")
    font_size = parts[7] if len(parts) > 7 else "7pt"
    try:
        fs = float(font_size.replace("pt", ""))
    except ValueError:
        fs = 7.0
    anchor = (
        parts[10]
        if len(parts) > 10 and parts[10] in ("start", "middle", "end")
        else "start"
    )
    bbox.add(x, y)
    transform = f' transform="rotate({rotation},{x},{y})"' if rotation else ""
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{fs}" fill="{color}"{transform}>'
        f"{html.escape(parts[12])}</text>"
    )


_SYMBOL_RENDERERS: dict[str, Any] = {
    "P": _render_pin,
    "PL": _render_polyline,
    "PG": lambda s, b: _render_polyline(s, b, closed=True),
    "E": _render_ellipse,
    "C": _render_circle,
    "R": _render_rectangle,
    "A": _render_arc,
    "PT": _render_path,
    "T": _render_text,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_symbol_svg(api_result: dict[str, Any], bg_color: str = "white") -> str:
    """Render a symbol from EasyEDA API result data as SVG.

    Args:
        api_result: The ``result`` dict from ``get_cad_data_of_component()``.

    Returns:
        SVG markup as a string.
    """
    data_str = api_result.get("dataStr", {})
    shapes = data_str.get("shape", [])
    title = api_result.get("title", "")

    bbox = _BBox()
    _seed_bbox_from_api(data_str, bbox)

    elements: list[str] = []
    for shape in shapes:
        if not isinstance(shape, str):
            continue
        designator = shape.split("~")[0]
        renderer = _SYMBOL_RENDERERS.get(designator)
        if renderer:
            svg_elem = renderer(shape, bbox)
            if svg_elem:
                elements.append(svg_elem)
        else:
            logger.debug("render_symbol_svg: unhandled shape type %r", designator)

    return _build_svg(elements, bbox, title, bg_color=bg_color)


def render_footprint_svg(api_result: dict[str, Any], bg_color: str = "black") -> str:
    """Render a footprint from EasyEDA API result data as SVG.

    Footprint shapes live under ``packageDetail.dataStr.shape``.

    Args:
        api_result: The ``result`` dict from ``get_cad_data_of_component()``.

    Returns:
        SVG markup as a string.
    """
    pkg = api_result.get("packageDetail", {})
    data_str = pkg.get("dataStr", {})
    shapes = data_str.get("shape", [])
    title = api_result.get("title", "")

    bbox = _BBox()
    _seed_bbox_from_api(data_str, bbox)

    elements: list[str] = []

    for shape in shapes:
        if not isinstance(shape, str):
            continue
        parts = shape.split("~")
        designator = parts[0]

        if designator == "TRACK":
            # TRACK~stroke_width~layer_id~net~points~id~is_locked
            if len(parts) < 5:
                continue
            pts = _parse_points(parts[4])
            if not pts:
                continue
            bbox.add_pts(pts)
            layer_color = _LAYER_COLORS.get(parts[2], "#888888")
            pts_attr = " ".join(f"{x},{y}" for x, y in pts)
            elements.append(
                f'<polyline points="{pts_attr}" stroke="{layer_color}" '
                f'stroke-width="{_stroke_w(parts[1])}" fill="none"/>'
            )

        elif designator == "PAD":
            # PAD~shape~center_x~center_y~width~height~layer_id~net~number~hole_radius~points~rotation~
            #     id~hole_length~slot_outline~is_plated~is_locked~clearance1~clearance2~hole_point
            # [15] is_plated: "Y"=plated (has copper), "N"=non-plated (drill only, no copper fill).
            if len(parts) < 7:
                continue
            pad_shape = parts[1].lower()
            px, py = _f(parts[2]), _f(parts[3])
            pw, ph = _f(parts[4]), _f(parts[5])
            layer_color = _LAYER_COLORS.get(parts[6], "#FF0000")
            pad_number = parts[8] if len(parts) > 8 else ""
            rotation = _f(parts[11]) if len(parts) > 11 else 0.0
            hole_r = _f(parts[9]) if len(parts) > 9 else 0.0
            hole_length = _f(parts[13]) if len(parts) > 13 else 0.0
            is_plated = (parts[15] if len(parts) > 15 else "Y") != "N"
            bbox.add(px - pw / 2, py - ph / 2)
            bbox.add(px + pw / 2, py + ph / 2)
            transform = f' transform="rotate({rotation},{px},{py})"' if rotation else ""
            if is_plated:
                if pad_shape == "polygon":
                    pts = (
                        _parse_points(parts[10])
                        if len(parts) > 10 and parts[10]
                        else []
                    )
                    if pts:
                        bbox.add_pts(pts)
                        pts_attr = " ".join(f"{x},{y}" for x, y in pts)
                        elements.append(
                            f'<polygon points="{pts_attr}" '
                            f'stroke="{layer_color}" stroke-width="0.5" fill="{layer_color}"{transform}/>'
                        )
                elif pad_shape in ("ellipse", "oval"):
                    if pw == ph:
                        elements.append(
                            f'<circle cx="{px}" cy="{py}" r="{pw / 2}" '
                            f'stroke="{layer_color}" stroke-width="0.5" fill="{layer_color}"{transform}/>'
                        )
                    else:
                        elements.append(
                            f'<ellipse cx="{px}" cy="{py}" rx="{pw / 2}" ry="{ph / 2}" '
                            f'stroke="{layer_color}" stroke-width="0.5" fill="{layer_color}"{transform}/>'
                        )
                else:
                    elements.append(
                        f'<rect x="{px - pw / 2}" y="{py - ph / 2}" width="{pw}" height="{ph}" '
                        f'stroke="{layer_color}" stroke-width="0.5" fill="{layer_color}"{transform}/>'
                    )
            # Through-hole drill (plated: white hole punched through copper;
            # non-plated: same appearance since no copper was drawn).
            # hole_length > 0 → slot (capsule): render as rounded rect with the pad's rotation.
            if hole_r > 0:
                if hole_length > 0:
                    elements.append(
                        f'<rect x="{px - hole_r}" y="{py - hole_length / 2}" '
                        f'width="{hole_r * 2}" height="{hole_length}" '
                        f'rx="{hole_r}" ry="{hole_r}" '
                        f'stroke="#222222" stroke-width="0.3" fill="white"{transform}/>'
                    )
                else:
                    elements.append(
                        f'<circle cx="{px}" cy="{py}" r="{hole_r}" '
                        f'stroke="#222222" stroke-width="0.3" fill="white"/>'
                    )
            if pad_number and is_plated:
                elements.append(
                    f'<text x="{px}" y="{py}" text-anchor="middle" dominant-baseline="central" '
                    f'font-size="2" fill="white">{html.escape(pad_number)}</text>'
                )

        elif designator == "CIRCLE":
            # CIRCLE~cx~cy~radius~stroke_width~layer_id~id~is_locked
            if len(parts) < 4:
                continue
            cx, cy, r = _f(parts[1]), _f(parts[2]), _f(parts[3])
            layer_color = _LAYER_COLORS.get(
                parts[5] if len(parts) > 5 else "", "#888888"
            )
            bbox.add(cx - r, cy - r)
            bbox.add(cx + r, cy + r)
            elements.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{layer_color}" '
                f'stroke-width="{_stroke_w(parts[4] if len(parts) > 4 else "")}" fill="none"/>'
            )

        elif designator == "ARC":
            # ARC~stroke_width~layer_id~net~path~helper_dots~id~is_locked
            if len(parts) < 5:
                continue
            path_d = parts[4]
            layer_color = _LAYER_COLORS.get(parts[2], "#888888")
            # bbox intentionally not updated: arc flags (0/1) corrupt _bbox_from_path. API BBox is authoritative.
            elements.append(
                f'<path d="{path_d}" stroke="{layer_color}" stroke-width="{_stroke_w(parts[1])}" fill="none"/>'
            )

        elif designator == "RECT":
            # RECT~x~y~width~height~layer_id~id~is_locked~stroke_width~fill_color~[...]
            # Verified against real API data: layer at [5], stroke_width at [8], fill at [9].
            if len(parts) < 6:
                continue
            x, y, w, h = _f(parts[1]), _f(parts[2]), _f(parts[3]), _f(parts[4])
            layer_color = _LAYER_COLORS.get(parts[5], "#888888")
            stroke_w = _stroke_w(parts[8] if len(parts) > 8 else "")
            fill_color = _fill(parts[9] if len(parts) > 9 else "none")
            bbox.add(x, y)
            bbox.add(x + w, y + h)
            elements.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                f'stroke="{layer_color}" stroke-width="{stroke_w}" fill="{fill_color}"/>'
            )

        elif designator in ("TEXT", "SILK_LABEL"):
            # TEXT~type~center_x~center_y~stroke_width~rotation~mirror~layer_id~net~font_size~text~...
            if len(parts) < 11 or not parts[10]:
                continue
            x, y = _f(parts[2]), _f(parts[3])
            rotation = _f(parts[5])
            layer_color = _LAYER_COLORS.get(
                parts[7] if len(parts) > 7 else "", "#888888"
            )
            try:
                fs = float(parts[9].replace("pt", "")) if parts[9] else 5.0
            except ValueError:
                fs = 5.0
            bbox.add(x, y)
            transform = f' transform="rotate({rotation},{x},{y})"' if rotation else ""
            elements.append(
                f'<text x="{x}" y="{y}" font-size="{fs}" fill="{layer_color}"{transform}>'
                f"{html.escape(parts[10])}</text>"
            )

        elif designator == "SOLIDREGION":
            # SOLIDREGION~layer_id~net~path~region_type~id~~[is_locked]
            # region_type: "solid" (filled copper), "cutout" (void in copper),
            #              "npth" (non-plated hole outline)
            # Layers 100/101 (LeadShapeLayer/ComponentPolarityLayer) are skipped per spec.
            if len(parts) < 4 or parts[1] in ("100", "101"):
                continue
            path_d = parts[3]
            region_type = parts[4] if len(parts) > 4 else "solid"
            layer_color = _LAYER_COLORS.get(parts[1], "#888888")
            # bbox intentionally not updated: arc flags (0/1) corrupt _bbox_from_path. API BBox is authoritative.
            if region_type == "cutout":
                fill_attr = 'fill="none"'
                stroke_color = layer_color
            elif region_type == "npth":
                fill_attr = 'fill="white"'
                stroke_color = "#222222"
            else:
                fill_attr = f'fill="{layer_color}"'
                stroke_color = layer_color
            elements.append(
                f'<path d="{path_d}" stroke="{stroke_color}" stroke-width="0.5" {fill_attr}/>'
            )

        elif designator == "HOLE":
            # HOLE~center_x~center_y~radius~id~is_locked
            if len(parts) < 4:
                continue
            hx, hy, r = _f(parts[1]), _f(parts[2]), _f(parts[3])
            bbox.add(hx - r, hy - r)
            bbox.add(hx + r, hy + r)
            elements.append(
                f'<circle cx="{hx}" cy="{hy}" r="{r}" stroke="#222222" '
                f'stroke-width="0.5" fill="white"/>'
            )

        elif designator == "VIA":
            # VIA~center_x~center_y~pad_diameter~net~drill_radius~id~is_locked
            # [3] = pad diameter, [5] = drill radius (JS multiplies by 2 for drill diameter).
            # VIAs span all copper layers → Multi-Layer color (11), not TopLayer (1).
            if len(parts) < 6:
                continue
            vx, vy = _f(parts[1]), _f(parts[2])
            pad_r = _f(parts[3]) / 2  # pad diameter → radius
            drill_r = _f(parts[5])  # drill radius
            layer_color = _LAYER_COLORS.get(
                "11", "#C0C0C0"
            )  # Multi-Layer: vias span all copper layers
            bbox.add(vx - pad_r, vy - pad_r)
            bbox.add(vx + pad_r, vy + pad_r)
            elements.append(
                f'<circle cx="{vx}" cy="{vy}" r="{pad_r}" '
                f'stroke="{layer_color}" stroke-width="0.5" fill="{layer_color}"/>'
            )
            # Drill hole
            elements.append(
                f'<circle cx="{vx}" cy="{vy}" r="{drill_r}" '
                f'stroke="white" stroke-width="0.3" fill="white"/>'
            )

        elif designator != "SVGNODE":
            logger.debug("render_footprint_svg: unhandled shape type %r", designator)

    return _build_svg(elements, bbox, title, bg_color=bg_color)
