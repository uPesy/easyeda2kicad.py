from __future__ import annotations

# Global imports
import logging
import math
import re
from pathlib import Path
from typing import Sequence

# Local imports
from .._version import GENERATOR_URL
from ..easyeda.parameters_easyeda import (
    EasyedaPinType,
    EeSymbol,
    EeSymbolArc,
    EeSymbolBbox,
    EeSymbolCircle,
    EeSymbolEllipse,
    EeSymbolPath,
    EeSymbolPin,
    EeSymbolPolygon,
    EeSymbolPolyline,
    EeSymbolRectangle,
    EeSymbolText,
)
from ..easyeda.svg_path_parser import SvgPathEllipticalArc, SvgPathMoveTo
from .parameters_kicad_symbol import (
    KICAD_SYM_VERSIONS_SORTED,
    KiPinStyle,
    KiPinType,
    KiSymbol,
    KiSymbolArc,
    KiSymbolCircle,
    KiSymbolInfo,
    KiSymbolPin,
    KiSymbolPolygon,
    KiSymbolRectangle,
    KiSymbolText,
)

_SYM_LIB_REGEX = r'\n(\s*)\(symbol "{component_name}".*?\n\1\)(?=\n|$)'


def read_symbol_lib_version(lib_path: str | None) -> int:
    """Return the .kicad_sym format version to use for the given library file.

    - If lib_path is None or the file cannot be read: oldest known version.
    - If the file has no (version ...) field: oldest known version.
    - Otherwise: the largest known version that is <= the version in the file.
    """
    if lib_path is not None:
        try:
            with open(lib_path, encoding="utf-8") as f:
                content = f.read(512)  # version is always near the top
            match = re.search(r"\(version\s+(\d+)\)", content)
            if match:
                file_version = int(match.group(1))
                result = KICAD_SYM_VERSIONS_SORTED[0]
                for v in KICAD_SYM_VERSIONS_SORTED:
                    if v <= file_version:
                        result = v
                return result
        except OSError:
            pass
    return KICAD_SYM_VERSIONS_SORTED[0]


def id_already_in_symbol_lib(lib_path: str, component_name: str) -> bool:
    if not Path(lib_path).is_file():
        return False
    with open(lib_path, encoding="utf-8") as lib_file:
        current_lib = lib_file.read()
        component = re.findall(
            _SYM_LIB_REGEX.format(component_name=re.escape(component_name)),
            current_lib,
            flags=re.DOTALL,
        )
        if component != []:
            logging.warning(f"This id is already in {lib_path}")
            return True
    return False


def write_component_in_symbol_lib_file(
    lib_path: str,
    component_name: str,
    component_content: str,
    version: int = KICAD_SYM_VERSIONS_SORTED[0],
    generator: str = GENERATOR_URL,
) -> None:
    """Write a symbol into the library, replacing it if it already exists."""
    if not Path(lib_path).is_file():
        Path(lib_path).write_text(
            f"(kicad_symbol_lib\n  (version {version})\n  (generator {generator})\n)",
            encoding="utf-8",
        )
        logging.debug(f"Created symbol lib: {lib_path}")

    current = Path(lib_path).read_text(encoding="utf-8")

    pattern = _SYM_LIB_REGEX.format(component_name=re.escape(component_name))
    if re.search(pattern, current, flags=re.DOTALL):
        # Symbol exists — replace it
        new_lib = re.sub(
            pattern, component_content.rstrip("\n"), current, flags=re.DOTALL
        )
    else:
        # Symbol is new — insert before closing parenthesis
        last_paren_pos = current.rfind(")")
        if last_paren_pos == -1:
            raise ValueError("Invalid KiCad library file: no closing parenthesis found")
        sep = "" if component_content.endswith("\n") else "\n"
        new_lib = (
            current[:last_paren_pos]
            + component_content
            + sep
            + current[last_paren_pos:]
        )

    new_lib = new_lib.replace(
        "(generator kicad_symbol_editor)", f"(generator {GENERATOR_URL})"
    )
    Path(lib_path).write_text(new_lib, encoding="utf-8")


# EasyEDA uses a 5px grid (= 1.27mm = 50mil). Snapping bbox coordinates to this
# boundary ensures pin coordinates land on the KiCad grid after subtraction.
_EASYEDA_SYMBOL_GRID_PX = 5

