"""Export EasyEDA components to an Eagle .lbr library file.

Eagle libraries store symbols (schematic), packages (footprint),
and devicesets (linking a symbol to a package) in a single XML file.
3D models are handled by Fusion 360 online and are not supported here.
"""

# Global imports
import logging
import xml.etree.ElementTree as ET
from collections import Counter
from math import isnan
from typing import Dict, List, Optional, Union

from easyeda2kicad.easyeda.parameters_easyeda import (
    EasyedaPinType,
    EeFootprint,
    EeSymbol,
    EeSymbolPolygon,
)

# ─── Constants ──────────────────────────────────────────────────────────────────

EAGLE_VERSION = "9.6.2"

# EasyEDA pin type → Eagle pin direction attribute
EE_PIN_TYPE_TO_EAGLE_DIR: Dict[EasyedaPinType, str] = {
    EasyedaPinType.unspecified: "pas",
    EasyedaPinType._input: "in",
    EasyedaPinType.output: "out",
    EasyedaPinType.bidirectional: "io",
    EasyedaPinType.power: "pwr",
}

# EasyEDA footprint layer_id → Eagle layer number
EE_FP_LAYER_TO_EAGLE: Dict[int, int] = {
    1: 1,  # Top copper
    2: 16,  # Bottom copper
    3: 21,  # Top silkscreen  → tPlace
    4: 22,  # Bottom silkscreen → bPlace
    5: 31,  # Top paste → tCream
    6: 32,  # Bottom paste → bCream
    7: 29,  # Top solder mask → tStop
    8: 30,  # Bottom solder mask → bStop
    10: 20,  # Edge.Cuts → Dimension
    11: 20,  # Edge.Cuts → Dimension
    12: 48,  # Cmts.User → Document
    13: 51,  # F.Fab → tDocu
    14: 52,  # B.Fab → bDocu
    15: 48,  # Dwgs.User → Document
    101: 51,  # F.Fab → tDocu
}

# Standard Eagle layer definitions: (number, name, color, fill, visible, active)
EAGLE_LAYERS = [
    (1, "Top", 4, 1, "yes", "yes"),
    (2, "Route2", 16, 1, "no", "yes"),
    (3, "Route3", 17, 1, "no", "yes"),
    (4, "Route4", 18, 1, "no", "yes"),
    (5, "Route5", 19, 1, "no", "yes"),
    (6, "Route6", 25, 1, "no", "yes"),
    (7, "Route7", 26, 1, "no", "yes"),
    (8, "Route8", 27, 1, "no", "yes"),
    (9, "Route9", 28, 1, "no", "yes"),
    (10, "Route10", 29, 1, "no", "yes"),
    (11, "Route11", 30, 1, "no", "yes"),
    (12, "Route12", 20, 1, "no", "yes"),
    (13, "Route13", 21, 1, "no", "yes"),
    (14, "Route14", 22, 1, "no", "yes"),
    (15, "Route15", 23, 1, "no", "yes"),
    (16, "Bottom", 1, 1, "yes", "yes"),
    (17, "Pads", 2, 1, "yes", "yes"),
    (18, "Vias", 2, 1, "yes", "yes"),
    (19, "Unrouted", 6, 1, "yes", "yes"),
    (20, "Dimension", 24, 1, "yes", "yes"),
    (21, "tPlace", 7, 1, "yes", "yes"),
    (22, "bPlace", 7, 1, "yes", "yes"),
    (23, "tOrigins", 15, 1, "yes", "yes"),
    (24, "bOrigins", 15, 1, "yes", "yes"),
    (25, "tNames", 7, 1, "yes", "yes"),
    (26, "bNames", 7, 1, "yes", "yes"),
    (27, "tValues", 7, 1, "yes", "yes"),
    (28, "bValues", 7, 1, "yes", "yes"),
    (29, "tStop", 7, 3, "no", "yes"),
    (30, "bStop", 7, 6, "no", "yes"),
    (31, "tCream", 7, 4, "no", "yes"),
    (32, "bCream", 7, 5, "no", "yes"),
    (33, "tFinish", 6, 3, "no", "yes"),
    (34, "bFinish", 6, 6, "no", "yes"),
    (35, "tGlue", 7, 4, "no", "yes"),
    (36, "bGlue", 7, 5, "no", "yes"),
    (37, "tTest", 7, 1, "no", "yes"),
    (38, "bTest", 7, 1, "no", "yes"),
    (39, "tKeepout", 4, 11, "yes", "yes"),
    (40, "bKeepout", 1, 11, "yes", "yes"),
    (41, "tRestrict", 4, 10, "yes", "yes"),
    (42, "bRestrict", 1, 10, "yes", "yes"),
    (43, "vRestrict", 2, 10, "yes", "yes"),
    (44, "Drills", 7, 1, "no", "yes"),
    (45, "Holes", 7, 1, "yes", "yes"),
    (46, "Milling", 3, 1, "no", "yes"),
    (47, "Measures", 7, 1, "no", "yes"),
    (48, "Document", 7, 1, "yes", "yes"),
    (49, "Reference", 7, 1, "yes", "yes"),
    (51, "tDocu", 7, 1, "yes", "yes"),
    (52, "bDocu", 7, 1, "yes", "yes"),
    (88, "SimResults", 9, 1, "yes", "yes"),
    (89, "SimProbes", 9, 1, "yes", "yes"),
    (90, "Modules", 5, 1, "yes", "yes"),
    (91, "Nets", 2, 1, "yes", "yes"),
    (92, "Busses", 1, 1, "yes", "yes"),
    (93, "Pins", 2, 1, "no", "yes"),
    (94, "Symbols", 4, 1, "yes", "yes"),
    (95, "Names", 7, 1, "yes", "yes"),
    (96, "Values", 7, 1, "yes", "yes"),
    (97, "Info", 7, 1, "yes", "yes"),
    (98, "Guide", 6, 1, "yes", "yes"),
    (99, "SpiceOrder", 7, 1, "yes", "yes"),
]


