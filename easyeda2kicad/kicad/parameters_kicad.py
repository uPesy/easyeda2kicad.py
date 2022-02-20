# Global imports
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import List

# ---------------- CONFIG ----------------

# Origin point.
KI_XO = 0
KI_YO = 0

# Settings for box drawn around pins in a unit.
KI_DEFAULT_BOX_LINE_WIDTH = 0

# Mapping from understandable schematic symbol box fill-type name
# to the fill-type indicator used in the KiCad part library.
KI_BOX_FILLS = {"no_fill": "N", "fg_fill": "F", "bg_fill": "f"}
KI_DEFAULT_BOX_FILL = "bg_fill"

# Part reference.
KI_REF_SIZE = 60  # Font size.
KI_REF_Y_OFFSET = 200

# Part number.
KI_PART_NUM_SIZE = 60  # Font size.
KI_PART_NUM_Y_OFFSET = 200

# Part footprint
KI_PART_FOOTPRINT_SIZE = 60  # Font size.
KI_PART_FOOTPRINT_Y_OFFSET = KI_PART_NUM_Y_OFFSET + 100

# Part manufacturer number.
KI_PART_MPN_SIZE = 60  # Font size.
KI_PART_MPN_Y_OFFSET = KI_PART_FOOTPRINT_Y_OFFSET + 100

# Part datasheet.
KI_PART_DATASHEET_SIZE = 60  # Font size.
KI_PART_DATASHEET_Y_OFFSET = KI_PART_MPN_Y_OFFSET + 100

# Part description.
KI_PART_DESC_SIZE = 60  # Font size.
KI_PART_DESC_Y_OFFSET = KI_PART_DATASHEET_Y_OFFSET + 100


KI_ROTATION = {"left": 0, "right": 180, "bottom": 90, "top": -90}

KI_PIN_LENGTH = 100
KI_PIN_SPACING = 100
KI_PIN_NUM_SIZE = 50  # Font size for pin numbers.
KI_PIN_NAME_SIZE = 50  # Font size for pin names.
KI_PIN_NAME_OFFSET = 40  # Separation between pin and pin name.
KI_PIN_ORIENTATION = "left"
KI_PIN_STYLE = "line"
KI_SHOW_PIN_NUMBER = True  # Show pin numbers when True.
KI_SHOW_PIN_NAME = True  # Show pin names when True.
KI_SINGLE_PIN_SUFFIX = ""
KI_MULTI_PIN_SUFFIX = "*"
KI_PIN_SPACER_PREFIX = "*"

# --------------

KI_LIB_HEADER = "EESchema-LIBRARY Version 2.3\n#encoding utf-8\n"
KI_START_DEF = "DEF {name} {ref} 0 {pin_name_offset} {show_pin_number} {show_pin_name} {num_units} L N\n"
KI_REF_FIELD = 'F0 "{ref_prefix}" {x} {y} {font_size} H V {text_justification} CNN\n'
KI_PARTNUM_FIELD = 'F1 "{num}" {x} {y} {font_size} H V {text_justification} CNN\n'
KI_FOOTPRINT_FIELD = (
    'F2 "{footprint}" {x} {y} {font_size} H I {text_justification} CNN\n'
)
KI_DATASHEET_FIELD = (
    'F3 "{datasheet}" {x} {y} {font_size} H I {text_justification} CNN\n'
)
KI_MPN_FIELD = 'F4 "{manufacturer}" 0 0 0 H I C CNN "Manufacturer"\n'
KI_DESC_FIELD = 'F5 "{desc}" 0 0 0 H I C CNN "desc"\n'
KI_LCSC_FIELD = 'F6 "{id}" 0 0 0 H I C CNN "LCSC Part"\n'
KI_JLCPCB_FIELD = 'F7 "{type}" 0 0 0 H I C CNN "JLC Part"\n'

KI_START_DRAW = "DRAW\n"

KI_BOX = "S {x0} {y0} {x1} {y1} {unit_num} 1 {line_width} {fill}\n"
KI_PIN = "X {name} {num} {x} {y} {length} {orientation} {num_sz} {name_sz} {unit_num} 1 {pin_type} {pin_style}\n"
KI_POLYLINE = "P {points_number} {unit_num} 1 {line_width} {coordinate} {fill}\n"

KI_END_DRAW = "ENDDRAW\n"
KI_END_DEF = "ENDDEF\n"

# --------------