ee_pin_type_to_ki_pin_type = {
    EasyedaPinType.unspecified: KiPinType.unspecified,
    EasyedaPinType._input: KiPinType._input,
    EasyedaPinType.output: KiPinType.output,
    EasyedaPinType.bidirectional: KiPinType.bidirectional,
    EasyedaPinType.power: KiPinType.power_in,
}


def px_to_mm(dim: int | float | str) -> float:
    return 10.0 * float(dim) * 0.0254


def px_to_mm_grid(dim: int | float | str, grid: float = 1.27) -> float:
    """Convert EasyEDA pixels to KiCad mm and snap to grid (default 50mil = 1.27mm)."""
    mm_value = 10.0 * float(dim) * 0.0254
    return round(mm_value / grid) * grid


def snap_bbox(
    ee_bbox: EeSymbolBbox, grid_px: int = _EASYEDA_SYMBOL_GRID_PX
) -> tuple[float, float]:
    """Round bbox origin to the nearest grid_px boundary (5px = 1.27mm = 50mil).

    EasyEDA bbox coordinates often contain sub-pixel values. Snapping to the
    nearest 5px boundary ensures that pin coordinates (which are typically
    integer multiples of 5px in absolute space) land on the KiCad 1.27mm grid
    after subtraction, without per-coordinate rounding.
    """
    snapped_x = round(float(ee_bbox.x) / grid_px) * grid_px
    snapped_y = round(float(ee_bbox.y) / grid_px) * grid_px
    return snapped_x, snapped_y


def convert_ee_pins(
    ee_pins: list[EeSymbolPin], ee_bbox: EeSymbolBbox
) -> list[KiSymbolPin]:
    kicad_pins = []
    for ee_pin in ee_pins:
        pin_length = abs(int(float(ee_pin.pin_path.path.split("h")[-1].split()[0])))

        ki_pin = KiSymbolPin(
            name=ee_pin.name.text.replace(" ", ""),
            number=ee_pin.settings.spice_pin_number.replace(" ", ""),
            style=KiPinStyle.line,
            length=px_to_mm_grid(pin_length),
            type=ee_pin_type_to_ki_pin_type[ee_pin.settings.type],
            orientation=ee_pin.settings.rotation,
            pos_x=px_to_mm_grid(ee_pin.settings.pos_x - ee_bbox.x),
            pos_y=-px_to_mm_grid(ee_pin.settings.pos_y - ee_bbox.y),
        )

        if ee_pin.dot.is_displayed and ee_pin.clock.is_displayed:
            ki_pin.style = KiPinStyle.inverted_clock
        elif ee_pin.dot.is_displayed:
            ki_pin.style = KiPinStyle.inverted
        elif ee_pin.clock.is_displayed:
            ki_pin.style = KiPinStyle.clock

        kicad_pins.append(ki_pin)

    return kicad_pins


def convert_ee_rectangles(
    ee_rectangles: list[EeSymbolRectangle],
    ee_bbox: EeSymbolBbox,
) -> list[KiSymbolRectangle]:
    kicad_rectangles = []
    for ee_rectangle in ee_rectangles:
        ki_rectangle = KiSymbolRectangle(
            pos_x0=px_to_mm(ee_rectangle.pos_x - ee_bbox.x),
            pos_y0=-px_to_mm(ee_rectangle.pos_y - ee_bbox.y),
        )
        ki_rectangle.pos_x1 = px_to_mm(ee_rectangle.width) + ki_rectangle.pos_x0
        ki_rectangle.pos_y1 = -px_to_mm(ee_rectangle.height) + ki_rectangle.pos_y0

        kicad_rectangles.append(ki_rectangle)

    return kicad_rectangles


def convert_ee_circles(
    ee_circles: list[EeSymbolCircle],
    ee_bbox: EeSymbolBbox,
) -> list[KiSymbolCircle]:
    return [
        KiSymbolCircle(
            pos_x=px_to_mm(ee_circle.center_x - ee_bbox.x),
            pos_y=-px_to_mm(ee_circle.center_y - ee_bbox.y),
            radius=px_to_mm(ee_circle.radius),
            background_filling=ee_circle.fill_color,
        )
        for ee_circle in ee_circles
    ]


