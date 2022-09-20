# Global imports
import logging
from typing import Callable, List, Tuple, Union

from easyeda2kicad.easyeda.parameters_easyeda import (
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
from easyeda2kicad.easyeda.svg_path_parser import SvgPathEllipticalArc, SvgPathMoveTo
from easyeda2kicad.helpers import get_middle_arc_pos
from easyeda2kicad.kicad.export_kicad_footprint import compute_arc
from easyeda2kicad.kicad.parameters_kicad_symbol import *

ee_pin_type_to_ki_pin_type = {
    EasyedaPinType.unspecified: KiPinType.unspecified,
    EasyedaPinType._input: KiPinType._input,
    EasyedaPinType.output: KiPinType.output,
    EasyedaPinType.bidirectional: KiPinType.bidirectional,
    EasyedaPinType.power: KiPinType.power_in,
}


def px_to_mil(dim: Union[int, float]) -> int:
    return int(10 * dim)


def px_to_mm(dim: Union[int, float]) -> float:
    return 10.0 * dim * 0.0254


def convert_ee_pins(
    ee_pins: List[EeSymbolPin], ee_bbox: EeSymbolBbox, kicad_version: KicadVersion
) -> List[KiSymbolPin]:

    to_ki: Callable = px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm
    # pin_spacing = (
    #     KiExportConfigV5.PIN_SPACING.value
    #     if kicad_version == KicadVersion.v5
    #     else KiExportConfigV6.PIN_SPACING.value
    # )

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

        # Deal with different pin length
        # if ee_pin.settings.rotation == 0:
        #     ki_pin.pos_x -= to_ki(pin_length) - pin_spacing
        # elif ee_pin.settings.rotation == 180:
        #     ki_pin.pos_x += to_ki(pin_length) - pin_spacing
        # elif ee_pin.settings.rotation == 90:
        #     ki_pin.pos_y -= to_ki(pin_length) - pin_spacing
        # elif ee_pin.settings.rotation == 270:
        #     ki_pin.pos_y += to_ki(pin_length) - pin_spacing

        kicad_pins.append(ki_pin)

    return kicad_pins


def convert_ee_rectangles(
    ee_rectangles: List[EeSymbolRectangle],
    ee_bbox: EeSymbolBbox,
    kicad_version: KicadVersion,
) -> List[KiSymbolRectangle]:

    to_ki: Callable = px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm

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
    ee_circles: List[EeSymbolCircle], ee_bbox: EeSymbolBbox, kicad_version: KicadVersion
):
    to_ki: Callable = px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm

    return [
        KiSymbolCircle(
            pos_x=to_ki(int(ee_circle.center_x) - int(ee_bbox.x)),
            pos_y=-to_ki(int(ee_circle.center_y) - int(ee_bbox.y)),
            radius=to_ki(ee_circle.radius),
            background_filling=ee_circle.fill_color,
        )
        for ee_circle in ee_circles
    ]


def convert_ee_ellipses(
    ee_ellipses: List[EeSymbolEllipse],
    ee_bbox: EeSymbolBbox,
    kicad_version: KicadVersion,
) -> List[KiSymbolCircle]:
    to_ki: Callable = px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm

    # Ellipses are not supported in Kicad -> If it's not a real ellipse, but just a circle
    return [
        KiSymbolCircle(
            pos_x=to_ki(int(ee_ellipses.center_x) - int(ee_bbox.x)),
            pos_y=-to_ki(int(ee_ellipses.center_y) - int(ee_bbox.y)),
            radius=to_ki(ee_ellipses.radius_x),
        )
        for ee_ellipses in ee_ellipses
        if ee_ellipses.radius_x == ee_ellipses.radius_y
    ]