KI_PIN_TYPES = {
    "input": "I",
    "inp": "I",
    "in": "I",
    "clk": "I",
    "output": "O",
    "outp": "O",
    "out": "O",
    "bidirectional": "B",
    "bidir": "B",
    "bi": "B",
    "inout": "B",
    "io": "B",
    "iop": "B",
    "tristate": "T",
    "tri": "T",
    "passive": "P",
    "pass": "P",
    "unspecified": "U",
    "un": "U",
    "": "U",
    "analog": "U",
    "power_in": "W",
    "pwr_in": "W",
    "pwrin": "W",
    "power": "W",
    "pwr": "W",
    "ground": "W",
    "gnd": "W",
    "power_out": "w",
    "pwr_out": "w",
    "pwrout": "w",
    "pwr_o": "w",
    "open_collector": "C",
    "opencollector": "C",
    "open_coll": "C",
    "opencoll": "C",
    "oc": "C",
    "open_emitter": "E",
    "openemitter": "E",
    "open_emit": "E",
    "openemit": "E",
    "oe": "E",
    "no_connect": "N",
    "noconnect": "N",
    "no_conn": "N",
    "noconn": "N",
    "nc": "N",
}

KI_PIN_STYLES = {
    "line": "",
    "": "",
    "inverted": "I",
    "inv": "I",
    "~": "I",
    "#": "I",
    "clock": "C",
    "clk": "C",
    "rising_clk": "C",
    "inverted_clock": "IC",
    "inv_clk": "IC",
    "clk_b": "IC",
    "clk_n": "IC",
    "~clk": "IC",
    "#clk": "IC",
    "input_low": "L",
    "inp_low": "L",
    "in_lw": "L",
    "in_b": "L",
    "in_n": "L",
    "~in": "L",
    "#in": "L",
    "clock_low": "CL",
    "clk_low": "CL",
    "clk_lw": "CL",
    "output_low": "V",
    "outp_low": "V",
    "out_lw": "V",
    "out_b": "V",
    "out_n": "V",
    "~out": "V",
    "#out": "V",
    "falling_edge_clock": "F",
    "falling_clk": "F",
    "fall_clk": "F",
    "non_logic": "X",
    "nl": "X",
    "analog": "X",
}

KI_PIN_ORIENTATIONS = {
    "": "R",
    "left": "R",
    "right": "L",
    "bottom": "U",
    "down": "U",
    "top": "D",
    "up": "D",
}


class kicad_pin_orientation(Enum):
    right = 0
    top = 90
    left = 180
    bottom = 270


# ---------------------------- SYMBOL PART ----------------------------

# ---------------- INFO HEADER ----------------
@dataclass
class ki_symbol_info:
    name: str
    prefix: str
    package: str
    manufacturer: str
    datasheet: str
    lcsc_id: str
    jlc_id: str


# ---------------- PIN ----------------
@dataclass
class ki_symbol_pin:
    name: str
    number: str
    style: str
    type: float
    orientation: float
    pos_x: int
    pos_y: int


# ---------------- RECTANGLE ----------------
@dataclass
class ki_symbol_rectangle:
    pos_x0: int = 0
    pos_y0: int = 0
    pos_x1: int = 0
    pos_y1: int = 0


# ---------------- POLYLINE ----------------
@dataclass
class ki_symbol_polyline:
    points: List[List[int]] = field(default_factory=List[List[int]])
    points_number: int = 0
    is_closed: bool = False


# ---------------- SYMBOL ----------------
@dataclass
class ki_symbol:
    info: ki_symbol_info
    pins: List[ki_symbol_pin] = field(default_factory=List[ki_symbol_pin])
    rectangles: List[ki_symbol_rectangle] = field(
        default_factory=List[ki_symbol_rectangle]
    )
    polylines: List[ki_symbol_polyline] = field(
        default_factory=List[ki_symbol_polyline]
    )


# ---------------------------- FOOTPRINT PART ----------------------------

KI_MODULE_INFO = "(module {package_lib}:{package_name} (layer F.Cu) (tedit {edit})\n"
KI_DESCRIPTION = (
    '\t(descr "{datasheet_link}, generated with easyeda2kicad.py on {date}")\n'
)
KI_TAGS_INFO = '\t(tags "{tag}")\n'
KI_FP_TYPE = "\t(attr {component_type})\n"
KI_REFERENCE = "\t(fp_text reference REF** (at {pos_x} {pos_y}) (layer F.SilkS)\n\t\t(effects (font (size 1 1) (thickness 0.15)))\n\t)\n"
KI_PACKAGE_VALUE = "\t(fp_text value {package_name} (at {pos_x} {pos_y}) (layer F.Fab)\n\t\t(effects (font (size 1 1) (thickness 0.15)))\n\t)\n"
KI_FAB_REF = "\t(fp_text user %R (at 0 0) (layer F.Fab)\n\t\t(effects (font (size 1 1) (thickness 0.15)))\n\t)\n"
KI_END_FILE = ")"

