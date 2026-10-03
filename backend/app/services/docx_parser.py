from pathlib import Path

from docx import Document


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from all paragraphs of a DOCX file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"DOCX file not found: {file_path}"
        )

    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs).strip()