import asyncio
import traceback
from datetime import UTC, datetime, time, timedelta

import sentry_sdk
from celery import Celery
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from ulid import ULID

from config import settings
from core.common_helpers import (
    capture_exception,
    fetch_mail_box_config,
    fetch_outlook_settings,
    get_last_execution_date,
    get_tenant_data,
)
from core.db import redis
from core.exceptions import CustomException
from core.types import FrequencyType, Providers
from core.utils.email_utils import fetch_email_outlook, logger
from apps.mail_box_config.helper import revoke_running_task
from core.utils.celery_config import celery_app



if settings.ACTIVATE_WORKER_SENTRY is True:

    def init_sentry():
        """Initialize Sentry for error tracking in Celery worker."""

        def before_send(*args):
            """Function to process data before sending to Sentry.

            Args:
                *args: Variable length argument list.

            Returns:
                The processed event data.
            """
            event, _ = args

            exc = event.get("exception")

            if isinstance(exc, CustomException):
                return None
            return event

        if settings.is_development or settings.is_production:
            sentry_sdk.init(
                dsn=settings.SENTRY_SDK_DSN,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
                server_name=settings.APP_NAME,
                before_send=before_send,
                integrations=[
                    CeleryIntegration(),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                ],
            )

    init_sentry()


# @celery_app.task(ignore_result=True)
# def process_attachments(
#     attachments: list[bytes],
#     date: datetime,
#     mail_box_config_id: UUID,
#     tenant_id: UUID,
#     tenant_secrate_key,
#     filename: str,
#     email_id: str,
#     mail_box_email: str,
#     additional_filter: str | None = None,
#     polling_session_id: str | None = None,
# ) -> None:
#     """This Celery worker processes attachments and makes an API request."""
#     try:
#         # **MOST IMPORTANT LOG** - Main email attachment processing workflow started
#         asyncio.get_event_loop().run_until_complete(
#             activity_log_event(
#                 tenant_id=tenant_id,
#                 module=ActivityLogModule.BANK_RECONCILIATION,
#                 sub_module=ActivityLogSubModule.BANK_STATEMENT_EXTRACTION,
#                 operation=ActivityLogOperation.EMAIL_PROCESSING,
#                 status=ActivityLogStatus.STARTED,
#                 summary="BANK_STATEMENT_EXTRACTION: Bank statement processing lifecycle started",
#                 record_id=polling_session_id,  # Use session ID for full traceability
#                 meta_data={
#                     "workflow_details": {
#                         "tenant_id": str(tenant_id),
#                         "user_config_id": str(user_config_id),
#                         "filename": filename,
#                         "email_id": email_id,
#                         "mail_box_email": mail_box_email,
#                         "workflow_stage": "email_attachment_processing",
#                         "operation_type": "main_workflow_start",
#                     },
#                     "user_impact": "Starting complete bank statement processing from email attachment to final recording",
#                     "started_at": datetime.now(UTC).isoformat(),
#                 },
#             )
#         )

#         if not attachments or not attachments[0]:
#             print(f"{filename}: No valid attachment found. Skipping processing.")
#             return
#         print(f"{filename}: Fetching last execution date")

#         print(f"{filename}: Fetching llm prompt")
#         owners_prompt = asyncio.get_event_loop().run_until_complete(get_owners_prompt())

#         print(f"{filename}: Fetching Tenant config")
#         tenant_config_str = asyncio.get_event_loop().run_until_complete(
#             redis.get(f"tenant_config_{tenant_id}")
#         )
#         tenant_config = json.loads(str(tenant_config_str))
#         print(f"{filename}: Fetching bank_recon_config")
#         bank_config = tenant_config.get("bank_reconciliation_config", {})
#         print(f"{filename}: {bank_config}")
#         post_processing_mode = bank_config.get("post_processing_mode")
#         ocr_service_mode = bank_config.get("ocr_service_mode")
#         llm_service_mode = bank_config.get("llm_service_mode")
#         if settings.CREDIT_CONSUMPTION_ENABLE:
#             (
#                 total_cost,
#                 total_ai_cost,
#                 total_ocr_cost,
#                 total_manual_cost,
#                 total_misc_cost,
#                 page_count,
#             ) = asyncio.get_event_loop().run_until_complete(
#                 calculate_bank_recon_credit(
#                     tenant_id=tenant_id,
#                     secret_key=tenant_secrate_key,
#                     bank_config=bank_config,
#                     attachments=attachments[0],
#                 )
#             )
#         if not additional_filter:
#             asyncio.get_event_loop().run_until_complete(
#                 set_last_execution(
#                     last_execution_date=date, user_config_id=user_config_id
#                 )
#             )
#         asyncio.get_event_loop().run_until_complete(
#             validate_account_number(
#                 attachments=attachments[0],
#                 tenant_id=tenant_id,
#                 user_config_id=str(user_config_id),
#                 post_processing_mode=post_processing_mode,
#                 llm_service_mode=llm_service_mode,
#                 polling_session_id=polling_session_id,
#             )
#         )

