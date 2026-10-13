
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi import HTTPException

from app.utils.zip_utils import (
    MAX_RESUME_SIZE,
    extract_zip_file,
    validate_zip_file,
)


def create_zip(
    zip_path: Path,
    files: dict[str, bytes],
) -> Path:
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for filename, contents in files.items():
            archive.writestr(filename, contents)

    return zip_path


def test_validates_zip_with_pdf_and_docx(tmp_path: Path) -> None:
    zip_path = create_zip(
        tmp_path / "resumes.zip",
        {
            "candidate.pdf": b"%PDF-1.7 sample",
            "folder/candidate.docx": b"docx placeholder",
        },
    )

    result = validate_zip_file(str(zip_path))

    assert result == [
        "candidate.pdf",
        "folder/candidate.docx",
    ]


@pytest.mark.parametrize(
    "filename",
    [
        "../outside.pdf",
        "folder/../../outside.pdf",
        r"..\outside.pdf",
        r"C:\outside.pdf",
        "/outside.pdf",
    ],
)
def test_rejects_unsafe_paths(
    tmp_path: Path,
    filename: str,
) -> None:
    zip_path = create_zip(
        tmp_path / "unsafe.zip",
        {filename: b"resume"},
    )

    with pytest.raises(HTTPException) as exc:
        validate_zip_file(str(zip_path))

    assert exc.value.status_code == 400


def test_rejects_duplicate_paths_case_insensitively(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "duplicates.zip",
        {
            "Resume.pdf": b"first",
            "resume.PDF": b"second",
        },
    )

    with pytest.raises(HTTPException, match="duplicate"):
        validate_zip_file(str(zip_path))


def test_rejects_unsupported_file_types(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "unsupported.zip",
        {"notes.txt": b"not a resume"},
    )

    with pytest.raises(HTTPException, match="Unsupported file"):
        validate_zip_file(str(zip_path))


def test_rejects_individual_resume_over_size_limit(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "oversized.zip",
        {"large.pdf": b"x" * (MAX_RESUME_SIZE + 1)},
    )

    with pytest.raises(HTTPException, match="10 MB"):
        validate_zip_file(str(zip_path))


def test_extracts_files_into_destination(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "resumes.zip",
        {
            "candidate.pdf": b"%PDF-1.7 sample",
            "nested/candidate.docx": b"docx placeholder",
        },
    )
    destination = tmp_path / "extracted"

    extracted = extract_zip_file(
        str(zip_path),
        str(destination),
    )

    assert len(extracted) == 2
    assert (destination / "candidate.pdf").read_bytes() == (
        b"%PDF-1.7 sample"
    )
    assert (
        destination / "nested" / "candidate.docx"
    ).read_bytes() == b"docx placeholder"


def test_extraction_does_not_overwrite_existing_file(
    tmp_path: Path,
) -> None:
    zip_path = create_zip(
        tmp_path / "resumes.zip",
        {"candidate.pdf": b"new content"},
    )
    destination = tmp_path / "extracted"
    destination.mkdir()
    existing_file = destination / "candidate.pdf"
    existing_file.write_bytes(b"original content")

    with pytest.raises(FileExistsError):
        extract_zip_file(str(zip_path), str(destination))

    assert existing_file.read_bytes() == b"original content"


def test_rejects_corrupt_zip(
    tmp_path: Path,
) -> None:
    zip_path = tmp_path / "corrupt.zip"
    zip_path.write_bytes(b"not a ZIP archive")

    with pytest.raises(HTTPException, match="corrupted"):
        validate_zip_file(str(zip_path))
