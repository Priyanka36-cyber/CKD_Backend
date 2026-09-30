# analyze.py

from extraction.ocr import extract_text_from_image
from extraction.extractor import extract_features
from prediction import predict_kidney_disease


def analyze_report(image_bytes: bytes):

    # ========================================================
    # STEP 1: OCR
    # ========================================================

    ocr_text = extract_text_from_image(
        image_bytes
    )

    # ========================================================
    # STEP 2: EXTRACT FEATURES
    # ========================================================

    extracted_data, warnings = extract_features(
        ocr_text
    )

    # ========================================================
    # STEP 3: PREDICTION
    # ========================================================

    prediction_result = predict_kidney_disease(
        extracted_data
    )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "extracted_data": extracted_data,
        "warnings": warnings,
        "prediction": prediction_result
    }