# extraction/validator.py


# Broad technical ranges.
# These are NOT medical diagnostic ranges.
FIELD_RANGES = {

    "age": (0, 120),

    "bp": (20, 300),

    "sg": (0.9, 1.1),

    "al": (0, 5),

    "su": (0, 5),

    "bgr": (1, 2000),

    "bu": (1, 1000),

    "sc": (0.01, 100),

    "sod": (50, 250),

    "pot": (1, 15),

    "hemo": (1, 30),

    "pcv": (1, 100),

    "wc": (100, 100000),

    "rc": (0.1, 15),
}


def validate_value(
    field: str,
    value
) -> bool:

    if value is None:
        return True

    if field not in FIELD_RANGES:
        return True

    minimum, maximum = FIELD_RANGES[field]

    return minimum <= value <= maximum


def validate_extracted_data(data: dict):

    warnings = []

    for field, value in data.items():

        if value is None:
            continue

        if field in FIELD_RANGES:

            if not validate_value(
                field,
                value
            ):

                warnings.append(
                    f"Suspicious extracted value "
                    f"for {field}: {value}"
                )

    return warnings