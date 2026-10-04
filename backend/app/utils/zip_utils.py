from pathlib import Path
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, status


ALLOWED_RESUME_EXTENSIONS = {
    ".pdf",
    ".docx",
}

MAX_FILES_PER_ZIP = 50
MAX_TOTAL_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50 MB


def validate_zip_file(zip_path: str) -> list[str]:
    """
    Validate the contents of a ZIP file before extraction.

    Checks:
    - ZIP integrity
    - Maximum number of files
    - Allowed resume extensions
    - Path traversal attempts
    - Total uncompressed size
    """

    path = Path(zip_path)

    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP file not found.",
        )

    try:
        with ZipFile(path, "r") as zip_file:
            members = zip_file.infolist()

            if not members:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP file is empty.",
                )

            if len(members) > MAX_FILES_PER_ZIP:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"ZIP contains too many files. "
                        f"Maximum is {MAX_FILES_PER_ZIP}."
                    ),
                )

            total_size = 0
            valid_files = []

            for member in members:
                member_path = Path(member.filename)

                # Ignore directories.
                if member.is_dir():
                    continue

                # Prevent absolute paths and path traversal.
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="ZIP contains an unsafe file path.",
                    )

                extension = member_path.suffix.lower()

                if extension not in ALLOWED_RESUME_EXTENSIONS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Unsupported file in ZIP: {member.filename}. "
                            "Only PDF and DOCX files are allowed."
                        ),
                    )

                total_size += member.file_size

                if total_size > MAX_TOTAL_UNCOMPRESSED_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            "ZIP contents are too large. "
                            "Maximum total size is 50 MB."
                        ),
                    )

                valid_files.append(member.filename)

            if not valid_files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "ZIP does not contain any PDF or DOCX resumes."
                    ),
                )

            return valid_files

    except BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted ZIP file.",
        )
def extract_zip_file(
    zip_path: str,
    extract_directory: str,
) -> list[str]:
    """
    Safely extract validated resume files from a ZIP.

    Returns the paths of the extracted PDF/DOCX files.
    """

    zip_file_path = Path(zip_path)
    destination = Path(extract_directory)

    if not zip_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP file not found.",
        )

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    extracted_files = []

    try:
        with ZipFile(zip_file_path, "r") as zip_file:
            for member in zip_file.infolist():

                # Ignore directories.
                if member.is_dir():
                    continue

                member_path = Path(member.filename)

                # Only extract PDF and DOCX files.
                if member_path.suffix.lower() not in ALLOWED_RESUME_EXTENSIONS:
                    continue

                # Resolve the final extraction path.
                target_path = (destination / member.filename).resolve()
                destination_path = destination.resolve()

                # Prevent path traversal.
                if not target_path.is_relative_to(destination_path):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="ZIP contains an unsafe file path.",
                    )

                # Create parent directories if needed.
                target_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with zip_file.open(member) as source:
                    target_path.write_bytes(source.read())

                extracted_files.append(str(target_path))

        return extracted_files

    except BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted ZIP file.",
        )