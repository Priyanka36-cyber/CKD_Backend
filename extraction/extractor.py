# extraction/extractor.py

import re

from .field_aliases import FIELD_ALIASES
from .normalizer import (
    normalize_text,
    normalize_number,
    normalize_yes_no,
    normalize_normal_abnormal,
    normalize_present,
)
from .validator import validate_extracted_data


# ============================================================
# MODEL FEATURE ORDER
# ============================================================

FEATURE_COLUMNS = [
    "age",
    "bp",
    "sg",
    "al",
    "su",
    "rbc",
    "pc",
    "pcc",
    "ba",
    "bgr",
    "bu",
    "sc",
    "sod",
    "pot",
    "hemo",
    "pcv",
    "wc",
    "rc",
    "htn",
    "dm",
    "cad",
    "appet",
    "pe",
    "ane",
]


# ============================================================
# FIELD TYPES
# ============================================================

NUMERIC_FIELDS = {
    "age",
    "bp",
    "sg",
    "al",
    "su",
    "bgr",
    "bu",
    "sc",
    "sod",
    "pot",
    "hemo",
    "pcv",
    "wc",
    "rc",
}


# ============================================================
# BASIC HELPERS
# ============================================================

def get_lines(text: str):
    """
    Convert OCR text into clean non-empty lines.
    """

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:
            lines.append(line)

    return lines


def clean_line(line: str):
    """
    Normalize spacing inside a single OCR line.
    """

    line = re.sub(
        r"[ \t]+",
        " ",
        line
    )

    return line.strip()


def normalize_ocr_value(value: str):
    """
    Handle common OCR mistakes before parsing.

    Examples:
        ° -> 0
        O -> 0 when appropriate
    """

    if value is None:
        return None

    value = value.strip()

    # OCR may convert zero into degree symbol
    if value == "°":
        return "0"

    return value


# ============================================================
# ALIAS SEARCH
# ============================================================

def find_alias_in_line(
    field: str,
    line: str
):
    """
    Find the best matching alias for a field.

    Longest aliases are checked first so that:

        "blood glucose fasting"

    is preferred over:

        "glucose"
    """

    aliases = FIELD_ALIASES.get(
        field,
        []
    )

    aliases = sorted(
        aliases,
        key=len,
        reverse=True
    )

    normalized_line = line.lower()

    for alias in aliases:

        alias_lower = alias.lower()

        if alias_lower in normalized_line:

            return alias

    return None


# ============================================================
# REMOVE FIELD LABEL
# ============================================================

def extract_result_after_label(
    line: str,
    alias: str
):
    """
    Return the text occurring after a field label.

    Example:

        Blood Urea 36 mg/dL 15-45

    becomes:

        36 mg/dL 15-45
    """

    pattern = re.escape(alias)

    match = re.search(
        pattern,
        line,
        re.IGNORECASE
    )

    if not match:
        return None

    remaining = line[
        match.end():
    ].strip()

    # Remove separators such as:
    #
    # :
    # -
    # >
    # |
    #
    remaining = re.sub(
        r"^[\s:|>]+",
        "",
        remaining
    )

    return remaining.strip()


# ============================================================
# NUMERIC EXTRACTION
# ============================================================

def extract_first_number(text: str):
    """
    Extract the first numeric value from text.

    Examples:

        "121 mg/dL" -> 121
        "1.2 mg/dL" -> 1.2
        "7800 cells/cumm" -> 7800
        "5.2 millions/cumm" -> 5.2
    """

    if not text:
        return None

    text = normalize_ocr_value(text)

    match = re.search(
        r"(?<![\w.])"
        r"(\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)",
        text
    )

    if not match:
        return None

    return normalize_number(
        match.group(1)
    )


