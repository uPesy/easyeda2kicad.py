# Global imports
import json
import logging

from .easyeda_api import EasyedaApi
from .parameters_easyeda import *


# Safe conversion helpers
def _safe_float(value, default=0.0):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def add_easyeda_pin(pin_data: str, ee_symbol: EeSymbol):
    segments = pin_data.split("^^")
    ee_segments = [seg.split("~") for seg in segments]

    # Extract the correct KiCad pin number from segment 4[4]
    correct_pin_number = None
    if len(ee_segments) > 4 and len(ee_segments[4]) > 4:
        correct_pin_number = ee_segments[4][4]

    from dataclasses import fields

    pin_settings_data = (
        ee_segments[0][1:] if len(ee_segments) > 0 and len(ee_segments[0]) > 1 else []
    )
    pin_settings_fields = [f.name for f in fields(EeSymbolPinSettings)]
    pin_settings = EeSymbolPinSettings(
        **dict(zip(pin_settings_fields, pin_settings_data))
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
    pin_name = EeSymbolPinName(
        **dict(
            zip(
                [f.name for f in fields(EeSymbolPinName)],
                ee_segments[3][:] if len(ee_segments) > 3 else [],
            )
        )
    )

    pin_dot_bis = EeSymbolPinDotBis(
        is_displayed=(
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
        is_displayed=(
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

    # Handle EasyEDA format inconsistency: sometimes has empty fields at index 2,3
    # Format: R~x~y~(empty)~(empty)~width~height~...
    # We need to map: x, y, width, height correctly
    if len(parts) >= 7 and parts[2] == '' and parts[3] == '':
        # Move width/height from position 4,5 to 2,3
        parts = [parts[0], parts[1], parts[4], parts[5]] + parts[6:]

    ee_symbol.rectangles.append(
        EeSymbolRectangle(
            **dict(
                zip(
                    [f.name for f in fields(EeSymbolRectangle)],
                    parts,
                )
            )
        )
    )


def add_easyeda_polyline(polyline_data: str, ee_symbol: EeSymbol):
    ee_symbol.polylines.append(
        EeSymbolPolyline(
            **dict(
                zip(
                    [f.name for f in fields(EeSymbolPolyline)],
                    polyline_data.split("~")[1:],
                )
            )
        )
    )


def add_easyeda_polygon(polygon_data: str, ee_symbol: EeSymbol):
    ee_symbol.polygons.append(
        EeSymbolPolygon(
            **dict(
                zip(
                    [f.name for f in fields(EeSymbolPolygon)],
                    polygon_data.split("~")[1:],
                )
            )
        )
    )


def add_easyeda_path(path_data: str, ee_symbol: EeSymbol):
    ee_symbol.paths.append(
        EeSymbolPath(
            **dict(
                zip([f.name for f in fields(EeSymbolPath)], path_data.split("~")[1:])
            )
        )
    )


def add_easyeda_circle(circle_data: str, ee_symbol: EeSymbol):
    ee_symbol.circles.append(
        EeSymbolCircle(
            **dict(
                zip(
                    [f.name for f in fields(EeSymbolCircle)], circle_data.split("~")[1:]
                )
            )
        )
    )


def add_easyeda_ellipse(ellipse_data: str, ee_symbol: EeSymbol):
    ee_symbol.ellipses.append(
        EeSymbolEllipse(
            **dict(
                zip(
                    [f.name for f in fields(EeSymbolEllipse)],
                    ellipse_data.split("~")[1:],
                )
            )
        )
    )


def add_easyeda_arc(arc_data: str, ee_symbol: EeSymbol):
    ee_symbol.arcs.append(
        EeSymbolArc(
            **dict(zip([f.name for f in fields(EeSymbolArc)], arc_data.split("~")[1:]))
        )
    )


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
        new_ee_symbol = EeSymbol(
            info=EeSymbolInfo(
                name=ee_data_info["name"],
                prefix=ee_data_info["pre"],
                package=ee_data_info.get("package", None),
                manufacturer=ee_data_info.get("BOM_Manufacturer", None),
                datasheet=ee_data["lcsc"].get("url", None),
                lcsc_id=ee_data["lcsc"].get("number", None),
                jlc_id=ee_data_info.get("BOM_JLCPCB Part Class", None),
            ),
            bbox=EeSymbolBbox(
                x=_safe_float(ee_data["dataStr"]["head"].get("x")),
                y=_safe_float(ee_data["dataStr"]["head"].get("y")),
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
            is_smd=self.input.get("SMT")
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
                model_3d_name=ee_data_info.get("3DModel"),
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
                x=(
                    info["c_origin"].split(",")[0]
                    if "c_origin" in info and "," in info["c_origin"]
                    else "0"
                ),
                y=(
                    info["c_origin"].split(",")[1]
                    if "c_origin" in info and len(info["c_origin"].split(",")) > 1
                    else "0"
                ),
                z=info.get("z", "0"),
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
