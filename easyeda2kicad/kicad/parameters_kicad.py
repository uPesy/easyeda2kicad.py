# Global imports
import itertools
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
    "inverted": "I",
    "clock": "C",
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
    y_low: int = 0
    y_high: int = 0

    def export(self) -> str:
        return "\n".join(
            (
                f"#\n# {self.name}\n#",
                "DEF {name} {ref} 0 {pin_name_offset} {show_pin_number} {show_pin_name} {num_units} L N".format(
                    name=self.name,
                    ref=self.prefix,
                    pin_name_offset=KI_PIN_NAME_OFFSET,
                    show_pin_number=KI_SHOW_PIN_NUMBER and "Y" or "N",
                    show_pin_name=KI_SHOW_PIN_NAME and "Y" or "N",
                    num_units=1,
                ),
                'F0 "{ref_prefix}" {x} {y} {font_size} H V {text_justification} CNN'.format(
                    ref_prefix=self.prefix,
                    x=0,
                    y=self.y_high + KI_REF_Y_OFFSET,
                    text_justification="C",  # Center align
                    font_size=KI_REF_SIZE,
                ),
                'F1 "{num}" {x} {y} {font_size} H V {text_justification} CNN'.format(
                    num=self.name,
                    x=0,
                    y=self.y_low - KI_PART_NUM_Y_OFFSET,
                    text_justification="C",  # Center align
                    font_size=KI_PART_NUM_SIZE,
                ),
                'F2 "{footprint}" {x} {y} {font_size} H I {text_justification} CNN'.format(
                    footprint=self.package,
                    x=0,
                    y=self.y_low - KI_PART_FOOTPRINT_Y_OFFSET,
                    text_justification="C",  # Center align
                    font_size=KI_PART_FOOTPRINT_SIZE,
                )
                if self.package
                else "",
                'F3 "{datasheet}" {x} {y} {font_size} H I {text_justification} CNN'.format(
                    datasheet=self.datasheet,
                    x=0,
                    y=self.y_low - KI_PART_DATASHEET_Y_OFFSET,
                    text_justification="C",  # Center align
                    font_size=KI_PART_DATASHEET_SIZE,
                )
                if self.datasheet
                else "",
                'F4 "{manufacturer}" 0 0 0 H I C CNN "Manufacturer"'.format(
                    manufacturer=self.manufacturer,
                )
                if self.manufacturer
                else "",
                f'F6 "{self.lcsc_id}" 0 0 0 H I C CNN "LCSC Part"'
                if self.lcsc_id
                else "",
                f'F7 "{self.jlc_id}" 0 0 0 H I C CNN "JLC Part"' if self.jlc_id else "",
                "DRAW\n",
            )
        ).replace("\n\n", "\n")


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

    def export(self) -> str:
        return "X {name} {num} {x} {y} {length} {orientation} {num_sz} {name_sz} {unit_num} 1 {pin_type} {pin_style}\n".format(
            name=self.name,
            num=self.number,
            x=self.pos_x,
            y=self.pos_y,
            length=KI_PIN_LENGTH,
            orientation=self.orientation,
            num_sz=KI_PIN_NUM_SIZE,
            name_sz=KI_PIN_NAME_SIZE,
            unit_num=1,
            pin_type=self.type,
            pin_style=self.style,
        )


# ---------------- RECTANGLE ----------------
@dataclass
class ki_symbol_rectangle:
    pos_x0: int = 0
    pos_y0: int = 0
    pos_x1: int = 0
    pos_y1: int = 0

    def export(self) -> str:
        return "S {x0} {y0} {x1} {y1} {unit_num} 1 {line_width} {fill}\n".format(
            x0=int(round(self.pos_x0 / 50.0)) * 50,
            y0=int(round(self.pos_y0 / 50.0)) * 50,
            x1=int(round(self.pos_x1 / 50.0)) * 50,
            y1=int(round(self.pos_y1 / 50.0)) * 50,
            unit_num=1,
            line_width=KI_DEFAULT_BOX_LINE_WIDTH,
            fill=KI_BOX_FILLS["bg_fill"],
        )


# ---------------- POLYGON ----------------
@dataclass
class ki_symbol_polygon:
    points: List[List[int]] = field(default_factory=List[List[int]])
    points_number: int = 0
    is_closed: bool = False

    def export(self) -> str:
        return (
            "P {points_number} {unit_num} 1 {line_width} {coordinate} {fill}\n".format(
                points_number=self.points_number,
                unit_num=1,
                line_width=KI_DEFAULT_BOX_LINE_WIDTH,
                coordinate=" ".join(list(itertools.chain.from_iterable(self.points))),
                fill=KI_BOX_FILLS["bg_fill"]
                if self.is_closed
                else KI_BOX_FILLS["no_fill"],
            )
        )


