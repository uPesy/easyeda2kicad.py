# Global import
# Global imports
import json

# Local imports
# Local import
from core.easyeda.parameters_easyeda import *


class easyeda_symbol_importer:
    def __init__(self, easyeda_cp_cad_data):
        self.ee_data = easyeda_cp_cad_data
        self.ee_data_info = easyeda_cp_cad_data["dataStr"]["head"]["c_para"]

    def get_symbol(self):
        return self.extract_easyeda_data()

    def extract_easyeda_data(self):
        new_ee_symbol = ee_symbol(
            info=ee_symbol_info(
                name=self.ee_data_info["name"],
                prefix=self.ee_data_info["pre"],
                package=self.ee_data_info["package"]
                if "package" in self.ee_data_info
                else None,
                manufacturer=self.ee_data_info["BOM_Manufacturer"]
                if "BOM_Manufacturer" in self.ee_data_info
                else None,
                datasheet=self.ee_data["lcsc"]["url"]
                if "url" in self.ee_data["lcsc"]
                else None,
                lcsc_id=self.ee_data["lcsc"]["number"]
                if "number" in self.ee_data["lcsc"]
                else None,
                jlc_id=self.ee_data_info["BOM_JLCPCB Part Class"]
                if "BOM_JLCPCB Part Class" in self.ee_data_info
                else None,
            ),
            bbox=ee_symbol_bbox(
                x=float(self.ee_data["dataStr"]["head"]["x"]),
                y=float(self.ee_data["dataStr"]["head"]["y"]),
            ),
        )

        for line in self.ee_data["dataStr"]["shape"]:
            designator = line.split("~")[0]
            # Pour les pins
            if designator == "P":
                ee_pin = self.extract_easyeda_pin(pin_data=line)
                new_ee_symbol.pins.append(self.tune_ee_pin(pin=ee_pin))
            # Pour les rectangles
            elif designator == "R":
                ee_rectangle = self.extract_easyeda_rectangle(pin_data=line)
                new_ee_symbol.rectangles.append(
                    self.tune_ee_rectangle(rect=ee_rectangle)
                )
            # Pour les polylines
            elif designator == "PL":
                ee_polyline = self.extract_easyeda_polyline(pin_data=line)
                new_ee_symbol.polylines.append(
                    self.tune_ee_polyline(polyline=ee_polyline)
                )
            # Pour les ellipse
            elif designator == "E":
                ...  # TODO
            # Pour les arcs
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

    def extract_easyeda_rectangle(self, pin_data: str):
        ee_segment = pin_data.split("~")
        return ee_symbol_rectangle(
            **dict(zip(ee_symbol_rectangle.__fields__, ee_segment[1:]))
        )

    # ---------------------------------------

    def extract_easyeda_polyline(self, pin_data: str):
        ee_segment = pin_data.split("~")
        return ee_symbol_polyline(
            **dict(zip(ee_symbol_polyline.__fields__, ee_segment[1:]))
        )

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

    # ---------------------------------------


# ------------------------------------------------------------------------------


class easyeda_footprint_importer:
    def __init__(self, easyeda_cp_cad_data):
        self.ee_data = easyeda_cp_cad_data
        self.ee_data_str = easyeda_cp_cad_data["packageDetail"]["dataStr"]
        self.ee_data_info = easyeda_cp_cad_data["packageDetail"]["dataStr"]["head"][
            "c_para"
        ]

    def get_footprint(self):
        self.easyeda_footprint_lib = self.extract_easyeda_data()
        return self.easyeda_footprint_lib

    def extract_easyeda_data(self):
        new_ee_footprint = ee_footprint(
            info=ee_footprint_info(
                name=self.ee_data_info["package"],
                fp_type="smd" if "SMT" in self.ee_data_info else "tht",
            ),
            bbox=ee_footprint_bbox(
                x=float(self.ee_data_str["head"]["x"]),
                y=float(self.ee_data_str["head"]["y"]),
            ),
        )

        for line in self.ee_data_str["shape"]:

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
            elif ee_designator == "SOLIDREGION":
                ...
            elif ee_designator == "SVGNODE":
                ...
            else:
                print(f"\t[-] Unknow footprint designator : {ee_designator}")

        return new_ee_footprint
