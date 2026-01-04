"""
File validation utilities for upload handling.
"""

import logging

from fastapi import HTTPException, UploadFile, status

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Raised when file validation fails."""

    def __init__(self, message: str, code: str = "FILE_VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


def validate_file_extension(
    filename: str | None,
    allowed_extensions: list[str] | None = None,
    settings: Settings | None = None,
) -> str:
    """
    Validate file extension against allowed extensions.

    Args:
        filename: The filename to validate.
        allowed_extensions: List of allowed extensions (without dots).
        settings: Application settings.

    Returns:
        The validated extension (lowercase, without dot).

    Raises:
        FileValidationError: If extension is not allowed.
    """
    # TODO: Implement extension validation
    # - Extract extension from filename
    # - Normalize to lowercase
    # - Check against allowed list

    if not filename:
        raise FileValidationError("Filename is required", "MISSING_FILENAME")

    settings = settings or get_settings()
    allowed = allowed_extensions or settings.allowed_image_extensions

    # Extract extension
    if "." not in filename:
        raise FileValidationError(
            "File must have an extension",
            "MISSING_EXTENSION",
        )

    extension = filename.rsplit(".", 1)[-1].lower()

    if extension not in [ext.lower() for ext in allowed]:
        raise FileValidationError(
            f"File extension '{extension}' is not allowed. "
            f"Allowed extensions: {', '.join(allowed)}",
            "INVALID_EXTENSION",
        )

    return extension


def validate_file_size(
    file: UploadFile,
    max_size_bytes: int | None = None,
    settings: Settings | None = None,
) -> int:
    """
    Validate file size against maximum allowed.

    Args:
        file: The uploaded file.
        max_size_bytes: Maximum allowed size in bytes.
        settings: Application settings.

    Returns:
        The file size in bytes.

    Raises:
        FileValidationError: If file is too large.
    """
    # TODO: Implement size validation
    # - Check file size
    # - Compare against maximum

    settings = settings or get_settings()
    max_size = max_size_bytes or settings.max_file_size_bytes

    # Get file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        file_mb = file_size / (1024 * 1024)
        raise FileValidationError(
            f"File size ({file_mb:.2f} MB) exceeds maximum allowed ({max_mb:.2f} MB)",
            "FILE_TOO_LARGE",
        )

    return file_size


def validate_mime_type(
    content_type: str | None,
    allowed_types: list[str] | None = None,
    settings: Settings | None = None,
) -> str:
    """
    Validate MIME type against allowed types.

    Args:
        content_type: The file's content type.
        allowed_types: List of allowed MIME types.
        settings: Application settings.

    Returns:
        The validated MIME type.

    Raises:
        FileValidationError: If MIME type is not allowed.
    """
    # TODO: Implement MIME type validation
    # - Check content type is provided
    # - Normalize and compare against allowed list

    if not content_type:
        raise FileValidationError(
            "Content type is required",
            "MISSING_CONTENT_TYPE",
        )

    settings = settings or get_settings()
    allowed = allowed_types or settings.allowed_mime_types

    # Normalize content type (remove parameters like charset)
    mime_type = content_type.split(";")[0].strip().lower()

    if mime_type not in [t.lower() for t in allowed]:
        raise FileValidationError(
            f"MIME type '{mime_type}' is not allowed. " f"Allowed types: {', '.join(allowed)}",
            "INVALID_MIME_TYPE",
        )

    return mime_type


async def validate_image_file(
    file: UploadFile,
    settings: Settings | None = None,
) -> dict:
    """
    Perform comprehensive validation on an image file.

    Validates extension, size, and MIME type.

    Args:
        file: The uploaded file.
        settings: Application settings.

    Returns:
        Dict with validation results including extension, size, and mime_type.

    Raises:
        HTTPException: If validation fails.
    """
    # TODO: Implement comprehensive image validation
    # - Validate extension
    # - Validate size
    # - Validate MIME type
    # - Optionally verify actual file content matches claimed type

    settings = settings or get_settings()

    try:
        extension = validate_file_extension(file.filename, settings=settings)
        file_size = validate_file_size(file, settings=settings)
        mime_type = validate_mime_type(file.content_type, settings=settings)

        # TODO: Optionally verify file magic bytes match claimed type
        # This provides additional security against spoofed content types

        return {
            "extension": extension,
            "size_bytes": file_size,
            "mime_type": mime_type,
            "filename": file.filename,
        }

    except FileValidationError as e:
        logger.warning(f"File validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )


def get_supported_formats(settings: Settings | None = None) -> dict:
    """
    Get information about supported file formats.

    Args:
        settings: Application settings.

    Returns:
        Dict with supported formats information.
    """
    settings = settings or get_settings()

    return {
        "extensions": settings.allowed_image_extensions,
        "mime_types": settings.allowed_mime_types,
        "max_size_mb": settings.max_file_size_mb,
        "max_size_bytes": settings.max_file_size_bytes,
    }
