# Global imports
import json
import logging
from dataclasses import fields
from typing import Union, get_args, get_origin, get_type_hints

# Local imports
from .easyeda_api import EasyedaApi
from .parameters_easyeda import (
    Ee3dModel,
    Ee3dModelBase,
    EeFootprintArc,
    EeFootprintBbox,
    EeFootprintCircle,
    EeFootprintHole,
    EeFootprintInfo,
    EeFootprintPad,
    EeFootprintRectangle,
    EeFootprintText,
    EeFootprintTrack,
    EeFootprintVia,
    EeSymbol,
    EeSymbolArc,
    EeSymbolBbox,
    EeSymbolCircle,
    EeSymbolEllipse,
    EeSymbolInfo,
    EeSymbolPath,
    EeSymbolPin,
    EeSymbolPinClock,
    EeSymbolPinDot,
    EeSymbolPinDotBis,
    EeSymbolPinName,
    EeSymbolPinPath,
    EeSymbolPinSettings,
    EeSymbolPolygon,
    EeSymbolPolyline,
    EeSymbolRectangle,
    ee_footprint,
)


# Safe conversion helpers
def _safe_float(value, default=0.0):
    """Convert value to float, return default if conversion fails."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value, default=0):
    """Convert value to int, return default if conversion fails."""
    if value is None or value == "":
        return default
    try:
        return int(float(value))  # float first to handle "1.0" -> 1
    except (ValueError, TypeError):
        return default


def _safe_bool(value, default=False):
    """Convert value to bool, return default if conversion fails."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    try:
        return bool(int(value))
    except (ValueError, TypeError):
        return default


def convert_fields_to_types(field_dict, dataclass_type):
    """
    Convert string values in field_dict to appropriate types based on dataclass_type annotations.
    This is the ROOT CAUSE FIX for EasyEDA string data.
    """
    try:
        type_hints = get_type_hints(dataclass_type)
    except Exception:
        # Fallback if type hints can't be resolved
        return field_dict

    converted = {}
    for key, value in field_dict.items():
        if key not in type_hints:
            converted[key] = value
            continue

        field_type = type_hints[key]

        # Handle Optional types
        origin = get_origin(field_type)
        if origin is type(None) or str(origin) == "typing.Union":
            args = get_args(field_type)
            if args and type(None) in args:
                # It's Optional[T], get the non-None type
                field_type = next((arg for arg in args if arg is not type(None)), str)

        # Convert based on type
        if field_type is float or field_type == "float":
            converted[key] = _safe_float(value)
        elif field_type is int or field_type == "int":
            converted[key] = _safe_int(value)
        elif field_type is bool or field_type == "bool":
            converted[key] = _safe_bool(value)
        else:
            converted[key] = value

    return converted


def add_easyeda_pin(pin_data: str, ee_symbol: EeSymbol):
    segments = pin_data.split("^^")
    ee_segments = [seg.split("~") for seg in segments]

    # Extract the correct KiCad pin number from segment 4[4]
    correct_pin_number = None
    if len(ee_segments) > 4 and len(ee_segments[4]) > 4:
        correct_pin_number = ee_segments[4][4]

    pin_settings_data = (
        ee_segments[0][1:] if len(ee_segments) > 0 and len(ee_segments[0]) > 1 else []
    )
    pin_settings_fields = [f.name for f in fields(EeSymbolPinSettings)]
    pin_settings_dict = dict(zip(pin_settings_fields, pin_settings_data))
    pin_settings = EeSymbolPinSettings(
        **convert_fields_to_types(pin_settings_dict, EeSymbolPinSettings)
    )

    # Override spice_pin_number with the correct KiCad pin number if found
    if correct_pin_number is not None:
        pin_settings.spice_pin_number = correct_pin_number
    else:
        logging.warning(
            f"Could not find correct pin number for pin data, using spice_pin_number: {pin_settings.spice_pin_number}"
        )

    pin_dot = EeSymbolPinDot(
        dot_x=_safe_float(
            ee_segments[1][0]
            if len(ee_segments) > 1 and len(ee_segments[1]) > 0
            else None
        ),
        dot_y=_safe_float(
            ee_segments[1][1]
            if len(ee_segments) > 1 and len(ee_segments[1]) > 1
            else None
        ),
    )
    pin_path = EeSymbolPinPath(
        path=(
            ee_segments[2][0]
            if len(ee_segments) > 2 and len(ee_segments[2]) > 0
            else ""
        ),
        color=(
            ee_segments[2][1]
            if len(ee_segments) > 2 and len(ee_segments[2]) > 1
            else ""
        ),
    )
    pin_name_dict = dict(
        zip(
            [f.name for f in fields(EeSymbolPinName)],
            ee_segments[3][:] if len(ee_segments) > 3 else [],
        )
    )
    pin_name = EeSymbolPinName(
        **convert_fields_to_types(pin_name_dict, EeSymbolPinName)
    )

    pin_dot_bis = EeSymbolPinDotBis(
        is_displayed=_safe_bool(
            ee_segments[5][0]
            if len(ee_segments) > 5 and len(ee_segments[5]) > 0
            else ""
        ),
        circle_x=_safe_float(
            ee_segments[5][1]
            if len(ee_segments) > 5 and len(ee_segments[5]) > 1
            else None
        ),
        circle_y=_safe_float(
            ee_segments[5][2]
            if len(ee_segments) > 5 and len(ee_segments[5]) > 2
            else None
        ),
    )
    pin_clock = EeSymbolPinClock(
        is_displayed=_safe_bool(
            ee_segments[6][0]
            if len(ee_segments) > 6 and len(ee_segments[6]) > 0
            else ""
        ),
        path=(
            ee_segments[6][1]
            if len(ee_segments) > 6 and len(ee_segments[6]) > 1
            else ""
        ),
    )

    ee_symbol.pins.append(
        EeSymbolPin(
            settings=pin_settings,
            pin_dot=pin_dot,
            pin_path=pin_path,
            name=pin_name,
            dot=pin_dot_bis,
            clock=pin_clock,
        )
    )


