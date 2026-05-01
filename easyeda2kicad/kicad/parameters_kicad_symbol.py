from __future__ import annotations

# Global imports
import itertools
import re
from typing import Union
import textwrap
from dataclasses import dataclass, field, fields
from enum import Enum, auto


# .kicad_sym file format versions — each constant marks a breaking schema change.
# KiCad 6.0   baseline: arc start/mid/end, property id field
KICAD_SYM_VERSION_20211014 = 20211014
# KiCad 7.0   property id field removed, unit_name added
KICAD_SYM_VERSION_20220914 = 20220914
# KiCad 7.0.x ki_description renamed to Description
KICAD_SYM_VERSION_20230620 = 20230620
# KiCad 8.0   generator_version added to header
KICAD_SYM_VERSION_20231120 = 20231120
# KiCad 9.0   exclude_from_sim property flag added
KICAD_SYM_VERSION_20241209 = 20241209
# KiCad 10.0  hide token becomes (hide yes); corner_radius on rectangle; stacked pins
KICAD_SYM_VERSION_20251024 = 20251024

KICAD_SYM_VERSIONS_SORTED = [
    KICAD_SYM_VERSION_20211014,
    KICAD_SYM_VERSION_20220914,
    KICAD_SYM_VERSION_20230620,
    KICAD_SYM_VERSION_20231120,
    KICAD_SYM_VERSION_20241209,
    KICAD_SYM_VERSION_20251024,
]


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


# Config
# Dimensions are in mm
class KiSymbolDefaults(Enum):
    PIN_LENGTH = 2.54
    PIN_SPACING = 2.54
    PIN_NUM_SIZE = 1.27
    PIN_NAME_SIZE = 1.27
    DEFAULT_BOX_LINE_WIDTH = 0
    PROPERTY_FONT_SIZE = 1.27
    FIELD_OFFSET_START = 5.08
    FIELD_OFFSET_INCREMENT = 2.54


# Characters illegal in KiCad LIB_IDs (lib_id.cpp: isLegalChar).
_ILLEGAL_SYMBOL_ID_RE = re.compile(r'[/\\:<>"\t\n\r]')


def sanitize_fields(name: str) -> str:
    return _ILLEGAL_SYMBOL_ID_RE.sub("_", name).replace(" ", "")


def apply_text_style(text: str) -> str:
    if text.endswith("#"):
        text = f"~{{{text[:-1]}}}"
    return text


def apply_pin_name_style(pin_name: str) -> str:
    return "/".join(apply_text_style(text=txt) for txt in pin_name.split("/"))


