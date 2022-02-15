# Global imports
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union

from pydantic import BaseModel, validator


class easyeda_pin_type(Enum):
    unspecified = 0
    input = 1
    output = 2
    bidirectional = 3
    power = 4


# Symbol


class ee_symbol_bbox(BaseModel):
    x: float
    y: float


# ---------------- PIN ----------------
class ee_symbol_pin_settings(BaseModel):
    is_displayed: bool
    type: str
    spice_pin_number: str
    pos_x: float
    pos_y: float
    rotation: int
    id: str
    is_locked: bool

    @validator("is_displayed", pre=True)
    def parse_display_field(cls, v):
        return True if v == "show" else v

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked

    @validator("rotation", pre=True)
    def empty_str_rotation(cls, rotation):
        return 0.0 if rotation == "" else rotation


class ee_symbol_pin_dot(BaseModel):
    dot_x: float
    dot_y: float


@dataclass
class ee_symbol_pin_path:
    path: str
    color: str


class ee_symbol_pin_name(BaseModel):
    is_displayed: bool
    pos_x: float
    pos_y: float
    rotation: int
    text: str
    text_anchor: str
    font: str
    font_size: float

    @validator("font_size", pre=True)
    def empty_str_font(cls, font_size):
        if isinstance(font_size, str) and "pt" in font_size:
            return float(font_size.replace("pt", ""))
        return 7.0 if font_size == "" else font_size

    @validator("is_displayed", pre=True)
    def parse_display_field(cls, v):
        return True if v == "show" else v

    @validator("rotation", pre=True)
    def empty_str_rotation(cls, rotation):
        return 0.0 if rotation == "" else rotation


class ee_symbol_pin_dot_bis(BaseModel):
    is_displayed: bool
    circle_x: float
    circle_y: float

    @validator("is_displayed", pre=True)
    def parse_display_field(cls, v):
        return True if v == "show" else v


class ee_symbol_pin_clock(BaseModel):
    is_displayed: bool
    path: str

    @validator("is_displayed", pre=True)
    def parse_display_field(cls, v):
        return True if v == "show" else v


@dataclass
class ee_symbol_pin:
    settings: ee_symbol_pin_settings
    pin_dot: ee_symbol_pin_dot
    pin_path: ee_symbol_pin_path
    name: ee_symbol_pin_name
    dot: ee_symbol_pin_dot_bis
    clock: ee_symbol_pin_clock


# ---------------- RECTANGLE ----------------
class ee_symbol_rectangle(BaseModel):
    pos_x: float
    pos_y: float
    rx: Union[float, None]
    ry: Union[float, None]
    width: float
    height: float
    stroke_color: str
    stroke_width: str
    stroke_style: str
    fill_color: str
    id: str
    is_locked: bool

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        return None if v == "" else v


# ---------------- POLYLINE ----------------
class ee_symbol_polyline(BaseModel):
    points: str
    stroke_color: str
    stroke_width: str
    stroke_style: str
    fill_color: str
    id: str
    is_locked: bool

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked


# ---------------- POLYGON ----------------
class ee_symbol_polygon(ee_symbol_polyline):
    ...


# ---------------- PATH ----------------
# TODO : ee_symbol_path.paths should be a SVG PATH https://www.w3.org/TR/SVG11/paths.html#PathElement
# TODO : small svg parser and then convert to kicad
# TODO: support bezier curve, currently paths are seen as polygone
class ee_symbol_path(BaseModel):
    paths: str
    stroke_color: str
    stroke_width: str
    stroke_style: str
    fill_color: str
    id: str
    is_locked: bool

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked

    # @validator("paths", pre=True)
    # def clean_svg_path(cls, paths:str):
    #     return paths.replace("M", "").replace("C","")


# ---------------- SYMBOL ----------------
@dataclass
class ee_symbol_info:
    name: str = ""
    prefix: str = ""
    package: str = ""
    manufacturer: str = ""
    datasheet: str = ""
    lcsc_id: str = ""
    jlc_id: str = ""


@dataclass
class ee_symbol:
    info: ee_symbol_info
    bbox: ee_symbol_bbox
    pins: List[ee_symbol_pin] = field(default_factory=list)
    rectangles: List[ee_symbol_rectangle] = field(default_factory=list)
    polylines: List[ee_symbol_polyline] = field(default_factory=list)
    polygons: List[ee_symbol_polygon] = field(default_factory=list)
    paths: List[ee_symbol_path] = field(default_factory=list)


