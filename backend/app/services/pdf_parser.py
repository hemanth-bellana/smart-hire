from pathlib import Path

import pymupdf


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from all pages of a PDF file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {file_path}"
        )

    document = pymupdf.open(file_path)

    try:
        pages_text = []

        for page in document:
            text = page.get_text()
            pages_text.append(text)

        return "\n".join(pages_text).strip()

    finally:
        document.close()