#         if ocr_service_mode == "PLATFORM":
#             print(f"{filename}: ocr_service_mode = PLATFORM")
#             key, endpoint = asyncio.get_event_loop().run_until_complete(
#                 fetch_azure_owner_configurations()
#             )
#         else:
#             print(f"{filename}: ocr_service_mode = CUSTOM")
#             key, endpoint = asyncio.get_event_loop().run_until_complete(
#                 fetch_azure_configurations(tenant_id)
#             )

#         # Log PDF processing start
#         asyncio.get_event_loop().run_until_complete(
#             activity_log_event(
#                 tenant_id=tenant_id,
#                 module=ActivityLogModule.BANK_RECONCILIATION,
#                 sub_module=ActivityLogSubModule.DOCUMENT_PROCESSING,
#                 operation=ActivityLogOperation.PDF_PROCESSING,
#                 status=ActivityLogStatus.STARTED,
#                 summary="PDF processing started",
#                 record_id=polling_session_id,  # Use session ID for full traceability
#                 meta_data={
#                     "request_details": {
#                         "filename": filename,
#                         "post_processing_mode": post_processing_mode,
#                         "ocr_service_mode": ocr_service_mode,
#                         "llm_service_mode": llm_service_mode
#                         if post_processing_mode == "AI"
#                         else None,
#                         "operation_type": "pdf_processing",
#                     },
#                     "user_impact": "Processing PDF to extract bank statement data",
#                     "started_at": datetime.now(UTC).isoformat(),
#                 },
#             )
#         )

#         if post_processing_mode == "MANUAL":
#             print(f"{filename}: post_processing_mode = MANUAL")
#             data = analyze_layout(
#                 attachment=attachments, key=key, endpoint=endpoint, filename=filename
#             )
#             print(f"{filename}: Data received from Layout")
#         else:
#             print(f"{filename}: post_processing_mode = AI")

#             if llm_service_mode == "PLATFORM":
#                 print(f"{filename}: llm_service_mode = PLATFORM")
#                 llm_creds = asyncio.get_event_loop().run_until_complete(
#                     fetch_llm_creds_owner()
#                 )
#             else:
#                 print(f"{filename}: llm_service_mode = CUSTOM")
#                 llm_creds = asyncio.get_event_loop().run_until_complete(
#                     fetch_llm_creds_user(tenant_id)
#                 )
#             data = analyze_document_llm(
#                 file_content=attachments[0],
#                 endpoint=endpoint,
#                 key=key,
#                 llm_creds=llm_creds,
#                 filename=filename,
#                 owners_prompt=owners_prompt,
#             )
#         if data:
#             print(f"{filename}: Data received from LLM")
#             print("Getting Transaction From ERP")

#             # Log PDF processing completion
#             asyncio.get_event_loop().run_until_complete(
#                 activity_log_event(
#                     tenant_id=tenant_id,
#                     module=ActivityLogModule.BANK_RECONCILIATION,
#                     sub_module=ActivityLogSubModule.DOCUMENT_PROCESSING,
#                     operation=ActivityLogOperation.PDF_PROCESSING,
#                     status=ActivityLogStatus.COMPLETED,
#                     summary="PDF processing completed successfully",
#                     record_id=polling_session_id,  # Use session ID for full traceability
#                     meta_data={
#                         "result_details": {
#                             "filename": filename,
#                             "processing_mode": post_processing_mode,
#                             "transactions_extracted": len(data.get("Transactions", [])),
#                             "data_extracted": bool(data),
#                         },
#                         "user_impact": f"Successfully extracted {len(data.get('Transactions', []))} transactions from PDF",
#                         "completed_at": datetime.now(UTC).isoformat(),
#                     },
#                 )
#             )

#             asyncio.get_event_loop().run_until_complete(
#                 record_bank_statement(
#                     data=data,
#                     tenant_id=tenant_id,
#                     file_name=filename[0],
#                     email_id=email_id,
#                     user_config_id=str(user_config_id),
#                     polling_session_id=polling_session_id,
#                 )
#             )

#             if settings.CREDIT_CONSUMPTION_ENABLE:
#                 asyncio.get_event_loop().run_until_complete(
#                     bank_recon_credit_consumption(
#                         total_cost=total_cost,
#                         total_ai_cost=total_ai_cost,
#                         total_ocr_cost=total_ocr_cost,
#                         total_manual_cost=total_manual_cost,
#                         total_misc_cost=total_misc_cost,
#                         page_count=page_count,
#                         data=data,
#                         tenant_id=tenant_id,
#                         secret_key=tenant_secrate_key,
#                         mail_box_email=mail_box_email,
#                     )
#                 )