# ------------------------------------------------------------------------------
# Footprint


def convert_to_mm(dim: float):
    return float(dim) * 10 * 0.0254


@dataclass
class ee_footprint_bbox:

    x: float
    y: float

    def convert_to_mm(self):
        self.x = convert_to_mm(self.x)
        self.y = convert_to_mm(self.y)


class ee_footprint_pad(BaseModel):
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

    def convert_to_mm(self):
        self.center_x = convert_to_mm(self.center_x)
        self.center_y = convert_to_mm(self.center_y)
        self.width = convert_to_mm(self.width)
        self.height = convert_to_mm(self.height)
        self.hole_radius = convert_to_mm(self.hole_radius)
        self.hole_length = convert_to_mm(self.hole_length)

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked

    @validator("rotation", pre=True)
    def empty_str_rotation(cls, rotation):
        return 0.0 if rotation == "" else rotation


class ee_footprint_track(BaseModel):
    stroke_width: float
    layer_id: int
    net: str
    points: str
    id: str
    is_locked: bool

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked

    def convert_to_mm(self):
        self.stroke_width = convert_to_mm(self.stroke_width)


class ee_footprint_hole(BaseModel):
    center_x: float
    center_y: float
    radius: float
    id: str
    is_locked: bool

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked

    def convert_to_mm(self):
        self.center_x = convert_to_mm(self.center_x)
        self.center_y = convert_to_mm(self.center_y)
        self.radius = convert_to_mm(self.radius)


class ee_footprint_circle(BaseModel):
    cx: float
    cy: float
    radius: float
    stroke_width: float
    layer_id: int
    id: str
    is_locked: bool

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked

    def convert_to_mm(self):
        self.cx = convert_to_mm(self.cx)
        self.cy = convert_to_mm(self.cy)
        self.radius = convert_to_mm(self.radius)
        self.stroke_width = convert_to_mm(self.stroke_width)


class ee_footprint_rectangle(BaseModel):
    x: float
    y: float
    width: float
    height: float
    stroke_width: float
    id: str
    layer_id: int
    is_locked: bool

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked

    def convert_to_mm(self):
        self.x = convert_to_mm(self.x)
        self.y = convert_to_mm(self.y)
        self.width = convert_to_mm(self.width)
        self.height = convert_to_mm(self.height)


class ee_footprint_arc(BaseModel):
    stroke_width: float
    layer_id: int
    net: str
    path: str
    helper_dots: str
    id: str
    is_locked: bool

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked


class ee_footprint_text(BaseModel):
    type: str
    center_x: float
    center_y: float
    stroke_width: float
    rotation: int
    miror: str
    layer_id: int
    net: str
    font_size: float
    text: str
    text_path: str
    is_displayed: bool
    id: str
    is_locked: bool

    @validator("is_displayed", pre=True)
    def empty_str_display(cls, is_displayed):
        return True if is_displayed == "" else is_displayed

    @validator("is_locked", pre=True)
    def empty_str_lock(cls, is_locked):
        return False if is_locked == "" else is_locked

    @validator("rotation", pre=True)
    def empty_str_rotation(cls, rotation):
        return 0.0 if rotation == "" else rotation

    def convert_to_mm(self):

        self.center_x = convert_to_mm(self.center_x)
        self.center_y = convert_to_mm(self.center_y)
        self.stroke_width = convert_to_mm(self.stroke_width)
        self.font_size = convert_to_mm(self.font_size)


# ---------------- FOOTPRINT ----------------


@dataclass
class ee_footprint_info:
    name: str
    fp_type: str


@dataclass
class ee_footprint:
    info: ee_footprint_info
    bbox: ee_footprint_bbox
    pads: List[ee_footprint_pad] = field(default_factory=list)
    tracks: List[ee_footprint_track] = field(default_factory=list)
    holes: List[ee_footprint_hole] = field(default_factory=list)
    circles: List[ee_footprint_circle] = field(default_factory=list)
    arcs: List[ee_footprint_arc] = field(default_factory=list)
    rectangles: List[ee_footprint_rectangle] = field(default_factory=list)
    texts: List[ee_footprint_text] = field(default_factory=list)
