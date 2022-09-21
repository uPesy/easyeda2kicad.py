# Global imports
import itertools
import re
import textwrap
from dataclasses import dataclass, field, fields
from enum import Enum, auto
from typing import List, Union


class KicadVersion(Enum):
    v5 = auto()
    v6 = auto()
    v6_99 = auto()


class KiPinType(Enum):
    _input = auto()
    output = auto()
    bidirectional = auto()
    tri_state = auto()
    passive = auto()
    free = auto()
    unspecified = auto()
    power_in = auto()
    power_out = auto()
    open_collector = auto()
    open_emitter = auto()
    no_connect = auto()


class KiPinStyle(Enum):
    line = auto()
    inverted = auto()
    clock = auto()
    inverted_clock = auto()
    input_low = auto()
    clock_low = auto()
    output_low = auto()
    edge_clock_high = auto()
    non_logic = auto()


class KiBoxFill(Enum):
    none = auto()
    outline = auto()
    background = auto()


# Config V5
# Dimensions are in mil
class KiExportConfigV5(Enum):
    PIN_LENGTH = 100
    PIN_SPACING = 100
    PIN_NUM_SIZE = 50
    PIN_NAME_SIZE = 50
    PIN_NAME_OFFSET = 40
    DEFAULT_BOX_LINE_WIDTH = 0
    FIELD_FONT_SIZE = 60
    FIELD_OFFSET_START = 200
    FIELD_OFFSET_INCREMENT = 100


ki_pin_type_v5_format = {
    KiPinType._input: "I",
    KiPinType.output: "O",
    KiPinType.bidirectional: "B",
    KiPinType.tri_state: "T",
    KiPinType.passive: "P",
    KiPinType.free: "U",
    KiPinType.unspecified: "U",
    KiPinType.power_in: "W",
    KiPinType.power_out: "W",
    KiPinType.open_collector: "C",
    KiPinType.open_emitter: "E",
    KiPinType.no_connect: "N",
}

ki_pin_style_v5_format = {
    KiPinStyle.line: "",
    KiPinStyle.inverted: "I",
    KiPinStyle.clock: "C",
    KiPinStyle.inverted_clock: "F",
    KiPinStyle.input_low: "L",
    KiPinStyle.clock_low: "CL",
    KiPinStyle.output_low: "V",
    KiPinStyle.edge_clock_high: "C",
    KiPinStyle.non_logic: "X",
}

ki_pin_orientation_v5_format = {"0": "L", "90": "D", "180": "R", "270": "U"}

ki_box_fill_v5_format = {
    KiBoxFill.none: "N",
    KiBoxFill.outline: "F",
    KiBoxFill.background: "f",
}


def sanitize_fields(name: str) -> str:
    return name.replace(" ", "").replace("/", "_")


def apply_text_style(text: str, kicad_version: KicadVersion) -> str:
    if text.endswith("#"):
        text = (
            f"~{{{text[:-1]}}}"
            if kicad_version == KicadVersion.v6
            else f"~{text[:-1]}~"
        )
    return text


def apply_pin_name_style(pin_name: str, kicad_version: KicadVersion) -> str:
    return "/".join(
        apply_text_style(text=txt, kicad_version=kicad_version)
        for txt in pin_name.split("/")
    )


# Config V6
# Dimensions are in mm
class KiExportConfigV6(Enum):
    PIN_LENGTH = 2.54
    PIN_SPACING = 2.54
    PIN_NUM_SIZE = 1.27
    PIN_NAME_SIZE = 1.27
    DEFAULT_BOX_LINE_WIDTH = 0
    PROPERTY_FONT_SIZE = 1.27
    FIELD_OFFSET_START = 5.08
    FIELD_OFFSET_INCREMENT = 2.54


