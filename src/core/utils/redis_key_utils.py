# core/cache/keys.py
from enum import Enum


class RedisKeyFormats(Enum):
    """
    Enum to define the Redis key formats
    """

    AICB_MEDDRA_VERSION_LIST = "AICB-Meddra-VersionList"  # new


class RedisKeyConfig:
    """
    Configuration class to generate Redis keys based on the formats
    """

    @staticmethod
    def get_aicb_meddra_version_list_key():
        """
        Get the Redis key for the MedDRA version list
        """
        return RedisKeyFormats.AICB_MEDDRA_VERSION_LIST.value
