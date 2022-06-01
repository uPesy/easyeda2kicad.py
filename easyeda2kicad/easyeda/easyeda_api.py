# Global imports
import logging

import requests

from easyeda2kicad import __version__

API_ENDPOINT = "https://easyeda.com/api/products/{lcsc_id}/components?version=6.4.19.5"
ENDPOINT_3D_MODEL = "https://easyeda.com/analyzer/api/3dmodel/{uuid}"
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
        r = requests.get(url=API_ENDPOINT.format(lcsc_id=lcsc_id), headers=self.headers)
        api_response = r.json()

        if not api_response or (
            "code" in api_response and api_response["success"] is False
        ):
            logging.debug(f"{api_response}")
            return {}

        return r.json()

    def get_cad_data_of_component(self, lcsc_id: str) -> dict:
        cp_cad_info = self.get_info_from_easyeda_api(lcsc_id=lcsc_id)
        if cp_cad_info == {}:
            return {}
        return cp_cad_info["result"]

    def get_raw_3d_model_obj(self, uuid: str) -> str:
        r = requests.get(
            url=ENDPOINT_3D_MODEL.format(uuid=uuid),
            headers={"User-Agent": self.headers["User-Agent"]},
        )
        if r.status_code != requests.codes.ok:
            logging.error(f"No 3D model data found for uuid:{uuid} on easyeda")
            return None
        return r.content.decode()