def add_easyeda_rectangle(rectangle_data: str, ee_symbol: EeSymbol):
    parts = rectangle_data.split("~")[1:]

    # Handle EasyEDA format inconsistency with TWO different formats:
    # Format 1: R~x~y~~width~height~stroke_color~stroke_width~stroke_style~fill_color~id~locked
    #           Empty fields at positions 2,3 indicate no rounded corners
    # Format 2: R~x~y~rx~ry~width~height~stroke_color~stroke_width~stroke_style~fill_color~id~locked
    #           rx, ry for rounded corners at positions 2,3
    #
    # Dataclass expects: pos_x, pos_y, width, height, stroke_color, stroke_width, stroke_style,
    #                    fill_color, id, is_locked, rx, ry

    rx, ry = None, None

    if len(parts) >= 6 and parts[2] == "" and parts[3] == "":
        # Format 1: No rounded corners (empty fields at 2,3)
        # R~x~y~~width~height~stroke_color~...
        # Map to: [x, y, width, height, stroke_color, ...]
        normalized_parts = [parts[0], parts[1], parts[4], parts[5]] + parts[6:]
        rx, ry = None, None
    elif len(parts) >= 8:
        # Format 2: Rounded corners (rx, ry at positions 2,3)
        # R~x~y~rx~ry~width~height~stroke_color~...
        # Map to: [x, y, width, height, stroke_color, ...]
        rx, ry = parts[2], parts[3]
        normalized_parts = [parts[0], parts[1], parts[4], parts[5]] + parts[6:]
    else:
        # Fallback: assume Format 1 layout
        normalized_parts = parts

    # Build dict for dataclass fields (without rx, ry first)
    rectangle_dict = dict(
        zip(
            [f.name for f in fields(EeSymbolRectangle)],
            normalized_parts,
        )
    )

    # Add rx, ry at the end if they were extracted
    if rx is not None:
        rectangle_dict["rx"] = rx
    if ry is not None:
        rectangle_dict["ry"] = ry

    ee_symbol.rectangles.append(
        EeSymbolRectangle(**convert_fields_to_types(rectangle_dict, EeSymbolRectangle))
    )


def add_easyeda_polyline(polyline_data: str, ee_symbol: EeSymbol):
    polyline_dict = dict(
        zip(
            [f.name for f in fields(EeSymbolPolyline)],
            polyline_data.split("~")[1:],
        )
    )
    ee_symbol.polylines.append(
        EeSymbolPolyline(**convert_fields_to_types(polyline_dict, EeSymbolPolyline))
    )


def add_easyeda_polygon(polygon_data: str, ee_symbol: EeSymbol):
    polygon_dict = dict(
        zip(
            [f.name for f in fields(EeSymbolPolygon)],
            polygon_data.split("~")[1:],
        )
    )
    ee_symbol.polygons.append(
        EeSymbolPolygon(**convert_fields_to_types(polygon_dict, EeSymbolPolygon))
    )


def add_easyeda_path(path_data: str, ee_symbol: EeSymbol):
    path_dict = dict(
        zip([f.name for f in fields(EeSymbolPath)], path_data.split("~")[1:])
    )
    ee_symbol.paths.append(
        EeSymbolPath(**convert_fields_to_types(path_dict, EeSymbolPath))
    )


