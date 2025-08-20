"""
easyeda2kicad - Convert EasyEDA components to KiCad format

A Python tool for converting EasyEDA symbols, footprints, and 3D models
to KiCad library format.
"""

__version__ = "0.8.0"
__author__ = "uPesy"
__email__ = "contact@upesy.com"

# Import main functionality for easy access
from .easyeda.easyeda_api import EasyedaApi
from .easyeda.easyeda_importer import (
    EasyedaSymbolImporter,
    EasyedaFootprintImporter,
    Easyeda3dModelImporter,
)
from .kicad.export_kicad_symbol import ExporterSymbolKicad
from .kicad.export_kicad_footprint import ExporterFootprintKicad
from .kicad.export_kicad_3d_model import Exporter3dModelKicad
from .kicad.parameters_kicad_symbol import KicadVersion

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "EasyedaApi",
    "EasyedaSymbolImporter",
    "EasyedaFootprintImporter",
    "Easyeda3dModelImporter",
    "ExporterSymbolKicad",
    "ExporterFootprintKicad",
    "Exporter3dModelKicad",
    "KicadVersion",
]
