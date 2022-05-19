# Global imports
import json
import logging

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi
from easyeda2kicad.easyeda.parameters_easyeda import *


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
                x=float(ee_data["dataStr"]["head"]["x"]),
                y=float(ee_data["dataStr"]["head"]["y"]),
            ),
        )

        for line in ee_data["dataStr"]["shape"]:
            designator = line.split("~")[0]
            # For pins
            if designator == "P":
                ee_pin = self.extract_easyeda_pin(pin_data=line)
                new_ee_symbol.pins.append(self.tune_ee_pin(pin=ee_pin))
            # For rectangles
            elif designator == "R":
                ee_rectangle = self.extract_easyeda_rectangle(rectangle_data=line)
                new_ee_symbol.rectangles.append(
                    self.tune_ee_rectangle(rect=ee_rectangle)
                )
            # For polylines
            elif designator == "PL":
                ee_polyline = self.extract_easyeda_polyline(polyline_data=line)
                new_ee_symbol.polylines.append(
                    self.tune_ee_polyline(polyline=ee_polyline)
                )
            # For polygons
            elif designator == "PG":
                ee_polygon = self.extract_easyeda_polygon(polygon_data=line)
                new_ee_symbol.polygons.append(self.tune_ee_polygon(polygon=ee_polygon))
            # For paths
            elif designator == "PT":
                ee_path = self.extract_easyeda_path(path_data=line)
                new_ee_symbol.paths.append(self.tune_ee_path(path=ee_path))
            # For Pie
            elif designator == "PI":
                # Elliptical arc seems to be not supported in Kicad
                ...
            # For ellipse
            elif designator == "E":
                ...  # Ellipse seems to be not supported in Kicad
            # For arcs
            elif designator == "A":
                ...  # TODO
            else:
                logging.warning(f"Unknow symbol designator : {designator}")

        return new_ee_symbol

    # ---------------------------------------

    def extract_easyeda_pin(self, pin_data: str) -> EeSymbolPin:
        segments = pin_data.split("^^")
        ee_segments = [seg.split("~") for seg in segments]

        pin_settings = EeSymbolPinSettings(
            **dict(zip(EeSymbolPinSettings.__fields__, ee_segments[0][1:]))
        )
        pin_dot = EeSymbolPinDot(
            dot_x=float(ee_segments[1][0]), dot_y=float(ee_segments[1][1])
        )
        pin_path = EeSymbolPinPath(path=ee_segments[2][0], color=ee_segments[2][1])
        pin_name = EeSymbolPinName(
            **dict(zip(EeSymbolPinName.__fields__, ee_segments[3][:]))
        )

        pin_dot_bis = EeSymbolPinDotBis(
            is_displayed=ee_segments[5][0],
            circle_x=float(ee_segments[5][1]),
            circle_y=float(ee_segments[5][2]),
        )
        pin_clock = EeSymbolPinClock(
            is_displayed=ee_segments[6][0], path=ee_segments[6][1]
        )
        return EeSymbolPin(
            settings=pin_settings,
            pin_dot=pin_dot,
            pin_path=pin_path,
            name=pin_name,
            dot=pin_dot_bis,
            clock=pin_clock,
        )

    # ---------------------------------------

    def extract_easyeda_rectangle(self, rectangle_data: str) -> EeSymbolRectangle:
        ee_segment = rectangle_data.split("~")
        return EeSymbolRectangle(
            **dict(zip(EeSymbolRectangle.__fields__, ee_segment[1:]))
        )

    def extract_easyeda_polyline(self, polyline_data: str) -> EeSymbolPolyline:
        ee_segment = polyline_data.split("~")
        return EeSymbolPolyline(
            **dict(zip(EeSymbolPolyline.__fields__, ee_segment[1:]))
        )

    def extract_easyeda_polygon(self, polygon_data: str) -> EeSymbolPolygon:
        ee_segment = polygon_data.split("~")
        return EeSymbolPolygon(**dict(zip(EeSymbolPolygon.__fields__, ee_segment[1:])))

    def extract_easyeda_path(self, path_data: str) -> EeSymbolPath:
        ee_segment = path_data.split("~")
        return EeSymbolPath(**dict(zip(EeSymbolPath.__fields__, ee_segment[1:])))

    # ---------------------------------------

    def tune_ee_pin(self, pin: EeSymbolPin) -> EeSymbolPin:
        return pin

    def tune_ee_rectangle(self, rect: EeSymbolRectangle) -> EeSymbolRectangle:
        return rect

    def tune_ee_polyline(self, polyline: EeSymbolPolyline) -> EeSymbolPolyline:
        return polyline

    def tune_ee_polygon(self, polygon: EeSymbolPolygon) -> EeSymbolPolygon:
        return polygon

    def tune_ee_path(self, path: EeSymbolPath) -> EeSymbolPath:
        return path


