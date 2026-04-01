"""Unit tests for EasyedaApi cache logic — no network required."""

from __future__ import annotations

import gzip
import io
import json
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_response(body: bytes, status: int = 200) -> MagicMock:
    """Minimal context-manager mock that mimics urllib response."""
    resp = MagicMock()
    resp.read.return_value = body
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _gzip_encode(text: str) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write(text.encode("utf-8"))
    return buf.getvalue()


@pytest.fixture()
def api_with_cache(tmp_path: Path) -> EasyedaApi:
    """EasyedaApi instance with cache enabled and tmp cache dir."""
    api = EasyedaApi(use_cache=True)
    api.cache_dir = tmp_path
    return api


# ---------------------------------------------------------------------------
# _get_cache_path
# ---------------------------------------------------------------------------


class TestGetCachePath:
    def test_returns_path_with_extension(self, api_with_cache: EasyedaApi) -> None:
        p = api_with_cache._get_cache_path("C12345", "json")
        assert p.suffix == ".json"
        assert "C12345" in p.name

    def test_sanitizes_slashes(self, api_with_cache: EasyedaApi) -> None:
        p = api_with_cache._get_cache_path("a/b\\c", "obj")
        assert "/" not in p.name
        assert "\\" not in p.name


# ---------------------------------------------------------------------------
# _write_to_cache / _read_from_cache — text
# ---------------------------------------------------------------------------


class TestCacheRoundtripText:
    def test_write_and_read_plain_text(self, api_with_cache: EasyedaApi) -> None:
        path = api_with_cache._get_cache_path("test_plain", "txt")
        api_with_cache._write_to_cache(path, "hello cache")
        result = api_with_cache._read_from_cache(path, binary=False)
        assert result == "hello cache"

    def test_write_json_pretty_prints(self, api_with_cache: EasyedaApi) -> None:
        path = api_with_cache._get_cache_path("test_json", "json")
        api_with_cache._write_to_cache(path, '{"a":1}')
        content = path.read_text()
        assert "\n" in content  # pretty-printed

    def test_write_invalid_json_falls_back_to_plain(
        self, api_with_cache: EasyedaApi
    ) -> None:
        path = api_with_cache._get_cache_path("test_badjson", "json")
        api_with_cache._write_to_cache(path, "not-json{{{")
        assert path.exists()

    def test_read_returns_none_if_file_missing(
        self, api_with_cache: EasyedaApi
    ) -> None:
        path = api_with_cache._get_cache_path("nonexistent", "json")
        assert api_with_cache._read_from_cache(path) is None

    def test_no_write_when_cache_disabled(self, tmp_path: Path) -> None:
        api = EasyedaApi(use_cache=False)
        api.cache_dir = tmp_path
        path = api._get_cache_path("disabled", "txt")
        api._write_to_cache(path, "data")
        assert not path.exists()

    def test_no_read_when_cache_disabled(self, tmp_path: Path) -> None:
        api = EasyedaApi(use_cache=False)
        api.cache_dir = tmp_path
        path = tmp_path / "disabled.txt"
        path.write_text("data")
        assert api._read_from_cache(path) is None


# ---------------------------------------------------------------------------
# _write_to_cache / _read_from_cache — binary
# ---------------------------------------------------------------------------


class TestCacheRoundtripBinary:
    def test_write_and_read_binary(self, api_with_cache: EasyedaApi) -> None:
        path = api_with_cache._get_cache_path("test_bin", "step")
        data = b"\x00\x01\x02\xff"
        api_with_cache._write_to_cache(path, data, binary=True)
        result = api_with_cache._read_from_cache(path, binary=True)
        assert result == data

    def test_read_binary_wrong_mode_returns_str(
        self, api_with_cache: EasyedaApi
    ) -> None:
        # Write binary, read as text → returns str (not bytes)
        path = api_with_cache._get_cache_path("test_bin2", "step")
        api_with_cache._write_to_cache(path, b"ABC", binary=True)
        result = api_with_cache._read_from_cache(path, binary=False)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# get_info_from_easyeda_api — cache hit path (no network)
# ---------------------------------------------------------------------------


