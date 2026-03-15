"""Unit tests for EasyedaApi.search_jlcpcb_components — no network required."""

from __future__ import annotations

import io
import json
import urllib.error
from typing import Any
from unittest.mock import MagicMock

import pytest

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi


@pytest.fixture()
def api() -> EasyedaApi:
    return EasyedaApi(use_cache=False)


def _fake_response(payload: dict[str, Any]) -> MagicMock:
    """Return a context-manager mock that yields a response with the given JSON payload."""
    body = json.dumps(payload).encode("utf-8")
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=io.BytesIO(body))
    cm.__exit__ = MagicMock(return_value=False)
    # urlopen is used as a context manager; the mock itself must act as one too
    urlopen_mock = MagicMock(return_value=cm)
    return urlopen_mock


def _jlcpcb_response(
    items: list[dict[str, Any]],
    total: int | None = None,
) -> dict[str, Any]:
    """Wrap items in the JLCPCB API envelope."""
    return {
        "data": {
            "componentPageInfo": {
                "total": total if total is not None else len(items),
                "list": items,
            }
        }
    }


# ---------------------------------------------------------------------------
# Realistic API item builders
# ---------------------------------------------------------------------------


def _item_resistor() -> dict[str, Any]:
    """Realistic JLCPCB item for a basic 10kΩ 0402 resistor (C25744)."""
    return {
        "componentCode": "C25744",
        "componentName": "100KΩ 100mW ±1% 0402 Chip Resistor",
        "componentModelEn": "RC0402FR-07100KL",
        "componentBrandEn": "YAGEO",
        "componentSpecificationEn": "0402",
        "componentTypeEn": "Chip Resistor - Surface Mount",
        "stockCount": 19832,
        "componentLibraryType": "base",
        "minPurchaseNum": 50,
        "encapsulationNumber": 5000,
        "componentPrices": [
            {"startNumber": 100, "productPrice": 0.0024},
            {"startNumber": 500, "productPrice": 0.0018},
            {"startNumber": 3000, "productPrice": 0.0014},
        ],
        "describe": "100kΩ resistor 0402 1%",
        "lcscGoodsUrl": "https://www.lcsc.com/product-detail/C25744.html",
        "dataManualUrl": "",
        "attributes": [
            {"attribute_name_en": "Resistance", "attribute_value_name": "100KΩ"},
            {"attribute_name_en": "Tolerance", "attribute_value_name": "±1%"},
            {"attribute_name_en": "Power Rating", "attribute_value_name": "100mW"},
            {
                "attribute_name_en": "TC",
                "attribute_value_name": "-",
            },  # should be filtered
            {
                "attribute_name_en": "Mounting Type",
                "attribute_value_name": "",
            },  # should be filtered
        ],
    }


def _item_capacitor_extended() -> dict[str, Any]:
    """Realistic JLCPCB item for an extended electrolytic capacitor (C72861)."""
    return {
        "componentCode": "C72861",
        "componentName": "100µF 25V Electrolytic",
        "componentModelEn": "VT1E101MCHA",
        "componentBrandEn": "Nichicon",
        "componentSpecificationEn": "Through Hole",
        "componentTypeEn": "Aluminum Electrolytic Capacitors",
        "stockCount": 0,
        "componentLibraryType": "expand",
        "minPurchaseNum": 1,
        "encapsulationNumber": None,  # tape-and-reel not applicable
        "componentPrices": [],  # no price tiers available
        "describe": "100µF 25V electrolytic cap",
        "lcscGoodsUrl": "https://www.lcsc.com/product-detail/C72861.html",
        "dataManualUrl": "https://datasheet.lcsc.com/lcsc/some.pdf",
        "attributes": [],
    }


def _item_missing_fields() -> dict[str, Any]:
    """Intentionally sparse item — tests default/fallback behaviour."""
    return {}


# ---------------------------------------------------------------------------
# TestSearchJlcpcbComponents — parsing correctness
# ---------------------------------------------------------------------------


