# Global import
# Global imports
import json
from unicodedata import name

from easyeda2kicad.easyeda.easyeda_api import easyeda_api
from easyeda2kicad.easyeda.parameters_easyeda import *


class easyeda_symbol_importer:
    def __init__(self, easyeda_cp_cad_data):
        self.input = easyeda_cp_cad_data
        self.output: ee_symbol = self.extract_easyeda_data(
            ee_data=easyeda_cp_cad_data,
            ee_data_info=easyeda_cp_cad_data["dataStr"]["head"]["c_para"],
        )

    def get_symbol(self):
        return self.output

    def extract_easyeda_data(self, ee_data: dict, ee_data_info: dict):
        new_ee_symbol = ee_symbol(
            info=ee_symbol_info(
                name=ee_data_info["name"],
                prefix=ee_data_info["pre"],
                package=ee_data_info.get("package", None),
                manufacturer=ee_data_info.get("BOM_Manufacturer", None),
                datasheet=ee_data["lcsc"].get("url", None),
                lcsc_id=ee_data["lcsc"].get("number", None),
                jlc_id=ee_data_info.get("BOM_JLCPCB Part Class", None),
            ),
            bbox=ee_symbol_bbox(
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
                print(f"\t[-] Unknow symbol designator : {designator}")

        return new_ee_symbol

    # ---------------------------------------

    def extract_easyeda_pin(self, pin_data: str):
        segments = pin_data.split("^^")
        ee_segments = [seg.split("~") for seg in segments]

        pin_settings = ee_symbol_pin_settings(
            **dict(zip(ee_symbol_pin_settings.__fields__, ee_segments[0][1:]))
        )
        pin_dot = ee_symbol_pin_dot(
            dot_x=float(ee_segments[1][0]), dot_y=float(ee_segments[1][1])
        )
        pin_path = ee_symbol_pin_path(path=ee_segments[2][0], color=ee_segments[2][1])
        pin_name = ee_symbol_pin_name(
            **dict(zip(ee_symbol_pin_name.__fields__, ee_segments[3][:]))
        )

        pin_dot_bis = ee_symbol_pin_dot_bis(
            is_displayed=ee_segments[5][0],
            circle_x=float(ee_segments[5][1]),
            circle_y=float(ee_segments[5][2]),
        )
        pin_clock = ee_symbol_pin_clock(
            is_displayed=ee_segments[6][0], path=ee_segments[6][1]
        )
        return ee_symbol_pin(
            settings=pin_settings,
            pin_dot=pin_dot,
            pin_path=pin_path,
            name=pin_name,
            dot=pin_dot_bis,
            clock=pin_clock,
        )

    # ---------------------------------------

    def extract_easyeda_rectangle(self, rectangle_data: str):
        ee_segment = rectangle_data.split("~")
        return ee_symbol_rectangle(
            **dict(zip(ee_symbol_rectangle.__fields__, ee_segment[1:]))
        )

    def extract_easyeda_polyline(self, polyline_data: str):
        ee_segment = polyline_data.split("~")
        return ee_symbol_polyline(
            **dict(zip(ee_symbol_polyline.__fields__, ee_segment[1:]))
        )

    def extract_easyeda_polygon(self, polygon_data: str):
        ee_segment = polygon_data.split("~")
        return ee_symbol_polygon(
            **dict(zip(ee_symbol_polygon.__fields__, ee_segment[1:]))
        )

    def extract_easyeda_path(self, path_data: str):
        ee_segment = path_data.split("~")
        return ee_symbol_path(**dict(zip(ee_symbol_path.__fields__, ee_segment[1:])))

    # ---------------------------------------

    def tune_ee_pin(self, pin: ee_symbol_pin):
        pin.settings.rotation = (
            pin.settings.rotation if pin.settings.rotation != "" else "0"
        )
        pin.settings.type = (
            easyeda_pin_type(int(pin.settings.type)).name
            if pin.settings.type != ""
            else "unspecified"
        )
        pin.pin_path.path = pin.pin_path.path.replace("v", "h")
        pin.name.text = pin.name.text.replace(" ", "")
        return pin

    def tune_ee_rectangle(self, rect: ee_symbol_rectangle):
        return rect

    def tune_ee_polyline(self, polyline: ee_symbol_polyline):
        return polyline

    def tune_ee_polygon(self, polygon: ee_symbol_polygon):
        return polygon

    def tune_ee_path(self, path: ee_symbol_path):
        return path

    # ---------------------------------------


# ------------------------------------------------------------------------------


class easyeda_footprint_importer:
    def __init__(self, easyeda_cp_cad_data):
        self.input = easyeda_cp_cad_data
        self.output = self.extract_easyeda_data(
            ee_data_str=self.input["packageDetail"]["dataStr"],
            ee_data_info=self.input["packageDetail"]["dataStr"]["head"]["c_para"],
        )

    def get_footprint(self):
        return self.output

    def extract_easyeda_data(self, ee_data_str: str, ee_data_info: str):
        new_ee_footprint = ee_footprint(
            info=ee_footprint_info(
                name=ee_data_info["package"],
                fp_type="smd" if "SMT" in ee_data_info else "tht",
                model_3d_name=ee_data_info["3DModel"],
            ),
            bbox=ee_footprint_bbox(
                x=float(ee_data_str["head"]["x"]),
                y=float(ee_data_str["head"]["y"]),
            ),
            model_3d=None,
        )

        for line in ee_data_str["shape"]:

            ee_designator = line.split("~")[0]
            ee_fields = line.split("~")[1:]

            if ee_designator == "PAD":
                ee_pad = ee_footprint_pad(
                    **dict(zip(ee_footprint_pad.__fields__, ee_fields[:18]))
                )
                new_ee_footprint.pads.append(ee_pad)
            elif ee_designator == "TRACK":
                ee_track = ee_footprint_track(
                    **dict(zip(ee_footprint_track.__fields__, ee_fields))
                )
                new_ee_footprint.tracks.append(ee_track)
            elif ee_designator == "HOLE":
                ee_hole = ee_footprint_hole(
                    **dict(zip(ee_footprint_hole.__fields__, ee_fields))
                )
                new_ee_footprint.holes.append(ee_hole)
            elif ee_designator == "CIRCLE":
                ee_circle = ee_footprint_circle(
                    **dict(zip(ee_footprint_circle.__fields__, ee_fields))
                )
                new_ee_footprint.circles.append(ee_circle)
            elif ee_designator == "ARC":
                ee_arc = ee_footprint_arc(
                    **dict(zip(ee_footprint_arc.__fields__, ee_fields))
                )
                new_ee_footprint.arcs.append(ee_arc)
            elif ee_designator == "RECT":
                ee_rectangle = ee_footprint_rectangle(
                    **dict(zip(ee_footprint_rectangle.__fields__, ee_fields))
                )
                new_ee_footprint.rectangles.append(ee_rectangle)
            elif ee_designator == "TEXT":
                ee_text = ee_footprint_text(
                    **dict(zip(ee_footprint_text.__fields__, ee_fields))
                )
                new_ee_footprint.texts.append(ee_text)
            elif ee_designator == "SVGNODE":
                new_ee_footprint.model_3d = easyeda_3d_model_importer(
                    easyeda_cp_cad_data=[line]
                ).output

            elif ee_designator == "SOLIDREGION":
                ...
            else:
                print(f"\t[-] Unknow footprint designator : {ee_designator}")

        return new_ee_footprint


# ------------------------------------------------------------------------------


class easyeda_3d_model_importer:
    def __init__(self, easyeda_cp_cad_data):
        self.input = easyeda_cp_cad_data
        self.output = self.create_3d_model()

    def create_3d_model(self):
        ee_data = (
            self.input["packageDetail"]["dataStr"]["shape"]
            if isinstance(self.input, dict)
            else self.input
        )
        model_3d: ee_3d_model = self.parse_3d_model_info(
            info=self.get_3d_model_info(ee_data=ee_data)
        )
        model_3d.raw_obj = easyeda_api().get_raw_3d_model_obj(uuid=model_3d.uuid)
        return model_3d

    def get_3d_model_info(self, ee_data: str) -> dict:
        for line in ee_data:
            ee_designator = line.split("~")[0]
            if ee_designator == "SVGNODE":
                raw_json = line.split("~")[1:][0]
                return json.loads(raw_json)["attrs"]
        return {}

    def parse_3d_model_info(self, info: dict) -> ee_3d_model:
        return ee_3d_model(
            name=info["title"],
            uuid=info["uuid"],
            translation=ee_3d_model_base(
                x=info["c_origin"].split(",")[0],
                y=info["c_origin"].split(",")[1],
                z=info["z"],
            ),
            rotation=ee_3d_model_base(
                **dict(zip(ee_3d_model_base.__fields__, info["c_rotation"].split(",")))
            ),
        )
