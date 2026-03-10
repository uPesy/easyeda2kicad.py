from __future__ import annotations

# Global imports
import re
import textwrap
from dataclasses import dataclass, field, fields
from enum import Enum, auto


class KicadVersion(Enum):
    # v6 covers KiCad 6 through current (7/8/9/10+).
    # The .kicad_sym S-Expression format has been stable since KiCad 6.0.
    # Future format versions (v7, v8, ...) can be added here when KiCad
    # introduces breaking changes to the symbol file format.
    v6 = auto()


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


def sanitize_fields(name: str) -> str:
    return name.replace(" ", "").replace("/", "_").replace(":", "_")


def apply_text_style(text: str) -> str:
    if text.endswith("#"):
        text = f"~{{{text[:-1]}}}"
    return text


def apply_pin_name_style(pin_name: str) -> str:
    return "/".join(apply_text_style(text=txt) for txt in pin_name.split("/"))


# ---------------- INFO HEADER ----------------
@dataclass
class KiSymbolInfo:
    name: str
    prefix: str
    package: str
    manufacturer: str
    datasheet: str
    lcsc_id: str
    mpn: str = ""
    keywords: str = ""
    description: str = ""
    y_low: int | float = 0
    y_high: int | float = 0

    def export_v6(self) -> list[str]:
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
        header: list[str] = [
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
        if self.mpn:
            field_offset_y += KiExportConfigV6.FIELD_OFFSET_INCREMENT.value
            header.append(
                property_template.format(
                    key="MPN",
                    value=self.mpn,
                    id_=5,
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
                    id_=6,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiExportConfigV6.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                )
            )
        if self.keywords:
            field_offset_y += KiExportConfigV6.FIELD_OFFSET_INCREMENT.value
            header.append(
                property_template.format(
                    key="ki_keywords",
                    value=self.keywords,
                    id_=8,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiExportConfigV6.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                )
            )
        if self.description:
            field_offset_y += KiExportConfigV6.FIELD_OFFSET_INCREMENT.value
            header.append(
                property_template.format(
                    key="ki_description",
                    value=self.description,
                    id_=9,
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
    pos_x: int | float
    pos_y: int | float

    def export_v6(self) -> str:
        return """
            (pin {pin_type} {pin_style}
              (at {x:.2f} {y:.2f} {orientation})
              (length {pin_length})
              (name "{pin_name}" (effects (font (size {name_size} {name_size}))))
              (number "{pin_num}" (effects (font (size {num_size} {num_size}))))
            )""".format(
            pin_type=(
                self.type.name[1:] if self.type.name.startswith("_") else self.type.name
            ),
            pin_style=self.style.name,
            x=self.pos_x,
            y=self.pos_y,
            # KiCad pin orientation is offset by 180° from EasyEDA's convention
            orientation=(180 + self.orientation) % 360,
            pin_length=self.length,
            pin_name=apply_pin_name_style(pin_name=self.name),
            name_size=KiExportConfigV6.PIN_NAME_SIZE.value,
            pin_num=self.number,
            num_size=KiExportConfigV6.PIN_NUM_SIZE.value,
        )


# ---------------- RECTANGLE ----------------
@dataclass
class KiSymbolRectangle:
    pos_x0: int | float = 0
    pos_y0: int | float = 0
    pos_x1: int | float = 0
    pos_y1: int | float = 0

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
    points: list[list[float]] = field(default_factory=list)
    points_number: int = 0
    is_closed: bool = False

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
    pos_x: int | float = 0
    pos_y: int | float = 0
    radius: int | float = 0
    background_filling: bool = False

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
            fill=(
                KiBoxFill.background.name
                if self.background_filling
                else KiBoxFill.none.name
            ),
        )


# ---------------- ARC ----------------
@dataclass
class KiSymbolArc:
    radius: float = 0
    angle_start: float = 0.0
    angle_end: float = 0.0
    start_x: float = 0
    start_y: float = 0
    middle_x: float = 0
    middle_y: float = 0
    end_x: float = 0
    end_y: float = 0

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
            fill=(
                KiBoxFill.background.name
                if self.angle_start == self.angle_end
                else KiBoxFill.none.name
            ),
        )


# ---------------- BEZIER CURVE ----------------
@dataclass
class KiSymbolBezier:
    points: list[list[float]] = field(default_factory=list)
    points_number: int = 0
    is_closed: bool = False

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


# ---------------- TEXT ----------------
@dataclass
class KiSymbolText:
    # Represents a free text label from EasyEDA (T~ command).
    #
    # (text ...) is a valid graphic primitive in KiCad symbol libraries from KiCad 6+
    # (file format >= 20220102). It is documented in the official KiCad symbol library
    # file format spec as "graphical text in a symbol definition".
    #
    # NOTE: Older KiCad versions or libraries with an older format version may silently
    # discard (text ...) blocks when loading/saving. If text disappears after a
    # round-trip, check the (version ...) header in the .kicad_sym file — it must
    # be >= 20220102 for text primitives to be preserved.
    text: str = ""
    pos_x: float = 0.0
    pos_y: float = 0.0
    rotation: float = 0.0
    font_size: float = 1.27  # mm

    def export_v6(self) -> str:
        return """
            (text "{text}"
              (at {pos_x:.2f} {pos_y:.2f} {rotation:.0f})
              (effects (font (size {font_size:.2f} {font_size:.2f})))
            )""".format(
            text=self.text.replace('"', '\\"'),
            pos_x=self.pos_x,
            pos_y=self.pos_y,
            rotation=self.rotation,
            font_size=self.font_size,
        )


# ---------------- SYMBOL ----------------
@dataclass
class KiSymbol:
    info: KiSymbolInfo
    pins: list[KiSymbolPin] = field(default_factory=lambda: [])
    rectangles: list[KiSymbolRectangle] = field(default_factory=lambda: [])
    circles: list[KiSymbolCircle] = field(default_factory=lambda: [])
    arcs: list[KiSymbolArc] = field(default_factory=lambda: [])
    polygons: list[KiSymbolPolygon] = field(default_factory=lambda: [])
    beziers: list[KiSymbolBezier] = field(default_factory=lambda: [])
    texts: list[KiSymbolText] = field(default_factory=lambda: [])

    def export_handler(self, kicad_version: KicadVersion) -> dict[str, str | list[str]]:
        method_name = f"export_{kicad_version.name}"  # e.g. "export_v6"

        # Get y_min and y_max to put component info
        self.info.y_low = min(pin.pos_y for pin in self.pins) if self.pins else 0
        self.info.y_high = max(pin.pos_y for pin in self.pins) if self.pins else 0

        sym_export_data: dict[str, str | list[str]] = {}
        for _field in fields(self):
            shapes = getattr(self, _field.name)
            if isinstance(shapes, list):
                values: list[str] = []
                for sub_symbol in shapes:
                    method = getattr(sub_symbol, method_name, None)
                    if method is None:
                        raise ValueError(
                            f"{type(sub_symbol).__name__} has no {method_name}()"
                        )
                    values.append(method())
                sym_export_data[_field.name] = values
            else:
                method = getattr(shapes, method_name, None)
                if method is None:
                    raise ValueError(f"{type(shapes).__name__} has no {method_name}()")
                sym_export_data[_field.name] = method()
        return sym_export_data

    def export_v6(self) -> str:
        sym_export_data = self.export_handler(kicad_version=KicadVersion.v6)
        sym_info = sym_export_data.pop("info")
        sym_pins = sym_export_data.pop("pins")
        sym_graphic_items = (v for values in sym_export_data.values() for v in values)

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
