# Global imports
import logging
import re
from typing import Callable, Sequence

# Local imports
from ..helpers import sanitize_for_regex
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
)
from ..easyeda.svg_path_parser import SvgPathEllipticalArc, SvgPathMoveTo
from ..helpers import get_middle_arc_pos
from .export_kicad_footprint import compute_arc
from .parameters_kicad_symbol import (
    KicadVersion,
    KiPinStyle,
    KiPinType,
    KiSymbol,
    KiSymbolArc,
    KiSymbolCircle,
    KiSymbolInfo,
    KiSymbolPin,
    KiSymbolPolygon,
    KiSymbolRectangle,
)

ee_pin_type_to_ki_pin_type = {
    EasyedaPinType.unspecified: KiPinType.unspecified,
    EasyedaPinType._input: KiPinType._input,
    EasyedaPinType.output: KiPinType.output,
    EasyedaPinType.bidirectional: KiPinType.bidirectional,
    EasyedaPinType.power: KiPinType.power_in,
}


def px_to_mil(dim: int | float | str) -> int:
    return int(10 * float(dim))


def px_to_mm(dim: int | float | str) -> float:
    return 10.0 * float(dim) * 0.0254


def px_to_mm_grid(dim: int | float | str, grid: float = 1.27) -> float:
    """Convert EasyEDA pixels to KiCad mm and snap to grid (default 50mil = 1.27mm)."""
    mm_value = 10.0 * float(dim) * 0.0254
    return round(mm_value / grid) * grid


def convert_ee_pins(
    ee_pins: list[EeSymbolPin], ee_bbox: EeSymbolBbox, kicad_version: KicadVersion
) -> list[KiSymbolPin]:
    to_ki: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm_grid
    )

    kicad_pins = []
    for ee_pin in ee_pins:
        pin_length = abs(int(float(ee_pin.pin_path.path.split("h")[-1])))

        ki_pin = KiSymbolPin(
            name=ee_pin.name.text.replace(" ", ""),
            number=ee_pin.settings.spice_pin_number.replace(" ", ""),
            style=KiPinStyle.line,
            length=to_ki(pin_length),
            type=ee_pin_type_to_ki_pin_type[ee_pin.settings.type],
            orientation=ee_pin.settings.rotation,
            pos_x=to_ki(int(ee_pin.settings.pos_x) - int(ee_bbox.x)),
            pos_y=-to_ki(int(ee_pin.settings.pos_y) - int(ee_bbox.y)),
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
    kicad_version: KicadVersion,
) -> list[KiSymbolRectangle]:
    to_ki: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm_grid
    )

    kicad_rectangles = []
    for ee_rectangle in ee_rectangles:
        ki_rectangle = KiSymbolRectangle(
            pos_x0=to_ki(int(ee_rectangle.pos_x) - int(ee_bbox.x)),
            pos_y0=-to_ki(int(ee_rectangle.pos_y) - int(ee_bbox.y)),
        )
        ki_rectangle.pos_x1 = to_ki(int(ee_rectangle.width)) + ki_rectangle.pos_x0
        ki_rectangle.pos_y1 = -to_ki(int(ee_rectangle.height)) + ki_rectangle.pos_y0

        kicad_rectangles.append(ki_rectangle)

    return kicad_rectangles


def convert_ee_circles(
    ee_circles: list[EeSymbolCircle], ee_bbox: EeSymbolBbox, kicad_version: KicadVersion
) -> list[KiSymbolCircle]:
    to_ki: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm_grid
    )
    # For dimensions like radius, use px_to_mm without grid snapping
    to_ki_dimension: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm
    )

    return [
        KiSymbolCircle(
            pos_x=to_ki(int(ee_circle.center_x) - int(ee_bbox.x)),
            pos_y=-to_ki(int(ee_circle.center_y) - int(ee_bbox.y)),
            radius=to_ki_dimension(ee_circle.radius),
            background_filling=ee_circle.fill_color,
        )
        for ee_circle in ee_circles
    ]


def convert_ee_ellipses(
    ee_ellipses: list[EeSymbolEllipse],
    ee_bbox: EeSymbolBbox,
    kicad_version: KicadVersion,
) -> list[KiSymbolCircle]:
    to_ki: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm_grid
    )
    # For dimensions like radius, use px_to_mm without grid snapping
    to_ki_dimension: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm
    )

    # Ellipses are not supported in Kicad -> If it's not a real ellipse, but just a circle
    return [
        KiSymbolCircle(
            pos_x=to_ki(int(ee_ellipses.center_x) - int(ee_bbox.x)),
            pos_y=-to_ki(int(ee_ellipses.center_y) - int(ee_bbox.y)),
            radius=to_ki_dimension(ee_ellipses.radius_x),
        )
        for ee_ellipses in ee_ellipses
        if ee_ellipses.radius_x == ee_ellipses.radius_y
    ]


