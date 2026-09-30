# extraction/ocr.py

import pytesseract

from PIL import Image
from io import BytesIO

from pytesseract import Output

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
# If Tesseract is not in PATH, uncomment this:
#
# pytesseract.pytesseract.tesseract_cmd = (
#     r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# )


def extract_text_from_image(image_bytes: bytes) -> str:

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    text = pytesseract.image_to_string(
        image,
        config="--psm 6"
    )

    return text


def extract_ocr_data(image_bytes: bytes):

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    data = pytesseract.image_to_data(
        image,
        output_type=Output.DICT,
        config="--psm 6"
    )

    words = []

    for i in range(len(data["text"])):

        text = data["text"][i].strip()

        if not text:
            continue

        try:
            confidence = float(
                data["conf"][i]
            )
        except (ValueError, TypeError):
            confidence = 0.0

        words.append({
            "text": text,
            "confidence": confidence,
            "left": data["left"][i],
            "top": data["top"][i],
            "width": data["width"][i],
            "height": data["height"][i],
            "block_num": data["block_num"][i],
            "par_num": data["par_num"][i],
            "line_num": data["line_num"][i],
        })

    return words