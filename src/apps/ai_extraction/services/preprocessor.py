"""PreProcessor - File handling and text extraction utilities"""

import logging
import re
from pathlib import Path
from typing import List

import fitz

from apps.ai_extraction.exceptions import PreProcessError
from apps.ai_extraction.schemas.response import PreProcessResult


class PreProcessor:
    """Utility class for all file → text conversions and document preparation."""

    _logger = logging.getLogger(__name__)

    @staticmethod
    def redact_pdf(src: Path, dst: Path, patterns: List[str]) -> None:
        """Applies in-place redaction rectangles for each regex pattern.

        Writes a new PDF to *dst* so audit can keep the redacted artifact.

        Args:
            src: Source PDF path
            dst: Destination PDF path
            patterns: List of regex patterns to redact

        Raises:
            PreProcessError: On PDF processing failure
        """
        PreProcessor._logger.info(
            f"Starting PDF redaction - Source: {src}, Destination: {dst}, Patterns: {len(patterns)}"
        )

        try:
            doc = fitz.open(src)
            PreProcessor._logger.debug(f"PDF opened successfully - Pages: {len(doc)}")

            redaction_count = 0
            for page_num, page in enumerate(doc):
                page_redactions = 0
                for pattern in patterns:
                    # Find text matching pattern and redact
                    text_instances = page.search_for(pattern)
                    for inst in text_instances:
                        page.add_redact_annot(inst)
                        page_redactions += 1

                if page_redactions > 0:
                    page.apply_redactions()
                    redaction_count += page_redactions
                    PreProcessor._logger.debug(
                        f"Applied {page_redactions} redactions on page {page_num + 1}"
                    )

            doc.save(dst)
            doc.close()

            PreProcessor._logger.info(
                f"PDF redaction completed - Total redactions: {redaction_count}"
            )

        except Exception as e:
            error_msg = f"PDF redaction failed: {str(e)}"
            PreProcessor._logger.error(
                f"PDF redaction error - Source: {src}, Error: {error_msg}",
                exc_info=True,
            )
            raise PreProcessError(error_msg)

    @staticmethod
    def load(path: Path) -> str:
        """Detects mime-type and routes to appropriate extractor.

        Args:
            path: Path to document file

        Returns:
            Extracted text content

        Raises:
            PreProcessError: On unreadable file, OCR failure, or empty output
        """
        PreProcessor._logger.info(f"Loading document - Path: {path}")

        if not path.exists():
            error_msg = f"File not found: {path}"
            PreProcessor._logger.error(f"File not found - Path: {path}")
            raise PreProcessError(error_msg)

        if not path.is_file():
            error_msg = f"Path is not a file: {path}"
            PreProcessor._logger.error(f"Path is not a file - Path: {path}")
            raise PreProcessError(error_msg)

        try:
            file_extension = path.suffix.lower()
            PreProcessor._logger.debug(f"File extension detected: {file_extension}")

            if file_extension == ".pdf":
                PreProcessor._logger.info(f"Processing PDF file - Path: {path}")
                return PreProcessor._extract_pdf_text(path)
            else:
                error_msg = f"Unsupported file type: {file_extension}"
                PreProcessor._logger.error(
                    f"Unsupported file type - Path: {path}, Extension: {file_extension}"
                )
                raise PreProcessError(error_msg)

        except Exception as e:
            error_msg = f"Text extraction failed: {str(e)}"
            PreProcessor._logger.error(
                f"Text extraction error - Path: {path}, Error: {error_msg}",
                exc_info=True,
            )
            raise PreProcessError(error_msg)

    @staticmethod
    def _extract_pdf_text(path: Path) -> str:
        """Extract text from PDF file.

        Args:
            path: Path to PDF file

        Returns:
            Extracted text content
        """
        PreProcessor._logger.info(f"Extracting text from PDF - Path: {path}")

        try:
            doc = fitz.open(path)
            page_count = len(doc)
            PreProcessor._logger.debug(f"PDF opened - Pages: {page_count}")

            text = ""
            total_chars = 0

            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                text += page_text
                total_chars += len(page_text)

                PreProcessor._logger.debug(
                    f"Page {page_num + 1} processed - Characters: {len(page_text)}"
                )

            doc.close()

            if not text.strip():
                error_msg = "PDF contains no extractable text"
                PreProcessor._logger.error(f"No extractable text - Path: {path}")
                raise PreProcessError(error_msg)

            word_count = len(text.split())
            PreProcessor._logger.info(
                f"PDF text extraction completed - Path: {path}, Pages: {page_count}, Characters: {total_chars}, Words: {word_count}"
            )

            return text.strip()

        except Exception as e:
            error_msg = f"PDF text extraction failed: {str(e)}"
            PreProcessor._logger.error(
                f"PDF text extraction error - Path: {path}, Error: {error_msg}",
                exc_info=True,
            )
            raise PreProcessError(error_msg)

    @staticmethod
    def _extract_txt_content(path: Path) -> str:
        """Extract content from text file.

        Args:
            path: Path to text file

        Returns:
            File content
        """
        PreProcessor._logger.info(f"Extracting content from text file - Path: {path}")

        try:
            content = path.read_text(encoding="utf-8")

            if not content.strip():
                error_msg = "Text file is empty"
                PreProcessor._logger.error(f"Text file is empty - Path: {path}")
                raise PreProcessError(error_msg)

            word_count = len(content.split())
            PreProcessor._logger.info(
                f"Text file extraction completed - Path: {path}, Characters: {len(content)}, Words: {word_count}"
            )

            return content.strip()

        except UnicodeDecodeError:
            PreProcessor._logger.warning(
                f"UTF-8 decoding failed, trying latin-1 - Path: {path}"
            )
            # Try with different encoding
            try:
                content = path.read_text(encoding="latin-1")
                word_count = len(content.split())
                PreProcessor._logger.info(
                    f"Text file extraction completed with latin-1 encoding - Path: {path}, Characters: {len(content)}, Words: {word_count}"
                )
                return content.strip()
            except Exception as e:
                error_msg = f"Text file encoding error: {str(e)}"
                PreProcessor._logger.error(
                    f"Text file encoding error - Path: {path}, Error: {error_msg}"
                )
                raise PreProcessError(error_msg)
        except Exception as e:
            error_msg = f"Text file read error: {str(e)}"
            PreProcessor._logger.error(
                f"Text file read error - Path: {path}, Error: {error_msg}"
            )
            raise PreProcessError(error_msg)

    @staticmethod
    def get_file_info(path: Path) -> PreProcessResult:
        """Get detailed information about a file.

        Args:
            path: Path to file

        Returns:
            PreProcessResult with file details
        """
        PreProcessor._logger.info(f"Getting file info - Path: {path}")

        try:
            text_content = PreProcessor.load(path)
            word_count = len(text_content.split())

            # Detect file type and page count
            file_type = path.suffix.lower().lstrip(".")
            page_count = None

            if file_type == "pdf":
                try:
                    import fitz

                    doc = fitz.open(path)
                    page_count = len(doc)
                    doc.close()
                    PreProcessor._logger.debug(
                        f"PDF page count determined - Pages: {page_count}"
                    )
                except Exception as e:
                    PreProcessor._logger.warning(
                        f"Failed to determine PDF page count - Path: {path}, Error: {str(e)}"
                    )

            PreProcessor._logger.info(
                f"File info completed - Path: {path}, Type: {file_type}, Pages: {page_count}, Words: {word_count}"
            )

            return PreProcessResult(
                text_content=text_content,
                file_type=file_type,
                page_count=page_count,
                word_count=word_count,
            )

        except Exception as e:
            error_msg = f"Failed to get file info: {str(e)}"
            PreProcessor._logger.error(
                f"File info error - Path: {path}, Error: {error_msg}", exc_info=True
            )
            raise PreProcessError(error_msg)