def convert_ee_ellipses(
    ee_ellipses: list[EeSymbolEllipse],
    ee_bbox: EeSymbolBbox,
) -> list[KiSymbolCircle]:
    # Ellipses are not supported in KiCad — convert only if radius_x == radius_y (circle)
    return [
        KiSymbolCircle(
            pos_x=px_to_mm(ee_ellipse.center_x - ee_bbox.x),
            pos_y=-px_to_mm(ee_ellipse.center_y - ee_bbox.y),
            radius=px_to_mm(ee_ellipse.radius_x),
        )
        for ee_ellipse in ee_ellipses
        if ee_ellipse.radius_x == ee_ellipse.radius_y
    ]


def _svg_arc_mid_point(
    sx: float,
    sy: float,
    ex: float,
    ey: float,
    rx: float,
    ry: float,
    x_rotation_deg: float,
    large_arc: bool,
    sweep: bool,
) -> tuple[float, float]:
    """Return the parametric mid-point on an SVG arc.

    Implements the SVG spec endpoint-to-center conversion
    (https://www.w3.org/TR/SVG11/implnote.html#ArcConversionEndpointToCenter)
    and evaluates the ellipse at θ_mid = θ_start + Δθ/2.
    All coordinates are in the caller's coordinate system (SVG or KiCad).
    """
    phi = math.radians(x_rotation_deg % 360.0)
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)

    # Step 1: rotate midpoint of chord into ellipse-local frame
    dx2 = (sx - ex) / 2.0
    dy2 = (sy - ey) / 2.0
    x1 = cos_phi * dx2 + sin_phi * dy2
    y1 = -sin_phi * dx2 + cos_phi * dy2

    # Ensure radii are positive and large enough
    rx = abs(rx)
    ry = abs(ry)
    rx_sq = rx * rx
    ry_sq = ry * ry
    x1_sq = x1 * x1
    y1_sq = y1 * y1
    radii_scale = x1_sq / rx_sq + y1_sq / ry_sq if rx_sq and ry_sq else 0.0
    if radii_scale > 1.0:
        scale = math.sqrt(radii_scale)
        rx *= scale
        ry *= scale
        rx_sq = rx * rx
        ry_sq = ry * ry

    # Step 2: compute center in ellipse-local frame
    sign = -1.0 if large_arc == sweep else 1.0
    num = max(0.0, rx_sq * ry_sq - rx_sq * y1_sq - ry_sq * x1_sq)
    den = rx_sq * y1_sq + ry_sq * x1_sq
    coef = sign * math.sqrt(num / den) if den > 0 else 0.0
    cx1 = coef * (rx * y1 / ry)
    cy1 = coef * -(ry * x1 / rx) if rx else 0.0

    # Step 3: center in SVG frame
    cx = cos_phi * cx1 - sin_phi * cy1 + (sx + ex) / 2.0
    cy = sin_phi * cx1 + cos_phi * cy1 + (sy + ey) / 2.0

    # Step 4: start angle and angular extent
    def angle_between(ux: float, uy: float, vx: float, vy: float) -> float:
        n = math.hypot(ux, uy) * math.hypot(vx, vy)
        if n == 0:
            return 0.0
        cos_val = max(-1.0, min(1.0, (ux * vx + uy * vy) / n))
        a = math.acos(cos_val)
        if ux * vy - uy * vx < 0:
            a = -a
        return a

    ux = (x1 - cx1) / rx if rx else 0.0
    uy = (y1 - cy1) / ry if ry else 0.0
    vx = (-x1 - cx1) / rx if rx else 0.0
    vy = (-y1 - cy1) / ry if ry else 0.0

    theta1 = angle_between(1.0, 0.0, ux, uy)
    d_theta = angle_between(ux, uy, vx, vy)

    if not sweep and d_theta > 0:
        d_theta -= 2 * math.pi
    elif sweep and d_theta < 0:
        d_theta += 2 * math.pi

    theta_mid = theta1 + d_theta / 2.0

    # Evaluate ellipse at theta_mid (with rotation phi)
    lx = rx * math.cos(theta_mid)
    ly = ry * math.sin(theta_mid)
    mid_x = cos_phi * lx - sin_phi * ly + cx
    mid_y = sin_phi * lx + cos_phi * ly + cy
    return mid_x, mid_y