# ------------------------------------------------------------------------------


class EasyedaFootprintImporter:
    def __init__(self, easyeda_cp_cad_data: dict):
        self.input = easyeda_cp_cad_data
        self.output = self.extract_easyeda_data(
            ee_data_str=self.input["packageDetail"]["dataStr"],
            ee_data_info=self.input["packageDetail"]["dataStr"]["head"]["c_para"],
        )

    def get_footprint(self):
        return self.output

    def extract_easyeda_data(self, ee_data_str: str, ee_data_info: str) -> ee_footprint:
        new_ee_footprint = ee_footprint(
            info=EeFootprintInfo(
                name=ee_data_info["package"],
                fp_type="smd" if "SMT" in ee_data_info else "tht",
                model_3d_name=ee_data_info.get("3DModel"),
            ),
            bbox=EeFootprintBbox(
                x=float(ee_data_str["head"]["x"]),
                y=float(ee_data_str["head"]["y"]),
            ),
            model_3d=None,
        )

        for line in ee_data_str["shape"]:

            ee_designator = line.split("~")[0]
            ee_fields = line.split("~")[1:]

            if ee_designator == "PAD":
                ee_pad = EeFootprintPad(
                    **dict(zip(EeFootprintPad.__fields__, ee_fields[:18]))
                )
                new_ee_footprint.pads.append(ee_pad)
            elif ee_designator == "TRACK":
                ee_track = EeFootprintTrack(
                    **dict(zip(EeFootprintTrack.__fields__, ee_fields))
                )
                new_ee_footprint.tracks.append(ee_track)
            elif ee_designator == "HOLE":
                ee_hole = EeFootprintHole(
                    **dict(zip(EeFootprintHole.__fields__, ee_fields))
                )
                new_ee_footprint.holes.append(ee_hole)
            elif ee_designator == "CIRCLE":
                ee_circle = EeFootprintCircle(
                    **dict(zip(EeFootprintCircle.__fields__, ee_fields))
                )
                new_ee_footprint.circles.append(ee_circle)
            elif ee_designator == "ARC":
                ee_arc = EeFootprintArc(
                    **dict(zip(EeFootprintArc.__fields__, ee_fields))
                )
                new_ee_footprint.arcs.append(ee_arc)
            elif ee_designator == "RECT":
                ee_rectangle = EeFootprintRectangle(
                    **dict(zip(EeFootprintRectangle.__fields__, ee_fields))
                )
                new_ee_footprint.rectangles.append(ee_rectangle)
            elif ee_designator == "TEXT":
                ee_text = EeFootprintText(
                    **dict(zip(EeFootprintText.__fields__, ee_fields))
                )
                new_ee_footprint.texts.append(ee_text)
            elif ee_designator == "SVGNODE":
                new_ee_footprint.model_3d = Easyeda3dModelImporter(
                    easyeda_cp_cad_data=[line]
                ).output

            elif ee_designator == "SOLIDREGION":
                ...
            else:
                logging.warning(f"Unknow footprint designator : {ee_designator}")

        return new_ee_footprint


# ------------------------------------------------------------------------------


class Easyeda3dModelImporter:
    def __init__(self, easyeda_cp_cad_data):
        self.input = easyeda_cp_cad_data
        self.output = self.create_3d_model()

    def create_3d_model(self) -> Union[Ee3dModel, None]:
        ee_data = (
            self.input["packageDetail"]["dataStr"]["shape"]
            if isinstance(self.input, dict)
            else self.input
        )

        if model_3d_info := self.get_3d_model_info(ee_data=ee_data):
            model_3d: Ee3dModel = self.parse_3d_model_info(info=model_3d_info)
            model_3d.raw_obj = EasyedaApi().get_raw_3d_model_obj(uuid=model_3d.uuid)
            return model_3d

        logging.warning("There is no 3D model for this component")
        return None

    def get_3d_model_info(self, ee_data: str) -> dict:
        for line in ee_data:
            ee_designator = line.split("~")[0]
            if ee_designator == "SVGNODE":
                raw_json = line.split("~")[1:][0]
                return json.loads(raw_json)["attrs"]
        return {}

    def parse_3d_model_info(self, info: dict) -> Ee3dModel:
        return Ee3dModel(
            name=info["title"],
            uuid=info["uuid"],
            translation=Ee3dModelBase(
                x=info["c_origin"].split(",")[0],
                y=info["c_origin"].split(",")[1],
                z=info["z"],
            ),
            rotation=Ee3dModelBase(
                **dict(zip(Ee3dModelBase.__fields__, info["c_rotation"].split(",")))
            ),
        )