def _make_property(
    key: str,
    value: str,
    id_: int,
    pos_y: float,
    font_size: float,
    style: str,
    hide: str,
    version: int,
) -> str:
    """Render a KiCad symbol property S-expression.

    Schema changes by version:
    - <20220914:  (id N) field present inside property block
    - >=20220914: (id N) removed (KiCad 7.0)
    - >=20251024: hide moves out of (effects ...) and becomes a standalone
                  (hide yes) token directly inside the property block (KiCad 10.0)
    """
    if version >= KICAD_SYM_VERSION_20220914:
        id_part = ""
    else:
        id_part = f"\n          (id {id_})"

    if version >= KICAD_SYM_VERSION_20251024:
        hide_token = "\n          (hide yes)" if hide else ""
        effects = f"(effects (font (size {font_size} {font_size}) {style}))"
    else:
        hide_token = ""
        effects = f"(effects (font (size {font_size} {font_size}) {style}) {hide})"

    return textwrap.indent(
        textwrap.dedent(f"""
        (property
          "{key}"
          "{value}"{id_part}
          (at 0 {pos_y:.2f} 0){hide_token}
          {effects}
        )"""),
        "  ",
    )


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
    custom_fields: dict[str, str] = field(default_factory=dict)
    y_low: Union[int, float] = 0
    y_high: Union[int, float] = 0

    def export(self, version: int = KICAD_SYM_VERSION_20211014) -> list[str]:
        description_key = (
            "Description" if version >= KICAD_SYM_VERSION_20230620 else "ki_description"
        )

        field_offset_y = KiSymbolDefaults.FIELD_OFFSET_START.value
        header: list[str] = [
            _make_property(
                key="Reference",
                value=self.prefix,
                id_=0,
                pos_y=self.y_high + field_offset_y,
                font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                style="",
                hide="",
                version=version,
            ),
            _make_property(
                key="Value",
                value=self.name,
                id_=1,
                pos_y=self.y_low - field_offset_y,
                font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                style="",
                hide="",
                version=version,
            ),
        ]
        if self.package:
            field_offset_y += KiSymbolDefaults.FIELD_OFFSET_INCREMENT.value
            header.append(
                _make_property(
                    key="Footprint",
                    value=self.package,
                    id_=2,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                    version=version,
                )
            )
        if self.datasheet:
            field_offset_y += KiSymbolDefaults.FIELD_OFFSET_INCREMENT.value
            header.append(
                _make_property(
                    key="Datasheet",
                    value=self.datasheet,
                    id_=3,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                    version=version,
                )
            )
        if self.manufacturer:
            field_offset_y += KiSymbolDefaults.FIELD_OFFSET_INCREMENT.value
            header.append(
                _make_property(
                    key="Manufacturer",
                    value=self.manufacturer,
                    id_=4,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                    version=version,
                )
            )
        if self.mpn:
            field_offset_y += KiSymbolDefaults.FIELD_OFFSET_INCREMENT.value
            header.append(
                _make_property(
                    key="MPN",
                    value=self.mpn,
                    id_=5,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                    version=version,
                )
            )
        if self.lcsc_id:
            field_offset_y += KiSymbolDefaults.FIELD_OFFSET_INCREMENT.value
            header.append(
                _make_property(
                    key="LCSC Part",
                    value=self.lcsc_id,
                    id_=6,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                    version=version,
                )
            )
        if self.keywords:
            field_offset_y += KiSymbolDefaults.FIELD_OFFSET_INCREMENT.value
            header.append(
                _make_property(
                    key="ki_keywords",
                    value=self.keywords,
                    id_=8,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                    version=version,
                )
            )
        if self.description:
            field_offset_y += KiSymbolDefaults.FIELD_OFFSET_INCREMENT.value
            header.append(
                _make_property(
                    key=description_key,
                    value=self.description,
                    id_=9,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                    version=version,
                )
            )

        # Built-in property IDs 0–9 are reserved; custom fields start at 10
        property_id = 10
        for key, value in self.custom_fields.items():
            field_offset_y += KiSymbolDefaults.FIELD_OFFSET_INCREMENT.value
            header.append(
                _make_property(
                    key=key,
                    value=value,
                    id_=property_id,
                    pos_y=self.y_low - field_offset_y,
                    font_size=KiSymbolDefaults.PROPERTY_FONT_SIZE.value,
                    style="",
                    hide="hide",
                    version=version,
                )
            )
            property_id += 1

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

    def export(self, version: int = KICAD_SYM_VERSION_20211014) -> str:
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
            name_size=KiSymbolDefaults.PIN_NAME_SIZE.value,
            pin_num=self.number,
            num_size=KiSymbolDefaults.PIN_NUM_SIZE.value,
        )


# ---------------- RECTANGLE ----------------
@dataclass
class KiSymbolRectangle:
    pos_x0: Union[int, float] = 0
    pos_y0: Union[int, float] = 0
    pos_x1: Union[int, float] = 0
    pos_y1: Union[int, float] = 0

    def export(self, version: int = KICAD_SYM_VERSION_20211014) -> str:
        return """
            (rectangle
              (start {x0:.2f} {y0:.2f})
              (end {x1:.2f} {y1:.2f})
              (stroke (width {line_width}) (type default))
              (fill (type {fill}))
            )""".format(
            x0=self.pos_x0,
            y0=self.pos_y0,
            x1=self.pos_x1,
            y1=self.pos_y1,
            line_width=KiSymbolDefaults.DEFAULT_BOX_LINE_WIDTH.value,
            fill=KiBoxFill.background.name,
        )


# ---------------- POLYGON ----------------
@dataclass
class KiSymbolPolygon:
    points: list[list[float]] = field(default_factory=list)
    points_number: int = 0
    is_closed: bool = False

    def export(self, version: int = KICAD_SYM_VERSION_20211014) -> str:
        return """
            (polyline
              (pts
                {polyline_path}
              )
              (stroke (width {line_width}) (type default))
              (fill (type {fill}))
            )""".format(
            polyline_path=" ".join(
                [f"(xy {pts[0]:.2f} {pts[1]:.2f})" for pts in self.points]
            ),
            line_width=KiSymbolDefaults.DEFAULT_BOX_LINE_WIDTH.value,
            fill=KiBoxFill.background.name if self.is_closed else KiBoxFill.none.name,
        )


# ---------------- CIRCLE ----------------
@dataclass
class KiSymbolCircle:
    pos_x: Union[int, float] = 0
    pos_y: Union[int, float] = 0
    radius: Union[int, float] = 0
    background_filling: bool = False

    def export(self, version: int = KICAD_SYM_VERSION_20211014) -> str:
        return """
            (circle
              (center {pos_x:.2f} {pos_y:.2f})
              (radius {radius:.2f})
              (stroke (width {line_width}) (type default))
              (fill (type {fill}))
            )""".format(
            pos_x=self.pos_x,
            pos_y=self.pos_y,
            radius=self.radius,
            line_width=KiSymbolDefaults.DEFAULT_BOX_LINE_WIDTH.value,
            fill=(
                KiBoxFill.background.name
                if self.background_filling
                else KiBoxFill.none.name
            ),
        )