# ─── Helper functions ───────────────────────────────────────────────────────────


def _px_to_mm(dim: Union[int, float]) -> float:
    """Convert EasyEDA symbol pixel units to millimetres.

    1 EasyEDA pixel = 10 mil = 0.254 mm.
    """
    return round(10.0 * float(dim) * 0.0254, 4)


def _fp_dim_to_mm(dim) -> float:
    """Convert a raw EasyEDA footprint dimension (string or number) to mm."""
    try:
        val = float(dim)
        if isnan(val):
            return 0.0
        return round(val * 10 * 0.0254, 4)
    except (ValueError, TypeError):
        return 0.0


def _eagle_pin_length_keyword(length_px: int) -> str:
    """Map an EasyEDA pin length (pixels) to an Eagle pin-length keyword."""
    mm = _px_to_mm(abs(length_px))
    if mm < 0.5:
        return "point"
    if mm <= 3.0:
        return "short"
    if mm <= 6.0:
        return "middle"
    return "long"


def _sanitize_name(name: str) -> str:
    """Sanitize a component / symbol / package name for Eagle XML."""
    return name.replace(" ", "").replace("/", "_").replace('"', "").replace("'", "")


def _fmt(val: float) -> str:
    """Format a float for Eagle XML attributes (strip trailing zeros)."""
    return f"{round(val, 4):g}"


# ─── Exporter class ─────────────────────────────────────────────────────────────


