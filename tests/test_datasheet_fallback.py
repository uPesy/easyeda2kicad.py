from __future__ import annotations

from easyeda2kicad.easyeda.easyeda_importer import EasyedaSymbolImporter


def _make_symbol_data(datasheet_url: str, lcsc_id: str) -> dict[str, object]:
    return {
        "lcsc": {
            "url": datasheet_url,
            "number": lcsc_id,
        },
        "description": "Test component",
        "tags": ["logic"],
        "dataStr": {
            "BBox": {"x": "0", "y": "0", "width": "10", "height": "10"},
            "head": {
                "x": "0",
                "y": "0",
                "c_para": {
                    "name": "TestPart",
                    "pre": "U",
                    "package": "QFN-32",
                },
            },
            "shape": [],
        },
    }


def test_symbol_importer_keeps_source_datasheet() -> None:
    importer = EasyedaSymbolImporter(
        _make_symbol_data(
            datasheet_url="https://example.com/source.pdf",
            lcsc_id="C2040",
        )
    )

    assert importer.get_symbol().info.datasheet == "https://example.com/source.pdf"


def test_symbol_importer_falls_back_to_lcsc_datasheet() -> None:
    importer = EasyedaSymbolImporter(
        _make_symbol_data(datasheet_url="", lcsc_id="C2040")
    )

    assert (
        importer.get_symbol().info.datasheet
        == "https://www.lcsc.com/datasheet/C2040.pdf"
    )


def test_symbol_importer_no_datasheet_when_lcsc_key_absent() -> None:
    data = _make_symbol_data(datasheet_url="", lcsc_id="C2040")
    del data["lcsc"]
    importer = EasyedaSymbolImporter(data)

    assert importer.get_symbol().info.datasheet == ""
