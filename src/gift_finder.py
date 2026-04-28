# src/gift_finder.py
import json
from groq import Groq
from pydantic import ValidationError
from src.models import IntentExtraction, GiftFinderResult, GiftSuggestion
from src.data_loader import retrieve_products
import os
from dotenv import load_dotenv
load_dotenv()

client = Groq()

# ── SYSTEM PROMPTS ────────────────────────────────────────────────────────────

INTENT_SYSTEM = """You are a shopping assistant for Mumzworld, the MENA's largest baby and child e-commerce platform.
Extract structured gift search parameters from the user's query.
The user may write in English or Arabic — detect the language.

Return ONLY valid JSON matching this schema — no markdown, no explanation:
{
  "age_min_months": int or null,
  "age_max_months": int or null,
  "budget_max_aed": float or null,
  "occasion": string or null,
  "relationship": string or null (e.g. "friend", "sister", "colleague"),
  "preferred_categories": [],
  "keywords": [],
  "language_detected": "en" or "ar",
  "is_valid_gift_query": true or false,
  "rejection_reason": null or string (if not valid, explain briefly)
}

Rules:
- If user says "6 months old" → age_min_months=3, age_max_months=9 (give a range)
- If user says "toddler" → age_min_months=12, age_max_months=36
- If user says "baby" → age_min_months=0, age_max_months=12
- If user says "under 200 AED" → budget_max_aed=200
- If query is not gift-related, set is_valid_gift_query=false
"""

GIFT_RANKING_SYSTEM_EN = """You are a helpful gift advisor for Mumzworld, the MENA's leading baby e-commerce platform.
Given a list of candidate products and a user's gift request, select the 3 best matches and explain why.

Return ONLY valid JSON — no markdown, no preamble:
{
  "suggestions": [
    {
      "product_id": "P001",
      "name_en": "Product name in English",
      "name_ar": "اسم المنتج بالعربية",
      "price_aed": 150.0,
      "reason_en": "This is perfect because... (2-3 sentences, specific to the request)",
      "reason_ar": "هذا المنتج مثالي لأن... (جملتان بالعربية الطبيعية، ليست ترجمة حرفية)",
      "age_appropriate": true,
      "confidence_score": 0.92
    }
  ],
  "search_summary_en": "Here are 3 thoughtful gift ideas for [occasion/context]...",
  "search_summary_ar": "إليك ثلاثة هدايا مناسبة لـ..."
}

RULES:
- If NO products match the request well, return an empty suggestions list and explain in search_summary
- The Arabic reason_ar must be natural Arabic — NOT a word-for-word translation of reason_en
- Confidence score: 0.9+ = perfect match, 0.7-0.9 = good match, below 0.7 = include only if nothing better
- reason_en must reference specific product features that match the user's request
"""

GIFT_RANKING_SYSTEM_AR = GIFT_RANKING_SYSTEM_EN  # Model handles both; language comes from the user prompt

# ── PIPELINE ─────────────────────────────────────────────────────────────────

def extract_intent(query: str) -> IntentExtraction:
    """Step 1: Parse user query into structured parameters."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user", "content": query}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)
    return IntentExtraction(**data)


def run_gift_finder(query: str) -> GiftFinderResult:
    """Full pipeline: query → intent → retrieval → ranking → validated output."""

    # Step 1: Extract intent
    try:
        intent = extract_intent(query)
    except (json.JSONDecodeError, Exception) as e:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en="Sorry, I couldn't understand your request. Please try rephrasing.",
            search_summary_ar="عذراً، لم أتمكن من فهم طلبك. يرجى إعادة الصياغة.",
            refusal_reason=f"Intent extraction failed: {str(e)}"
        )

    # Step 2: Check if valid query
    if not intent.is_valid_gift_query:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en=f"I can only help with gift searches for babies and children. {intent.rejection_reason or ''}",
            search_summary_ar=f"يمكنني فقط المساعدة في البحث عن هدايا للأطفال. {intent.rejection_reason or ''}",
            refusal_reason=intent.rejection_reason
        )

    # Check for impossibly low budget
    if intent.budget_max_aed is not None and intent.budget_max_aed < 15:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en="The budget is too low to find any suitable products.",
            search_summary_ar="الميزانية منخفضة جداً للعثور على أي منتجات مناسبة.",
            refusal_reason="Budget too low"
        )

    # Step 3: Build search query + retrieve
    search_query = f"{query} {' '.join(intent.keywords)}"
    candidates = retrieve_products(
        query=search_query,
        age_months=intent.age_min_months,
        budget_aed=intent.budget_max_aed,
        categories=intent.preferred_categories if intent.preferred_categories else None
    )

    # Step 4: Handle no results
    if not candidates:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en="I couldn't find products matching all your requirements. Try adjusting the budget or age range.",
            search_summary_ar="لم أجد منتجات تطابق جميع متطلباتك. جرب تعديل الميزانية أو الفئة العمرية.",
            refusal_reason="No products matched the filters"
        )

    # Step 5: LLM ranking
    products_block = json.dumps(candidates, ensure_ascii=False, indent=2)
    user_message = f"""User request: {query}

Intent extracted:
- Age range: {intent.age_min_months}-{intent.age_max_months} months
- Budget: up to {intent.budget_max_aed} AED
- Occasion: {intent.occasion}
- Language: {intent.language_detected}

Candidate products:
{products_block}

Select the 3 best matches. For each, write reason_ar in NATURAL Arabic (not a translation of reason_en)."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": GIFT_RANKING_SYSTEM_EN},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
        result_data = json.loads(raw)

        # Validate with Pydantic
        suggestions = [GiftSuggestion(**s) for s in result_data.get("suggestions", [])]

        return GiftFinderResult(
            query=query,
            suggestions=suggestions,
            search_summary_en=result_data.get("search_summary_en", ""),
            search_summary_ar=result_data.get("search_summary_ar", ""),
        )

    except (json.JSONDecodeError, ValidationError) as e:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en="Something went wrong generating your gift list. Please try again.",
            search_summary_ar="حدث خطأ في إنشاء قائمة الهدايا. يرجى المحاولة مرة أخرى.",
            refusal_reason=f"Output validation failed: {str(e)}"
        )