def convert_ee_arcs(
    ee_arcs: list[EeSymbolArc], ee_bbox: EeSymbolBbox, kicad_version: KicadVersion
) -> list[KiSymbolArc]:
    to_ki: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm_grid
    )
    # For dimensions like radius, use px_to_mm without grid snapping
    to_ki_dimension: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm
    )

    kicad_arcs = []
    for ee_arc in ee_arcs:
        if (
            len(ee_arc.path) < 2
            or not isinstance(ee_arc.path[0], SvgPathMoveTo)
            or not isinstance(ee_arc.path[1], SvgPathEllipticalArc)
        ):
            logging.error("Can't convert this arc: unexpected SVG path structure")
            continue
        else:
            ki_arc = KiSymbolArc(
                radius=to_ki_dimension(
                    max(float(ee_arc.path[1].radius_x), float(ee_arc.path[1].radius_y))
                ),  # doesn't support elliptical arc
                angle_start=float(ee_arc.path[1].x_axis_rotation),
                start_x=to_ki(float(ee_arc.path[0].start_x) - ee_bbox.x),
                start_y=-to_ki(float(ee_arc.path[0].start_y) - ee_bbox.y),
                end_x=to_ki(float(ee_arc.path[1].end_x) - ee_bbox.x),
                end_y=-to_ki(float(ee_arc.path[1].end_y) - ee_bbox.y),
            )

            center_x, center_y, angle_end = compute_arc(
                start_x=ki_arc.start_x,
                start_y=ki_arc.start_y,
                radius_x=to_ki_dimension(ee_arc.path[1].radius_x),
                radius_y=to_ki_dimension(ee_arc.path[1].radius_y),
                angle=ki_arc.angle_start,
                large_arc_flag=ee_arc.path[1].flag_large_arc,
                sweep_flag=ee_arc.path[1].flag_sweep,
                end_x=ki_arc.end_x,
                end_y=ki_arc.end_y,
            )
            ki_arc.center_x = center_x
            ki_arc.center_y = center_y if ee_arc.path[1].flag_large_arc else -center_y
            ki_arc.angle_end = (
                (360 - angle_end) if ee_arc.path[1].flag_large_arc else angle_end
            )

            ki_arc.middle_x, ki_arc.middle_y = get_middle_arc_pos(
                center_x=ki_arc.center_x,
                center_y=ki_arc.center_y,
                radius=ki_arc.radius,
                angle_start=ki_arc.angle_start,
                angle_end=ki_arc.angle_end,
            )

            ki_arc.start_y = (
                ki_arc.start_y if ee_arc.path[1].flag_large_arc else -ki_arc.start_y
            )
            ki_arc.end_y = (
                ki_arc.end_y if ee_arc.path[1].flag_large_arc else -ki_arc.end_y
            )

            kicad_arcs.append(ki_arc)

    return kicad_arcs


def convert_ee_polylines(
    ee_polylines: Sequence[EeSymbolPolyline | EeSymbolPolygon],
    ee_bbox: EeSymbolBbox,
    kicad_version: KicadVersion,
) -> list[KiSymbolPolygon]:
    to_ki: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm_grid
    )
    kicad_polygons = []
    for ee_polyline in ee_polylines:
        raw_pts = ee_polyline.points.split()
        # print(raw_pts)
        x_points = [
            to_ki(int(float(raw_pts[i])) - int(ee_bbox.x))
            for i in range(0, len(raw_pts), 2)
        ]
        y_points = [
            -to_ki(int(float(raw_pts[i])) - int(ee_bbox.y))
            for i in range(1, len(raw_pts), 2)
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
    kicad_version: KicadVersion,
) -> list[KiSymbolPolygon]:
    return convert_ee_polylines(
        ee_polylines=ee_polygons, ee_bbox=ee_bbox, kicad_version=kicad_version
    )