def convert_ee_arcs(
    ee_arcs: List[EeSymbolArc], ee_bbox: EeSymbolBbox, kicad_version: KicadVersion
) -> List[KiSymbolArc]:
    to_ki: Callable = px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm

    kicad_arcs = []
    for ee_arc in ee_arcs:
        if not (
            isinstance(ee_arc.path[0], SvgPathMoveTo)
            or isinstance(ee_arc.path[1], SvgPathEllipticalArc)
        ):
            logging.error("Can't convert this arc")
        else:
            ki_arc = KiSymbolArc(
                radius=to_ki(
                    max(ee_arc.path[1].radius_x, ee_arc.path[1].radius_y)
                ),  # doesn't support elliptical arc
                angle_start=ee_arc.path[1].x_axis_rotation,
                start_x=to_ki(ee_arc.path[0].start_x - ee_bbox.x),
                start_y=to_ki(ee_arc.path[0].start_y - ee_bbox.y),
                end_x=to_ki(ee_arc.path[1].end_x - ee_bbox.x),
                end_y=to_ki(ee_arc.path[1].end_y - ee_bbox.y),
            )

            center_x, center_y, angle_end = compute_arc(
                start_x=ki_arc.start_x,
                start_y=ki_arc.start_y,
                radius_x=to_ki(ee_arc.path[1].radius_x),
                radius_y=to_ki(ee_arc.path[1].radius_y),
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
    ee_polylines: List[Union[EeSymbolPolyline, EeSymbolPolygon]],
    ee_bbox: EeSymbolBbox,
    kicad_version: KicadVersion,
) -> List[KiSymbolPolygon]:

    to_ki: Callable = px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm
    kicad_polygons = []
    for ee_polyline in ee_polylines:
        raw_pts = ee_polyline.points.split(" ")
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

        kicad_polygon = KiSymbolPolygon(
            points=[
                [x_points[i], y_points[i]]
                for i in range(min(len(x_points), len(y_points)))
            ],
            points_number=min(len(x_points), len(y_points)),
            is_closed=x_points[0] == x_points[-1] and y_points[0] == y_points[-1],
        )

        kicad_polygons.append(kicad_polygon)

    return kicad_polygons


def convert_ee_polygons(
    ee_polygons: List[EeSymbolPolygon],
    ee_bbox: EeSymbolBbox,
    kicad_version: KicadVersion,
) -> List[KiSymbolPolygon]:
    return convert_ee_polylines(
        ee_polylines=ee_polygons, ee_bbox=ee_bbox, kicad_version=kicad_version
    )


def convert_ee_paths(
    ee_paths: List[EeSymbolPath], ee_bbox: EeSymbolBbox, kicad_version: KicadVersion
) -> Tuple[List[KiSymbolPolygon], List[KiSymbolPolygon]]:
    kicad_polygons = []
    kicad_beziers = []
    to_ki: Callable = px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm

    for ee_path in ee_paths:
        raw_pts = ee_path.paths.split(" ")

        x_points = []
        y_points = []

        # Small svg path parser : doc -> https://www.w3.org/TR/SVG11/paths.html#PathElement

        for i in range(len(raw_pts)):
            if raw_pts[i] in ["M", "L"]:
                x_points.append(to_ki(int(float(raw_pts[i + 1])) - int(ee_bbox.x)))
                y_points.append(-to_ki(int(float(raw_pts[i + 2])) - int(ee_bbox.y)))
                i += 2
            elif raw_pts[i] == "Z":
                x_points.append(x_points[0])
                y_points.append(y_points[0])
            elif raw_pts[i] == "C":
                ...
                # TODO : Add bezier support

        # if ee_path.fill_color:
        #     x_points.append(x_points[0])
        #     y_points.append(y_points[0])

        ki_polygon = KiSymbolPolygon(
            points=[
                [x_points[i], y_points[i]]
                for i in range(min(len(x_points), len(y_points)))
            ],
            points_number=min(len(x_points), len(y_points)),
            is_closed=x_points[0] == x_points[-1] and y_points[0] == y_points[-1],
        )

        kicad_polygons.append(ki_polygon)

    return kicad_polygons, kicad_beziers


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

    kicad_symbol.polygons, kicad_symbol.beziers = convert_ee_paths(
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


def tune_footprint_ref_path(ki_symbol: KiSymbol, footprint_lib_name: str):
    ki_symbol.info.package = f"{footprint_lib_name}:{ki_symbol.info.package}"


class ExporterSymbolKicad:
    def __init__(self, symbol, kicad_version: KicadVersion):
        self.input: EeSymbol = symbol
        self.version = kicad_version
        self.output = (
            convert_to_kicad(ee_symbol=self.input, kicad_version=kicad_version)
            if isinstance(self.input, EeSymbol)
            else logging.error("Unknown input symbol format")
        )

    def export(self, footprint_lib_name: str) -> str:

        tune_footprint_ref_path(
            ki_symbol=self.output,
            footprint_lib_name=footprint_lib_name,
        )
        return self.output.export(kicad_version=self.version)
