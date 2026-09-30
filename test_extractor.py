from extraction.ocr import extract_text_from_image
from extraction.extractor import extract_features


IMAGE_PATH = "test_report/Test_OCR_Image.png"


with open(
    IMAGE_PATH,
    "rb"
) as file:

    image_bytes = file.read()


# OCR
text = extract_text_from_image(
    image_bytes
)


# Extraction
data, warnings = extract_features(
    text
)


print()
print("=" * 70)
print("EXTRACTED FEATURES")
print("=" * 70)

for field, value in data.items():

    print(
        f"{field:8} : {value}"
    )


print()
print("=" * 70)
print("WARNINGS")
print("=" * 70)

if warnings:

    for warning in warnings:
        print(warning)

else:

    print("No extraction warnings.")


print("=" * 70)