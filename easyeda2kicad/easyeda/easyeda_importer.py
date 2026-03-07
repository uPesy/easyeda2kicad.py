from __future__ import annotations

# Global imports
import json
import logging
from dataclasses import fields
from typing import Any, Union, get_args, get_origin, get_type_hints

__all__ = [
    "EasyedaSymbolImporter",
    "EasyedaFootprintImporter",
    "Easyeda3dModelImporter",
    "EeSymbol",
]


# Local imports
from .easyeda_api import EasyedaApi
from .parameters_easyeda import (
    _safe_bool,
    _safe_float,
    _safe_int,
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
    EeFootprint,
)


def _sanitize_component_name(name: str) -> str:
    """Clean up component name from EasyEDA API.

    Removes packaging suffixes that start with '(' or '[' (e.g. '(T', '(TR)',
    '[Cut tape]') and strips whitespace.  Returns the base component name.
    """
    for ch in ("(", "["):
        idx = name.find(ch)
        if idx >= 0:
            name = name[:idx]
    return name.strip()


def convert_fields_to_types(
    field_dict: dict[str, Any], dataclass_type: type
) -> dict[str, Any]:
    """
    Convert string values in field_dict to appropriate Python types based on
    the dataclass type annotations. Needed because EasyEDA API returns all
    field values as strings regardless of their intended type.
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

        origin = get_origin(field_type)
        if origin is Union:
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


def add_easyeda_pin(pin_data: str, ee_symbol: EeSymbol) -> None:
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


def add_easyeda_rectangle(rectangle_data: str, ee_symbol: EeSymbol) -> None:
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


def add_easyeda_polyline(polyline_data: str, ee_symbol: EeSymbol) -> None:
    polyline_dict = dict(
        zip(
            [f.name for f in fields(EeSymbolPolyline)],
            polyline_data.split("~")[1:],
        )
    )
    ee_symbol.polylines.append(
        EeSymbolPolyline(**convert_fields_to_types(polyline_dict, EeSymbolPolyline))
    )


def add_easyeda_polygon(polygon_data: str, ee_symbol: EeSymbol) -> None:
    polygon_dict = dict(
        zip(
            [f.name for f in fields(EeSymbolPolygon)],
            polygon_data.split("~")[1:],
        )
    )
    ee_symbol.polygons.append(
        EeSymbolPolygon(**convert_fields_to_types(polygon_dict, EeSymbolPolygon))
    )


def add_easyeda_path(path_data: str, ee_symbol: EeSymbol) -> None:
    path_dict = dict(
        zip([f.name for f in fields(EeSymbolPath)], path_data.split("~")[1:])
    )
    ee_symbol.paths.append(
        EeSymbolPath(**convert_fields_to_types(path_dict, EeSymbolPath))
    )


def add_easyeda_circle(circle_data: str, ee_symbol: EeSymbol) -> None:
    circle_dict = dict(
        zip([f.name for f in fields(EeSymbolCircle)], circle_data.split("~")[1:])
    )
    ee_symbol.circles.append(
        EeSymbolCircle(**convert_fields_to_types(circle_dict, EeSymbolCircle))
    )


def add_easyeda_ellipse(ellipse_data: str, ee_symbol: EeSymbol) -> None:
    ellipse_dict = dict(
        zip(
            [f.name for f in fields(EeSymbolEllipse)],
            ellipse_data.split("~")[1:],
        )
    )
    ee_symbol.ellipses.append(
        EeSymbolEllipse(**convert_fields_to_types(ellipse_dict, EeSymbolEllipse))
    )


def add_easyeda_arc(arc_data: str, ee_symbol: EeSymbol) -> None:
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
    def __init__(self, easyeda_cp_cad_data: dict[str, Any]):
        self.input = easyeda_cp_cad_data
        self.output: EeSymbol = self._extract(easyeda_cp_cad_data)

    def get_symbol(self) -> EeSymbol:
        return self.output

    @staticmethod
    def _shared_origin(
        subparts: list[dict[str, Any]],
    ) -> tuple[float, float] | None:
        """Derive the shared canvas origin from the first sub-part's head position.

        All sub-parts of a multi-unit symbol carry the same head.x/y value which
        EasyEDA uses as the common reference point.  Using this shared origin for
        every unit keeps their geometry aligned in KiCad.
        """
        if not subparts:
            return None
        head = subparts[0]["dataStr"]["head"]
        return (float(head.get("x") or 0), float(head.get("y") or 0))

    def _extract(self, ee_data: dict[str, Any]) -> EeSymbol:
        subparts: list[dict[str, Any]] = ee_data.get("subparts", [])
        shared_origin = self._shared_origin(subparts)

        symbol = self._extract_unit(
            ee_data=ee_data,
            ee_data_info=ee_data["dataStr"]["head"]["c_para"],
            shared_origin=shared_origin,
        )

        for subpart in subparts:
            symbol.sub_symbols.append(
                self._extract_unit(
                    ee_data=subpart,
                    ee_data_info=subpart["dataStr"]["head"]["c_para"],
                    shared_origin=shared_origin,
                )
            )

        return symbol

    def _extract_unit(
        self,
        ee_data: dict[str, Any],
        ee_data_info: dict[str, Any],
        shared_origin: tuple[float, float] | None,
    ) -> EeSymbol:
        bbox_data = ee_data["dataStr"].get("BBox", {})

        bbox_x = _safe_float(bbox_data.get("x"))
        bbox_y = _safe_float(bbox_data.get("y"))
        bbox_width = _safe_float(bbox_data.get("width"))
        bbox_height = _safe_float(bbox_data.get("height"))

        if shared_origin is not None:
            # Multi-unit symbol: all units use the same canvas origin so their
            # geometry stays aligned when placed together in a schematic.
            origin_x, origin_y = shared_origin
        elif bbox_width > 0 or bbox_height > 0:
            origin_x = bbox_x + bbox_width / 2.0
            origin_y = bbox_y + bbox_height / 2.0
        else:
            head_data = ee_data["dataStr"]["head"]
            origin_x = _safe_float(head_data.get("x")) or 0.0
            origin_y = _safe_float(head_data.get("y")) or 0.0

        new_ee_symbol = EeSymbol(
            info=EeSymbolInfo(
                name=_sanitize_component_name(ee_data_info["name"]),
                prefix=ee_data_info["pre"],
                package=ee_data_info.get("package", ""),
                manufacturer=ee_data_info.get("Manufacturer", "")
                or ee_data_info.get("BOM_Manufacturer", ""),
                mpn=ee_data_info.get("Manufacturer Part", "")
                or ee_data_info.get("BOM_Manufacturer Part", ""),
                datasheet=ee_data.get("lcsc", {}).get("url", ""),
                lcsc_id=ee_data.get("lcsc", {}).get("number", ""),
                keywords=" ".join(ee_data.get("tags", [])),
                description=ee_data.get("description", ""),
            ),
            bbox=EeSymbolBbox(
                x=origin_x,
                y=origin_y,
                width=bbox_width,
                height=bbox_height,
            ),
        )

        for line in ee_data["dataStr"]["shape"]:
            designator = line.split("~")[0]
            if designator in easyeda_handlers:
                easyeda_handlers[designator](line, new_ee_symbol)
            else:
                logging.warning(f"Unknown symbol designator: {designator}")

        return new_ee_symbol


class EasyedaFootprintImporter:
    def __init__(self, easyeda_cp_cad_data: dict[str, Any]):
        self.input = easyeda_cp_cad_data
        _c_para = self.input["packageDetail"]["dataStr"]["head"]["c_para"]
        # Mirror smt-gl-engine.js: i.tht = n.customData?.jlcPara?.assemblyProcess
        # Primary source: customData.jlcPara.assemblyProcess ("SMT" / "THT").
        # Fallback: top-level SMT flag + title heuristic for older API responses.
        _assembly = (
            self.input.get("customData", {})
            .get("jlcPara", {})
            .get("assemblyProcess", "")
        )
        if _assembly:
            _is_smd = _assembly.upper() == "SMT"
        else:
            _is_smd = (
                bool(self.input.get("SMT"))
                and "-TH_" not in self.input["packageDetail"]["title"]
            )

        self.output = self.extract_easyeda_data(
            ee_data_str=self.input["packageDetail"]["dataStr"],
            ee_data_info=_c_para,
            is_smd=_is_smd,
            lcsc_id=self.input.get("lcsc", {}).get("number", ""),
            manufacturer=_c_para.get("Manufacturer", "")
            or _c_para.get("BOM_Manufacturer", ""),
            mpn=_c_para.get("Manufacturer Part", "")
            or _c_para.get("BOM_Manufacturer Part", ""),
        )

    def get_footprint(self) -> EeFootprint:
        return self.output

    def extract_easyeda_data(
        self,
        ee_data_str: dict[str, Any],
        ee_data_info: dict[str, Any],
        is_smd: bool,
        lcsc_id: str = "",
        manufacturer: str = "",
        mpn: str = "",
    ) -> EeFootprint:
        new_ee_footprint = EeFootprint(
            info=EeFootprintInfo(
                name=ee_data_info["package"],
                fp_type="smd" if is_smd else "tht",
                model_3d_name=ee_data_info.get("3DModel", ""),
                lcsc_id=lcsc_id,
                manufacturer=manufacturer,
                mpn=mpn,
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
                # Mirror smt-gl-engine.js _I(): canvas.split("~")[16] and [17]
                # are the authoritative canvas origin. Fall back to head.x/y
                # if the canvas string is absent or too short.
                _canvas_parts = ee_data_str.get("canvas", "").split("~")
                if len(_canvas_parts) > 17:
                    _cox = _safe_float(_canvas_parts[16])
                    _coy = _safe_float(_canvas_parts[17])
                else:
                    _cox = _safe_float(ee_data_str["head"].get("x"))
                    _coy = _safe_float(ee_data_str["head"].get("y"))
                new_ee_footprint.model_3d = Easyeda3dModelImporter(
                    easyeda_cp_cad_data=[line],
                    download_raw_3d_model=False,
                    canvas_origin_x=_cox,
                    canvas_origin_y=_coy,
                ).output

            elif ee_designator == "SOLIDREGION":
                pass  # Not yet implemented; see KiFootprintSolidRegion
            else:
                logging.warning(f"Unknown footprint designator: {ee_designator}")

        return new_ee_footprint


# ------------------------------------------------------------------------------


class Easyeda3dModelImporter:
    # EasyEDA canvas scale: 1 canvas-unit = 0.254 mm (confirmed from smt-gl-engine.js)
    _CANVAS_SCALE = 0.254
    # Outline-fix threshold from smt-gl-engine.js: if |outline_centre - c_origin| > 0.1mm
    _FIX_THRESHOLD = 0.1

    def __init__(
        self,
        easyeda_cp_cad_data: dict[str, Any] | list[str],
        download_raw_3d_model: bool,
        api: EasyedaApi | None = None,
        canvas_origin_x: float = 0.0,
        canvas_origin_y: float = 0.0,
    ):
        self.input = easyeda_cp_cad_data
        self.download_raw_3d_model = download_raw_3d_model
        self.api = api
        self.canvas_origin_x = canvas_origin_x
        self.canvas_origin_y = canvas_origin_y
        self.output = self.create_3d_model()

    def create_3d_model(self) -> Ee3dModel | None:
        ee_data = (
            self.input["packageDetail"]["dataStr"]["shape"]
            if isinstance(self.input, dict)
            else self.input
        )

        if model_3d_info := self.get_3d_model_info(ee_data=ee_data):
            model_3d: Ee3dModel = self.parse_3d_model_info(node=model_3d_info)
            if self.download_raw_3d_model:
                api = self.api or EasyedaApi()
                model_3d.raw_obj = api.get_raw_3d_model_obj(uuid=model_3d.uuid)
                model_3d.step = api.get_step_3d_model(uuid=model_3d.uuid)
            return model_3d

        logging.warning("No 3D model available for this component")
        return None

    def get_3d_model_info(self, ee_data: list[str]) -> dict[str, Any]:
        for line in ee_data:
            ee_designator = line.split("~")[0]
            if ee_designator == "SVGNODE":
                split_data = line.split("~")[1:]
                if split_data:
                    raw_json = split_data[0]
                    try:
                        parsed_json: dict[str, Any] = json.loads(raw_json)
                        # Return full node so parse_3d_model_info can access childNodes
                        return parsed_json
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to parse 3D model JSON: {e}")
                        return {}
        return {}

    def _outline_centre_mm(self, node: dict[str, Any]) -> tuple[float, float] | None:
        """Compute 2D outline bbox centre in mm, mirroring smt-gl-engine.js logic.

        Returns (cx_mm, cy_mm) or None if no childNode points are found.
        """
        xs: list[float] = []
        ys: list[float] = []
        ox, oy = self.canvas_origin_x, self.canvas_origin_y
        scale = self._CANVAS_SCALE
        for child in node.get("childNodes", []):
            pts = child.get("attrs", {}).get("points", "").split()
            for i in range(0, len(pts) - 1, 2):
                xs.append((_safe_float(pts[i]) - ox) * scale)
                ys.append(-(_safe_float(pts[i + 1]) - oy) * scale)
        if not xs:
            return None
        return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)

    def parse_3d_model_info(self, node: dict[str, Any]) -> Ee3dModel:
        info = node.get("attrs", {})
        scale = self._CANVAS_SCALE
        ox, oy = self.canvas_origin_x, self.canvas_origin_y

        co = info.get("c_origin", "0,0").split(",")
        c_ox = _safe_float(co[0] if co else "0")
        c_oy = _safe_float(co[1] if len(co) > 1 else "0")

        # Primary offset: (c_origin - canvas_origin) * scale, Y negated
        # Matches smt-gl-engine.js: f(b,x) = [(b - canvas_x)*e, -(x - canvas_y)*e]
        tx = (c_ox - ox) * scale
        ty = -(c_oy - oy) * scale
        tz = _safe_float(info.get("z", "0")) * scale

        # Outline-centre correction (smt-gl-engine.js: if |centre - offset| > 0.1mm → use centre)
        outline = self._outline_centre_mm(node)
        if outline is not None:
            out_x, out_y = outline
            if (
                abs(out_x - tx) > self._FIX_THRESHOLD
                or abs(out_y - ty) > self._FIX_THRESHOLD
            ):
                logging.debug(
                    f"3D outline fix for {info.get('uuid', '?')}: "
                    f"({tx:.3f},{ty:.3f}) → ({out_x:.3f},{out_y:.3f})"
                )
                tx, ty = out_x, out_y

        return Ee3dModel(
            name=info["title"],
            uuid=info["uuid"],
            translation=Ee3dModelBase(x=tx, y=ty, z=tz),
            rotation=Ee3dModelBase(
                **dict(
                    zip(
                        [f.name for f in fields(Ee3dModelBase)],
                        info.get("c_rotation", "0,0,0").split(","),
                    )
                )
            ),
        )