class TestSearchJlcpcbComponents:
    def test_resistor_all_fields_parsed(
        self, api: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Full field mapping for a realistic Basic resistor item."""
        raw = _jlcpcb_response([_item_resistor()])
        monkeypatch.setattr("urllib.request.urlopen", _fake_response(raw))

        result = api.search_jlcpcb_components("100k 0402")

        assert result["total"] == 1
        r = result["results"][0]

        assert r["lcsc"] == "C25744"
        assert r["name"] == "100KΩ 100mW ±1% 0402 Chip Resistor"
        assert r["model"] == "RC0402FR-07100KL"
        assert r["brand"] == "YAGEO"
        assert r["package"] == "0402"
        assert r["category"] == "Chip Resistor - Surface Mount"
        assert r["stock"] == 19832
        assert r["type"] == "Basic"
        assert r["price"] == 0.0024
        assert r["min_qty"] == 50
        assert r["reel_qty"] == 5000
        assert r["description"] == "100kΩ resistor 0402 1%"
        assert "C25744" in r["url"]
        assert r["datasheet"] == ""

    def test_price_breaks_parsed_correctly(
        self, api: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """price_breaks list must contain all tiers with qty + price."""
        raw = _jlcpcb_response([_item_resistor()])
        monkeypatch.setattr("urllib.request.urlopen", _fake_response(raw))

        r = api.search_jlcpcb_components("100k 0402")["results"][0]

        assert r["price_breaks"] == [
            {"qty": 100, "price": 0.0024},
            {"qty": 500, "price": 0.0018},
            {"qty": 3000, "price": 0.0014},
        ]

    def test_attributes_dash_and_empty_filtered(
        self, api: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Attributes with value '-' or empty string must be dropped."""
        raw = _jlcpcb_response([_item_resistor()])
        monkeypatch.setattr("urllib.request.urlopen", _fake_response(raw))

        r = api.search_jlcpcb_components("100k 0402")["results"][0]

        names = [a["name"] for a in r["attributes"]]
        assert "Resistance" in names
        assert "Tolerance" in names
        assert "Power Rating" in names
        # TC has value "-" → must be absent
        assert "TC" not in names
        # Mounting Type has value "" → must be absent
        assert "Mounting Type" not in names

    def test_extended_type_and_no_prices(
        self, api: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Extended component with empty price list: type='Extended', price=None, price_breaks=[]."""
        raw = _jlcpcb_response([_item_capacitor_extended()])
        monkeypatch.setattr("urllib.request.urlopen", _fake_response(raw))

        r = api.search_jlcpcb_components("100uF 25V")["results"][0]

        assert r["type"] == "Extended"
        assert r["price"] is None
        assert r["price_breaks"] == []
        assert r["reel_qty"] is None
        assert r["datasheet"] == "https://datasheet.lcsc.com/lcsc/some.pdf"

    def test_missing_fields_use_defaults(
        self, api: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Completely empty API item must not raise — all fields get safe defaults."""
        raw = _jlcpcb_response([_item_missing_fields()])
        monkeypatch.setattr("urllib.request.urlopen", _fake_response(raw))

        r = api.search_jlcpcb_components("anything")["results"][0]

        assert r["lcsc"] == ""
        assert r["stock"] == 0
        assert r["type"] == "Extended"  # missing key → not "base" → Extended
        assert r["price"] is None
        assert r["price_breaks"] == []
        assert r["min_qty"] == 1
        assert r["reel_qty"] is None
        assert r["attributes"] == []

    def test_multiple_results_and_total(
        self, api: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """total reflects API value, not len(results)."""
        raw = _jlcpcb_response(
            [_item_resistor(), _item_capacitor_extended()],
            total=247,
        )
        monkeypatch.setattr("urllib.request.urlopen", _fake_response(raw))

        result = api.search_jlcpcb_components("resistor")

        assert result["total"] == 247
        assert len(result["results"]) == 2
        assert result["results"][0]["lcsc"] == "C25744"
        assert result["results"][1]["lcsc"] == "C72861"

    def test_network_error_returns_empty(
        self, api: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """URLError must be caught; function returns empty result, no exception."""

        def fail(*_args: object, **_kwargs: object) -> None:
            raise urllib.error.URLError("simulated timeout")

        monkeypatch.setattr("urllib.request.urlopen", fail)

        result = api.search_jlcpcb_components("anything")
        assert result == {"total": 0, "results": []}

    def test_empty_response_envelope(
        self, api: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """API returning {} or missing keys must not raise."""
        monkeypatch.setattr("urllib.request.urlopen", _fake_response({}))

        result = api.search_jlcpcb_components("ghost")
        assert result == {"total": 0, "results": []}
