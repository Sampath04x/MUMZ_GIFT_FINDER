# src/models.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum

class Language(str, Enum):
    EN = "en"
    AR = "ar"

class GiftSuggestion(BaseModel):
    product_id: str
    name_en: str
    name_ar: str
    price_aed: float
    reason_en: str = Field(..., description="Why this product fits the request, in English")
    reason_ar: str = Field(..., description="Why this product fits the request, in Arabic")
    age_appropriate: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    @field_validator('reason_en')
    @classmethod
    def reason_en_not_empty(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("reason_en must be a meaningful sentence")
        return v

    @field_validator('reason_ar')
    @classmethod
    def reason_ar_not_empty(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("reason_ar must be a meaningful Arabic sentence")
        return v

class GiftFinderResult(BaseModel):
    query: str
    suggestions: list[GiftSuggestion] = Field(..., min_length=0, max_length=5)
    search_summary_en: str
    search_summary_ar: str
    refusal_reason: Optional[str] = None  # populated when we can't fulfill request

class ReviewVerdict(BaseModel):
    pros_en: list[str] = Field(..., min_length=1)
    pros_ar: list[str] = Field(..., min_length=1)
    cons_en: list[str] = Field(..., min_length=1)
    cons_ar: list[str] = Field(..., min_length=1)
    age_suitability_note_en: str
    age_suitability_note_ar: str
    safety_notes_en: Optional[str] = None
    safety_notes_ar: Optional[str] = None
    verdict_score: float = Field(..., ge=1.0, le=5.0)
    total_reviews_analyzed: int
    confidence: float = Field(..., ge=0.0, le=1.0)

class IntentExtraction(BaseModel):
    age_min_months: Optional[int] = None
    age_max_months: Optional[int] = None
    budget_max_aed: Optional[float] = None
    occasion: Optional[str] = None
    relationship: Optional[str] = None
    preferred_categories: list[str] = []
    keywords: list[str] = []
    language_detected: Language = Language.EN
    is_valid_gift_query: bool = True
    rejection_reason: Optional[str] = None
