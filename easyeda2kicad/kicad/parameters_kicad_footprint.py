# Global imports
import itertools
import re
import textwrap
from dataclasses import dataclass, field, fields
from enum import Enum, auto
from typing import List

# ---------------------------- FOOTPRINT PART ----------------------------

KI_MODULE_INFO = "(module {package_lib}:{package_name} (layer F.Cu) (tedit {edit})\n"
KI_DESCRIPTION = (
    '\t(descr "{datasheet_link}, generated with easyeda2kicad.py on {date}")\n'
)
KI_TAGS_INFO = '\t(tags "{tag}")\n'
KI_FP_TYPE = "\t(attr {component_type})\n"
KI_REFERENCE = (
    "\t(fp_text reference REF** (at {pos_x} {pos_y}) (layer F.SilkS)\n\t\t(effects"
    " (font (size 1 1) (thickness 0.15)))\n\t)\n"
)
KI_PACKAGE_VALUE = (
    "\t(fp_text value {package_name} (at {pos_x} {pos_y}) (layer F.Fab)\n\t\t(effects"
    " (font (size 1 1) (thickness 0.15)))\n\t)\n"
)
KI_FAB_REF = (
    "\t(fp_text user %R (at 0 0) (layer F.Fab)\n\t\t(effects (font (size 1 1)"
    " (thickness 0.15)))\n\t)\n"
)
KI_END_FILE = ")"

KI_PAD = (
    "\t(pad {number} {type} {shape} (at {pos_x:.2f} {pos_y:.2f} {orientation:.2f})"
    " (size {width:.2f} {height:.2f}) (layers {layers}){drill}{polygon})\n"
)
KI_LINE = (
    "\t(fp_line (start {start_x:.2f} {start_y:.2f}) (end {end_x:.2f} {end_y:.2f})"
    " (layer {layers}) (width {stroke_width:.2f}))\n"
)
KI_HOLE = (
    '\t(pad "" thru_hole circle (at {pos_x:.2f} {pos_y:.2f}) (size {size:.2f}'
    " {size:.2f}) (drill {size:.2f}) (layers *.Cu *.Mask))\n"
)
KI_VIA = (
    '\t(pad "" thru_hole circle (at {pos_x:.2f} {pos_y:.2f}) (size {diameter:.2f}'
    " {diameter:.2f}) (drill {size:.2f}) (layers *.Cu *.Paste *.Mask))\n"
)
KI_CIRCLE = (
    "\t(fp_circle (center {cx:.2f} {cy:.2f}) (end {end_x:.2f} {end_y:.2f}) (layer"
    " {layers}) (width {stroke_width:.2f}))\n"
)
KI_ARC = (
    "\t(fp_arc (start {start_x:.2f} {start_y:.2f}) (end {end_x:.2f} {end_y:.2f}) (angle"
    " {angle:.2f}) (layer {layers}) (width {stroke_width:.2f}))\n"
)
KI_TEXT = (
    "\t(fp_text user {text} (at {pos_x:.2f} {pos_y:.2f} {orientation:.2f}) (layer"
    " {layers}){display}\n\t\t(effects (font (size {font_size:.2f} {font_size:.2f})"
    " (thickness {thickness:.2f})) (justify left{mirror}))\n\t)\n"
)
KI_MODEL_3D = (
    '\t(model "{file_3d}"\n\t\t(offset (xyz {pos_x:.3f} {pos_y:.3f}'
    " {pos_z:.3f}))\n\t\t(scale (xyz 1 1 1))\n\t\t(rotate (xyz {rot_x:.0f} {rot_y:.0f}"
    " {rot_z:.0f}))\n\t)\n"
)


# ---------------------------------------

KI_PAD_SHAPE = {
    "ELLIPSE": "circle",
    "RECT": "rect",
    "OVAL": "oval",
    "POLYGON": "custom",
}
KI_PAD_LAYER = {
    1: "F.Cu F.Paste F.Mask",
    2: "B.Cu B.Paste B.Mask",
    3: "F.SilkS",
    11: "*.Cu *.Paste *.Mask",
    13: "F.Fab",
    15: "Dwgs.User",
}

KI_PAD_LAYER_THT = {
    1: "F.Cu F.Mask",
    2: "B.Cu B.Mask",
    3: "F.SilkS",
    11: "*.Cu *.Mask",
    13: "F.Fab",
    15: "Dwgs.User",
}