def extract_numeric_field(
    field: str,
    lines: list[str]
):
    """
    Extract a numeric field from OCR text.

    IMPORTANT:
    We only look for the value immediately after
    the field label.

    This prevents reference ranges from being
    accidentally interpreted as patient results.
    """

    for line in lines:

        alias = find_alias_in_line(
            field,
            line
        )

        if not alias:
            continue

        remaining = extract_result_after_label(
            line,
            alias
        )

        if not remaining:
            continue

        remaining = remaining.strip()

        # --------------------------------------------------
        # If the result begins with a dash, it is missing.
        #
        # Example:
        #
        # Sodium (Na+) - mEq/L 135-145
        #
        # -> None
        # --------------------------------------------------

        if re.match(
            r"^[\-–—]",
            remaining
        ):
            return None

        # --------------------------------------------------
        # Extract the first token.
        #
        # This is safer than searching the entire line.
        # --------------------------------------------------

        first_token = remaining.split()[0]

        first_token = first_token.strip(
            ":,;."
        )

        # --------------------------------------------------
        # OCR zero mistakes
        # --------------------------------------------------

        if first_token in {
            "°",
            "o",
            "O"
        }:

            return 0.0

        # --------------------------------------------------
        # Numeric conversion
        # --------------------------------------------------

        value = normalize_number(
            first_token
        )

        if value is not None:
            return value

        # --------------------------------------------------
        # Sometimes OCR puts a separator between label
        # and result.
        #
        # Example:
        #
        # Creatinine : 1.2
        # --------------------------------------------------

        value = extract_first_number(
            remaining
        )

        return value

    return None


# ============================================================
# SUGAR EXTRACTION
# ============================================================

def extract_sugar(lines):
    """
    Extract urine sugar.

    Handles OCR variations such as:

        Sugar 0
        Sugar °
        Sugar o
        Sugar Negative
    """

    for line in lines:

        alias = find_alias_in_line(
            "su",
            line
        )

        if not alias:
            continue

        remaining = extract_result_after_label(
            line,
            alias
        )

        if not remaining:
            continue

        remaining = remaining.strip()

        # OCR may convert 0 into ° or o
        if re.match(
            r"^(0|°|o|O)(?:\s|$)",
            remaining
        ):
            return 0.0

        # Negative urine sugar
        if re.match(
            r"^negative\b",
            remaining,
            re.IGNORECASE
        ):
            return 0.0

        # Numeric sugar value
        value = extract_first_number(
            remaining
        )

        if value is not None:
            return value

    return None


# ============================================================
# OPTIONAL LAB VALUE
# ============================================================

def extract_optional_lab_value(
    field: str,
    lines: list[str]
):
    """
    Extract lab values such as Sodium/Potassium.

    Important distinction:

        Sodium - mEq/L 135-145

    means the patient result is missing.

    Whereas:

        Sodium 138 mEq/L 135-145

    means:

        sodium = 138
    """

    for line in lines:

        alias = find_alias_in_line(
            field,
            line
        )

        if not alias:
            continue

        remaining = extract_result_after_label(
            line,
            alias
        )

        if not remaining:
            continue

        remaining = remaining.strip()

        # --------------------------------------------------
        # Missing result
        # --------------------------------------------------

        if re.match(
            r"^[\-–—]",
            remaining
        ):
            return None

        # --------------------------------------------------
        # Result must begin with a number.
        #
        # This prevents:
        #
        # mEq/L 135-145
        #
        # from becoming:
        #
        # 135
        # --------------------------------------------------

        match = re.match(
            r"^(\d+(?:\.\d+)?)",
            remaining
        )

        if not match:
            return None

        return normalize_number(
            match.group(1)
        )

    return None


# ============================================================
# CATEGORICAL EXTRACTION
# ============================================================

def extract_categorical_field(
    field: str,
    lines: list[str],
    possible_values
):
    """
    Extract categorical values.

    Multi-word values such as:

        Not Present

    are checked before:

        Present

    to prevent substring errors.
    """

    for line in lines:

        alias = find_alias_in_line(
            field,
            line
        )

        if not alias:
            continue

        remaining = extract_result_after_label(
            line,
            alias
        )

        if not remaining:
            continue

        # --------------------------------------------------
        # Check longest values first
        # --------------------------------------------------

        sorted_values = sorted(
            possible_values,
            key=len,
            reverse=True
        )

        for value in sorted_values:

            pattern = (
                rf"(?<!\w)"
                rf"{re.escape(value)}"
                rf"(?!\w)"
            )

            match = re.search(
                pattern,
                remaining,
                re.IGNORECASE
            )

            if match:

                return value

    return None