def add_easyeda_circle(circle_data: str, ee_symbol: EeSymbol):
    circle_dict = dict(
        zip([f.name for f in fields(EeSymbolCircle)], circle_data.split("~")[1:])
    )
    ee_symbol.circles.append(
        EeSymbolCircle(**convert_fields_to_types(circle_dict, EeSymbolCircle))
    )


def add_easyeda_ellipse(ellipse_data: str, ee_symbol: EeSymbol):
    ellipse_dict = dict(
        zip(
            [f.name for f in fields(EeSymbolEllipse)],
            ellipse_data.split("~")[1:],
        )
    )
    ee_symbol.ellipses.append(
        EeSymbolEllipse(**convert_fields_to_types(ellipse_dict, EeSymbolEllipse))
    )


def add_easyeda_arc(arc_data: str, ee_symbol: EeSymbol):
    arc_dict = dict(zip([f.name for f in fields(EeSymbolArc)], arc_data.split("~")[1:]))
    ee_symbol.arcs.append(EeSymbolArc(**convert_fields_to_types(arc_dict, EeSymbolArc)))


easyeda_handlers = {
    "P": add_easyeda_pin,
    "R": add_easyeda_rectangle,
    "E": add_easyeda_ellipse,
    "C": add_easyeda_circle,
    "A": add_easyeda_arc,
    "PL": add_easyeda_polyline,
    "PG": add_easyeda_polygon,
    "PT": add_easyeda_path,
    # "PI" : Pie, Elliptical arc seems to be not supported in Kicad
}


class EasyedaSymbolImporter:
    def __init__(self, easyeda_cp_cad_data: dict):
        self.input = easyeda_cp_cad_data
        self.output: EeSymbol = self.extract_easyeda_data(
            ee_data=easyeda_cp_cad_data,
            ee_data_info=easyeda_cp_cad_data["dataStr"]["head"]["c_para"],
        )

    def get_symbol(self) -> EeSymbol:
        return self.output

    def extract_easyeda_data(self, ee_data: dict, ee_data_info: dict) -> EeSymbol:
        # Try to get BBox from dataStr.BBox first (correct geometry bounds)
        # Fall back to head.x/y for backward compatibility
        bbox_data = ee_data["dataStr"].get("BBox", {})
        head_data = ee_data["dataStr"]["head"]

        # Use BBox.x/y if available, otherwise fall back to head.x/y
        bbox_x = _safe_float(bbox_data.get("x", head_data.get("x")))
        bbox_y = _safe_float(bbox_data.get("y", head_data.get("y")))
        bbox_width = _safe_float(bbox_data.get("width", 0.0))
        bbox_height = _safe_float(bbox_data.get("height", 0.0))

        new_ee_symbol = EeSymbol(
            info=EeSymbolInfo(
                name=ee_data_info["name"],
                prefix=ee_data_info["pre"],
                package=ee_data_info.get("package", ""),
                manufacturer=ee_data_info.get("BOM_Manufacturer", ""),
                datasheet=ee_data["lcsc"].get("url", ""),
                lcsc_id=ee_data["lcsc"].get("number", ""),
                jlc_id=ee_data_info.get("BOM_JLCPCB Part Class", ""),
            ),
            bbox=EeSymbolBbox(
                x=bbox_x,
                y=bbox_y,
                width=bbox_width,
                height=bbox_height,
            ),
        )

        for line in ee_data["dataStr"]["shape"]:
            designator = line.split("~")[0]
            if designator in easyeda_handlers:
                easyeda_handlers[designator](line, new_ee_symbol)
            else:
                logging.warning(f"Unknow symbol designator : {designator}")

        return new_ee_symbol


