# Global imports
import gzip
import json
import logging
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Union

# Local imports
from .._version import __version__

# Optional import for SSL certificate verification
try:
    import certifi  # type: ignore[import]

    HAS_CERTIFI = True
    _certifi = certifi  # Store reference to avoid possibly unbound warnings
except ImportError:
    HAS_CERTIFI = False
    _certifi = None  # type: ignore[assignment]

API_ENDPOINT = "https://easyeda.com/api/products/{lcsc_id}/components?version=6.4.19.5"
ENDPOINT_3D_MODEL = "https://modules.easyeda.com/3dmodel/{uuid}"
ENDPOINT_3D_MODEL_STEP = "https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}"
# ENDPOINT_3D_MODEL_STEP found in https://modules.lceda.cn/smt-gl-engine/0.8.22.6032922c/smt-gl-engine.js : points to the bucket containing the step files.

# ------------------------------------------------------------


class EasyedaApi:
    def __init__(self) -> None:
        self.headers = {
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": f"easyeda2kicad v{__version__}",
        }
        self.ssl_context = self._create_ssl_context()
        self.debug_cache_enabled = logging.getLogger().level <= logging.DEBUG
        self.cache_dir = Path.cwd() / ".easyeda_cache"
        if self.debug_cache_enabled:
            logging.info(f"Debug cache enabled: {self.cache_dir}")

    def _get_cache_path(self, identifier: str, extension: str) -> Path:
        """Get the cache file path for a specific resource."""
        safe_id = identifier.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_id}.{extension}"

    def _read_from_cache(
        self, cache_path: Path, binary: bool = False
    ) -> Optional[Union[str, bytes]]:
        """Read data from cache if it exists."""
        if not self.debug_cache_enabled or not cache_path.exists():
            return None
        try:
            mode = "rb" if binary else "r"
            with open(cache_path, mode) as f:
                data = f.read()
            logging.debug(f"Cache hit: {cache_path}")
            return data
        except Exception as e:
            logging.warning(f"Failed to read cache {cache_path}: {e}")
            return None

    def _write_to_cache(
        self, cache_path: Path, data: Union[str, bytes], binary: bool = False
    ) -> None:
        """Write data to cache."""
        if not self.debug_cache_enabled:
            return
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            # For JSON files, pretty-print with indentation
            if not binary and cache_path.suffix == ".json":
                try:
                    # Try to parse as JSON and write with indentation
                    json_data = json.loads(data) if isinstance(data, str) else data
                    with open(cache_path, "w") as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    logging.debug(f"Cached (formatted): {cache_path}")
                    return
                except (json.JSONDecodeError, TypeError):
                    # If not valid JSON, fall back to normal write
                    pass

            mode = "wb" if binary else "w"
            with open(cache_path, mode) as f:
                f.write(data)
            logging.debug(f"Cached: {cache_path}")
        except Exception as e:
            logging.warning(f"Failed to write cache {cache_path}: {e}")

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with proper certificate handling for macOS."""
        context = ssl.create_default_context()

        # macOS-specific: Try to use KiCad's embedded Python certifi first
        if sys.platform == "darwin":
            kicad_certifi_paths = [
                "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/certifi/cacert.pem",
                "/Applications/KiCad-9.0/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/certifi/cacert.pem",
                "/Applications/KiCad-10.0/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/certifi/cacert.pem",
            ]

            for cert_path in kicad_certifi_paths:
                if os.path.isfile(cert_path):
                    try:
                        context.load_verify_locations(cafile=cert_path)
                        logging.info(f"Using KiCad certificate bundle: {cert_path}")
                        return context
                    except Exception as e:
                        logging.warning(f"Failed to load cert from {cert_path}: {e}")

        # Try to use certifi package if available (works on all platforms)
        if HAS_CERTIFI and _certifi is not None:
            try:
                context.load_verify_locations(cafile=_certifi.where())
                logging.debug("Using certifi package for SSL certificates")
                return context
            except Exception as e:
                logging.debug(f"Failed to use certifi: {e}")
        else:
            logging.debug("certifi package not available")

        # Fall back to default context (uses system certificates)
        logging.info("Using system default SSL certificates")
        return context

    def get_info_from_easyeda_api(self, lcsc_id: str) -> dict:
        # Try to read from cache first
        cache_path = self._get_cache_path(lcsc_id, "json")
        cached_data = self._read_from_cache(cache_path, binary=False)
        if cached_data is not None:
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                logging.warning(
                    f"Invalid cached JSON for {lcsc_id}, fetching fresh data"
                )

        try:
            req = urllib.request.Request(
                url=API_ENDPOINT.format(lcsc_id=lcsc_id), headers=self.headers
            )
            with urllib.request.urlopen(
                req, timeout=30, context=self.ssl_context
            ) as response:
                raw_data = response.read()
                # Handle gzip compression
                if raw_data[:2] == b"\x1f\x8b":  # gzip magic number
                    data = gzip.decompress(raw_data).decode("utf-8")
                else:
                    data = raw_data.decode("utf-8")
                try:
                    api_response = json.loads(data)
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON response from API: {e}")
                    return {}

            if not api_response or (
                "code" in api_response and api_response["success"] is False
            ):
                logging.debug(f"{api_response}")
                return {}

            # Write to cache
            self._write_to_cache(cache_path, data, binary=False)

            return api_response
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            logging.error(f"API request failed: {e}")
            return {}

    def get_cad_data_of_component(self, lcsc_id: str) -> dict:
        cp_cad_info = self.get_info_from_easyeda_api(lcsc_id=lcsc_id)
        if cp_cad_info == {}:
            return {}
        return cp_cad_info["result"]

    def get_raw_3d_model_obj(self, uuid: str) -> Optional[str]:
        # Try to read from cache first
        cache_path = self._get_cache_path(uuid, "obj")
        cached_data = self._read_from_cache(cache_path, binary=False)
        if cached_data is not None:
            assert isinstance(cached_data, str)
            return cached_data

        try:
            req = urllib.request.Request(
                url=ENDPOINT_3D_MODEL.format(uuid=uuid),
                headers={"User-Agent": self.headers["User-Agent"]},
            )
            with urllib.request.urlopen(
                req, timeout=30, context=self.ssl_context
            ) as response:
                if response.status != 200:
                    logging.error(
                        f"No raw 3D model data found for uuid:{uuid} on easyeda"
                    )
                    return None
                data = response.read().decode()
                # Write to cache
                self._write_to_cache(cache_path, data, binary=False)
                return data
        except urllib.error.URLError as e:
            logging.error(f"Failed to get 3D model for uuid:{uuid}: {e}")
            return None

    def get_step_3d_model(self, uuid: str) -> Optional[bytes]:
        # Try to read from cache first
        cache_path = self._get_cache_path(uuid, "step")
        cached_data = self._read_from_cache(cache_path, binary=True)
        if cached_data is not None:
            assert isinstance(cached_data, bytes)
            return cached_data

        try:
            req = urllib.request.Request(
                url=ENDPOINT_3D_MODEL_STEP.format(uuid=uuid),
                headers={"User-Agent": self.headers["User-Agent"]},
            )
            with urllib.request.urlopen(
                req, timeout=30, context=self.ssl_context
            ) as response:
                if response.status != 200:
                    logging.error(
                        f"No step 3D model data found for uuid:{uuid} on easyeda"
                    )
                    return None
                data = response.read()
                # Write to cache
                self._write_to_cache(cache_path, data, binary=True)
                return data
        except urllib.error.URLError as e:
            logging.error(f"Failed to get STEP model for uuid:{uuid}: {e}")
            return None