# ---------------- INFO HEADER ----------------
@dataclass
class KiSymbolInfo:
    name: str
    prefix: str
    package: str
    manufacturer: str
    datasheet: str
    lcsc_id: str
    jlc_id: str
    y_low: Union[int, float] = 0
    y_high: Union[int, float] = 0

    def export_v5(self) -> str:
        field_offset_y = KiExportConfigV5.FIELD_OFFSET_START.value
        header: List[str] = [
            "DEF {name} {ref} 0 {pin_name_offset} {show_pin_number} {show_pin_name}"
            " {num_units} L N".format(
                name=sanitize_fields(self.name),
                ref=self.prefix,
                pin_name_offset=KiExportConfigV5.PIN_NAME_OFFSET.value,
                show_pin_number="Y",
                show_pin_name="Y",
                num_units=1,
            ),
            'F0 "{ref_prefix}" {x} {y} {font_size} H V {text_justification} CNN'.format(
                ref_prefix=self.prefix,
                x=0,
                y=self.y_high + field_offset_y,
                text_justification="C",  # Center align
                font_size=KiExportConfigV5.FIELD_FONT_SIZE.value,
            ),
            'F1 "{num}" {x} {y} {font_size} H V {text_justification} CNN'.format(
                num=self.name,
                x=0,
                y=self.y_low - field_offset_y,
                text_justification="C",  # Center align
                font_size=KiExportConfigV5.FIELD_FONT_SIZE.value,
            ),
        ]

        if self.package:
            field_offset_y += KiExportConfigV5.FIELD_OFFSET_INCREMENT.value
            header.append(
                'F2 "{footprint}" {x} {y} {font_size} H I {text_justification} CNN'
                .format(
                    footprint=self.package,
                    x=0,
                    y=self.y_low - field_offset_y,
                    text_justification="C",  # Center align
                    font_size=KiExportConfigV5.FIELD_FONT_SIZE.value,
                )
            )
        if self.datasheet:
            field_offset_y += KiExportConfigV5.FIELD_OFFSET_INCREMENT.value
            header.append(
                'F3 "{datasheet}" {x} {y} {font_size} H I {text_justification} CNN'
                .format(
                    datasheet=self.datasheet,
                    x=0,
                    y=self.y_low - field_offset_y,
                    text_justification="C",  # Center align
                    font_size=KiExportConfigV5.FIELD_FONT_SIZE.value,
                )
            )
        if self.manufacturer:
            header.append(
                'F4 "{manufacturer}" 0 0 0 H I C CNN "Manufacturer"'.format(
                    manufacturer=self.manufacturer,
                )
            )
        if self.lcsc_id:
            header.append(f'F6 "{self.lcsc_id}" 0 0 0 H I C CNN "LCSC Part"')
        if self.jlc_id:
            header.append(f'F7 "{self.jlc_id}" 0 0 0 H I C CNN "JLC Part"')

        header.append("DRAW\n")

        return "\n".join(header)

    def export_v6(self) -> List[str]:
        property_template = textwrap.indent(
            textwrap.dedent(
                """
                (property
                  "{key}"
                  "{value}"
                  (id {id_})
                  (at 0 {pos_y:.2f} 0)
                  (effects (font (size {font_size} {font_size}) {style}) {hide})
                )"""
            ),
            "  ",
        )

        field_offset_y = KiExportConfigV6.FIELD_OFFSET_START.value
        header: List[str] = [
            property_template.format(
                key="Reference",
                value=self.prefix,
                id_=0,
                pos_y=self.y_high + field_offset_y,
                font_size=KiExportConfigV6.PROPERTY_FONT_SIZE.value,
                style="",
                hide="",
            ),
            property_template.format(
                key="Value",
                value=self.name,
                id_=1,
                pos_y=self.y_low - field_offset_y,
                font_size=KiExportConfigV6.PROPERTY_FONT_SIZE.value,
                style="",
                hide="",
            ),
        ]
        if self.package:
            field_offset_y += KiExportConfigV6.FIELD_OFFSET_INCREMENT.value
            header.append(
                property_template.format(
                    key="Footprint",
                    value=self.package,
                    id_=2,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiExportConfigV6.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                )
            )
        if self.datasheet:
            field_offset_y += KiExportConfigV6.FIELD_OFFSET_INCREMENT.value
            header.append(
                property_template.format(
                    key="Datasheet",
                    value=self.datasheet,
                    id_=3,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiExportConfigV6.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                )
            )
        if self.manufacturer:
            field_offset_y += KiExportConfigV6.FIELD_OFFSET_INCREMENT.value
            header.append(
                property_template.format(
                    key="Manufacturer",
                    value=self.manufacturer,
                    id_=4,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiExportConfigV6.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                )
            )
        if self.lcsc_id:
            field_offset_y += KiExportConfigV6.FIELD_OFFSET_INCREMENT.value
            header.append(
                property_template.format(
                    key="LCSC Part",
                    value=self.lcsc_id,
                    id_=5,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiExportConfigV6.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                )
            )
        if self.jlc_id:
            field_offset_y += KiExportConfigV6.FIELD_OFFSET_INCREMENT.value
            header.append(
                property_template.format(
                    key="JLC Part",
                    value=self.jlc_id,
                    id_=6,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiExportConfigV6.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                )
            )

        return header