#             # **MOST IMPORTANT LOG** - Main bank statement processing workflow completed
#             asyncio.get_event_loop().run_until_complete(
#                 activity_log_event(
#                     tenant_id=tenant_id,
#                     module=ActivityLogModule.BANK_RECONCILIATION,
#                     sub_module=ActivityLogSubModule.BANK_STATEMENT_EXTRACTION,
#                     operation=ActivityLogOperation.BANK_STATEMENT_RECORDING,
#                     status=ActivityLogStatus.COMPLETED,
#                     summary="BANK_STATEMENT_EXTRACTION: Bank statement processing lifecycle completed successfully",
#                     record_id=polling_session_id,  # Use session ID for full traceability
#                     meta_data={
#                         "workflow_details": {
#                             "tenant_id": str(tenant_id),
#                             "user_config_id": str(user_config_id),
#                             "filename": filename,
#                             "email_id": email_id,
#                             "mail_box_email": mail_box_email,
#                             "workflow_stage": "completed",
#                             "operation_type": "main_workflow_completion",
#                         },
#                         "workflow_results": {
#                             "processing_mode": post_processing_mode,
#                             "ocr_service_mode": ocr_service_mode,
#                             "llm_service_mode": llm_service_mode
#                             if post_processing_mode == "AI"
#                             else None,
#                             "transactions_processed": len(data.get("Transactions", [])),
#                             "credit_consumption_enabled": settings.CREDIT_CONSUMPTION_ENABLE,
#                             "data_extracted_successfully": bool(data),
#                         },
#                         "user_impact": f" Successfully completed full bank statement processing workflow with {len(data.get('Transactions', []))} transactions",
#                         "workflow_summary": [
#                             "Email attachment processed",
#                             "Account number validated",
#                             "PDF processed via Azure OCR",
#                             f"{post_processing_mode} post-processing completed",
#                             "Bank statement recorded",
#                             "Transaction matching completed",
#                         ],
#                         "completed_at": datetime.now(UTC).isoformat(),
#                     },
#                 )
#             )

#     except Exception as e:
#         # **MOST IMPORTANT LOG** - Main bank statement processing workflow failed
#         asyncio.get_event_loop().run_until_complete(
#             activity_log_event(
#                 tenant_id=tenant_id,
#                 module=ActivityLogModule.BANK_RECONCILIATION,
#                 sub_module=ActivityLogSubModule.BANK_STATEMENT_EXTRACTION,
#                 operation=ActivityLogOperation.EMAIL_PROCESSING,
#                 status=ActivityLogStatus.FAILED,
#                 summary="BANK_STATEMENT_EXTRACTION: Bank statement processing lifecycle failed",
#                 record_id=polling_session_id,  # Use session ID for full traceability
#                 meta_data={
#                     "workflow_details": {
#                         "tenant_id": str(tenant_id),
#                         "user_config_id": str(user_config_id),
#                         "filename": filename,
#                         "email_id": email_id,
#                         "mail_box_email": mail_box_email,
#                         "workflow_stage": "failed",
#                         "operation_type": "main_workflow_failure",
#                     },
#                     "error_details": {
#                         "error_type": type(e).__name__,
#                         "error_message": str(e),
#                         "traceback": traceback.format_exc(),
#                     },
#                     "user_impact": "Bank statement processing failed",
#                     "failed_at": datetime.now(UTC).isoformat(),
#                 },
#             )
#         )
#         capture_exception(e)
#         print(f"{filename},\n {traceback.format_exc()}")



