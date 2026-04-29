import json
from pathlib import Path
from groq import Groq
from pydantic import ValidationError
from src.models import ReviewVerdict
import os
from dotenv import load_dotenv
load_dotenv()

client = Groq()
PRODUCTS_PATH = Path("data/products.json")

VERDICT_SYSTEM = """You are a product review synthesizer for Mumzworld, a baby and child e-commerce platform.
Given a set of customer reviews, synthesize them into a structured "Moms Verdict" card.

RULES:
- pros and cons MUST be grounded in actual review content — no invented claims
- Arabic text must be natural Arabic, NOT a word-for-word translation from English
  Example WRONG (translated): "هذا المنتج ممتاز للأطفال الصغار"
  Example RIGHT (natural): "ما شاء الله، الكل من حواليها مبسوطين فيه وسهل الاستخدام"
- verdict_score = weighted average of ratings, rounded to 1 decimal place
- confidence = lower when reviews conflict heavily or sample size is small (< 5 reviews → max 0.7)
- If safety concerns appear in 2+ reviews, populate safety_notes_en and safety_notes_ar; otherwise set to null
- total_reviews_analyzed must exactly match the number of reviews provided

Return ONLY valid JSON matching this exact schema — no markdown, no preamble:
{
  "pros_en": ["pro 1", "pro 2"],
  "pros_ar": ["ميزة 1", "ميزة 2"],
  "cons_en": ["con 1", "con 2"],
  "cons_ar": ["عيب 1", "عيب 2"],
  "age_suitability_note_en": "string",
  "age_suitability_note_ar": "string",
  "safety_notes_en": null,
  "safety_notes_ar": null,
  "verdict_score": 4.5,
  "total_reviews_analyzed": 3,
  "confidence": 0.8
}"""


def run_moms_verdict(product_id: str) -> dict:
    """Generate a structured Moms Verdict for a given product."""
    if not PRODUCTS_PATH.exists():
        return {"error": "Products data not found", "product_id": product_id}

    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        return {"error": f"Product {product_id} not found", "product_id": product_id}

    reviews = product["reviews"]
    reviews_block = json.dumps(reviews, ensure_ascii=False, indent=2)
    user_message = f"""Product: {product['name_en']} ({product['name_ar']})
Category: {product['category']}
Price: {product['price_aed']} AED
Age range: {product['age_min_months']}-{product['age_max_months']} months

Reviews ({len(reviews)} total):
{reviews_block}

Synthesize the above {len(reviews)} reviews into a structured Moms Verdict.
total_reviews_analyzed must be exactly {len(reviews)}."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": VERDICT_SYSTEM},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=1024
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        verdict = ReviewVerdict(**data)
        return {
            "product_id": product_id,
            "product_name_en": product["name_en"],
            "product_name_ar": product["name_ar"],
            "verdict": verdict.model_dump()
        }
    except json.JSONDecodeError as e:
        return {
            "product_id": product_id,
            "error": f"JSON parse failed: {str(e)}"
        }
    except ValidationError as e:
        return {
            "product_id": product_id,
            "error": f"Schema validation failed: {str(e)}"
        }
    except Exception as e:
        return {
            "product_id": product_id,
            "error": f"Verdict generation failed: {str(e)}"
        }
