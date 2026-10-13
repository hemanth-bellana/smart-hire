
import asyncio
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.utils.file_utils import (
    MAX_FILE_SIZE,
    validate_resume_file,
)


def make_upload(
    filename: str,
    contents: bytes,
    content_type: str = "application/octet-stream",
) -> UploadFile:
    return UploadFile(
        file=BytesIO(contents),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def make_zip(files: dict[str, bytes]) -> bytes:
    buffer = BytesIO()

    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for filename, contents in files.items():
            archive.writestr(filename, contents)

    return buffer.getvalue()


def test_accepts_valid_pdf_signature() -> None:
    upload = make_upload("resume.pdf", b"%PDF-1.7\nsample content")

    result = asyncio.run(validate_resume_file(upload))

    assert result.startswith(b"%PDF-")


def test_rejects_pdf_with_invalid_signature() -> None:
    upload = make_upload("resume.pdf", b"not a PDF")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(validate_resume_file(upload))

    assert exc.value.status_code == 400


def test_rejects_empty_file() -> None:
    upload = make_upload("resume.pdf", b"")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(validate_resume_file(upload))

    assert exc.value.status_code == 400
    assert exc.value.detail == "Resume file is empty."


def test_rejects_oversized_file() -> None:
    upload = make_upload(
        "resume.pdf",
        b"%PDF-" + b"x" * MAX_FILE_SIZE,
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(validate_resume_file(upload))

    assert exc.value.status_code == 413


def test_rejects_unsupported_extension() -> None:
    upload = make_upload("resume.exe", b"some content")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(validate_resume_file(upload))

    assert exc.value.status_code == 400


def test_rejects_corrupt_docx() -> None:
    upload = make_upload("resume.docx", b"not a DOCX")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(validate_resume_file(upload))

    assert exc.value.status_code == 400


def test_accepts_valid_docx_container() -> None:
    contents = make_zip(
        {
            "[Content_Types].xml": b"<Types/>",
            "word/document.xml": b"<document/>",
        }
    )
    upload = make_upload("resume.docx", contents)

    result = asyncio.run(validate_resume_file(upload))

    assert result == contents


def test_rejects_corrupt_zip() -> None:
    upload = make_upload("resumes.zip", b"not a ZIP archive")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(validate_resume_file(upload))

    assert exc.value.status_code == 400


def test_accepts_valid_zip_container() -> None:
    contents = make_zip({"resume.pdf": b"%PDF-1.7\nsample"})
    upload = make_upload("resumes.zip", contents)

    result = asyncio.run(validate_resume_file(upload))

    assert result == contents
