# Global imports
import logging
from typing import Callable, List, Tuple, Union

from easyeda2kicad.easyeda.parameters_easyeda import (
    EasyedaPinType,
    EeSymbol,
    EeSymbolBbox,
    EeSymbolPath,
    EeSymbolPin,
    EeSymbolPolygon,
    EeSymbolPolyline,
    EeSymbolRectangle,
)
from easyeda2kicad.kicad.parameters_kicad_symbol import *

ee_pin_type_to_ki_pin_type = {
    EasyedaPinType.unspecified: KiPinType.unspecified,
    EasyedaPinType._input: KiPinType._input,
    EasyedaPinType.output: KiPinType.output,
    EasyedaPinType.bidirectional: KiPinType.bidirectional,
    EasyedaPinType.power: KiPinType.power_in,
}


def px_to_mil(dim: int) -> int:
    return 10 * dim


def px_to_mm(dim: int) -> float:
    return 10.0 * dim * 0.0254


def convert_ee_pins(
    ee_pins: List[EeSymbolPin], ee_bbox: EeSymbolBbox, kicad_version: KicadVersion
) -> List[KiSymbolPin]:

    to_ki: Callable = px_to_mil if kicad_version == KicadVersion.v5 else px_to_mm
    pin_spacing = (
        KiExportConfigV5.PIN_SPACING.value
        if kicad_version == KicadVersion.v5
        else KiExportConfigV6.PIN_SPACING.value
    )

    kicad_pins = []
    for ee_pin in ee_pins:
        ki_pin = KiSymbolPin(
            name=ee_pin.name.text.replace(" ", ""),
            number=ee_pin.settings.spice_pin_number.replace(" ", ""),
            style=KiPinStyle.line,
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

        pin_length = abs(int(float(ee_pin.pin_path.path.split("h")[-1])))
        # Deal with different pin length
        if ee_pin.settings.rotation == 0:
            ki_pin.pos_x -= to_ki(pin_length) - pin_spacing
        elif ee_pin.settings.rotation == 180:
            ki_pin.pos_x += to_ki(pin_length) - pin_spacing
        elif ee_pin.settings.rotation == 90:
            ki_pin.pos_y -= to_ki(pin_length) - pin_spacing
        elif ee_pin.settings.rotation == 270:
            ki_pin.pos_y += to_ki(pin_length) - pin_spacing

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


def convert_ee_circles(kicad_version: KicadVersion):
    # TODO
    return []


def convert_ee_arcs(kicad_version: KicadVersion):
    # TODO
    return []


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
        if isinstance(ee_polyline, EeSymbolPolygon):
            x_points.append(x_points[0])
            y_points.append(y_points[0])

        # print(x_points, y_points)
        # print(ee_bbox.x, ee_bbox.y)

        kicad_polygon = KiSymbolPolygon(
            points=[
                [str(x_points[i]), str(y_points[i])]
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
        for i in range(len(raw_pts) - 1):
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

        ki_polygon = KiSymbolPolygon(
            points=[
                [str(x_points[i]), str(y_points[i])]
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
        prefix=ee_symbol.info.prefix,
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
        circles=convert_ee_circles(kicad_version=kicad_version),
        arcs=convert_ee_arcs(kicad_version=kicad_version),
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


class ExporterSymbolKicad:
    def __init__(self, symbol, kicad_version: KicadVersion):
        self.input: EeSymbol = symbol
        self.version = kicad_version
        self.output = (
            convert_to_kicad(ee_symbol=self.input, kicad_version=kicad_version)
            if isinstance(self.input, EeSymbol)
            else logging.error("Unknown input symbol format")
        )

    def get_kicad_lib(self) -> str:
        # TODO: export for v5 and v6 kicad
        return self.output.export(kicad_version=self.version)
