"""
EasyEDA module - Handle EasyEDA data import and processing
"""

from .easyeda_api import EasyedaApi
from .easyeda_importer import (
    EasyedaSymbolImporter,
    EasyedaFootprintImporter,
    Easyeda3dModelImporter,
)
from .parameters_easyeda import (
    EasyedaPinType,
    EeSymbol,
    EeSymbolInfo,
    EeSymbolPin,
    EeSymbolRectangle,
    EeSymbolCircle,
    EeSymbolArc,
    EeSymbolPolyline,
    EeSymbolPolygon,
    EeSymbolPath,
    ee_footprint,
    Ee3dModel,
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
