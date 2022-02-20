# Global imports
from itertools import chain

from easyeda2kicad.easyeda.parameters_easyeda import ee_symbol
from easyeda2kicad.kicad.parameters_kicad import *


# ---------------------------------------
def resize_to_kicad(dim: int):
    return 10 * dim


# ---------------------------------------
class exporter_symbol_kicad:
    def __init__(self, symbol):
        self.input: ee_symbol = symbol
        if type(self.input) is not ee_symbol:
            print("Conversion non supportée")
        else:
            self.generate_kicad_symbol()

    def generate_kicad_symbol(self):

        ki_info = ki_symbol_info(
            name=self.input.info.name.replace(" ", ""),
            prefix=self.input.info.prefix.replace(" ", ""),
            package=self.input.info.package,
            manufacturer=self.input.info.manufacturer,
            datasheet=self.input.info.datasheet,
            lcsc_id=self.input.info.lcsc_id,
            jlc_id=self.input.info.jlc_id,
        )

        self.output = ki_symbol(info=ki_info, pins=[], rectangles=[], polylines=[])

        # For pins
        for ee_pin in self.input.pins:
            ki_pin = ki_symbol_pin(
                name=ee_pin.name.text.replace(" ", ""),
                number=ee_pin.settings.spice_pin_number.replace(" ", ""),
                style="",
                type=KI_PIN_TYPES[ee_pin.settings.type],
                orientation=KI_PIN_ORIENTATIONS[
                    kicad_pin_orientation(ee_pin.settings.rotation).name
                ],
                pos_x=resize_to_kicad(
                    int(ee_pin.settings.pos_x) - int(self.input.bbox.x)
                ),
                pos_y=-resize_to_kicad(
                    int(ee_pin.settings.pos_y) - int(self.input.bbox.y)
                ),
            )

            ki_pin.style = (
                KI_PIN_STYLES["inverted"] if ee_pin.dot.is_displayed == "1" else ""
            )  # A vérifier
            ki_pin.style += (
                KI_PIN_STYLES["clock"] if ee_pin.clock.is_displayed == "1" else ""
            )

            pin_length = abs(int(float(ee_pin.pin_path.path.split("h")[-1])))
            # Deal with different pin length
            if ee_pin.settings.rotation == 0:
                ki_pin.pos_x -= resize_to_kicad(pin_length) - KI_PIN_SPACING
            elif ee_pin.settings.rotation == 180:
                ki_pin.pos_x += resize_to_kicad(pin_length) - KI_PIN_SPACING
            elif ee_pin.settings.rotation == 90:
                ki_pin.pos_y -= resize_to_kicad(pin_length) - KI_PIN_SPACING
            elif ee_pin.settings.rotation == 270:
                ki_pin.pos_y += resize_to_kicad(pin_length) - KI_PIN_SPACING

            self.output.pins.append(ki_pin)

        # For rectangles
        for ee_rectangle in self.input.rectangles:
            ki_rectangle = ki_symbol_rectangle(
                pos_x0=resize_to_kicad(
                    int(ee_rectangle.pos_x) - int(self.input.bbox.x)
                ),
                pos_y0=-resize_to_kicad(
                    int(ee_rectangle.pos_y) - int(self.input.bbox.y)
                ),
            )
            ki_rectangle.pos_x1 = (
                resize_to_kicad(int(ee_rectangle.width)) + ki_rectangle.pos_x0
            )
            ki_rectangle.pos_y1 = (
                -resize_to_kicad(int(ee_rectangle.height)) + ki_rectangle.pos_y0
            )

            self.output.rectangles.append(ki_rectangle)

        # For polylines
        for ee_polyline in self.input.polylines:
            raw_pts = ee_polyline.points.split(" ")
            print(raw_pts)
            x_points = [
                resize_to_kicad(int(float(raw_pts[i])) - int(self.input.bbox.x))
                for i in range(0, len(raw_pts), 2)
            ]
            y_points = [
                resize_to_kicad(int(float(raw_pts[i])) - int(self.input.bbox.y))
                for i in range(1, len(raw_pts), 2)
            ]
            print(x_points, y_points)
            print(self.input.bbox.x, self.input.bbox.y)

            ki_polyline = ki_symbol_polyline(
                points=[
                    [str(x_points[i]), str(y_points[i])]
                    for i in range(min(len(x_points), len(y_points)))
                ],
                points_number=min(len(x_points), len(y_points)),
            )

            self.output.polylines.append(ki_polyline)

        # For paths
        for ee_path in self.input.paths:
            raw_pts = ee_path.paths.split(" ")

            x_points = []
            y_points = []

            # Small svg path parser : doc -> https://www.w3.org/TR/SVG11/paths.html#PathElement
            for i in range(len(raw_pts) - 1):
                if raw_pts[i] in ["M", "L"]:
                    x_points.append(
                        resize_to_kicad(
                            int(float(raw_pts[i + 1])) - int(self.input.bbox.x)
                        )
                    )
                    y_points.append(
                        resize_to_kicad(
                            int(float(raw_pts[i + 2])) - int(self.input.bbox.y)
                        )
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

            self.output.polylines.append(ki_polyline)

    def get_ki_symbol(self):
        return self.output

    def export_symbol(self):
        ki = self.output

        # ki_lib = "EESchema-LIBRARY Version 2.4\n"
        ki_lib = f"#\n# {ki.info.name}\n#\n"
        # Start the part definition with the header.
        ki_lib += KI_START_DEF.format(
            name=ki.info.name,
            ref=ki.info.prefix,
            pin_name_offset=KI_PIN_NAME_OFFSET,
            show_pin_number=KI_SHOW_PIN_NUMBER and "Y" or "N",
            show_pin_name=KI_SHOW_PIN_NAME and "Y" or "N",
            num_units=1,
        )

        # Determine if there are pins across the top of the symbol.
        text_justification = "C"  # Center

        # Get y_min and y_max to put component info

        y_low = min(pin.pos_y for pin in ki.pins) if ki.pins else 0
        y_high = max(pin.pos_y for pin in ki.pins) if ki.pins else 0

        # Create the field that stores the part reference.
        ki_lib += KI_REF_FIELD.format(
            ref_prefix=ki.info.prefix,
            x=0,
            y=y_high + KI_REF_Y_OFFSET,
            text_justification=text_justification,
            font_size=KI_REF_SIZE,
        )

        # Create the field that stores the part number.
        ki_lib += KI_PARTNUM_FIELD.format(
            num=ki.info.name,
            x=0,
            y=y_low - KI_PART_NUM_Y_OFFSET,
            text_justification=text_justification,
            font_size=KI_PART_NUM_SIZE,
        )

        # Create the field that stores the part footprint.
        if ki.info.package:
            ki_lib += KI_FOOTPRINT_FIELD.format(
                footprint=ki.info.package,
                x=0,
                y=y_low - KI_PART_FOOTPRINT_Y_OFFSET,
                text_justification=text_justification,
                font_size=KI_PART_FOOTPRINT_SIZE,
            )

        # Create the field that stores the datasheet link.
        if ki.info.datasheet:
            ki_lib += KI_DATASHEET_FIELD.format(
                datasheet=ki.info.datasheet,
                x=0,
                y=y_low - KI_PART_DATASHEET_Y_OFFSET,
                text_justification=text_justification,
                font_size=KI_PART_DATASHEET_SIZE,
            )

        # Create the field that stores the manufacturer part number.
        if ki.info.manufacturer:
            ki_lib += KI_MPN_FIELD.format(
                manufacturer=ki.info.manufacturer,
            )

        if ki.info.lcsc_id:
            ki_lib += KI_LCSC_FIELD.format(
                id=ki.info.lcsc_id,
            )

        if ki.info.jlc_id:
            ki_lib += KI_JLCPCB_FIELD.format(type=ki.info.jlc_id)

        # Start the section of the part definition that holds the part's units.
        ki_lib += KI_START_DRAW

        # ---------------------------------------
        for ki_pin in ki.pins:
            ki_lib += KI_PIN.format(
                name=ki_pin.name,
                num=ki_pin.number,
                x=ki_pin.pos_x,
                y=ki_pin.pos_y,
                length=KI_PIN_LENGTH,
                orientation=ki_pin.orientation,
                num_sz=KI_PIN_NUM_SIZE,
                name_sz=KI_PIN_NAME_SIZE,
                unit_num=1,
                pin_type=ki_pin.type,
                pin_style=ki_pin.style,
            )

        # ---------------------------------------
        for rectangle in ki.rectangles:
            ki_lib += KI_BOX.format(
                x0=int(round(rectangle.pos_x0 / 50.0)) * 50,
                y0=int(round(rectangle.pos_y0 / 50.0)) * 50,
                x1=int(round(rectangle.pos_x1 / 50.0)) * 50,
                y1=int(round(rectangle.pos_y1 / 50.0)) * 50,
                unit_num=1,
                line_width=KI_DEFAULT_BOX_LINE_WIDTH,
                fill=KI_BOX_FILLS["bg_fill"],
            )

        # ---------------------------------------
        for polyline in ki.polylines:
            ki_lib += KI_POLYLINE.format(
                points_number=polyline.points_number,
                unit_num=1,
                line_width=KI_DEFAULT_BOX_LINE_WIDTH,
                coordinate=" ".join(list(chain.from_iterable(polyline.points))),
                fill=KI_BOX_FILLS["bg_fill"]
                if polyline.is_closed
                else KI_BOX_FILLS["no_fill"],
            )
        # ---------------------------------------

        # Close the section that holds the part's units.
        ki_lib += KI_END_DRAW

        # Close the part definition.
        ki_lib += KI_END_DEF

        return ki_lib