# ============================================================
# YES / NO EXTRACTION
# ============================================================

def extract_yes_no_field(
    field: str,
    lines: list[str]
):
    """
    Extract Yes/No values.

    Example:

        Diabetes Mellitus (DM) : Yes
        -> yes
    """

    for line in lines:

        alias = find_alias_in_line(
            field,
            line
        )

        if not alias:
            continue

        remaining = extract_result_after_label(
            line,
            alias
        )

        if not remaining:
            continue

        # --------------------------------------------------
        # Look for Yes/No immediately after the label.
        # --------------------------------------------------

        match = re.search(
            r"\b(Yes|No)\b",
            remaining,
            re.IGNORECASE
        )

        if match:

            return normalize_yes_no(
                match.group(1)
            )

    return None


# ============================================================
# PEDAL EDEMA
# ============================================================

def extract_pedal_edema(lines):
    """
    Extract Pedal Edema.

    Handles:

        Pedal Edema : No

    and prevents unrelated Yes/No values
    from being selected.
    """

    for line in lines:

        match = re.search(
            r"Pedal\s+Edema\s*[:\-]?\s*"
            r"(Yes|No)\b",
            line,
            re.IGNORECASE
        )

        if match:

            return normalize_yes_no(
                match.group(1)
            )

    return None


# ============================================================
# APPETITE
# ============================================================

def extract_appetite(lines):

    for line in lines:

        alias = find_alias_in_line(
            "appet",
            line
        )

        if not alias:
            continue

        remaining = extract_result_after_label(
            line,
            alias
        )

        if not remaining:
            continue

        match = re.search(
            r"\b(Good|Poor)\b",
            remaining,
            re.IGNORECASE
        )

        if match:

            return match.group(1).lower()

    return None


# ============================================================
# AGE
# ============================================================

def extract_age(lines):

    for line in lines:

        # Example:
        #
        # Age / Gender : 48 Years / Male
        #

        match = re.search(
            r"Age\s*/\s*Gender\s*"
            r"[:\-]?\s*"
            r"(\d+(?:\.\d+)?)",
            line,
            re.IGNORECASE
        )

        if match:

            return normalize_number(
                match.group(1)
            )

        # More general form:
        #
        # Age: 48
        #

        match = re.search(
            r"\bAge\b\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)",
            line,
            re.IGNORECASE
        )

        if match:

            return normalize_number(
                match.group(1)
            )

    return None


# ============================================================
# BLOOD PRESSURE
# ============================================================

def extract_blood_pressure(lines):

    for line in lines:

        alias = find_alias_in_line(
            "bp",
            line
        )

        if not alias:
            continue

        remaining = extract_result_after_label(
            line,
            alias
        )

        if not remaining:
            continue

        # --------------------------------------------------
        # Case:
        #
        # Blood Pressure: 80
        # --------------------------------------------------

        match = re.match(
            r"^(\d+(?:\.\d+)?)",
            remaining
        )

        if match:

            return normalize_number(
                match.group(1)
            )

        # --------------------------------------------------
        # Case:
        #
        # Blood Pressure: 120/80 mmHg
        #
        # DO NOT automatically choose 80 yet.
        #
        # We need to confirm how your training dataset
        # defines the bp feature.
        # --------------------------------------------------

        match = re.match(
            r"^(\d+(?:\.\d+)?)\s*/\s*"
            r"(\d+(?:\.\d+)?)",
            remaining
        )

        if match:

            systolic = normalize_number(
                match.group(1)
            )

            diastolic = normalize_number(
                match.group(2)
            )

            # Currently return the full pair as None
            # until training semantics are confirmed.
            #
            # We should NOT guess whether bp means
            # systolic or diastolic.
            return None

    return None


