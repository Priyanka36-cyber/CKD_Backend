# schemas.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class PredictionResponse(BaseModel):

    prediction: int

    classification: str

    probability: float


class AnalysisResponse(BaseModel):

    success: bool

    prediction: PredictionResponse

    extracted_data: Dict[str, Any]

    warnings: List[str]