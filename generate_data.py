# generate_data.py
import json, os
from google import genai
from dotenv import load_dotenv
load_dotenv()

client = genai.Client()

prompt = """Generate a JSON array of exactly 10 baby/child products for a MENA e-commerce platform (like Mumzworld).
Each product must have:
- id: string like "P001"
- name_en: English product name
- name_ar: Arabic product name (proper Arabic, NOT transliteration)
- category: one of ["feeding", "gear", "toys", "clothing", "safety", "bedroom", "bath", "health"]
- brand: brand name
- price_aed: number between 15 and 850
- age_min_months: minimum age in months (0=newborn)
- age_max_months: maximum age in months (use 144 for 12 years)
- description_en: 2-sentence English product description
- description_ar: 2-sentence Arabic description (natural Arabic, not translated)
- tags: array of 3-5 keyword strings
- reviews: array of exactly 3 objects, each with:
    - rating: 1-5
    - text_en: English review (1-2 sentences)
    - text_ar: Arabic review (1-2 sentences, natural Arabic)

Include a diverse mix: newborn items, toddler toys, car seats, strollers, bottles, monitors, etc.
Cover price range from budget (15 AED) to premium (850 AED).
Return ONLY valid JSON, no markdown, no preamble."""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=genai.types.GenerateContentConfig(
        response_mime_type="application/json",
    )
)

products = json.loads(response.text)
os.makedirs("data", exist_ok=True)
with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"Generated {len(products)} products")