# ============================================================
# RBC
# ============================================================

def extract_rbc(lines):

    value = extract_categorical_field(
        "rbc",
        lines,
        [
            "abnormal",
            "normal",
        ]
    )

    return normalize_normal_abnormal(
        value
    )


# ============================================================
# PUS CELLS
# ============================================================

def extract_pus_cells(lines):

    value = extract_categorical_field(
        "pc",
        lines,
        [
            "abnormal",
            "normal",
        ]
    )

    return normalize_normal_abnormal(
        value
    )


# ============================================================
# PUS CELL CLUMPS
# ============================================================

def extract_pus_cell_clumps(lines):

    value = extract_categorical_field(
        "pcc",
        lines,
        [
            "not present",
            "present",
        ]
    )

    return normalize_present(
        value
    )


# ============================================================
# BACTERIA
# ============================================================

def extract_bacteria(lines):

    value = extract_categorical_field(
        "ba",
        lines,
        [
            "not present",
            "present",
        ]
    )

    return normalize_present(
        value
    )


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_features(text: str):
    """
    Main extraction function.

    Parameters
    ----------
    text : str
        OCR text extracted from the medical report.

    Returns
    -------
    data : dict
        Extracted model features.

    warnings : list
        Technical extraction warnings.
    """

    # --------------------------------------------------------
    # Normalize OCR
    # --------------------------------------------------------

    text = normalize_text(
        text
    )

    # --------------------------------------------------------
    # Create clean lines
    # --------------------------------------------------------

    lines = [
        clean_line(line)
        for line in get_lines(text)
    ]

    # --------------------------------------------------------
    # Initialize all fields as None
    # --------------------------------------------------------

    data = {
        field: None
        for field in FEATURE_COLUMNS
    }

    # ========================================================
    # NUMERIC FEATURES
    # ========================================================

    data["age"] = extract_age(
        lines
    )

    data["bp"] = extract_blood_pressure(
        lines
    )

    data["sg"] = extract_numeric_field(
        "sg",
        lines
    )

    data["al"] = extract_numeric_field(
        "al",
        lines
    )

    data["su"] = extract_sugar(
        lines
    )

    data["bgr"] = extract_numeric_field(
        "bgr",
        lines
    )

    data["bu"] = extract_numeric_field(
        "bu",
        lines
    )

    data["sc"] = extract_numeric_field(
        "sc",
        lines
    )

    data["sod"] = extract_optional_lab_value(
        "sod",
        lines
    )

    data["pot"] = extract_optional_lab_value(
        "pot",
        lines
    )

    data["hemo"] = extract_numeric_field(
        "hemo",
        lines
    )

    data["pcv"] = extract_numeric_field(
        "pcv",
        lines
    )

    data["wc"] = extract_numeric_field(
        "wc",
        lines
    )

    data["rc"] = extract_numeric_field(
        "rc",
        lines
    )

    # ========================================================
    # URINE / CATEGORICAL FEATURES
    # ========================================================

    data["rbc"] = extract_rbc(
        lines
    )

    data["pc"] = extract_pus_cells(
        lines
    )

    data["pcc"] = extract_pus_cell_clumps(
        lines
    )

    data["ba"] = extract_bacteria(
        lines
    )

    # ========================================================
    # CLINICAL INFORMATION
    # ========================================================

    data["htn"] = extract_yes_no_field(
        "htn",
        lines
    )

    data["dm"] = extract_yes_no_field(
        "dm",
        lines
    )

    data["cad"] = extract_yes_no_field(
        "cad",
        lines
    )

    data["appet"] = extract_appetite(
        lines
    )

    data["pe"] = extract_pedal_edema(
        lines
    )

    data["ane"] = extract_yes_no_field(
        "ane",
        lines
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    warnings = validate_extracted_data(
        data
    )

    return data, warnings