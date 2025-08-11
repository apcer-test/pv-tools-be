from enum import IntEnum


class ComponentType(IntEnum):
    """Component types for case number configuration"""

    PROMPT = 1
    YYYYMM = 2
    YYYY = 3
    YY = 4
    YYMM = 5
    SEQUENCE_MONTH = 6
    SEQUENCE_YEAR = 7
    SEQUENCE_RUNNING = 8
    INITIAL_UNIT = 9
    OWNER_UNIT = 10

    @classmethod
    def get_display_name(cls, value: int) -> str:
        """Get display name for the enum value"""
        mapping = {
            cls.PROMPT: "PROMPT",
            cls.YYYYMM: "YYYYMM",
            cls.YYYY: "YYYY",
            cls.YY: "YY",
            cls.YYMM: "YYMM",
            cls.SEQUENCE_MONTH: "SEQUENCE_MONTH",
            cls.SEQUENCE_YEAR: "SEQUENCE_YEAR",
            cls.SEQUENCE_RUNNING: "SEQUENCE_RUNNING",
            cls.INITIAL_UNIT: "INITIAL_UNIT",
            cls.OWNER_UNIT: "OWNER_UNIT",
        }
        return mapping.get(value, "UNKNOWN")