class ExporterEagleLibrary:
    """Convert EasyEDA symbol + footprint into an Eagle *.lbr* library file."""

    def __init__(
        self,
        symbol: Optional[EeSymbol] = None,
        footprint: Optional[EeFootprint] = None,
    ):
        self.symbol = symbol
        self.footprint = footprint
        # Mapping: Eagle symbol pin-name → list of pad-name(s) for <connect>
        self._pin_to_pads: Dict[str, List[str]] = {}

    # ── public API ──────────────────────────────────────────────────

    def export(self, lbr_path: str) -> None:
        """Write the Eagle *.lbr* file to *lbr_path*."""
        root = self._build_xml_tree()
        xml_str = self._serialize(root)
        with open(lbr_path, "w", encoding="utf-8") as fh:
            fh.write(xml_str)

    # ── XML tree construction ───────────────────────────────────────

    def _build_xml_tree(self) -> ET.Element:
        root = ET.Element("eagle", version=EAGLE_VERSION)
        drawing = ET.SubElement(root, "drawing")

        # Settings
        settings = ET.SubElement(drawing, "settings")
        ET.SubElement(settings, "setting", alwaysvectorfont="no")
        ET.SubElement(settings, "setting", verticaltext="up")

        # Grid
        ET.SubElement(
            drawing,
            "grid",
            distance="0.5",
            unitdist="mm",
            unit="mm",
            style="lines",
            multiple="1",
            display="yes",
            altdistance="0.1",
            altunitdist="mm",
            altunit="mm",
        )

        # Layers
        layers_el = ET.SubElement(drawing, "layers")
        for num, name, color, fill, vis, act in EAGLE_LAYERS:
            ET.SubElement(
                layers_el,
                "layer",
                number=str(num),
                name=name,
                color=str(color),
                fill=str(fill),
                visible=vis,
                active=act,
            )

        # Library
        library_el = ET.SubElement(drawing, "library")
        packages_el = ET.SubElement(library_el, "packages")
        symbols_el = ET.SubElement(library_el, "symbols")
        devicesets_el = ET.SubElement(library_el, "devicesets")

        pkg_name = self._build_package(packages_el) if self.footprint else None
        sym_name = self._build_symbol(symbols_el) if self.symbol else None
        self._build_deviceset(devicesets_el, sym_name, pkg_name)

        return root

    # ── Package (footprint) ─────────────────────────────────────────

    def _build_package(self, packages_el: ET.Element) -> str:
        """Add a ``<package>`` and return its *name*."""
        fp = self.footprint

        pkg_name = _sanitize_name(fp.info.name)
        pkg_el = ET.SubElement(packages_el, "package", name=pkg_name)

        # ── Pads ──
        for ee_pad in fp.pads:
            pad_name = str(ee_pad.number)
            if "(" in pad_name and ")" in pad_name:
                pad_name = pad_name.split("(")[1].split(")")[0]

            pos_x = round(ee_pad.center_x - fp.bbox.x, 4)
            pos_y = -round(ee_pad.center_y - fp.bbox.y, 4)  # Y-flip for Eagle

            rotation = 0.0
            try:
                rotation = float(ee_pad.rotation)
                if isnan(rotation):
                    rotation = 0.0
            except (ValueError, TypeError):
                rotation = 0.0

            if ee_pad.hole_radius > 0:
                # Through-hole pad
                attrs: dict = {
                    "name": pad_name,
                    "x": _fmt(pos_x),
                    "y": _fmt(pos_y),
                    "drill": _fmt(2 * ee_pad.hole_radius),
                }
                pad_size = max(ee_pad.width, ee_pad.height)
                if pad_size > 2 * ee_pad.hole_radius + 0.01:
                    attrs["diameter"] = _fmt(pad_size)
                if ee_pad.shape == "RECT":
                    attrs["shape"] = "square"
                elif ee_pad.shape == "OVAL":
                    attrs["shape"] = "long"
                # default shape is "round"
                if rotation != 0:
                    attrs["rot"] = f"R{int(rotation)}"
                ET.SubElement(pkg_el, "pad", **attrs)
            else:
                # SMD pad
                eagle_layer = EE_FP_LAYER_TO_EAGLE.get(ee_pad.layer_id, 1)
                attrs = {
                    "name": pad_name,
                    "x": _fmt(pos_x),
                    "y": _fmt(pos_y),
                    "dx": _fmt(max(ee_pad.width, 0.01)),
                    "dy": _fmt(max(ee_pad.height, 0.01)),
                    "layer": str(eagle_layer),
                }
                if ee_pad.shape in ("ELLIPSE", "OVAL"):
                    attrs["roundness"] = "100"
                if rotation != 0:
                    attrs["rot"] = f"R{int(rotation)}"
                ET.SubElement(pkg_el, "smd", **attrs)

        # ── Tracks → wires ──
        for ee_track in fp.tracks:
            eagle_layer = EE_FP_LAYER_TO_EAGLE.get(ee_track.layer_id, 21)
            raw_points = ee_track.points.split(" ")
            pts = [_fp_dim_to_mm(p) for p in raw_points]
            for i in range(0, len(pts) - 3, 2):
                x1 = round(pts[i] - fp.bbox.x, 4)
                y1 = -round(pts[i + 1] - fp.bbox.y, 4)
                x2 = round(pts[i + 2] - fp.bbox.x, 4)
                y2 = -round(pts[i + 3] - fp.bbox.y, 4)
                ET.SubElement(
                    pkg_el,
                    "wire",
                    x1=_fmt(x1),
                    y1=_fmt(y1),
                    x2=_fmt(x2),
                    y2=_fmt(y2),
                    width=_fmt(max(ee_track.stroke_width, 0.01)),
                    layer=str(eagle_layer),
                )

        # ── Holes ──
        for ee_hole in fp.holes:
            hx = round(ee_hole.center_x - fp.bbox.x, 4)
            hy = -round(ee_hole.center_y - fp.bbox.y, 4)
            ET.SubElement(
                pkg_el, "hole", x=_fmt(hx), y=_fmt(hy), drill=_fmt(ee_hole.radius * 2)
            )

        # ── Circles ──
        for ee_circle in fp.circles:
            cx = round(ee_circle.cx - fp.bbox.x, 4)
            cy = -round(ee_circle.cy - fp.bbox.y, 4)
            eagle_layer = EE_FP_LAYER_TO_EAGLE.get(ee_circle.layer_id, 21)
            ET.SubElement(
                pkg_el,
                "circle",
                x=_fmt(cx),
                y=_fmt(cy),
                radius=_fmt(ee_circle.radius),
                width=_fmt(max(ee_circle.stroke_width, 0.01)),
                layer=str(eagle_layer),
            )

        # ── Rectangles → 4 wires ──
        for ee_rect in fp.rectangles:
            eagle_layer = EE_FP_LAYER_TO_EAGLE.get(ee_rect.layer_id, 21)
            sx = round(ee_rect.x - fp.bbox.x, 4)
            sy = -round(ee_rect.y - fp.bbox.y, 4)
            w = ee_rect.width
            h = ee_rect.height
            sw = _fmt(max(ee_rect.stroke_width, 0.01))
            # Eagle Y-up: positive height goes down → subtract
            corners = [
                (sx, sy),
                (sx + w, sy),
                (sx + w, sy - h),
                (sx, sy - h),
            ]
            for j in range(4):
                x1, y1 = corners[j]
                x2, y2 = corners[(j + 1) % 4]
                ET.SubElement(
                    pkg_el,
                    "wire",
                    x1=_fmt(x1),
                    y1=_fmt(y1),
                    x2=_fmt(x2),
                    y2=_fmt(y2),
                    width=sw,
                    layer=str(eagle_layer),
                )

        # ── Texts ──
        has_name_text = False
        has_value_text = False
        for ee_text in fp.texts:
            tx = round(ee_text.center_x - fp.bbox.x, 4)
            ty = -round(ee_text.center_y - fp.bbox.y, 4)
            eagle_layer = EE_FP_LAYER_TO_EAGLE.get(ee_text.layer_id, 25)
            text_content = ee_text.text

            if ee_text.type == "N":
                text_content = ">Name"
                eagle_layer = 25  # tNames
                has_name_text = True
            elif ee_text.type == "P":
                text_content = ">Value"
                eagle_layer = 27  # tValues
                has_value_text = True

            text_el = ET.SubElement(
                pkg_el,
                "text",
                x=_fmt(tx),
                y=_fmt(ty),
                size=_fmt(max(ee_text.font_size, 0.5)),
                layer=str(eagle_layer),
                align="center",
            )
            text_el.text = text_content

            rotation = 0.0
            try:
                rotation = float(ee_text.rotation)
                if isnan(rotation):
                    rotation = 0.0
            except (ValueError, TypeError):
                rotation = 0.0
            if rotation != 0:
                text_el.set("rot", f"R{int(rotation)}")

        # Ensure >Name and >Value placeholders exist
        if fp.pads:
            y_vals = [-(p.center_y - fp.bbox.y) for p in fp.pads]
            y_min, y_max = min(y_vals), max(y_vals)
        else:
            y_min, y_max = -2.0, 2.0

        if not has_name_text:
            name_el = ET.SubElement(
                pkg_el,
                "text",
                x="0",
                y=_fmt(y_max + 1.5),
                size="1.27",
                layer="25",
                align="center",
            )
            name_el.text = ">Name"

        if not has_value_text:
            val_el = ET.SubElement(
                pkg_el,
                "text",
                x="0",
                y=_fmt(y_min - 1.5),
                size="1.27",
                layer="27",
                align="center",
            )
            val_el.text = ">Value"

        # Log skipped elements
        if fp.arcs:
            logging.warning(
                f"Skipping {len(fp.arcs)} arc(s) in footprint — "
                "arc export to Eagle is not yet supported"
            )

        return pkg_name

    # ── Symbol ──────────────────────────────────────────────────────

    def _build_symbol(self, symbols_el: ET.Element) -> str:
        """Add a ``<symbol>`` and return its *name*."""
        sym = self.symbol
        bbox = sym.bbox
        sym_name = _sanitize_name(sym.info.name)
        sym_el = ET.SubElement(symbols_el, "symbol", name=sym_name)

        # Helper: symbol-coordinate conversion (px → mm, bbox-relative, Y-flip)
        def _sx(px_val):
            return _px_to_mm(float(px_val) - float(bbox.x))

        def _sy(px_val):
            return -_px_to_mm(float(px_val) - float(bbox.y))

        # ── Rectangles → 4 wires (layer 94 = Symbols) ──
        for ee_rect in sym.rectangles:
            x0 = _sx(ee_rect.pos_x)
            y0 = _sy(ee_rect.pos_y)
            w = _px_to_mm(float(ee_rect.width))
            h = _px_to_mm(float(ee_rect.height))
            corners = [(x0, y0), (x0 + w, y0), (x0 + w, y0 - h), (x0, y0 - h)]
            for j in range(4):
                x1, y1 = corners[j]
                x2, y2 = corners[(j + 1) % 4]
                ET.SubElement(
                    sym_el,
                    "wire",
                    x1=_fmt(x1),
                    y1=_fmt(y1),
                    x2=_fmt(x2),
                    y2=_fmt(y2),
                    width="0.254",
                    layer="94",
                )

        # ── Circles (layer 94) ──
        for ee_circle in sym.circles:
            cx = _sx(ee_circle.center_x)
            cy = _sy(ee_circle.center_y)
            r = _px_to_mm(ee_circle.radius)
            ET.SubElement(
                sym_el,
                "circle",
                x=_fmt(cx),
                y=_fmt(cy),
                radius=_fmt(r),
                width="0.254",
                layer="94",
            )

        # ── Ellipses (only truly circular ones) ──
        for ee_ellipse in sym.ellipses:
            if ee_ellipse.radius_x == ee_ellipse.radius_y:
                cx = _sx(ee_ellipse.center_x)
                cy = _sy(ee_ellipse.center_y)
                r = _px_to_mm(ee_ellipse.radius_x)
                ET.SubElement(
                    sym_el,
                    "circle",
                    x=_fmt(cx),
                    y=_fmt(cy),
                    radius=_fmt(r),
                    width="0.254",
                    layer="94",
                )

        # ── Polylines & Polygons → wire segments ──
        for ee_pl in list(sym.polylines) + list(sym.polygons):
            raw_pts = ee_pl.points.split(" ")
            x_pts = [
                _px_to_mm(float(raw_pts[i]) - float(bbox.x))
                for i in range(0, len(raw_pts), 2)
            ]
            y_pts = [
                -_px_to_mm(float(raw_pts[i]) - float(bbox.y))
                for i in range(1, len(raw_pts), 2)
            ]
            n = min(len(x_pts), len(y_pts))
            for j in range(n - 1):
                ET.SubElement(
                    sym_el,
                    "wire",
                    x1=_fmt(x_pts[j]),
                    y1=_fmt(y_pts[j]),
                    x2=_fmt(x_pts[j + 1]),
                    y2=_fmt(y_pts[j + 1]),
                    width="0.254",
                    layer="94",
                )
            # Close polygon / filled polyline
            if n > 1 and (isinstance(ee_pl, EeSymbolPolygon) or ee_pl.fill_color):
                if not (x_pts[0] == x_pts[n - 1] and y_pts[0] == y_pts[n - 1]):
                    ET.SubElement(
                        sym_el,
                        "wire",
                        x1=_fmt(x_pts[n - 1]),
                        y1=_fmt(y_pts[n - 1]),
                        x2=_fmt(x_pts[0]),
                        y2=_fmt(y_pts[0]),
                        width="0.254",
                        layer="94",
                    )

        # ── Paths → wire segments (polygon approximation, no bezier) ──
        for ee_path in sym.paths:
            raw = ee_path.paths.split(" ")
            x_pts: List[float] = []
            y_pts: List[float] = []
            i = 0
            while i < len(raw):
                if raw[i] in ("M", "L"):
                    try:
                        x_pts.append(
                            _px_to_mm(float(raw[i + 1]) - float(bbox.x))
                        )
                        y_pts.append(
                            -_px_to_mm(float(raw[i + 2]) - float(bbox.y))
                        )
                    except (ValueError, IndexError):
                        pass
                    i += 3
                elif raw[i] == "Z":
                    if x_pts:
                        x_pts.append(x_pts[0])
                        y_pts.append(y_pts[0])
                    i += 1
                else:
                    i += 1  # skip unsupported commands (C, etc.)
            for j in range(len(x_pts) - 1):
                ET.SubElement(
                    sym_el,
                    "wire",
                    x1=_fmt(x_pts[j]),
                    y1=_fmt(y_pts[j]),
                    x2=_fmt(x_pts[j + 1]),
                    y2=_fmt(y_pts[j + 1]),
                    width="0.254",
                    layer="94",
                )

        # ── Pins ──
        # Deduplicate display-names using Eagle's @N suffix convention
        pin_names_raw = [p.name.text.replace(" ", "") for p in sym.pins]
        name_counts = Counter(pin_names_raw)
        name_seen: Dict[str, int] = {}

        self._pin_to_pads = {}

        for ee_pin in sym.pins:
            raw_name = ee_pin.name.text.replace(" ", "")
            pin_number = ee_pin.settings.spice_pin_number.replace(" ", "")

            # Unique Eagle pin name
            if name_counts[raw_name] > 1:
                idx = name_seen.get(raw_name, 0) + 1
                name_seen[raw_name] = idx
                eagle_pin_name = f"{raw_name}@{idx}"
            else:
                eagle_pin_name = raw_name

            # Track mapping for <connect> elements
            self._pin_to_pads[eagle_pin_name] = [pin_number]

            # Position (px → mm, bbox-relative, Y-flip)
            px = _sx(ee_pin.settings.pos_x)
            py = _sy(ee_pin.settings.pos_y)

            # Pin length
            try:
                length_px = abs(int(float(ee_pin.pin_path.path.split("h")[-1])))
            except (ValueError, IndexError):
                length_px = 10  # default ≈ 2.54 mm → "short"
            eagle_length = _eagle_pin_length_keyword(length_px)

            # Direction
            direction = EE_PIN_TYPE_TO_EAGLE_DIR.get(ee_pin.settings.type, "pas")

            # Rotation: EasyEDA 0° = stub points right, Eagle R0 = stub
            # points left → add 180° and normalise to [0, 360).
            rotation = (int(ee_pin.settings.rotation) + 180) % 360

            attrs: dict = {
                "name": eagle_pin_name,
                "x": _fmt(px),
                "y": _fmt(py),
                "length": eagle_length,
                "direction": direction,
            }
            if rotation != 0:
                attrs["rot"] = f"R{rotation}"

            ET.SubElement(sym_el, "pin", **attrs)

        # ── >Name / >Value text placeholders (layers 95 / 96) ──
        all_y: List[float] = []
        for ee_pin in sym.pins:
            all_y.append(_sy(ee_pin.settings.pos_y))
        for ee_rect in sym.rectangles:
            y0 = _sy(ee_rect.pos_y)
            h = _px_to_mm(float(ee_rect.height))
            all_y.extend([y0, y0 - h])

        y_max = max(all_y) if all_y else 5.0
        y_min = min(all_y) if all_y else -5.0

        name_text = ET.SubElement(
            sym_el, "text", x="0", y=_fmt(y_max + 2), size="1.778", layer="95"
        )
        name_text.text = ">Name"

        value_text = ET.SubElement(
            sym_el, "text", x="0", y=_fmt(y_min - 2), size="1.778", layer="96"
        )
        value_text.text = ">Value"

        # Log skipped arcs
        if sym.arcs:
            logging.warning(
                f"Skipping {len(sym.arcs)} arc(s) in symbol — "
                "arc export to Eagle is not yet supported"
            )

        return sym_name

    # ── Deviceset ───────────────────────────────────────────────────

    def _build_deviceset(
        self,
        devicesets_el: ET.Element,
        sym_name: Optional[str],
        pkg_name: Optional[str],
    ) -> None:
        """Add a ``<deviceset>`` linking symbol and package."""
        if not sym_name and not pkg_name:
            return

        info = self.symbol.info if self.symbol else None
        device_name = _sanitize_name(info.name) if info else (pkg_name or "DEVICE")
        prefix = info.prefix.replace("?", "") if info else "X"

        ds_el = ET.SubElement(
            devicesets_el, "deviceset", name=device_name, prefix=prefix
        )

        # Description
        if info and info.datasheet:
            desc_el = ET.SubElement(ds_el, "description")
            desc_el.text = f"Datasheet: {info.datasheet}"

        # Gates
        gates_el = ET.SubElement(ds_el, "gates")
        if sym_name:
            ET.SubElement(
                gates_el, "gate", name="G$1", symbol=sym_name, x="0", y="0"
            )

        # Devices
        devices_el = ET.SubElement(ds_el, "devices")
        device_attrs: dict = {"name": ""}
        if pkg_name:
            device_attrs["package"] = pkg_name
        device_el = ET.SubElement(devices_el, "device", **device_attrs)

        # Connects — map each Eagle symbol pin to its footprint pad(s)
        if sym_name and pkg_name and self._pin_to_pads:
            connects_el = ET.SubElement(device_el, "connects")
            for eagle_pin, pad_names in self._pin_to_pads.items():
                ET.SubElement(
                    connects_el,
                    "connect",
                    gate="G$1",
                    pin=eagle_pin,
                    pad=" ".join(pad_names),
                )

        # Technologies (with manufacturer / LCSC attributes)
        techs_el = ET.SubElement(device_el, "technologies")
        tech_el = ET.SubElement(techs_el, "technology", name="")

        if info:
            if info.manufacturer:
                ET.SubElement(
                    tech_el, "attribute", name="MF", value=info.manufacturer
                )
            if info.name:
                ET.SubElement(
                    tech_el, "attribute", name="MPN", value=info.name
                )
            if info.lcsc_id:
                ET.SubElement(
                    tech_el, "attribute", name="OC_LCSC", value=info.lcsc_id
                )

    # ── Serialization ───────────────────────────────────────────────

    @staticmethod
    def _serialize(root: ET.Element) -> str:
        """Serialize the XML tree with proper declaration and DOCTYPE."""
        # Pretty-print if Python ≥ 3.9
        try:
            ET.indent(root)
        except AttributeError:
            pass  # older Python — compact output is fine

        xml_body = ET.tostring(root, encoding="unicode", xml_declaration=False)
        return (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE eagle SYSTEM "eagle.dtd">\n'
            + xml_body
            + "\n"
        )

