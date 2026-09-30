# extraction/normalizer.py

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize OCR output without destroying useful information.
    """

    # Unicode normalization
    text = unicodedata.normalize(
        "NFKC",
        text
    )

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Common OCR substitutions
    replacements = {
        "–": "-",
        "—": "-",
        "−": "-",
        "µ": "u",
        "º": "°",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Normalize multiple spaces
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def normalize_label(label: str) -> str:
    """
    Normalize a field label for comparison.
    """

    label = label.lower().strip()

    # Remove punctuation
    label = re.sub(
        r"[^\w\s+]",
        " ",
        label
    )

    # Normalize whitespace
    label = re.sub(
        r"\s+",
        " ",
        label
    )

    return label.strip()


def normalize_yes_no(value: str | None):
    if value is None:
        return None

    value = value.lower().strip()

    if value in {
        "yes",
        "y",
        "1",
        "true"
    }:
        return "yes"

    if value in {
        "no",
        "n",
        "0",
        "false"
    }:
        return "no"

    return None


def normalize_normal_abnormal(value: str | None):
    if value is None:
        return None

    value = value.lower().strip()

    if value.startswith("normal"):
        return "normal"

    if value.startswith("abnormal"):
        return "abnormal"

    return None


def normalize_present(value: str | None):
    if value is None:
        return None

    value = value.lower().strip()

    value = value.replace("-", " ")

    if "not present" in value:
        return "notpresent"

    if value == "present":
        return "present"

    return None


def normalize_number(value: str | None):
    """
    Convert an OCR-extracted number to float.

    Handles common OCR errors such as:
        1,200 -> 1200
        1.2. -> 1.2
    """

    if value is None:
        return None

    value = value.strip()

    # Remove commas
    value = value.replace(",", "")

    # Remove trailing punctuation
    value = value.rstrip(".,;:")

    # OCR may read 0 as O/o in some situations.
    # Only apply when the entire value looks numeric.
    if re.fullmatch(r"[Oo]+", value):
        value = value.replace("O", "0").replace("o", "0")

    try:
        return float(value)
    except ValueError:
        return None