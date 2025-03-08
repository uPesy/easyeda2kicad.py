# Global imports
import json
import logging

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi
from easyeda2kicad.easyeda.parameters_easyeda import *


def shift_paths_x(paths: str, add_value: float):
    numbers = list(map(float, paths.split()))

    # Add `add_value` to every second number
    for i in range(0, len(numbers), 2):  # Start from index 1 and step by 2
        numbers[i] += add_value

    # Convert back to a space-separated string
    return " ".join(map(str, numbers))


def add_easyeda_pin(pin_data: str, ee_symbol: EeSymbol, shiftX=0):
    segments = pin_data.split("^^")
    ee_segments = [seg.split("~") for seg in segments]

    pin_settings = EeSymbolPinSettings(
        **dict(zip(EeSymbolPinSettings.__fields__, ee_segments[0][1:]))
    )
    pin_settings.pos_x+=shiftX

    pin_dot = EeSymbolPinDot(
        dot_x=float(ee_segments[1][0])+shiftX, dot_y=float(ee_segments[1][1])
    )
    pin_path = EeSymbolPinPath(path=ee_segments[2][0], color=ee_segments[2][1])
    pin_name = EeSymbolPinName(
        **dict(zip(EeSymbolPinName.__fields__, ee_segments[3][:]))
    )
    pin_name.pos_x+=shiftX

    pin_dot_bis = EeSymbolPinDotBis(
        is_displayed=ee_segments[5][0],
        circle_x=float(ee_segments[5][1])+shiftX,
        circle_y=float(ee_segments[5][2]),
    )
    pin_clock = EeSymbolPinClock(is_displayed=ee_segments[6][0], path=ee_segments[6][1])

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


def add_easyeda_rectangle(rectangle_data: str, ee_symbol: EeSymbol, shiftX=0):
    rectangle = EeSymbolRectangle(
        **dict(zip(EeSymbolRectangle.__fields__, rectangle_data.split("~")[1:]))
    )
    rectangle.pos_x+=shiftX
    ee_symbol.rectangles.append(rectangle)


def add_easyeda_polyline(polyline_data: str, ee_symbol: EeSymbol, shiftX=0):
    polyline = EeSymbolPolyline(
        **dict(zip(EeSymbolPolyline.__fields__, polyline_data.split("~")[1:]))
    )
    polyline.points = shift_paths_x(polyline.points, shiftX)
    ee_symbol.polylines.append(polyline)


def add_easyeda_polygon(polygon_data: str, ee_symbol: EeSymbol, shiftX=0):
    polygon = EeSymbolPolygon(
        **dict(zip(EeSymbolPolygon.__fields__, polygon_data.split("~")[1:]))
    )
    polygon.points = shift_paths_x(polygon.points, shiftX)
    ee_symbol.polygons.append(polygon)


def add_easyeda_path(path_data: str, ee_symbol: EeSymbol, shiftX=0):
    path = EeSymbolPath(**dict(zip(EeSymbolPath.__fields__, path_data.split("~")[1:])))
    path.paths = shift_paths_x(path.paths, shiftX)
    ee_symbol.paths.append(path)



def add_easyeda_circle(circle_data: str, ee_symbol: EeSymbol, shiftX=0):
    circle = EeSymbolCircle(
        **dict(zip(EeSymbolCircle.__fields__, circle_data.split("~")[1:]))
    )
    circle.center_x+=shiftX
    ee_symbol.circles.append(circle)


def add_easyeda_ellipse(ellipse_data: str, ee_symbol: EeSymbol, shiftX=0):
    ellipse = EeSymbolEllipse(
        **dict(zip(EeSymbolEllipse.__fields__, ellipse_data.split("~")[1:]))
    )
    ellipse.center_x+=shiftX
    ee_symbol.ellipses.append(ellipse)

def add_easyeda_arc(arc_data: str, ee_symbol: EeSymbol, shiftX=0):
    arc=EeSymbolArc(**dict(zip(EeSymbolArc.__fields__, arc_data.split("~")[1:])))
    arc.arcs[-1]+=shiftX
    ee_symbol.arcs.append(arc)



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
                x=float(ee_data["dataStr"]["head"]["x"]),
                y=float(ee_data["dataStr"]["head"]["y"]),
            ),
        )

        if len(ee_data["dataStr"]["shape"]) == 0:
            symbol_descriptors = []
            for symbol in ee_data["subparts"]:
                symbol_descriptors.append(symbol["dataStr"])
        else:
            symbol_descriptors=ee_data["dataStr"]

        if len(symbol_descriptors) > 0:
            shiftX = 0
            for descriptor in symbol_descriptors:
                for line in descriptor["shape"]:
                    designator = line.split("~")[0]
                    if designator in easyeda_handlers:
                        easyeda_handlers[designator](line, new_ee_symbol, shiftX=shiftX)
                    else:
                        logging.warning(f"Unknow symbol designator : {designator}")
                shiftX += descriptor["BBox"]["width"] * 1.5

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
            elif ee_designator == "VIA":
                ee_via = EeFootprintVia(
                    **dict(zip(EeFootprintVia.__fields__, ee_fields))
                )
                new_ee_footprint.vias.append(ee_via)
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