def convert_ee_arcs(
    ee_arcs: list[EeSymbolArc],
    ee_bbox: EeSymbolBbox,
) -> list[KiSymbolArc]:
    kicad_arcs = []
    for ee_arc in ee_arcs:
        if (
            len(ee_arc.path) < 2
            or not isinstance(ee_arc.path[0], SvgPathMoveTo)
            or not isinstance(ee_arc.path[1], SvgPathEllipticalArc)
        ):
            logging.error("Can't convert this arc: unexpected SVG path structure")
            continue
        elif float(ee_arc.path[1].radius_y) == 0 or float(ee_arc.path[1].radius_x) == 0:
            logging.warning(
                f"Skipping degenerate arc (radius_x={ee_arc.path[1].radius_x},"
                f" radius_y={ee_arc.path[1].radius_y})"
            )
            continue
        else:
            svg_arc = ee_arc.path[1]
            radius = px_to_mm(max(float(svg_arc.radius_x), float(svg_arc.radius_y)))

            svg_sx = float(ee_arc.path[0].start_x)
            svg_sy = float(ee_arc.path[0].start_y)
            svg_ex = float(svg_arc.end_x)
            svg_ey = float(svg_arc.end_y)

            svg_mid_x, svg_mid_y = _svg_arc_mid_point(
                sx=svg_sx,
                sy=svg_sy,
                ex=svg_ex,
                ey=svg_ey,
                rx=float(svg_arc.radius_x),
                ry=float(svg_arc.radius_y),
                x_rotation_deg=float(svg_arc.x_axis_rotation),
                large_arc=svg_arc.flag_large_arc,
                sweep=svg_arc.flag_sweep,
            )

            # Transform to KiCad coordinates (shift by bbox origin, flip Y-axis).
            # Start and end are swapped: the Y-flip mirrors the arc, reversing the
            # traversal direction, which would move the mid-point to the wrong side
            # of the chord. Swapping start/end preserves the correct winding.
            start_x = px_to_mm(svg_ex - ee_bbox.x)
            start_y = -px_to_mm(svg_ey - ee_bbox.y)
            middle_x = px_to_mm(svg_mid_x - ee_bbox.x)
            middle_y = -px_to_mm(svg_mid_y - ee_bbox.y)
            end_x = px_to_mm(svg_sx - ee_bbox.x)
            end_y = -px_to_mm(svg_sy - ee_bbox.y)

            ki_arc = KiSymbolArc(
                radius=radius,
                start_x=start_x,
                start_y=start_y,
                middle_x=middle_x,
                middle_y=middle_y,
                end_x=end_x,
                end_y=end_y,
                # angle_start != angle_end (default 0.0) disables background fill.
                angle_start=1.0,
                angle_end=0.0,
            )
            kicad_arcs.append(ki_arc)

    return kicad_arcs


def convert_ee_polylines(
    ee_polylines: Sequence[EeSymbolPolyline | EeSymbolPolygon],
    ee_bbox: EeSymbolBbox,
) -> list[KiSymbolPolygon]:
    kicad_polygons = []
    for ee_polyline in ee_polylines:
        raw_pts = ee_polyline.points.split()
        x_points = [
            px_to_mm(float(raw_pts[i]) - ee_bbox.x) for i in range(0, len(raw_pts), 2)
        ]
        y_points = [
            -px_to_mm(float(raw_pts[i]) - ee_bbox.y) for i in range(1, len(raw_pts), 2)
        ]

        if isinstance(ee_polyline, EeSymbolPolygon) or ee_polyline.fill_color:
            x_points.append(x_points[0])
            y_points.append(y_points[0])
        if len(x_points) > 0 and len(y_points) > 0:
            kicad_polygon = KiSymbolPolygon(
                points=[
                    [x_points[i], y_points[i]]
                    for i in range(min(len(x_points), len(y_points)))
                ],
                points_number=min(len(x_points), len(y_points)),
                is_closed=x_points[0] == x_points[-1] and y_points[0] == y_points[-1],
            )
            kicad_polygons.append(kicad_polygon)
        else:
            logging.warning("Skipping polygon with no parseable points")

    return kicad_polygons


def convert_ee_polygons(
    ee_polygons: list[EeSymbolPolygon],
    ee_bbox: EeSymbolBbox,
) -> list[KiSymbolPolygon]:
    return convert_ee_polylines(ee_polylines=ee_polygons, ee_bbox=ee_bbox)


