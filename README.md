# Mumz Gift Finder + Moms Verdict

AI-powered gift discovery and product review synthesis for Mumzworld (MENA baby e-commerce).

## What it does

**Gift Finder**: Natural-language query → LLM intent extraction → RAG retrieval over product catalog → ranked bilingual (EN/AR) shortlist with reasoning and confidence scores.

**Moms Verdict**: Given a product ID → synthesize customer reviews into a structured verdict card in English and Arabic.

## Setup (under 5 minutes)

```bash
git clone https://github.com/Sampath04x/mumz-gift-finder
cd mumz-gift-finder
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # Fill in GROQ_API_KEY (and GEMINI_API_KEY for data generation)
python generate_data.py       # Creates data/products.json with 50 bilingual products
uvicorn src.api:app --reload  # Starts server at http://localhost:8000
```

Visit http://localhost:8000/docs for the interactive API explorer.

## Architecture

```
User query
    ↓
[Groq llama-3.1-8b-instant]  Intent extraction → structured params (age, budget, occasion)
    ↓
[ChromaDB + all-MiniLM-L6-v2]  Semantic retrieval → top 5 candidates
    ↓
[Groq llama-3.3-70b-versatile]  Ranking + bilingual reasoning → JSON-validated output
    ↓
FastAPI response (GiftFinderResult schema)
```

## API Reference

### Health check
```bash
curl http://localhost:8000/
# {"status":"ok","features":["gift-finder","moms-verdict"]}
```

### List all products
```bash
curl http://localhost:8000/products | python -m json.tool
```

### Gift Finder — English query
```bash
curl -s -X POST http://localhost:8000/gift-finder \
  -H "Content-Type: application/json" \
  -d '{"query": "thoughtful gift for a friend with a 6-month-old, under 200 AED"}' \
  | python -m json.tool
```

### Gift Finder — Arabic query
```bash
curl -s -X POST http://localhost:8000/gift-finder \
  -H "Content-Type: application/json" \
  -d '{"query": "هدية لطفل عمره سنة بميزانية 300 درهم"}' \
  | python -m json.tool
```

### Moms Verdict
```bash
curl -s http://localhost:8000/moms-verdict/P001 | python -m json.tool
```

## Tooling

| Tool | Model / Version | Used for |
|------|----------------|----------|
| Groq | llama-3.1-8b-instant | Intent extraction (cheap, fast) |
| Groq | llama-3.3-70b-versatile | Gift ranking + Moms Verdict (quality) |
| Gemini API | gemini-2.5-flash | Synthetic data generation (products.json) |
| ChromaDB | 1.5.8 + all-MiniLM-L6-v2 | Product embedding + semantic retrieval |
| FastAPI | 0.136.1 | REST API layer |

**How I used AI in this build:**
- Used Groq's Llama models for all production inference (fast, cheap, reliable JSON output via `response_format`)
- Used Gemini 2.5 Flash to generate the synthetic product catalog (50 products with Arabic names and reviews)
- Iterated the Arabic system prompt twice after testing showed literal-translation artifacts — natural Arabic phrasing requires explicit counter-examples in the prompt, not just instructions
- Split intent extraction and ranking into two separate LLM calls; combining them in one call degraded Arabic output quality significantly

**What didn't work:**
- Single-call intent+ranking produced weaker Arabic naturalness — split pipeline fixed this
- Groq's `json_object` mode requires the exact schema to be spelled out in the system prompt; ambiguous schemas produce unpredictable field names that break Pydantic validation
- Combined budget+age ChromaDB `where` filters fail silently — age filter is now applied post-query in Python
