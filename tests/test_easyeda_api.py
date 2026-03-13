"""Unit tests for EasyedaApi cache logic — no network required."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi


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
