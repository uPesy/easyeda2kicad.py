"""
KiCad module - Handle KiCad format export and data structures
"""

# Local imports
from .export_kicad_3d_model import Exporter3dModelKicad
from .export_kicad_footprint import ExporterFootprintKicad
from .export_kicad_symbol import ExporterSymbolKicad, integrate_sub_units
from .parameters_kicad_footprint import (
    Ki3dModel,
    KiFootprint,
    KiFootprintInfo,
    KiFootprintPad,
    KiFootprintTrack,
)
from .parameters_kicad_symbol import (
    KiBoxFill,
    KiPinStyle,
    KiPinType,
    KiSymbol,
    KiSymbolInfo,
    KiSymbolPin,
)

__all__ = [
    # Exporters
    "ExporterSymbolKicad",
    "integrate_sub_units",
    "ExporterFootprintKicad",
    "Exporter3dModelKicad",
    # Symbol parameters
    "KiSymbol",
    "KiSymbolInfo",
    "KiSymbolPin",
    "KiPinType",
    "KiPinStyle",
    "KiBoxFill",
    # Footprint parameters
    "KiFootprint",
    "KiFootprintInfo",
    "KiFootprintPad",
    "KiFootprintTrack",
    "Ki3dModel",
]