def convert_ee_paths(
    ee_paths: list[EeSymbolPath],
    ee_bbox: EeSymbolBbox,
) -> list[KiSymbolPolygon]:
    """Convert EasyEDA PT path shapes to KiCad polygons.

    Supports M, L, Z commands exactly. Curve commands (C, Q, A) are approximated
    by their endpoint so the polygon stays closed — the curve shape is lost.
    A warning is emitted when curves are present.

    TODO: replace endpoint approximation with proper tessellation once KiCad
    supports native bezier/arc in symbols or verified test cases are available.
    """
    kicad_polygons: list[KiSymbolPolygon] = []

    # (total args, 0-based index of endpoint x) per curve command
    # C: x1 y1 x2 y2 x y   Q: x1 y1 x y   A: rx ry rot fA fS x y
    _curve_cmd: dict[str, tuple[int, int]] = {"C": (6, 4), "Q": (4, 2), "A": (7, 5)}

    for ee_path in ee_paths:
        raw_pts = ee_path.paths.split()

        x_points = []
        y_points = []
        has_curves = False

        # Minimal SVG path parser: https://www.w3.org/TR/SVG11/paths.html#PathElement
        idx = 0
        while idx < len(raw_pts):
            token = raw_pts[idx]
            if token in ("M", "L"):
                x_points.append(px_to_mm(float(raw_pts[idx + 1]) - ee_bbox.x))
                y_points.append(-px_to_mm(float(raw_pts[idx + 2]) - ee_bbox.y))
                idx += 3
            elif token == "Z":  # noqa: S105 — SVG path command, not a password
                if x_points:
                    x_points.append(x_points[0])
                    y_points.append(y_points[0])
                idx += 1
            elif token in _curve_cmd:
                n_args, ep_idx = _curve_cmd[token]
                # Use the curve endpoint as straight-line approximation
                x_points.append(px_to_mm(float(raw_pts[idx + ep_idx + 1]) - ee_bbox.x))
                y_points.append(-px_to_mm(float(raw_pts[idx + ep_idx + 2]) - ee_bbox.y))
                has_curves = True
                idx += 1 + n_args
            else:
                idx += 1  # unknown token or stray coordinate

        if has_curves:
            logging.warning(
                f"PT path in symbol '{ee_path.paths[:40]}...': "
                f"curve commands (C/Q/A) approximated as straight lines — "
                f"shape may differ from original"
            )

        if x_points:
            ki_polygon = KiSymbolPolygon(
                points=[
                    [x_points[i], y_points[i]]
                    for i in range(min(len(x_points), len(y_points)))
                ],
                points_number=min(len(x_points), len(y_points)),
                is_closed=x_points[0] == x_points[-1] and y_points[0] == y_points[-1],
            )
            kicad_polygons.append(ki_polygon)
        else:
            logging.warning("PT path: skipping shape with no parseable points")

    return kicad_polygons


def convert_ee_texts(
    ee_texts: list[EeSymbolText],
    ee_bbox: EeSymbolBbox,
) -> list[KiSymbolText]:
    return [
        KiSymbolText(
            text=t.text,
            pos_x=px_to_mm(t.pos_x - ee_bbox.x),
            pos_y=-px_to_mm(t.pos_y - ee_bbox.y),
            rotation=t.rotation,
            font_size=t.font_size,
        )
        for t in ee_texts
    ]


