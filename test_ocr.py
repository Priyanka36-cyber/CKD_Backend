from pathlib import Path

from extraction.ocr import extract_text_from_image


# Path to test report
image_path = Path("test_report/Test_OCR_Image.png")


# Read image as bytes
with open(image_path, "rb") as file:
    image_bytes = file.read()


# Run OCR
text = extract_text_from_image(image_bytes)


# Display result
print("\n")
print("=" * 70)
print("OCR RESULT")
print("=" * 70)
print()

print(text)

print()
print("=" * 70)
print("END OF OCR RESULT")
print("=" * 70)