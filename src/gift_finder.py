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

Age conversion rules:
- "newborn" → age_min_months=0, age_max_months=3
- "baby" → age_min_months=0, age_max_months=12
- "toddler" → age_min_months=12, age_max_months=36
- "preschool" or "preschooler" → age_min_months=36, age_max_months=60
- "6 months old" → age_min_months=3, age_max_months=9 (give a ±3 month range)
- "1 year old" → age_min_months=9, age_max_months=15
- "2 year old" → age_min_months=21, age_max_months=27

Rules:
- If user says "under 200 AED" → budget_max_aed=200
- If query is clearly NOT about buying gifts for babies or children, set is_valid_gift_query=false and explain in rejection_reason
- If the query is ambiguous (could be gift-related), lean toward is_valid_gift_query=true

Return ONLY valid JSON matching this schema — no markdown, no preamble:
{
  "age_min_months": integer or null,
  "age_max_months": integer or null,
  "budget_max_aed": float or null,
  "occasion": string or null,
  "relationship": string or null,
  "preferred_categories": [],
  "keywords": [],
  "language_detected": "en" or "ar",
  "is_valid_gift_query": true or false,
  "rejection_reason": null or string
}"""

GIFT_RANKING_SYSTEM = """You are a helpful gift advisor for Mumzworld, the MENA's leading baby e-commerce platform.
Given a list of candidate products and a user's gift request, select the 3 best matches and explain why.

RULES:
- If NO products match the request well, return an empty suggestions list and explain in search_summary_en and search_summary_ar
- The reason_ar MUST be natural Arabic — NOT a word-for-word translation of reason_en
  Example WRONG Arabic (translated): "هذا المنتج مثالي لأنه آمن وعملي" (mechanical translation)
  Example RIGHT Arabic (natural): "ما شاء الله، هذا الشيء مناسب جداً للبيبي وبسعر معقول"
- Confidence score scale: 0.9+ = perfect match, 0.7–0.9 = good match, below 0.7 = include only if nothing better
- reason_en must reference specific product features that match the user's request (minimum 2 sentences)
- age_appropriate = true only if the product's age range covers the child's age in the query

Return ONLY valid JSON — no markdown, no preamble:
{
  "suggestions": [
    {
      "product_id": "P001",
      "name_en": "Product name in English",
      "name_ar": "اسم المنتج بالعربية",
      "price_aed": 150.0,
      "reason_en": "This is perfect because... (2-3 sentences, specific to the request)",
      "reason_ar": "هذا المنتج مناسب لأن... (جملتان بالعربية الطبيعية، ليست ترجمة حرفية)",
      "age_appropriate": true,
      "confidence_score": 0.92
    }
  ],
  "search_summary_en": "Here are 3 thoughtful gift ideas for [occasion/context]...",
  "search_summary_ar": "إليك ثلاث هدايا مناسبة لـ..."
}"""

# ── PIPELINE ─────────────────────────────────────────────────────────────────

def extract_intent(query: str) -> IntentExtraction:
    """Step 1: Parse user query into structured parameters (cheap/fast model)."""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": INTENT_SYSTEM},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=512,
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        return IntentExtraction(**data)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Intent JSON parse failed: {e.msg}", e.doc, e.pos)


def run_gift_finder(query: str) -> GiftFinderResult:
    """Full pipeline: query → intent → retrieval → ranking → validated output."""

    # Step 1: Extract intent
    try:
        intent = extract_intent(query)
    except (json.JSONDecodeError, ValidationError, Exception) as e:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en="Sorry, I couldn't understand your request. Please try rephrasing.",
            search_summary_ar="عذراً، لم أتمكن من فهم طلبك. يرجى إعادة الصياغة.",
            refusal_reason=f"Intent extraction failed: {str(e)}"
        )

    # Step 2: Check if valid gift query
    if not intent.is_valid_gift_query:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en=f"I can only help with gift searches for babies and children. {intent.rejection_reason or ''}",
            search_summary_ar=f"يمكنني فقط المساعدة في البحث عن هدايا للأطفال. {intent.rejection_reason or ''}",
            refusal_reason=intent.rejection_reason or "Not a gift query"
        )

    # Step 3: Guard against impossibly low budget
    if intent.budget_max_aed is not None and intent.budget_max_aed < 15:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en="The budget is too low to find any suitable products. Our products start from 15 AED.",
            search_summary_ar="الميزانية منخفضة جداً للعثور على أي منتجات مناسبة. أسعارنا تبدأ من 15 درهم.",
            refusal_reason="Budget too low"
        )

    # Step 4: Semantic retrieval
    search_query = f"{query} {' '.join(intent.keywords)}"
    candidates = retrieve_products(
        query=search_query,
        age_months=intent.age_min_months,
        budget_aed=intent.budget_max_aed,
        categories=intent.preferred_categories if intent.preferred_categories else None
    )

    if not candidates:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en="I couldn't find products matching all your requirements. Try adjusting the budget or age range.",
            search_summary_ar="لم أجد منتجات تطابق جميع متطلباتك. جرب تعديل الميزانية أو الفئة العمرية.",
            refusal_reason="No products matched the filters"
        )

    # Step 5: LLM ranking (quality model)
    products_block = json.dumps(candidates, ensure_ascii=False, indent=2)
    user_message = f"""User request: {query}

Intent extracted:
- Age range: {intent.age_min_months}–{intent.age_max_months} months
- Budget: up to {intent.budget_max_aed} AED
- Occasion: {intent.occasion}
- Language: {intent.language_detected}

Candidate products:
{products_block}

Select the 3 best matches. Write reason_ar in NATURAL Arabic (not a translation of reason_en)."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": GIFT_RANKING_SYSTEM},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
        result_data = json.loads(raw)

        suggestions = [GiftSuggestion(**s) for s in result_data.get("suggestions", [])]

        return GiftFinderResult(
            query=query,
            suggestions=suggestions,
            search_summary_en=result_data.get("search_summary_en", ""),
            search_summary_ar=result_data.get("search_summary_ar", ""),
        )

    except json.JSONDecodeError as e:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en="Something went wrong generating your gift list. Please try again.",
            search_summary_ar="حدث خطأ في إنشاء قائمة الهدايا. يرجى المحاولة مرة أخرى.",
            refusal_reason=f"JSON parse failed: {str(e)}"
        )
    except ValidationError as e:
        return GiftFinderResult(
            query=query,
            suggestions=[],
            search_summary_en="The AI returned an invalid response. Please try again.",
            search_summary_ar="عاد الذكاء الاصطناعي باستجابة غير صالحة. يرجى المحاولة مرة أخرى.",
            refusal_reason=f"Output validation failed: {str(e)}"
        )