def convert_to_kicad(
    ee_symbol: EeSymbol, custom_fields: dict[str, str] | None = None
) -> KiSymbol:
    ki_info = KiSymbolInfo(
        name=ee_symbol.info.name,
        prefix=ee_symbol.info.prefix.replace("?", ""),
        package=ee_symbol.info.package,
        manufacturer=ee_symbol.info.manufacturer,
        mpn=ee_symbol.info.mpn,
        datasheet=ee_symbol.info.datasheet,
        lcsc_id=ee_symbol.info.lcsc_id,
        keywords=ee_symbol.info.keywords,
        description=ee_symbol.info.description,
        custom_fields=dict(custom_fields or {}),
    )

    # Snap bbox to the 5px grid (= 1.27mm) so that pin coordinates, which are
    # typically integer multiples of 5px in absolute EasyEDA space, land on the
    # KiCad grid after subtraction — without per-coordinate rounding.
    snapped_x, snapped_y = snap_bbox(ee_symbol.bbox)
    snapped_bbox = EeSymbolBbox(x=snapped_x, y=snapped_y)

    kicad_symbol = KiSymbol(
        info=ki_info,
        pins=convert_ee_pins(ee_pins=ee_symbol.pins, ee_bbox=snapped_bbox),
        rectangles=convert_ee_rectangles(
            ee_rectangles=ee_symbol.rectangles, ee_bbox=snapped_bbox
        ),
        circles=convert_ee_circles(ee_circles=ee_symbol.circles, ee_bbox=snapped_bbox),
        arcs=convert_ee_arcs(ee_arcs=ee_symbol.arcs, ee_bbox=snapped_bbox),
    )
    kicad_symbol.circles += convert_ee_ellipses(
        ee_ellipses=ee_symbol.ellipses, ee_bbox=snapped_bbox
    )

    kicad_symbol.polygons = convert_ee_paths(
        ee_paths=ee_symbol.paths, ee_bbox=snapped_bbox
    )
    kicad_symbol.polygons += convert_ee_polylines(
        ee_polylines=ee_symbol.polylines, ee_bbox=snapped_bbox
    )
    kicad_symbol.polygons += convert_ee_polygons(
        ee_polygons=ee_symbol.polygons, ee_bbox=snapped_bbox
    )

    kicad_symbol.texts = convert_ee_texts(
        ee_texts=ee_symbol.texts, ee_bbox=snapped_bbox
    )

    return kicad_symbol


def tune_footprint_ref_path(ki_symbol: KiSymbol, footprint_lib_name: str) -> None:
    ki_symbol.info.package = f"{footprint_lib_name}:{ki_symbol.info.package}"


def integrate_sub_units(
    main_symbol: str,
    sub_symbols: list[str],
    component_name: str,
) -> str:
    """Integrate sub-unit symbols into a multi-unit KiCad symbol string.

    Extracts the _0_1 body block from each sub_symbol, renames it to _1_1,
    _2_1, ... and replaces the placeholder _0_1 block in main_symbol.
    Returns main_symbol unchanged if sub_symbols is empty or no match is found.
    """
    if not sub_symbols:
        return main_symbol

    name = re.escape(component_name)
    sub_units = []
    for i, sub_content in enumerate(sub_symbols, 1):
        match = re.search(
            rf'( +)\(symbol "{name}_0_1".*?\n\1\)(?=\n)', sub_content, re.DOTALL
        )
        if match:
            sub_units.append(
                match.group(0).replace(
                    f'"{component_name}_0_1"', f'"{component_name}_{i}_1"'
                )
            )

    if not sub_units:
        return main_symbol

    return re.sub(
        rf'( *)\(symbol "{name}_0_1".*?\n\1\)',
        "\n".join(sub_units),
        main_symbol,
        count=1,
        flags=re.DOTALL,
    )


class ExporterSymbolKicad:
    def __init__(
        self,
        symbol: EeSymbol,
        lib_path: str | None = None,
        version: int | None = None,
        custom_fields: dict[str, str] | None = None,
    ) -> None:
        self.input: EeSymbol = symbol
        self.version = (
            version if version is not None else read_symbol_lib_version(lib_path)
        )
        self.output = convert_to_kicad(
            ee_symbol=self.input, custom_fields=custom_fields
        )

    def export(self, footprint_lib_name: str) -> str:
        tune_footprint_ref_path(
            ki_symbol=self.output,
            footprint_lib_name=footprint_lib_name,
        )
        main_content = self.output.export(version=self.version)

        if not self.input.sub_symbols:
            return main_content

        sub_contents = [
            ExporterSymbolKicad(symbol=sub, version=self.version).export(
                footprint_lib_name=footprint_lib_name
            )
            for sub in self.input.sub_symbols
        ]
        return integrate_sub_units(
            main_symbol=main_content,
            sub_symbols=sub_contents,
            component_name=self.input.info.name,
        )

    def save_to_lib(
        self, lib_path: str, footprint_lib_name: str, overwrite: bool
    ) -> bool:
        """Export the symbol and write it into the .kicad_sym library file.

        Returns False if the symbol already exists and overwrite is False.
        """
        already_exists = id_already_in_symbol_lib(
            lib_path=lib_path, component_name=self.input.info.name
        )
        if already_exists and not overwrite:
            return False

        content = self.export(footprint_lib_name=footprint_lib_name)
        write_component_in_symbol_lib_file(
            lib_path=lib_path,
            component_name=self.input.info.name,
            component_content=content,
            version=self.version,
        )
        return True