class TestGetInfoCacheHit:
    def test_returns_cached_json(self, api_with_cache: EasyedaApi) -> None:
        payload = {"success": True, "result": {"foo": "bar"}}
        path = api_with_cache._get_cache_path("C99999", "json")
        path.write_text(json.dumps(payload))

        result = api_with_cache.get_info_from_easyeda_api("C99999")
        assert result == payload

    def test_invalid_cached_json_falls_through(
        self, api_with_cache: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Write broken JSON to cache → should attempt network (patched to fail gracefully)
        path = api_with_cache._get_cache_path("C88888", "json")
        path.write_text("broken{{{")

        import urllib.error

        def fake_urlopen(*args: object, **kwargs: object) -> None:
            raise urllib.error.URLError("no network in test")

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        result = api_with_cache.get_info_from_easyeda_api("C88888")
        assert result == {}


# ---------------------------------------------------------------------------
# get_raw_3d_model_obj — cache hit path
# ---------------------------------------------------------------------------


class TestGet3dModelObjCacheHit:
    def test_returns_cached_obj(self, api_with_cache: EasyedaApi) -> None:
        obj_data = "v 0 0 0\nv 1 0 0\n"
        path = api_with_cache._get_cache_path("uuid-abc", "obj")
        path.write_text(obj_data)

        result = api_with_cache.get_raw_3d_model_obj("uuid-abc")
        assert result == obj_data


# ---------------------------------------------------------------------------
# get_step_3d_model — cache hit path
# ---------------------------------------------------------------------------


class TestGetStepCacheHit:
    def test_returns_cached_step(self, api_with_cache: EasyedaApi) -> None:
        step_data = b"ISO-10303-21;"
        path = api_with_cache._get_cache_path("uuid-step", "step")
        path.write_bytes(step_data)

        result = api_with_cache.get_step_3d_model("uuid-step")
        assert result == step_data


# ---------------------------------------------------------------------------
# get_svg_from_api — cache hit path (no network)
# ---------------------------------------------------------------------------


class TestGetSvgFromApiCacheHit:
    def test_returns_cached_svg(self, api_with_cache: EasyedaApi) -> None:
        payload = {"symbol": "<svg>sym</svg>", "footprint": "<svg>fp</svg>"}
        path = api_with_cache._get_cache_path("C1591_svg", "json")
        path.write_text(json.dumps(payload))

        result = api_with_cache.get_svg_from_api("C1591")
        assert result == payload

    def test_invalid_cache_falls_through_to_network(
        self, api_with_cache: EasyedaApi, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = api_with_cache._get_cache_path("C1591_svg", "json")
        path.write_text("broken{{{")

        import urllib.error

        def fake_urlopen(*args: object, **kwargs: object) -> None:
            raise urllib.error.URLError("no network in test")

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        result = api_with_cache.get_svg_from_api("C1591")
        assert result == {"symbol": "", "footprint": ""}


# ---------------------------------------------------------------------------
# get_info_from_easyeda_api — network path (monkeypatched)
# ---------------------------------------------------------------------------


class TestGetInfoNetworkPath:
    def test_fetches_and_returns_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=False)
        payload = {"success": True, "result": {"dataStr": "abc"}}
        body = json.dumps(payload).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        result = api.get_info_from_easyeda_api("C11111")
        assert result == payload

    def test_gzip_response_decoded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=False)
        payload = {"success": True, "result": {"dataStr": "gz"}}
        body = _gzip_encode(json.dumps(payload))
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        result = api.get_info_from_easyeda_api("C22222")
        assert result == payload

    def test_failed_request_returns_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=False)

        def raise_url_error(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("timeout")

        monkeypatch.setattr("urllib.request.urlopen", raise_url_error)
        assert api.get_info_from_easyeda_api("C33333") == {}

    def test_writes_to_cache_on_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=True)
        api.cache_dir = tmp_path
        payload = {"success": True, "result": {"dataStr": "cached"}}
        body = json.dumps(payload).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        api.get_info_from_easyeda_api("C44444")
        cache_file = api._get_cache_path("C44444", "json")
        assert cache_file.exists()

    def test_success_false_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        payload = {"success": False, "message": "not found"}
        body = json.dumps(payload).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        assert api.get_info_from_easyeda_api("C55555") == {}


