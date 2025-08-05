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