@celery_app.task(bind=True, ignore_result=True)
def pooling_mail_box(
    self,
    mail_box_config_id,
    frequency: FrequencyType | None = None,
    additional_filter: str | None = None,
):

    try:
        print(f"CurrentDatetime: {datetime.now()}")
        print(f"Frequency: {frequency}")
        print(f"mail_box_config_id: {mail_box_config_id}")

        # Remove the start logging - we'll only log when attachments are found

        mail_box_config = asyncio.get_event_loop().run_until_complete(
            fetch_mail_box_config(mail_box_config_id)
        )
        tenant = asyncio.get_event_loop().run_until_complete(
            get_tenant_data(mail_box_config.tenant_id)
        )
        secret_key = tenant.secret_key

        if not mail_box_config:
            asyncio.get_event_loop().run_until_complete(
                revoke_running_task(mail_box_config_id)
            )
            return
        current_time = datetime.now(UTC).replace(tzinfo=None)
        end_date = mail_box_config.end_date
        provider = mail_box_config.provider
        password = mail_box_config.app_password
        email = mail_box_config.recipient_email
        end_date = datetime.combine(end_date, time.min)

        
        print(f"Current time: {current_time}, End date: {end_date}")
        print(f"MailBox :{email}")
        if current_time >= end_date:
            print(
                f"End date reached for mail_box_config_id: {mail_box_config.id}. Stopping task."
            )
            return
        last_execution_date = asyncio.get_event_loop().run_until_complete(
            get_last_execution_date(mail_box_config_id=mail_box_config_id)
        )
        if last_execution_date is None:
            last_execution_date = datetime.combine(mail_box_config.start_date, time.min)
        company_emails = mail_box_config.company_emails
        subject_lines = mail_box_config.subject_lines
    
        if len(company_emails) >= 1:
            if provider == Providers.MICROSOFT:
                (
                    client_id,
                    redirect_uri,
                    client_secret,
                    refresh_token_validity_days,
                    microsoft_tenant_id,
                ) = asyncio.get_event_loop().run_until_complete(
                    fetch_outlook_settings(mail_box_config.tenant_id)
                )
                list_of_items = fetch_email_outlook(
                    client_id=client_id,
                    client_secret=client_secret,
                    microsoft_tenant_id=microsoft_tenant_id,
                    password=password,
                    last_execution_date=last_execution_date,
                    company_emails=company_emails,
                    subject_lines=subject_lines,
                    additional_filter=additional_filter,
                    app_password_expiry=mail_box_config.app_password_expired_at,
                )
                # No further action required for now after fetching emails
                print(f"Fetched {len(list_of_items)} email(s) from mailbox, no further action taken.")
                return

            polling_session_id = str(ULID())

            attachments_found = 0
            processed_attachments = []

            # for item in list_of_items:
            #     email_extracted = asyncio.get_event_loop().run_until_complete(
            #         is_email_extracted(email_id=item.get("id"))
            #     )
            #     if not email_extracted:
            #         attachment = item.get("attachment")
            #         date = item.get("date")
            #         filename = item.get("filename")
            #         print("filename :", filename)
            #         print(f"{filename}")
            #         if filename[0].lower().endswith(".pdf"):
            #             print("PVT Extraction")
            #             attachments_found += 1
            #             process_attachments.delay(
            #                 attachment,
            #                 date,
            #                 mail_box_config_id,
            #                 mail_box_config.tenant_id,
            #                 secret_key,
            #                 filename,
            #                 item.get("id"),
            #                 email,
            #                 additional_filter,
            #                 polling_session_id,  # Pass session ID for full traceability
            #             )
            
            # Log only if attachments were found and processed
            # if attachments_found > 0:
            #     asyncio.get_event_loop().run_until_complete(
            #         activity_log_event(
            #             tenant_id=user_config.tenant_id,
            #             module=ActivityLogModule.BANK_RECONCILIATION,
            #             sub_module=ActivityLogSubModule.EMAIL_PROCESSING,
            #             operation=ActivityLogOperation.EMAIL_PROCESSING,
            #             status=ActivityLogStatus.COMPLETED,
            #             summary=f"Found and processed {attachments_found} email attachments",
            #             record_id=polling_session_id,  # Use unique session ID for traceability
            #             meta_data={
            #                 "result_details": {
            #                     "polling_session_id": polling_session_id,
            #                     "total_emails_checked": len(list_of_items),
            #                     "attachments_found": attachments_found,
            #                     "processed_attachments": processed_attachments,
            #                     "provider": provider,
            #                     "mailbox_email": email,
            #                     "mail_box_config_id": str(mail_box_config_id),
            #                     "last_execution_date": last_execution_date.isoformat()
            #                     if last_execution_date
            #                     else None,
            #                 },
            #                 "user_impact": f"Successfully initiated processing of {attachments_found} email attachments",
            #                 "completed_at": datetime.now(UTC).isoformat(),
            #             },
            #         )
            #     )
    except Exception as e:
        capture_exception(e)
        print(str(traceback.format_exc()))

    task_id = str(ULID())
    asyncio.get_event_loop().run_until_complete(
        redis.set(name=str(mail_box_config_id), value=task_id)
    )

    match frequency:
        case FrequencyType.DAILY:
            days = 1
            eta = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=days)
        case FrequencyType.WEEKLY:
            days = 7
            eta = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=days)
        case FrequencyType.MONTHLY:
            days = 30
            eta = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=days)
        case FrequencyType.SECONDLY30:
            seconds = 30
            eta = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=seconds)
        case FrequencyType.SECONDLY60:
            seconds = 60
            eta = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=seconds)
        case _:
            seconds = 30
            eta = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=seconds)

    if frequency:
        self.apply_async(
            eta=eta,
            task_id=task_id,
            args=[mail_box_config_id, frequency, additional_filter],
        )
