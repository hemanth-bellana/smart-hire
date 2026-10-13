
import stat
from pathlib import Path, PurePosixPath, PureWindowsPath
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, status


ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}

MAX_FILES_PER_ZIP = 50
MAX_TOTAL_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10 MB per resume
CHUNK_SIZE = 64 * 1024


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def _validate_member_name(name: str) -> Path:
    """Reject absolute paths and traversal across POSIX and Windows paths."""

    posix_path = PurePosixPath(name)
    windows_path = PureWindowsPath(name)

    if (
        not name
        or "\x00" in name
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or ".." in posix_path.parts
        or ".." in windows_path.parts
    ):
        raise _bad_request("ZIP contains an unsafe file path.")

    parts = [
        part for part in posix_path.parts
        if part not in ("", ".")
    ]

    if not parts:
        raise _bad_request("ZIP contains an invalid file path.")

    return Path(*parts)


def _validate_members(zip_file: ZipFile) -> list:
    members = zip_file.infolist()

    if not members:
        raise _bad_request("ZIP file is empty.")

    if len(members) > MAX_FILES_PER_ZIP:
        raise _bad_request(
            f"ZIP contains too many entries. Maximum is {MAX_FILES_PER_ZIP}."
        )

    total_size = 0
    valid_files = []
    seen_paths: set[str] = set()

    for member in members:
        relative_path = _validate_member_name(member.filename)

        if member.is_dir():
            continue

        # Reject Unix symbolic links and other non-regular file entries.
        unix_mode = member.external_attr >> 16
        file_type = stat.S_IFMT(unix_mode)

        if file_type not in (0, stat.S_IFREG):
            raise _bad_request(
                "ZIP contains an unsupported special file."
            )

        extension = relative_path.suffix.lower()

        if extension not in ALLOWED_RESUME_EXTENSIONS:
            raise _bad_request(
                f"Unsupported file in ZIP: {member.filename}. "
                "Only PDF and DOCX files are allowed."
            )

        if member.file_size > MAX_RESUME_SIZE:
            raise _bad_request(
                "A resume in the ZIP exceeds the 10 MB file-size limit."
            )

        total_size += member.file_size

        if total_size > MAX_TOTAL_UNCOMPRESSED_SIZE:
            raise _bad_request(
                "ZIP contents are too large. Maximum total size is 50 MB."
            )

        normalized_name = relative_path.as_posix().casefold()

        if normalized_name in seen_paths:
            raise _bad_request(
                "ZIP contains duplicate resume paths."
            )

        seen_paths.add(normalized_name)
        valid_files.append((member, relative_path))

    if not valid_files:
        raise _bad_request(
            "ZIP does not contain any PDF or DOCX resumes."
        )

    return valid_files


def validate_zip_file(zip_path: str) -> list[str]:
    """Validate the archive and return the accepted resume member names."""

    path = Path(zip_path)

    if not path.is_file():
        raise _bad_request("ZIP file not found.")

    try:
        with ZipFile(path, "r") as zip_file:
            valid_files = _validate_members(zip_file)

            # Check archive integrity before extraction.
            bad_member = zip_file.testzip()

            if bad_member is not None:
                raise _bad_request("ZIP contains a corrupted file.")

            return [member.filename for member, _ in valid_files]

    except BadZipFile as exc:
        raise _bad_request("Invalid or corrupted ZIP file.") from exc


def extract_zip_file(
    zip_path: str,
    extract_directory: str,
) -> list[str]:
    """Validate and extract resume files without trusting archive paths."""

    zip_file_path = Path(zip_path)
    destination = Path(extract_directory).resolve()

    if not zip_file_path.is_file():
        raise _bad_request("ZIP file not found.")

    try:
        with ZipFile(zip_file_path, "r") as zip_file:
            valid_files = _validate_members(zip_file)

            bad_member = zip_file.testzip()

            if bad_member is not None:
                raise _bad_request("ZIP contains a corrupted file.")

            destination.mkdir(parents=True, exist_ok=True)
            extracted_files = []

            for member, relative_path in valid_files:
                target_path = (destination / relative_path).resolve()

                if not target_path.is_relative_to(destination):
                    raise _bad_request("ZIP contains an unsafe file path.")

                target_path.parent.mkdir(parents=True, exist_ok=True)

                bytes_written = 0

                with zip_file.open(member, "r") as source:
                    with target_path.open("xb") as target:
                        while True:
                            chunk = source.read(CHUNK_SIZE)

                            if not chunk:
                                break

                            bytes_written += len(chunk)

                            if bytes_written > MAX_RESUME_SIZE:
                                raise _bad_request(
                                    "Extracted resume exceeds the 10 MB limit."
                                )

                            target.write(chunk)

                if bytes_written != member.file_size:
                    raise _bad_request(
                        "Extracted file size does not match ZIP metadata."
                    )

                extracted_files.append(str(target_path))

            return extracted_files

    except BadZipFile as exc:
        raise _bad_request("Invalid or corrupted ZIP file.") from exc
