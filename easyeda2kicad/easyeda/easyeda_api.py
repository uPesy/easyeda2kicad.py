from __future__ import annotations

# Global imports
import glob  # noqa: F401  # used inside sys.platform=="darwin" block
import gzip
import json
import logging
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from types import ModuleType
from typing import Any

# Local imports
try:
    from .._version import __version__
except ImportError:
    __version__ = "1.0.0"

# Optional import for SSL certificate verification
_certifi: ModuleType | None = None
try:
    import certifi

    HAS_CERTIFI = True
    _certifi = certifi
except ImportError:
    HAS_CERTIFI = False

API_BASE_LEGACY = "https://easyeda.com"
API_ENDPOINT = "https://easyeda.com/api/products/{lcsc_id}/components"
ENDPOINT_SVG = "https://easyeda.com/api/products/{lcsc_id}/svgs"
ENDPOINT_3D_MODEL = "https://modules.easyeda.com/3dmodel/{uuid}"
ENDPOINT_3D_MODEL_STEP = "https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}"

# EasyEDA Pro API (v2) endpoints
API_BASE_V2 = "https://pro.easyeda.com"
ENDPOINT_V2_SEARCH_BY_NUMBERS = "/api/components/searchByNumbers"
ENDPOINT_V2_COMPONENT = "/api/v2/components/{uuid}"  # requires auth
ENDPOINT_V2_COMPONENT_SEARCH_BY_IDS = "/api/v2/components/searchByIds"  # requires auth
ENDPOINT_V2_DEVICE = "/api/v2/devices/{uuid}"  # requires auth
ENDPOINT_V2_DEVICE_SEARCH_BY_IDS = "/api/devices/searchByIds"  # requires auth
ENDPOINT_V2_DOCUMENT_DATASTR = "/api/documents/{uuid}/datastrid"  # requires auth

# JLCPCB component search returns lcsc, name, package, stock, price
JLCPCB_SEARCH_API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"

# ------------------------------------------------------------


