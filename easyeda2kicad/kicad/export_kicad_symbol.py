# Global imports
from typing import List

from easyeda2kicad.easyeda.parameters_easyeda import (
    ee_symbol,
    ee_symbol_bbox,
    ee_symbol_pin,
    ee_symbol_rectangle,
)
from easyeda2kicad.kicad.parameters_kicad import *


def px_to_mil(dim: int):
    return 10 * dim


def convert_pins(
    ee_pins: List[ee_symbol_pin], ee_bbox: ee_symbol_bbox
) -> List[ki_symbol_pin]:
    kicad_pins = []
    for ee_pin in ee_pins:
        ki_pin = ki_symbol_pin(
            name=ee_pin.name.text.replace(" ", ""),
            number=ee_pin.settings.spice_pin_number.replace(" ", ""),
            style="",
            type=KI_PIN_TYPES[ee_pin.settings.type],
            orientation=KI_PIN_ORIENTATIONS[
                kicad_pin_orientation(ee_pin.settings.rotation).name
            ],
            pos_x=px_to_mil(int(ee_pin.settings.pos_x) - int(ee_bbox.x)),
            pos_y=-px_to_mil(int(ee_pin.settings.pos_y) - int(ee_bbox.y)),
        )

        ki_pin.style = (
            KI_PIN_STYLES["inverted"] if ee_pin.dot.is_displayed == "1" else ""
        )
        ki_pin.style += (
            KI_PIN_STYLES["clock"] if ee_pin.clock.is_displayed == "1" else ""
        )

        pin_length = abs(int(float(ee_pin.pin_path.path.split("h")[-1])))
        # Deal with different pin length
        if ee_pin.settings.rotation == 0:
            ki_pin.pos_x -= px_to_mil(pin_length) - KI_PIN_SPACING
        elif ee_pin.settings.rotation == 180:
            ki_pin.pos_x += px_to_mil(pin_length) - KI_PIN_SPACING
        elif ee_pin.settings.rotation == 90:
            ki_pin.pos_y -= px_to_mil(pin_length) - KI_PIN_SPACING
        elif ee_pin.settings.rotation == 270:
            ki_pin.pos_y += px_to_mil(pin_length) - KI_PIN_SPACING

        kicad_pins.append(ki_pin)

    return kicad_pins


def convert_rectangles(
    ee_rectangles: List[ee_symbol_rectangle], ee_bbox: ee_symbol_bbox
) -> List[ki_symbol_rectangle]:
    kicad_rectangles = []
    for ee_rectangle in ee_rectangles:
        ki_rectangle = ki_symbol_rectangle(
            pos_x0=px_to_mil(int(ee_rectangle.pos_x) - int(ee_bbox.x)),
            pos_y0=-px_to_mil(int(ee_rectangle.pos_y) - int(ee_bbox.y)),
        )
        ki_rectangle.pos_x1 = px_to_mil(int(ee_rectangle.width)) + ki_rectangle.pos_x0
        ki_rectangle.pos_y1 = -px_to_mil(int(ee_rectangle.height)) + ki_rectangle.pos_y0

        kicad_rectangles.append(ki_rectangle)

    return kicad_rectangles


def convert_to_kicad(ee_symbol: ee_symbol):

    ki_info = ki_symbol_info(
        name=ee_symbol.info.name.replace(" ", ""),
        prefix=ee_symbol.info.prefix.replace(" ", ""),
        package=ee_symbol.info.package,
        manufacturer=ee_symbol.info.manufacturer,
        datasheet=ee_symbol.info.datasheet,
        lcsc_id=ee_symbol.info.lcsc_id,
        jlc_id=ee_symbol.info.jlc_id,
    )

    kicad_symbol = ki_symbol(
        info=ki_info,
        pins=convert_pins(ee_pins=ee_symbol.pins, ee_bbox=ee_symbol.bbox),
        rectangles=convert_rectangles(
            ee_rectangles=ee_symbol.rectangles, ee_bbox=ee_symbol.bbox
        ),
        circles=[],
        arcs=[],
        polylines=[],
    )

    # For polylines
    for ee_polyline in ee_symbol.polylines:
        raw_pts = ee_polyline.points.split(" ")
        # print(raw_pts)
        x_points = [
            px_to_mil(int(float(raw_pts[i])) - int(ee_symbol.bbox.x))
            for i in range(0, len(raw_pts), 2)
        ]
        y_points = [
            px_to_mil(int(float(raw_pts[i])) - int(ee_symbol.bbox.y))
            for i in range(1, len(raw_pts), 2)
        ]
        # print(x_points, y_points)
        # print(ee_symbol.bbox.x, ee_symbol.bbox.y)

        ki_polyline = ki_symbol_polyline(
            points=[
                [str(x_points[i]), str(y_points[i])]
                for i in range(min(len(x_points), len(y_points)))
            ],
            points_number=min(len(x_points), len(y_points)),
        )

        kicad_symbol.polylines.append(ki_polyline)

    # For paths
    for ee_path in ee_symbol.paths:
        raw_pts = ee_path.paths.split(" ")

        x_points = []
        y_points = []

        # Small svg path parser : doc -> https://www.w3.org/TR/SVG11/paths.html#PathElement
        for i in range(len(raw_pts) - 1):
            if raw_pts[i] in ["M", "L"]:
                x_points.append(
                    px_to_mil(int(float(raw_pts[i + 1])) - int(ee_symbol.bbox.x))
                )
                y_points.append(
                    px_to_mil(int(float(raw_pts[i + 2])) - int(ee_symbol.bbox.y))
                )
                i += 2
            elif raw_pts[i] == "Z":
                x_points.append(x_points[0])
                y_points.append(y_points[0])
            elif raw_pts[i] == "C":
                ...
                # TODO : Add bezier support

        ki_polyline = ki_symbol_polyline(
            points=[
                [str(x_points[i]), str(y_points[i])]
                for i in range(min(len(x_points), len(y_points)))
            ],
            points_number=min(len(x_points), len(y_points)),
            is_closed=x_points[0] == x_points[-1] and y_points[0] == y_points[-1],
        )

        kicad_symbol.polylines.append(ki_polyline)

    # For circle
    return kicad_symbol


class exporter_symbol_kicad:
    def __init__(self, symbol, kicad_version):
        self.input: ee_symbol = symbol
        self.version = kicad_version
        self.output = (
            convert_to_kicad(ee_symbol=self.input)
            if isinstance(self.input, ee_symbol)
            else print("[-] Unknown format")
        )

    def get_kicad_lib(self):
        # TODO: export for v5 and v6 kicad
        return self.output.export()
