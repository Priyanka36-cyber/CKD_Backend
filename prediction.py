# prediction.py

import os
import joblib
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "model",
    "xgboost.pkl"
)

print(MODEL_PATH)
# ============================================================
# LOAD MODEL
# ============================================================

if not os.path.exists(MODEL_PATH):

    raise FileNotFoundError(
        f"XGBoost model not found at: {MODEL_PATH}"
    )


model = joblib.load(
    MODEL_PATH
)


print(
    f"XGBoost model loaded successfully from: {MODEL_PATH}"
)


# ============================================================
# FEATURE COLUMNS
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
# PREDICTION FUNCTION
# ============================================================
def predict_kidney_disease(
    extracted_data: dict
):
    """
    Predict kidney disease using the saved
    XGBoost pipeline.

    Parameters
    ----------
    extracted_data : dict
        Data extracted from the medical report.

    Returns
    -------
    dict
        Prediction result.
    """

    # --------------------------------------------------------
    # Create dictionary containing exactly the features
    # expected by the model.
    # --------------------------------------------------------

    data = {}

    for column in FEATURE_COLUMNS:

        data[column] = extracted_data.get(
            column,
            None
        )


    # --------------------------------------------------------
    # Convert dictionary into a one-row DataFrame.
    #
    # The saved pipeline will handle:
    #
    # - missing numerical values
    # - missing categorical values
    # - categorical encoding
    # --------------------------------------------------------

    input_df = pd.DataFrame(
        [data],
        columns=FEATURE_COLUMNS
    )


    # --------------------------------------------------------
    # Convert None to NaN.
    #
    # SimpleImputer inside the saved pipeline expects
    # missing numerical values to be represented properly.
    # --------------------------------------------------------

    input_df = input_df.where(
        pd.notnull(input_df),
        None
    )


    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    prediction = model.predict(
        input_df
    )[0]


    # --------------------------------------------------------
    # Probability
    # --------------------------------------------------------

    probabilities = model.predict_proba(
        input_df
    )[0]


    # Find the probability corresponding to class 1.
    classifier = model.named_steps[
        "classifier"
    ]

    classes = list(
        classifier.classes_
    )

    if 1 in classes:

        ckd_probability = probabilities[
            classes.index(1)
        ]

    else:

        ckd_probability = 0.0


    # --------------------------------------------------------
    # Convert numpy values to normal Python types
    # --------------------------------------------------------

    prediction = int(
        prediction
    )

    ckd_probability = float(
        ckd_probability
    )


    # --------------------------------------------------------
    # Human-readable result
    # --------------------------------------------------------

    if prediction == 1:

        result = "ckd"

    else:

        result = "notckd"


    return {
        "prediction": prediction,
        "classification": result,
        "probability": ckd_probability,
    }