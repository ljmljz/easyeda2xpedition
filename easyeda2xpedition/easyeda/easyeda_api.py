# Global imports
import logging

import requests

__version__ = "0.1.1"

API_ENDPOINT = "https://easyeda.com/api/products/{lcsc_id}/components?version=6.4.19.5"
API_ENDPOINT_LCEDA = "https://lceda.cn/api/products/{lcsc_id}/components?version=6.4.19.5"

ENDPOINT_3D_MODEL = "https://modules.easyeda.com/3dmodel/{uuid}"
ENDPOINT_3D_MODEL_LCEDA = "https://modules.lceda.cn/3dmodel/{uuid}"

ENDPOINT_3D_MODEL_STEP = "https://modules.easyeda.com/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}"
ENDPOINT_3D_MODEL_STEP_LCEDA = "https://modules.lceda.cn/qAxj6KHrDKw4blvCG8QJPs7Y/{uuid}"
# ENDPOINT_3D_MODEL_STEP found in https://modules.lceda.cn/smt-gl-engine/0.8.22.6032922c/smt-gl-engine.js : points to the bucket containing the step files.

# ------------------------------------------------------------


class EasyedaApi:
    def __init__(self, endpoint: str = 'lceda') -> None:
        self.endpoint = endpoint
        if self.endpoint == 'easyeda':
            self.api_endpoint = API_ENDPOINT
            self.endpoint_3d_model = ENDPOINT_3D_MODEL
            self.endpoint_3d_model_step = ENDPOINT_3D_MODEL_STEP
        elif self.endpoint == 'lceda':
            self.api_endpoint = API_ENDPOINT_LCEDA
            self.endpoint_3d_model = ENDPOINT_3D_MODEL_LCEDA
            self.endpoint_3d_model_step = ENDPOINT_3D_MODEL_STEP_LCEDA
        else:
            raise ValueError(f"Unknown endpoint: {self.endpoint}")
        
        self.headers = {
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": f"easyeda2xpedition v{__version__}",
        }

    def get_info_from_easyeda_api(self, lcsc_id: str) -> dict:
        r = requests.get(url=self.api_endpoint.format(lcsc_id=lcsc_id), headers=self.headers)
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
            url=self.endpoint_3d_model.format(uuid=uuid),
            headers={"User-Agent": self.headers["User-Agent"]},
        )
        if r.status_code != requests.codes.ok:
            logging.error(f"No raw 3D model data found for uuid:{uuid} on easyeda")
            return None
        return r.content.decode()

    def get_step_3d_model(self, uuid: str) -> bytes:
        r = requests.get(
            url=self.endpoint_3d_model_step.format(uuid=uuid),
            headers={"User-Agent": self.headers["User-Agent"]},
        )
        if r.status_code != requests.codes.ok:
            logging.error(f"No step 3D model data found for uuid:{uuid} on easyeda")
            return None
        return r.content
