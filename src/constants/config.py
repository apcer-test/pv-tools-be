rate_limiter_config = {"request_limit": 10, "time": 5}
PAYLOAD_TIMEOUT = 5
DOC_TYPE_SCHEMAS = {
    "CIOMS": None,  # CIOMSSchema,
    "IRMS": None,  # IRMSSchema,
    "AER": None,  # AERSchema,
    "LAB_REPORT": None,  # LabReportSchema,
    "UNKNOWN": None,  # GenericSchema
}
MICROSOFT_GENERATE_CODE_SCOPE = "offline_access%20User.Read%20Mail.Read"

OUTLOOK_PAGE_SIZE = 10

ALLOWED_ATTACHMENT_EXTENSIONS = ["pdf"]

ALLOWED_FILE_EXTENSIONS = ["xlsx", "xls"]

REQUIRED_EXCEL_SHEET_NAMES = ["Lookup", "Lookup Values"]

REQUIRED_LOOKUP_SHEET_COLUMNS = ["Name", "Slug", "Lookup Type"]

REQUIRED_LOOKUP_VALUES_SHEET_COLUMNS = ["Slug", "Value", "E2B Code R2", "E2B Code R3"]

MAX_PARAMS = 32000
SAFETY = 64
MAX_BATCH_SIZE = 1000

NAME_MAX_LENGTH = 100
R2_R3_MAX_LENGTH = 50