# ---------------- ARC ----------------
@dataclass
class KiSymbolArc:
    angle_start: float = 0.0
    angle_end: float = 0.0
    start_x: float = 0
    start_y: float = 0
    middle_x: float = 0
    middle_y: float = 0
    end_x: float = 0
    end_y: float = 0

    def export(self, version: int = KICAD_SYM_VERSION_20211014) -> str:
        return """
            (arc
              (start {start_x:.2f} {start_y:.2f})
              (mid {middle_x:.2f} {middle_y:.2f})
              (end {end_x:.2f} {end_y:.2f})
              (stroke (width {line_width}) (type default))
              (fill (type {fill}))
            )""".format(
            start_x=self.start_x,
            start_y=self.start_y,
            middle_x=self.middle_x,
            middle_y=self.middle_y,
            end_x=self.end_x,
            end_y=self.end_y,
            line_width=KiSymbolDefaults.DEFAULT_BOX_LINE_WIDTH.value,
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

    def export(self, version: int = KICAD_SYM_VERSION_20211014) -> str:
        fmt_pts = " ".join(f"(xy {p[0]:.2f} {p[1]:.2f})" for p in self.points)
        fill = KiBoxFill.background.name if self.is_closed else KiBoxFill.none.name
        lw = KiSymbolDefaults.DEFAULT_BOX_LINE_WIDTH.value
        if version >= KICAD_SYM_VERSION_20220914:
            return f"""
            (bezier
              (pts {fmt_pts})
              (stroke (width {lw}) (type default))
              (fill (type {fill}))
            )"""
        # Format < 20220914 has no (bezier ...) — emit straight line start→end
        start = self.points[0] if self.points else [0, 0]
        end = self.points[-1] if len(self.points) > 1 else start
        return f"""
            (polyline
              (pts (xy {start[0]:.2f} {start[1]:.2f}) (xy {end[0]:.2f} {end[1]:.2f}))
              (stroke (width {lw}) (type default))
              (fill (type {fill}))
            )"""


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

    def export(self, version: int = KICAD_SYM_VERSION_20211014) -> str:
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

    def export_handler(
        self, version: int = KICAD_SYM_VERSION_20211014
    ) -> dict[str, str | list[str]]:
        self.info.y_low = min(pin.pos_y for pin in self.pins) if self.pins else 0
        self.info.y_high = max(pin.pos_y for pin in self.pins) if self.pins else 0

        sym_export_data: dict[str, str | list[str]] = {}
        for _field in fields(self):
            shapes = getattr(self, _field.name)
            if isinstance(shapes, list):
                values: list[str] = []
                for sub_symbol in shapes:
                    export_method = getattr(sub_symbol, "export", None)
                    if export_method is None:
                        raise ValueError(f"{type(sub_symbol).__name__} has no export()")
                    values.append(export_method(version=version))
                sym_export_data[_field.name] = values
            else:
                export_method = getattr(shapes, "export", None)
                if export_method is None:
                    raise ValueError(f"{type(shapes).__name__} has no export()")
                sym_export_data[_field.name] = export_method(version=version)
        return sym_export_data

    def export(self, version: int = KICAD_SYM_VERSION_20211014) -> str:
        sym_export_data = self.export_handler(version=version)
        sym_info = sym_export_data.pop("info")
        sym_pins = sym_export_data.pop("pins")
        sym_graphic_items = itertools.chain.from_iterable(sym_export_data.values())

        if version >= KICAD_SYM_VERSION_20241209:
            sym_attrs = "(exclude_from_sim no)\n    (in_bom yes)\n    (on_board yes)"
        else:
            sym_attrs = "(in_bom yes)\n    (on_board yes)"

        component_data = textwrap.indent(
            textwrap.dedent(
                """
            (symbol "{library_id}"
              {sym_attrs}
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
            sym_attrs=sym_attrs,
            symbol_properties=textwrap.indent(
                textwrap.dedent("".join(sym_info)), "  " * 2
            ),
            graphic_items=textwrap.indent(
                textwrap.dedent("".join(sym_graphic_items)), "  " * 3
            ),
            pins=textwrap.indent(textwrap.dedent("".join(sym_pins)), "  " * 3),
        )
        return re.sub(r"\n\s*\n", "\n", component_data, flags=re.MULTILINE)
