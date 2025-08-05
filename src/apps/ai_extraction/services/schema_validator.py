"""Schema Validator - JSON validation and repair utilities"""

import json
import logging
import re
from typing import Any, Dict, Optional

from apps.ai_extraction.exceptions import ValidationError
from apps.ai_extraction.schemas.request import DocType
from apps.ai_extraction.schemas.response import ValidationResult
from constants.config import DOC_TYPE_SCHEMAS

# import jsonrepair


class SchemaValidator:
    """Utility for validating and repairing JSON responses against schemas."""

    _logger = logging.getLogger(__name__)

    @staticmethod
    def validate(
        json_str: str, doc_type: DocType, agent_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate JSON against document type schema.

        Ensures JSON complies with schema; attempts repair first if needed.

        Args:
            json_str: JSON string to validate
            doc_type: Document type for schema selection
            agent_code: Optional agent code for agent-specific schema validation

        Returns:
            Validated data dictionary

        Raises:
            ValidationError: When validation fails after repair attempts
        """
        SchemaValidator._logger.info(
            f"Starting JSON validation - DocType: {doc_type}, Agent: {agent_code}, Length: {len(json_str)}"
        )

        # First, try to parse the JSON
        try:
            # Try to extract JSON from markdown code blocks
            pattern = r"```json\s*({[\s\S]*?})\s*```"
            match = re.search(pattern, json_str)
            if match:
                json_str = match.group(1)
                SchemaValidator._logger.debug(
                    f"Extracted JSON from markdown code block - DocType: {doc_type}"
                )

            data = json.loads(json_str)
            SchemaValidator._logger.info(
                f"JSON parsing successful - DocType: {doc_type}, Agent: {agent_code}"
            )

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {str(e)}"
            SchemaValidator._logger.error(
                f"JSON parsing failed - DocType: {doc_type}, Agent: {agent_code}, Error: {error_msg}"
            )
            raise ValidationError(error_msg)

        # Validate against schema if available
        # schema_cls = DOC_TYPE_SCHEMAS.get(doc_type)

        # if schema_cls:
        #     try:
        #         validated_instance = schema_cls.model_validate(data)
        #         SchemaValidator._logger.info(f"Schema validation successful - DocType: {doc_type}, Agent: {agent_code}")
        #         return validated_instance.model_dump()
        #     except Exception as e:
        #         error_msg = f"Schema validation failed: {str(e)}"
        #         SchemaValidator._logger.error(f"Schema validation failed - DocType: {doc_type}, Agent: {agent_code}, Error: {error_msg}")
        #         raise ValidationError(error_msg)
        # else:
        #     # No specific schema - basic validation
        #     if not isinstance(data, dict):
        #         error_msg = "Expected JSON object, got other type"
        #         SchemaValidator._logger.error(f"Basic validation failed - DocType: {doc_type}, Agent: {agent_code}, Error: {error_msg}")
        #         raise ValidationError(error_msg)
        #
        #     SchemaValidator._logger.info(f"Basic validation successful - DocType: {doc_type}, Agent: {agent_code}")

        # For now, just return the parsed data
        field_count = len(data) if isinstance(data, dict) else 0
        SchemaValidator._logger.info(
            f"Validation completed - DocType: {doc_type}, Agent: {agent_code}, Fields: {field_count}"
        )
        return data

    @staticmethod
    def validate_with_result(json_str: str, doc_type: DocType) -> ValidationResult:
        """Validate JSON and return detailed validation result.

        Args:
            json_str: JSON string to validate
            doc_type: Document type for schema selection

        Returns:
            ValidationResult with detailed information
        """
        SchemaValidator._logger.info(
            f"Starting detailed validation - DocType: {doc_type}, Length: {len(json_str)}"
        )

        repaired = False

        try:
            # First, try to parse the JSON
            try:
                data = json.loads(json_str)
                SchemaValidator._logger.debug(
                    f"JSON parsing successful - DocType: {doc_type}"
                )
            except json.JSONDecodeError:
                # Try to repair the JSON
                SchemaValidator._logger.warning(
                    f"JSON parsing failed, attempting repair - DocType: {doc_type}"
                )
                # data = jsonrepair.repair_json(json_str)
                # repaired = True
                # For now, just raise the error
                raise ValidationError("JSON parsing failed and repair not implemented")

            # Validate against schema if available
            schema_cls = DOC_TYPE_SCHEMAS.get(doc_type)

            if schema_cls:
                try:
                    validated_instance = schema_cls.model_validate(data)
                    validated_data = validated_instance.model_dump()
                    SchemaValidator._logger.info(
                        f"Schema validation successful - DocType: {doc_type}, Fields: {len(validated_data)}"
                    )
                except Exception as e:
                    error_msg = f"Schema validation failed: {str(e)}"
                    SchemaValidator._logger.error(
                        f"Schema validation failed - DocType: {doc_type}, Error: {error_msg}"
                    )
                    raise ValidationError(error_msg)
            else:
                # No specific schema - basic validation
                if not isinstance(data, dict):
                    error_msg = "Expected JSON object, got other type"
                    SchemaValidator._logger.error(
                        f"Basic validation failed - DocType: {doc_type}, Error: {error_msg}"
                    )
                    raise ValidationError(error_msg)
                validated_data = data
                SchemaValidator._logger.info(
                    f"Basic validation successful - DocType: {doc_type}, Fields: {len(validated_data)}"
                )

            return ValidationResult(
                is_valid=True,
                validated_data=validated_data,
                errors=None,
                repaired=repaired,
            )

        except ValidationError as e:
            SchemaValidator._logger.error(
                f"Validation failed - DocType: {doc_type}, Error: {str(e)}"
            )
            return ValidationResult(
                is_valid=False, validated_data=None, errors=[str(e)], repaired=repaired
            )
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            SchemaValidator._logger.error(
                f"Unexpected validation error - DocType: {doc_type}, Error: {error_msg}",
                exc_info=True,
            )
            return ValidationResult(
                is_valid=False,
                validated_data=None,
                errors=[error_msg],
                repaired=repaired,
            )

    @staticmethod
    def repair_json(json_str: str) -> str:
        """Attempt to repair malformed JSON.

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Repaired JSON string

        Raises:
            ValidationError: When repair is not possible
        """
        SchemaValidator._logger.info(
            f"Attempting JSON repair - Length: {len(json_str)}"
        )

        try:
            # First check if it's already valid
            json.loads(json_str)
            SchemaValidator._logger.info("JSON is already valid, no repair needed")
            return json_str
        except json.JSONDecodeError:
            SchemaValidator._logger.warning("JSON is malformed, attempting repair")

        try:
            # repaired = jsonrepair.repair_json(json_str)
            # SchemaValidator._logger.info("JSON repair successful")
            # return repaired

            # For now, just raise an error since jsonrepair is not available
            raise ValidationError("JSON repair not implemented")

        except Exception as e:
            error_msg = f"JSON repair failed: {str(e)}"
            SchemaValidator._logger.error(f"JSON repair failed - Error: {error_msg}")
            raise ValidationError(error_msg)

    @staticmethod
    def _basic_json_cleanup(json_str: str) -> str:
        """Basic JSON cleanup for common issues.

        Args:
            json_str: JSON string to clean

        Returns:
            Cleaned JSON string
        """
        SchemaValidator._logger.debug(
            f"Performing basic JSON cleanup - Length: {len(json_str)}"
        )

        # Remove common markdown artifacts
        cleaned = json_str.strip()

        # Remove markdown code block markers
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
            SchemaValidator._logger.debug("Removed ```json prefix")
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
            SchemaValidator._logger.debug("Removed ``` prefix")

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            SchemaValidator._logger.debug("Removed ``` suffix")

        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()

        # Try to find JSON object boundaries
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            cleaned = cleaned[start_idx : end_idx + 1]
            SchemaValidator._logger.debug("Extracted JSON object boundaries")

        SchemaValidator._logger.debug(
            f"JSON cleanup completed - New length: {len(cleaned)}"
        )
        return cleaned

    @staticmethod
    def get_schema_info(doc_type: DocType) -> Dict[str, Any]:
        """Get information about the schema for a document type.

        Args:
            doc_type: Document type to inspect

        Returns:
            Dictionary with schema information
        """
        SchemaValidator._logger.info(f"Getting schema info - DocType: {doc_type}")

        schema_cls = DOC_TYPE_SCHEMAS.get(doc_type)

        if not schema_cls:
            SchemaValidator._logger.warning(
                f"No schema defined for doc type: {doc_type}"
            )
            return {
                "exists": False,
                "doc_type": doc_type,
                "message": f"No schema defined for {doc_type}",
            }

        try:
            # TODO: Extract schema info when schemas are defined
            SchemaValidator._logger.info(f"Schema found for doc type: {doc_type}")
            return {
                "exists": True,
                "doc_type": doc_type,
                "schema_name": schema_cls.__name__,
                "fields": [],  # schema_cls.model_fields.keys()
                "message": "Schema available",
            }
        except Exception as e:
            error_msg = f"Schema introspection failed: {str(e)}"
            SchemaValidator._logger.error(
                f"Schema introspection failed - DocType: {doc_type}, Error: {error_msg}"
            )
            return {
                "exists": True,
                "doc_type": doc_type,
                "error": str(e),
                "message": "Schema introspection failed",
            }
