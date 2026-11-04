from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.pdf_parser import extract_text_from_pdf


def test_extracts_text_from_all_pdf_pages(tmp_path: Path):
    file_path = tmp_path / "resume.pdf"
    file_path.write_bytes(b"fake pdf")

    page_one = MagicMock()
    page_one.get_text.return_value = "Python Developer"

    page_two = MagicMock()
    page_two.get_text.return_value = "Experience: 3 years"

    document = MagicMock()
    document.__iter__.return_value = [page_one, page_two]

    with patch(
        "app.services.pdf_parser.pymupdf.open",
        return_value=document,
    ):
        result = extract_text_from_pdf(str(file_path))

    assert result == "Python Developer\nExperience: 3 years"
    document.close.assert_called_once()


def test_missing_pdf_raises_file_not_found(tmp_path: Path):
    file_path = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf(str(file_path))


def test_corrupt_pdf_raises_parsing_error(tmp_path: Path):
    file_path = tmp_path / "corrupt.pdf"
    file_path.write_text("This is not a PDF file.", encoding="utf-8")

    with patch(
        "app.services.pdf_parser.pymupdf.open",
        side_effect=ValueError("Invalid PDF"),
    ):
        with pytest.raises(ValueError, match="Invalid PDF"):
            extract_text_from_pdf(str(file_path))


def test_closes_pdf_when_page_extraction_fails(tmp_path: Path):
    file_path = tmp_path / "broken-page.pdf"
    file_path.write_bytes(b"fake pdf")

    page = MagicMock()
    page.get_text.side_effect = RuntimeError("Page extraction failed")

    document = MagicMock()
    document.__iter__.return_value = [page]

    with patch(
        "app.services.pdf_parser.pymupdf.open",
        return_value=document,
    ):
        with pytest.raises(RuntimeError, match="Page extraction failed"):
            extract_text_from_pdf(str(file_path))

    document.close.assert_called_once()