"""
EasyEDA module - Handle EasyEDA data import and processing
"""

from .easyeda_api import EasyedaApi
from .easyeda_importer import (
    Easyeda3dModelImporter,
    EasyedaFootprintImporter,
    EasyedaSymbolImporter,
)
from .parameters_easyeda import (
    EasyedaPinType,
    Ee3dModel,
    EeSymbol,
    EeSymbolArc,
    EeSymbolCircle,
    EeSymbolInfo,
    EeSymbolPath,
    EeSymbolPin,
    EeSymbolPolygon,
    EeSymbolPolyline,
    EeSymbolRectangle,
    ee_footprint,
)

__all__ = [
    # API
    "EasyedaApi",
    # Importers
    "EasyedaSymbolImporter",
    "EasyedaFootprintImporter",
    "Easyeda3dModelImporter",
    # Data structures
    "EasyedaPinType",
    "EeSymbol",
    "EeSymbolInfo",
    "EeSymbolPin",
    "EeSymbolRectangle",
    "EeSymbolCircle",
    "EeSymbolArc",
    "EeSymbolPolyline",
    "EeSymbolPolygon",
    "EeSymbolPath",
    "ee_footprint",
    "Ee3dModel",
]
