from typing import List

import httpx
from fastapi import status

from config import settings
from core.exceptions import InvalidUsernamePassword
from core.external_service_client.aicloudbase.constants import AICBTimeouts, AICBURLs
from core.external_service_client.aicloudbase.response import (
    MeddraDetailNode,
    MeddraTerm,
    MeddraVersion,
)
from core.external_service_client.exception import AICBClientError
from core.utils import logger


class AICBClient:
    """
    Client for AiCloudBase external endpoints.
    """

    AICB_URL = settings.AICB_URL

    def _json_headers(self) -> dict[str, str]:
        """
        Generate JSON headers for HTTP requests.
        """
        return {"Accept": "application/json", "Content-Type": "application/json"}

    async def meddra_version_list(
        self, username: str, password: str
    ) -> List[MeddraVersion]:
        """
        POST /api/externalmeddra/meddra-versionlist

        Body:
        {
          "username": "...",
          "password": "..."
        }
        """
        async with httpx.AsyncClient(
            timeout=AICBTimeouts.MEDDRA_VERSION_LIST
        ) as client:
            try:
                # Generate API endpoint
                meddra_version_list_url = (
                    f"{self.AICB_URL}{AICBURLs.MEDDRA_VERSION_LIST}"
                )

                # Get headers
                headers = self._json_headers()

                # Call API
                response = await client.post(
                    meddra_version_list_url,
                    headers=headers,
                    json={"username": username, "password": password},
                )
                if response.status_code != status.HTTP_200_OK:
                    raise InvalidUsernamePassword

                response_data = response.json()
                if response_data.get("statusCode") != 200:
                    logger.info(
                        f"Error in calling AICB API: {response_data.get('message')}",
                        exc_info=True,
                    )
                    raise AICBClientError
                data = response_data.get("data", [])
                return [MeddraVersion(**item) for item in data]
            except Exception as e:
                logger.info(f"Error in calling AICB API: {e}", exc_info=True)
                raise AICBClientError

    async def meddra_list_search(
        self,
        *,
        version_id: int,
        level: str,
        username: str,
        password: str,
        levelcode: str | None = None,
        term: str | None = None,
        condition: str = "startswith",
        orderby: str = "Code",
        soctype: str = "Y",
        matchcase: bool = False,
    ) -> List[MeddraTerm]:
        """
        POST /api/externalmeddra/MedDRAListSearch
        """
        body = {
            "version_id": version_id,
            "level": level,
            "levelcode": levelcode,
            "term": term,
            "condition": condition,
            "orderby": orderby,
            "soctype": soctype,
            "matchcase": matchcase,
            "username": username,
            "password": password,
        }

        async with httpx.AsyncClient(timeout=AICBTimeouts.MEDDRA_LIST_SEARCH) as client:
            try:
                url = f"{self.AICB_URL}{AICBURLs.MEDDRA_LIST_SEARCH}"
                headers = self._json_headers()

                response = await client.post(url, headers=headers, json=body)
                if response.status_code != status.HTTP_200_OK:
                    raise InvalidUsernamePassword

                response_data = response.json()
                if response_data.get("statusCode") != 200:
                    logger.info(
                        f"Error in calling AICB API: {response_data.get('message')}",
                        exc_info=True,
                    )
                    raise AICBClientError

                data = response_data.get("data", [])
                return [MeddraTerm(**item) for item in data]
            except Exception as e:
                logger.info(f"Error in calling AICB API: {e}", exc_info=True)
                raise AICBClientError

    async def meddra_detail_search(
        self,
        *,
        level: str,  # "LLT" | "PT" | "HLGT" | "HLT" | "SOC"
        levelcode: str,  # required term code
        version_id: int,
        username: str,
        password: str,
        soctype: str = "Y",  # "Y" -> primary SOCs only, "N" -> all applicable
    ) -> List[MeddraDetailNode]:
        """
        POST /api/externalmeddra/MedDRADetailSearch
        """
        body = {
            "level": level,
            "levelcode": levelcode,
            "soctype": soctype,
            "version_id": version_id,
            "username": username,
            "password": password,
        }

        async with httpx.AsyncClient(
            timeout=AICBTimeouts.MEDDRA_DETAIL_SEARCH
        ) as client:
            try:
                url = f"{self.AICB_URL}{AICBURLs.MEDDRA_DETAIL_SEARCH}"
                headers = self._json_headers()

                response = await client.post(url, headers=headers, json=body)
                if response.status_code != status.HTTP_200_OK:
                    raise InvalidUsernamePassword

                payload = response.json()
                if payload.get("statusCode") != 200:
                    logger.info(
                        f"AICB MedDRADetailSearch error: {payload.get('message')}",
                        exc_info=True,
                    )
                    raise AICBClientError

                data = payload.get("data", []) or []
                return [MeddraDetailNode(**item) for item in data]
            except Exception as e:
                logger.info(
                    f"Error calling AICB MedDRADetailSearch: {e}", exc_info=True
                )
                raise AICBClientError