KI_PAD = "\t(pad {number} {type} {shape} (at {pos_x:.2f} {pos_y:.2f} {orientation:.2f}) (size {width:.2f} {height:.2f}) (layers {layers}){drill}{polygon})\n"
KI_LINE = "\t(fp_line (start {start_x:.2f} {start_y:.2f}) (end {end_x:.2f} {end_y:.2f}) (layer {layers}) (width {stroke_width:.2f}))\n"
KI_HOLE = '\t(pad "" thru_hole circle (at {pos_x:.2f} {pos_y:.2f}) (size {size:.2f} {size:.2f}) (drill {size:.2f}) (layers *.Cu *.Mask))\n'
KI_CIRCLE = "\t(fp_circle (center {cx:.2f} {cy:.2f}) (end {end_x:.2f} {end_y:.2f}) (layer {layers}) (width {stroke_width:.2f}))\n"
KI_ARC = "\t(fp_arc (start {start_x:.2f} {start_y:.2f}) (end {end_x:.2f} {end_y:.2f}) (angle {angle:.2f}) (layer {layers}) (width {stroke_width:.2f}))\n"
KI_TEXT = "\t(fp_text user {text} (at {pos_x:.2f} {pos_y:.2f} {orientation:.2f}) (layer {layers}){display}\n\t\t(effects (font (size {font_size:.2f} {font_size:.2f}) (thickness {thickness:.2f})) (justify left{mirror}))\n\t)\n"

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
def round_float_values(self):
    for _field in fields(self):
        current_value = getattr(self, _field.name)
        if isinstance(current_value, float):
            setattr(self, _field.name, round(current_value, 2))


# ---------------- PAD ----------------
@dataclass
class ki_footprint_pad:
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

    def __post_init__(self):
        round_float_values(self)


# ---------------- TRACK ----------------
@dataclass
class ki_footprint_track:
    points_start_x: List[float] = field(default_factory=list)
    points_start_y: List[float] = field(default_factory=list)
    points_end_x: List[float] = field(default_factory=list)
    points_end_y: List[float] = field(default_factory=list)
    stroke_width: float = 0
    layers: str = ""


# ---------------- HOLE ----------------
@dataclass
class ki_footprint_hole:
    pos_x: float
    pos_y: float
    size: float

    def __post_init__(self):
        round_float_values(self)


# ---------------- CIRCLE ----------------
@dataclass
class ki_footprint_circle:
    cx: float
    cy: float
    end_x: float
    end_y: float
    layers: str
    stroke_width: float

    def __post_init__(self):
        round_float_values(self)


# ---------------- RECTANGLE ----------------
@dataclass
class ki_footprint_rectangle(ki_footprint_track):
    ...
    # points_start_x:List[float] = field(default_factory=list)
    # points_start_y:List[float] = field(default_factory=list)
    # points_end_x:List[float] = field(default_factory=list)
    # points_end_y:List[float] = field(default_factory=list)
    # stroke_width:float = 0
    # layers:str = ''


# ---------------- ARC ----------------
@dataclass
class ki_footprint_arc:
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
class ki_footprint_text:
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
class ki_footprint_via:
    name: str = ""
    # TODO


# ---------------- SOLID REGION ----------------
@dataclass
class ki_footprint_solid_region:
    name: str = ""
    # TODO


# ---------------- COPPER AREA ----------------
@dataclass
class ki_footprint_copper_area:
    name: str = ""
    # TODO


# ---------------- FOOTPRINT INFO ----------------
@dataclass
class ki_footprint_info:
    name: str
    fp_type: str


# ---------------- FOOTPRINT OBJ ----------------
@dataclass
class ki_footprint:
    info: ki_footprint_info
    pads: List[ki_footprint_pad] = field(default_factory=list)
    tracks: List[ki_footprint_track] = field(default_factory=list)
    vias: List[ki_footprint_via] = field(default_factory=list)
    holes: List[ki_footprint_hole] = field(default_factory=list)
    circles: List[ki_footprint_circle] = field(default_factory=list)
    arcs: List[ki_footprint_arc] = field(default_factory=list)
    rectangles: List[ki_footprint_rectangle] = field(default_factory=list)
    texts: List[ki_footprint_text] = field(default_factory=list)
    solid_regions: List[ki_footprint_solid_region] = field(default_factory=list)
    copper_areas: List[ki_footprint_copper_area] = field(default_factory=list)