# ---------------- CIRCLE ----------------
@dataclass
class ki_symbol_circle:
    pos_x: int = 0
    pos_y: int = 0
    radius: int = 0

    def export(self) -> str:
        return "C {pos_x} {pos_y} {radius} {unit_num} 1 {line_width} {fill}\n".format(
            pos_x=self.pos_x,
            pos_y=self.pos_y,
            radius=self.radius,
            unit_num=1,
            line_width=KI_DEFAULT_BOX_LINE_WIDTH,
            fill=KI_BOX_FILLS["bg_fill"],
        )


# ---------------- ARC ----------------
@dataclass
class ki_symbol_arc:
    pos_x: int = 0
    pos_y: int = 0
    radius: int = 0
    angle_start: float = 0.0
    angle_end: float = 0.0
    start_x: int = 0
    start_y: int = 0
    end_x: int = 0
    end_y: int = 0

    def export(self) -> str:
        return "C {pos_x} {pos_y} {radius} {angle_start} {angle_end} {unit_num} 1 {line_width} {fill} {start_x} {start_y} {end_x} {end_y}\n".format(
            pos_x=self.pos_x,
            pos_y=self.pos_y,
            radius=self.radius,
            angle_start=self.angle_start,
            angle_end=self.angle_end,
            unit_num=1,
            line_width=KI_DEFAULT_BOX_LINE_WIDTH,
            fill=KI_BOX_FILLS["bg_fill"]
            if self.angle_start == self.angle_end
            else KI_BOX_FILLS["no_fill"],
            start_x=self.start_x,
            start_y=self.start_y,
            end_x=self.end_x,
            end_y=self.end_y,
        )


# ---------------- BEZIER CURVE ----------------
@dataclass
class ki_symbol_bezier:
    points: List[List[int]] = field(default_factory=List[List[int]])
    points_number: int = 0
    is_closed: bool = False

    def export(self) -> str:
        return (
            "B {points_number} {unit_num} 1 {line_width} {coordinate} {fill}\n".format(
                points_number=self.points_number,
                unit_num=1,
                line_width=KI_DEFAULT_BOX_LINE_WIDTH,
                coordinate=" ".join(list(itertools.chain.from_iterable(self.points))),
                fill=KI_BOX_FILLS["bg_fill"]
                if self.is_closed
                else KI_BOX_FILLS["no_fill"],
            )
        )


# ---------------- SYMBOL ----------------
@dataclass
class ki_symbol:
    info: ki_symbol_info
    pins: List[ki_symbol_pin] = field(default_factory=lambda: [])
    rectangles: List[ki_symbol_rectangle] = field(default_factory=lambda: [])
    circles: List[ki_symbol_circle] = field(default_factory=lambda: [])
    arcs: List[ki_symbol_arc] = field(default_factory=lambda: [])
    polygons: List[ki_symbol_polygon] = field(default_factory=lambda: [])
    beziers: List[ki_symbol_bezier] = field(default_factory=lambda: [])

    def export(self) -> str:
        lib_output = ""
        # Get y_min and y_max to put component info
        self.info.y_low = min(pin.pos_y for pin in self.pins) if self.pins else 0
        self.info.y_high = max(pin.pos_y for pin in self.pins) if self.pins else 0

        for _field in fields(self):
            shapes = getattr(self, _field.name)
            if isinstance(shapes, list):
                for sub_symbol in shapes:
                    lib_output += sub_symbol.export()
            else:
                lib_output += shapes.export()

        lib_output += "ENDDRAW\n" + "ENDDEF\n"

        return lib_output


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
KI_MODEL_3D = '\t(model "{file_3d}"\n\t\t(offset (xyz {pos_x:.3f} {pos_y:.3f} {pos_z:.3f}))\n\t\t(scale (xyz 1 1 1))\n\t\t(rotate (xyz {rot_x:.0f} {rot_y:.0f} {rot_z:.0f}))\n\t)\n'


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


# ---------------- 3D MODEL ----------------
@dataclass
class ki_3d_model_base:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class ki_3d_model:
    name: str
    translation: ki_3d_model_base
    rotation: ki_3d_model_base
    raw_wrl: str = None


# ---------------- FOOTPRINT  ----------------
@dataclass
class ki_footprint:
    info: ki_footprint_info
    model_3d: ki_3d_model
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