class EasyedaApi:
    def __init__(self, use_cache: bool = False) -> None:
        self.headers = {
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://easyeda.com/",
        }
        self.ssl_context = self._create_ssl_context()
        self.cache_dir = Path.cwd() / ".easyeda_cache"
        self.use_cache = use_cache

    def _get_cache_path(self, identifier: str, extension: str) -> Path:
        """Get the cache file path for a specific resource."""
        safe_id = identifier.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_id}.{extension}"

    def _read_from_cache(
        self, cache_path: Path, binary: bool = False
    ) -> str | bytes | None:
        """Read data from cache if it exists."""
        if not self.use_cache or not cache_path.exists():
            return None
        try:
            mode = "rb" if binary else "r"
            with open(cache_path, mode) as f:
                data: str | bytes = f.read()
            logging.debug(f"Cache hit: {cache_path}")
            return data
        except Exception as e:
            logging.warning(f"Failed to read cache {cache_path}: {e}")
            return None

    def _write_to_cache(
        self, cache_path: Path, data: str | bytes, binary: bool = False
    ) -> None:
        """Write data to cache."""
        if not self.use_cache:
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

    @staticmethod
    def _decode_response(raw: bytes) -> str:
        """Decompress gzip if needed and decode bytes to UTF-8 string."""
        if raw[:2] == b"\x1f\x8b":
            return gzip.decompress(raw).decode("utf-8")
        return raw.decode("utf-8")

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with proper certificate handling for macOS."""
        context = ssl.create_default_context()

        # macOS-specific: Try to use KiCad's embedded Python certifi first.
        # Use a glob so future KiCad versions are found automatically.
        if sys.platform == "darwin":
            kicad_certifi_paths = sorted(
                glob.glob(
                    "/Applications/KiCad*/KiCad.app/Contents/Frameworks/"
                    "Python.framework/Versions/*/lib/python*/site-packages/certifi/cacert.pem"
                ),
                reverse=True,  # prefer newer KiCad versions first
            )

            for cert_path in kicad_certifi_paths:
                if Path(cert_path).is_file():
                    try:
                        context.load_verify_locations(cafile=cert_path)
                        logging.debug(f"Using KiCad certificate bundle: {cert_path}")
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
        logging.debug("Using system default SSL certificates")
        return context

    def get_info_from_easyeda_api(self, lcsc_id: str) -> dict[str, Any]:
        # Try to read from cache first
        cache_path = self._get_cache_path(lcsc_id, "json")
        cached_data = self._read_from_cache(cache_path, binary=False)
        if cached_data is not None:
            try:
                cached: dict[str, Any] = json.loads(cached_data)
                return cached
            except json.JSONDecodeError:
                logging.warning(
                    f"Invalid cached JSON for {lcsc_id}, fetching fresh data"
                )

        try:
            req = urllib.request.Request(  # noqa: S310
                url=API_ENDPOINT.format(lcsc_id=lcsc_id), headers=self.headers
            )
            with urllib.request.urlopen(  # noqa: S310
                req, timeout=30, context=self.ssl_context
            ) as response:
                data = self._decode_response(response.read())
                try:
                    api_response: dict[str, Any] = json.loads(data)
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON response from API: {e}")
                    return {}

            if not api_response or api_response.get("success") is False:
                logging.debug(f"{api_response}")
                return {}

            # Write to cache
            self._write_to_cache(cache_path, data, binary=False)

            return api_response
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            logging.error(f"API request failed: {e}")
            return {}

    def get_cad_data_of_component(self, lcsc_id: str) -> dict[str, Any]:
        cp_cad_info = self.get_info_from_easyeda_api(lcsc_id=lcsc_id)
        if not cp_cad_info:
            return {}
        result: dict[str, Any] = cp_cad_info["result"]
        return result

    def get_raw_3d_model_obj(self, uuid: str) -> str | None:
        # Try to read from cache first
        cache_path = self._get_cache_path(uuid, "obj")
        cached_data = self._read_from_cache(cache_path, binary=False)
        if cached_data is not None:
            if not isinstance(cached_data, str):
                return None
            return cached_data

        try:
            req = urllib.request.Request(  # noqa: S310
                url=ENDPOINT_3D_MODEL.format(uuid=uuid),
                headers={"User-Agent": self.headers["User-Agent"]},
            )
            with urllib.request.urlopen(  # noqa: S310
                req, timeout=30, context=self.ssl_context
            ) as response:
                if response.status != 200:
                    logging.error(
                        f"No raw 3D model data found for uuid:{uuid} on easyeda"
                    )
                    return None
                data: str = self._decode_response(response.read())
                # Write to cache
                self._write_to_cache(cache_path, data, binary=False)
                return data
        except urllib.error.URLError as e:
            logging.error(f"Failed to get 3D model for uuid:{uuid}: {e}")
            return None

    def get_step_3d_model(self, uuid: str) -> bytes | None:
        # Try to read from cache first
        cache_path = self._get_cache_path(uuid, "step")
        cached_data = self._read_from_cache(cache_path, binary=True)
        if cached_data is not None:
            if not isinstance(cached_data, bytes):
                return None
            return cached_data

        try:
            req = urllib.request.Request(  # noqa: S310
                url=ENDPOINT_3D_MODEL_STEP.format(uuid=uuid),
                headers={"User-Agent": self.headers["User-Agent"]},
            )
            with urllib.request.urlopen(  # noqa: S310
                req, timeout=30, context=self.ssl_context
            ) as response:
                if response.status != 200:
                    logging.error(
                        f"No step 3D model data found for uuid:{uuid} on easyeda"
                    )
                    return None
                data: bytes = response.read()
                # Write to cache
                self._write_to_cache(cache_path, data, binary=True)
                return data
        except urllib.error.URLError as e:
            logging.error(f"Failed to get STEP model for uuid:{uuid}: {e}")
            return None

    # ------------------------------------------------------------------
    # EasyEDA Pro v2 API helpers
    # ------------------------------------------------------------------

    def _get_v2_json(self, path: str, base: str = API_BASE_V2) -> dict[str, Any]:
        """GET request against an EasyEDA API base, returns parsed JSON."""
        url = base + path
        try:
            req = urllib.request.Request(url=url, headers=self.headers)  # noqa: S310
            with urllib.request.urlopen(  # noqa: S310
                req, timeout=30, context=self.ssl_context
            ) as response:
                result: dict[str, Any] = json.loads(
                    self._decode_response(response.read())
                )
                return result
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            logging.error(f"v2 GET {path} failed: {e}")
            return {}

    def search_v2_component_uuids_by_lcsc(
        self, lcsc_numbers: list[str]
    ) -> dict[str, Any]:
        """POST /api/components/searchByNumbers — resolve LCSC numbers to component UUIDs.

        Body format: numbers=json.dumps([...]) as form-encoded, not JSON.
        """
        url = API_BASE_LEGACY + ENDPOINT_V2_SEARCH_BY_NUMBERS
        try:
            params = urllib.parse.urlencode(
                {"numbers": json.dumps(lcsc_numbers)}
            ).encode("utf-8")
            req = urllib.request.Request(  # noqa: S310
                url=url,
                data=params,
                headers={
                    **self.headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                },
            )
            with urllib.request.urlopen(  # noqa: S310
                req, timeout=30, context=self.ssl_context
            ) as response:
                result: dict[str, Any] = json.loads(
                    self._decode_response(response.read())
                )
                return result
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            logging.error(f"searchByNumbers failed: {e}")
            return {}

    def search_jlcpcb_components(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 10,
        part_type: str | None = None,
    ) -> dict[str, Any]:
        """POST JLCPCB_SEARCH_API — keyword search across the JLCPCB parts library.

        Works anonymously. Returns dict with 'total' and 'results' list; each result
        contains: lcsc, name, model, brand, package, category, stock, type, price,
        price_breaks, min_qty, reel_qty, description, url, datasheet, attributes.
        part_type: "base" = Basic, "expand" = Extended.
        """
        payload: dict[str, Any] = {
            "keyword": keyword,
            "currentPage": page,
            "pageSize": page_size,
        }
        if part_type:
            payload["componentLibraryType"] = part_type

        try:
            req = urllib.request.Request(  # noqa: S310
                url=JLCPCB_SEARCH_API,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Origin": "https://jlcpcb.com",
                    "Referer": "https://jlcpcb.com/parts",
                },
            )
            with urllib.request.urlopen(  # noqa: S310
                req, timeout=15, context=self.ssl_context
            ) as response:
                raw: dict[str, Any] = json.loads(self._decode_response(response.read()))
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            logging.error(f"JLCPCB search failed: {e}")
            return {"total": 0, "results": []}

        page_info: dict[str, Any] = (raw.get("data") or {}).get(
            "componentPageInfo"
        ) or {}
        items: list[dict[str, Any]] = page_info.get("list") or []
        results = []
        for item in items:
            prices = item.get("componentPrices") or []
            results.append(
                {
                    "lcsc": item.get("componentCode", ""),
                    "name": item.get("componentName", ""),
                    "model": item.get("componentModelEn", ""),
                    "brand": item.get("componentBrandEn", ""),
                    "package": item.get("componentSpecificationEn", ""),
                    "category": item.get("componentTypeEn", ""),
                    "stock": item.get("stockCount", 0),
                    "type": "Basic"
                    if item.get("componentLibraryType") == "base"
                    else "Extended",
                    "price": prices[0].get("productPrice") if prices else None,
                    "price_breaks": [
                        {"qty": p.get("startNumber"), "price": p.get("productPrice")}
                        for p in prices
                    ],
                    "min_qty": item.get("minPurchaseNum", 1),
                    "reel_qty": item.get("encapsulationNumber"),
                    "description": item.get("describe", ""),
                    "url": item.get("lcscGoodsUrl", ""),
                    "datasheet": item.get("dataManualUrl", ""),
                    # Technical specs list; entries with value "-" are omitted as uninformative.
                    "attributes": [
                        {
                            "name": a.get("attribute_name_en", ""),
                            "value": a["attribute_value_name"],
                        }
                        for a in (item.get("attributes") or [])
                        if a.get("attribute_value_name")
                        and a["attribute_value_name"] != "-"
                    ],
                }
            )
        return {"total": page_info.get("total", 0), "results": results}

    def get_svg_from_api(self, lcsc_id: str) -> dict[str, Any]:
        """Return pre-rendered SVGs from the EasyEDA /svgs endpoint as ``{"symbol": str, "footprint": str}``.

        The API returns one entry per symbol unit plus one footprint entry (last).
        Multi-unit symbols yield multiple symbol SVGs; only the first unit is returned here.
        Results are cached as JSON when caching is enabled.
        """
        cache_path = self._get_cache_path(f"{lcsc_id}_svg", "json")
        cached_data = self._read_from_cache(cache_path, binary=False)
        if cached_data is not None:
            try:
                result: dict[str, Any] = json.loads(cached_data)
                return result
            except json.JSONDecodeError:
                pass

        try:
            req = urllib.request.Request(  # noqa: S310
                url=ENDPOINT_SVG.format(lcsc_id=lcsc_id),
                headers=self.headers,
            )
            with urllib.request.urlopen(  # noqa: S310
                req, timeout=15, context=self.ssl_context
            ) as response:
                raw = self._decode_response(response.read())
                data: dict[str, Any] = json.loads(raw)
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            logging.error(f"get_svg_from_api failed for {lcsc_id}: {e}")
            return {"symbol": "", "footprint": ""}

        entries: list[dict[str, Any]] = data.get("result") or []
        if not entries:
            return {"symbol": "", "footprint": ""}

        # Last entry = footprint, all earlier entries = symbol units
        symbol_svg: str = entries[0].get("svg", "") if len(entries) >= 2 else ""
        footprint_svg: str = entries[-1].get("svg", "") if len(entries) >= 1 else ""
        result = {"symbol": symbol_svg, "footprint": footprint_svg}
        self._write_to_cache(cache_path, json.dumps(result), binary=False)
        return result

    def get_product_image_url(self, lcsc_url: str) -> str | None:
        """Fetch the 900x900 product image URL for an LCSC product page.

        Extraction order (most reliable first):
        1. og:image meta tag — always in <head>, no JS needed
        2. JSON-LD image/contentUrl/thumbnail — fallback for pages without og:image

        Only fetches from lcsc.com to prevent unintended external requests.
        Returns None if the page cannot be fetched or contains no image.
        """
        if not lcsc_url:
            return None
        parsed = urllib.parse.urlparse(lcsc_url)
        if parsed.hostname not in ("lcsc.com", "www.lcsc.com"):
            logging.warning(
                f"get_product_image_url: unexpected host {parsed.hostname!r}, skipping"
            )
            return None
        try:
            req = urllib.request.Request(  # noqa: S310
                url=lcsc_url,
                headers={
                    **self.headers,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(  # noqa: S310
                req, timeout=10, context=self.ssl_context
            ) as response:
                html = self._decode_response(response.read())
        except (urllib.error.URLError, OSError) as e:
            logging.error(f"Failed to fetch LCSC product page: {e}")
            return None

        # 1) og:image — attribute order varies between name= and property=
        og = re.search(
            r'<meta[^>]+(?:name|property)=["\']og:image["\'][^>]+content=["\']([^"\'>\s]+)["\']',
            html,
        ) or re.search(
            r'<meta[^>]+content=["\']([^"\'>\s]+)["\'][^>]+(?:name|property)=["\']og:image["\']',
            html,
        )
        if og:
            return og.group(1)

        # 2) JSON-LD fallback
        for blob in re.findall(
            r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        ):
            try:
                data: dict[str, Any] = json.loads(blob)
            except json.JSONDecodeError:
                continue
            for key in ("image", "contentUrl", "thumbnail"):
                value = data.get(key)
                if isinstance(value, str) and value.startswith("http"):
                    return value
        return None
