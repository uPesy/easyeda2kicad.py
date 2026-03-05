# Global imports
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Local imports
from .svg_path_parser import parse_svg_path


# Safe conversion helpers – used by all EasyEDA dataclass __post_init__ methods.
# EasyEDA API returns all field values as strings; these helpers handle the conversion.
def _safe_float(value: str | float | int | bool | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value: str | float | int | bool | None, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))  # float first to handle "1.0" -> 1
    except (ValueError, TypeError):
        return default


def _safe_bool(value: str | float | int | bool | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on", "show")
    try:
        return bool(int(value))
    except (ValueError, TypeError):
        return default


class EasyedaPinType(Enum):
    unspecified = 0
    _input = 1
    output = 2
    bidirectional = 3
    power = 4


# ------------------------- Symbol -------------------------
@dataclass
class EeSymbolBbox:
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.x = _safe_float(self.x, 0.0)
        self.y = _safe_float(self.y, 0.0)
        self.width = _safe_float(self.width, 0.0)
        self.height = _safe_float(self.height, 0.0)


# ---------------- PIN ----------------
@dataclass
class EeSymbolPinSettings:
    is_displayed: bool
    type: EasyedaPinType
    spice_pin_number: str
    pos_x: float
    pos_y: float
    rotation: int
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Convert string values safely
        self.is_displayed = _safe_bool(self.is_displayed, False)
        self.is_locked = _safe_bool(self.is_locked, False)
        self.rotation = _safe_int(self.rotation, 0)
        self.pos_x = _safe_float(self.pos_x, 0.0)
        self.pos_y = _safe_float(self.pos_y, 0.0)
        self.spice_pin_number = (
            str(self.spice_pin_number) if self.spice_pin_number else ""
        )
        if isinstance(self.type, str):
            type_val = _safe_int(self.type, 0)
            self.type = (
                EasyedaPinType(type_val)
                if type_val in EasyedaPinType._value2member_map_
                else EasyedaPinType.unspecified
            )


@dataclass
class EeSymbolPinDot:
    dot_x: float
    dot_y: float

    def __post_init__(self) -> None:
        self.dot_x = _safe_float(self.dot_x, 0.0)
        self.dot_y = _safe_float(self.dot_y, 0.0)


@dataclass
class EeSymbolPinPath:
    path: str
    color: str

    def __post_init__(self) -> None:
        if isinstance(self.path, str):
            self.path = self.path.replace("v", "h")


@dataclass
class EeSymbolPinName:
    is_displayed: bool
    pos_x: float
    pos_y: float
    rotation: int
    text: str
    text_anchor: str
    font: str
    font_size: float

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.pos_x = _safe_float(self.pos_x, 0.0)
        self.pos_y = _safe_float(self.pos_y, 0.0)
        self.rotation = _safe_int(self.rotation, 0)
        self.is_displayed = _safe_bool(self.is_displayed, True)
        if isinstance(self.font_size, str) and "pt" in self.font_size:
            self.font_size = _safe_float(self.font_size.replace("pt", ""), 7.0)
        else:
            self.font_size = _safe_float(self.font_size, 7.0)


@dataclass
class EeSymbolPinDotBis:
    is_displayed: bool
    circle_x: float
    circle_y: float

    def __post_init__(self) -> None:
        self.circle_x = _safe_float(self.circle_x, 0.0)
        self.circle_y = _safe_float(self.circle_y, 0.0)
        self.is_displayed = _safe_bool(self.is_displayed, True)


@dataclass
class EeSymbolPinClock:
    is_displayed: bool
    path: str

    def __post_init__(self) -> None:
        self.is_displayed = _safe_bool(self.is_displayed, True)


@dataclass
class EeSymbolPin:
    settings: EeSymbolPinSettings
    pin_dot: EeSymbolPinDot
    pin_path: EeSymbolPinPath
    name: EeSymbolPinName
    dot: EeSymbolPinDotBis
    clock: EeSymbolPinClock


# ---------------- RECTANGLE ----------------
@dataclass
class EeSymbolRectangle:
    pos_x: float
    pos_y: float
    width: float
    height: float
    stroke_color: str
    stroke_width: str
    stroke_style: str
    fill_color: str
    id: str
    is_locked: bool
    rx: float | None = None
    ry: float | None = None

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.pos_x = _safe_float(self.pos_x, 0.0)
        self.pos_y = _safe_float(self.pos_y, 0.0)
        self.rx = _safe_float(self.rx, 0.0) if self.rx is not None else None
        self.ry = _safe_float(self.ry, 0.0) if self.ry is not None else None
        self.width = _safe_float(self.width, 0.0)
        self.height = _safe_float(self.height, 0.0)
        self.is_locked = _safe_bool(self.is_locked, False)
        # Convert empty strings to None for all string fields
        for field_name in [
            "stroke_color",
            "stroke_width",
            "stroke_style",
            "fill_color",
            "id",
        ]:
            value = getattr(self, field_name)
            if isinstance(value, str) and not value:
                setattr(self, field_name, None)


# ---------------- CIRCLE ----------------
@dataclass
class EeSymbolCircle:
    center_x: float
    center_y: float
    radius: float
    stroke_color: str
    stroke_width: str
    stroke_style: str
    fill_color: bool
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.center_x = _safe_float(self.center_x, 0.0)
        self.center_y = _safe_float(self.center_y, 0.0)
        self.radius = _safe_float(self.radius, 0.0)
        self.is_locked = _safe_bool(self.is_locked, False)
        if isinstance(self.fill_color, str):
            self.fill_color = bool(
                self.fill_color and self.fill_color.lower() != "none"
            )
        else:
            self.fill_color = _safe_bool(self.fill_color, False)


# ---------------- ARC ----------------
@dataclass
class EeSymbolArc:
    path: list[Any]
    helper_dots: str
    stroke_color: str
    stroke_width: str
    stroke_style: str
    fill_color: bool
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all fields
        self.is_locked = _safe_bool(self.is_locked, False)
        if isinstance(self.fill_color, str):
            self.fill_color = bool(
                self.fill_color and self.fill_color.lower() != "none"
            )
        else:
            self.fill_color = _safe_bool(self.fill_color, False)
        if isinstance(self.path, str):
            self.path = parse_svg_path(svg_path=self.path)


@dataclass
class EeSymbolEllipse:
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float
    stroke_color: str
    stroke_width: str
    stroke_style: str
    fill_color: bool
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.center_x = _safe_float(self.center_x, 0.0)
        self.center_y = _safe_float(self.center_y, 0.0)
        self.radius_x = _safe_float(self.radius_x, 0.0)
        self.radius_y = _safe_float(self.radius_y, 0.0)
        self.is_locked = _safe_bool(self.is_locked, False)
        if isinstance(self.fill_color, str):
            self.fill_color = bool(
                self.fill_color and self.fill_color.lower() != "none"
            )
        else:
            self.fill_color = _safe_bool(self.fill_color, False)


# ---------------- POLYLINE ----------------
@dataclass
class EeSymbolPolyline:
    points: str
    stroke_color: str
    stroke_width: str
    stroke_style: str
    fill_color: bool
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all fields
        self.is_locked = _safe_bool(self.is_locked, False)
        if isinstance(self.fill_color, str):
            self.fill_color = bool(
                self.fill_color and self.fill_color.lower() != "none"
            )
        else:
            self.fill_color = _safe_bool(self.fill_color, False)


# ---------------- POLYGON ----------------
@dataclass
class EeSymbolPolygon(EeSymbolPolyline):
    pass


# ---------------- PATH ----------------
# Known limitation: only M/L/Z commands are converted (as polygon segments).
# Curve commands (C/Q/A) are skipped; paths are approximated as straight-line polygons.
# Full SVG path spec: https://www.w3.org/TR/SVG11/paths.html#PathElement
@dataclass
class EeSymbolPath:
    paths: str
    stroke_color: str
    stroke_width: str
    stroke_style: str
    fill_color: bool
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all fields
        self.is_locked = _safe_bool(self.is_locked, False)
        if isinstance(self.fill_color, str):
            self.fill_color = bool(
                self.fill_color and self.fill_color.lower() != "none"
            )
        else:
            self.fill_color = _safe_bool(self.fill_color, False)


# ---------------- SYMBOL ----------------
@dataclass
class EeSymbolInfo:
    name: str = ""
    prefix: str = ""
    package: str = ""
    manufacturer: str = ""
    datasheet: str = ""
    lcsc_id: str = ""
    mpn: str = ""
    keywords: str = ""
    description: str = ""


@dataclass
class EeSymbol:
    info: EeSymbolInfo
    bbox: EeSymbolBbox
    pins: list[EeSymbolPin] = field(default_factory=list)
    rectangles: list[EeSymbolRectangle] = field(default_factory=list)
    circles: list[EeSymbolCircle] = field(default_factory=list)
    arcs: list[EeSymbolArc] = field(default_factory=list)
    ellipses: list[EeSymbolEllipse] = field(default_factory=list)
    polylines: list[EeSymbolPolyline] = field(default_factory=list)
    polygons: list[EeSymbolPolygon] = field(default_factory=list)
    paths: list[EeSymbolPath] = field(default_factory=list)
    # Sub-units of a multi-unit symbol (e.g. op-amp body + power pins as separate units)
    sub_symbols: list["EeSymbol"] = field(default_factory=list)


# ------------------------- Footprint -------------------------


def convert_to_mm(dim: float) -> float:
    return float(dim) * 10 * 0.0254


@dataclass
class EeFootprintBbox:
    x: float
    y: float

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.x = _safe_float(self.x, 0.0)
        self.y = _safe_float(self.y, 0.0)

    def convert_to_mm(self) -> None:
        self.x = convert_to_mm(self.x)
        self.y = convert_to_mm(self.y)


@dataclass
class EeFootprintPad:
    shape: str
    center_x: float
    center_y: float
    width: float
    height: float
    layer_id: int
    net: str
    number: str
    hole_radius: float
    points: str
    rotation: float
    id: str
    hole_length: float
    hole_point: str
    is_plated: bool
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.center_x = _safe_float(self.center_x, 0.0)
        self.center_y = _safe_float(self.center_y, 0.0)
        self.width = _safe_float(self.width, 0.0)
        self.height = _safe_float(self.height, 0.0)
        self.hole_radius = _safe_float(self.hole_radius, 0.0)
        self.rotation = _safe_float(self.rotation, 0.0)
        self.hole_length = _safe_float(self.hole_length, 0.0)
        self.layer_id = _safe_int(self.layer_id, 0)
        self.is_locked = _safe_bool(self.is_locked, False)
        self.is_plated = _safe_bool(self.is_plated, True)

    def convert_to_mm(self) -> None:
        self.center_x = convert_to_mm(self.center_x)
        self.center_y = convert_to_mm(self.center_y)
        self.width = convert_to_mm(self.width)
        self.height = convert_to_mm(self.height)
        self.hole_radius = convert_to_mm(self.hole_radius)
        self.hole_length = convert_to_mm(self.hole_length)


@dataclass
class EeFootprintTrack:
    stroke_width: float
    layer_id: int
    net: str
    points: str
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.stroke_width = _safe_float(self.stroke_width, 0.0)
        self.layer_id = _safe_int(self.layer_id, 0)
        self.is_locked = _safe_bool(self.is_locked, False)

    def convert_to_mm(self) -> None:
        self.stroke_width = convert_to_mm(self.stroke_width)


@dataclass
class EeFootprintHole:
    center_x: float
    center_y: float
    radius: float
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.center_x = _safe_float(self.center_x, 0.0)
        self.center_y = _safe_float(self.center_y, 0.0)
        self.radius = _safe_float(self.radius, 0.0)
        self.is_locked = _safe_bool(self.is_locked, False)

    def convert_to_mm(self) -> None:
        self.center_x = convert_to_mm(self.center_x)
        self.center_y = convert_to_mm(self.center_y)
        self.radius = convert_to_mm(self.radius)


@dataclass
class EeFootprintVia:
    center_x: float
    center_y: float
    diameter: float
    net: str
    radius: float
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.center_x = _safe_float(self.center_x, 0.0)
        self.center_y = _safe_float(self.center_y, 0.0)
        self.diameter = _safe_float(self.diameter, 0.0)
        self.radius = _safe_float(self.radius, 0.0)
        self.is_locked = _safe_bool(self.is_locked, False)

    def convert_to_mm(self) -> None:
        self.center_x = convert_to_mm(self.center_x)
        self.center_y = convert_to_mm(self.center_y)
        self.radius = convert_to_mm(self.radius)
        self.diameter = convert_to_mm(self.diameter)


@dataclass
class EeFootprintCircle:
    cx: float
    cy: float
    radius: float
    stroke_width: float
    layer_id: int
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        self.cx = _safe_float(self.cx, 0.0)
        self.cy = _safe_float(self.cy, 0.0)
        self.radius = _safe_float(self.radius, 0.0)
        self.stroke_width = _safe_float(self.stroke_width, 0.0)
        self.layer_id = _safe_int(self.layer_id, 0)
        self.is_locked = _safe_bool(self.is_locked, False)

    def convert_to_mm(self) -> None:
        self.cx = convert_to_mm(self.cx)
        self.cy = convert_to_mm(self.cy)
        self.radius = convert_to_mm(self.radius)
        self.stroke_width = convert_to_mm(self.stroke_width)


@dataclass
class EeFootprintRectangle:
    x: float
    y: float
    width: float
    height: float
    stroke_width: float
    id: str
    layer_id: int
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.x = _safe_float(self.x, 0.0)
        self.y = _safe_float(self.y, 0.0)
        self.width = _safe_float(self.width, 0.0)
        self.height = _safe_float(self.height, 0.0)
        self.stroke_width = _safe_float(self.stroke_width, 0.0)
        self.layer_id = _safe_int(self.layer_id, 0)
        self.is_locked = _safe_bool(self.is_locked, False)

    def convert_to_mm(self) -> None:
        self.x = convert_to_mm(self.x)
        self.y = convert_to_mm(self.y)
        self.width = convert_to_mm(self.width)
        self.height = convert_to_mm(self.height)
        self.stroke_width = convert_to_mm(self.stroke_width)


@dataclass
class EeFootprintArc:
    stroke_width: float
    layer_id: int
    net: str
    path: str
    helper_dots: str
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        self.stroke_width = _safe_float(self.stroke_width, 0.0)
        self.layer_id = _safe_int(self.layer_id, 0)
        self.is_locked = _safe_bool(self.is_locked, False)

    def convert_to_mm(self) -> None:
        self.stroke_width = convert_to_mm(self.stroke_width)


@dataclass
class EeFootprintText:
    type: str
    center_x: float
    center_y: float
    stroke_width: float
    rotation: int
    mirror: str
    layer_id: int
    net: str
    font_size: float
    text: str
    text_path: str
    is_displayed: bool
    id: str
    is_locked: bool

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.center_x = _safe_float(self.center_x, 0.0)
        self.center_y = _safe_float(self.center_y, 0.0)
        self.stroke_width = _safe_float(self.stroke_width, 0.0)
        self.rotation = _safe_int(self.rotation, 0)
        self.font_size = _safe_float(self.font_size, 7.0)
        self.layer_id = _safe_int(self.layer_id, 0)
        self.is_displayed = _safe_bool(self.is_displayed, True)
        self.is_locked = _safe_bool(self.is_locked, False)

    def convert_to_mm(self) -> None:
        self.center_x = convert_to_mm(self.center_x)
        self.center_y = convert_to_mm(self.center_y)
        self.stroke_width = convert_to_mm(self.stroke_width)
        self.font_size = convert_to_mm(self.font_size)


# ---------------- FOOTPRINT ----------------


@dataclass
class EeFootprintInfo:
    name: str
    fp_type: str
    model_3d_name: str
    lcsc_id: str = ""
    manufacturer: str = ""
    mpn: str = ""


# ------------------------- 3D MODEL -------------------------
@dataclass
class Ee3dModelBase:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __post_init__(self) -> None:
        # Safe conversions for all numeric fields
        self.x = _safe_float(self.x, 0.0)
        self.y = _safe_float(self.y, 0.0)
        self.z = _safe_float(self.z, 0.0)

    def convert_to_mm(self) -> None:
        self.x = convert_to_mm(self.x)
        self.y = convert_to_mm(self.y)
        self.z = convert_to_mm(self.z)


@dataclass
class Ee3dModel:
    name: str
    uuid: str
    translation: Ee3dModelBase
    rotation: Ee3dModelBase
    raw_obj: str | None = None
    step: bytes | None = None

    def convert_to_mm(self) -> None:
        self.translation.convert_to_mm()


@dataclass
class EeFootprint:
    info: EeFootprintInfo
    bbox: EeFootprintBbox
    model_3d: Ee3dModel | None
    pads: list[EeFootprintPad] = field(default_factory=list)
    tracks: list[EeFootprintTrack] = field(default_factory=list)
    holes: list[EeFootprintHole] = field(default_factory=list)
    vias: list[EeFootprintVia] = field(default_factory=list)
    circles: list[EeFootprintCircle] = field(default_factory=list)
    arcs: list[EeFootprintArc] = field(default_factory=list)
    rectangles: list[EeFootprintRectangle] = field(default_factory=list)
    texts: list[EeFootprintText] = field(default_factory=list)
