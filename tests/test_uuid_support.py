"""Tests for UUID-based component import (--uuid flag, API_ENDPOINT_BY_UUID,
importer fallbacks for private-component field names)."""

from __future__ import annotations

import urllib.error
from pathlib import Path
from typing import Any

import pytest

from easyeda2kicad.__main__ import main, valid_arguments
from easyeda2kicad.easyeda.easyeda_api import EasyedaApi
from easyeda2kicad.easyeda.easyeda_importer import (
    EasyedaFootprintImporter,
    EasyedaSymbolImporter,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _symbol_data(
    *, lcsc: dict[str, Any] | None = None, c_para_extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    c_para: dict[str, Any] = {"name": "TestPart", "pre": "U", "package": "QFN-32"}
    if c_para_extra:
        c_para.update(c_para_extra)
    data: dict[str, Any] = {
        "description": "private component",
        "tags": [],
        "dataStr": {
            "BBox": {"x": "0", "y": "0", "width": "10", "height": "10"},
            "head": {"x": "0", "y": "0", "c_para": c_para},
            "shape": [],
        },
    }
    if lcsc is not None:
        data["lcsc"] = lcsc
    return data


def _footprint_data(
    *, lcsc_number: str = "", c_para_extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    c_para: dict[str, Any] = {"package": "SOT-23", "name": "TestPart", "pre": "U"}
    if c_para_extra:
        c_para.update(c_para_extra)
    return {
        "SMT": True,
        "packageDetail": {
            "title": "SOT-23",
            "dataStr": {
                "head": {"x": "0", "y": "0", "c_para": c_para},
                "shape": [],
                "canvas": "",
            },
        },
        "lcsc": {"number": lcsc_number},
        "customData": {},
        "description": "",
    }


# ---------------------------------------------------------------------------
# CLI validation
# ---------------------------------------------------------------------------


class TestValidArguments:
    def _base_args(self, **overrides: Any) -> dict[str, Any]:
        args: dict[str, Any] = {
            "lcsc_id": None,
            "uuid": None,
            "symbol": True,
            "footprint": False,
            "3d": False,
            "svg": False,
            "full": False,
            "overwrite": False,
            "project_relative": False,
            "output": None,
            "custom_field": [],
            "debug": False,
            "use_cache": False,
        }
        args.update(overrides)
        return args

    def test_neither_lcsc_id_nor_uuid_fails(self) -> None:
        args = self._base_args()
        assert valid_arguments(args) is False

    def test_lcsc_id_alone_passes(self, tmp_path: Path) -> None:
        args = self._base_args(lcsc_id=["C2040"], output=str(tmp_path / "lib"))
        assert valid_arguments(args) is True

    def test_uuid_alone_passes(self, tmp_path: Path) -> None:
        args = self._base_args(uuid=["abc-123-def"], output=str(tmp_path / "lib"))
        assert valid_arguments(args) is True

    def test_both_lcsc_id_and_uuid_passes(self, tmp_path: Path) -> None:
        args = self._base_args(
            lcsc_id=["C2040"], uuid=["abc-123-def"], output=str(tmp_path / "lib")
        )
        assert valid_arguments(args) is True

    def test_invalid_lcsc_id_format_fails(self, tmp_path: Path) -> None:
        args = self._base_args(lcsc_id=["12345"], output=str(tmp_path / "lib"))
        assert valid_arguments(args) is False

    def test_uuid_not_validated_for_c_prefix(self, tmp_path: Path) -> None:
        args = self._base_args(uuid=["anything-goes"], output=str(tmp_path / "lib"))
        assert valid_arguments(args) is True


# ---------------------------------------------------------------------------
# Importer: symbol fallbacks for private-component field names
# ---------------------------------------------------------------------------


class TestSymbolImporterFallbacks:
    def test_supplier_part_used_as_lcsc_number(self) -> None:
        data = _symbol_data(lcsc={}, c_para_extra={"Supplier Part": "C9999"})
        sym = EasyedaSymbolImporter(data).get_symbol()
        assert sym.info.lcsc_id == "C9999"

    def test_lcsc_part_used_as_lcsc_number(self) -> None:
        data = _symbol_data(lcsc={}, c_para_extra={"LCSC Part": "C8888"})
        sym = EasyedaSymbolImporter(data).get_symbol()
        assert sym.info.lcsc_id == "C8888"

    def test_lcsc_number_takes_priority_over_supplier_part(self) -> None:
        data = _symbol_data(
            lcsc={"number": "C1111"},
            c_para_extra={"Supplier Part": "C9999"},
        )
        sym = EasyedaSymbolImporter(data).get_symbol()
        assert sym.info.lcsc_id == "C1111"

    def test_datasheet_link_fallback(self) -> None:
        data = _symbol_data(
            lcsc={}, c_para_extra={"link": "https://example.com/ds.pdf"}
        )
        sym = EasyedaSymbolImporter(data).get_symbol()
        assert sym.info.datasheet == "https://example.com/ds.pdf"

    def test_datasheet_field_fallback(self) -> None:
        data = _symbol_data(
            lcsc={}, c_para_extra={"datasheet": "https://example.com/ds2.pdf"}
        )
        sym = EasyedaSymbolImporter(data).get_symbol()
        assert sym.info.datasheet == "https://example.com/ds2.pdf"

    def test_lcsc_url_generated_only_for_c_prefix(self) -> None:
        data = _symbol_data(lcsc={}, c_para_extra={"Supplier Part": "C7777"})
        sym = EasyedaSymbolImporter(data).get_symbol()
        assert sym.info.datasheet == "https://www.lcsc.com/datasheet/C7777.pdf"

    def test_no_lcsc_url_for_non_c_prefix_part(self) -> None:
        data = _symbol_data(lcsc={}, c_para_extra={"Supplier Part": "MOQ1234"})
        sym = EasyedaSymbolImporter(data).get_symbol()
        assert sym.info.datasheet == ""

    def test_no_datasheet_without_any_source(self) -> None:
        data = _symbol_data(lcsc={})
        sym = EasyedaSymbolImporter(data).get_symbol()
        assert sym.info.datasheet == ""


# ---------------------------------------------------------------------------
# Importer: footprint fallbacks for private-component field names
# ---------------------------------------------------------------------------


class TestFootprintImporterFallbacks:
    def test_supplier_part_used_as_lcsc_id(self) -> None:
        data = _footprint_data(lcsc_number="", c_para_extra={"Supplier Part": "C5555"})
        fp = EasyedaFootprintImporter(data).get_footprint()
        assert fp.info.lcsc_id == "C5555"

    def test_lcsc_part_used_as_lcsc_id(self) -> None:
        data = _footprint_data(lcsc_number="", c_para_extra={"LCSC Part": "C4444"})
        fp = EasyedaFootprintImporter(data).get_footprint()
        assert fp.info.lcsc_id == "C4444"

    def test_lcsc_number_takes_priority_over_supplier_part(self) -> None:
        data = _footprint_data(
            lcsc_number="C1111", c_para_extra={"Supplier Part": "C5555"}
        )
        fp = EasyedaFootprintImporter(data).get_footprint()
        assert fp.info.lcsc_id == "C1111"

    def test_empty_lcsc_id_when_no_fallback(self) -> None:
        data = _footprint_data(lcsc_number="")
        fp = EasyedaFootprintImporter(data).get_footprint()
        assert fp.info.lcsc_id == ""


# ---------------------------------------------------------------------------
# CLI end-to-end: --uuid routes through without network error
# ---------------------------------------------------------------------------


class TestMainUuidFlow:
    def test_uuid_flag_error_on_api_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def raise_err(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("no network")

        monkeypatch.setattr("urllib.request.urlopen", raise_err)
        output = str(tmp_path / "lib")
        result = main(["--uuid", "bad-uuid", "--symbol", "--output", output])
        assert result == 1

    def test_no_id_at_all_returns_error(self, tmp_path: Path) -> None:
        result = main(["--symbol", "--output", str(tmp_path / "lib")])
        assert result == 1


# ---------------------------------------------------------------------------
# Live network: UUID endpoint resolves to correct component
# ---------------------------------------------------------------------------


class TestUuidMatchesLcscId:
    # C2040's component UUID, extracted from the LCSC API response.
    C2040_UUID = "c2754a5dac404cb1b757213b56759c67"

    def test_uuid_resolves_to_correct_lcsc_number(self) -> None:
        api = EasyedaApi()
        result = api.get_cad_data_of_component(uuid=self.C2040_UUID)
        assert result.get("lcsc", {}).get("number") == "C2040"
