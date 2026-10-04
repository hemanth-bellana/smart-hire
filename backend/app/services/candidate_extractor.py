import re


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)"
    r"(?:\+?\d{1,3}[-.\s]?)?"
    r"(?:\(?\d{3,5}\)?[-.\s]?)?"
    r"\d{3,5}[-.\s]?\d{3,5}"
    r"(?!\d)"
)


def extract_email(text: str) -> str | None:
    """
    Extract the first email address found in the resume text.
    """

    match = EMAIL_PATTERN.search(text)

    if match:
        return match.group(0)

    return None


def extract_phone(text: str) -> str | None:
    """
    Extract the first phone number found in the resume text.
    """

    match = PHONE_PATTERN.search(text)

    if match:
        return match.group(0).strip()

    return None


def extract_name(text: str) -> str | None:
    """
    Extract a candidate name using the first meaningful line
    of the resume.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return None

    first_line = lines[0]

    # Ignore lines that clearly look like section headings.
    ignored_headings = {
        "resume",
        "curriculum vitae",
        "cv",
        "summary",
        "profile",
        "objective",
    }

    if first_line.lower() in ignored_headings:
        return None

    # Avoid treating an email address as the candidate name.
    if EMAIL_PATTERN.fullmatch(first_line):
        return None

    # Avoid treating a phone number as the candidate name.
    if PHONE_PATTERN.fullmatch(first_line):
        return None

    return first_line


def extract_location(text: str) -> str | None:
    location_pattern = re.compile(
        r"\b(?:location|address|based in|located in)\s*[:\-]\s*(.+)",
        re.IGNORECASE,
    )

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        # First, check explicitly labelled locations.
        match = location_pattern.search(line)

        if match:
            return match.group(1).strip()

        # Handle resume headers where location appears
        # together with phone number and email.
        if EMAIL_PATTERN.search(line) and PHONE_PATTERN.search(line):
            cleaned_line = EMAIL_PATTERN.sub("", line)
            cleaned_line = PHONE_PATTERN.sub("", cleaned_line)

            cleaned_line = re.sub(r"[|•,]{2,}", " ", cleaned_line)
            cleaned_line = cleaned_line.strip(" |•,-")

            if cleaned_line:
                return cleaned_line

    return None