def convert_ee_paths(
    ee_paths: list[EeSymbolPath], ee_bbox: EeSymbolBbox, kicad_version: KicadVersion
) -> list[KiSymbolPolygon]:
    # TODO: PT path support is simplified — curves are silently dropped.
    # EasyEDA's PT command supports M, L, C (cubic bezier), Q (quadratic bezier),
    # A (arc), and Z. Currently only M/L/Z are converted to straight-line polygon
    # segments; C/Q/A tokens are skipped along with their coordinate values.
    # This produces correct output for paths made of straight lines, but symbols
    # with curves will appear as polygons with missing segments.
    # Note: the EasyEDA PT format documentation (CMD_SYMBOL.md) is not fully
    # verified — implement curve support only once test cases are confirmed.
    kicad_polygons: list[KiSymbolPolygon] = []
    to_ki: Callable[[int | float | str], float] = (
        px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm_grid
    )

    # Token counts consumed by each SVG path command (excluding the command letter itself)
    _curve_tokens = {"C": 6, "Q": 4, "A": 7}

    for ee_path in ee_paths:
        raw_pts = ee_path.paths.split()

        x_points = []
        y_points = []

        # Minimal SVG path parser: https://www.w3.org/TR/SVG11/paths.html#PathElement
        idx = 0
        while idx < len(raw_pts):
            token = raw_pts[idx]
            if token in ("M", "L"):
                x_points.append(to_ki(int(float(raw_pts[idx + 1])) - int(ee_bbox.x)))
                y_points.append(-to_ki(int(float(raw_pts[idx + 2])) - int(ee_bbox.y)))
                idx += 3
            elif token == "Z":
                if x_points:
                    x_points.append(x_points[0])
                    y_points.append(y_points[0])
                idx += 1
            elif token in _curve_tokens:
                logging.debug(
                    f"PT path: '{token}' curve command not supported, "
                    f"skipping {_curve_tokens[token]} coordinate tokens"
                )
                idx += 1 + _curve_tokens[token]
            else:
                idx += 1  # unknown token or stray coordinate

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


def convert_to_kicad(ee_symbol: EeSymbol, kicad_version: KicadVersion) -> KiSymbol:
    ki_info = KiSymbolInfo(
        name=ee_symbol.info.name,
        prefix=ee_symbol.info.prefix.replace("?", ""),
        package=ee_symbol.info.package,
        manufacturer=ee_symbol.info.manufacturer,
        datasheet=ee_symbol.info.datasheet,
        lcsc_id=ee_symbol.info.lcsc_id,
        jlc_id=ee_symbol.info.jlc_id,
    )

    kicad_symbol = KiSymbol(
        info=ki_info,
        pins=convert_ee_pins(
            ee_pins=ee_symbol.pins, ee_bbox=ee_symbol.bbox, kicad_version=kicad_version
        ),
        rectangles=convert_ee_rectangles(
            ee_rectangles=ee_symbol.rectangles,
            ee_bbox=ee_symbol.bbox,
            kicad_version=kicad_version,
        ),
        circles=convert_ee_circles(
            ee_circles=ee_symbol.circles,
            ee_bbox=ee_symbol.bbox,
            kicad_version=kicad_version,
        ),
        arcs=convert_ee_arcs(
            ee_arcs=ee_symbol.arcs, ee_bbox=ee_symbol.bbox, kicad_version=kicad_version
        ),
    )
    kicad_symbol.circles += convert_ee_ellipses(
        ee_ellipses=ee_symbol.ellipses,
        ee_bbox=ee_symbol.bbox,
        kicad_version=kicad_version,
    )

    kicad_symbol.polygons = convert_ee_paths(
        ee_paths=ee_symbol.paths, ee_bbox=ee_symbol.bbox, kicad_version=kicad_version
    )
    kicad_symbol.polygons += convert_ee_polylines(
        ee_polylines=ee_symbol.polylines,
        ee_bbox=ee_symbol.bbox,
        kicad_version=kicad_version,
    )
    kicad_symbol.polygons += convert_ee_polygons(
        ee_polygons=ee_symbol.polygons,
        ee_bbox=ee_symbol.bbox,
        kicad_version=kicad_version,
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

    name = sanitize_for_regex(component_name)
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
    def __init__(self, symbol: EeSymbol, kicad_version: KicadVersion) -> None:
        self.input: EeSymbol = symbol
        self.version = kicad_version
        self.output = convert_to_kicad(ee_symbol=self.input, kicad_version=kicad_version)

    def export(self, footprint_lib_name: str) -> str:
        tune_footprint_ref_path(
            ki_symbol=self.output,
            footprint_lib_name=footprint_lib_name,
        )
        main_content = self.output.export(kicad_version=self.version)

        if not self.input.sub_symbols or self.version != KicadVersion.v6:
            return main_content

        sub_contents = [
            ExporterSymbolKicad(symbol=sub, kicad_version=self.version).export(
                footprint_lib_name=footprint_lib_name
            )
            for sub in self.input.sub_symbols
        ]
        return integrate_sub_units(
            main_symbol=main_content,
            sub_symbols=sub_contents,
            component_name=self.input.info.name,
        )
