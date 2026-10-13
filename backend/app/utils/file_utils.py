
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, UploadFile, status


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".zip"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

DOCX_REQUIRED_FILES = {
    "[Content_Types].xml",
    "word/document.xml",
}


def _validate_file_signature(extension: str, contents: bytes) -> None:
    """Check file content instead of trusting the supplied MIME type."""

    if extension == ".pdf":
        if not contents.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file content.",
            )
        return

    if extension not in {".docx", ".zip"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported resume format.",
        )

    try:
        with ZipFile(BytesIO(contents)) as archive:
            if extension == ".docx":
                names = set(archive.namelist())

                if not DOCX_REQUIRED_FILES.issubset(names):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid DOCX file content.",
                    )

            else:
                if not archive.namelist():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="ZIP file is empty.",
                    )

    except BadZipFile as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {extension[1:].upper()} file content.",
        ) from exc


async def validate_resume_file(file: UploadFile) -> bytes:
    """Validate an upload with a bounded read before returning its bytes."""

    if not file.filename or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume filename is missing.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported resume format. "
                "Only PDF, DOCX, and ZIP files are allowed."
            ),
        )

    # Read at most one byte beyond the limit to detect oversized uploads.
    contents = await file.read(MAX_FILE_SIZE + 1)

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume file is empty.",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Resume file is too large. Maximum size is 10 MB.",
        )

    _validate_file_signature(extension, contents)

    return contents
