# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from analyze import analyze_report

from schemas import AnalysisResponse


# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Kidney Disease Prediction API",
    description="OCR + XGBoost based kidney disease prediction backend",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Kidney Disease Prediction API is running",
        "status": "ok"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# ANALYZE REPORT
# ============================================================

@app.post(
    "/analyze",
    response_model=AnalysisResponse
)
async def analyze_uploaded_report(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )


    # --------------------------------------------------------
    # Allowed image formats
    # --------------------------------------------------------

    allowed_extensions = {
        ".png",
        ".jpg",
        ".jpeg"
    }

    filename = file.filename.lower()

    if not any(
        filename.endswith(extension)
        for extension in allowed_extensions
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. "
                "Currently supported: PNG, JPG and JPEG."
            )
        )


    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    try:

        image_bytes = await file.read()

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=f"Unable to read uploaded file: {error}"
        )


    # --------------------------------------------------------
    # Check empty file
    # --------------------------------------------------------

    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )


    # --------------------------------------------------------
    # Run complete pipeline
    #
    # Image
    #   ↓
    # OCR
    #   ↓
    # Extraction
    #   ↓
    # XGBoost
    # --------------------------------------------------------

    try:

        result = analyze_report(
            image_bytes
        )

    except Exception as error:

        print(
            "Analysis error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to analyze the report. "
                "Please make sure the report is clear "
                "and readable."
            )
        )


    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "success": True,

        "prediction": result[
            "prediction"
        ],

        "extracted_data": result[
            "extracted_data"
        ],

        "warnings": result[
            "warnings"
        ]
    }