# ---------------- PIN ----------------
@dataclass
class KiSymbolPin:
    name: str
    number: str
    style: KiPinStyle
    length: float
    type: KiPinType
    orientation: float
    pos_x: Union[int, float]
    pos_y: Union[int, float]

    def export_v5(self) -> str:

        return (
            "X {name} {num} {x} {y} {length:.0f} {orientation} {num_sz} {name_sz}"
            " {unit_num} 1 {pin_type} {pin_style}\n".format(
                name=apply_pin_name_style(
                    pin_name=self.name, kicad_version=KicadVersion.v5
                ),
                num=self.number,
                x=self.pos_x,
                y=self.pos_y,
                length=self.length,
                orientation=ki_pin_orientation_v5_format[f"{self.orientation}"]
                if f"{self.orientation}" in ki_pin_orientation_v5_format
                else ki_pin_orientation_v5_format["0"],
                num_sz=KiExportConfigV5.PIN_NUM_SIZE.value,
                name_sz=KiExportConfigV5.PIN_NAME_SIZE.value,
                unit_num=1,
                pin_type=ki_pin_type_v5_format[self.type],
                pin_style=ki_pin_style_v5_format[self.style],
            )
        )

    def export_v6(self) -> str:
        return """
            (pin {pin_type} {pin_style}
              (at {x:.2f} {y:.2f} {orientation})
              (length {pin_length})
              (name "{pin_name}" (effects (font (size {name_size} {name_size}))))
              (number "{pin_num}" (effects (font (size {num_size} {num_size}))))
            )""".format(
            pin_type=self.type.name[1:]
            if self.type.name.startswith("_")
            else self.type.name,
            pin_style=self.style.name,
            x=self.pos_x,
            y=self.pos_y,
            orientation=(180 + self.orientation) % 360,  # TODO: 360 - ?
            pin_length=self.length,
            # pin_length=KiExportConfigV6.PIN_LENGTH.value,
            pin_name=apply_pin_name_style(
                pin_name=self.name, kicad_version=KicadVersion.v6
            ),
            name_size=KiExportConfigV6.PIN_NAME_SIZE.value,
            pin_num=self.number,
            num_size=KiExportConfigV6.PIN_NUM_SIZE.value,
        )


# ---------------- RECTANGLE ----------------
@dataclass
class KiSymbolRectangle:
    pos_x0: Union[int, float] = 0
    pos_y0: Union[int, float] = 0
    pos_x1: Union[int, float] = 0
    pos_y1: Union[int, float] = 0

    def export_v5(self) -> str:
        return (
            "S {x0:.0f} {y0:.0f} {x1:.0f} {y1:.0f} {unit_num} 1 {line_width} {fill}\n"
            .format(
                x0=self.pos_x0,
                y0=self.pos_y0,
                x1=self.pos_x1,
                y1=self.pos_y1,
                unit_num=1,
                line_width=KiExportConfigV5.DEFAULT_BOX_LINE_WIDTH.value,
                fill=ki_box_fill_v5_format[KiBoxFill.background],
            )
        )

    def export_v6(self) -> str:
        return """
            (rectangle
              (start {x0:.2f} {y0:.2f})
              (end {x1:.2f} {y1:.2f})
              (stroke (width {line_width}) (type default) (color 0 0 0 0))
              (fill (type {fill}))
            )""".format(
            x0=self.pos_x0,
            y0=self.pos_y0,
            x1=self.pos_x1,
            y1=self.pos_y1,
            line_width=KiExportConfigV6.DEFAULT_BOX_LINE_WIDTH.value,
            fill=KiBoxFill.background.name,
        )