# ---------------------------------------------------------------------------
# get_cad_data_of_component — delegates to get_info_from_easyeda_api
# ---------------------------------------------------------------------------


class TestGetCadDataOfComponent:
    def test_returns_result_field(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        payload = {"success": True, "result": {"dataStr": "xyz"}}
        body = json.dumps(payload).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        assert api.get_cad_data_of_component("C66666") == {"dataStr": "xyz"}

    def test_empty_info_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)

        def raise_err(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("no net")

        monkeypatch.setattr("urllib.request.urlopen", raise_err)
        assert api.get_cad_data_of_component("C77777") == {}


# ---------------------------------------------------------------------------
# get_raw_3d_model_obj — network path (monkeypatched)
# ---------------------------------------------------------------------------


class TestGet3dModelObjNetworkPath:
    def test_fetches_obj_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        obj_text = "v 0 0 0\nf 1 2 3\n"
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(obj_text.encode()),
        )
        result = api.get_raw_3d_model_obj("uuid-net")
        assert result == obj_text

    def test_non_200_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(b"not found", status=404),
        )
        assert api.get_raw_3d_model_obj("uuid-404") is None

    def test_url_error_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)

        def raise_err(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("no net")

        monkeypatch.setattr("urllib.request.urlopen", raise_err)
        assert api.get_raw_3d_model_obj("uuid-err") is None

    def test_writes_to_cache(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=True)
        api.cache_dir = tmp_path
        obj_text = "v 1 2 3\n"
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(obj_text.encode()),
        )
        api.get_raw_3d_model_obj("uuid-cache")
        assert api._get_cache_path("uuid-cache", "obj").exists()


# ---------------------------------------------------------------------------
# get_step_3d_model — network path (monkeypatched)
# ---------------------------------------------------------------------------


class TestGetStepNetworkPath:
    def test_fetches_step_bytes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        step_bytes = b"ISO-10303-21;"
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(step_bytes),
        )
        result = api.get_step_3d_model("uuid-step-net")
        assert result == step_bytes

    def test_non_200_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(b"", status=404),
        )
        assert api.get_step_3d_model("uuid-step-404") is None

    def test_url_error_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)

        def raise_err(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("no net")

        monkeypatch.setattr("urllib.request.urlopen", raise_err)
        assert api.get_step_3d_model("uuid-step-err") is None

    def test_writes_to_cache(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=True)
        api.cache_dir = tmp_path
        step_bytes = b"ISO-10303-21;"
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(step_bytes),
        )
        api.get_step_3d_model("uuid-step-cache")
        assert api._get_cache_path("uuid-step-cache", "step").exists()


# ---------------------------------------------------------------------------
# get_svg_from_api — network path (monkeypatched)
# ---------------------------------------------------------------------------


