# test_analyze.py

from analyze import analyze_report


IMAGE_PATH = "test_report/Test_OCR_Image.png"


# ============================================================
# READ REPORT
# ============================================================

with open(
    IMAGE_PATH,
    "rb"
) as file:

    image_bytes = file.read()


# ============================================================
# ANALYZE
# ============================================================

result = analyze_report(
    image_bytes
)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 70)
print("COMPLETE KIDNEY REPORT ANALYSIS")
print("=" * 70)


print("\nEXTRACTED DATA")
print("-" * 70)

for field, value in result["extracted_data"].items():

    print(
        f"{field:8} : {value}"
    )


print("\nWARNINGS")
print("-" * 70)

if result["warnings"]:

    for warning in result["warnings"]:
        print(warning)

else:

    print("No extraction warnings.")


print("\nPREDICTION")
print("-" * 70)

prediction = result["prediction"]

print(
    "Prediction    :",
    prediction["prediction"]
)

print(
    "Classification :",
    prediction["classification"]
)

print(
    "Probability    :",
    f"{prediction['probability']:.4f}"
)

print("=" * 70)