# ---------------- POLYGON ----------------
@dataclass
class KiSymbolPolygon:
    points: List[List[float]] = field(default_factory=List[List[float]])
    points_number: int = 0
    is_closed: bool = False

    def export_v5(self) -> str:
        return (
            "P {points_number} {unit_num} 1 {line_width} {coordinate} {fill}\n".format(
                points_number=self.points_number,
                unit_num=1,
                line_width=KiExportConfigV5.DEFAULT_BOX_LINE_WIDTH.value,
                coordinate=" ".join(
                    map(str, list(itertools.chain.from_iterable(self.points)))
                ),
                fill=ki_box_fill_v5_format[KiBoxFill.background]
                if self.is_closed
                else ki_box_fill_v5_format[KiBoxFill.none],
            )
        )

    def export_v6(self) -> str:
        return """
            (polyline
              (pts
                {polyline_path}
              )
              (stroke (width {line_width}) (type default) (color 0 0 0 0))
              (fill (type {fill}))
            )""".format(
            polyline_path=" ".join(
                [f"(xy {pts[0]:.2f} {pts[1]:.2f})" for pts in self.points]
            ),
            line_width=KiExportConfigV6.DEFAULT_BOX_LINE_WIDTH.value,
            fill=KiBoxFill.background.name if self.is_closed else KiBoxFill.none.name,
        )


# ---------------- CIRCLE ----------------
@dataclass
class KiSymbolCircle:
    pos_x: Union[int, float] = 0
    pos_y: Union[int, float] = 0
    radius: Union[int, float] = 0
    background_filling: bool = False

    def export_v5(self) -> str:
        return (
            "C {pos_x:.0f} {pos_y:.0f} {radius:.0f} {unit_num} 1 {line_width} {fill}\n"
            .format(
                pos_x=self.pos_x,
                pos_y=self.pos_y,
                radius=int(self.radius),
                unit_num=1,
                line_width=KiExportConfigV5.DEFAULT_BOX_LINE_WIDTH.value,
                fill=ki_box_fill_v5_format[KiBoxFill.background]
                if self.background_filling
                else ki_box_fill_v5_format[KiBoxFill.none],
            )
        )

    def export_v6(self) -> str:
        return """
            (circle
              (center {pos_x:.2f} {pos_y:.2f})
              (radius {radius:.2f})
              (stroke (width {line_width}) (type default) (color 0 0 0 0))
              (fill (type {fill}))
            )""".format(
            pos_x=self.pos_x,
            pos_y=self.pos_y,
            radius=self.radius,
            line_width=KiExportConfigV6.DEFAULT_BOX_LINE_WIDTH.value,
            fill=KiBoxFill.background.name
            if self.background_filling
            else KiBoxFill.none.name,
        )


# ---------------- ARC ----------------
@dataclass
class KiSymbolArc:
    center_x: float = 0
    center_y: float = 0
    radius: float = 0
    angle_start: float = 0.0
    angle_end: float = 0.0
    start_x: float = 0
    start_y: float = 0
    middle_x: float = 0
    middle_y: float = 0
    end_x: float = 0
    end_y: float = 0

    def export_v5(self) -> str:
        return (
            "A {center_x:.0f} {center_y:.0f} {radius:.0f} {angle_start:.0f}"
            " {angle_end:.0f} {unit_num} 1 {line_width} {fill} {start_x:.0f}"
            " {start_y:.0f} {end_x:.0f} {end_y:.0f}\n".format(
                center_x=self.center_x,
                center_y=self.center_y,
                radius=self.radius,
                angle_start=self.angle_start * 10,
                angle_end=self.angle_end * 10,
                unit_num=1,
                line_width=KiExportConfigV5.DEFAULT_BOX_LINE_WIDTH.value,
                fill=ki_box_fill_v5_format[KiBoxFill.background]
                if self.angle_start == self.angle_end
                else ki_box_fill_v5_format[KiBoxFill.none],
                start_x=self.start_x,
                start_y=self.start_y,
                end_x=self.end_x,
                end_y=self.end_y,
            )
        )

    def export_v6(self) -> str:
        return """
            (arc
              (start {start_x:.2f} {start_y:.2f})
              (mid {middle_x:.2f} {middle_y:.2f})
              (end {end_x:.2f} {end_y:.2f})
              (stroke (width {line_width}) (type default) (color 0 0 0 0))
              (fill (type {fill}))
            )""".format(
            start_x=self.start_x,
            start_y=self.start_y,
            middle_x=self.middle_x,
            middle_y=self.middle_y,
            end_x=self.end_x,
            end_y=self.end_y,
            line_width=KiExportConfigV6.DEFAULT_BOX_LINE_WIDTH.value,
            fill=KiBoxFill.background.name
            if self.angle_start == self.angle_end
            else KiBoxFill.none.name,
        )


