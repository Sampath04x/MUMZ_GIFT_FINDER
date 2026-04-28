# Mumz Gift Finder + Moms Verdict

AI-powered gift discovery and product review synthesis for Mumzworld (MENA baby e-commerce).

## What it does

**Gift Finder**: Natural-language query → LLM intent extraction → RAG retrieval over product catalog → ranked bilingual (EN/AR) shortlist with reasoning and confidence scores.

**Moms Verdict**: Given a product → synthesize customer reviews into a structured verdict card in English and Arabic.

## Setup (under 5 minutes)

```bash
git clone https://github.com/Sampath04x/mumz-gift-finder
cd mumz-gift-finder
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your GROQ_API_KEY (and GEMINI_API_KEY for data generation)
python generate_data.py   # Creates data/products.json + embeds into ChromaDB
uvicorn src.api:app --reload
```

Visit http://localhost:8000/docs for the interactive API explorer.

## Example queries

```bash
# English gift request
curl -X POST http://localhost:8000/gift-finder \
  -H "Content-Type: application/json" \
  -d '{"query": "thoughtful gift for a friend with a 6-month-old, under 200 AED"}'

# Arabic query
curl -X POST http://localhost:8000/gift-finder \
  -H "Content-Type: application/json" \
  -d '{"query": "هدية لطفل عمره سنة بميزانية 300 درهم"}'

# Moms Verdict
curl http://localhost:8000/moms-verdict/P001
```

## Architecture

```
User query
    ↓
[Groq Llama-3.3-70b] Intent extraction → structured params (age, budget, occasion)
    ↓
[ChromaDB + all-MiniLM-L6-v2] Semantic retrieval → top 5 candidates
    ↓
[Groq Llama-3.3-70b] Ranking + bilingual reasoning → JSON-validated output
    ↓
FastAPI response (GiftFinderResult schema)
```

## Tooling

| Tool | Model / Version | Used for |
|------|----------------|----------|
| Groq | llama-3.3-70b-versatile | Intent extraction, Gift ranking, Moms Verdict |
| Gemini API | gemini-2.5-pro | Used originally for data generation (products.json) |
| ChromaDB | 0.4.x + all-MiniLM-L6-v2 | Product embedding + semantic retrieval |
| KiloCode | VS Code extension | Agent-assisted refactoring, prompt iteration |

**How I used AI in this build:**
- Gemini 2.5 Pro via KiloCode for pair-programming the pipeline logic and catching edge cases
- Gemini 2.5 Pro to generate the synthetic product catalog (60 products with Arabic names/reviews)
- Manual overrides: I rewrote the Arabic system prompt twice after testing showed literal-translation artifacts
- Eval grading: ran Gemini 2.5 Flash as a judge on 5 test cases to score Arabic naturalness (results in EVALS.md)

**What worked:** Migrating to the Groq API for production tasks eliminated rate-limiting bottlenecks, while the `llama-3.3-70b-versatile` model was able to easily handle structured JSON schema extraction and bilingual content generation.

**What didn't work:** Initial attempts at combined intent+ranking in one call led to worse Arabic output. Splitting into two calls improved naturalness significantly. Similarly, using Groq's `json_object` mode requires the strict JSON schema to be explicitly defined in the system prompt; otherwise, it will generate arbitrary structures that break Pydantic validation.
