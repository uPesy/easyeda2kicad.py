# Global imports
import json
import logging
import urllib.error
import urllib.request

from .._version import __version__

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

    def get_info_from_easyeda_api(self, lcsc_id: str) -> dict:
        try:
            req = urllib.request.Request(
                url=API_ENDPOINT.format(lcsc_id=lcsc_id), headers=self.headers
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                raw_data = response.read()
                # Handle gzip compression
                if raw_data[:2] == b"\x1f\x8b":  # gzip magic number
                    import gzip

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

            return api_response
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            logging.error(f"API request failed: {e}")
            return {}

    def get_cad_data_of_component(self, lcsc_id: str) -> dict:
        cp_cad_info = self.get_info_from_easyeda_api(lcsc_id=lcsc_id)
        if cp_cad_info == {}:
            return {}
        return cp_cad_info["result"]

    def get_raw_3d_model_obj(self, uuid: str) -> str:
        try:
            req = urllib.request.Request(
                url=ENDPOINT_3D_MODEL.format(uuid=uuid),
                headers={"User-Agent": self.headers["User-Agent"]},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    logging.error(
                        f"No raw 3D model data found for uuid:{uuid} on easyeda"
                    )
                    return None
                return response.read().decode()
        except urllib.error.URLError as e:
            logging.error(f"Failed to get 3D model for uuid:{uuid}: {e}")
            return None

    def get_step_3d_model(self, uuid: str) -> bytes:
        try:
            req = urllib.request.Request(
                url=ENDPOINT_3D_MODEL_STEP.format(uuid=uuid),
                headers={"User-Agent": self.headers["User-Agent"]},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    logging.error(
                        f"No step 3D model data found for uuid:{uuid} on easyeda"
                    )
                    return None
                return response.read()
        except urllib.error.URLError as e:
            logging.error(f"Failed to get STEP model for uuid:{uuid}: {e}")
            return None