# ---------------- BEZIER CURVE ----------------
@dataclass
class KiSymbolBezier:
    points: List[List[float]] = field(default_factory=List[List[float]])
    points_number: int = 0
    is_closed: bool = False

    def export_v5(self) -> str:
        return (
            "B {points_number} {unit_num} 1 {line_width} {coordinate} {fill}\n".format(
                points_number=self.points_number,
                unit_num=1,
                line_width=KiExportConfigV5.DEFAULT_BOX_LINE_WIDTH.value,
                coordinate=" ".join(
                    map(str, list(itertools.chain.from_iterable(self.points)))
                ),
                fill=ki_box_fill_v5_format[KiBoxFill.background]
                if self.is_closed
                else ki_box_fill_v5_format[KiBoxFill.none],
            )
        )

    def export_v6(self) -> str:
        return """
            (gr_curve
              (pts
                {polyline_path}
              )
              (stroke (width {line_width}) (type default) (color 0 0 0 0))
              (fill (type {fill}))
            )""".format(
            polyline_path="".join([f" (xy {pts[0]} {pts[1]})" for pts in self.points]),
            line_width=KiExportConfigV6.DEFAULT_BOX_LINE_WIDTH.value,
            fill=KiBoxFill.background.name if self.is_closed else KiBoxFill.none.name,
        )


# ---------------- SYMBOL ----------------
@dataclass
class KiSymbol:
    info: KiSymbolInfo
    pins: List[KiSymbolPin] = field(default_factory=lambda: [])
    rectangles: List[KiSymbolRectangle] = field(default_factory=lambda: [])
    circles: List[KiSymbolCircle] = field(default_factory=lambda: [])
    arcs: List[KiSymbolArc] = field(default_factory=lambda: [])
    polygons: List[KiSymbolPolygon] = field(default_factory=lambda: [])
    beziers: List[KiSymbolBezier] = field(default_factory=lambda: [])

    def export_handler(self, kicad_version: str):
        # Get y_min and y_max to put component info
        self.info.y_low = min(pin.pos_y for pin in self.pins) if self.pins else 0
        self.info.y_high = max(pin.pos_y for pin in self.pins) if self.pins else 0

        sym_export_data = {}
        for _field in fields(self):
            shapes = getattr(self, _field.name)
            if isinstance(shapes, list):
                sym_export_data.setdefault(_field.name, [])
                for sub_symbol in shapes:
                    sym_export_data[_field.name].append(
                        getattr(sub_symbol, f"export_v{kicad_version}")()
                    )
            else:
                sym_export_data[_field.name] = getattr(
                    shapes, f"export_v{kicad_version}"
                )()
        return sym_export_data

    def export_v5(self):
        sym_export_data = self.export_handler(kicad_version="5")
        sym_info = sym_export_data.pop("info")
        sym_graphic_items = itertools.chain.from_iterable(sym_export_data.values())

        return (
            "#\n#"
            f" {sanitize_fields(self.info.name)}\n#\n{sym_info}{''.join(sym_graphic_items)}ENDDRAW\nENDDEF\n"
        )

    def export_v6(self):
        sym_export_data = self.export_handler(kicad_version="6")
        sym_info = sym_export_data.pop("info")
        sym_pins = sym_export_data.pop("pins")
        sym_graphic_items = itertools.chain.from_iterable(sym_export_data.values())

        return textwrap.indent(
            textwrap.dedent(
                """
            (symbol "{library_id}"
              (in_bom yes)
              (on_board yes)
              {symbol_properties}
              (symbol "{library_id}_0_1"
                {graphic_items}
                {pins}
              )
            )"""
            ),
            "  ",
        ).format(
            library_id=sanitize_fields(self.info.name),
            symbol_properties=textwrap.indent(
                textwrap.dedent("".join(sym_info)), "  " * 2
            ),
            graphic_items=textwrap.indent(
                textwrap.dedent("".join(sym_graphic_items)), "  " * 3
            ),
            pins=textwrap.indent(textwrap.dedent("".join(sym_pins)), "  " * 3),
        )

    def export(self, kicad_version: KicadVersion) -> str:
        component_data = getattr(self, f"export_{kicad_version.name}")()
        return re.sub(r"\n\s*\n", "\n", component_data, re.MULTILINE)