KI_LAYERS = {
    1: "F.Cu",
    2: "B.Cu",
    3: "F.SilkS",
    4: "B.SilkS",
    5: "F.Paste",
    6: "B.Paste",
    7: "F.Mask",
    8: "B.Mask",
    10: "Edge.Cuts",
    11: "Edge.Cuts",
    12: "Cmts.User",
    13: "F.Fab",
    14: "B.Fab",
    15: "Dwgs.User",
    101: "F.Fab",
}


# Round all float values contained in the dataclass
def round_float_values(self) -> None:
    for _field in fields(self):
        current_value = getattr(self, _field.name)
        if isinstance(current_value, float):
            setattr(self, _field.name, round(current_value, 2))


# ---------------- PAD ----------------
@dataclass
class KiFootprintPad:
    type: str
    shape: str
    pos_x: float
    pos_y: float
    width: float
    height: float
    layers: str
    number: str
    drill: float
    orientation: float
    polygon: str

    def __post_init__(self) -> None:
        round_float_values(self)


# ---------------- TRACK ----------------
@dataclass
class KiFootprintTrack:
    points_start_x: List[float] = field(default_factory=list)
    points_start_y: List[float] = field(default_factory=list)
    points_end_x: List[float] = field(default_factory=list)
    points_end_y: List[float] = field(default_factory=list)
    stroke_width: float = 0
    layers: str = ""


# ---------------- HOLE ----------------
@dataclass
class KiFootprintHole:
    pos_x: float
    pos_y: float
    size: float

    def __post_init__(self) -> None:
        round_float_values(self)


# ---------------- CIRCLE ----------------
@dataclass
class KiFootprintCircle:
    cx: float
    cy: float
    end_x: float
    end_y: float
    layers: str
    stroke_width: float

    def __post_init__(self) -> None:
        round_float_values(self)


# ---------------- RECTANGLE ----------------
@dataclass
class KiFootprintRectangle(KiFootprintTrack):
    ...
    # points_start_x:List[float] = field(default_factory=list)
    # points_start_y:List[float] = field(default_factory=list)
    # points_end_x:List[float] = field(default_factory=list)
    # points_end_y:List[float] = field(default_factory=list)
    # stroke_width:float = 0
    # layers:str = ''


# ---------------- ARC ----------------
@dataclass
class KiFootprintArc:
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    angle: float
    layers: str
    stroke_width: float

    def __post_init__(self):
        round_float_values(self)


# ---------------- TEXT ----------------
@dataclass
class KiFootprintText:
    pos_x: float
    pos_y: float
    orientation: float
    text: str
    layers: str
    font_size: float
    thickness: float
    display: str
    mirror: str

    def __post_init__(self):
        round_float_values(self)


# ---------------- VIA ----------------
@dataclass
class KiFootprintVia:
    pos_x: float
    pos_y: float
    size: float
    diameter: float

    def __post_init__(self) -> None:
        round_float_values(self)

    # TODO


# ---------------- SOLID REGION ----------------
@dataclass
class KiFootprintSolidRegion:
    name: str = ""
    # TODO


# ---------------- COPPER AREA ----------------
@dataclass
class KiFootprintCopperArea:
    name: str = ""
    # TODO


# ---------------- FOOTPRINT INFO ----------------
@dataclass
class KiFootprintInfo:
    name: str
    fp_type: str


# ---------------- 3D MODEL ----------------
@dataclass
class Ki3dModelBase:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Ki3dModel:
    name: str
    translation: Ki3dModelBase
    rotation: Ki3dModelBase
    raw_wrl: str = None


# ---------------- FOOTPRINT  ----------------
@dataclass
class KiFootprint:
    info: KiFootprintInfo
    model_3d: Ki3dModel
    pads: List[KiFootprintPad] = field(default_factory=list)
    tracks: List[KiFootprintTrack] = field(default_factory=list)
    vias: List[KiFootprintVia] = field(default_factory=list)
    holes: List[KiFootprintHole] = field(default_factory=list)
    circles: List[KiFootprintCircle] = field(default_factory=list)
    arcs: List[KiFootprintArc] = field(default_factory=list)
    rectangles: List[KiFootprintRectangle] = field(default_factory=list)
    texts: List[KiFootprintText] = field(default_factory=list)
    solid_regions: List[KiFootprintSolidRegion] = field(default_factory=list)
    copper_areas: List[KiFootprintCopperArea] = field(default_factory=list)
