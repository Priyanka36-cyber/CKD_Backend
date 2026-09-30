# test_prediction.py

from prediction import predict_kidney_disease


# ============================================================
# TEST DATA
# ============================================================

test_data = {

    "age": 48.0,
    "bp": None,
    "sg": 1.02,
    "al": 1.0,
    "su": 0.0,

    "rbc": "normal",
    "pc": "normal",
    "pcc": "notpresent",
    "ba": "notpresent",

    "bgr": 121.0,
    "bu": 36.0,
    "sc": 1.2,
    "sod": None,
    "pot": None,

    "hemo": 15.4,
    "pcv": 44.0,
    "wc": 7800.0,
    "rc": 5.2,

    "htn": "yes",
    "dm": "yes",
    "cad": "no",
    "appet": "good",
    "pe": "no",
    "ane": "no",
}


# ============================================================
# RUN PREDICTION
# ============================================================

result = predict_kidney_disease(
    test_data
)


# ============================================================
# DISPLAY RESULT
# ============================================================

print()
print("=" * 60)
print("KIDNEY DISEASE PREDICTION")
print("=" * 60)

print(
    "Prediction    :",
    result["prediction"]
)

print(
    "Classification :",
    result["classification"]
)

print(
    "Probability    :",
    f"{result['probability']:.4f}"
)

print("=" * 60)