class EasyedaFootprintImporter:
    def __init__(self, easyeda_cp_cad_data: dict):
        self.input = easyeda_cp_cad_data
        self.output = self.extract_easyeda_data(
            ee_data_str=self.input["packageDetail"]["dataStr"],
            ee_data_info=self.input["packageDetail"]["dataStr"]["head"]["c_para"],
            is_smd=bool(self.input.get("SMT"))
            and "-TH_" not in self.input["packageDetail"]["title"],
        )

    def get_footprint(self):
        return self.output

    def extract_easyeda_data(
        self, ee_data_str: dict, ee_data_info: dict, is_smd: bool
    ) -> ee_footprint:
        new_ee_footprint = ee_footprint(
            info=EeFootprintInfo(
                name=ee_data_info["package"],
                fp_type="smd" if is_smd else "tht",
                model_3d_name=ee_data_info.get("3DModel", ""),
            ),
            bbox=EeFootprintBbox(
                x=_safe_float(ee_data_str["head"].get("x")),
                y=_safe_float(ee_data_str["head"].get("y")),
            ),
            model_3d=None,
        )

        for line in ee_data_str["shape"]:
            ee_designator = line.split("~")[0]
            ee_fields = line.split("~")[1:]

            if ee_designator == "PAD":
                ee_pad = EeFootprintPad(
                    **dict(
                        zip([f.name for f in fields(EeFootprintPad)], ee_fields[:18])
                    )
                )
                new_ee_footprint.pads.append(ee_pad)
            elif ee_designator == "TRACK":
                ee_track = EeFootprintTrack(
                    **dict(zip([f.name for f in fields(EeFootprintTrack)], ee_fields))
                )
                new_ee_footprint.tracks.append(ee_track)
            elif ee_designator == "HOLE":
                ee_hole = EeFootprintHole(
                    **dict(zip([f.name for f in fields(EeFootprintHole)], ee_fields))
                )
                new_ee_footprint.holes.append(ee_hole)
            elif ee_designator == "VIA":
                ee_via = EeFootprintVia(
                    **dict(zip([f.name for f in fields(EeFootprintVia)], ee_fields))
                )
                new_ee_footprint.vias.append(ee_via)
            elif ee_designator == "CIRCLE":
                ee_circle = EeFootprintCircle(
                    **dict(zip([f.name for f in fields(EeFootprintCircle)], ee_fields))
                )
                new_ee_footprint.circles.append(ee_circle)
            elif ee_designator == "ARC":
                ee_arc = EeFootprintArc(
                    **dict(zip([f.name for f in fields(EeFootprintArc)], ee_fields))
                )
                new_ee_footprint.arcs.append(ee_arc)
            elif ee_designator == "RECT":
                ee_rectangle = EeFootprintRectangle(
                    **dict(
                        zip([f.name for f in fields(EeFootprintRectangle)], ee_fields)
                    )
                )
                new_ee_footprint.rectangles.append(ee_rectangle)
            elif ee_designator == "TEXT":
                ee_text = EeFootprintText(
                    **dict(zip([f.name for f in fields(EeFootprintText)], ee_fields))
                )
                new_ee_footprint.texts.append(ee_text)
            elif ee_designator == "SVGNODE":
                new_ee_footprint.model_3d = Easyeda3dModelImporter(
                    easyeda_cp_cad_data=[line], download_raw_3d_model=False
                ).output

            elif ee_designator == "SOLIDREGION":
                ...
            else:
                logging.warning(f"Unknow footprint designator : {ee_designator}")

        return new_ee_footprint


# ------------------------------------------------------------------------------


class Easyeda3dModelImporter:
    def __init__(self, easyeda_cp_cad_data, download_raw_3d_model: bool):
        self.input = easyeda_cp_cad_data
        self.download_raw_3d_model = download_raw_3d_model
        self.output = self.create_3d_model()

    def create_3d_model(self) -> Union[Ee3dModel, None]:
        ee_data = (
            self.input["packageDetail"]["dataStr"]["shape"]
            if isinstance(self.input, dict)
            else self.input
        )

        if model_3d_info := self.get_3d_model_info(ee_data=ee_data):
            model_3d: Ee3dModel = self.parse_3d_model_info(info=model_3d_info)
            if self.download_raw_3d_model:
                model_3d.raw_obj = EasyedaApi().get_raw_3d_model_obj(uuid=model_3d.uuid)
                model_3d.step = EasyedaApi().get_step_3d_model(uuid=model_3d.uuid)
            return model_3d

        logging.warning("No 3D model available for this component")
        return None

    def get_3d_model_info(self, ee_data: str) -> dict:
        for line in ee_data:
            ee_designator = line.split("~")[0]
            if ee_designator == "SVGNODE":
                split_data = line.split("~")[1:]
                if split_data:
                    raw_json = split_data[0]
                    try:
                        parsed_json = json.loads(raw_json)
                        return parsed_json.get("attrs", {})
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to parse 3D model JSON: {e}")
                        return {}
        return {}

    def parse_3d_model_info(self, info: dict) -> Ee3dModel:
        return Ee3dModel(
            name=info["title"],
            uuid=info["uuid"],
            translation=Ee3dModelBase(
                x=_safe_float(
                    info["c_origin"].split(",")[0]
                    if "c_origin" in info and "," in info["c_origin"]
                    else "0"
                ),
                y=_safe_float(
                    info["c_origin"].split(",")[1]
                    if "c_origin" in info and len(info["c_origin"].split(",")) > 1
                    else "0"
                ),
                z=_safe_float(info.get("z", "0")),
            ),
            rotation=Ee3dModelBase(
                **dict(
                    zip(
                        [f.name for f in fields(Ee3dModelBase)],
                        info.get("c_rotation", "0,0,0").split(","),
                    )
                )
            ),
        )