class TestGetSvgFromApiNetworkPath:
    def _make_api_body(self, entries: list[dict[str, Any]]) -> bytes:
        return json.dumps({"result": entries}).encode()

    def test_two_entries_symbol_and_footprint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=False)
        entries = [
            {"svg": "<svg>symbol</svg>"},
            {"svg": "<svg>footprint</svg>"},
        ]
        body = self._make_api_body(entries)
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        result = api.get_svg_from_api("C1591")
        assert result["symbol"] == "<svg>symbol</svg>"
        assert result["footprint"] == "<svg>footprint</svg>"

    def test_single_entry_only_footprint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        entries = [{"svg": "<svg>fp_only</svg>"}]
        body = self._make_api_body(entries)
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        result = api.get_svg_from_api("C0001")
        assert result["symbol"] == ""
        assert result["footprint"] == "<svg>fp_only</svg>"

    def test_empty_result_returns_empty_strings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=False)
        body = json.dumps({"result": []}).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        result = api.get_svg_from_api("C0002")
        assert result == {"symbol": "", "footprint": ""}

    def test_url_error_returns_empty_strings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=False)

        def raise_err(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("no net")

        monkeypatch.setattr("urllib.request.urlopen", raise_err)
        result = api.get_svg_from_api("C0003")
        assert result == {"symbol": "", "footprint": ""}

    def test_writes_to_cache(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=True)
        api.cache_dir = tmp_path
        entries = [{"svg": "<svg>s</svg>"}, {"svg": "<svg>f</svg>"}]
        body = self._make_api_body(entries)
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        api.get_svg_from_api("C0004")
        assert api._get_cache_path("C0004_svg", "json").exists()


# ---------------------------------------------------------------------------
# search_jlcpcb_components — monkeypatched
# ---------------------------------------------------------------------------


class TestSearchJlcpcbComponents:
    def _make_jlcpcb_body(self, items: list[dict[str, Any]]) -> bytes:
        payload = {
            "data": {
                "componentPageInfo": {
                    "total": len(items),
                    "list": items,
                }
            }
        }
        return json.dumps(payload).encode()

    def test_basic_search_returns_results(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        api = EasyedaApi(use_cache=False)
        items = [
            {
                "componentCode": "C1591",
                "componentName": "CL10B104KB8NNNC",
                "componentSpecificationEn": "0402",
                "stockCount": 100,
                "componentLibraryType": "base",
                "componentPrices": [{"startNumber": 10, "productPrice": 0.01}],
                "minPurchaseNum": 10,
            }
        ]
        body = self._make_jlcpcb_body(items)
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(body)
        )
        result = api.search_jlcpcb_components("CL10B104KB8NNNC")
        assert result["total"] == 1
        assert result["results"][0]["lcsc"] == "C1591"
        assert result["results"][0]["type"] == "Basic"

    def test_url_error_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)

        def raise_err(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("no net")

        monkeypatch.setattr("urllib.request.urlopen", raise_err)
        result = api.search_jlcpcb_components("anything")
        assert result == {"total": 0, "results": []}

    def test_part_type_filter_included(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        captured: list[Any] = []

        def fake_urlopen(req: Any, **kw: Any) -> Any:
            captured.append(req)
            return _fake_response(self._make_jlcpcb_body([]))

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        api.search_jlcpcb_components("cap", part_type="base")
        body_sent = captured[0].data.decode()
        assert "componentLibraryType" in body_sent


# ---------------------------------------------------------------------------
# get_product_image_url — monkeypatched
# ---------------------------------------------------------------------------


class TestGetProductImageUrl:
    def test_og_image_extracted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        html = (
            b"<html><head>"
            b'<meta property="og:image" content="https://img.lcsc.com/product.jpg"/>'
            b"</head></html>"
        )
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(html)
        )
        result = api.get_product_image_url("https://www.lcsc.com/product/C1591.html")
        assert result == "https://img.lcsc.com/product.jpg"

    def test_json_ld_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        ld = json.dumps({"@type": "Product", "image": "https://img.lcsc.com/ld.jpg"})
        html = (
            f'<html><head><script type="application/ld+json">{ld}</script>'
            f"</head></html>"
        ).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(html)
        )
        result = api.get_product_image_url("https://lcsc.com/product/C1591.html")
        assert result == "https://img.lcsc.com/ld.jpg"

    def test_empty_url_returns_none(self) -> None:
        api = EasyedaApi(use_cache=False)
        assert api.get_product_image_url("") is None

    def test_non_lcsc_host_returns_none(self) -> None:
        api = EasyedaApi(use_cache=False)
        assert api.get_product_image_url("https://evil.com/page") is None

    def test_url_error_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)

        def raise_err(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("no net")

        monkeypatch.setattr("urllib.request.urlopen", raise_err)
        assert api.get_product_image_url("https://www.lcsc.com/product/C1.html") is None

    def test_no_image_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(b"<html><body>no image</body></html>"),
        )
        assert api.get_product_image_url("https://www.lcsc.com/product/C1.html") is None


# ---------------------------------------------------------------------------
# _get_v2_json / search_v2_component_uuids_by_lcsc — monkeypatched
# ---------------------------------------------------------------------------


