# generate_data.py
import json
import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq()

prompt = """Generate a JSON array of exactly 50 baby/child products for a MENA e-commerce platform (like Mumzworld).
Each product must have:
- id: string like "P001"
- name_en: English product name
- name_ar: Arabic product name (proper Arabic script, NOT English transliteration)
- category: one of ["feeding", "gear", "toys", "clothing", "safety", "bedroom", "bath", "health"]
- brand: brand name
- price_aed: number between 15 and 850
- age_min_months: minimum age in months (0=newborn)
- age_max_months: maximum age in months (use 144 for 12 years)
- description_en: 2-sentence English product description
- description_ar: 2-sentence Arabic description (natural Arabic, not translated from English)
- tags: array of 3-5 keyword strings
- reviews: array of exactly 8 objects, each with:
    - rating: integer 1-5
    - text_en: English review (1-2 sentences)
    - text_ar: Arabic review (1-2 sentences, natural Arabic — not translated from text_en)

CRITICAL: name_ar, description_ar, and text_ar MUST be written in Arabic script (Unicode Arabic characters),
NOT English transliteration like 'zujajat al-atfal'. Every Arabic field must contain actual Arabic letters.

Include a diverse mix: newborn items, toddler toys, car seats, strollers, feeding bottles, baby monitors,
clothing, bath products, health items, bedroom items.
Cover price range from budget (15 AED) to premium (850 AED).
Give each product a realistic mix of ratings (not all 5-stars).

Return ONLY valid JSON array, no markdown, no preamble, no explanation."""

print("Generating 50 products via Groq llama-3.3-70b-versatile ...")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=32000,
    response_format={"type": "json_object"}
)

raw = response.choices[0].message.content.strip()

# Groq json_object wraps in a dict — unwrap if needed
data = json.loads(raw)
if isinstance(data, dict):
    # Find the list value (could be "products", "items", etc.)
    products = next((v for v in data.values() if isinstance(v, list)), None)
    if products is None:
        raise ValueError(f"Expected a list inside the JSON object, got keys: {list(data.keys())}")
else:
    products = data

print(f"Generated {len(products)} products")

# Validate basics
missing_ar = [p.get("id", "?") for p in products if not p.get("name_ar", "").strip()]
if missing_ar:
    print(f"WARNING: {len(missing_ar)} products have empty name_ar: {missing_ar[:5]}")

os.makedirs("data", exist_ok=True)
with open("data/products.json", "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"Saved to data/products.json")
print(f"Sample: {products[0]['name_en']} | {products[0]['name_ar']}")