class TestGetV2Json:
    def test_returns_parsed_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        payload = {"code": 0, "result": [{"uuid": "abc"}]}
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(json.dumps(payload).encode()),
        )
        result = api._get_v2_json("/api/some/path")
        assert result == payload

    def test_url_error_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)

        def raise_err(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("no net")

        monkeypatch.setattr("urllib.request.urlopen", raise_err)
        assert api._get_v2_json("/api/broken") == {}


class TestSearchV2ComponentUuidsByLcsc:
    def test_returns_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)
        payload = {"code": 0, "result": {"C1591": "uuid-abc"}}
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(json.dumps(payload).encode()),
        )
        result = api.search_v2_component_uuids_by_lcsc(["C1591"])
        assert result == payload

    def test_url_error_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        api = EasyedaApi(use_cache=False)

        def raise_err(*a: Any, **kw: Any) -> None:
            raise urllib.error.URLError("no net")

        monkeypatch.setattr("urllib.request.urlopen", raise_err)
        assert api.search_v2_component_uuids_by_lcsc(["C1591"]) == {}


# ---------------------------------------------------------------------------
# Additional edge-case coverage
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_get_info_invalid_json_from_network(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Lines 186-188: inner json.JSONDecodeError inside urlopen block."""
        api = EasyedaApi(use_cache=False)
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _fake_response(b"not-json{{{"),
        )
        assert api.get_info_from_easyeda_api("C99991") == {}

    def test_get_raw_3d_model_obj_cache_wrong_type(self, tmp_path: Path) -> None:
        """Line 215: cache returns bytes instead of str → returns None."""
        api = EasyedaApi(use_cache=True)
        api.cache_dir = tmp_path
        original = api._read_from_cache

        def patched(path: Path, binary: bool = False) -> Any:
            if "uuid-wrongtype" in str(path):
                return b"\x00\x01binary"
            return original(path, binary=binary)

        api._read_from_cache = patched  # type: ignore[assignment]
        assert api.get_raw_3d_model_obj("uuid-wrongtype") is None

    def test_get_step_3d_model_cache_wrong_type(self, tmp_path: Path) -> None:
        """Line 245: cache returns str instead of bytes → returns None."""
        api = EasyedaApi(use_cache=True)
        api.cache_dir = tmp_path
        original = api._read_from_cache

        def patched(path: Path, binary: bool = False) -> Any:
            if "uuid-strtype" in str(path):
                return "not-bytes"
            return original(path, binary=binary)

        api._read_from_cache = patched  # type: ignore[assignment]
        assert api.get_step_3d_model("uuid-strtype") is None

    def test_get_product_image_url_json_ld_contenturl(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JSON-LD fallback via contentUrl key."""
        api = EasyedaApi(use_cache=False)
        ld = json.dumps(
            {"@type": "ImageObject", "contentUrl": "https://img.lcsc.com/cu.jpg"}
        )
        html = (
            f'<html><head><script type="application/ld+json">{ld}</script>'
            f"</head></html>"
        ).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(html)
        )
        result = api.get_product_image_url("https://www.lcsc.com/product/C1.html")
        assert result == "https://img.lcsc.com/cu.jpg"

    def test_get_product_image_url_json_ld_invalid_json_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Lines 497-498: broken JSON-LD blob is skipped, valid second blob used."""
        api = EasyedaApi(use_cache=False)
        ld_valid = json.dumps({"image": "https://img.lcsc.com/valid.jpg"})
        html = (
            "<html><head>"
            '<script type="application/ld+json">broken{{{</script>'
            f'<script type="application/ld+json">{ld_valid}</script>'
            "</head></html>"
        ).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *a, **kw: _fake_response(html)
        )
        result = api.get_product_image_url("https://www.lcsc.com/product/C1.html")
        assert result == "https://img.lcsc.com/valid.jpg"


# ---------------------------------------------------------------------------
# get_svg_from_api — live network (optional)
# ---------------------------------------------------------------------------


@pytest.mark.network
class TestGetSvgFromApiNetwork:
    def test_returns_non_empty_svgs(self) -> None:
        api = EasyedaApi()
        result = api.get_svg_from_api("C1591")
        assert result["symbol"], "symbol SVG should not be empty"
        assert result["footprint"], "footprint SVG should not be empty"
        assert "<svg" in result["symbol"]
        assert "<svg" in result["footprint"]
